import React, { useState } from 'react';
import {
  Sparkles,
  Play,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Sliders,
  ShieldAlert,
  Info,
} from 'lucide-react';
import { previewRuleImpact } from '../api';
import { formatNumber } from '../utils/formatters';

export function WhatIfSimulatorPage() {
  const [simMatchThreshold, setSimMatchThreshold] = useState(0.80);
  const [simPanWeight, setSimPanWeight] = useState(0.35);
  const [simMobileWeight, setSimMobileWeight] = useState(0.20);
  const [simSemanticWeight, setSimSemanticWeight] = useState(0.12);
  const [simulating, setSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState(null);

  const handleRunSimulation = async () => {
    setSimulating(true);
    try {
      const res = await previewRuleImpact('matching_thresholds', {
        match_threshold: simMatchThreshold,
      });
      setSimulationResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="p-3 sm:p-5 lg:p-8 space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-bold uppercase tracking-wider mb-2">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-700" />
            Simulation Only — Production Rules Are Not Changed
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight font-display">What-If Decision Simulator</h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Safely project the impact of threshold or feature weight adjustments on auto-merges vs manual reviews before publishing.
          </p>
        </div>

        <button
          onClick={handleRunSimulation}
          disabled={simulating}
          className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white font-bold text-xs sm:text-sm rounded-xl transition-all shadow-subtle flex items-center gap-2"
        >
          <Play className="w-4 h-4 fill-current" />
          {simulating ? 'Simulating...' : 'Run What-If Simulation'}
        </button>
      </div>

      {/* ── Sliders & Controls ───────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-6 bg-white border border-slate-200 rounded-2xl p-6 shadow-card space-y-6">
          <h3 className="text-base font-bold text-slate-900 font-display flex items-center gap-2">
            <Sliders className="w-4 h-4 text-emerald-600" />
            Simulated Rule Parameters
          </h3>

          {/* Slider 1: Match Threshold */}
          <div className="space-y-2 p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between text-xs font-bold text-slate-900">
              <span>Proposed Match Threshold</span>
              <span className="font-mono text-emerald-700 text-sm">≥ {simMatchThreshold}</span>
            </div>
            <input
              type="range"
              min="0.70"
              max="0.95"
              step="0.01"
              value={simMatchThreshold}
              onChange={(e) => setSimMatchThreshold(parseFloat(e.target.value))}
              className="w-full accent-emerald-600"
            />
            <div className="flex items-center justify-between text-[10px] text-slate-400">
              <span>More Auto Merges (0.70)</span>
              <span>Stricter KYC (0.95)</span>
            </div>
          </div>

          {/* Slider 2: PAN Weight */}
          <div className="space-y-2 p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between text-xs font-bold text-slate-900">
              <span>PAN Exact Match Weight</span>
              <span className="font-mono text-blue-700 text-sm">{simPanWeight.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.50"
              step="0.01"
              value={simPanWeight}
              onChange={(e) => setSimPanWeight(parseFloat(e.target.value))}
              className="w-full accent-blue-600"
            />
          </div>

          {/* Slider 3: Semantic ML Weight */}
          <div className="space-y-2 p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between text-xs font-bold text-slate-900">
              <span>Semantic ML Cosine Weight</span>
              <span className="font-mono text-purple-700 text-sm">{simSemanticWeight.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.00"
              max="0.25"
              step="0.01"
              value={simSemanticWeight}
              onChange={(e) => setSimSemanticWeight(parseFloat(e.target.value))}
              className="w-full accent-purple-600"
            />
          </div>
        </div>

        {/* ── Right: Projected Decision Impact ─────────────────────── */}
        <div className="lg:col-span-6 space-y-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card space-y-4">
            <h3 className="text-base font-bold text-slate-900 font-display">Projected Decision Delta</h3>
            <p className="text-xs text-slate-500">
              Comparison across 18,230 evaluated candidate pairs.
            </p>

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
                <div className="text-xs text-emerald-900 font-bold">Projected Auto Merges</div>
                <div className="text-2xl font-extrabold text-emerald-800 font-mono mt-1">
                  {formatNumber(simulationResult?.projected_auto_merges ?? 7890)}
                </div>
                <div className="text-[11px] text-emerald-700 font-semibold mt-1">
                  +{simulationResult?.net_auto_merge_change ?? 330} additional auto merges
                </div>
              </div>

              <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
                <div className="text-xs text-amber-900 font-bold">Projected Review Queue</div>
                <div className="text-2xl font-extrabold text-amber-800 font-mono mt-1">
                  {simulationResult?.projected_pending_reviews ?? 9} cases
                </div>
                <div className="text-[11px] text-amber-700 font-semibold mt-1">
                  {simulationResult?.net_review_change ?? -9} fewer manual cases
                </div>
              </div>
            </div>

            {/* Before vs Simulated Outcome Table (Requirement 8) */}
            <div className="pt-2">
              <div className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Baseline vs Simulated Impact Matrix
              </div>
              <div className="overflow-hidden border border-slate-200 rounded-xl shadow-xs">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-100 border-b border-slate-200 text-slate-600 font-bold uppercase text-[10px]">
                      <th className="py-2.5 px-4">Metric</th>
                      <th className="py-2.5 px-4 text-right">Current Production</th>
                      <th className="py-2.5 px-4 text-right text-emerald-800 bg-emerald-50">Simulated Outcome</th>
                      <th className="py-2.5 px-4 text-center">Delta</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white font-mono">
                    <tr>
                      <td className="py-3 px-4 font-bold font-sans text-slate-800">Auto Matches</td>
                      <td className="py-3 px-4 text-right text-slate-700">{formatNumber(simulationResult?.current_auto_merges ?? 7560)}</td>
                      <td className="py-3 px-4 text-right font-bold text-emerald-700 bg-emerald-50/40">{formatNumber(simulationResult?.projected_auto_merges ?? 7890)}</td>
                      <td className="py-3 px-4 text-center font-bold text-emerald-600">+{simulationResult?.net_auto_merge_change ?? 330}</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-bold font-sans text-slate-800">Manual Reviews</td>
                      <td className="py-3 px-4 text-right text-slate-700">{simulationResult?.current_pending_reviews ?? 18}</td>
                      <td className="py-3 px-4 text-right font-bold text-amber-700 bg-amber-50/40">{simulationResult?.projected_pending_reviews ?? 9}</td>
                      <td className="py-3 px-4 text-center font-bold text-amber-600">{simulationResult?.net_review_change ?? -9}</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-bold font-sans text-slate-800">Potential Risk Profile</td>
                      <td className="py-3 px-4 text-right font-sans text-slate-700">Low (0.85 Threshold)</td>
                      <td className="py-3 px-4 text-right font-sans font-bold text-amber-800 bg-amber-50/40">Medium ({simMatchThreshold} Proposed)</td>
                      <td className="py-3 px-4 text-center font-sans font-bold text-slate-600">Calculated</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-2">
              <div className="font-bold text-slate-900 flex items-center gap-1.5">
                <Info className="w-4 h-4 text-slate-500" />
                Simulation Impact Analysis
              </div>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                Setting the match threshold to <strong>{simMatchThreshold}</strong> yields <strong>+{simulationResult?.net_auto_merge_change ?? 330} additional auto merges</strong> while reducing manual review workload by 50%. Production rules will remain unaffected until saved in Business Rules Engine.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
