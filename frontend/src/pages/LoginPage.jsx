import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import '../pages/AuthPages.css';
import { authAPI } from '../utils/api';
import { useAuthStore } from '../store/authStore';

function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [unverified, setUnverified] = useState(false);
  const [resendEmail, setResendEmail] = useState('');
  const [resendSent, setResendSent] = useState(false);
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();

  const handleLogin = async (e) => {
    e.preventDefault();
    setUnverified(false);
    setError('');
    try {
      const response = await authAPI.login(username, password);
      localStorage.setItem('token', response.data.access_token);
      setAuth(true, response.data.access_token);
      navigate('/');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail === 'EMAIL_NOT_VERIFIED') {
        setUnverified(true);
      } else {
        setError(detail || 'Invalid credentials');
      }
    }
  };

  const handleResend = async (e) => {
    e.preventDefault();
    try {
      await authAPI.resendVerification(resendEmail);
      setResendSent(true);
    } catch {}
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>💼 Freelancer Time Tracker</h1>
        <p className="auth-subtitle">Log in to your account</p>
        {error && <div className="error-message">{error}</div>}
        {unverified && (
          <div className="error-message">
            <strong>Email not verified.</strong> Check your inbox for the verification link.
            {!resendSent ? (
              <form onSubmit={handleResend} style={{marginTop:'0.5rem'}}>
                <input
                  type="email"
                  placeholder="Your email address"
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  required
                  style={{marginBottom:'0.4rem'}}
                />
                <button type="submit" style={{width:'100%'}}>Resend verification email</button>
              </form>
            ) : (
              <p style={{marginTop:'0.5rem'}}>A new link has been sent — check your inbox.</p>
            )}
          </div>
        )}
        <form onSubmit={handleLogin}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">Login</button>
        </form>
        <p className="auth-link">
          Don't have an account? <Link to="/register">Register here</Link>
        </p>
        <p className="auth-link">
          <Link to="/forgot-password">Forgot your password?</Link>
        </p>
      </div>
    </div>
  );
}

export default LoginPage;
