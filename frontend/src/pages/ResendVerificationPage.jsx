import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import '../pages/AuthPages.css';
import { authAPI } from '../utils/api';

function ResendVerificationPage() {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await authAPI.resendVerification(email);
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong.');
    }
  };

  if (submitted) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h1>💼 Freelancer Time Tracker</h1>
          <div className="success-message">
            If that email is registered and unverified, a new link has been sent. Check your inbox.
          </div>
          <p className="auth-link"><Link to="/login">Back to Login</Link></p>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>💼 Freelancer Time Tracker</h1>
        <p className="auth-subtitle">Resend verification email</p>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Your email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <button type="submit">Send Verification Link</button>
        </form>
        <p className="auth-link"><Link to="/login">Back to Login</Link></p>
      </div>
    </div>
  );
}

export default ResendVerificationPage;
