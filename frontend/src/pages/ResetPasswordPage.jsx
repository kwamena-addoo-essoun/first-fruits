import React, { useState } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import '../pages/AuthPages.css';
import { authAPI } from '../utils/api';

function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    try {
      await authAPI.resetPassword(token, password);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid or expired reset link.');
    }
  };

  if (!token) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h1>💼 Freelancer Time Tracker</h1>
          <p className="auth-subtitle" style={{ color: '#721c24' }}>
            Missing reset token. Use the link from your email.
          </p>
          <p className="auth-link"><Link to="/forgot-password">Request a new link</Link></p>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h1>💼 Freelancer Time Tracker</h1>
          <p className="auth-subtitle">Password updated!</p>
          <p style={{ textAlign: 'center', color: '#444' }}>
            Redirecting to login…
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>💼 Freelancer Time Tracker</h1>
        <p className="auth-subtitle">Choose a new password</p>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <input
            type="password"
            placeholder="New password (min 8 characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Confirm new password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
          />
          <button type="submit">Set New Password</button>
        </form>
        <p className="auth-link">
          <Link to="/login">Back to login</Link>
        </p>
      </div>
    </div>
  );
}

export default ResetPasswordPage;
