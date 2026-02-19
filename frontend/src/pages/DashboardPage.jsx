import React, { useState, useEffect } from 'react';
import './DashboardPage.css';
import { projectAPI, invoiceAPI } from '../utils/api';

function DashboardPage() {
  const [projects, setProjects] = useState([]);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [projectsRes, summaryRes] = await Promise.all([
        projectAPI.getAll(),
        invoiceAPI.getSummary()
      ]);
      setProjects(projectsRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
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
    </div>
  );
}

export default DashboardPage;
