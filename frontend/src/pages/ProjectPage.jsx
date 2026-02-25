import React, { useState, useEffect } from 'react';
import './DashboardPage.css';
import { projectAPI } from '../utils/api';
import { useToastStore } from '../store/toastStore';

function ProjectPage() {
  const push = useToastStore((s) => s.push);
  const [projects, setProjects] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    hourly_rate: ''
  });

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await projectAPI.getAll();
      setProjects(response.data);
    } catch (error) {
      push('error', 'Failed to load projects.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await projectAPI.create({
        ...formData,
        hourly_rate: parseFloat(formData.hourly_rate)
      });
      setFormData({
        name: '',
        description: '',
        hourly_rate: ''
      });
      setShowForm(false);
      push('success', `Project "${formData.name}" created.`);
      fetchProjects();
    } catch (error) {
      push('error', error?.response?.data?.detail || 'Failed to create project.');
    }
  };

  const handleDelete = async (projectId) => {
    if (window.confirm('Delete this project? This cannot be undone.')) {
      try {
        await projectAPI.delete(projectId);
        push('success', 'Project deleted.');
        fetchProjects();
      } catch (error) {
        push('error', error?.response?.data?.detail || 'Failed to delete project.');
      }
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="dashboard">
      <h1>💼 Projects</h1>

      <button 
        className="btn-primary" 
        onClick={() => setShowForm(!showForm)}
      >
        {showForm ? 'Cancel' : '+ New Project'}
      </button>

      {showForm && (
        <div className="card form-card">
          <h2>Create New Project</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Project Name</label>
              <input 
                type="text" 
                name="name" 
                value={formData.name} 
                onChange={handleInputChange}
                placeholder="e.g., Website Redesign"
                required
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea 
                name="description" 
                value={formData.description} 
                onChange={handleInputChange}
                placeholder="Project details..."
                rows="3"
              />
            </div>

            <div className="form-group">
              <label>Hourly Rate ($)</label>
              <input 
                type="number" 
                name="hourly_rate" 
                value={formData.hourly_rate} 
                onChange={handleInputChange}
                step="0.01"
                min="0"
                required
              />
            </div>

            <button type="submit" className="btn-primary">Create Project</button>
          </form>
        </div>
      )}

      <div className="card">
        <h2>Your Projects</h2>
        {projects.length === 0 ? (
          <p>No projects yet. Create one to start logging time!</p>
        ) : (
          <div className="projects-grid">
            {projects.map(project => (
              <div key={project.id} className="project-card">
                <h3>{project.name}</h3>
                {project.description && <p>{project.description}</p>}
                <div className="project-stats">
                  <div className="stat">
                    <span className="label">Hours</span>
                    <span className="value">{project.total_hours.toFixed(2)}h</span>
                  </div>
                  <div className="stat">
                    <span className="label">Earned</span>
                    <span className="value">${project.total_earned.toFixed(2)}</span>
                  </div>
                  <div className="stat">
                    <span className="label">Rate</span>
                    <span className="value">${project.hourly_rate}/hr</span>
                  </div>
                </div>
                <div className="project-actions">
                  <button
                    className="btn-small btn-delete"
                    onClick={() => handleDelete(project.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default ProjectPage;
