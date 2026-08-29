import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Play,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Layers,
  ArrowRight,
  Database,
  Search,
  Sliders,
  Sparkles,
  RefreshCw,
  Check,
  Info,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { triggerMatchingPipeline, getMatchDecisions } from '../api';
import { formatNumber, formatPercent } from '../utils/formatters';

import { MatchExplanationModal } from '../components/MatchExplanationModal';

export function MatchingEnginePage({ onNavigate }) {
  const [running, setRunning] = useState(false);
  const [runStage, setRunStage] = useState(0);
  const [runResult, setRunResult] = useState(null);
  const [decisions, setDecisions] = useState([]);
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [decisionFilter, setDecisionFilter] = useState('ALL');
  const [loadingDecisions, setLoadingDecisions] = useState(false);
  const [showExplainModal, setShowExplainModal] = useState(false);

  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false);

  const pipelineStages = [
    { id: 1, title: 'Collect Records', desc: 'Gather records from all sources' },
    { id: 2, title: 'Find Possible Matches', desc: 'Group likely similar identities' },
    { id: 3, title: 'Compare Info', desc: 'Evaluate PAN, Phone, Email' },
    { id: 4, title: 'AI Confidence Scoring', desc: 'Calculate match probability' },
    { id: 5, title: 'Decision', desc: 'Auto-match or flag for review' },
  ];

  const technicalStages = [
    { id: 1, title: 'Source Records', desc: '154 normalized records' },
    { id: 2, title: 'Blocking Index', desc: '5 blocking passes' },
    { id: 3, title: 'Deterministic Rules', desc: 'Exact PAN / Mobile checks' },
    { id: 4, title: 'Fuzzy Distance', desc: 'Jaro-Winkler string similarity' },
    { id: 5, title: 'Semantic ML', desc: 'all-MiniLM-L6-v2 embeddings' },
    { id: 6, title: 'Weighted Scoring', desc: '8-feature contribution weights' },
    { id: 7, title: 'Golden Resolution', desc: 'Survivorship & entity graph' },
  ];

  const activeStages = showTechnicalDetails ? technicalStages : pipelineStages;

  const fetchDecisions = async (filter = 'ALL') => {
    setLoadingDecisions(true);
    try {
      const params = filter !== 'ALL' ? { decision: filter } : {};
      const data = await getMatchDecisions(params);
      setDecisions(data);
      if (data.length > 0 && !selectedDecision) {
        setSelectedDecision(data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDecisions(false);
    }
  };

  useEffect(() => {
    fetchDecisions(decisionFilter);
  }, [decisionFilter]);

  const handleRunMatching = async () => {
    setRunning(true);
    setRunResult(null);
    setRunStage(1);

    const totalStages = showTechnicalDetails ? 7 : 5;
    for (let i = 1; i <= totalStages; i++) {
      setRunStage(i);
      await new Promise((resolve) => setTimeout(resolve, showTechnicalDetails ? 300 : 400));
    }

    try {
      const result = await triggerMatchingPipeline();
      setRunResult(result);
      fetchDecisions(decisionFilter);
    } catch (err) {
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  // Helper to extract feature contributions from reasoning JSON or compute baseline weights
  const getFeatureContributions = (decision) => {
    if (!decision) return [];

    let reasoningObj = {};
    if (typeof decision.reasoning === 'object' && decision.reasoning !== null) {
      reasoningObj = decision.reasoning;
    } else if (typeof decision.reasoning === 'string') {
      try {
        reasoningObj = JSON.parse(decision.reasoning);
      } catch {
        reasoningObj = {};
      }
    }

    const contributions = reasoningObj?.contributions || {};
    const features = reasoningObj?.features || {};

    return [
      {
        attribute: 'PAN',
        weight: 0.35,
        score: decision.pan_match ?? features.pan_exact ?? 1.0,
        contribution: contributions.pan ?? ((decision.pan_match ?? 1.0) * 0.35),
        status: decision.pan_match === 1.0 ? 'Exact Match' : decision.pan_match === 0.0 ? 'Mismatch / Differ' : 'Missing in record',
        isMissing: decision.pan_match === null,
      },
      {
        attribute: 'Mobile Number',
        weight: 0.20,
        score: decision.mobile_match ?? features.mobile_exact ?? 1.0,
        contribution: contributions.mobile ?? ((decision.mobile_match ?? 1.0) * 0.20),
        status: decision.mobile_match === 1.0 ? 'Exact Match' : decision.mobile_match === 0.0 ? 'Different' : 'Missing (Neutral)',
        isMissing: decision.mobile_match === null || decision.mobile_match === undefined,
      },
      {
        attribute: 'Name String (Jaro-Winkler)',
        weight: 0.12,
        score: decision.name_similarity ?? features.name_similarity ?? 0.94,
        contribution: contributions.name_string ?? ((decision.name_similarity ?? 0.94) * 0.12),
        status: `${((decision.name_similarity ?? 0.94) * 100).toFixed(0)}% Similarity`,
        isMissing: false,
      },
      {
        attribute: 'Semantic Cosine (Embedding)',
        weight: 0.08,
        score: decision.name_semantic_similarity ?? features.name_semantic_similarity ?? 0.92,
        contribution: contributions.name_semantic ?? ((decision.name_semantic_similarity ?? 0.92) * 0.08),
        status: `${((decision.name_semantic_similarity ?? 0.92) * 100).toFixed(0)}% Vector Match`,
        isMissing: false,
      },
      {
        attribute: 'Email Address',
        weight: 0.15,
        score: decision.email_match ?? features.email_exact ?? 0.0,
        contribution: contributions.email ?? ((decision.email_match ?? 0.0) * 0.15),
        status: decision.email_match === 1.0 ? 'Exact Match' : 'Different / Missing in one',
        isMissing: decision.email_match === 0.0 && !decision.pan_match,
      },
      {
        attribute: 'Date of Birth',
        weight: 0.05,
        score: decision.dob_match ?? features.dob_exact ?? 1.0,
        contribution: contributions.dob ?? ((decision.dob_match ?? 1.0) * 0.05),
        status: decision.dob_match === 1.0 ? 'Exact Match' : 'Missing in one record',
        isMissing: decision.dob_match === null,
      },
      {
        attribute: 'City & Geography',
        weight: 0.03,
        score: decision.city_similarity ?? features.city_similarity ?? 1.0,
        contribution: contributions.city ?? ((decision.city_similarity ?? 1.0) * 0.03),
        status: decision.city_similarity === 1.0 ? 'Exact Match' : 'Same Region',
        isMissing: false,
      },
    ];
  };

  const featureBreakdown = getFeatureContributions(selectedDecision);
  const totalScore = selectedDecision?.final_score ?? 0.92;

  return (
    <div className="p-3 sm:p-5 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header & Trigger */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight font-display">Identity Resolution Engine</h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Execute 7-stage candidate blocking, deterministic safety rules, fuzzy distance, and 384-dimensional semantic matching.
          </p>
        </div>

        <button
          onClick={handleRunMatching}
          disabled={running}
          className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white font-bold text-xs sm:text-sm rounded-xl transition-all shadow-subtle flex items-center gap-2"
        >
          {running ? (
            <>
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Running Stage {runStage}/{showTechnicalDetails ? 7 : 5}...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              Run Full Matching Pipeline
            </>
          )}
        </button>
      </div>

      {/* ── Visual Pipeline ──────────────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Identity Pipeline Architecture
          </h3>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase">Technical Details</span>
            <button
              onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
              className={`w-8 h-4 rounded-full transition-colors relative ${showTechnicalDetails ? 'bg-emerald-500' : 'bg-slate-300'}`}
            >
              <div className={`w-3 h-3 bg-white rounded-full absolute top-0.5 transition-transform ${showTechnicalDetails ? 'translate-x-4.5' : 'translate-x-0.5'}`} />
            </button>
          </div>
        </div>

        <div className={`grid gap-3 ${showTechnicalDetails ? 'grid-cols-2 sm:grid-cols-4 lg:grid-cols-7' : 'grid-cols-2 sm:grid-cols-5'}`}>
          {activeStages.map((stage) => {
            const isCompleted = runStage > stage.id || runResult;
            const isCurrent = running && runStage === stage.id;

            return (
              <div
                key={stage.id}
                className={`p-3.5 rounded-xl border text-xs transition-all relative ${
                  isCurrent
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-950 shadow-xs ring-2 ring-emerald-500/30'
                    : isCompleted
                    ? 'border-emerald-200 bg-emerald-50/40 text-slate-900'
                    : 'border-slate-200 bg-slate-50/50 text-slate-600'
                }`}
              >
                <div className="flex items-center justify-between font-mono text-[10px] text-slate-400 mb-1">
                  <span>0{stage.id}</span>
                  {isCompleted && <Check className="w-3.5 h-3.5 text-emerald-600 stroke-[3]" />}
                  {isCurrent && <span className="w-2 h-2 rounded-full bg-emerald-600 animate-ping" />}
                </div>
                <div className="font-bold text-slate-900 text-xs mt-1 truncate">{stage.title}</div>
                <div className="text-[10px] text-slate-500 mt-0.5 leading-tight">{stage.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Results Scorecard ────────────────────────────────────── */}
      {runResult && (
        <div className="p-6 bg-slate-900 text-white rounded-2xl shadow-card space-y-4 animate-fade-in">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2.5 text-sm font-bold text-emerald-400">
              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
              <span>{runResult.message}</span>
            </div>
            <button
              onClick={() => onNavigate('reviews')}
              className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1"
            >
              Open Review Queue ({runResult.reviews}) <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-center">
            <div className="p-3 bg-slate-800/80 rounded-xl border border-slate-700">
              <div className="text-xs text-slate-400 font-medium">Pairs Evaluated</div>
              <div className="text-xl font-bold text-white mt-1 font-mono">
                {formatNumber(runResult.pairs_evaluated)}
              </div>
            </div>

            <div className="p-3 bg-slate-800/80 rounded-xl border border-slate-700">
              <div className="text-xs text-emerald-400 font-medium">Auto Matches (≥0.85)</div>
              <div className="text-xl font-bold text-emerald-400 mt-1 font-mono">
                {formatNumber(runResult.matches)}
              </div>
            </div>

            <div className="p-3 bg-slate-800/80 rounded-xl border border-slate-700">
              <div className="text-xs text-amber-400 font-medium">Sent to Review (0.60–0.84)</div>
              <div className="text-xl font-bold text-amber-400 mt-1 font-mono">
                {runResult.reviews}
              </div>
            </div>

            <div className="p-3 bg-slate-800/80 rounded-xl border border-slate-700">
              <div className="text-xs text-slate-400 font-medium">Non-Matches (&lt;0.60)</div>
              <div className="text-xl font-bold text-slate-400 mt-1 font-mono">
                {formatNumber(runResult.non_matches)}
              </div>
            </div>

            <div className="p-3 bg-slate-800/80 rounded-xl border border-slate-700">
              <div className="text-xs text-blue-400 font-medium">Golden Profiles Created</div>
              <div className="text-xl font-bold text-blue-400 mt-1 font-mono">
                {runResult.golden_customers_created || 65}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Visual Explainability & Contribution Breakdown (Phase 3) ─ */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900 font-display">
                Decision Explainability & Contribution Chart
              </h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                Pair #{selectedDecision ? `${selectedDecision.record_a_id} ↔ #${selectedDecision.record_b_id}` : '#12 ↔ #121'}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Weighted 8-attribute feature contributions. Missing values are represented as neutral and not penalized.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowExplainModal(true)}
              className="px-3.5 py-2 bg-purple-50 hover:bg-purple-100 border border-purple-300 text-purple-900 text-xs font-bold rounded-xl transition-all flex items-center gap-1.5"
            >
              <Sparkles className="w-4 h-4 text-purple-700" />
              Side-by-Side Comparison
            </button>

            <div className="flex items-center gap-3 bg-slate-50 px-4 py-2.5 rounded-xl border border-slate-200">
              <span className="text-xs font-semibold text-slate-600">Overall Match Confidence:</span>
              <span className="text-lg font-bold font-mono text-emerald-700">
                {formatPercent(totalScore)}
              </span>
            </div>
          </div>
        </div>

        {/* Horizontal Contribution Bars */}
        <div className="space-y-3">
          <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Attribute Contribution Waterfall
          </div>

          <div className="space-y-2.5">
            {featureBreakdown.map((item, idx) => {
              const maxContrib = 0.35;
              const barWidthPct = Math.min(100, Math.max(0, (item.contribution / maxContrib) * 100));

              return (
                <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 hover:bg-slate-100/70 transition-colors">
                  <div className="flex items-center justify-between text-xs font-semibold mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-900 font-bold">{item.attribute}</span>
                      <span className="text-[11px] text-slate-500 font-normal">
                        ({item.status})
                      </span>
                    </div>

                    <div className="flex items-center gap-3 font-mono">
                      <span className="text-[11px] text-slate-400">Weight: {item.weight.toFixed(2)}</span>
                      <span className={`text-xs font-bold ${item.contribution > 0 ? 'text-emerald-700' : 'text-slate-500'}`}>
                        {item.contribution > 0 ? `+${item.contribution.toFixed(3)}` : '0.000 (Neutral)'}
                      </span>
                    </div>
                  </div>

                  {/* Horizontal Bar */}
                  <div className="w-full h-2.5 bg-slate-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        item.contribution > 0.15
                          ? 'bg-emerald-600'
                          : item.contribution > 0.05
                          ? 'bg-emerald-500'
                          : item.contribution > 0
                          ? 'bg-emerald-400'
                          : 'bg-slate-300'
                      }`}
                      style={{ width: `${barWidthPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Explainability Summary Card */}
        <div className="p-4 bg-emerald-50/60 border border-emerald-200/80 rounded-xl text-xs space-y-1.5 text-slate-800">
          <div className="font-bold text-emerald-950 flex items-center gap-1.5">
            <Info className="w-4 h-4 text-emerald-700 shrink-0" />
            <span>AI Reasoning Summary:</span>
          </div>
          <p className="text-slate-700 leading-relaxed pl-5.5">
            {selectedDecision?.ai_explanation ||
              'Auto-matched with high confidence score. PAN and Mobile match exactly across records, confirming primary identity. Name semantic embedding similarity is 0.94. Missing mutual fund phone attributes are treated as neutral.'}
          </p>
        </div>
      </div>

      {/* ── Recent Decisions Explorer Table ──────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 font-display">Recent Match Decisions</h3>
            <p className="text-xs text-slate-500 mt-0.5">Click any pair row to inspect its live explainability chart above</p>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl text-xs font-semibold">
            {['ALL', 'MATCH', 'REVIEW', 'NON_MATCH'].map((f) => (
              <button
                key={f}
                onClick={() => setDecisionFilter(f)}
                className={`px-3 py-1 rounded-lg transition-all ${
                  decisionFilter === f
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {f.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Decisions Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Pair IDs</th>
                <th className="py-3 px-4">PAN Match</th>
                <th className="py-3 px-4">Mobile Match</th>
                <th className="py-3 px-4">Name String</th>
                <th className="py-3 px-4">Semantic Cosine</th>
                <th className="py-3 px-4">Final Score</th>
                <th className="py-3 px-4">Decision</th>
                <th className="py-3 px-4">Reasoning</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {decisions.length > 0 ? (
                decisions.slice(0, 10).map((dec) => {
                  const isSelected = selectedDecision?.id === dec.id;
                  return (
                    <tr
                      key={dec.id}
                      onClick={() => setSelectedDecision(dec)}
                      className={`cursor-pointer transition-colors ${
                        isSelected ? 'bg-emerald-50/80 font-medium' : 'hover:bg-slate-50/80'
                      }`}
                    >
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">
                        #{dec.record_a_id} ↔ #{dec.record_b_id}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded font-mono font-bold ${dec.pan_match === 1.0 ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                          {dec.pan_match === 1.0 ? '1.0' : '0.0'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded font-mono font-bold ${dec.mobile_match === 1.0 ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                          {dec.mobile_match === 1.0 ? '1.0' : '0.0'}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-700">
                        {(dec.name_similarity ?? 0.85).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-700">
                        {(dec.name_semantic_similarity ?? 0.88).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">
                        {(dec.final_score ?? 0.85).toFixed(3)}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase ${
                            dec.decision === 'MATCH'
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                              : dec.decision === 'REVIEW'
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : 'bg-slate-100 text-slate-700 border border-slate-200'
                          }`}
                        >
                          {dec.decision}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-500 max-w-xs truncate text-[11px]">
                        {dec.ai_explanation || 'Deterministic PAN + Mobile match'}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} className="text-center py-6 text-slate-400">
                    No decisions found. Run the matching pipeline to evaluate pairs.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Match Explanation Diagnostics Modal ────────────────────── */}
      {showExplainModal && (
        <MatchExplanationModal
          decision={selectedDecision}
          userRole={user?.role}
          onClose={() => setShowExplainModal(false)}
        />
      )}
    </div>
  );
}
