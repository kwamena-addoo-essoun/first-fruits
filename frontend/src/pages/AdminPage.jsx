import React, { useState, useEffect } from 'react';
import { adminAPI } from '../utils/api';
import './AdminPage.css';

function AdminPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [resetInfo, setResetInfo] = useState(null); // { username, url }

  const loadUsers = async () => {
    try {
      const res = await adminAPI.listUsers();
      setUsers(res.data);
    } catch {
      setError('Failed to load users.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadUsers(); }, []);

  const handleDelete = async (userId, username) => {
    if (!window.confirm(`Delete "${username}" and ALL their data? This cannot be undone.`)) return;
    setError('');
    try {
      await adminAPI.deleteUser(userId);
      setUsers(users.filter(u => u.id !== userId));
    } catch (err) {
      setError(err.response?.data?.detail || 'Delete failed.');
    }
  };

  const handleToggleAdmin = async (userId) => {
    setError('');
    try {
      const res = await adminAPI.toggleAdmin(userId);
      setUsers(users.map(u => u.id === userId ? { ...u, is_admin: res.data.is_admin } : u));
    } catch (err) {
      setError(err.response?.data?.detail || 'Toggle admin failed.');
    }
  };


      const handleDeleteAllUsers = async () => {
        if (!window.confirm('Delete ALL non-admin users and all their data? This cannot be undone.')) return;
        setError('');
        try {
          await adminAPI.deleteAllUsers();
          setUsers(users.filter(u => u.is_admin));
        } catch (err) {
          setError(err.response?.data?.detail || 'Bulk delete failed.');
        }
      };
  const handleResetPassword = async (userId, username) => {
    setError('');
    try {
      const res = await adminAPI.resetPassword(userId);
      setResetInfo({ username, url: res.data.reset_url, emailSent: res.data.email_sent });
    } catch (err) {
      setError(err.response?.data?.detail || 'Reset failed.');
    }
  };

  if (loading) return <div className="admin-container"><p>Loading…</p></div>;

  return (
    <div className="admin-container">
      <h2>Admin Panel</h2>
      <p className="admin-subtitle">{users.length} registered user{users.length !== 1 ? 's' : ''}</p>

      {error && <div className="error-message" style={{ marginBottom: '1rem' }}>{error}</div>}

      {resetInfo && (
        <div className="reset-url-box">
          <strong>Password reset link for {resetInfo.username}:</strong>
          {resetInfo.emailSent
            ? <p style={{ margin: '0.4rem 0 0' }}>Email sent successfully.</p>
            : (
              <>
                <p style={{ margin: '0.4rem 0 0', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  SMTP not configured — copy and send this link manually:
          <button className="btn-small btn-danger" style={{ marginBottom: '1rem' }} onClick={handleDeleteAllUsers}>
            Delete All Non-Admin Users
          </button>
                </p>
                <a
                  href={resetInfo.url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ display: 'block', wordBreak: 'break-all', marginTop: '0.25rem', fontSize: '0.85rem' }}
                >
                  {resetInfo.url}
                </a>
                <button
                  className="btn-small"
                  style={{ marginTop: '0.5rem' }}
                  onClick={() => navigator.clipboard.writeText(resetInfo.url)}
                >
                  Copy Link
                </button>
              </>
            )
          }
          <button
            className="btn-small btn-outline"
            style={{ marginTop: '0.5rem', marginLeft: resetInfo.emailSent ? '0' : '0.5rem' }}
            onClick={() => setResetInfo(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      <table className="admin-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Joined</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id}>
              <td>{user.username}</td>
              <td>{user.email}</td>
              <td>{new Date(user.created_at).toLocaleDateString()}</td>
              <td>
                <span className={`badge ${user.is_admin ? 'badge-admin' : 'badge-user'}`}>
                  {user.is_admin ? 'Admin' : 'User'}
                </span>
              </td>
              <td className="action-cell">
                <button className="btn-small" onClick={() => handleToggleAdmin(user.id)}>
                  {user.is_admin ? 'Revoke Admin' : 'Make Admin'}
                </button>
                <button className="btn-small" onClick={() => handleResetPassword(user.id, user.username)}>
                  Reset PW
                </button>
                <button className="btn-small btn-danger" onClick={() => handleDelete(user.id, user.username)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default AdminPage;
