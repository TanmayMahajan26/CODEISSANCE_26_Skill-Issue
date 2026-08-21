import React from 'react';
import {
  Search,
  Bell,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { ChevronDown, LogOut } from 'lucide-react';

export function Topbar({ title, subtitle, onSearchClick }) {
  const { user, backendStatus, switchDemoRole, logout } = useAuth();
  const [showRoleMenu, setShowRoleMenu] = React.useState(false);

  return (
    <header className="h-20 bg-white border-b border-slate-200 px-6 sm:px-8 flex items-center justify-between shrink-0 select-none">
      {/* ── Title & Breadcrumb ───────────────────────────────────── */}
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight font-display">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>

      {/* ── Right Actions & Status ──────────────────────────────── */}
      <div className="flex items-center gap-4">
        {/* Universal Customer Search Bar */}
        <div
          onClick={onSearchClick}
          className="hidden md:flex items-center gap-2.5 px-3.5 py-2 bg-slate-100/90 border border-slate-200/80 rounded-xl text-xs text-slate-500 hover:border-emerald-500 hover:bg-white cursor-pointer transition-all w-64 shadow-xs"
        >
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <span className="truncate">Search customer by PAN, name...</span>
          <kbd className="ml-auto px-1.5 py-0.5 bg-white border border-slate-200 text-slate-400 rounded text-[10px] font-mono">
            /
          </kbd>
        </div>

        {/* Backend Live Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-50 border border-slate-200">
          <span
            className={`w-2 h-2 rounded-full ${
              backendStatus.online ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
            }`}
          />
          <span className="text-slate-700 hidden sm:inline">
            {backendStatus.online ? 'FastAPI 8000' : 'Demo DB'}
          </span>
        </div>

        {/* User Identity Chip with Role Dropdown */}
        <div className="relative">
          <div 
            className="flex items-center gap-2 pl-3 border-l border-slate-200 text-xs cursor-pointer hover:bg-slate-50 p-1 rounded-lg transition-colors"
            onClick={() => setShowRoleMenu(!showRoleMenu)}
          >
            <div className="w-8 h-8 rounded-full bg-emerald-600 text-white font-bold flex items-center justify-center text-xs shadow-xs">
              {user?.username ? user.username[0].toUpperCase() : 'A'}
            </div>
            <div className="hidden lg:flex items-center gap-2 text-left">
              <div>
                <div className="font-semibold text-slate-800 leading-tight">
                  {user?.full_name?.split(' ')[0] || user?.username || 'Admin'}
                </div>
                <div className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                  {user?.role?.replace('_', ' ') || 'ADMIN'} <ChevronDown className="w-3 h-3" />
                </div>
              </div>
            </div>
          </div>

          {/* Role Switcher Dropdown */}
          {showRoleMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white border border-slate-200 rounded-xl shadow-card py-2 z-50 animate-slide-up">
              <div className="px-4 py-2 border-b border-slate-100 mb-2">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Simulate Demo Role</p>
              </div>
              {['ADMIN', 'REVIEWER', 'RELATIONSHIP_MANAGER', 'ANALYST'].map((r) => (
                <button
                  key={r}
                  onClick={() => { switchDemoRole(r); setShowRoleMenu(false); }}
                  className={`w-full text-left px-4 py-2 text-xs font-semibold hover:bg-slate-50 transition-colors ${user?.role === r ? 'text-emerald-600 bg-emerald-50' : 'text-slate-700'}`}
                >
                  {r.replace('_', ' ')}
                </button>
              ))}
              <div className="border-t border-slate-100 mt-2 pt-2">
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-xs font-bold text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
