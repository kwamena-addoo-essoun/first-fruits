import React, { useState, useEffect } from 'react';
import './DashboardPage.css';
import { clientAPI } from '../utils/api';
import { useToastStore } from '../store/toastStore';

function ClientsPage() {
  const push = useToastStore((s) => s.push);
  const [clients, setClients] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({ name: '', email: '', rate: '' });
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', email: '', rate: '' });

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await clientAPI.getAll();
      setClients(response.data);
    } catch (error) {
      push('error', 'Failed to load clients.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await clientAPI.create(formData);
      setFormData({ name: '', email: '', rate: '' });
      setShowForm(false);
      push('success', `Client "${formData.name}" added.`);
      fetchClients();
    } catch (error) {
      push('error', error?.response?.data?.detail || 'Failed to create client.');
    }
  };

  const handleEditStart = (client) => {
    setEditingId(client.id);
    setEditForm({ name: client.name, email: client.email, rate: client.rate || '' });
  };

  const handleEditSave = async (clientId) => {
    try {
      await clientAPI.update(clientId, editForm);
      setEditingId(null);
      push('success', 'Client updated.');
      fetchClients();
    } catch (error) {
      push('error', error?.response?.data?.detail || 'Failed to update client.');
    }
  };

  const handleDelete = async (clientId, name) => {
    if (window.confirm(`Delete "${name}"? This cannot be undone.`)) {
      try {
        await clientAPI.delete(clientId);
        push('success', `Client "${name}" deleted.`);
        fetchClients();
      } catch (error) {
        push('error', error?.response?.data?.detail || 'Failed to delete client.');
      }
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="dashboard">
      <h1>ðŸ‘¥ Clients</h1>

      <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
        {showForm ? 'Cancel' : '+ New Client'}
      </button>

      {showForm && (
        <div className="card form-card">
          <h2>Add Client</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Name</label>
              <input type="text" name="name" value={formData.name} onChange={handleInputChange} placeholder="e.g., Acme Corp" required />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input type="email" name="email" value={formData.email} onChange={handleInputChange} placeholder="contact@client.com" required />
            </div>
            <div className="form-group">
              <label>Rate (optional)</label>
              <input type="text" name="rate" value={formData.rate} onChange={handleInputChange} placeholder="e.g., 95.00" />
            </div>
            <button type="submit" className="btn-primary">Add Client</button>
          </form>
        </div>
      )}

      <div className="card">
        <h2>Your Clients</h2>
        {clients.length === 0 ? (
          <p>No clients yet. Add one to associate projects and invoices with clients.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Rate</th>
                <th>Added</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {clients.map(client => (
                editingId === client.id ? (
                  <tr key={client.id}>
                    <td><input type="text" value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} required /></td>
                    <td><input type="email" value={editForm.email} onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} required /></td>
                    <td><input type="text" value={editForm.rate} onChange={(e) => setEditForm({ ...editForm, rate: e.target.value })} /></td>
                    <td>{new Date(client.created_at).toLocaleDateString()}</td>
                    <td>
                      <button className="btn-small" onClick={() => handleEditSave(client.id)}>Save</button>
                      <button className="btn-small" onClick={() => setEditingId(null)} style={{ marginLeft: '0.25rem' }}>Cancel</button>
                    </td>
                  </tr>
                ) : (
                  <tr key={client.id}>
                    <td><strong>{client.name}</strong></td>
                    <td>{client.email}</td>
                    <td>{client.rate || 'â€”'}</td>
                    <td>{new Date(client.created_at).toLocaleDateString()}</td>
                    <td>
                      <button className="btn-small" onClick={() => handleEditStart(client)}>Edit</button>
                      <button className="btn-small btn-delete" onClick={() => handleDelete(client.id, client.name)} style={{ marginLeft: '0.25rem' }}>Delete</button>
                    </td>
                  </tr>
                )
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default ClientsPage;
