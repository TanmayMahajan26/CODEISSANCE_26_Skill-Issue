/**
 * Nexus360 — API Service Layer
 * Wraps backend endpoints for seamless frontend integration.
 */

import { api } from './client';

// ── Admin Reset ───────────────────────────────────────────────────
export async function resetDemoData() {
  return await api.post('/health/reset-demo');
}

// ── Health Check ──────────────────────────────────────────────────
export async function checkBackendHealth() {
  try {
    return await api.get('/health');
  } catch (err) {
    return { status: 'offline', app: 'Nexus360', database: 'unreachable' };
  }
}

// ── Authentication ────────────────────────────────────────────────
export async function loginUser(usernameOrEmail, password) {
  // Use real backend auth
  return await api.post('/auth/login', {
    username_or_email: usernameOrEmail,
    password: password,
  });
}

export async function getCurrentUser() {
  return await api.get('/auth/me');
}

export async function getDemoUsers() {
  return await api.get('/auth/demo-users');
}

// ── Overview & Statistics ─────────────────────────────────────────
export async function getMatchingStats() {
  return await api.get('/matching/stats');
}

export async function getDataQualityReport() {
  return await api.get('/ingest/quality-report');
}

// ── Data Ingestion ────────────────────────────────────────────────
export async function uploadCSV(sourceSystem, file) {
  const formData = new FormData();
  formData.append('source_system', sourceSystem);
  formData.append('file', file);
  return await api.post('/ingest', formData);
}

export async function seedSyntheticData() {
  return await api.post('/ingest/seed', {});
}

export async function getSourceRecords(params = {}) {
  return await api.get('/source-records', params);
}

// ── Matching Engine ───────────────────────────────────────────────
export async function triggerMatchingPipeline() {
  return await api.post('/matching/run', {});
}

export async function getMatchDecisions(params = {}) {
  return await api.get('/matching/decisions', params);
}

// ── Customer 360 ──────────────────────────────────────────────────
export async function getCustomers(params = {}) {
  return await api.get('/customers', params);
}

export async function getCustomerById(customerId) {
  return await api.get(`/customers/${customerId}`);
}

export async function getCustomerGraph(customerId) {
  return await api.get(`/customers/${customerId}/graph`);
}

export async function getIdentityGraphAll(params = {}) {
  return await api.get('/customers/identity-graph/all', params);
}

export async function getCustomerWaterfall(customerId) {
  return await api.get(`/customers/${customerId}/waterfall`);
}

// ── Review Queue ──────────────────────────────────────────────────
export async function getReviewCases(params = {}) {
  return await api.get('/reviews', params);
}

export async function getReviewDetail(reviewId) {
  return await api.get(`/reviews/${reviewId}`);
}

export async function approveReviewCase(reviewId, payload = {}) {
  return await api.post(`/reviews/${reviewId}/approve`, payload);
}

export async function rejectReviewCase(reviewId, payload = {}) {
  return await api.post(`/reviews/${reviewId}/reject`, payload);
}

export async function manualMergeReviewCase(reviewId, payload) {
  return await api.post(`/reviews/${reviewId}/manual-merge`, payload);
}

export async function unmergeCustomer(goldenCustomerId) {
  return await api.post(`/reviews/unmerge/${goldenCustomerId}`, {});
}

// ── Identity Verification Escalation ──────────────────────────────
export async function getVerificationCases() {
  return await api.get('/verification/cases');
}

export async function triggerAIVerification(reviewId, targetPhone) {
  return await api.post(`/verification/${reviewId}/trigger-ai`, { target_phone: targetPhone });
}

// ── Opportunities ─────────────────────────────────────────────────
export async function getOpportunities(params = {}) {
  return await api.get('/opportunities', params);
}

export async function getOpportunitiesDashboard() {
  return await api.get('/opportunities/dashboard');
}

export async function updateOpportunityStatus(opportunityId, status, rmId = null) {
  return await api.patch(`/opportunities/${opportunityId}/status`, { status, assigned_rm_id: rmId });
}

// ── Business Rules (BRE) ──────────────────────────────────────────
export async function getConfigRules() {
  return await api.get('/config/rules');
}

export async function updateConfigRule(ruleKey, ruleValue) {
  return await api.put(`/config/rules/${ruleKey}`, { rule_value: ruleValue });
}

export async function previewRuleImpact(ruleKey, newValue) {
  return await api.post('/config/rules/impact-preview', { rule_key: ruleKey, new_value: newValue });
}

// ── Audit Logs ────────────────────────────────────────────────────
export async function getAuditLogs(params = {}) {
  return await api.get('/audit/logs', params);
}

// ── Nexus AI Assistant ────────────────────────────────────────────
export async function sendAIChatMessage({ page = 'general', context = {}, message = '' }) {
  return await api.post('/ai/chat', { page, context, message });
}

// ── Market Intelligence ───────────────────────────────────────────
export async function getMarketQuotes() {
  return await api.get('/market/quotes');
}

export async function getMarketTimeSeries(symbol = 'TCS', range = '1M') {
  return await api.get('/market/timeseries', { symbol, range });
}

export async function getMarketPortfolioContext() {
  return await api.get('/market/portfolio-context');
}

// ── RM Communications (Twilio WhatsApp) ───────────────────────────
export async function sendCommunication(payload) {
  return await api.post('/communications/send', payload);
}

export async function getCommunicationHistory(customerId) {
  return await api.get(`/communications/customer/${customerId}`);
}

// ── Export Centralized Modular Services ───────────────────────────
export * from './services';
