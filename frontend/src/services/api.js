import axios from 'axios';

const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
});

API.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

API.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.clear();
      window.location.href = '/';
    }
    return Promise.reject(err);
  }
);

export const shipmentAPI = {
  getAll: (params) => API.get('/api/shipments', { params }),
  getOne: (id) => API.get(`/api/shipments/${id}`),
  register: (data) => API.post('/api/shipments', data),
  updateStatus: (id, status) => API.patch(`/api/shipments/${id}/status`, { status }),
  reoptimize: (id, trigger) => API.post(`/api/shipments/${id}/reoptimize`, { triggered_by: trigger }),
  addEvent: (id, data) => API.post(`/api/shipments/${id}/add-event`, data),
  getEvents: (id, limit=50) => API.get(`/api/shipments/${id}/tracking-events?limit=${limit}`),
  getDelays: (id) => API.get(`/api/shipments/${id}/delays`),
  getCurrentRoute: (id) => API.get(`/api/shipments/${id}/current-route`),
  getOriginalRoute: (id) => API.get(`/api/shipments/${id}/original-route`),
  getRouteHistory: (id) => API.get(`/api/shipments/${id}/route-history`),
  getAlerts: (id) => API.get(`/api/shipments/${id}/alerts`),
  getPorts: () => API.get('/api/ports'),
};

export const analyticsAPI = {
  getDashboard: (days=30) => API.get(`/api/analytics/dashboard?days=${days}`),
  getAIInsights: (query) => API.post('/api/analytics/ai-insights', { query }),
};

export const authAPI = {
  login: (email, password) => API.post('/api/auth/login', { email, password }),
};

export default API;
