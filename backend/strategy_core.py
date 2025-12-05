# backend/strategy_core.py
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class TradingEngine:
    def __init__(self, initial_capital=10000):
        self.initial_capital = float(initial_capital)

    def fetch_data(self, symbol, requested_period="1y", interval="1d", start_date=None, end_date=None):
        """
        LOGIKA PERBAIKAN: 
        Selalu fetch data 'MAX' atau '2y' untuk memastikan indikator (EMA200, dll) 
        memiliki data warm-up yang cukup, terlepas dari periode yang diminta user.
        """
        try:
            # 1. Tentukan Fetch Period (Selalu Ambil Lebih Banyak untuk Warm-up)
            fetch_period = "max" # Default untuk daily
            if interval in ['1h', '90m', '4h']:
                fetch_period = "730d" # Limit Yahoo untuk intraday ~2 tahun
            
            # Jika user minta custom range, kita abaikan fetch_period dan pakai range
            # TAPI, idealnya kita tarik mundur start_date 200 candle untuk warm up.
            # Untuk simplifikasi & konsistensi scanner, kita pakai logika fetch_period luas.

            print(f"📥 [CORE] Fetching FULL Data for Warmup: {symbol} ({interval} | Raw: {fetch_period})")
            
            # Download data mentah (Full History)
            df = yf.download(symbol, period=fetch_period, interval=interval, progress=False, auto_adjust=True, timeout=30)
            
            if df.empty: return None

            # Fix MultiIndex Column issue
            if isinstance(df.columns, pd.MultiIndex):
                try:
                    if 'Close' in df.columns.get_level_values(0):
                        df.columns = df.columns.get_level_values(0)
                    else:
                        df.columns = [col[0] for col in df.columns]
                except: pass

            df = df.reset_index()
            df.columns = [str(c).lower() for c in df.columns]
            
            # Standardize Time Column
            if 'date' in df.columns: df.rename(columns={'date': 'time'}, inplace=True)
            elif 'datetime' in df.columns: df.rename(columns={'datetime': 'time'}, inplace=True)

            # Ensure timezone naive for calculations
            if pd.api.types.is_datetime64_any_dtype(df['time']):
                df['time'] = df['time'].dt.tz_localize(None)

            return df

        except Exception as e:
            print(f"❌ Data Error {symbol}: {e}")
            return None

    def prepare_indicators(self, df):
        """Menghitung indikator pada SELURUH data yang tersedia"""
        if len(df) < 50: return df

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

        # 4. MULTITIMEFRAME (EMA Trend) - INI PENYEBAB BUG UTAMA SEBELUMNYA
        # EMA 200 butuh setidaknya 200 bar, idealnya 600+ bar untuk akurat
        df['ema_trend'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # 5. ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()

        df.fillna(0, inplace=True)
        return df

    def slice_data_by_period(self, df, period, start_date=None, end_date=None):
        """Memotong data SETELAH indikator dihitung, agar sesuai permintaan user"""
        if df is None or df.empty: return df
        
        cutoff_date = None
        now = datetime.now()

        if start_date and end_date:
            # Custom Range
            try:
                s_date = pd.to_datetime(start_date).replace(tzinfo=None)
                e_date = pd.to_datetime(end_date).replace(tzinfo=None)
                mask = (df['time'] >= s_date) & (df['time'] <= e_date)
                return df.loc[mask].copy()
            except:
                pass # Fallback ke logic period

        # Logic Period String
        if period == "1mo": cutoff_date = now - timedelta(days=30)
        elif period == "3mo": cutoff_date = now - timedelta(days=90)
        elif period == "6mo": cutoff_date = now - timedelta(days=180)
        elif period == "1y": cutoff_date = now - timedelta(days=365)
        elif period == "2y": cutoff_date = now - timedelta(days=730)
        elif period == "5y": cutoff_date = now - timedelta(days=1825)
        elif period == "max": return df # Return all

        if cutoff_date:
            mask = df['time'] >= cutoff_date
            sliced_df = df.loc[mask].copy()
            # Safety check: kalau hasil slice kosong (misal data cuma ada 1 minggu tapi minta 1 tahun), return full
            if sliced_df.empty: return df
            return sliced_df
        
        return df

    def run_backtest(self, raw_df, strategy_type, requested_period="1y", start_date=None, end_date=None):
        # 1. HITUNG INDIKATOR PADA DATA FULL (Warm-up Correct)
        full_df = self.prepare_indicators(raw_df.copy())
        
        # 2. POTONG DATA SESUAI PERMINTAAN USER (Slice)
        # Logika trading hanya berjalan pada periode yang dilihat user, 
        # TAPI indikator sudah matang dari data masa lalu.
        df = self.slice_data_by_period(full_df, requested_period, start_date, end_date)
        
        capital = self.initial_capital
        position_size = 0 
        entry_price = 0
        
        markers = [] 
        trades = []
        equity_curve = []
        
        if df.empty or len(df) < 5:
            return df, [], self.calculate_metrics([], capital, 0, capital, []), []

        start_price = df.iloc[0]['close']
        
        # Reset Index agar iterasi mulus
        df = df.reset_index(drop=True)

        for i in range(1, len(df)):
            curr = df.iloc[i]
            prev = df.iloc[i-1]
            date_unix = int(curr['time'].timestamp())
            
            signal = "HOLD"

            # --- STRATEGY LOGIC (Konsisten dengan Scanner) ---
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
                # Logic: Harga di atas EMA200 (Uptrend) + RSI Oversold
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
        
        return df, markers, metrics, equity_curve

    def calculate_metrics(self, trades, final_equity, bh_return, bh_final, equity_curve):
        total_trades = len(trades)
        wins = [t for t in trades if t['pnl_pct'] > 0]
        
        win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
        net_profit = final_equity - self.initial_capital
        
        equity_values = [e['value'] for e in equity_curve]
        
        # Max Drawdown
        max_drawdown_pct = 0
        if equity_values:
            peak = equity_values[0]
            max_dd = 0
            for val in equity_values:
                if val > peak: peak = val
                dd = (peak - val) / peak
                if dd > max_dd: max_dd = dd
            max_drawdown_pct = max_dd * 100

        # Sharpe Ratio
        if len(equity_values) > 1:
            series = pd.Series(equity_values)
            returns = series.pct_change().dropna()
            if returns.std() != 0:
                sharpe = (returns.mean() / returns.std()) * np.sqrt(252) 
            else:
                sharpe = 0
        else:
            sharpe = 0

        # Calmar Ratio
        total_return_pct = (net_profit / self.initial_capital)
        calmar = 0
        if max_drawdown_pct > 0:
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
            "max_drawdown": round(max_drawdown_pct, 2),
            "sharpe_ratio": round(sharpe, 2),
            "calmar_ratio": round(calmar, 2)
        }

    def get_signal_advice(self, df, strategy_type):
        """Menghasilkan saran Entry, SL, TP berdasarkan data terakhir"""
        if df is None or df.empty: return None
        
        last = df.iloc[-1]
        atr = last.get('atr', last['close']*0.02) 
        current_price = last['close']
        
        tp_long = current_price + (2 * atr)
        sl_long = current_price - (1 * atr)
        
        tp_short = current_price - (2 * atr)
        sl_short = current_price + (1 * atr)
        
        return {
            "price": current_price,
            "atr": atr,
            "setup_long": {"entry": current_price, "tp": tp_long, "sl": sl_long},
            "setup_short": {"entry": current_price, "tp": tp_short, "sl": sl_short}
        }