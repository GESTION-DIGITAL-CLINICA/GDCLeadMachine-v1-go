import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const http = axios.create({
  timeout: 10000,
});

const cache = new Map();
const inflight = new Map();

const getCachedOrFetch = async (key, ttlMs, fetcher) => {
  const now = Date.now();
  const cached = cache.get(key);

  if (cached && now - cached.ts < ttlMs) {
    return cached.value;
  }

  if (inflight.has(key)) {
    return inflight.get(key);
  }

  const promise = fetcher()
    .then((value) => {
      cache.set(key, { ts: Date.now(), value });
      inflight.delete(key);
      return value;
    })
    .catch((error) => {
      inflight.delete(key);
      throw error;
    });

  inflight.set(key, promise);
  return promise;
};

// Clinics
export const createClinic = async (clinicData) => {
  const response = await http.post(`${API}/clinics`, clinicData);
  return response.data;
};

export const bulkImportClinics = async (clinics, source = 'Bulk Import') => {
  const response = await http.post(`${API}/clinics/bulk`, { clinics, source });
  return response.data;
};

export const getClinics = async (skip = 0, limit = 100) => {
  const key = `clinics:${skip}:${limit}`;
  return getCachedOrFetch(key, 8000, async () => {
    const response = await http.get(`${API}/clinics?skip=${skip}&limit=${limit}`);
    return response.data;
  });
};

export const scoreClinic = async (clinicId) => {
  const response = await http.post(`${API}/clinics/${clinicId}/score`);
  return response.data;
};

// Email Management
export const addEmailAccount = async (username, password) => {
  const response = await http.post(`${API}/email-accounts`, { username, password });
  return response.data;
};

export const getEmailAccounts = async () => {
  return getCachedOrFetch('email_accounts', 10000, async () => {
    const response = await http.get(`${API}/email-accounts`);
    return response.data;
  });
};

export const getEmailStats = async () => {
  return getCachedOrFetch('email_stats', 5000, async () => {
    const response = await http.get(`${API}/email/stats`);
    return response.data;
  });
};

export const getEmailQueue = async (status = null) => {
  const cacheKey = status ? `email_queue:${status}` : 'email_queue:all';
  return getCachedOrFetch(cacheKey, 5000, async () => {
    const url = status ? `${API}/email/queue?status=${status}` : `${API}/email/queue`;
    const response = await http.get(url);
    return response.data;
  });
};

export const uploadAttachment = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await http.post(`${API}/email/attachments`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

// Dashboard Stats
export const getDashboardStats = async () => {
  return getCachedOrFetch('dashboard_stats', 10000, async () => {
    const response = await http.get(`${API}/stats/dashboard`);
    return response.data;
  });
};
