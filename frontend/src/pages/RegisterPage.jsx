import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../pages/AuthPages.css';
import { authAPI } from '../utils/api';
import HourStackLogo from '../components/HourStackLogo';

function RegisterPage() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [company, setCompany] = useState('');
  const [rate, setRate] = useState('50');
  const [error, setError] = useState('');
  const [registered, setRegistered] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      await authAPI.register(email, username, password, company, parseFloat(rate));
      setRegistered(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    }
  };

  if (registered) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center', marginBottom: '0.5rem' }}>
            <HourStackLogo size={32} />
            <h1 style={{ margin: 0 }}>HourStack</h1>
          </div>
          <div className="success-message">
            Account created! Check your email for a verification link before logging in.
          </div>
          <p className="auth-link"><a href="/login">Go to Login</a></p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center', marginBottom: '0.5rem' }}>
          <HourStackLogo size={32} />
          <h1 style={{ margin: 0 }}>HourStack</h1>
        </div>
        <p className="auth-subtitle">Create your account</p>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleRegister}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
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
          <input
            type="text"
            placeholder="Company Name (optional)"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
          />
          <input
            type="number"
            placeholder="Hourly Rate"
            value={rate}
            onChange={(e) => setRate(e.target.value)}
            min="1"
            step="0.01"
            required
          />
          <button type="submit">Register</button>
        </form>
        <p className="auth-link">
          Already have an account? <Link to="/login">Login here</Link>
        </p>
      </div>
    </div>
  );
}

export default RegisterPage;
