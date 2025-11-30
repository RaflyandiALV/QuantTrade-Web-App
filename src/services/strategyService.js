import api from './api';

export const startStrategy = async (strategyType, params) => {
  // strategyType contoh: "grid_trading", "mean_reversal"
  const response = await api.post('/strategy/start', { 
    type: strategyType, 
    ...params 
  });
  return response.data;
};