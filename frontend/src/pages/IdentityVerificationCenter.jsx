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
    const targetPhone = "+919920602745"; // Hardcoded as per user request

    setActionLoading(true);
    setStatusMessage('');
    try {
      const updatedCase = await triggerAIVerification(caseId, targetPhone);
      setStatusMessage('Kovi AI Verification Call initiated successfully to ' + targetPhone);
      
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
  const aiEligible = cases.filter(c => c.ai_eligible).length;
  const humanRequired = cases.filter(c => !c.ai_eligible).length;
  const aiCompleted = cases.filter(c => c.status === 'CALL_COMPLETED' || c.status === 'AI_VERIFIED' || c.status === 'AI_FAILED' || c.status === 'VERIFIED').length;

  const getStatusBadge = (status) => {
    const s = status || 'PENDING';
    if (s === 'AI_VERIFIED' || s === 'VERIFIED') return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    if (s === 'HUMAN_VERIFICATION_REQUIRED' || s === 'AI_FAILED') return 'bg-red-100 text-red-800 border-red-200';
    return 'bg-amber-100 text-amber-800 border-amber-200';
  };

  const getClassificationBadge = (c) => {
    if (c.ai_eligible) return 'bg-blue-100 text-blue-800';
    if (!c.ai_eligible) return 'bg-red-100 text-red-800';
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
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getClassificationBadge(c)}`}>
                      {c.ai_eligible ? 'AI ELIGIBLE' : 'HUMAN REQUIRED'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getStatusBadge(c.status)}`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {c.result?.confidence ? (
                      <span className="font-mono font-bold text-emerald-600">{(c.result.confidence * 100).toFixed(0)}%</span>
                    ) : (
                      <span className="text-slate-400 font-mono">-</span>
                    )}
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
              {/* Customer Contact Tab */}
              <div className="bg-blue-50 p-4 rounded-xl border border-blue-100 flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-blue-800 uppercase flex items-center gap-1 mb-1">
                    <UserCheck className="w-4 h-4"/> Target Customer Profile
                  </div>
                  <div className="font-bold text-slate-900">{selectedCase.record_a?.original_name || 'Customer'}</div>
                  <div className="font-mono text-sm text-slate-600 mt-0.5">Phone: +91 9920602745</div>
                  {selectedCase.result ? (
                      <div className="space-y-4 mt-4">
                        <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl">
                          <p className="text-xs font-bold text-emerald-800 uppercase tracking-wider mb-2">Customer Confirmed</p>
                          <p className="text-sm font-semibold text-emerald-900 leading-snug">
                            "{selectedCase.result.customer_response}"
                          </p>
                        </div>
                        <div className="space-y-2 text-xs">
                          <div className="flex justify-between pb-2 border-b border-slate-100">
                            <span className="text-slate-500">Detected Language</span>
                            <span className="font-semibold text-slate-800">{selectedCase.result.language_detected}</span>
                          </div>
                          <div className="flex justify-between pb-2 border-b border-slate-100">
                            <span className="text-slate-500">Kovi Confidence</span>
                            <span className="font-bold text-emerald-600 font-mono">{(selectedCase.result.confidence * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-32 text-slate-400 space-y-2 mt-4">
                        <Bot className="w-8 h-8 opacity-20" />
                        <p className="text-xs">Awaiting Kovi AI contact outcome...</p>
                      </div>
                    )}
                </div>
              </div>

              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-2">
                <div className="text-xs font-bold text-slate-500 uppercase">Match Reasoning</div>
                <div className="text-sm font-mono text-slate-700 bg-white p-2 rounded border border-slate-200 break-words">
                  {selectedCase.discrepancy_type ? selectedCase.discrepancy_type : 'No reasoning available'}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 flex justify-end gap-3">
                {selectedCase.ai_eligible && (
                  <button
                    onClick={() => handleTriggerAI(selectedCase.id)}
                    disabled={actionLoading || selectedCase.status === 'CALL_COMPLETED' || selectedCase.status === 'CALL_QUEUED'}
                    className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-bold text-sm rounded-xl flex items-center gap-2 shadow-sm disabled:opacity-50 transition-all shadow-purple-900/20"
                  >
                    <PhoneCall className="w-5 h-5" />
                    Call +91 9920602745 (Kovi AI)
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
