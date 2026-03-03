import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import '../pages/AuthPages.css';
import { authAPI } from '../utils/api';
import { useAuthStore } from '../store/authStore';
import HourStackLogo from '../components/HourStackLogo';

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
    <div className="auth-split-container">
      {/* Left branding panel */}
      <div className="auth-split-left">
        <div className="auth-split-brand">
          <HourStackLogo size={64} />
          <h1>HourStack</h1>
          <p>Track your hours, invoice clients,<br/>and own your time.</p>
          <div className="auth-split-dots">
            <span className="active"></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="auth-split-right">
        <div className="auth-split-form">
          <h2>Welcome back</h2>
          <p className="auth-subtitle">Sign in to your account</p>

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
                  <button type="submit">Resend verification email</button>
                </form>
              ) : (
                <p style={{marginTop:'0.5rem'}}>A new link has been sent — check your inbox.</p>
              )}
            </div>
          )}

          <form onSubmit={handleLogin}>
            <div className="field-group">
              <label className="field-label">Username</label>
              <input
                type="text"
                placeholder="your_username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="field-group">
              <label className="field-label">Password</label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit">Sign in →</button>
          </form>

          <p className="auth-link">
            Don't have an account? <Link to="/register">Register here</Link>
          </p>
          <p className="auth-link">
            <Link to="/forgot-password">Forgot your password?</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
