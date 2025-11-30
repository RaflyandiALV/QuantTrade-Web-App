import axios from 'axios';

// Ganti URL sesuai port FastAPI kamu (biasanya localhost:8000)
const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;