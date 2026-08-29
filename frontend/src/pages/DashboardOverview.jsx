import React, { useState, useEffect } from 'react';
import {
  Users,
  Database,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  GitMerge,
  ShieldCheck,
  Bot,
  Cpu
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getMatchingStats, resetDemoData } from '../api';
import { formatNumber, formatPercent } from '../utils/formatters';
import { MOCK_OVERVIEW_STATS, MOCK_REVIEW_CASES, MOCK_VERIFICATION_CASES } from '../utils/mockData';

export function DashboardOverview({ onNavigate }) {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const sData = await getMatchingStats();
      if (!sData) throw new Error("No data received from API");
      setStats(sData);
    } catch (err) {
      console.error("Failed to fetch dashboard stats", err);
      setError(err.message || "Failed to load dashboard statistics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleResetDemo = async () => {
    if (window.confirm("This will restore all demo records, review decisions and verification statuses to their original state.")) {
      setResetting(true);
      try {
        await resetDemoData();
        await fetchStats();
        alert("Demo data reset successfully.");
      } catch (err) {
        console.error(err);
        alert("Failed to reset demo data.");
      } finally {
        setResetting(false);
      }
    }
  };

  const totalSourceRecords = stats?.total_source_records ?? 0;
  const goldenCustomers = stats?.total_golden_records ?? 0;
  const duplicateReductionPct = stats?.match_rate_pct ?? 0;
  const pendingReviews = stats?.total_reviews_pending ?? 0;
  const aiEligible = stats?.ai_eligible ?? 0;
  const humanRequired = stats?.human_required ?? 0;
  const verificationRequired = aiEligible + humanRequired;

  if (error) {
    return (
      <div className="p-3 sm:p-5 lg:p-8 max-w-7xl mx-auto">
        <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <p className="font-medium">{error}</p>
          <button onClick={fetchStats} className="ml-auto underline text-sm hover:text-red-800">Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 sm:p-5 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* ── Top Welcome ──────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight font-display">
            Operational Overview
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Monitor identity resolution pipeline, required actions, and data quality.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {user?.role === 'ADMIN' && (
            <button
              onClick={handleResetDemo}
              disabled={resetting}
              className="px-4 py-2 bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 rounded-xl text-sm font-semibold transition-all flex items-center gap-2"
            >
              {resetting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <AlertTriangle className="w-4 h-4" />}
              Reset Demo Data
            </button>
          )}
          <button
            onClick={fetchStats}
            title="Refresh statistics"
            className="p-2.5 bg-white border border-slate-200 text-slate-600 hover:text-slate-900 rounded-xl hover:bg-slate-50 transition-all shadow-xs"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* ── TOP SECTION: KPIs ──────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1: Total Records */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Total Records</span>
            <Database className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2 font-display">
            {formatNumber(totalSourceRecords)}
          </div>
        </div>

        {/* Card 2: Golden Profiles */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Golden Profiles</span>
            <Users className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2 font-display">
            {formatNumber(goldenCustomers)}
          </div>
        </div>

        {/* Card 3: Pending Review */}
        <div 
          onClick={() => onNavigate('reviews')}
          className="bg-amber-50 border border-amber-200 rounded-2xl p-5 shadow-card cursor-pointer hover:shadow-card-hover transition-all group"
        >
          <div className="flex items-center justify-between text-xs text-amber-700 font-bold uppercase tracking-wider">
            <span>Pending Review</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-amber-700 mt-2 font-display flex items-center justify-between">
            {pendingReviews}
            <ArrowRight className="w-5 h-5 text-amber-600 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Card 4: Verification Required */}
        <div 
          onClick={() => onNavigate('verification')}
          className="bg-blue-50 border border-blue-200 rounded-2xl p-5 shadow-card cursor-pointer hover:shadow-card-hover transition-all group"
        >
          <div className="flex items-center justify-between text-xs text-blue-700 font-bold uppercase tracking-wider">
            <span>Verification Required</span>
            <ShieldCheck className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-blue-700 mt-2 font-display flex items-center justify-between">
            {verificationRequired}
            <ArrowRight className="w-5 h-5 text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          <div className="flex items-center gap-3 mt-2 text-[10px] font-semibold">
            <span className="text-blue-800 flex items-center gap-1"><Bot className="w-3 h-3"/> {aiEligible} AI</span>
            <span className="text-red-600 flex items-center gap-1"><Users className="w-3 h-3"/> {humanRequired} Human</span>
          </div>
        </div>

        {/* Card 5: Duplicate Reduction */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Duplicate Reduction</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2 font-display">
            {formatPercent(duplicateReductionPct)}
          </div>
        </div>
      </div>

      {/* ── SECOND SECTION: REQUIRES ATTENTION ──────────────────── */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-4 font-display flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-500" /> Requires Attention
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-amber-700 font-bold text-sm">
                <GitMerge className="w-4 h-4" />
                {pendingReviews} Records Pending Review
              </div>
              <p className="text-xs text-slate-500 mt-2">Borderline identity matches requiring human review decision.</p>
            </div>
            <button 
              onClick={() => onNavigate('reviews')}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs rounded-lg transition-colors mt-2"
            >
              Open Review Queue
            </button>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-blue-700 font-bold text-sm">
                <ShieldCheck className="w-4 h-4" />
                {verificationRequired} Verification Cases
              </div>
              <p className="text-xs text-slate-500 mt-2">
                <strong>{aiEligible}</strong> eligible for AI call.<br/>
                <strong>{humanRequired}</strong> require human intervention.
              </p>
            </div>
            <button 
              onClick={() => onNavigate('verification')}
              className="w-full py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold text-xs rounded-lg transition-colors mt-2"
            >
              Open Verification Center
            </button>
          </div>

          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-red-700 font-bold text-sm">
                <ShieldAlert className="w-4 h-4" />
                2 Data Feed Issues
              </div>
              <p className="text-xs text-slate-500 mt-2">Recent source records contain validation warnings (Missing PAN).</p>
            </div>
            <button 
              onClick={() => onNavigate('ingestion')}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs rounded-lg transition-colors mt-2"
            >
              View Data Feeds
            </button>
          </div>
        </div>
      </div>

      {/* ── THIRD SECTION: IDENTITY RESOLUTION SUMMARY ──────────────────── */}
      <div>
        <h3 className="text-lg font-bold text-slate-900 mb-4 font-display">
          Identity Resolution Workflow
        </h3>
        
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm overflow-x-auto">
          <div className="flex items-center justify-between min-w-[800px]">
            {/* Step 1: Data Sources */}
            <div className="flex flex-col items-center gap-2 flex-1 cursor-pointer hover:scale-105 transition-transform" onClick={() => onNavigate('ingestion')}>
              <div className="w-12 h-12 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600">
                <Database className="w-6 h-6" />
              </div>
              <div className="text-center">
                <div className="text-sm font-bold text-slate-800">Data Sources</div>
                <div className="text-xs text-slate-500">12,450 Records</div>
              </div>
            </div>

            <ArrowRight className="w-6 h-6 text-slate-300" />

            {/* Step 2: Matching Engine */}
            <div className="flex flex-col items-center gap-2 flex-1 cursor-pointer hover:scale-105 transition-transform" onClick={() => onNavigate('matching')}>
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                <Cpu className="w-6 h-6" />
              </div>
              <div className="text-center">
                <div className="text-sm font-bold text-slate-800">Matching Engine</div>
                <div className="text-xs text-slate-500">Pipeline</div>
              </div>
            </div>

            <ArrowRight className="w-6 h-6 text-slate-300" />

            {/* Step 3: Decision */}
            <div className="flex flex-col items-center gap-2 flex-1 cursor-pointer hover:scale-105 transition-transform" onClick={() => onNavigate('reviews')}>
              <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center text-amber-600">
                <GitMerge className="w-6 h-6" />
              </div>
              <div className="text-center">
                <div className="text-sm font-bold text-slate-800">Decision</div>
                <div className="text-[10px] text-slate-500 space-y-0.5 mt-1 text-left">
                  <div className="flex justify-between gap-3"><span className="font-semibold text-emerald-600">Auto:</span> 7,560</div>
                  <div className="flex justify-between gap-3"><span className="font-semibold text-amber-600">Review:</span> 18</div>
                  <div className="flex justify-between gap-3"><span className="font-semibold text-slate-600">None:</span> 10,652</div>
                </div>
              </div>
            </div>

            <ArrowRight className="w-6 h-6 text-slate-300" />

            {/* Step 4: Verification */}
            <div className="flex flex-col items-center gap-2 flex-1 cursor-pointer hover:scale-105 transition-transform" onClick={() => onNavigate('verification')}>
              <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center text-purple-600">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div className="text-center">
                <div className="text-sm font-bold text-slate-800">Verification</div>
                <div className="text-xs text-slate-500">6 Cases</div>
              </div>
            </div>

            <ArrowRight className="w-6 h-6 text-slate-300" />

            {/* Step 5: Golden Profile */}
            <div className="flex flex-col items-center gap-2 flex-1 cursor-pointer hover:scale-105 transition-transform" onClick={() => onNavigate('customers')}>
              <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600 border border-emerald-200 shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                <Users className="w-6 h-6" />
              </div>
              <div className="text-center">
                <div className="text-sm font-bold text-slate-800">Golden Profile</div>
                <div className="text-xs text-slate-500">4,890 Profiles</div>
              </div>
            </div>

          </div>
        </div>
      </div>

    </div>
  );
}
