import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Save,
  CheckCircle2,
  AlertTriangle,
  ArrowUpDown,
  Shield,
  Layers,
  Sparkles,
  Info,
} from 'lucide-react';
import { getConfigRules, updateConfigRule } from '../api';
import { useAuth } from '../context/AuthContext';

export function BusinessRulesPage() {
  const { user } = useAuth();
  const [rules, setRules] = useState([]);
  const [sourceOrder, setSourceOrder] = useState(['WEALTH', 'BANKING', 'EQUITY', 'MUTUAL_FUND', 'INSURANCE', 'LOAN']);
  const [thresholds, setThresholds] = useState({ match_threshold: 0.85, review_threshold: 0.60 });
  const [weights, setWeights] = useState({
    pan_exact: 0.35,
    mobile_exact: 0.20,
    email_exact: 0.15,
    name_similarity: 0.12,
    name_semantic_similarity: 0.08,
    dob_exact: 0.05,
    city_similarity: 0.03,
    segment_exact: 0.02,
  });
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState('');

  const fetchRules = async () => {
    try {
      const data = await getConfigRules();
      setRules(data);
      const prec = data.find((r) => r.rule_key === 'source_precedence_order');
      if (prec?.rule_value?.order) setSourceOrder(prec.rule_value.order);
      const thresh = data.find((r) => r.rule_key === 'matching_thresholds');
      if (thresh?.rule_value) setThresholds(thresh.rule_value);
      const w = data.find((r) => r.rule_key === 'feature_weights');
      if (w?.rule_value) setWeights(w.rule_value);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const totalWeight = Object.values(weights).reduce((a, b) => a + Number(b), 0);

  const handleSaveAll = async () => {
    setSaving(true);
    setSaveSuccess('');
    try {
      await Promise.all([
        updateConfigRule('source_precedence_order', { order: sourceOrder }),
        updateConfigRule('matching_thresholds', thresholds),
        updateConfigRule('feature_weights', weights),
      ]);
      setSaveSuccess('Business rules successfully updated and recorded in audit log.');
    } catch (err) {
      alert(err.message || 'Failed to save rules');
    } finally {
      setSaving(false);
    }
  };

  const moveSource = (index, direction) => {
    const newOrder = [...sourceOrder];
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= newOrder.length) return;
    const temp = newOrder[index];
    newOrder[index] = newOrder[targetIndex];
    newOrder[targetIndex] = temp;
    setSourceOrder(newOrder);
  };

  return (
    <div className="p-6 sm:p-8 space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight font-display">Business Rules Engine (BRE)</h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Configure source precedence hierarchies, matching confidence thresholds, and 8-attribute feature weights.
          </p>
        </div>

        <button
          onClick={handleSaveAll}
          disabled={saving}
          className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white font-bold text-xs sm:text-sm rounded-xl transition-all shadow-subtle flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving Rules...' : 'Save Configuration'}
        </button>
      </div>

      {/* Success Notification */}
      {saveSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center gap-2 text-xs font-semibold text-emerald-900 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{saveSuccess}</span>
        </div>
      )}

      {/* ── Section 1: Source Precedence Hierarchy ────────────────── */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card space-y-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 font-display">1. Master Source Precedence Order</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Defines which business line takes precedence when conflicting canonical attribute values exist.
          </p>
        </div>

        <div className="space-y-2">
          {sourceOrder.map((src, idx) => (
            <div
              key={src}
              className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs"
            >
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-full bg-slate-200 text-slate-800 font-mono font-bold flex items-center justify-center text-xs">
                  {idx + 1}
                </span>
                <span className="font-bold text-slate-900">{src.replace('_', ' ')}</span>
                {idx === 0 && (
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                    Primary Authority
                  </span>
                )}
              </div>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => moveSource(idx, -1)}
                  disabled={idx === 0}
                  className="px-2 py-1 bg-white border border-slate-300 rounded text-slate-700 disabled:opacity-30 hover:bg-slate-100"
                >
                  ▲
                </button>
                <button
                  type="button"
                  onClick={() => moveSource(idx, 1)}
                  disabled={idx === sourceOrder.length - 1}
                  className="px-2 py-1 bg-white border border-slate-300 rounded text-slate-700 disabled:opacity-30 hover:bg-slate-100"
                >
                  ▼
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Section 2: Matching Thresholds ───────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card space-y-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 font-display">2. Identity Resolution Thresholds</h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Controls automatic merging vs human review queue routing.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 bg-emerald-50/50 border border-emerald-200 rounded-xl space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-emerald-950">
              <span>Auto-Match Threshold (MATCH)</span>
              <span className="font-mono text-base text-emerald-700">≥ {thresholds.match_threshold}</span>
            </div>
            <input
              type="range"
              min="0.70"
              max="0.95"
              step="0.01"
              value={thresholds.match_threshold}
              onChange={(e) => setThresholds({ ...thresholds, match_threshold: parseFloat(e.target.value) })}
              className="w-full accent-emerald-600"
            />
            <p className="text-[11px] text-slate-500">
              Candidate pairs with final score ≥ {thresholds.match_threshold} are automatically unified into Golden Customers.
            </p>
          </div>

          <div className="p-4 bg-amber-50/50 border border-amber-200 rounded-xl space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-amber-950">
              <span>Human Review Threshold (REVIEW)</span>
              <span className="font-mono text-base text-amber-700">≥ {thresholds.review_threshold}</span>
            </div>
            <input
              type="range"
              min="0.40"
              max="0.75"
              step="0.01"
              value={thresholds.review_threshold}
              onChange={(e) => setThresholds({ ...thresholds, review_threshold: parseFloat(e.target.value) })}
              className="w-full accent-amber-600"
            />
            <p className="text-[11px] text-slate-500">
              Pairs scoring between {thresholds.review_threshold} and {thresholds.match_threshold} are flagged for KYC review.
            </p>
          </div>
        </div>
      </div>

      {/* ── Section 3: Feature Weights ───────────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 font-display">3. Normalized 8-Attribute Scoring Weights</h3>
            <p className="text-xs text-slate-500 mt-0.5">Sum of weights must equal exactly 1.00</p>
          </div>
          <div className={`text-xs font-mono font-bold px-2.5 py-1 rounded-lg ${Math.abs(totalWeight - 1.0) < 0.001 ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
            Total: {totalWeight.toFixed(2)} / 1.00
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          {Object.entries(weights).map(([key, val]) => (
            <div key={key} className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
              <div className="flex items-center justify-between font-bold text-slate-800">
                <span className="capitalize">{key.replace('_', ' ')}</span>
                <span className="font-mono text-emerald-700">{Number(val).toFixed(2)}</span>
              </div>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={val}
                onChange={(e) => setWeights({ ...weights, [key]: parseFloat(e.target.value) || 0 })}
                className="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg font-mono text-xs focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
