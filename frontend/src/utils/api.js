import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const API_BASE_URL = process.env.REACT_APP_API_URL || (process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8002/api');

const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

export const userAPI = {
  getMe: () => api.get('/users/me'),
  updateMe: (data) => api.put('/users/me', data),
};

export const authAPI = {
  register: (email, username, password, company, rate) =>
    api.post('/auth/register', { email, username, password, company_name: company, hourly_rate: rate }),
  login: (username, password) =>
    api.post('/auth/login', { username, password }),
  forgotPassword: (email) =>
    api.post('/auth/forgot-password', { email }),
  resetPassword: (token, password) =>
    api.post('/auth/reset-password', { token, password }),
  verifyEmail: (token) =>
    api.get(`/auth/verify-email?token=${token}`),
  resendVerification: (email) =>
    api.post('/auth/resend-verification', { email }),
};

export const projectAPI = {
  getAll: () => api.get('/projects/'),
  create: (project) => api.post('/projects/', project),
  update: (projectId, project) => api.put(`/projects/${projectId}`, project),
  delete: (projectId) => api.delete(`/projects/${projectId}`),
};

export const timelogAPI = {
  create: (timelog) => api.post('/timelog/', timelog),
  getAll: () => api.get('/timelog/'),
  getByProject: (projectId) => api.get(`/timelog/project/${projectId}`),
  getActive: () => api.get('/timelog/active'),
  start: (projectId, description) =>
    api.post('/timelog/', { project_id: projectId, description }),
  stop: (timelogId) => api.patch(`/timelog/${timelogId}/stop`),
  update: (timelogId, data) => api.put(`/timelog/${timelogId}`, data),
  delete: (timelogId) => api.delete(`/timelog/${timelogId}`),
};

export const invoiceAPI = {
  create: (invoice) => api.post('/invoices/', invoice),
  getAll: () => api.get('/invoices/'),
  getSummary: () => api.get('/invoices/earnings/summary'),
  updateStatus: (invoiceId, status) => api.put(`/invoices/${invoiceId}/status`, null, { params: { status } }),
  delete: (invoiceId) => api.delete(`/invoices/${invoiceId}`),
  getPDF: (invoiceId) => api.get(`/invoices/${invoiceId}/pdf`, { responseType: 'blob' }),
  sendToClient: (invoiceId) => api.post(`/invoices/${invoiceId}/send`),
};

export const adminAPI = {
  listUsers: () => api.get('/admin/users'),
  deleteAllUsers: () => api.delete('/admin/users'),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
  toggleAdmin: (userId) => api.post(`/admin/users/${userId}/toggle-admin`),
  resetPassword: (userId) => api.post(`/admin/users/${userId}/reset-password`),
};

export const clientAPI = {
  getAll: () => api.get('/clients/'),
  create: (client) => api.post('/clients/', client),
  update: (clientId, data) => api.put(`/clients/${clientId}`, data),
  delete: (clientId) => api.delete(`/clients/${clientId}`),
};

export const billingAPI = {
  getStatus: () => api.get('/billing/status'),
  createCheckout: () => api.post('/billing/checkout'),
  createPortal: () => api.post('/billing/portal'),
};

export default api;
