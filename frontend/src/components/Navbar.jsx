import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

function Navbar() {
  const { logout } = useAuthStore();
  const navigate = useNavigate();

  return (
    <nav className="navbar">
      <h1 onClick={() => navigate('/')}>💼 Time Tracker</h1>
      <button onClick={() => { logout(); navigate('/login'); }}>Logout</button>
    </nav>
  );
}

export default Navbar;
