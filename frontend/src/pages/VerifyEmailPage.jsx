import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import '../pages/AuthPages.css';
import { authAPI } from '../utils/api';

function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('loading'); // loading | success | error
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setMessage('Missing verification token.');
      return;
    }
    authAPI.verifyEmail(token)
      .then(() => {
        setStatus('success');
        setMessage('Your email has been verified! You can now log in.');
      })
      .catch((err) => {
        setStatus('error');
        setMessage(err.response?.data?.detail || 'Invalid or expired verification link.');
      });
  }, [searchParams]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>💼 Freelancer Time Tracker</h1>
        {status === 'loading' && <p className="auth-subtitle">Verifying your email…</p>}
        {status === 'success' && (
          <>
            <div className="success-message">{message}</div>
            <p className="auth-link"><Link to="/login">Go to Login</Link></p>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="error-message">{message}</div>
            <p className="auth-link">
              Need a new link? <Link to="/resend-verification">Resend verification email</Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}

export default VerifyEmailPage;
