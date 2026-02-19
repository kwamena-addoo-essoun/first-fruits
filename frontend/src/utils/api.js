import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8002/api';

const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.params = config.params || {};
    config.params.token = token;
  }
  return config;
});

export const authAPI = {
  register: (email, username, password, company, rate) =>
    api.post('/auth/register', { email, username, password, company_name: company, hourly_rate: rate }),
  login: (username, password) =>
    api.post('/auth/login', { username, password }),
};

export const projectAPI = {
  getAll: () => api.get('/projects/'),
  create: (project) => api.post('/projects/', project),
};

export const timelogAPI = {
  create: (timelog) => api.post('/timelog/', timelog),
  getAll: () => api.get('/timelog/'),
  getByProject: (projectId) => api.get(`/timelog/project/${projectId}`),
};

export const invoiceAPI = {
  create: (invoice) => api.post('/invoices/', invoice),
  getAll: () => api.get('/invoices/'),
  getSummary: () => api.get('/invoices/earnings/summary'),
};

export default api;
