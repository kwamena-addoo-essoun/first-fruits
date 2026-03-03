import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './DashboardPage.css';
import { invoiceAPI, clientAPI, projectAPI } from '../utils/api';
import { useToastStore } from '../store/toastStore';
import { useAuthStore } from '../store/authStore';

function InvoicePage() {
  const push = useToastStore((s) => s.push);
  const plan = useAuthStore((s) => s.plan);
  const navigate = useNavigate();
  const isPro = plan === 'pro';
  const [invoices, setInvoices] = useState([]);
  const [clients, setClients] = useState([]);
  const [projects, setProjects] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(true);

  const [selectedClientId, setSelectedClientId] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState('');
  const [autoCompute, setAutoCompute] = useState(true);
  const [formData, setFormData] = useState({
    total_hours: '',
    hourly_rate: '',
    due_date: '',
    notes: '',
  });

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [invRes, clientRes, projRes] = await Promise.all([
        invoiceAPI.getAll(),
        clientAPI.getAll(),
        projectAPI.getAll(),
      ]);
      setInvoices(invRes.data);
      setClients(clientRes.data);
      setProjects(projRes.data);
    } catch (error) {
      push('error', 'Failed to load invoice data.');
    } finally {
      setLoading(false);
    }
  }, [push]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // When a project is selected, pre-fill the hourly rate
  useEffect(() => {
    if (selectedProjectId) {
      const proj = projects.find((p) => p.id === parseInt(selectedProjectId));
      if (proj) {
        setFormData((prev) => ({ ...prev, hourly_rate: proj.hourly_rate }));
      }
    }
  }, [selectedProjectId, projects]);

  // Filter projects by selected client (or show all if no client selected)
  const filteredProjects = selectedClientId
    ? projects.filter((p) => p.client_id === parseInt(selectedClientId))
    : projects;

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const resetForm = () => {
    setSelectedClientId('');
    setSelectedProjectId('');
    setAutoCompute(true);
    setFormData({ total_hours: '', hourly_rate: '', due_date: '', notes: '' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        due_date: new Date(formData.due_date).toISOString(),
        notes: formData.notes || undefined,
      };

      if (selectedProjectId) {
        payload.project_id = parseInt(selectedProjectId);
        payload.hourly_rate = formData.hourly_rate ? parseFloat(formData.hourly_rate) : undefined;
        if (!autoCompute) {
          payload.total_hours = parseFloat(formData.total_hours);
        }
      } else {
        if (selectedClientId) payload.client_id = parseInt(selectedClientId);
        payload.total_hours = parseFloat(formData.total_hours);
        payload.hourly_rate = parseFloat(formData.hourly_rate);
      }

      await invoiceAPI.create(payload);
      resetForm();
      setShowForm(false);
      push('success', 'Invoice created.');
      fetchData();
    } catch (error) {
      push('error', error?.response?.data?.detail || 'Failed to create invoice.');
    }
  };

  const handleStatusChange = async (invoiceId, newStatus) => {
    try {
      await invoiceAPI.updateStatus(invoiceId, newStatus);
      push('success', `Invoice marked ${newStatus}.`);
      fetchData();
    } catch (error) {
      push('error', error?.response?.data?.detail || 'Failed to update invoice status.');
    }
  };

  const handleDelete = async (invoiceId) => {
    if (window.confirm('Delete this invoice?')) {
      try {
        await invoiceAPI.delete(invoiceId);
        push('success', 'Invoice deleted.');
        fetchData();
      } catch (error) {
        push('error', error?.response?.data?.detail || 'Failed to delete invoice.');
      }
    }
  };

  const handleDownloadPDF = async (invoice) => {
    try {
      const res = await invoiceAPI.getPDF(invoice.id);
      const url = URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${invoice.invoice_number}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      push('error', 'Failed to download PDF.');
    }
  };

  const handleEmailToClient = async (invoice) => {
    if (!window.confirm(`Email ${invoice.invoice_number} to the client on file?`)) return;
    try {
      const res = await invoiceAPI.sendToClient(invoice.id);
      push('success', res.data.message || 'Invoice emailed to client.');
      fetchData();
    } catch (error) {
      push('error', error?.response?.data?.detail || 'Failed to send invoice email.');
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'paid':  return 'status-badge status-badge--paid';
      case 'sent':  return 'status-badge status-badge--sent';
      case 'draft': return 'status-badge status-badge--draft';
      default:      return 'status-badge status-badge--default';
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  const needsManualHours = !selectedProjectId || !autoCompute;

  return (
    <div className="dashboard">
      <h1>📄 Invoices</h1>

      <button className="btn-primary" onClick={() => { setShowForm(!showForm); resetForm(); }}>
        {showForm ? 'Cancel' : '+ Create Invoice'}
      </button>

      {showForm && (
        <div className="card form-card">
          <h2>Create Invoice</h2>
          <form onSubmit={handleSubmit}>

            {/* Client */}
            <div className="form-group">
              <label>Client <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>
              <select
                value={selectedClientId}
                onChange={(e) => { setSelectedClientId(e.target.value); setSelectedProjectId(''); }}
              >
                <option value="">— No client —</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            {/* Project */}
            <div className="form-group">
              <label>Project <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional — auto-computes hours)</span></label>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
              >
                <option value="">— No project —</option>
                {filteredProjects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>

            {/* Auto-compute toggle if project selected */}
            {selectedProjectId && (
              <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="checkbox"
                  id="autoCompute"
                  checked={autoCompute}
                  onChange={(e) => setAutoCompute(e.target.checked)}
                  style={{ width: 'auto', marginTop: 0 }}
                />
                <label htmlFor="autoCompute" style={{ marginBottom: 0 }}>
                  Auto-compute hours from uninvoiced time logs
                </label>
              </div>
            )}

            {/* Manual hours (shown if no project, or auto-compute is off) */}
            {needsManualHours && (
              <div className="form-group">
                <label>Total Hours</label>
                <input
                  type="number"
                  name="total_hours"
                  value={formData.total_hours}
                  onChange={handleInputChange}
                  step="0.25"
                  min="0"
                  required
                />
              </div>
            )}

            {/* Hourly rate */}
            <div className="form-group">
              <label>Hourly Rate ($)</label>
              <input
                type="number"
                name="hourly_rate"
                value={formData.hourly_rate}
                onChange={handleInputChange}
                step="0.01"
                min="0"
                required={!selectedProjectId}
                placeholder={selectedProjectId ? 'Leave blank to use project rate' : ''}
              />
            </div>

            {/* Due date */}
            <div className="form-group">
              <label>Due Date</label>
              <input
                type="date"
                name="due_date"
                value={formData.due_date}
                onChange={handleInputChange}
                required
              />
            </div>

            {/* Notes */}
            <div className="form-group">
              <label>Notes <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleInputChange}
                rows="2"
                placeholder="e.g., Payment terms, project scope summary..."
              />
            </div>

            <button type="submit" className="btn-primary">Create Invoice</button>
          </form>
        </div>
      )}

      <div className="card">
        <h2>All Invoices</h2>
        {invoices.length === 0 ? (
          <p>No invoices yet. Create one to get started!</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Client</th>
                <th>Project</th>
                <th>Hours</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Due Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((invoice) => (
                <tr key={invoice.id}>
                  <td><strong>{invoice.invoice_number}</strong></td>
                  <td>{invoice.client_name || <span className="cell-empty">—</span>}</td>
                  <td>{invoice.project_name || <span className="cell-empty">—</span>}</td>
                  <td>{invoice.total_hours.toFixed(2)}h</td>
                  <td><strong>${invoice.total_amount.toFixed(2)}</strong></td>
                  <td>
                    <span className={getStatusClass(invoice.status)}>
                      {invoice.status.toUpperCase()}
                    </span>
                  </td>
                  <td>{new Date(invoice.due_date).toLocaleDateString()}</td>
                  <td>
                    <div className="project-actions">
                      <button
                        className="btn-small"
                        onClick={() => handleDownloadPDF(invoice)}
                        title="Download PDF"
                      >
                        ⬇ PDF
                      </button>
                      {invoice.client_name && (
                        isPro ? (
                          <button
                            className="btn-small"
                            onClick={() => handleEmailToClient(invoice)}
                            title="Email invoice to client"
                          >
                            📧 Email
                          </button>
                        ) : (
                          <button
                            className="btn-small btn-pro-lock"
                            onClick={() => navigate('/billing')}
                            title="Upgrade to Pro to email invoices"
                          >
                            🔒 Pro
                          </button>
                        )
                      )}
                      {invoice.status === 'draft' && (
                        <>
                          <button
                            className="btn-small"
                            onClick={() => handleStatusChange(invoice.id, 'sent')}
                          >
                            Send
                          </button>
                          <button
                            className="btn-small btn-delete"
                            onClick={() => handleDelete(invoice.id)}
                          >
                            Delete
                          </button>
                        </>
                      )}
                      {invoice.status === 'sent' && (
                        <button
                          className="btn-small"
                          onClick={() => handleStatusChange(invoice.id, 'paid')}
                        >
                          Mark Paid
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default InvoicePage;

