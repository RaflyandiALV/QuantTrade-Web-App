// File: src/pages/Strategies/ActiveBotsPage.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button, Table, Badge, Spinner, Container } from 'react-bootstrap'; 

const API_BASE_URL = 'http://localhost:8000/api';

const ActiveBotsPage = () => {
  const [bots, setBots] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fungsi untuk mengambil data bot dari FastAPI
  const fetchBots = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/bots/active`);
      setBots(response.data);
      setError(null);
    } catch (err) {
      console.error("Error fetching active bots:", err);
      setError("Gagal mengambil data bot dari server.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBots();
  }, []);

  // Fungsi Interaktif: Mengubah Status Bot (Pause/Run)
  const handleControlBot = async (botId, currentStatus) => {
    const newStatus = currentStatus === 'Running' ? 'Paused' : 'Running';
    
    // Perbarui status secara instan di UI
    setBots(prevBots =>
        prevBots.map(bot =>
            bot.id === botId ? { ...bot, status: newStatus } : bot
        )
    );

    try {
      // Kirim perintah POST ke FastAPI
      await axios.post(`${API_BASE_URL}/bots/${botId}/control`, {
        new_status: newStatus
      });
      // Jika berhasil, status sudah terupdate di UI dan backend.
      
    } catch (err) {
      // Jika gagal, refresh data untuk mengembalikan status yang benar
      console.error(`Gagal mengontrol bot ${botId}:`, err);
      alert(`Gagal mengubah status bot ${botId}. Cek terminal backend.`);
      fetchBots(); 
    }
  };


  if (isLoading) {
    return <Spinner animation="border" className="m-5" />;
  }
  
  if (error) {
      return <Container className="mt-4"><div>Error: {error}</div></Container>;
  }

  return (
    <Container className="mt-4">
      <h2>🤖 Active Trading Bots</h2>
      <p>Control Panel untuk memulai, menghentikan, dan memantau strategi yang sedang berjalan.</p>
      
      <Table striped bordered hover responsive className="mt-4">
        <thead>
          <tr>
            <th>ID</th>
            <th>Strategy Name</th>
            <th>Pair</th>
            <th>Status</th>
            <th>PnL</th>
            <th>Trades</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {bots.map((bot) => (
            <tr key={bot.id}>
              <td>{bot.id}</td>
              <td>{bot.strategy}</td>
              <td>{bot.pair}</td>
              <td>
                <Badge bg={bot.status === 'Running' ? 'success' : 'warning'}>
                    {bot.status}
                </Badge>
              </td>
              <td>{bot.pnl}</td>
              <td>{bot.trades}</td>
              <td>
                <Button 
                  variant={bot.status === 'Running' ? 'danger' : 'success'} 
                  size="sm"
                  onClick={() => handleControlBot(bot.id, bot.status)}
                >
                  {bot.status === 'Running' ? 'Pause' : 'Run'}
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Container>
  );
};

export default ActiveBotsPage;