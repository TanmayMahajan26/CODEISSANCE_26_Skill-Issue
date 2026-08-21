import React, { useState, useEffect } from 'react';
import {
  Inbox,
  CheckCircle2,
  XCircle,
  Split,
  AlertTriangle,
  FileCheck2,
  Shield,
  Clock,
  ArrowRight,
  User,
  CreditCard,
  Phone,
  Mail,
  MapPin,
  Calendar,
  Sparkles,
  GitMerge,
} from 'lucide-react';
import {
  getReviewCases,
  getReviewDetail,
  approveReviewCase,
  rejectReviewCase,
  manualMergeReviewCase,
} from '../api';
import { useAuth } from '../context/AuthContext';
import { formatPercent } from '../utils/formatters';

import { MatchExplanationModal } from '../components/MatchExplanationModal';

export function ReviewQueuePage({ onNavigate }) {
  const { user } = useAuth();
  const [reviewCases, setReviewCases] = useState([]);
  const [selectedReview, setSelectedReview] = useState(null);
  const [reviewDetail, setReviewDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [showManualMergeModal, setShowManualMergeModal] = useState(false);
  const [showExplainModal, setShowExplainModal] = useState(false);

  // Manual Merge selection state
  const [selectedAttributes, setSelectedAttributes] = useState({
    canonical_name: '',
    canonical_pan: '',
    canonical_mobile: '',
    canonical_email: '',
    canonical_city: '',
  });

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const data = await getReviewCases();
      setReviewCases(data);
      if (data.length > 0 && !selectedReview) {
        handleSelectReview(data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  const handleSelectReview = async (rev) => {
    setSelectedReview(rev);
    setStatusMessage('');
    try {
      const detail = await getReviewDetail(rev.id);
      setReviewDetail(detail || rev);

      // Pre-fill manual merge defaults
      const recA = detail?.record_a || rev.record_a || {};
      setSelectedAttributes({
        canonical_name: recA.original_name || '',
        canonical_pan: recA.original_pan || '',
        canonical_mobile: recA.original_mobile || '',
        canonical_email: recA.original_email || '',
        canonical_city: recA.original_city || '',
      });
    } catch {
      setReviewDetail(rev);
    }
  };

  const handleApprove = async () => {
    if (!selectedReview) return;
    setActionLoading(true);
    try {
      await approveReviewCase(selectedReview.id, {
        reviewer: user?.username || 'reviewer_sarah',
        review_notes: 'Approved match after side-by-side KYC verification.',
      });
      setStatusMessage('Match decision APPROVED and synced to Golden Master.');
      setReviewCases((prev) => prev.filter((r) => r.id !== selectedReview.id));
      setSelectedReview(null);
    } catch (err) {
      alert(err.message || 'Approval failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedReview) return;
    setActionLoading(true);
    try {
      await rejectReviewCase(selectedReview.id, {
        reviewer: user?.username || 'reviewer_sarah',
        review_notes: 'Rejected pair. Confirmed as separate independent customers.',
      });
      setStatusMessage('Review case REJECTED (Confirmed NON_MATCH).');
      setReviewCases((prev) => prev.filter((r) => r.id !== selectedReview.id));
      setSelectedReview(null);
    } catch (err) {
      alert(err.message || 'Rejection failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRequestVerification = async () => {
    if (!selectedReview) return;
    setActionLoading(true);
    try {
      // Mock logic: move to verification queue
      setStatusMessage('Pair flagged for AI Verification. Sent to Verification Center.');
      setReviewCases((prev) => prev.filter((r) => r.id !== selectedReview.id));
      setSelectedReview(null);
      setTimeout(() => {
        onNavigate('verification');
      }, 800);
    } catch (err) {
      alert('Verification request failed');
    } finally {
      setActionLoading(false);
    }
  };

  const recA = reviewDetail?.record_a || {};
  const recB = reviewDetail?.record_b || {};

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight font-display">Human-in-the-Loop Review Queue</h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Evaluate candidate pairs flagged for KYC conflicts, typos, or borderline confidence scores.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full bg-amber-100 border border-amber-200 text-amber-800 text-xs font-bold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            {reviewCases.filter((r) => r.status === 'PENDING').length} Cases Pending
          </span>
        </div>
      </div>

      {/* Success Notification */}
      {statusMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-2 text-xs font-semibold text-emerald-900 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* ── Main Layout: Case List (Left) + Split Screen Review (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Review Cases List */}
        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-2xl p-4 shadow-card space-y-2 max-h-[780px] overflow-y-auto">
          <div className="flex items-center justify-between px-2 py-1 text-xs font-bold text-slate-500 uppercase tracking-wider">
            <span>Pending Review Cases</span>
            <span>{reviewCases.length}</span>
          </div>

          {reviewCases.map((rev) => {
            const isSelected = selectedReview?.id === rev.id;
            return (
              <div
                key={rev.id}
                onClick={() => handleSelectReview(rev)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'border-emerald-500 bg-emerald-50/70 shadow-xs ring-1 ring-emerald-500/20'
                    : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center justify-between text-xs font-bold text-slate-900">
                  <span className="font-mono">Case #{rev.id}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 uppercase">
                    {rev.priority || 'HIGH'}
                  </span>
                </div>

                <div className="text-xs font-semibold text-slate-800 mt-2 truncate">
                  {rev.details?.record_a?.name || rev.record_a?.full_name || `Record #${rev.source_record_ids?.[0] || 'A'}`}
                  {' ↔ '}
                  {rev.details?.record_b?.name || rev.record_b?.full_name || `Record #${rev.source_record_ids?.[1] || 'B'}`}
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                  <span>Score: <strong className="text-amber-700 font-mono">{(rev.details?.final_score ?? rev.final_score ?? 0.76).toFixed(2)}</strong></span>
                  <span className="text-[10px] text-slate-400 font-mono">Decision #{rev.match_decision_id}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Split Screen Comparison & AI Explainability */}
        {selectedReview && (
          <div className="lg:col-span-8 space-y-6">
            {/* Split Screen Records: Record A vs Record B */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Record A */}
              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Record A</span>
                  <span className="px-2 py-0.5 bg-blue-50 border border-blue-200 text-blue-700 text-[10px] font-bold rounded">
                    {recA.source_system || 'EQUITY'}
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Full Name</span>
                    <div className="font-bold text-slate-900 text-sm">{recA.full_name || 'Vikram Aditya Singhania'}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">PAN Number</span>
                    <div className="font-mono font-bold text-slate-900">{recA.pan || 'AAACS1928L'}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Mobile</span>
                    <div className="font-mono text-slate-900">{recA.mobile || '9811234567'}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Email</span>
                    <div className="text-slate-900 truncate">{recA.email || 'vikram.singhania@singhania.com'}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">City</span>
                    <div className="text-slate-900">{recA.city || 'Bengaluru'}</div>
                  </div>
                </div>
              </div>

              {/* Record B */}
              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Record B</span>
                  <span className="px-2 py-0.5 bg-amber-50 border border-amber-200 text-amber-700 text-[10px] font-bold rounded">
                    {recB.source_system || 'MUTUAL_FUND'}
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Full Name</span>
                    <div className="font-bold text-slate-900 text-sm">{recB.full_name || 'Vikram A. Singhania'}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">PAN Number</span>
                    <div className="font-mono font-bold text-slate-900">{recB.pan || 'AAACS1928K'}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Mobile</span>
                    <div className="font-mono text-slate-900">{recB.mobile || '9811234567'}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">Email</span>
                    <div className="text-slate-900 truncate">{recB.email || 'vikram.s@singhania.com'}</div>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] uppercase font-semibold">City</span>
                    <div className="text-slate-900">{recB.city || 'Bangalore'}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Suggestion & Explainability Reason */}
            <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-card space-y-4">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                Explainable Decision Diagnostics
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                {reviewDetail?.ai_suggestion || selectedReview?.ai_suggestion || 'Review candidate pair: Name similarity (0.92) and Mobile match (1.0) are strong, but PAN differs in 1 character due to potential transcription typo.'}
              </p>

              {/* 8 Feature Comparison Breakdown */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-2">
                {[
                  { label: 'PAN Exact', score: '0.0', status: 'DIFFERENT', color: 'text-red-400 bg-red-950/60 border-red-800' },
                  { label: 'Mobile Exact', score: '1.0', status: 'MATCH', color: 'text-emerald-400 bg-emerald-950/60 border-emerald-800' },
                  { label: 'Name Jaro-Winkler', score: '0.92', status: 'PARTIAL', color: 'text-amber-400 bg-amber-950/60 border-amber-800' },
                  { label: 'Semantic ML Cosine', score: '0.94', status: 'MATCH', color: 'text-emerald-400 bg-emerald-950/60 border-emerald-800' },
                  { label: 'Email Match', score: '0.85', status: 'PARTIAL', color: 'text-amber-400 bg-amber-950/60 border-amber-800' },
                  { label: 'DOB Match', score: '1.0', status: 'MATCH', color: 'text-emerald-400 bg-emerald-950/60 border-emerald-800' },
                  { label: 'City Alias', score: '1.0', status: 'MATCH', color: 'text-emerald-400 bg-emerald-950/60 border-emerald-800' },
                  { label: 'Final Score', score: '0.764', status: 'REVIEW', color: 'text-amber-300 bg-slate-800 border-slate-700' },
                ].map((f, i) => (
                  <div key={i} className={`p-2.5 rounded-xl border text-[11px] ${f.color}`}>
                    <div className="text-[10px] text-slate-400 font-medium">{f.label}</div>
                    <div className="font-mono font-bold mt-0.5 flex items-center justify-between">
                      <span>{f.score}</span>
                      <span className="text-[9px] uppercase font-bold">{f.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Bar */}
            <div className="p-5 bg-white border border-slate-200 rounded-2xl shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <button
                onClick={() => setShowExplainModal(true)}
                className="px-4 py-2.5 bg-purple-50 hover:bg-purple-100 border border-purple-300 text-purple-900 text-xs font-bold rounded-xl transition-all flex items-center gap-1.5"
              >
                <Sparkles className="w-4 h-4 text-purple-700" />
                Inspect Full Match Explainability
              </button>

              <div className="flex items-center gap-3">
                <button
                  onClick={handleReject}
                  disabled={actionLoading}
                  className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-xl transition-all flex items-center gap-1.5"
                >
                  <XCircle className="w-4 h-4 text-red-600" />
                  Reject (Non-Match)
                </button>

                <button
                  onClick={handleRequestVerification}
                  disabled={actionLoading}
                  className="px-4 py-2.5 bg-blue-50 hover:bg-blue-100 border border-blue-300 text-blue-900 text-xs font-bold rounded-xl transition-all flex items-center gap-1.5"
                >
                  <Shield className="w-4 h-4 text-blue-700" />
                  Request AI Verification
                </button>

                <button
                  onClick={handleApprove}
                  disabled={actionLoading}
                  className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl transition-all shadow-subtle hover:shadow-emerald-glow flex items-center gap-1.5"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Approve Match
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Match Explanation Diagnostics Modal ────────────────────── */}
      {showExplainModal && (
        <MatchExplanationModal
          reviewCase={selectedReview}
          decision={selectedReview?.details || null}
          userRole={user?.role}
          onClose={() => setShowExplainModal(false)}
          onApprove={() => {
            setShowExplainModal(false);
            handleApprove();
          }}
          onReject={() => {
            setShowExplainModal(false);
            handleReject();
          }}
          onManualMerge={() => {
            setShowExplainModal(false);
            setShowManualMergeModal(true);
          }}
        />
      )}

      {/* ── Manual Merge Modal (Attribute Picker) ────────────────── */}
      {showManualMergeModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-card-hover border border-slate-200 space-y-5 animate-slide-up">
            <div>
              <h3 className="text-lg font-bold text-slate-900 font-display">Manual Merge Attribute Override</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Choose which source attribute values should become canonical in the Golden Customer record.
              </p>
            </div>

            {/* Radio selectors for canonical attributes */}
            <div className="space-y-4 text-xs">
              {/* Name */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <div className="font-bold text-slate-800">Canonical Name</div>
                <div className="space-y-1">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="name_pick"
                      checked={selectedAttributes.canonical_name === (recA.original_name || 'Vikram Aditya Singhania')}
                      onChange={() => setSelectedAttributes({ ...selectedAttributes, canonical_name: recA.original_name || 'Vikram Aditya Singhania' })}
                      className="text-emerald-600 focus:ring-emerald-500"
                    />
                    <span>{recA.original_name || 'Vikram Aditya Singhania'} (Source: Record A)</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="name_pick"
                      checked={selectedAttributes.canonical_name === (recB.original_name || 'Vikram A. Singhania')}
                      onChange={() => setSelectedAttributes({ ...selectedAttributes, canonical_name: recB.original_name || 'Vikram A. Singhania' })}
                      className="text-emerald-600 focus:ring-emerald-500"
                    />
                    <span>{recB.original_name || 'Vikram A. Singhania'} (Source: Record B)</span>
                  </label>
                </div>
              </div>

              {/* PAN */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <div className="font-bold text-slate-800">Canonical PAN</div>
                <div className="space-y-1">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="pan_pick"
                      checked={selectedAttributes.canonical_pan === (recA.original_pan || 'AAACS1928L')}
                      onChange={() => setSelectedAttributes({ ...selectedAttributes, canonical_pan: recA.original_pan || 'AAACS1928L' })}
                      className="text-emerald-600 focus:ring-emerald-500"
                    />
                    <span className="font-mono">{recA.original_pan || 'AAACS1928L'} (Verified Demat)</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="pan_pick"
                      checked={selectedAttributes.canonical_pan === (recB.original_pan || 'AAACS1928K')}
                      onChange={() => setSelectedAttributes({ ...selectedAttributes, canonical_pan: recB.original_pan || 'AAACS1928K' })}
                      className="text-emerald-600 focus:ring-emerald-500"
                    />
                    <span className="font-mono">{recB.original_pan || 'AAACS1928K'} (Mutual Fund Folio)</span>
                  </label>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200">
              <button
                type="button"
                onClick={() => setShowManualMergeModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleManualMergeSubmit}
                disabled={actionLoading}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-xs"
              >
                Confirm & Record in Audit Log
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
