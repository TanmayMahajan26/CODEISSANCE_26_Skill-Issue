import React, { useState } from 'react';
import {
  Compass,
  LayoutDashboard,
  Users,
  UploadCloud,
  Cpu,
  Inbox,
  Target,
  Sliders,
  Sparkles,
  History,
  ShieldCheck,
  TrendingUp,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export function Sidebar({ currentTab, onSelectTab }) {
  const { user } = useAuth();
  const role = user?.role || 'ADMIN';
  const [adminOpen, setAdminOpen] = useState(false);

  // Grouped Navigation Items
  const navGroups = [
    {
      title: 'MAIN',
      items: [
        { id: 'overview', label: 'Dashboard', icon: LayoutDashboard, roles: ['ADMIN', 'REVIEWER', 'RELATIONSHIP_MANAGER', 'ANALYST'] },
        { id: 'customers', label: 'Customers', icon: Users, roles: ['ADMIN', 'REVIEWER', 'RELATIONSHIP_MANAGER', 'ANALYST'] }
      ]
    },
    {
      title: 'IDENTITY OPERATIONS',
      items: [
        { id: 'matching', label: 'Matching Pipeline', icon: Cpu, roles: ['ADMIN'] },
        { id: 'reviews', label: 'Review Queue', icon: Inbox, roles: ['ADMIN', 'REVIEWER'], badge: 'Pending' },
        { id: 'verification', label: 'Verification Center', icon: ShieldCheck, roles: ['ADMIN', 'REVIEWER'], badge: 'AI/Human' }
      ]
    },
    {
      title: 'INTELLIGENCE',
      items: [
        { id: 'market', label: 'Market Intelligence', icon: TrendingUp, roles: ['ADMIN', 'RELATIONSHIP_MANAGER'], badge: 'Live' },
        { id: 'opportunities', label: 'Opportunities', icon: Target, roles: ['ADMIN', 'RELATIONSHIP_MANAGER'], badge: 'New' }
      ]
    }
  ];

  const adminItems = [
    { id: 'ingestion', label: 'Data Feeds', icon: UploadCloud, roles: ['ADMIN'] },
    { id: 'config', label: 'Business Rules', icon: Sliders, roles: ['ADMIN'] },
    { id: 'audit', label: 'Audit Trail', icon: History, roles: ['ADMIN'] },
    { id: 'simulator', label: 'What-If Simulator', icon: Sparkles, roles: ['ADMIN', 'ANALYST'] }
  ];

  const renderNavButton = (item) => {
    if (!item.roles.includes(role)) return null;
    const isActive = currentTab === item.id;
    const Icon = item.icon;

    return (
      <button
        key={item.id}
        onClick={() => onSelectTab(item.id)}
        className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all ${
          isActive
            ? 'bg-emerald-600 text-white shadow-sm font-bold'
            : 'text-slate-300 hover:bg-navy-850 hover:text-white'
        }`}
      >
        <div className="flex items-center gap-3">
          <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
          <span>{item.label}</span>
        </div>

        {item.badge && (
          <span
            className={`px-1.5 py-0.5 rounded-md text-[10px] font-bold ${
              isActive
                ? 'bg-emerald-800 text-emerald-100'
                : 'bg-emerald-950 text-emerald-400 border border-emerald-800/60'
            }`}
          >
            {item.badge}
          </span>
        )}
      </button>
    );
  };

  return (
    <aside className="w-64 bg-navy-950 text-white flex flex-col shrink-0 border-r border-slate-800 select-none h-full overflow-y-auto">
      {/* ── Brand Logo ───────────────────────────────────────────── */}
      <div>
        <div
          onClick={() => onSelectTab('landing')}
          className="h-20 px-6 flex items-center gap-3 border-b border-slate-800/80 cursor-pointer hover:bg-navy-900/50 transition-colors"
        >
          <div className="w-9 h-9 rounded-xl bg-emerald-600 flex items-center justify-center shadow-subtle">
            <Compass className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="text-lg font-bold tracking-tight font-display text-white">
              Nexus<span className="text-emerald-400">360</span>
            </div>
            <div className="text-[10px] text-slate-400 font-medium uppercase tracking-wider -mt-0.5">
              Financial Intelligence
            </div>
          </div>
        </div>

        {/* ── Navigation Menu ──────────────────────────────────────── */}
        <div className="px-3 py-6 space-y-6">
          {navGroups.map((group, idx) => {
            const hasVisibleItems = group.items.some(item => item.roles.includes(role));
            if (!hasVisibleItems) return null;

            return (
              <div key={idx} className="space-y-1">
                <div className="px-3 mb-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                  {group.title}
                </div>
                {group.items.map(renderNavButton)}
              </div>
            );
          })}

          {/* Collapsible Admin Section */}
          {adminItems.some(item => item.roles.includes(role)) && (
            <div className="space-y-1 pt-2 border-t border-slate-800/50">
              <button
                onClick={() => setAdminOpen(!adminOpen)}
                className="w-full flex items-center justify-between px-3 py-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest hover:text-slate-300 transition-colors"
              >
                ADMINISTRATION
                {adminOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
              </button>
              
              {adminOpen && (
                <div className="space-y-1 mt-1 pl-2 border-l border-slate-800/50 ml-3">
                  {adminItems.map(renderNavButton)}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
