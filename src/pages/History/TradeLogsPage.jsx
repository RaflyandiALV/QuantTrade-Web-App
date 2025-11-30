// File: src/pages/History/TradeLogsPage.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Table, Spinner, Container } from 'react-bootstrap'; 

const API_BASE_URL = 'http://localhost:8000/api';

const TradeLogsPage = () => {
    const [logs, setLogs] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchTradeLogs = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/trades/logs`);
                setLogs(response.data);
                setError(null);
            } catch (err) {
                console.error("Error fetching trade logs:", err);
                setError("Gagal mengambil log transaksi dari server.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchTradeLogs();
    }, []);

    if (isLoading) {
        return <Spinner animation="border" className="m-5" />;
    }
    
    if (error) {
        return <Container className="mt-4"><div>Error: {error}</div></Container>;
    }

    return (
        <Container className="mt-4">
            <h2>📜 Trade Logs ({logs.length} Total Trades)</h2>
            <p>Riwayat transaksi yang dieksekusi oleh semua bot.</p>
            
            <Table striped bordered hover responsive size="sm" className="mt-4">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Time</th>
                        <th>Pair</th>
                        <th>Type</th>
                        <th>Price</th>
                        <th>Qty</th>
                        <th>P&L (USD)</th>
                    </tr>
                </thead>
                <tbody>
                    {logs.map((log) => (
                        <tr key={log.id} className={log.pnl > 0 ? 'table-success' : 'table-danger'}>
                            <td>{log.id}</td>
                            <td>{log.time}</td>
                            <td>{log.pair}</td>
                            <td><strong>{log.type}</strong></td>
                            <td>{log.price.toFixed(2)}</td>
                            <td>{log.qty.toFixed(3)}</td>
                            <td><strong>{log.pnl.toFixed(2)}</strong></td>
                        </tr>
                    ))}
                </tbody>
            </Table>
        </Container>
    );
};

export default TradeLogsPage;