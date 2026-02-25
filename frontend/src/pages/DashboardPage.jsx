import React, { useState, useEffect } from 'react';
import './DashboardPage.css';
import { projectAPI, invoiceAPI, userAPI } from '../utils/api';
import { useToastStore } from '../store/toastStore';

function DashboardPage() {
  const push = useToastStore((s) => s.push);
  const [projects, setProjects] = useState([]);
  const [summary, setSummary] = useState(null);
  const [profile, setProfile] = useState(null);
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [profileForm, setProfileForm] = useState({ company_name: '', hourly_rate: '', password: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [projectsRes, summaryRes, profileRes] = await Promise.all([
        projectAPI.getAll(),
        invoiceAPI.getSummary(),
        userAPI.getMe(),
      ]);
      setProjects(projectsRes.data);
      setSummary(summaryRes.data);
      setProfile(profileRes.data);
      setProfileForm({
        company_name: profileRes.data.company_name || '',
        hourly_rate: profileRes.data.hourly_rate,
        password: '',
      });
    } catch (error) {
      push('error', 'Failed to load dashboard data.');
    }
  };

  const handleProfileSave = async (e) => {
    e.preventDefault();
    try {
      const payload = {};
      if (profileForm.company_name !== (profile.company_name || ''))
        payload.company_name = profileForm.company_name;
      if (parseFloat(profileForm.hourly_rate) !== profile.hourly_rate)
        payload.hourly_rate = parseFloat(profileForm.hourly_rate);
      if (profileForm.password)
        payload.password = profileForm.password;
      if (!Object.keys(payload).length) {
        setShowProfileForm(false);
        return;
      }
      const res = await userAPI.updateMe(payload);
      setProfile(res.data);
      setProfileForm({ ...profileForm, password: '' });
      setShowProfileForm(false);
      push('success', 'Profile updated.');
    } catch (error) {
      push('error', error?.response?.data?.detail || 'Failed to update profile.');
    }
  };

  return (
    <div className="dashboard">
      <h1>💼 Time Tracker Dashboard</h1>

      {summary && (
        <div className="summary-grid">
          <div className="card">
            <h3>Total Invoiced</h3>
            <p className="amount">${summary.total_invoiced.toFixed(2)}</p>
          </div>
          <div className="card">
            <h3>Paid</h3>
            <p className="amount paid">${summary.paid.toFixed(2)}</p>
          </div>
          <div className="card">
            <h3>Pending</h3>
            <p className="amount pending">${summary.pending.toFixed(2)}</p>
          </div>
        </div>
      )}

      <div className="card">
        <h2>Projects</h2>
        <div className="projects-list">
          {projects.map((project) => (
            <div key={project.id} className="project-item">
              <h4>{project.name}</h4>
              <p>Total Hours: {project.total_hours.toFixed(2)}</p>
              <p>Earned: ${project.total_earned.toFixed(2)}</p>
            </div>
          ))}
        </div>
      </div>

      {profile && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2>Profile Settings</h2>
            <button className="btn-small" onClick={() => setShowProfileForm(!showProfileForm)}>
              {showProfileForm ? 'Cancel' : 'Edit'}
            </button>
          </div>
          {!showProfileForm ? (
            <div className="profile-info">
              <p><strong>Username:</strong> {profile.username}</p>
              <p><strong>Email:</strong> {profile.email}</p>
              <p><strong>Company:</strong> {profile.company_name || '—'}</p>
              <p><strong>Default Rate:</strong> ${profile.hourly_rate}/hr</p>
            </div>
          ) : (
            <form onSubmit={handleProfileSave} style={{ marginTop: '1rem' }}>
              <div className="form-group">
                <label>Company Name</label>
                <input
                  type="text"
                  value={profileForm.company_name}
                  onChange={(e) => setProfileForm({ ...profileForm, company_name: e.target.value })}
                  placeholder="Your company name"
                />
              </div>
              <div className="form-group">
                <label>Default Hourly Rate ($)</label>
                <input
                  type="number"
                  value={profileForm.hourly_rate}
                  onChange={(e) => setProfileForm({ ...profileForm, hourly_rate: e.target.value })}
                  step="0.01"
                  min="0"
                  required
                />
              </div>
              <div className="form-group">
                <label>New Password <span style={{ color: '#999', fontWeight: 400 }}>(leave blank to keep current)</span></label>
                <input
                  type="password"
                  value={profileForm.password}
                  onChange={(e) => setProfileForm({ ...profileForm, password: e.target.value })}
                  placeholder="New password"
                  autoComplete="new-password"
                />
              </div>
              <button type="submit" className="btn-primary">Save Changes</button>
            </form>
          )}
        </div>
      )}
    </div>
  );
}

export default DashboardPage;

