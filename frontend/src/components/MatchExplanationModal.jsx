import React from 'react';
import {
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Info,
  Shield,
  X,
  Layers,
  Cpu,
  GitMerge,
} from 'lucide-react';
import { formatPercent } from '../utils/formatters';

/**
 * MatchExplanationModal — Enterprise Explainability & Side-by-Side Comparison Modal
 * Visualizes:
 * 1. Side-by-side Record A vs Record B comparison with field statuses (Exact Match, Similar, Missing, Conflict)
 * 2. Clear separation of Rule-Based Confidence vs AI/ML Similarity Confidence vs Final Decision
 * 3. Dynamic explanation generated from actual matching data
 * 4. Missing ≠ Mismatch visual callout & Color Legend
 * 5. High-Risk Conflict detection flags
 */
export function MatchExplanationModal({ decision, reviewCase, onClose, onApprove, onReject, onManualMerge, userRole }) {
  if (!decision && !reviewCase) return null;

  // Resolve Record A and Record B
  const recA = reviewCase?.record_a || decision?.record_a || reviewCase?.details?.record_a || {};
  const recB = reviewCase?.record_b || decision?.record_b || reviewCase?.details?.record_b || {};

  // Scores
  const ruleScore = decision?.final_score ?? 0.0;
  const aiScore = decision?.name_semantic_similarity ?? 0.0;
  const finalScore = decision?.final_score ?? reviewCase?.final_score ?? 0.0;
  const decisionType = decision?.decision || (finalScore >= 0.85 ? 'MATCH' : finalScore >= 0.6 ? 'REVIEW' : 'NON_MATCH');

  // Conflict Detection
  const hasPanConflict = recA.original_pan && recB.original_pan && recA.original_pan.toUpperCase() !== recB.original_pan.toUpperCase();
  const isHighRiskConflict = hasPanConflict || (decisionType === 'REVIEW' && hasPanConflict);

  // Field Level Evaluation Grid
  const getFieldStatus = (key) => {
    const comp = reviewCase?.field_comparisons?.find(f => f.field_name === key);
    if (!comp) return 'MISSING';
    if (comp.status === 'MATCH') return 'EXACT';
    if (comp.status === 'DIFFERENT') return 'CONFLICT';
    if (comp.status === 'PARTIAL') return 'SIMILAR';
    return 'MISSING';
  };

  const getFieldScore = (key) => {
    const comp = reviewCase?.field_comparisons?.find(f => f.field_name === key);
    return comp ? `${(comp.score * 100).toFixed(0)}%` : 'N/A';
  };

  const fields = [
    {
      key: 'name',
      label: 'Full Name',
      valA: recA.original_name || '—',
      valB: recB.original_name || '—',
      similarity: getFieldScore('name_string'),
      status: getFieldStatus('name_string'),
    },
    {
      key: 'pan',
      label: 'PAN Number',
      valA: recA.original_pan || 'Not available',
      valB: recB.original_pan || 'Not available',
      similarity: getFieldScore('pan'),
      status: getFieldStatus('pan'),
    },
    {
      key: 'mobile',
      label: 'Mobile Number',
      valA: recA.original_mobile || `Missing in ${recA.source_system || 'Source A'}`,
      valB: recB.original_mobile || `Missing in ${recB.source_system || 'Source B'}`,
      similarity: getFieldScore('mobile'),
      status: getFieldStatus('mobile'),
    },
    {
      key: 'dob',
      label: 'Date of Birth',
      valA: recA.original_dob || '—',
      valB: recB.original_dob || '—',
      similarity: getFieldScore('dob'),
      status: getFieldStatus('dob'),
    },
    {
      key: 'email',
      label: 'Email Address',
      valA: recA.original_email || '—',
      valB: recB.original_email || '—',
      similarity: getFieldScore('email'),
      status: getFieldStatus('email'),
    },
    {
      key: 'city',
      label: 'City / Location',
      valA: recA.original_city || '—',
      valB: recB.original_city || '—',
      similarity: getFieldScore('city'),
      status: getFieldStatus('city'),
    },
  ];

  // Helper for Status Badge
  const getStatusBadge = (field) => {
    switch (field.status) {
      case 'EXACT':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
            ✓ Exact Match
          </span>
        );
      case 'SIMILAR':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200 flex items-center gap-1">
            ~ Similar ({field.similarity})
          </span>
        );
      case 'MISSING':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200 flex items-center gap-1">
            — Missing Neutral
          </span>
        );
      case 'CONFLICT':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800 border border-red-200 flex items-center gap-1">
            ⚠ Conflict
          </span>
        );
      case 'MISMATCH':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200 flex items-center gap-1">
            ✕ Mismatch
          </span>
        );
      default:
        return null;
    }
  };

  // Generate dynamic explanation strictly from available fields
  const generateDynamicExplanation = () => {
    return reviewCase?.explanation?.summary || 'Explanation not available for this case.';
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-3xl max-w-4xl w-full p-6 sm:p-8 shadow-card-hover border border-slate-200 space-y-6 my-8 animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-subtle font-bold">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 font-display">
                Match Details & Explainability Diagnostics
              </h3>
              <p className="text-xs text-slate-500">
                Side-by-side source comparison, rule vs AI score breakdown, and conflict detection.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* High-Risk Conflict Alert Banner */}
        {isHighRiskConflict && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex items-start gap-3 text-xs text-red-950">
            <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <div className="font-bold uppercase tracking-wider text-red-800">
                HIGH-RISK CONFLICT DETECTED
              </div>
              <p className="mt-0.5 leading-relaxed">
                Critical identifier mismatch detected (PAN mismatch). Automatic merging was stopped by the Identity Engine. Human-in-the-loop review is required before entity consolidation.
              </p>
            </div>
          </div>
        )}

        {/* ── 3 DISTINCT CONFIDENCE CARDS (Requirement 2) ────────── */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Card 1: Rule-Based Confidence */}
          <div className="bg-blue-50/60 border border-blue-200 rounded-2xl p-4 space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-blue-900">
              <span>Rule-Based Confidence</span>
              <Cpu className="w-4 h-4 text-blue-600" />
            </div>
            <div className="text-2xl font-extrabold text-blue-900 font-mono">
              {(ruleScore * 100).toFixed(0)}%
            </div>
            <div className="text-[11px] text-blue-700 space-y-0.5 font-medium">
              <div>• PAN Match: {decision?.pan_match === 1.0 ? '100%' : '0%'}</div>
              <div>• Mobile: {decision?.mobile_match === 1.0 ? '100%' : '0%'}</div>
              <div>• Name Similarity: {((decision?.name_similarity || 0) * 100).toFixed(0)}%</div>
            </div>
          </div>

          {/* Card 2: AI / ML Similarity Confidence */}
          <div className="bg-purple-50/60 border border-purple-200 rounded-2xl p-4 space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-purple-900">
              <span>AI / ML Similarity Confidence</span>
              <Sparkles className="w-4 h-4 text-purple-600" />
            </div>
            <div className="text-2xl font-extrabold text-purple-900 font-mono">
              {(aiScore * 100).toFixed(0)}%
            </div>
            <div className="text-[11px] text-purple-700 space-y-0.5 font-medium">
              <div>• 384-Dim Sentence Transformer</div>
              <div>• Vector Cosine Embedding</div>
              <div>• Typo & Alias Resilient</div>
            </div>
          </div>

          {/* Card 3: Final Decision */}
          <div className={`border rounded-2xl p-4 space-y-2 ${
            decisionType === 'MATCH'
              ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950'
              : decisionType === 'REVIEW'
              ? 'bg-amber-50/80 border-amber-300 text-amber-950'
              : 'bg-slate-100 border-slate-300 text-slate-900'
          }`}>
            <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider">
              <span>Final Decision</span>
              <Shield className="w-4 h-4" />
            </div>
            <div className="text-xl font-extrabold font-mono">
              {decisionType === 'MATCH' ? 'STRONG MATCH' : decisionType === 'REVIEW' ? 'NEEDS REVIEW' : 'NON-MATCH'}
            </div>
            <div className="text-xs font-bold font-mono">
              {(finalScore * 100).toFixed(0)}% Final Confidence
            </div>
          </div>
        </div>

        {/* Dynamic Explanation Summary */}
        <div className="p-4 bg-slate-900 text-white rounded-2xl text-xs space-y-2">
          <div className="font-bold text-emerald-400 flex items-center gap-1.5 uppercase tracking-wider">
            <Info className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>AI Reasoning & Survivorship Explanation</span>
          </div>
          <p className="text-slate-200 leading-relaxed font-sans">
            "{generateDynamicExplanation()}"
          </p>
        </div>

        {/* ── SIDE-BY-SIDE FIELD COMPARISON TABLE (Requirement 1 & 3) ── */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Attribute Comparison (Record A vs Record B)
            </h4>
            {/* Color Legend (Requirement 3) */}
            <div className="flex items-center gap-3 text-[10px] font-semibold text-slate-500">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Green = Match</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500" /> Blue = Similar</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> Red = Conflict</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-slate-400" /> Grey = Missing Data</span>
            </div>
          </div>

          <div className="overflow-hidden border border-slate-200 rounded-2xl shadow-xs">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-100 border-b border-slate-200 text-slate-600 font-bold uppercase text-[10px]">
                  <th className="py-2.5 px-4">Field</th>
                  <th className="py-2.5 px-4 bg-blue-50/50 text-blue-900">Record A ({recA.source_system || 'EQUITY'})</th>
                  <th className="py-2.5 px-4 bg-purple-50/50 text-purple-900">Record B ({recB.source_system || 'MUTUAL_FUND'})</th>
                  <th className="py-2.5 px-4 text-center">Match Evaluation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {fields.map((f) => (
                  <tr key={f.key} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-800">{f.label}</td>
                    <td className="py-3 px-4 font-mono text-slate-900">
                      {f.valA.includes('Missing in') ? (
                        <span className="text-slate-400 italic font-sans">{f.valA}</span>
                      ) : (
                        f.valA
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-900">
                      {f.valB.includes('Missing in') ? (
                        <span className="text-slate-400 italic font-sans">{f.valB}</span>
                      ) : (
                        f.valB
                      )}
                    </td>
                    <td className="py-3 px-4 flex justify-center">{getStatusBadge(f)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Missing != Mismatch Banner (Requirement 3) */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center gap-2 text-[11px] text-slate-600 font-medium">
            <Info className="w-4 h-4 text-slate-400 shrink-0" />
            <span>
              <strong>Missing ≠ Mismatch</strong>: Missing attributes in one source system are handled as neutral context and do not penalize remaining strong identifiers.
            </span>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-4 border-t border-slate-200">
          <div className="text-xs text-slate-400 font-mono">
            Nexus360 Rule-Engine & Semantic Resolver
          </div>

          <div className="flex items-center gap-3">
            {onReject && (userRole === 'ADMIN' || userRole === 'REVIEWER') && (
              <button
                onClick={onReject}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-xl flex items-center gap-1"
              >
                <XCircle className="w-4 h-4 text-red-600" />
                Reject Match
              </button>
            )}

            {onManualMerge && userRole === 'ADMIN' && (
              <button
                onClick={onManualMerge}
                className="px-4 py-2 bg-amber-50 hover:bg-amber-100 border border-amber-300 text-amber-900 text-xs font-bold rounded-xl flex items-center gap-1"
              >
                <GitMerge className="w-4 h-4 text-amber-700" />
                Manual Merge...
              </button>
            )}

            {onApprove && (userRole === 'ADMIN' || userRole === 'REVIEWER') && (
              <button
                onClick={onApprove}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-xs flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-4 h-4" />
                Approve Match
              </button>
            )}

            <button
              onClick={onClose}
              className="px-4 py-2 bg-white border border-slate-300 text-slate-700 text-xs font-semibold rounded-xl hover:bg-slate-50"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
