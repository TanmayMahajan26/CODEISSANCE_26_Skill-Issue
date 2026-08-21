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
import { MOCK_VERIFICATION_CASES } from '../utils/mockData';

export function IdentityVerificationCenter() {
  const { user } = useAuth();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCase, setSelectedCase] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  
  // Bolna Simulation State
  const [simulationState, setSimulationState] = useState(null); // 'INITIATED', 'LANGUAGE_DETECTED', 'IDENTITY_CONFIRMED', 'DISCREPANCY_EXPLAINED', 'CUSTOMER_RESPONSE', 'VERIFIED'
  const [selectedLanguage, setSelectedLanguage] = useState('English');

  const fetchCases = async () => {
    setLoading(true);
    try {
      const data = await getVerificationCases();
      setCases(data || []);
      if (!data || data.length === 0) throw new Error("Fallback");
    } catch (err) {
      console.warn("Backend unavailable, using MOCK_VERIFICATION_CASES", err);
      setCases(MOCK_VERIFICATION_CASES);
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
    setSimulationState('INITIATED');
    
    // Run the Bolna Simulated Flow
    try {
      // 1. INITIATED
      await new Promise(r => setTimeout(r, 1500));
      setSimulationState('LANGUAGE_DETECTED');
      
      // 2. LANGUAGE DETECTED
      await new Promise(r => setTimeout(r, 2000));
      setSimulationState('IDENTITY_CONFIRMED');
      
      // 3. IDENTITY CONFIRMED
      await new Promise(r => setTimeout(r, 2000));
      setSimulationState('DISCREPANCY_EXPLAINED');
      
      // 4. DISCREPANCY EXPLAINED
      await new Promise(r => setTimeout(r, 2500));
      setSimulationState('CUSTOMER_RESPONSE');
      
      // 5. CUSTOMER RESPONSE
      await new Promise(r => setTimeout(r, 2000));
      setSimulationState('VERIFIED');
      
      // 6. VERIFIED - Finalizing
      await new Promise(r => setTimeout(r, 1000));

      const mockResult = {
        id: caseId,
        verification_classification: 'AI_VERIFICATION_ELIGIBLE',
        verification_status: 'AI_VERIFIED',
        details: { score: 0.92 },
        record_a: selectedCase?.record_a,
        ai_call_result: {
          language: selectedLanguage,
          summary: 'Customer confirmed that the phone number ending in 1234 is their old number, and 2745 is their current number. Identity verified.',
          timestamp: new Date().toISOString()
        },
        ai_call_confidence: 'High'
      };

      try {
        const updatedCase = await triggerAIVerification(caseId, targetPhone);
        setCases((prev) => prev.map(c => c.id === caseId ? updatedCase : c));
        setSelectedCase(updatedCase);
      } catch (err) {
        setCases((prev) => prev.map(c => c.id === caseId ? mockResult : c));
        setSelectedCase(mockResult);
      }
      setStatusMessage('Kovi AI Verification Call completed successfully.');
      setSimulationState(null);
    } catch (err) {
      alert(err.message || 'Failed to trigger AI Verification');
      setSimulationState(null);
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
              {/* Customer Contact Tab */}
              <div className="bg-blue-50 p-4 rounded-xl border border-blue-100 flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-blue-800 uppercase flex items-center gap-1 mb-1">
                    <UserCheck className="w-4 h-4"/> Target Customer Profile
                  </div>
                  <div className="font-bold text-slate-900">{selectedCase.record_a?.original_name || 'Customer'}</div>
                  <div className="font-mono text-sm text-slate-600 mt-0.5">Phone: +91 9920602745</div>
                </div>
              </div>

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

              {/* Simulated AI Flow UI */}
              {simulationState && (
                <div className="bg-slate-900 text-white p-5 rounded-xl border border-slate-700 space-y-4 animate-fade-in shadow-lg">
                  <div className="text-xs font-bold text-emerald-400 uppercase flex items-center gap-2 mb-2 tracking-wider">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    SIMULATED AI VERIFICATION (BOLNA)
                  </div>
                  
                  <div className="space-y-3 text-sm font-mono text-slate-300">
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className={`w-4 h-4 ${simulationState !== 'INITIATED' ? 'text-emerald-500' : 'text-slate-600'}`} />
                      <span className={simulationState === 'INITIATED' ? 'text-white font-bold' : ''}>Call Initiated to +91 9920602745</span>
                    </div>
                    
                    {['LANGUAGE_DETECTED', 'IDENTITY_CONFIRMED', 'DISCREPANCY_EXPLAINED', 'CUSTOMER_RESPONSE', 'VERIFIED'].indexOf(simulationState) >= 0 && (
                      <div className="flex items-center gap-3 animate-fade-in">
                        <CheckCircle2 className={`w-4 h-4 ${simulationState !== 'LANGUAGE_DETECTED' ? 'text-emerald-500' : 'text-slate-600'}`} />
                        <span className={simulationState === 'LANGUAGE_DETECTED' ? 'text-white font-bold' : ''}>Customer Language Detected: {selectedLanguage}</span>
                      </div>
                    )}
                    
                    {['IDENTITY_CONFIRMED', 'DISCREPANCY_EXPLAINED', 'CUSTOMER_RESPONSE', 'VERIFIED'].indexOf(simulationState) >= 0 && (
                      <div className="flex items-center gap-3 animate-fade-in">
                        <CheckCircle2 className={`w-4 h-4 ${simulationState !== 'IDENTITY_CONFIRMED' ? 'text-emerald-500' : 'text-slate-600'}`} />
                        <span className={simulationState === 'IDENTITY_CONFIRMED' ? 'text-white font-bold' : ''}>Identity Confirmed</span>
                      </div>
                    )}
                    
                    {['DISCREPANCY_EXPLAINED', 'CUSTOMER_RESPONSE', 'VERIFIED'].indexOf(simulationState) >= 0 && (
                      <div className="flex items-center gap-3 animate-fade-in">
                        <CheckCircle2 className={`w-4 h-4 ${simulationState !== 'DISCREPANCY_EXPLAINED' ? 'text-emerald-500' : 'text-slate-600'}`} />
                        <span className={simulationState === 'DISCREPANCY_EXPLAINED' ? 'text-white font-bold' : ''}>Discrepancy Explained to Customer</span>
                      </div>
                    )}
                    
                    {['CUSTOMER_RESPONSE', 'VERIFIED'].indexOf(simulationState) >= 0 && (
                      <div className="flex items-center gap-3 animate-fade-in">
                        <CheckCircle2 className={`w-4 h-4 ${simulationState !== 'CUSTOMER_RESPONSE' ? 'text-emerald-500' : 'text-slate-600'}`} />
                        <span className={simulationState === 'CUSTOMER_RESPONSE' ? 'text-white font-bold' : ''}>Customer Response Analyzed</span>
                      </div>
                    )}

                    {simulationState === 'VERIFIED' && (
                      <div className="flex items-center gap-3 animate-fade-in text-emerald-400 font-bold mt-4 pt-2 border-t border-slate-700">
                        <CheckCircle2 className="w-5 h-5" />
                        <span>AI VERIFIED</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-4 flex flex-col sm:flex-row justify-end items-center gap-3 border-t border-slate-100">
                {selectedCase.verification_classification === 'AI_VERIFICATION_ELIGIBLE' && !simulationState && (
                  <>
                    <select
                      value={selectedLanguage}
                      onChange={(e) => setSelectedLanguage(e.target.value)}
                      className="bg-slate-50 border border-slate-200 text-slate-700 text-xs font-bold rounded-xl px-3 py-2.5 outline-none focus:border-purple-500"
                    >
                      <option value="English">English</option>
                      <option value="Hindi">Hindi</option>
                      <option value="Marathi">Marathi</option>
                    </select>

                    <button
                      onClick={() => handleTriggerAI(selectedCase.id)}
                      disabled={actionLoading || selectedCase.verification_status === 'AI_CALL_IN_PROGRESS'}
                      className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-xl flex items-center gap-2 shadow-sm disabled:opacity-50 transition-all shadow-purple-900/20"
                    >
                      <PhoneCall className="w-4 h-4" />
                      Simulate AI Verification
                    </button>
                  </>
                )}

                {selectedCase.verification_classification === 'HUMAN_VERIFICATION_REQUIRED' && (
                  <button
                    disabled
                    className="px-5 py-2.5 bg-slate-100 text-slate-500 font-bold text-xs rounded-xl flex items-center gap-2 border border-slate-200 cursor-not-allowed"
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
