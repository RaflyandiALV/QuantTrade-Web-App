# backend/strategy_core.py
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

class TradingEngine:
    def __init__(self, initial_capital=10000):
        self.initial_capital = float(initial_capital)

    def fetch_data(self, symbol, period="1y", interval="1d", start_date=None, end_date=None):
        try:
            if start_date and end_date:
                print(f"📥 Fetching Custom Range: {start_date} to {end_date}")
                df = yf.download(symbol, start=start_date, end=end_date, interval=interval, progress=False, auto_adjust=True, timeout=20)
            else:
                if interval in ['1h', '90m'] and period in ['5y', 'max', '10y', '2y']:
                    period = "730d" 
                
                print(f"📥 Fetching Period: {period}")
                df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True, timeout=20)
            
            if df.empty: return None

            if isinstance(df.columns, pd.MultiIndex):
                try:
                    if 'Close' in df.columns.get_level_values(0):
                        df.columns = df.columns.get_level_values(0)
                    else:
                        df.columns = [col[0] for col in df.columns]
                except: pass

            df = df.reset_index()
            df.columns = [str(c).lower() for c in df.columns]
            
            if 'date' in df.columns: df.rename(columns={'date': 'time'}, inplace=True)
            elif 'datetime' in df.columns: df.rename(columns={'datetime': 'time'}, inplace=True)
            
            return df
        except Exception as e:
            print(f"❌ Data Error: {e}")
            return None

    def prepare_indicators(self, df):
        # 1. MOMENTUM (SMA Cross)
        df['sma_fast'] = df['close'].rolling(10).mean()
        df['sma_slow'] = df['close'].rolling(50).mean()

        # 2. MEAN REVERSAL (Bollinger + RSI)
        df['bb_mid'] = df['close'].rolling(20).mean()
        std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_mid'] + (2 * std)
        df['bb_lower'] = df['bb_mid'] - (2 * std)
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # 3. GRID TRADING
        df['grid_top'] = df['high'].rolling(50).max()
        df['grid_bottom'] = df['low'].rolling(50).min()
        df['grid_mid'] = (df['grid_top'] + df['grid_bottom']) / 2

        # 4. MULTITIMEFRAME (EMA Trend)
        df['ema_trend'] = df['close'].ewm(span=200).mean()
        
        # 5. ATR (Untuk Suggestion SL/TP)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()

        df.fillna(0, inplace=True)
        return df

    def run_backtest(self, df, strategy_type):
        df = self.prepare_indicators(df)
        
        capital = self.initial_capital
        position_size = 0 
        entry_price = 0
        
        markers = [] 
        trades = []
        equity_curve = []
        
        start_idx = 50 if len(df) > 50 else 0
        if len(df) < 50:
            return df, [], self.calculate_metrics([], capital, 0, capital, []), []

        start_price = df.iloc[start_idx]['close']
        
        for i in range(start_idx, len(df)):
            curr = df.iloc[i]
            prev = df.iloc[i-1]
            date_unix = int(curr['time'].timestamp())
            
            signal = "HOLD"

            # --- STRATEGY LOGIC ---
            if strategy_type == "MOMENTUM":
                if prev['sma_fast'] < prev['sma_slow'] and curr['sma_fast'] > curr['sma_slow']: signal = "BUY"
                elif prev['sma_fast'] > prev['sma_slow'] and curr['sma_fast'] < curr['sma_slow']: signal = "SELL"

            elif strategy_type == "MEAN_REVERSAL":
                if curr['rsi'] < 30 and curr['close'] < curr['bb_lower']: signal = "BUY"
                elif curr['rsi'] > 70 and curr['close'] > curr['bb_upper']: signal = "SELL"
            
            elif strategy_type == "GRID":
                buy_zone = curr['grid_bottom'] + (curr['grid_top'] - curr['grid_bottom']) * 0.2
                sell_zone = curr['grid_top'] - (curr['grid_top'] - curr['grid_bottom']) * 0.2
                if curr['close'] <= buy_zone: signal = "BUY"
                elif curr['close'] >= sell_zone: signal = "SELL"
            
            elif strategy_type == "MULTITIMEFRAME":
                is_uptrend = curr['close'] > curr['ema_trend']
                if is_uptrend and curr['rsi'] < 40: signal = "BUY"
                elif curr['rsi'] > 75: signal = "SELL"

            # --- EXECUTION ---
            if signal == "BUY" and position_size == 0:
                position_size = capital / curr['close']
                capital = 0
                entry_price = curr['close']
                markers.append({'time': date_unix, 'position': 'belowBar', 'color': '#00ff41', 'shape': 'arrowUp', 'text': 'BUY'})

            elif signal == "SELL" and position_size > 0:
                capital = position_size * curr['close']
                pnl = (curr['close'] - entry_price) / entry_price
                trades.append({'pnl_pct': pnl})
                position_size = 0
                markers.append({'time': date_unix, 'position': 'aboveBar', 'color': '#ff0055', 'shape': 'arrowDown', 'text': 'SELL'})
            
            current_equity = capital if position_size == 0 else position_size * curr['close']
            equity_curve.append({'time': date_unix, 'value': current_equity})

        final_equity = capital if position_size == 0 else position_size * df.iloc[-1]['close']
        
        end_price = df.iloc[-1]['close']
        if start_price > 0:
            buy_hold_return_pct = ((end_price - start_price) / start_price) * 100
            buy_hold_final = self.initial_capital * (1 + (buy_hold_return_pct / 100))
        else:
            buy_hold_return_pct = 0
            buy_hold_final = self.initial_capital

        metrics = self.calculate_metrics(trades, final_equity, buy_hold_return_pct, buy_hold_final, equity_curve)
        
        return df.iloc[start_idx:], markers, metrics, equity_curve

    def calculate_metrics(self, trades, final_equity, bh_return, bh_final, equity_curve):
        total_trades = len(trades)
        wins = [t for t in trades if t['pnl_pct'] > 0]
        
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
        net_profit = final_equity - self.initial_capital
        
        # --- NEW: ADVANCED METRICS (Sharpe, Calmar, Drawdown) ---
        equity_values = [e['value'] for e in equity_curve]
        
        # 1. Max Drawdown
        max_drawdown_pct = 0
        if equity_values:
            peak = equity_values[0]
            max_dd = 0
            for val in equity_values:
                if val > peak: peak = val
                dd = (peak - val) / peak
                if dd > max_dd: max_dd = dd
            max_drawdown_pct = max_dd * 100

        # 2. Sharpe Ratio (Simplified: Assuming 0% Risk Free Rate)
        # Convert equity curve to daily returns
        if len(equity_values) > 1:
            series = pd.Series(equity_values)
            returns = series.pct_change().dropna()
            if returns.std() != 0:
                sharpe = (returns.mean() / returns.std()) * np.sqrt(252) # Annualized
            else:
                sharpe = 0
        else:
            sharpe = 0

        # 3. Calmar Ratio (Annualized Return / Max Drawdown)
        # Simple CAGR approximation
        total_return_pct = (net_profit / self.initial_capital)
        calmar = 0
        if max_drawdown_pct > 0:
            # Asumsi periode setahun untuk penyederhanaan display
            calmar = total_return_pct / (max_drawdown_pct / 100)

        return {
            "initial_balance": self.initial_capital,
            "final_balance": round(final_equity, 2),
            "net_profit": round(net_profit, 2),
            "win_rate": round(win_rate, 2),
            "total_trades": total_trades,
            "buy_hold_return": round(bh_return, 2),
            "buy_hold_final": round(bh_final, 2),
            "vs_benchmark": round(((final_equity - bh_final) / bh_final) * 100, 2) if bh_final > 0 else 0,
            
            # New Metrics
            "max_drawdown": round(max_drawdown_pct, 2),
            "sharpe_ratio": round(sharpe, 2),
            "calmar_ratio": round(calmar, 2)
        }

    # --- NEW FEATURE: Signal Advice Generator ---
    def get_signal_advice(self, df, strategy_type):
        """Menghasilkan saran Entry, SL, TP berdasarkan data terakhir"""
        if df is None or df.empty: return None
        
        last = df.iloc[-1]
        atr = last.get('atr', last['close']*0.02) # Fallback 2% jika ATR error
        current_price = last['close']
        
        # Tentukan Arah berdasarkan Strategi (Sederhana)
        # Kita cek ulang logic manual trigger
        action = "WAIT"
        
        # Re-evaluasi logic terakhir untuk menentukan bias
        # Note: Ini simplifikasi, idealnya state posisi disimpan.
        # Disini kita berikan saran level JIKA user mau entry SEKARANG.
        
        tp_price = 0
        sl_price = 0
        
        # Gunakan ATR Multiplier untuk SL/TP
        # Long Setup
        tp_long = current_price + (2 * atr)
        sl_long = current_price - (1 * atr)
        
        # Short Setup
        tp_short = current_price - (2 * atr)
        sl_short = current_price + (1 * atr)
        
        return {
            "price": current_price,
            "atr": atr,
            "setup_long": {"entry": current_price, "tp": tp_long, "sl": sl_long},
            "setup_short": {"entry": current_price, "tp": tp_short, "sl": sl_short}
        }