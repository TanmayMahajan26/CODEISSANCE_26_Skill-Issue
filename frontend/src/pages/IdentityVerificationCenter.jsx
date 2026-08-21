import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Bot,
  UserCheck,
  CheckCircle2,
  XCircle,
  PhoneCall,
  Clock,
  AlertTriangle
} from 'lucide-react';
import {
  getVerificationCases,
  triggerAIVerification
} from '../api';
import { useAuth } from '../context/AuthContext';

export function IdentityVerificationCenter() {
  const { user } = useAuth();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCase, setSelectedCase] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');

  const fetchCases = async () => {
    setLoading(true);
    try {
      const data = await getVerificationCases();
      setCases(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const handleTriggerAI = async (caseId) => {
    setActionLoading(true);
    setStatusMessage('');
    try {
      const updatedCase = await triggerAIVerification(caseId);
      setStatusMessage('Kovi AI Verification Call initiated successfully.');
      
      // Update local state
      setCases((prev) => prev.map(c => c.id === caseId ? updatedCase : c));
      if (selectedCase?.id === caseId) {
        setSelectedCase(updatedCase);
      }
    } catch (err) {
      alert(err.message || 'Failed to trigger AI Verification');
    } finally {
      setActionLoading(false);
    }
  };

  // Metrics
  const totalCases = cases.length;
  const aiEligible = cases.filter(c => c.verification_classification === 'AI_VERIFICATION_ELIGIBLE').length;
  const humanRequired = cases.filter(c => c.verification_classification === 'HUMAN_VERIFICATION_REQUIRED').length;
  const aiCompleted = cases.filter(c => c.verification_status === 'AI_VERIFIED' || c.verification_status === 'AI_FAILED').length;

  const getStatusBadge = (status) => {
    const s = status || 'PENDING';
    if (s === 'AI_VERIFIED' || s === 'VERIFIED') return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    if (s === 'HUMAN_VERIFICATION_REQUIRED' || s === 'AI_FAILED') return 'bg-red-100 text-red-800 border-red-200';
    return 'bg-amber-100 text-amber-800 border-amber-200';
  };

  const getClassificationBadge = (classification) => {
    if (classification === 'AUTO_RESOLVE') return 'bg-emerald-100 text-emerald-800';
    if (classification === 'HUMAN_VERIFICATION_REQUIRED') return 'bg-red-100 text-red-800';
    return 'bg-blue-100 text-blue-800';
  };

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight font-display">Verification Center</h2>
            <span className="px-2.5 py-1 rounded-md bg-purple-100 text-purple-800 text-xs font-bold font-mono border border-purple-200 flex items-center gap-1.5">
              <Bot className="w-4 h-4" />
              Kovi AI (Powered by Bolna)
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">Escalation hub for borderline match confidence and critical identity conflicts.</p>
        </div>
      </div>

      {statusMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-2 text-sm text-emerald-900">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-slate-800">{totalCases}</span>
          <span className="text-xs font-semibold text-slate-500 uppercase mt-1">Total Cases</span>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-blue-600">{aiEligible}</span>
          <span className="text-xs font-semibold text-slate-500 uppercase mt-1">AI Eligible</span>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-red-600">{humanRequired}</span>
          <span className="text-xs font-semibold text-slate-500 uppercase mt-1">Human Required</span>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-emerald-600">{aiCompleted}</span>
          <span className="text-xs font-semibold text-slate-500 uppercase mt-1">AI Calls Completed</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Table/List */}
        <div className="lg:col-span-6 bg-white border border-slate-200 rounded-2xl shadow-card overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 text-xs uppercase font-bold">
              <tr>
                <th className="px-4 py-3">Case ID</th>
                <th className="px-4 py-3">Classification</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Confidence</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {cases.map((c) => (
                <tr 
                  key={c.id} 
                  onClick={() => setSelectedCase(c)}
                  className={`cursor-pointer hover:bg-slate-50 transition-colors ${selectedCase?.id === c.id ? 'bg-blue-50/50' : ''}`}
                >
                  <td className="px-4 py-3 font-mono font-medium text-slate-700">#{c.id}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getClassificationBadge(c.verification_classification)}`}>
                      {c.verification_classification?.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getStatusBadge(c.verification_status)}`}>
                      {c.verification_status?.replace(/_/g, ' ') || 'PENDING'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-slate-600">
                    {c.details?.score ? c.details.score.toFixed(2) : '-'}
                  </td>
                </tr>
              ))}
              {cases.length === 0 && (
                <tr><td colSpan="4" className="text-center py-6 text-slate-500">No verification cases found.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Case Detail View */}
        {selectedCase && (
          <div className="lg:col-span-6 bg-white border border-slate-200 rounded-2xl shadow-card p-5 space-y-5">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-800">Case Details #{selectedCase.id}</h3>
              <span className={`px-2 py-1 rounded text-xs font-bold border ${getStatusBadge(selectedCase.verification_status)}`}>
                {selectedCase.verification_status?.replace(/_/g, ' ')}
              </span>
            </div>

            <div className="space-y-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-2">
                <div className="text-xs font-bold text-slate-500 uppercase">Match Reasoning</div>
                <div className="text-sm font-mono text-slate-700 bg-white p-2 rounded border border-slate-200 break-words">
                  {selectedCase.details?.reasoning ? JSON.stringify(selectedCase.details.reasoning, null, 2) : 'No reasoning available'}
                </div>
              </div>

              {selectedCase.ai_call_result && (
                <div className="bg-purple-50 p-4 rounded-xl border border-purple-100 space-y-2">
                  <div className="text-xs font-bold text-purple-800 uppercase flex items-center gap-1">
                    <Bot className="w-4 h-4"/> Kovi AI Call Result
                  </div>
                  <div className="text-sm text-slate-700 bg-white p-2 rounded border border-purple-200 break-words font-mono">
                    {JSON.stringify(selectedCase.ai_call_result, null, 2)}
                  </div>
                  {selectedCase.ai_call_confidence && (
                    <div className="text-xs font-bold text-slate-700 mt-2">
                      Confidence: {selectedCase.ai_call_confidence}
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-4 flex justify-end gap-3">
                {selectedCase.verification_classification === 'AI_VERIFICATION_ELIGIBLE' && (
                  <button
                    onClick={() => handleTriggerAI(selectedCase.id)}
                    disabled={actionLoading || selectedCase.verification_status === 'AI_CALL_IN_PROGRESS'}
                    className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-sm rounded-xl flex items-center gap-2 shadow-sm disabled:opacity-50"
                  >
                    <PhoneCall className="w-4 h-4" />
                    Initiate Kovi AI Call
                  </button>
                )}

                {selectedCase.verification_classification === 'HUMAN_VERIFICATION_REQUIRED' && (
                  <button
                    disabled
                    className="px-5 py-2.5 bg-slate-100 text-slate-500 font-bold text-sm rounded-xl flex items-center gap-2 border border-slate-200 cursor-not-allowed"
                  >
                    <UserCheck className="w-4 h-4" />
                    Escalate to Human Verification
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
