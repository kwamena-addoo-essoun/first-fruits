import React, { useState, useEffect, useRef, useCallback } from 'react';
import './DashboardPage.css';
import { timelogAPI, projectAPI } from '../utils/api';
import { useToastStore } from '../store/toastStore';

// Format seconds → "H:MM:SS"
function formatElapsed(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// Format datetime to value for <input type="datetime-local">
function toDatetimeLocal(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function TimeLogPage() {
  const push = useToastStore((s) => s.push);
  const [timelogs, setTimelogs] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  // Live timer state
  const [activeTimer, setActiveTimer] = useState(null);  // active timelog object
  const [elapsed, setElapsed] = useState(0);             // seconds
  const [timerProject, setTimerProject] = useState('');
  const [timerDesc, setTimerDesc] = useState('');
  const intervalRef = useRef(null);

  // Manual log form
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    project_id: '', start_time: '', end_time: '', description: '',
  });

  // Inline edit state
  const [editingId, setEditingId] = useState(null);
  const [editData, setEditData] = useState({});

  const startElapsedInterval = useCallback((startTime) => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    const tick = () => {
      const secs = Math.floor((Date.now() - new Date(startTime).getTime()) / 1000);
      setElapsed(Math.max(0, secs));
    };
    tick();
    intervalRef.current = setInterval(tick, 1000);
  }, []);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [logsRes, projRes] = await Promise.all([
        timelogAPI.getAll(),
        projectAPI.getAll(),
      ]);
      setTimelogs(logsRes.data);
      setProjects(projRes.data);

      // Check for active timer
      try {
        const activeRes = await timelogAPI.getActive();
        setActiveTimer(activeRes.data);
        startElapsedInterval(activeRes.data.start_time);
        setTimerProject(String(activeRes.data.project_id));
      } catch {
        setActiveTimer(null);
        if (intervalRef.current) clearInterval(intervalRef.current);
      }
    } catch (error) {
      push('error', 'Failed to load time tracking data.');
    } finally {
      setLoading(false);
    }
  }, [push, startElapsedInterval]);

  useEffect(() => {
    fetchData();
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [fetchData]);

  // ── Live timer handlers ────────────────────────────────────────────────
  const handleStartTimer = async () => {
    if (!timerProject) { push('error', 'Select a project first.'); return; }
    try {
      const res = await timelogAPI.start(parseInt(timerProject), timerDesc || undefined);
      setActiveTimer(res.data);
      setElapsed(0);
      startElapsedInterval(res.data.start_time);
      setTimerDesc('');
      push('success', 'Timer started.');
    } catch (error) {
      push('error', error?.response?.data?.detail || 'Failed to start timer.');
    }
  };

  const handleStopTimer = async () => {
    if (!activeTimer) return;
    try {
      await timelogAPI.stop(activeTimer.id);
      clearInterval(intervalRef.current);
      setActiveTimer(null);
      setElapsed(0);
      push('success', `Timer stopped — ${formatElapsed(elapsed)} logged.`);
      fetchData();
    } catch (error) {
      push('error', error?.response?.data?.detail || 'Failed to stop timer.');
    }
  };

  // ── Manual log handlers ────────────────────────────────────────────────
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    try {
      await timelogAPI.create({
        ...formData,
        project_id: parseInt(formData.project_id),
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
      });
      setFormData({ project_id: '', start_time: '', end_time: '', description: '' });
      setShowForm(false);
      push('success', 'Time logged.');
      fetchData();
    } catch (error) {
      push('error', error?.response?.data?.detail || 'Failed to log time.');
    }
  };

  // ── Inline edit handlers ───────────────────────────────────────────────
  const handleEditStart = (log) => {
    setEditingId(log.id);
    setEditData({
      start_time: toDatetimeLocal(log.start_time),
      end_time: toDatetimeLocal(log.end_time),
      description: log.description || '',
    });
  };

  const handleEditSave = async (logId) => {
    try {
      await timelogAPI.update(logId, {
        start_time: editData.start_time ? new Date(editData.start_time).toISOString() : undefined,
        end_time: editData.end_time ? new Date(editData.end_time).toISOString() : undefined,
        description: editData.description || undefined,
      });
      setEditingId(null);
      push('success', 'Time log updated.');
      fetchData();
    } catch (error) {
      push('error', error?.response?.data?.detail || 'Failed to update time log.');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Delete this time log?')) {
      try {
        await timelogAPI.delete(id);
        push('success', 'Time log deleted.');
        fetchData();
      } catch (error) {
        push('error', error?.response?.data?.detail || 'Failed to delete time log.');
      }
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  const activeProject = projects.find((p) => String(p.id) === timerProject);

  return (
    <div className="dashboard">
      <h1>⏱️ Time Tracking</h1>

      {/* ── Live Timer Card ────────────────────────────────────────────── */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h2>Live Timer</h2>
        {activeTimer ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: '#2c3e50' }}>
              {formatElapsed(elapsed)}
            </div>
            <div style={{ color: '#666' }}>
              <div><strong>{projects.find((p) => p.id === activeTimer.project_id)?.name}</strong></div>
              {activeTimer.description && <div style={{ fontSize: '0.9rem' }}>{activeTimer.description}</div>}
            </div>
            <button className="btn-primary" style={{ background: '#e74c3c' }} onClick={handleStopTimer}>
              ⏹ Stop
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div className="form-group" style={{ marginBottom: 0, minWidth: '180px' }}>
              <label>Project</label>
              <select value={timerProject} onChange={(e) => setTimerProject(e.target.value)}>
                <option value="">Select project…</option>
                {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div className="form-group" style={{ marginBottom: 0, minWidth: '220px' }}>
              <label>Description <span style={{ color: '#999', fontWeight: 400 }}>(optional)</span></label>
              <input
                type="text"
                value={timerDesc}
                onChange={(e) => setTimerDesc(e.target.value)}
                placeholder="What are you working on?"
              />
            </div>
            <button className="btn-primary" style={{ background: '#27ae60' }} onClick={handleStartTimer}>
              ▶ Start Timer
            </button>
          </div>
        )}
      </div>

      {/* ── Manual Log Form ────────────────────────────────────────────── */}
      <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
        {showForm ? 'Cancel' : '+ Log Past Time'}
      </button>

      {showForm && (
        <div className="card form-card">
          <h2>Log Past Work</h2>
          <form onSubmit={handleManualSubmit}>
            <div className="form-group">
              <label>Project</label>
              <select name="project_id" value={formData.project_id} onChange={handleInputChange} required>
                <option value="">Select a project</option>
                {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Start Time</label>
              <input type="datetime-local" name="start_time" value={formData.start_time}
                onChange={handleInputChange} required />
            </div>
            <div className="form-group">
              <label>End Time</label>
              <input type="datetime-local" name="end_time" value={formData.end_time}
                onChange={handleInputChange} required />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea name="description" value={formData.description} onChange={handleInputChange}
                placeholder="What did you work on?" rows="2" />
            </div>
            <button type="submit" className="btn-primary">Log Time</button>
          </form>
        </div>
      )}

      {/* ── Time Logs Table ────────────────────────────────────────────── */}
      <div className="card">
        <h2>Time Logs</h2>
        {timelogs.length === 0 ? (
          <p>No time logs yet. Start the timer or log past work!</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Project</th>
                <th>Hours</th>
                <th>Description</th>
                <th>Start</th>
                <th>End</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {timelogs.map((log) => {
                const isRunning = log.end_time === null;
                if (editingId === log.id) {
                  return (
                    <tr key={log.id} style={{ background: '#f0f7ff' }}>
                      <td>{projects.find((p) => p.id === log.project_id)?.name}</td>
                      <td>—</td>
                      <td>
                        <input
                          type="text"
                          value={editData.description}
                          onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                          style={{ width: '100%', padding: '0.3rem' }}
                        />
                      </td>
                      <td>
                        <input
                          type="datetime-local"
                          value={editData.start_time}
                          onChange={(e) => setEditData({ ...editData, start_time: e.target.value })}
                          style={{ padding: '0.3rem' }}
                        />
                      </td>
                      <td>
                        <input
                          type="datetime-local"
                          value={editData.end_time}
                          onChange={(e) => setEditData({ ...editData, end_time: e.target.value })}
                          style={{ padding: '0.3rem' }}
                        />
                      </td>
                      <td>
                        <div className="project-actions">
                          <button className="btn-small" onClick={() => handleEditSave(log.id)}>Save</button>
                          <button className="btn-small" onClick={() => setEditingId(null)}>Cancel</button>
                        </div>
                      </td>
                    </tr>
                  );
                }
                return (
                  <tr key={log.id}>
                    <td>{projects.find((p) => p.id === log.project_id)?.name || '—'}</td>
                    <td>
                      {isRunning
                        ? <span style={{ color: '#27ae60', fontWeight: 600 }}>● Running</span>
                        : `${(log.hours || 0).toFixed(2)}h`}
                    </td>
                    <td>{log.description || <span style={{ color: '#aaa' }}>—</span>}</td>
                    <td>{new Date(log.start_time).toLocaleString()}</td>
                    <td>{log.end_time ? new Date(log.end_time).toLocaleString() : <span style={{ color: '#aaa' }}>—</span>}</td>
                    <td>
                      <div className="project-actions">
                        {!isRunning && (
                          <button className="btn-small" onClick={() => handleEditStart(log)}>Edit</button>
                        )}
                        <button className="btn-small btn-delete" onClick={() => handleDelete(log.id)}>Delete</button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default TimeLogPage;


