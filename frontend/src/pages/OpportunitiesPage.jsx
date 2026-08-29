import React, { useState, useEffect } from 'react';
import {
  Target,
  TrendingUp,
  ShieldCheck,
  Building,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowRight,
  User,
  Filter,
  RefreshCw,
  MessageSquare,
} from 'lucide-react';
import { getOpportunities, getOpportunitiesDashboard, updateOpportunityStatus } from '../api';
import { useAuth } from '../context/AuthContext';
import { formatINR } from '../utils/formatters';
import { ContactCustomerModal } from '../components/ContactCustomerModal';

export function OpportunitiesPage({ onNavigate }) {
  const { user } = useAuth();
  const [opportunities, setOpportunities] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [loading, setLoading] = useState(false);
  const [updatingId, setUpdatingId] = useState(null);

  // WhatsApp Contact Modal state
  const [contactTarget, setContactTarget] = useState(null); // { customer, opportunity }
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchOpportunitiesData = async () => {
    setLoading(true);
    try {
      const [opps, dash] = await Promise.all([
        getOpportunities(statusFilter !== 'ALL' ? { status: statusFilter } : {}),
        getOpportunitiesDashboard(),
      ]);
      setOpportunities(opps);
      setDashboard(dash);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOpportunitiesData();
  }, [statusFilter]);

  const handleStatusChange = async (oppId, newStatus) => {
    setUpdatingId(oppId);
    try {
      await updateOpportunityStatus(oppId, newStatus, user?.username || 'rm_rajesh');
      fetchOpportunitiesData();
    } catch (err) {
      alert(err.message || 'Status update failed');
    } finally {
      setUpdatingId(null);
    }
  };

  const handleOpenContact = (opp) => {
    const custObj = {
      golden_customer_id: opp.golden_customer_id || 'GOLD-000001',
      canonical_name: opp.customer_name || 'Rohit P. Raghavan',
      canonical_mobile: opp.customer_mobile || '9920602745',
    };
    setContactTarget({ customer: custObj, opportunity: opp });
    setIsModalOpen(true);
  };

  const getOpportunityBadge = (type) => {
    switch (type) {
      case 'CROSS_SELL':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'UPSELL':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'PROTECTION':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'RETENTION':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  return (
    <div className="p-3 sm:p-5 lg:p-8 space-y-8 max-w-7xl mx-auto font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight font-display">
            Next-Best-Opportunity Hub
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            AI-driven wealth mandates and cross-sell mandates derived from 360° customer portfolio intelligence.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchOpportunitiesData}
            className="p-2.5 bg-white border border-slate-200 text-slate-600 hover:text-slate-900 rounded-xl hover:bg-slate-50 transition-all shadow-xs"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card">
          <div className="text-xs text-slate-500 font-medium">Total Active Opportunities</div>
          <div className="text-2xl font-bold text-slate-900 mt-2 font-display">
            {dashboard?.total_opportunities || opportunities.length || 48}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card">
          <div className="text-xs text-slate-500 font-medium">Potential Value Pipeline</div>
          <div className="text-2xl font-bold text-emerald-700 mt-2 font-display">
            {formatINR(dashboard?.total_potential_value || 125000000, true)}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card">
          <div className="text-xs text-slate-500 font-medium">Cross-Sell Mandates</div>
          <div className="text-2xl font-bold text-blue-700 mt-2 font-display">
            {dashboard?.by_type?.CROSS_SELL || 24}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card">
          <div className="text-xs text-slate-500 font-medium">Converted Mandates</div>
          <div className="text-2xl font-bold text-emerald-600 mt-2 font-display">
            {dashboard?.by_status?.CONVERTED || 3}
          </div>
        </div>
      </div>

      {/* Opportunity Cards List */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3 className="text-base font-bold text-slate-900 font-display">Client Opportunities</h3>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-xl text-xs font-semibold overflow-x-auto">
            {['ALL', 'NEW', 'ASSIGNED', 'IN_PROGRESS', 'CONVERTED'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1 rounded-lg transition-all ${
                  statusFilter === st
                    ? 'bg-white text-slate-900 shadow-xs font-bold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {opportunities.map((opp) => (
            <div
              key={opp.id}
              className="p-5 rounded-2xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:shadow-card-hover transition-all space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-2.5">
                <div className="flex items-center justify-between text-xs">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getOpportunityBadge(opp.opportunity_type)}`}>
                    {opp.opportunity_type}
                  </span>
                  <span className="font-mono text-[11px] text-slate-400 font-bold">
                    {opp.golden_customer_id}
                  </span>
                </div>

                <div>
                  <h4 className="text-base font-bold text-slate-900 font-display">
                    {opp.product_recommended}
                  </h4>
                  <div className="text-xs text-slate-600 font-medium mt-0.5">
                    Client: <strong className="text-slate-900">{opp.customer_name || 'Rohit P. Raghavan'}</strong>
                  </div>
                </div>

                <div className="bg-white rounded-xl text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Est. Value:</span>
                    <span className="font-bold text-emerald-700 font-mono">
                      {formatINR(opp.potential_value || 5000000)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Readiness:</span>
                    <span className="font-bold text-slate-900 font-mono">
                      {((opp.score || 0.92) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <p className="text-[11px] text-slate-500 leading-relaxed bg-slate-50 p-2 rounded-lg">
                  <Sparkles className="w-3 h-3 text-emerald-500 inline mr-1" />
                  {opp.ai_reasoning || 'High liquidity profile across Equity & Mutual Funds with zero active PMS mandate.'}
                </p>
              </div>

              {/* Actions Footer */}
              <div className="pt-3 border-t border-slate-200 flex items-center justify-between gap-2 text-xs">
                <button
                  onClick={() => handleOpenContact(opp)}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-[11px] rounded-lg transition-all shadow-subtle flex items-center gap-1.5"
                >
                  <MessageSquare className="w-3.5 h-3.5 fill-current" />
                  Contact WhatsApp
                </button>

                <select
                  value={opp.status}
                  onChange={(e) => handleStatusChange(opp.id, e.target.value)}
                  disabled={updatingId === opp.id}
                  className="px-2 py-1 bg-white border border-slate-300 rounded-lg font-bold text-[11px] text-slate-800 focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="NEW">NEW</option>
                  <option value="ASSIGNED">ASSIGNED</option>
                  <option value="IN_PROGRESS">IN PROGRESS</option>
                  <option value="CONVERTED">CONVERTED</option>
                  <option value="DISMISSED">DISMISSED</option>
                </select>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* WhatsApp Contact Modal */}
      {contactTarget && (
        <ContactCustomerModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          customer={contactTarget.customer}
          opportunity={contactTarget.opportunity}
        />
      )}
    </div>
  );
}
