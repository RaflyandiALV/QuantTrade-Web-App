# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from strategy_core import TradingEngine
import pandas as pd
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

SECTORS = {
    "BIG_CAP": ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "AVAX-USD"],
    "AI_COINS": ["FET-USD", "RENDER-USD", "NEAR-USD", "ICP-USD", "GRT-USD", "TAO-USD"],
    "MEME_COINS": ["DOGE-USD", "SHIB-USD", "PEPE-USD", "WIF-USD", "BONK-USD", "FLOKI-USD"],
    "EXCHANGE_TOKENS": ["BNB-USD", "OKB-USD", "KCS-USD", "CRO-USD", "LEO-USD"],
    "DEX_DEFI": ["UNI-USD", "CAKE-USD", "AAVE-USD", "MKR-USD", "LDO-USD", "CRV-USD"],
    "LAYER_2": ["MATIC-USD", "ARB-USD", "OP-USD", "IMX-USD", "MNT-USD"],
    "US_TECH": ["NVDA", "TSLA", "AAPL", "MSFT", "AMD", "META", "GOOG"]
}

class StrategyRequest(BaseModel):
    symbol: str
    strategy: str
    capital: float
    timeframe: str = "1d"
    period: str = "1y"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ScanRequest(BaseModel):
    sector: str
    timeframe: str = "1d" # Ini akan jadi preferensi dasar, tapi kita akan scan variasi
    period: str = "1y" 
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    capital: float = 10000

def analyze_market_reason(best_strat, win_rate):
    if best_strat == "HOLD ONLY": return "🚀 Parabolic Run (Buy & Hold)"
    elif best_strat == "MOMENTUM": return "📈 Strong Uptrend"
    elif best_strat == "MULTITIMEFRAME": return "✅ Trend Confirmation"
    elif best_strat == "GRID": return "〰️ Ranging / Volatile"
    elif best_strat == "MEAN_REVERSAL": return "🔄 Reversal / Bounce"
    else: return "❓ Unclear"

@app.post("/api/run-backtest")
def run_backtest(req: StrategyRequest):
    engine = TradingEngine(initial_capital=req.capital)
    df = engine.fetch_data(req.symbol, period=req.period, interval=req.timeframe, start_date=req.start_date, end_date=req.end_date)
    
    if df is None or len(df) < 30:
        raise HTTPException(status_code=404, detail=f"Data kurang untuk {req.symbol}.")

    df_res, markers, metrics, equity_data = engine.run_backtest(df, req.strategy)
    
    chart_data = []
    line1, line2, line3 = [], [], []
    
    for index, row in df_res.iterrows():
        if pd.isna(row['close']): continue
        t = int(row['time'].timestamp())
        chart_data.append({ "time": t, "open": row['open'], "high": row['high'], "low": row['low'], "close": row['close'] })
        
        if req.strategy == "MOMENTUM":
            line1.append({"time": t, "value": row['sma_fast']})
            line2.append({"time": t, "value": row['sma_slow']})
        elif req.strategy in ["MEAN_REVERSAL", "GRID"]:
            line1.append({"time": t, "value": row['bb_upper'] if req.strategy == "MEAN_REVERSAL" else row['grid_top']})
            line2.append({"time": t, "value": row['bb_lower'] if req.strategy == "MEAN_REVERSAL" else row['grid_bottom']})
            if req.strategy == "GRID": line3.append({"time": t, "value": row['grid_mid']})
        elif req.strategy == "MULTITIMEFRAME":
            line3.append({"time": t, "value": row['ema_trend']})

    return {
        "status": "success",
        "chart_data": chart_data,
        "equity_curve": equity_data,
        "indicators": {"line1": line1, "line2": line2, "line3": line3},
        "markers": markers,
        "metrics": metrics
    }

@app.post("/api/compare-strategies")
def compare_strategies(req: StrategyRequest):
    engine = TradingEngine(initial_capital=req.capital)
    df = engine.fetch_data(req.symbol, period=req.period, interval=req.timeframe, start_date=req.start_date, end_date=req.end_date)
    
    if df is None or len(df) < 30: raise HTTPException(status_code=404, detail="Data Error")

    results = []
    strategies = ["MOMENTUM", "MEAN_REVERSAL", "GRID", "MULTITIMEFRAME"]
    
    for strat in strategies:
        _, _, metrics, _ = engine.run_backtest(df.copy(), strat)
        results.append({
            "strategy": strat,
            "net_profit": metrics['net_profit'],
            "win_rate": metrics['win_rate'],
            "trades": metrics['total_trades'],
            "sharpe": metrics.get('sharpe_ratio', 0),
            "is_hold": False
        })
    
    hold_return_pct = metrics['buy_hold_return']
    hold_profit_usd = req.capital * (hold_return_pct / 100)
    
    results.append({
        "strategy": "HOLD ONLY",
        "net_profit": round(hold_profit_usd, 2),
        "win_rate": 100 if hold_profit_usd > 0 else 0,
        "trades": 1,
        "sharpe": 0,
        "is_hold": True
    })
        
    results.sort(key=lambda x: x['net_profit'], reverse=True)
    return {"symbol": req.symbol, "comparison": results}

# --- UPDATED: SMART SCANNER (Multi-TF & Elite Signals) ---
@app.post("/api/scan-market")
def scan_market(req: ScanRequest):
    if req.sector == "ALL":
        symbols = []
        for s in SECTORS.values(): symbols.extend(s)
        symbols = list(set(symbols))[:15] # Limit demi performa
    else:
        symbols = SECTORS.get(req.sector, [])
    
    if not symbols: raise HTTPException(status_code=404, detail="Sektor tidak ditemukan")
    
    engine = TradingEngine(initial_capital=req.capital)
    strategies = ["MOMENTUM", "MEAN_REVERSAL", "GRID", "MULTITIMEFRAME"]
    
    # SETUP SMART SCANNING LOOP
    # Kita akan scan kombinasi Timeframe untuk mendapatkan hasil terbaik
    # Prioritas: 1h > 4h > 1d (jika profit beda tipis, ambil TF lebih kecil)
    scan_tf_options = ["1h", "4h", "1d"] # Timeframe yang diuji
    # Period yang diuji disederhanakan agar tidak timeout (misal 6mo dan 1y)
    scan_periods = ["6mo", "1y"] 
    
    scan_results = []
    elite_signals = [] # Menampung kandidat > 70% Winrate

    for sym in symbols:
        best_config = None
        best_profit = -999999999
        
        # Loop Timeframe & Period Combination
        for tf in scan_tf_options:
            for per in scan_periods:
                # Fetch data
                df = engine.fetch_data(sym, period=per, interval=tf)
                if df is None or len(df) < 40: continue
                
                # Test Strategy
                for strat in strategies:
                    _, _, metrics, _ = engine.run_backtest(df.copy(), strat)
                    
                    # Logic Pemilihan: Cari Profit Maksimal
                    if metrics['net_profit'] > best_profit:
                        best_profit = metrics['net_profit']
                        
                        # Get Signal Info (Advice)
                        signal_info = engine.get_signal_advice(df, strat)
                        
                        best_config = {
                            "symbol": sym,
                            "timeframe": tf,
                            "period": per,
                            "strategy": strat,
                            "profit": metrics['net_profit'],
                            "win_rate": metrics['win_rate'],
                            "trades": metrics['total_trades'],
                            "sharpe": metrics['sharpe_ratio'],
                            "calmar": metrics['calmar_ratio'],
                            "signal_data": signal_info # Entry, SL, TP
                        }
        
        if best_config:
            # Bandingkan dengan HOLD di konfigurasi terbaik
            # (Simplified: Kita anggap strategi terbaik sudah dipilih diatas)
            reason = analyze_market_reason(best_config['strategy'], best_config['win_rate'])
            best_config['reason'] = reason
            
            scan_results.append(best_config)

            # FILTER ELITE SIGNALS (>70% Winrate & Min 5 Trades)
            if best_config['win_rate'] >= 70 and best_config['trades'] >= 5:
                elite_signals.append(best_config)

    # Sorting Elite Signals:
    # 1. Win Rate (Desc)
    # 2. Total Trades (Desc) -> Preferensi user: makin banyak trade makin bagus
    elite_signals.sort(key=lambda x: (x['win_rate'], x['trades']), reverse=True)
    top_5_signals = elite_signals[:5]

    return {
        "sector": req.sector, 
        "results": scan_results,
        "elite_signals": top_5_signals # List top 5 untuk UI
    }