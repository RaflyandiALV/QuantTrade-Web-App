// File: src/components/layout/MainLayout.jsx
// (Menggunakan React Bootstrap untuk Fix Styling)

import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { LayoutDashboard, LineChart, Cpu, History } from 'lucide-react';
// Import komponen dari React-Bootstrap
import { Container, Row, Col, Nav, Navbar } from 'react-bootstrap'; 

const MainLayout = () => {
  return (
    <Container fluid style={{ padding: 0, minHeight: '100vh' }}>
      <Row className="flex-nowrap">
        {/* Sidebar Sederhana (Menggunakan Col dan Nav) */}
        <Col xs={4} md={3} lg={2} className="bg-light border-end d-none d-md-block p-0">
          <div className="d-flex flex-column align-items-center align-items-sm-start px-3 pt-2 text-dark min-vh-100">
            <Navbar.Brand 
                as={Link} 
                to="/" 
                className="d-flex align-items-center pb-3 mb-md-3 me-md-auto text-decoration-none border-bottom w-100"
            >
              <span className="fs-5 fw-bold text-primary">QuantPlatform</span>
            </Navbar.Brand>
            
            <Nav className="flex-column mb-auto w-100" defaultActiveKey="/">
                <Nav.Link as={Link} to="/" className="text-dark py-2 d-flex align-items-center">
                    <LayoutDashboard size={20} className="me-2" /> Dashboard
                </Nav.Link>
                <Nav.Link as={Link} to="/market" className="text-dark py-2 d-flex align-items-center">
                    <LineChart size={20} className="me-2" /> Market Data
                </Nav.Link>
                <Nav.Link as={Link} to="/strategies" className="text-dark py-2 d-flex align-items-center">
                    <Cpu size={20} className="me-2" /> Active Bots
                </Nav.Link>
                <Nav.Link as={Link} to="/history" className="text-dark py-2 d-flex align-items-center">
                    <History size={20} className="me-2" /> Trade Logs
                </Nav.Link>
            </Nav>
          </div>
        </Col>

        {/* Konten Halaman Utama (Outlet akan menampilkan DashboardPage, ActiveBotsPage, dll.) */}
        <Col className="py-3">
          <Outlet />
        </Col>
      </Row>
    </Container>
  );
};

export default MainLayout;