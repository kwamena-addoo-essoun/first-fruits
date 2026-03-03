import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import Navbar from './components/Navbar';
import Toast from './components/Toast';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import ProjectPage from './pages/ProjectPage';
import TimeLogPage from './pages/TimeLogPage';
import InvoicePage from './pages/InvoicePage';
import ClientsPage from './pages/ClientsPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import AdminPage from './pages/AdminPage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import ResendVerificationPage from './pages/ResendVerificationPage';
import BillingPage from './pages/BillingPage';
import LandingPage from './pages/LandingPage';
import { useAuthStore } from './store/authStore';
import { userAPI } from './utils/api';

function App() {
  const { isAuthenticated, isAdmin, validateStoredToken, setPlan } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = validateStoredToken();
    if (token) {
      userAPI.getMe()
        .then((res) => setPlan(res.data.plan))
        .catch(() => {});
    }
    setIsLoading(false);
  }, [validateStoredToken, setPlan]);

  if (isLoading) return <div className="loading">Loading...</div>;

  return (
    <Router>
      <div className="app">
        <Navbar />
        <Toast />
        <main className="main-content">
          <Routes>
            <Route path="/" element={isAuthenticated ? <DashboardPage /> : <LandingPage />} />
            <Route path="/login" element={!isAuthenticated ? <LoginPage /> : <Navigate to="/" />} />
            <Route path="/register" element={!isAuthenticated ? <RegisterPage /> : <Navigate to="/" />} />
            <Route path="/projects" element={isAuthenticated ? <ProjectPage /> : <Navigate to="/login" />} />
            <Route path="/timelogs" element={isAuthenticated ? <TimeLogPage /> : <Navigate to="/login" />} />
            <Route path="/invoices" element={isAuthenticated ? <InvoicePage /> : <Navigate to="/login" />} />
            <Route path="/clients" element={isAuthenticated ? <ClientsPage /> : <Navigate to="/login" />} />
            <Route path="/billing" element={isAuthenticated ? <BillingPage /> : <Navigate to="/login" />} />
            <Route path="/forgot-password" element={!isAuthenticated ? <ForgotPasswordPage /> : <Navigate to="/" />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            <Route path="/resend-verification" element={<ResendVerificationPage />} />
            <Route path="/admin" element={isAuthenticated && isAdmin ? <AdminPage /> : <Navigate to="/" />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
