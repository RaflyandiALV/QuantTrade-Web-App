// File: src/pages/MarketData/MarketDataPage.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Table, Spinner, Container } from 'react-bootstrap'; 

const API_BASE_URL = 'http://localhost:8000/api';

const MarketDataPage = () => {
    const [data, setData] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchMarketData = async () => {
            try {
                // Mengambil data untuk BTC/USDT
                const response = await axios.get(`${API_BASE_URL}/market/history?ticker=BTC/USDT`); 
                setData(response.data);
                setError(null);
            } catch (err) {
                console.error("Error fetching market data:", err);
                setError("Gagal mengambil data pasar dari server.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchMarketData();
    }, []);

    if (isLoading) {
        return <Spinner animation="border" className="m-5" />;
    }
    
    if (error) {
        return <Container className="mt-4"><div>Error: {error}</div></Container>;
    }

    return (
        <Container className="mt-4">
            <h2>📈 Market Data (BTC/USDT)</h2>
            <p>Data harga historis (OHLCV) yang digunakan untuk analisis.</p>
            
            <Table striped bordered hover responsive size="sm" className="mt-4">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Open</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Close</th>
                        <th>Volume</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((point, index) => (
                        <tr key={index}>
                            <td>{point.timestamp}</td>
                            <td>{point.open.toFixed(2)}</td>
                            <td>{point.high.toFixed(2)}</td>
                            <td>{point.low.toFixed(2)}</td>
                            <td>{point.close.toFixed(2)}</td>
                            <td>{point.volume.toLocaleString()}</td>
                        </tr>
                    ))}
                </tbody>
            </Table>
        </Container>
    );
};

export default MarketDataPage;