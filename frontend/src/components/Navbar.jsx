import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import HourStackLogo from './HourStackLogo';
import './Navbar.css';

function Navbar() {
  const { isAuthenticated, isAdmin, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="nav-brand" onClick={() => navigate('/')}>
          <HourStackLogo size={38} />
          <span>HourStack</span>
        </div>
        
        <div className="nav-links">
          <a 
            href="/" 
            className={`nav-link ${isActive('/') ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); navigate('/'); }}
          >
            Dashboard
          </a>
          <a 
            href="/projects" 
            className={`nav-link ${isActive('/projects') ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); navigate('/projects'); }}
          >
            Projects
          </a>
          <a 
            href="/timelogs" 
            className={`nav-link ${isActive('/timelogs') ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); navigate('/timelogs'); }}
          >
            Time Logs
          </a>
          <a 
            href="/invoices" 
            className={`nav-link ${isActive('/invoices') ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); navigate('/invoices'); }}
          >
            Invoices
          </a>
          <a 
            href="/clients" 
            className={`nav-link ${isActive('/clients') ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); navigate('/clients'); }}
          >
            Clients
          </a>
          <a
            href="/billing"
            className={`nav-link nav-link--billing ${isActive('/billing') ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); navigate('/billing'); }}
          >
            ⭐ Upgrade
          </a>
          {isAdmin && (
            <a
              href="/admin"
              className={`nav-link ${isActive('/admin') ? 'active' : ''}`}
              onClick={(e) => { e.preventDefault(); navigate('/admin'); }}
            >
              Admin
            </a>
          )}
          <button className="nav-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
