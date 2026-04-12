// src/config/api.js
export const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001';

export const ENDPOINTS = {
  HEALTH: '/health',
  STATUS: '/status',
  ORDERS: '/api/orders',
  ORDER_STATS: '/api/orders/stats/summary',
  MSME_REGISTER: '/api/msme/register',
  MSME_BY_WALLET: '/api/msme/wallet',
  OPPORTUNITIES: '/api/investors/opportunities',
  PORTFOLIO: '/api/investors/portfolio',
  TRIGGER_SCRAPE: '/api/admin/trigger-scrape',
  ADMIN_JOBS: '/api/admin/jobs',
};