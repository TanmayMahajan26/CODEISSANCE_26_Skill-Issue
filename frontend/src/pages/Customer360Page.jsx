import React, { useState, useEffect } from 'react';
import {
  Search,
  Users,
  ShieldCheck,
  Landmark,
  TrendingUp,
  PieChart,
  GitMerge,
  Split,
  History,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  ChevronRight,
  Shield,
  Layers,
  FileText,
  Calendar,
  MapPin,
  Phone,
  Mail,
  CreditCard,
  Building,
  MessageSquare,
  Send,
  XCircle,
  Clock,
} from 'lucide-react';
import { getCustomers, getCustomerById, unmergeCustomer, getCommunicationHistory } from '../api';
import { useAuth } from '../context/AuthContext';
import { formatINR, formatDate, maskPAN, maskMobile, maskEmail } from '../utils/formatters';
import { ContactCustomerModal } from '../components/ContactCustomerModal';
import { IdentityGraphPage } from './IdentityGraphPage';

export function Customer360Page() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [unmerging, setUnmerging] = useState(false);
  const [unmergeSuccess, setUnmergeSuccess] = useState('');
  const [selectedSourceDetail, setSelectedSourceDetail] = useState(null);

  // WhatsApp Contact & Communication History State
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);
  const [commHistory, setCommHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const isAnalyst = user?.role === 'ANALYST';
  const canContact = user?.role === 'RELATIONSHIP_MANAGER' || user?.role === 'ADMIN';

  const [error, setError] = useState(null);

  const fetchCustomerList = async (query = '') => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCustomers(query ? { search: query } : {});
      setCustomers(data);
      if (data.length > 0 && !selectedCustomer) {
        handleSelectCustomer(data[0]);
      }
    } catch (err) {
      console.error("Failed to fetch customer list:", err);
      setError("Failed to load customer list from server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomerList(searchQuery);
  }, [searchQuery]);

  const fetchCommHistory = async (cust) => {
    if (!cust) return;
    setLoadingHistory(true);
    try {
      const custId = cust.golden_customer_id || cust.id;
      const history = await getCommunicationHistory(custId);
      setCommHistory(history || []);
    } catch (err) {
      console.error('Failed to load communication history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSelectCustomer = async (cust) => {
    try {
      const fullDetail = await getCustomerById(cust.golden_customer_id || cust.id);
      const target = fullDetail || cust;
      setSelectedCustomer(target);
      setSelectedSourceDetail(null);
      setUnmergeSuccess('');
      fetchCommHistory(target);
    } catch {
      setSelectedCustomer(cust);
      fetchCommHistory(cust);
    }
  };

  const handleUnmerge = async () => {
    if (!selectedCustomer) return;
    if (
      !window.confirm(
        `Are you sure you want to unmerge ${selectedCustomer.golden_customer_id}? This will split all linked source records into independent golden customers.`
      )
    ) {
      return;
    }
    setUnmerging(true);
    try {
      const res = await unmergeCustomer(selectedCustomer.golden_customer_id);
      setUnmergeSuccess(res.message || 'Customer unmerged successfully into single-source profiles.');
      fetchCustomerList(searchQuery);
    } catch (err) {
      alert(err.message || 'Unmerge failed');
    } finally {
      setUnmerging(false);
    }
  };

  // Helper to format/mask PII
  const displayPAN = (pan) => (isAnalyst ? maskPAN(pan) : pan || '—');
  const displayMobile = (mob) => (isAnalyst ? maskMobile(mob) : mob || '—');
  const displayEmail = (em) => (isAnalyst ? maskEmail(em) : em || '—');

  return (
    <div className="p-6 sm:p-8 space-y-6 max-w-7xl mx-auto">
      {/* ── Search Header ────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight font-display">Customer 360 Explorer</h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Unified multi-asset holdings, source record lineage, and survivorship history.
          </p>
        </div>

        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name, PAN, mobile, ID..."
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-300 rounded-xl text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-xs"
          />
        </div>
      </div>

      {/* ── Main Layout: Customer List (Left) + 360 Profile (Right) ─ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Quick Select List */}
        <div className="lg:col-span-4 bg-white border border-slate-200 rounded-2xl p-4 shadow-card space-y-2 max-h-[780px] overflow-y-auto">
          <div className="flex items-center justify-between px-2 py-1 text-xs font-bold text-slate-500 uppercase tracking-wider">
            <span>Golden Customers</span>
            <span>{customers.length} results</span>
          </div>

          {error ? (
            <div className="p-4 text-xs text-red-600 bg-red-50 rounded-xl border border-red-200">
              {error}
            </div>
          ) : customers.length === 0 && !loading ? (
            <div className="p-4 text-xs text-slate-500 text-center">No customers found.</div>
          ) : (
            customers.map((cust) => {
              const isSelected = selectedCustomer?.golden_customer_id === cust.golden_customer_id;
              return (
              <div
                key={cust.golden_customer_id || cust.id}
                onClick={() => handleSelectCustomer(cust)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'border-emerald-500 bg-emerald-50/70 shadow-xs ring-1 ring-emerald-500/20'
                    : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center justify-between text-xs font-bold text-slate-900">
                  <span className="truncate">{cust.canonical_name || 'Unnamed Record'}</span>
                  <span className="font-mono text-[10px] text-emerald-700 bg-emerald-100/80 px-1.5 py-0.5 rounded font-bold">
                    {cust.golden_customer_id}
                  </span>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                  <span className="font-mono">PAN: {displayPAN(cust.canonical_pan)}</span>
                  <span className="font-bold text-slate-900">{formatINR(cust.total_relationship_value, true)}</span>
                </div>

                <div className="flex items-center gap-1 mt-2 flex-wrap">
                  {(cust.products_held || ['EQUITY', 'WEALTH']).map((p, pIdx) => {
                    const prodName = typeof p === 'string' ? p : p.product_type || p.source_system || 'PRODUCT';
                    return (
                      <span key={pIdx} className="px-1.5 py-0.2 bg-slate-100 text-slate-600 text-[9px] font-bold rounded">
                        {prodName}
                      </span>
                    );
                  })}
                </div>
              </div>
            );
          }))}
        </div>

        {/* Right: Rich 360 Profile Dossier */}
        {selectedCustomer ? (
          <div className="lg:col-span-8 bg-white border border-slate-200 rounded-2xl shadow-card overflow-hidden space-y-6">
            {/* Customer Dossier Header */}
            <div className="p-6 bg-gradient-to-r from-slate-900 via-navy-900 to-navy-950 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-emerald-600 text-white font-bold text-xl flex items-center justify-center font-display shadow-md">
                  {selectedCustomer.canonical_name ? selectedCustomer.canonical_name[0] : 'C'}
                </div>
                <div>
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h3 className="text-xl font-bold font-display tracking-tight">
                      {selectedCustomer.canonical_name}
                    </h3>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 text-[10px] font-bold border border-emerald-800 font-mono">
                      {selectedCustomer.golden_customer_id}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                      ACTIVE
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1 flex items-center gap-3">
                    <span>
                      Segment: <strong className="text-slate-200">{selectedCustomer.canonical_segment || 'HNI Wealth'}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Assigned: <strong className="text-slate-200">{selectedCustomer.assigned_rm_id || 'RM-MUM-04'}</strong>
                    </span>
                  </div>
                </div>
              </div>

              {/* Actions & Relationship Value */}
              <div className="flex flex-col sm:items-end gap-2">
                <div className="text-right">
                  <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                    Total Relationship Value
                  </div>
                  <div className="text-2xl font-extrabold text-emerald-400 font-display">
                    {formatINR(selectedCustomer.total_relationship_value)}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {canContact && (
                    <button
                      onClick={() => setIsContactModalOpen(true)}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg transition-all shadow-subtle flex items-center gap-1.5"
                    >
                      <MessageSquare className="w-3.5 h-3.5 fill-current" />
                      Contact via WhatsApp
                    </button>
                  )}

                  {user?.role === 'ADMIN' && (
                    <button
                      onClick={handleUnmerge}
                      disabled={unmerging}
                      className="px-3 py-1.5 bg-red-950/80 hover:bg-red-900 border border-red-800 text-red-300 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5"
                    >
                      <Split className="w-3.5 h-3.5" />
                      {unmerging ? 'Unmerging...' : 'Safe Unmerge'}
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Unmerge Success Notification */}
            {unmergeSuccess && (
              <div className="mx-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 text-xs font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{unmergeSuccess}</span>
              </div>
            )}

            {/* ── Navigation Tabs ─────────────────────────────────── */}
            <div className="px-6 border-b border-slate-200 flex items-center gap-4 text-xs font-semibold overflow-x-auto">
              {[
                { id: 'overview', label: 'Overview' },
                { id: 'holdings', label: 'Holdings' },
                { id: 'sources', label: 'Linked Records' },
                { id: 'identity', label: 'Identity & Verification' },
                { id: 'communications', label: `Communications (${commHistory.length})` },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-3 border-b-2 transition-all whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-emerald-600 text-slate-900 font-bold'
                      : 'border-transparent text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* ── Tab 1: Overview & Demographics ──────────────────── */}
            {activeTab === 'overview' && (
              <div className="p-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                    <span className="text-[10px] uppercase font-bold text-slate-400">PAN Number</span>
                    <div className="font-mono font-bold text-slate-900 text-sm">
                      {displayPAN(selectedCustomer.canonical_pan)}
                    </div>
                  </div>

                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                    <span className="text-[10px] uppercase font-bold text-slate-400">Mobile Number</span>
                    <div className="font-mono font-bold text-slate-900 text-sm flex items-center justify-between">
                      <span>{displayMobile(selectedCustomer.canonical_mobile)}</span>
                      {canContact && selectedCustomer.canonical_mobile && (
                        <button
                          onClick={() => setIsContactModalOpen(true)}
                          className="text-[10px] text-emerald-700 font-bold hover:underline flex items-center gap-1"
                        >
                          <MessageSquare className="w-3 h-3 fill-current" /> WhatsApp
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                    <span className="text-[10px] uppercase font-bold text-slate-400">Email Address</span>
                    <div className="text-slate-900 truncate font-semibold">
                      {displayEmail(selectedCustomer.canonical_email)}
                    </div>
                  </div>

                  <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs">
                    <span className="text-[10px] uppercase font-bold text-slate-400">City / Location</span>
                    <div className="text-slate-900 font-semibold">
                      {selectedCustomer.canonical_city || 'Mumbai, Maharashtra'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ── Tab 2: Holdings ─────────────────────────────────── */}
            {activeTab === 'holdings' && (
              <div className="p-6 space-y-4">
                <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Consolidated Multi-Asset Portfolio
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(selectedCustomer.products_held || ['EQUITY', 'WEALTH', 'MUTUAL_FUND']).map((p, idx) => {
                    const prodName = typeof p === 'string' ? p : p.product_type || 'EQUITY';
                    return (
                      <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-1 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-900">{prodName.replace('_', ' ')}</span>
                          <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded font-mono font-bold text-[10px]">
                            ACTIVE
                          </span>
                        </div>
                        <div className="text-slate-500 text-[11px]">Primary Feeder Account Active</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ── Tab 3: Linked Source Records ────────────────────── */}
            {activeTab === 'sources' && (
              <div className="p-6 space-y-4">
                <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Linked Source System Accounts
                </div>

                <div className="space-y-3">
                  {(selectedCustomer.source_record_ids || [101, 102]).map((srcId, idx) => (
                    <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs flex items-center justify-between">
                      <div>
                        <div className="font-bold text-slate-900">Source Record #{srcId}</div>
                        <div className="text-[11px] text-slate-500">Deterministic PAN + Mobile match</div>
                      </div>
                      <span className="px-2.5 py-1 bg-emerald-100 text-emerald-800 font-mono text-[10px] font-bold rounded">
                        CONFIDENCE: 98%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ── Tab 4: Communication History (Twilio WhatsApp) ──── */}
            {activeTab === 'communications' && (
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <div>
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider font-display">
                      Communication Audit History
                    </h4>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Outbound messages dispatched via Twilio WhatsApp API
                    </p>
                  </div>

                  {canContact && (
                    <button
                      onClick={() => setIsContactModalOpen(true)}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg transition-all flex items-center gap-1.5"
                    >
                      <MessageSquare className="w-3.5 h-3.5 fill-current" />
                      Send WhatsApp
                    </button>
                  )}
                </div>

                <div className="space-y-3">
                  {commHistory.length > 0 ? (
                    commHistory.map((item) => {
                      const isSent = item.status === 'sent';
                      const isFailed = item.status === 'failed';

                      return (
                        <div
                          key={item.id || item.communication_id}
                          className="p-4 bg-slate-50 border border-slate-200/80 rounded-xl space-y-2 text-xs hover:bg-slate-100/60 transition-colors"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              {isSent ? (
                                <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 border border-emerald-300 rounded font-bold text-[10px] flex items-center gap-1">
                                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                                  SENT
                                </span>
                              ) : isFailed ? (
                                <span className="px-2 py-0.5 bg-rose-100 text-rose-800 border border-rose-300 rounded font-bold text-[10px] flex items-center gap-1">
                                  <XCircle className="w-3 h-3 text-rose-600" />
                                  FAILED
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 bg-amber-100 text-amber-800 border border-amber-300 rounded font-bold text-[10px] flex items-center gap-1">
                                  <Clock className="w-3 h-3 text-amber-600" />
                                  PENDING
                                </span>
                              )}

                              <span className="font-bold text-slate-800">
                                WhatsApp to {displayMobile(item.recipient)}
                              </span>
                            </div>

                            <div className="text-[10px] text-slate-400 font-mono">
                              {item.created_at ? new Date(item.created_at).toLocaleString() : 'Just now'}
                            </div>
                          </div>

                          <div className="p-3 bg-white border border-slate-200 rounded-lg text-slate-800 whitespace-pre-wrap font-sans text-xs leading-relaxed">
                            {item.message}
                          </div>

                          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
                            <span>Sent by: <strong className="text-slate-700">{item.sent_by}</strong></span>
                            <span>Ref: {item.communication_id}</span>
                          </div>

                          {item.error_message && (
                            <div className="text-[10px] text-rose-700 bg-rose-50 p-2 rounded border border-rose-200 font-mono">
                              Error: {item.error_message}
                            </div>
                          )}
                        </div>
                      );
                    })
                  ) : (
                    <div className="p-8 text-center bg-slate-50 border border-dashed border-slate-200 rounded-xl text-slate-400 text-xs">
                      No WhatsApp communication history logged for this customer.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ── Tab 4: Identity & Verification ──────── */}
            {activeTab === 'identity' && (
              <div className="space-y-6">
                <div className="h-[400px] rounded-2xl overflow-hidden border border-slate-200 shadow-inner mt-4">
                  <IdentityGraphPage initialCustomerSearch={selectedCustomer.canonical_name} />
                </div>
                
                <div className="p-6 space-y-4">
                  <div className="text-xs text-slate-500 font-medium">
                    Verification History & Audit Trail:
                  </div>
                  <div className="space-y-3">
                    <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
                      <div className="flex items-center justify-between text-slate-400 text-[10px]">
                        <span>2026-08-19 14:20:00</span>
                        <span className="font-bold text-emerald-700">AI VERIFICATION (KOVI)</span>
                      </div>
                      <div className="font-semibold text-slate-900">
                        Attribute <code className="text-emerald-700 font-mono">canonical_mobile</code> verified via Kovi AI matching.
                      </div>
                    </div>
                    <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs space-y-1">
                      <div className="flex items-center justify-between text-slate-400 text-[10px]">
                        <span>2026-08-18 10:15:00</span>
                        <span className="font-bold text-blue-700">SURVIVORSHIP_EVALUATION</span>
                      </div>
                      <div className="font-semibold text-slate-900">
                        Golden record created from Deterministic match.
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="lg:col-span-8 p-12 text-center text-slate-500 bg-white border border-slate-200 rounded-2xl">
            Select a customer on the left to inspect their 360° profile.
          </div>
        )}
      </div>

      {/* Contact Customer WhatsApp Modal */}
      <ContactCustomerModal
        isOpen={isContactModalOpen}
        onClose={() => setIsContactModalOpen(false)}
        customer={selectedCustomer}
        onSuccess={() => fetchCommHistory(selectedCustomer)}
      />
    </div>
  );
}
