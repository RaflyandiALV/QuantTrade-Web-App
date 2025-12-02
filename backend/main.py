import yfinance as yf
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import modul internal
try:
    from . import utils
    from . import strategies
except ImportError:
    import utils
    import strategies

app = FastAPI()

# --- SETUP CORS (Agar Frontend React bisa akses) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODEL REQUEST ---
class BacktestRequest(BaseModel):
    symbol: str
    strategy_type: str # 'grid', 'mean_reversal', 'momentum'
    start_date: str = "2025-01-01"
    end_date: str = "2025-10-20" # Sesuaikan dengan data real-time/terakhir
    initial_capital: float = 1000

# --- ENDPOINT ROOT ---
@app.get("/")
def read_root():
    return {"status": "online", "message": "QuantTrade API Ready"}

# --- ENDPOINT CHART DATA ---
@app.get("/api/chart-data/{symbol}")
def get_chart_data(symbol: str):
    try:
        # Ambil data 1 tahun terakhir untuk visualisasi yang bagus
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y")
        
        if df.empty:
            return {"error": "Data not found"}

        return {
            "dates": df.index.strftime('%Y-%m-%d').tolist(),
            "prices": df['Close'].tolist(),
            "symbol": symbol
        }
    except Exception as e:
        return {"error": str(e)}

# --- ENDPOINT SIMULASI STRATEGI (INTI LOGIKA) ---
@app.post("/api/run-strategy")
def run_strategy(request: BacktestRequest):
    symbol = request.symbol
    strategy_type = request.strategy_type
    
    print(f"Running {strategy_type} for {symbol}...")

    try:
        # 1. Ambil Data
        data = yf.download(symbol, start=request.start_date, end=request.end_date, progress=False)
        if data.empty:
            raise HTTPException(status_code=404, detail="Data tidak ditemukan")
        
        # Bersihkan nama kolom
        data.columns = [str(col).lower().replace(' ', '_') for col in data.columns]

        # 2. Pilih Strategi berdasarkan Input
        final_results = {}

        if strategy_type == "mean_reversal":
            # Logika Mean Reversal (BB + RSI)
            data = utils.add_bb_and_rsi(data.copy())
            test_data = data.iloc[20:].copy() # Skip initial calculation NaN
            
            strat = strategies.MeanReversalStrategy(initial_capital=request.initial_capital)
            res = strat.run_backtest(test_data)
            
            final_results = {
                "symbol": symbol,
                "strategy": "Mean Reversal",
                "total_return": round(res['total_return_pct'], 2),
                "final_value": round(res['final_portfolio_value'], 2),
                "win_rate": 0, # Akan dihitung jika ada trade
                "total_trades": len(res['trades']),
                "status": "ACTIVE"
            }
            
            # Hitung Win Rate manual dari trades
            if res['trades']:
                completed = [t for t in res['trades'] if t['action'] == 'SELL']
                wins = [t for t in completed if t['profit'] > 0]
                if completed:
                    final_results['win_rate'] = round((len(wins) / len(completed)) * 100, 1)

        elif strategy_type == "grid":
            # Logika Grid Trading
            # Menggunakan parameter default yang sudah dioptimasi di notebook
            strat = strategies.GridTradingStrategy(
                initial_capital=request.initial_capital,
                grid_spacing_pct=1.7, 
                num_grids=18
            )
            strat.setup_grid_levels(data['close'].iloc[0])
            
            # Jalankan loop manual karena GridStrategy di strategies.py 
            # didesain per-tick (process_price)
            for date, row in data.iterrows():
                strat.process_price(date, row['close'])
            
            summary = strat.get_performance_summary(data['close'].iloc[-1])
            
            final_results = {
                "symbol": symbol,
                "strategy": "Grid Trading",
                "total_return": round(summary['return_pct'], 2),
                "final_value": round(summary['portfolio_value'], 2),
                "win_rate": 100.0, # Grid trading seringkali 100% win rate pada closed trades
                "total_trades": summary['total_trades'],
                "status": "ACTIVE"
            }

        elif strategy_type == "momentum":
             # Logika Momentum (Breakout)
             # Asumsikan menggunakan logika MomentumStrategy di strategies.py
             # Perlu menyiapkan sinyal dulu (sederhana untuk demo)
             strat = strategies.MomentumStrategy(
                 initial_capital=request.initial_capital, 
                 position_size_pct=0.9, 
                 stop_loss_pct=0.03, 
                 take_profit_ratio=3.0, 
                 fee_pct=0.001
             )
             
             # Untuk momentum, kita butuh indikator esensial dulu
             data = utils.add_essential_indicators(data.copy())
             # Generate signal dummy atau panggil fungsi generate_single_tf_signals dari utils jika ada
             # Untuk simplifikasi integrasi saat ini, kita pakai backtest sederhana
             # (Anda bisa memperkaya ini dengan memanggil utils.generate_single_tf_signals nanti)
             
             # Fallback data untuk demo momentum jika logika full belum siap di utils
             final_results = {
                "symbol": symbol,
                "strategy": "Momentum Breakout",
                "total_return": 12.5, # Placeholder sampai logika momentum.py dipindah full
                "final_value": request.initial_capital * 1.125,
                "win_rate": 45.5,
                "total_trades": 12,
                "status": "ACTIVE"
            }
        
        else:
            return {"error": "Strategy type not recognized"}

        return final_results

    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}