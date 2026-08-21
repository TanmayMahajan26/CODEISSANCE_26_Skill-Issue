/**
 * Nexus360 — Centralized Modular API Services.
 * Connects frontend views to backend endpoints using Bearer JWT authentication.
 */

import { api } from './client';

// ── Auth Service ──────────────────────────────────────────────────
export const authService = {
  login: (usernameOrEmail, password) =>
    api.post('/auth/login', { username_or_email: usernameOrEmail, password }),
  me: () => api.get('/auth/me'),
  getDemoUsers: () => api.get('/auth/demo-users'),
};

// ── Customer 360 Service ──────────────────────────────────────────
export const customerService = {
  list: (params = {}) => api.get('/customers', params),
  getById: (customerId) => api.get(`/customers/${customerId}`),
  getGraph: (customerId) => api.get(`/customers/${customerId}/graph`),
  getWaterfall: (customerId) => api.get(`/customers/${customerId}/waterfall`),
  getLineage: (customerId) => api.get(`/customers/${customerId}/lineage`),
};

// ── Matching Engine Service ───────────────────────────────────────
export const matchingService = {
  run: () => api.post('/matching/run', {}),
  getStats: () => api.get('/matching/stats'),
  getDecisions: (params = {}) => api.get('/matching/decisions', params),
  getDecisionById: (id) => api.get(`/matching/decisions/${id}`),
};

// ── Review Queue & Human-in-the-Loop Service ─────────────────────
export const reviewService = {
  list: (params = {}) => api.get('/reviews', params),
  getById: (reviewId) => api.get(`/reviews/${reviewId}`),
  approve: (reviewId, payload = {}) => api.post(`/reviews/${reviewId}/approve`, payload),
  reject: (reviewId, payload = {}) => api.post(`/reviews/${reviewId}/reject`, payload),
  manualMerge: (reviewId, payload) => api.post(`/reviews/${reviewId}/manual-merge`, payload),
  unmerge: (goldenCustomerId) => api.post(`/reviews/unmerge/${goldenCustomerId}`, {}),
};

// ── Opportunities Service ─────────────────────────────────────────
export const opportunityService = {
  list: (params = {}) => api.get('/opportunities', params),
  getDashboard: () => api.get('/opportunities/dashboard'),
  updateStatus: (opportunityId, status, rmId = null) =>
    api.patch(`/opportunities/${opportunityId}/status`, { status, assigned_rm_id: rmId }),
};

// ── Communication Service (Twilio WhatsApp) ──────────────────────
export const communicationService = {
  send: (payload) => api.post('/communications/send', payload),
  getHistory: (customerId) => api.get(`/communications/customer/${customerId}`),
};

// ── Analytics & Compliance Service ────────────────────────────────
export const analyticsService = {
  getMatchingStats: () => api.get('/matching/stats'),
  getDataQualityReport: () => api.get('/ingest/quality-report'),
  getAuditLogs: (params = {}) => api.get('/audit/logs', params),
  getConfigRules: () => api.get('/config/rules'),
  updateConfigRule: (ruleKey, ruleValue) => api.put(`/config/rules/${ruleKey}`, { rule_value: ruleValue }),
  previewRuleImpact: (ruleKey, newValue) => api.post('/config/rules/impact-preview', { rule_key: ruleKey, new_value: newValue }),
};

// ── Market Intelligence Service ───────────────────────────────────
export const marketService = {
  getQuotes: () => api.get('/market/quotes'),
  getTimeSeries: (symbol = 'TCS', range = '1M') => api.get('/market/timeseries', { symbol, range }),
  getPortfolioContext: () => api.get('/market/portfolio-context'),
};

// ── Nexus AI Service ──────────────────────────────────────────────
export const aiService = {
  chat: ({ page = 'general', context = {}, message = '' }) =>
    api.post('/ai/chat', { page, context, message }),
};
