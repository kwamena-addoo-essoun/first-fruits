import React, { useState, useEffect } from 'react';
import './DashboardPage.css';
import { projectAPI, invoiceAPI, userAPI } from '../utils/api';
import { useToastStore } from '../store/toastStore';

const formatCurrency = (val) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(val ?? 0);

const now = new Date();
const greeting = now.getHours() < 12 ? 'Good morning' : now.getHours() < 17 ? 'Good afternoon' : 'Good evening';
const dateLabel = now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

function KpiCard({ label, value, sub, accent, icon }) {
  return (
    <div className={`kpi-card kpi-card--${accent}`}>
      <div className="kpi-icon">{icon}</div>
      <div className="kpi-body">
        <span className="kpi-label">{label}</span>
        <span className="kpi-value">{value}</span>
        {sub && <span className="kpi-sub">{sub}</span>}
      </div>
      <div className="kpi-glow" />
    </div>
  );
}

function ProjectCard({ project, maxEarned }) {
  const barPct = maxEarned > 0 ? Math.round((project.total_earned / maxEarned) * 100) : 0;
  const initials = project.name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();

  return (
    <div className="project-card">
      <div className="project-card-header">
        <div className="project-avatar">{initials}</div>
        <div className="project-card-title">
          <h3>{project.name}</h3>
          <span className="project-status-badge">Active</span>
        </div>
      </div>
      <div className="project-stats-row">
        <div className="project-stat">
          <span className="project-stat-value">{project.total_hours.toFixed(1)}</span>
          <span className="project-stat-label">Hours</span>
        </div>
        <div className="project-stat-divider" />
        <div className="project-stat">
          <span className="project-stat-value project-stat-value--green">{formatCurrency(project.total_earned)}</span>
          <span className="project-stat-label">Earned</span>
        </div>
      </div>
      <div className="project-bar-track">
        <div className="project-bar-fill" style={{ width: `${barPct}%` }} />
      </div>
      <div className="project-bar-label">
        <span>{barPct}% of top earner</span>
      </div>
    </div>
  );
}

function DashboardPage() {
  const push = useToastStore((s) => s.push);
  const [projects, setProjects] = useState([]);
  const [summary, setSummary] = useState(null);
  const [profile, setProfile] = useState(null);
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [profileForm, setProfileForm] = useState({ company_name: '', hourly_rate: '', password: '' });
  const [loading, setLoading] = useState(true);

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
    } finally {
      setLoading(false);
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

  if (loading) {
    return (
      <div className="dash-loading">
        <div className="dash-spinner" />
        <span>Loading dashboard...</span>
      </div>
    );
  }

  const maxEarned = projects.reduce((m, p) => Math.max(m, p.total_earned), 0);
  const collectionRate = summary && summary.total_invoiced > 0
    ? Math.round((summary.paid / summary.total_invoiced) * 100)
    : 0;

  return (
    <div className="dashboard">

      {/* ── HEADER ─────────────────────────────────────── */}
      <div className="dash-header">
        <div className="dash-header-left">
          <p className="dash-greeting">{greeting}{profile ? `, ${profile.username}` : ''}</p>
          <h1 className="dash-title">Overview</h1>
          <p className="dash-date">{dateLabel}</p>
        </div>
        {profile && (
          <div className="dash-header-right">
            <div className="dash-avatar-ring">
              <span className="dash-avatar-initials">
                {profile.username.slice(0, 2).toUpperCase()}
              </span>
            </div>
            <div className="dash-header-meta">
              <span className="dash-header-name">{profile.username}</span>
              <span className="dash-header-rate">${profile.hourly_rate}/hr</span>
            </div>
          </div>
        )}
      </div>

      {/* ── KPI CARDS ──────────────────────────────────── */}
      {summary && (
        <div className="kpi-grid">
          <KpiCard
            label="Total Invoiced"
            value={formatCurrency(summary.total_invoiced)}
            sub={`${projects.length} active project${projects.length !== 1 ? 's' : ''}`}
            accent="cyan"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
              </svg>
            }
          />
          <KpiCard
            label="Collected"
            value={formatCurrency(summary.paid)}
            sub={`${collectionRate}% collection rate`}
            accent="green"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
              </svg>
            }
          />
          <KpiCard
            label="Pending"
            value={formatCurrency(summary.pending)}
            sub="Outstanding balance"
            accent="amber"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
              </svg>
            }
          />
          <KpiCard
            label="Active Projects"
            value={projects.length}
            sub="Across all clients"
            accent="violet"
            icon={
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 7a2 2 0 0 1 2-2h4l2 3H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3"/>
              </svg>
            }
          />
        </div>
      )}

      {/* ── MAIN GRID ──────────────────────────────────── */}
      <div className="dash-main-grid">

        {/* Projects */}
        <section className="dash-section">
          <div className="dash-section-header">
            <h2 className="dash-section-title">Projects</h2>
            <span className="dash-section-count">{projects.length} total</span>
          </div>
          {projects.length === 0 ? (
            <div className="dash-empty">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(0,255,136,0.3)" strokeWidth="1.5">
                <path d="M2 7a2 2 0 0 1 2-2h4l2 3H4a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3"/>
              </svg>
              <p>No projects yet. Create one to get started.</p>
            </div>
          ) : (
            <div className="projects-grid">
              {projects.map((p) => (
                <ProjectCard key={p.id} project={p} maxEarned={maxEarned} />
              ))}
            </div>
          )}
        </section>

        {/* Profile Panel */}
        {profile && (
          <aside className="dash-sidebar">
            <div className="profile-panel">
              <div className="profile-panel-top">
                <div className="profile-panel-avatar">
                  {profile.username.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <div className="profile-panel-name">{profile.username}</div>
                  <div className="profile-panel-email">{profile.email}</div>
                </div>
              </div>

              <div className="profile-panel-stats">
                <div className="profile-panel-stat">
                  <span className="profile-panel-stat-value">${profile.hourly_rate}</span>
                  <span className="profile-panel-stat-label">Hourly Rate</span>
                </div>
                <div className="profile-panel-stat-divider" />
                <div className="profile-panel-stat">
                  <span className="profile-panel-stat-value">{profile.company_name || '—'}</span>
                  <span className="profile-panel-stat-label">Company</span>
                </div>
              </div>

              <button
                className="profile-edit-btn"
                onClick={() => setShowProfileForm(!showProfileForm)}
              >
                {showProfileForm ? 'Cancel' : 'Edit Profile'}
              </button>

              {showProfileForm && (
                <form onSubmit={handleProfileSave} className="profile-edit-form">
                  <div className="form-group">
                    <label>Company Name</label>
                    <input
                      type="text"
                      value={profileForm.company_name}
                      onChange={(e) => setProfileForm({ ...profileForm, company_name: e.target.value })}
                      placeholder="Your company"
                    />
                  </div>
                  <div className="form-group">
                    <label>Hourly Rate ($)</label>
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
                    <label>
                      New Password
                      <span className="form-label-hint">(leave blank to keep)</span>
                    </label>
                    <input
                      type="password"
                      value={profileForm.password}
                      onChange={(e) => setProfileForm({ ...profileForm, password: e.target.value })}
                      placeholder="••••••••"
                      autoComplete="new-password"
                    />
                  </div>
                  <button type="submit" className="btn-primary" style={{ width: '100%' }}>
                    Save Changes
                  </button>
                </form>
              )}
            </div>
          </aside>
        )}
      </div>

    </div>
  );
}

export default DashboardPage;

