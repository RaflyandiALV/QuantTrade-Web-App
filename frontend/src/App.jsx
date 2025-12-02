import { useState } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { FaBitcoin, FaChartLine, FaWallet, FaExchangeAlt, FaRobot, FaSearch } from 'react-icons/fa';

// Registrasi komponen Chart.js
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

function App() {
  const [symbol, setSymbol] = useState('BTC-USD');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState(null);

  // --- Konfigurasi Grafik agar terlihat seperti TradingView (Tema Gelap) ---
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: { display: false }, // Sembunyikan legenda default
      tooltip: {
        backgroundColor: '#1e222d',
        titleColor: '#d1d4dc',
        bodyColor: '#d1d4dc',
        borderColor: '#2a2e39',
        borderWidth: 1,
        padding: 10,
        displayColors: false,
      }
    },
    scales: {
      x: {
        grid: { color: '#2a2e39', drawBorder: false },
        ticks: { color: '#777e91' }
      },
      y: {
        grid: { color: '#2a2e39', drawBorder: false },
        ticks: { color: '#777e91' },
        position: 'right' // Harga di sebelah kanan seperti aplikasi trading
      }
    }
  };

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 1. Ambil Data Grafik Historis
      const chartRes = await axios.get(`http://127.0.0.1:8000/api/chart-data/${symbol}`);
      if (chartRes.data.error) throw new Error(chartRes.data.error);

      // Logika Warna: Hijau jika harga naik, Merah jika turun
      const prices = chartRes.data.prices;
      const isUp = prices[prices.length - 1] >= prices[0];
      const lineColor = isUp ? '#0ecb81' : '#f6465d';
      const areaColor = isUp ? 'rgba(14, 203, 129, 0.1)' : 'rgba(246, 70, 93, 0.1)';

      setChartData({
        labels: chartRes.data.dates,
        datasets: [{
          label: 'Price',
          data: prices,
          borderColor: lineColor,
          backgroundColor: areaColor,
          borderWidth: 2,
          pointRadius: 0,     // Hilangkan titik agar garis terlihat bersih
          pointHoverRadius: 4, // Titik muncul saat di-hover
          fill: true,         // Isi area di bawah garis
          tension: 0.1
        }],
      });

      // 2. Ambil Data Statistik (Simulasi)
      const simRes = await axios.get(`http://127.0.0.1:8000/api/simulate/${symbol}`);
      setStats(simRes.data);

    } catch (err) {
      console.error(err);
      setError(err.message || "Gagal terhubung ke server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container-fluid vh-100 d-flex flex-column">
      
      {/* --- NAVBAR ATAS --- */}
      <nav className="navbar navbar-expand-lg border-bottom border-secondary px-4" style={{backgroundColor: '#1e222d', minHeight: '60px'}}>
        <div className="d-flex align-items-center text-white">
          <FaRobot className="me-2 text-primary" size={24} />
          <span className="fw-bold fs-5">QuantTrade <span className="badge bg-primary ms-2" style={{fontSize: '0.6rem', verticalAlign: 'middle'}}>PRO</span></span>
        </div>
      </nav>

      {/* --- GRID KONTEN UTAMA --- */}
      <div className="row flex-grow-1 g-0">
        
        {/* --- SIDEBAR KIRI (Control Panel) --- */}
        <div className="col-md-3 col-lg-2 d-flex flex-column p-4 border-end border-secondary" style={{backgroundColor: '#131722', minWidth: '250px'}}>
          <h6 className="text-secondary-custom mb-3 fw-bold" style={{fontSize: '0.75rem'}}>MARKET SELECTION</h6>
          
          <div className="mb-4">
            <div className="input-group">
              <span className="input-group-text bg-card border-secondary text-secondary"><FaSearch /></span>
              <input 
                type="text" 
                className="form-control form-control-dark" 
                placeholder="Symbol (e.g. BTC-USD)"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === 'Enter' && handleRunAnalysis()}
              />
            </div>
          </div>

          <h6 className="text-secondary-custom mb-3 fw-bold" style={{fontSize: '0.75rem'}}>STRATEGY CONFIG</h6>
          <div className="card bg-card text-white mb-4 p-3 shadow-sm">
            <div className="d-flex justify-content-between align-items-center mb-2">
                <small className="text-secondary">Strategy Type</small>
                <FaExchangeAlt className="text-secondary" size={12}/>
            </div>
            <div className="fw-bold mb-3" style={{fontSize: '0.9rem'}}>Mean Reversal (RSI + BB)</div>
            
            <small className="text-secondary d-block mb-1">Timeframe</small>
            <div className="fw-bold" style={{fontSize: '0.9rem'}}>1 Day (Daily)</div>
          </div>

          <button 
            className="btn btn-trade w-100 py-2 mt-auto shadow"
            onClick={handleRunAnalysis}
            disabled={loading}
          >
            {loading ? (
                <span><span className="spinner-border spinner-border-sm me-2"></span>Processing...</span>
            ) : 'Run Strategy'}
          </button>

          {error && <div className="alert alert-danger mt-3 py-2 small border-0" style={{backgroundColor: 'rgba(246, 70, 93, 0.1)', color: '#f6465d'}}>{error}</div>}
        </div>

        {/* --- PANEL KANAN (Visualisasi) --- */}
        <div className="col-md-9 col-lg-10 d-flex flex-column p-0">
          
          {/* Baris Statistik Atas */}
          <div className="d-flex border-bottom border-secondary px-4 py-3 align-items-center" style={{backgroundColor: '#131722', gap: '3rem', overflowX: 'auto'}}>
            <div className="d-flex flex-column">
              <span className="stat-label">Asset</span>
              <span className="stat-value text-white d-flex align-items-center">
                {stats ? stats.symbol : symbol}
              </span>
            </div>
            <div className="d-flex flex-column">
              <span className="stat-label">Total Return</span>
              <span className={`stat-value ${stats?.total_return >= 0 ? 'text-green' : 'text-red'}`}>
                {stats ? `${stats.total_return}%` : '--'}
              </span>
            </div>
            <div className="d-flex flex-column">
              <span className="stat-label">Win Rate</span>
              <span className="stat-value text-primary-custom">
                {stats ? `${stats.win_rate}%` : '--'}
              </span>
            </div>
            <div className="d-flex flex-column">
              <span className="stat-label">Total Trades</span>
              <span className="stat-value text-white">
                {stats ? stats.total_trades : '--'}
              </span>
            </div>
            <div className="d-flex flex-column ms-auto">
               <span className="badge bg-card text-secondary border border-secondary py-2 px-3">
                  STATUS: <span className={stats ? "text-green" : "text-secondary"}>{stats ? "ACTIVE" : "READY"}</span>
               </span>
            </div>
          </div>

          {/* Area Grafik Utama */}
          <div className="flex-grow-1 p-3 position-relative" style={{backgroundColor: '#131722'}}>
            {chartData ? (
              <div className="w-100 h-100 bg-card rounded p-3 shadow-sm border border-secondary position-relative">
                <div className="d-flex align-items-center mb-3">
                     <FaBitcoin className="me-2 text-warning" size={20} />
                     <h6 className="text-white m-0">Price Action & Strategy Performance</h6>
                </div>
                <div style={{height: 'calc(100% - 40px)', width: '100%'}}>
                  <Line data={chartData} options={chartOptions} />
                </div>
              </div>
            ) : (
              <div className="w-100 h-100 d-flex flex-column align-items-center justify-content-center text-secondary">
                <FaChartLine size={64} className="mb-3 opacity-25" />
                <h4>Ready to Analyze</h4>
                <p className="text-secondary">Select a symbol from the sidebar and run the strategy.</p>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

export default App;