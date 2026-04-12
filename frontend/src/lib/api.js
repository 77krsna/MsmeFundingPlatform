// src/lib/api.js
import axios from 'axios';
import { API_BASE, ENDPOINTS } from '../config/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health & Status
export const getHealth = async () => {
  const { data } = await api.get(ENDPOINTS.HEALTH);
  return data;
};

export const getStatus = async () => {
  const { data } = await api.get(ENDPOINTS.STATUS);
  return data;
};

// Orders
export const getOrders = async (page = 1, pageSize = 10, status = '') => {
  const params = { page, page_size: pageSize };
  if (status) params.status = status;
  const { data } = await api.get(ENDPOINTS.ORDERS, { params });
  return data;
};

export const getOrderById = async (orderId) => {
  const { data } = await api.get(`${ENDPOINTS.ORDERS}/${orderId}`);
  return data;
};

export const getOrderStats = async () => {
  const { data } = await api.get(ENDPOINTS.ORDER_STATS);
  return data;
};

// MSME
export const registerMSME = async (msmeData) => {
  const { data } = await api.post(ENDPOINTS.MSME_REGISTER, msmeData);
  return data;
};

export const getMSMEByWallet = async (walletAddress) => {
  const { data } = await api.get(`${ENDPOINTS.MSME_BY_WALLET}/${walletAddress}`);
  return data;
};

// Investors
export const getOpportunities = async () => {
  const { data } = await api.get(ENDPOINTS.OPPORTUNITIES);
  return data;
};

export const getPortfolio = async (walletAddress) => {
  const { data } = await api.get(`${ENDPOINTS.PORTFOLIO}/${walletAddress}`);
  return data;
};

// Admin
export const triggerScrape = async () => {
  const { data } = await api.post(ENDPOINTS.TRIGGER_SCRAPE);
  return data;
};

export const getAdminJobs = async () => {
  const { data } = await api.get(ENDPOINTS.ADMIN_JOBS);
  return data;
};

export default api;