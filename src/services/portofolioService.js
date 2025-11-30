import api from './api';

export const getPortfolioStatus = async () => {
  // Mengambil data balance dan posisi terbuka
  const response = await api.get('/portfolio'); 
  return response.data;
};

export const getTradeHistory = async () => {
  // Mengambil log history trading
  const response = await api.get('/trade_history');
  return response.data;
};