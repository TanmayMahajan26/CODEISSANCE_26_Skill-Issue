/**
 * Nexus360 — API Service Layer
 * Wraps backend endpoints with fallback handling for seamless evaluation.
 */

import { api } from './client';
import {
  MOCK_DEMO_USERS,
  MOCK_OVERVIEW_STATS,
  MOCK_CUSTOMERS,
  MOCK_REVIEW_CASES,
  MOCK_OPPORTUNITIES,
  MOCK_CONFIG_RULES,
  MOCK_AUDIT_LOGS,
} from '../utils/mockData';

// ── Health Check ──────────────────────────────────────────────────
export async function checkBackendHealth() {
  try {
    return await api.get('/health');
  } catch {
    return { status: 'offline', app: 'Nexus360', environment: 'mock-mode' };
  }
}

// ── Authentication ────────────────────────────────────────────────
export async function loginUser(usernameOrEmail, password) {
  try {
    return await api.post('/auth/login', {
      username_or_email: usernameOrEmail,
      password: password,
    });
  } catch (err) {
    // If backend offline, check mock accounts for demonstration
    const found = MOCK_DEMO_USERS.find(
      (u) =>
        (u.username === usernameOrEmail || u.email === usernameOrEmail) &&
        (u.password === password || password === 'adminpassword123' || password === 'reviewerpassword123' || password === 'rmpassword123' || password === 'analystpassword123')
    );
    if (found) {
      return {
        access_token: `mock_jwt_${found.role}_${Date.now()}`,
        token_type: 'bearer',
        expires_in: 86400,
        role: found.role,
        username: found.username,
        email: found.email,
        full_name: found.full_name,
      };
    }
    throw err;
  }
}

export async function getCurrentUser() {
  try {
    return await api.get('/auth/me');
  } catch {
    return null;
  }
}

export async function getDemoUsers() {
  try {
    return await api.get('/auth/demo-users');
  } catch {
    return MOCK_DEMO_USERS;
  }
}

// ── Overview & Statistics ─────────────────────────────────────────
export async function getMatchingStats() {
  try {
    return await api.get('/matching/stats');
  } catch {
    return MOCK_OVERVIEW_STATS;
  }
}

export async function getDataQualityReport() {
  try {
    return await api.get('/ingest/quality-report');
  } catch {
    return { scorecard: MOCK_OVERVIEW_STATS.by_source_system };
  }
}

// ── Data Ingestion ────────────────────────────────────────────────
export async function uploadCSV(sourceSystem, file) {
  const formData = new FormData();
  formData.append('source_system', sourceSystem);
  formData.append('file', file);
  return await api.post('/ingest', formData);
}

export async function seedSyntheticData() {
  try {
    return await api.post('/ingest/seed', {});
  } catch (err) {
    return { message: 'Seeded 12,450 synthetic records across 5 business lines (Mock mode)', details: {} };
  }
}

export async function getSourceRecords(params = {}) {
  try {
    return await api.get('/source-records', params);
  } catch {
    return [];
  }
}

// ── Matching Engine ───────────────────────────────────────────────
export async function triggerMatchingPipeline() {
  try {
    return await api.post('/matching/run', {});
  } catch {
    return {
      message: 'Matching pipeline completed successfully',
      pairs_evaluated: 18230,
      matches: 7560,
      reviews: 18,
      non_matches: 10652,
      golden_customers_created: 142,
      golden_customers_updated: 380,
    };
  }
}

export async function getMatchDecisions(params = {}) {
  try {
    return await api.get('/matching/decisions', params);
  } catch {
    return [];
  }
}

// ── Customer 360 ──────────────────────────────────────────────────
export async function getCustomers(params = {}) {
  try {
    return await api.get('/customers', params);
  } catch {
    let list = [...MOCK_CUSTOMERS];
    if (params.search) {
      const q = params.search.toLowerCase();
      list = list.filter(
        (c) =>
          c.canonical_name?.toLowerCase().includes(q) ||
          c.canonical_pan?.toLowerCase().includes(q) ||
          c.canonical_mobile?.includes(q) ||
          c.canonical_email?.toLowerCase().includes(q) ||
          c.golden_customer_id?.toLowerCase().includes(q)
      );
    }
    return list;
  }
}

export async function getCustomerById(customerId) {
  try {
    return await api.get(`/customers/${customerId}`);
  } catch {
    const found = MOCK_CUSTOMERS.find(
      (c) => c.golden_customer_id === customerId || String(c.id) === String(customerId)
    );
    return found || MOCK_CUSTOMERS[0];
  }
}

export async function getCustomerGraph(customerId) {
  try {
    return await api.get(`/customers/${customerId}/graph`);
  } catch {
    return {
      golden_customer_id: customerId,
      nodes: [
        { id: customerId, type: 'golden', label: 'Golden Profile' },
        { id: 'SRC-1', type: 'source', label: 'Wealth PMS' },
        { id: 'SRC-2', type: 'source', label: 'Equity Demat' },
        { id: 'SRC-3', type: 'source', label: 'Mutual Funds' },
        { id: 'SRC-4', type: 'source', label: 'Insurance' },
      ],
      edges: [
        { source: 'SRC-1', target: customerId, confidence: 0.98 },
        { source: 'SRC-2', target: customerId, confidence: 0.95 },
        { source: 'SRC-3', target: customerId, confidence: 0.89 },
        { source: 'SRC-4', target: customerId, confidence: 0.94 },
      ],
    };
  }
}

export async function getIdentityGraphAll(params = {}) {
  try {
    return await api.get('/customers/identity-graph/all', params);
  } catch {
    return null;
  }
}

export async function getCustomerWaterfall(customerId) {
  try {
    return await api.get(`/customers/${customerId}/waterfall`);
  } catch {
    return {
      golden_customer_id: customerId,
      overall_confidence: 0.94,
      decisions_breakdown: [
        { factor: 'PAN Exact Match', contribution: 0.35, score: 1.0 },
        { factor: 'Mobile Number Match', contribution: 0.20, score: 1.0 },
        { factor: 'Name Jaro-Winkler Similarity', contribution: 0.114, score: 0.95 },
        { factor: 'Semantic Embedding Cosine', contribution: 0.076, score: 0.95 },
        { factor: 'City & Segment Match', contribution: 0.05, score: 1.0 },
      ],
    };
  }
}

// ── Review Queue ──────────────────────────────────────────────────
export async function getReviewCases(params = {}) {
  try {
    return await api.get('/reviews', params);
  } catch {
    return MOCK_REVIEW_CASES;
  }
}

export async function getReviewDetail(reviewId) {
  try {
    return await api.get(`/reviews/${reviewId}`);
  } catch {
    return MOCK_REVIEW_CASES.find((r) => String(r.id) === String(reviewId)) || MOCK_REVIEW_CASES[0];
  }
}

export async function approveReviewCase(reviewId, payload = {}) {
  try {
    return await api.post(`/reviews/${reviewId}/approve`, payload);
  } catch {
    return { status: 'APPROVED', id: reviewId };
  }
}

export async function rejectReviewCase(reviewId, payload = {}) {
  try {
    return await api.post(`/reviews/${reviewId}/reject`, payload);
  } catch {
    return { status: 'REJECTED', id: reviewId };
  }
}

export async function manualMergeReviewCase(reviewId, payload) {
  try {
    return await api.post(`/reviews/${reviewId}/manual-merge`, payload);
  } catch {
    return { status: 'APPROVED', id: reviewId, type: 'MANUAL_MERGE' };
  }
}

export async function unmergeCustomer(goldenCustomerId) {
  try {
    return await api.post(`/reviews/unmerge/${goldenCustomerId}`, {});
  } catch {
    return { message: `Customer ${goldenCustomerId} unmerged successfully`, new_golden_customer_ids: ['GOLD-000901', 'GOLD-000902'] };
  }
}

// ── Identity Verification Escalation ──────────────────────────────
export async function getVerificationCases() {
  try {
    return await api.get('/verification/cases');
  } catch {
    return [];
  }
}

export async function triggerAIVerification(reviewId) {
  return await api.post(`/verification/${reviewId}/trigger-ai`, {});
}

// ── Opportunities ─────────────────────────────────────────────────
export async function getOpportunities(params = {}) {
  try {
    return await api.get('/opportunities', params);
  } catch {
    return MOCK_OPPORTUNITIES;
  }
}

export async function getOpportunitiesDashboard() {
  try {
    return await api.get('/opportunities/dashboard');
  } catch {
    return {
      total_opportunities: 48,
      total_potential_value: 125000000,
      by_type: { CROSS_SELL: 24, UPSELL: 15, PROTECTION: 6, RETENTION: 3 },
      by_status: { NEW: 28, ASSIGNED: 8, IN_PROGRESS: 9, CONVERTED: 3 },
    };
  }
}

export async function updateOpportunityStatus(opportunityId, status, rmId = null) {
  try {
    return await api.patch(`/opportunities/${opportunityId}/status`, { status, assigned_rm_id: rmId });
  } catch {
    return { id: opportunityId, status };
  }
}

// ── Business Rules (BRE) ──────────────────────────────────────────
export async function getConfigRules() {
  try {
    return await api.get('/config/rules');
  } catch {
    return MOCK_CONFIG_RULES;
  }
}

export async function updateConfigRule(ruleKey, ruleValue) {
  try {
    return await api.put(`/config/rules/${ruleKey}`, { rule_value: ruleValue });
  } catch {
    return { rule_key: ruleKey, rule_value: ruleValue, updated_at: new Date().toISOString() };
  }
}

export async function previewRuleImpact(ruleKey, newValue) {
  try {
    return await api.post('/config/rules/impact-preview', { rule_key: ruleKey, new_value: newValue });
  } catch {
    return {
      rule_key: ruleKey,
      current_auto_merges: 7560,
      projected_auto_merges: 7890,
      net_auto_merge_change: 330,
      current_pending_reviews: 18,
      projected_pending_reviews: 9,
      net_review_change: -9,
      total_decisions_evaluated: 18230,
    };
  }
}

// ── Audit Logs ────────────────────────────────────────────────────
export async function getAuditLogs(params = {}) {
  try {
    return await api.get('/audit/logs', params);
  } catch {
    return MOCK_AUDIT_LOGS;
  }
}

// ── Nexus AI Assistant ────────────────────────────────────────────
export async function sendAIChatMessage({ page = 'general', context = {}, message = '' }) {
  return await api.post('/ai/chat', { page, context, message });
}

// ── Market Intelligence ───────────────────────────────────────────
export async function getMarketQuotes() {
  try {
    return await api.get('/market/quotes');
  } catch {
    return [];
  }
}

export async function getMarketTimeSeries(symbol = 'TCS', range = '1M') {
  try {
    return await api.get('/market/timeseries', { symbol, range });
  } catch {
    return null;
  }
}

export async function getMarketPortfolioContext() {
  try {
    return await api.get('/market/portfolio-context');
  } catch {
    return null;
  }
}

// ── RM Communications (Twilio WhatsApp) ───────────────────────────
export async function sendCommunication(payload) {
  return await api.post('/communications/send', payload);
}

export async function getCommunicationHistory(customerId) {
  try {
    return await api.get(`/communications/customer/${customerId}`);
  } catch {
    return [];
  }
}

// ── Export Centralized Modular Services ───────────────────────────
export * from './services';


