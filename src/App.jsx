import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
// PASTIKAN PATH INI BENAR:
import MainLayout from './components/layout/MainLayout';
import DashboardPage from './pages/Dashboard/DashboardPage';
import TradeLogsPage from './pages/History/TradeLogsPage';
import MarketDataPage from './pages/MarketData/MarketDataPage';
import ActiveBotsPage from './pages/Strategies/ActiveBotsPage';

// Placeholder Pages (Jika kamu belum membuat file MarketPage, StrategyPage, HistoryPage,
// pastikan kamu mendeklarasikannya di App.jsx seperti ini!)
const MarketPage = () => <div>Market Data Page</div>;
const StrategyPage = () => <div>Strategy Control Page</div>;
const HistoryPage = () => <div>Trade History Page</div>;

function App() {
  return (
    <BrowserRouter>
      {/* Cek tag div penutup ini */}
      <div className="min-h-screen bg-gray-100 p-4">
        <h1 className="text-3xl font-extrabold text-indigo-700 mb-6 border-b pb-2">
          Vite Tailwind Test
        </h1>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="market" element={<MarketDataPage />} />
            <Route path="strategies" element={<ActiveBotsPage />} />
            <Route path="history" element={<TradeLogsPage />} />
          </Route>
        </Routes>
      </div>
      {/* Cek tag div penutup ini */}
    </BrowserRouter>
  );
}

export default App;