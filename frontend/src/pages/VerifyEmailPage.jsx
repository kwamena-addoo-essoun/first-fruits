import React, { useState, useEffect, useRef } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import '../pages/AuthPages.css';
import { authAPI } from '../utils/api';

function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('loading'); // loading | success | error
  const [message, setMessage] = useState('');
  const [countdown, setCountdown] = useState(5);
  const navigate = useNavigate();
  const calledRef = useRef(false);

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setMessage('Missing verification token.');
      return;
    }
    authAPI.verifyEmail(token)
      .then(() => {
        setStatus('success');
        setMessage('Your email has been verified! Redirecting to login…');
      })
      .catch((err) => {
        setStatus('error');
        setMessage(err.response?.data?.detail || 'Invalid or expired verification link.');
      });
  }, [searchParams]);

  // Auto-redirect to /login after successful verification
  useEffect(() => {
    if (status !== 'success') return;
    if (countdown <= 0) {
      navigate('/login');
      return;
    }
    const timer = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(timer);
  }, [status, countdown, navigate]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>⏱️ HourStack</h1>
        {status === 'loading' && <p className="auth-subtitle">Verifying your email…</p>}
        {status === 'success' && (
          <>
            <div className="success-message">{message}</div>
            <p className="auth-link">
              Redirecting in {countdown}s… <Link to="/login">Go now</Link>
            </p>
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
