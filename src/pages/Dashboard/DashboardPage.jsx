import React, { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import StatCard from "../../components/ui/StatCard"; // Path sudah benar

// Data dummy untuk inisialisasi sebelum fetch
const initialStats = [
  { title: "Total Equity", value: "$0.00", change: "N/A", isPositive: true },
  { title: "Strategy Win Rate", value: "0%", change: "N/A", isPositive: true },
  { title: "Open Positions", value: "0", change: "N/A", isPositive: true },
];

const initialEquityData = [{ day: "Mon", value: 0 }];

const DashboardPage = () => {
  const [stats, setStats] = useState(initialStats);
  const [equityData, setEquityData] = useState(initialEquityData);
  const [loading, setLoading] = useState(true);
  const API_URL = "http://localhost:8000/api/dashboard"; // Pastikan FastAPI berjalan di port 8000

  // Fungsi untuk mengambil data dari FastAPI
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Ambil data Stat Card
        const statsResponse = await fetch(`${API_URL}/summary`);
        const fetchedStats = await statsResponse.json();
        setStats(fetchedStats);

        // Ambil data Equity Curve
        const equityResponse = await fetch(`${API_URL}/equity_curve`);
        const fetchedEquity = await equityResponse.json();
        setEquityData(fetchedEquity);

        setLoading(false);
      } catch (error) {
        console.error("Gagal mengambil data dari FastAPI:", error);
        setLoading(false);
        // Biarkan data dummy jika gagal
      }
    };
    fetchDashboardData();
  }, []);

  if (loading) {
    return <div style={{ fontSize: '24px' }}>Loading Data...</div>; // Style mentah, tapi berfungsi
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Real-Time Portfolio Dashboard</h1>
      
      {/* Stat Cards (Data Ringkasan) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {stats.map((stat, index) => (
          <StatCard key={index} {...stat} />
        ))}
      </div>

      {/* Equity Curve Chart */}
      <div className="bg-white p-6 shadow-md rounded-lg">
        <h2 className="text-xl font-semibold mb-4">Equity Curve (Last 5 Days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={equityData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ccc" />
            <XAxis dataKey="day" />
            <YAxis 
              domain={['auto', 'auto']}
              tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`} // Format ke Ribuan Dolar
            />
            <Tooltip formatter={(value) => [`$${value.toFixed(2)}`, 'Equity Value']} />
            <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DashboardPage;