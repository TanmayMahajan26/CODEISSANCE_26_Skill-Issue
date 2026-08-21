import React, { useState } from 'react';
import {
  Compass,
  Lock,
  User,
  Shield,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  KeyRound,
  Eye,
  EyeOff,
  UserCheck,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { MOCK_DEMO_USERS } from '../utils/mockData';

export function LoginPage({ onNavigate }) {
  const { login, backendStatus } = useAuth();
  const [usernameOrEmail, setUsernameOrEmail] = useState('admin');
  const [password, setPassword] = useState('adminpassword123');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [selectedDemoUser, setSelectedDemoUser] = useState('admin');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setLoading(true);

    const res = await login(usernameOrEmail, password);
    setLoading(false);

    if (res.success) {
      // Role-based redirect
      if (res.user.role === 'REVIEWER') {
        onNavigate('reviews');
      } else if (res.user.role === 'RELATIONSHIP_MANAGER') {
        onNavigate('opportunities');
      } else {
        onNavigate('overview');
      }
    } else {
      setErrorMessage(res.error || 'Invalid username or password');
    }
  };

  const handleSelectDemo = (demo) => {
    setSelectedDemoUser(demo.username);
    setUsernameOrEmail(demo.username);
    setPassword(demo.password);
  };

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4 sm:p-6 lg:p-8 font-sans selection:bg-emerald-100 selection:text-emerald-900">
      <div className="w-full max-w-5xl bg-white rounded-3xl shadow-card-hover border border-slate-200/90 overflow-hidden grid grid-cols-1 lg:grid-cols-12 min-h-[640px]">
        {/* ── Left Side: Enterprise Brand Statement ──────────────── */}
        <div className="lg:col-span-5 bg-gradient-to-b from-navy-950 via-navy-900 to-navy-950 p-8 sm:p-10 text-white flex flex-col justify-between relative overflow-hidden">
          {/* Subtle Glow */}
          <div className="absolute -bottom-16 -right-16 w-64 h-64 bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />

          <div>
            {/* Logo */}
            <div
              className="flex items-center gap-3 cursor-pointer"
              onClick={() => onNavigate('landing')}
            >
              <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center shadow-subtle">
                <Compass className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold tracking-tight font-display">
                Nexus<span className="text-emerald-400">360</span>
              </span>
            </div>

            <div className="mt-12">
              <span className="px-3 py-1 rounded-full bg-emerald-950/80 border border-emerald-700/50 text-emerald-400 text-xs font-semibold uppercase tracking-wider">
                Enterprise Gateway
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mt-4 font-display leading-tight">
                Secure access to your customer intelligence platform.
              </h2>
              <p className="text-slate-400 text-sm mt-3 leading-relaxed">
                Connect directly to your institution's identity resolution pipeline, review queues, and relationship graphs.
              </p>
            </div>

            {/* Feature List */}
            <div className="mt-8 space-y-3.5 text-xs text-slate-300">
              <div className="flex items-center gap-2.5">
                <Shield className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Strict Role-Based Access Control (RBAC)</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Lock className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Standard RFC 7519 HMAC-SHA256 JWT Token Auth</span>
              </div>
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Immutable audit trail for all KYC operations</span>
              </div>
            </div>
          </div>

          {/* Bottom Backend Indicator */}
          <div className="pt-6 mt-8 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
            <span>Server: {backendStatus.online ? 'Live API (FastAPI)' : 'Embedded Demo DB'}</span>
            <span className="flex items-center gap-1 text-emerald-400 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              v0.1.0
            </span>
          </div>
        </div>

        {/* ── Right Side: Login Form & Demo Accounts ──────────────── */}
        <div className="lg:col-span-7 p-8 sm:p-12 flex flex-col justify-center bg-white">
          <div className="max-w-md w-full mx-auto">
            <h3 className="text-2xl font-bold text-slate-900 tracking-tight font-display">Sign in to Nexus360</h3>
            <p className="text-sm text-slate-500 mt-1">Enter your institution credentials or select a demo role below.</p>

            {/* Error Message */}
            {errorMessage && (
              <div className="mt-4 p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Username or Registered Email
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5 pointer-events-none" />
                  <input
                    type="text"
                    required
                    value={usernameOrEmail}
                    onChange={(e) => setUsernameOrEmail(e.target.value)}
                    placeholder="e.g. admin, reviewer_sarah"
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5 pointer-events-none" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-10 pr-10 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white font-semibold rounded-xl text-sm transition-all shadow-subtle hover:shadow-emerald-glow flex items-center justify-center gap-2 mt-2"
              >
                {loading ? (
                  <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    Sign In to Portal
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* ── Demo Accounts Switcher for Evaluation ─────────────── */}
            <div className="mt-8 pt-6 border-t border-slate-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                  <UserCheck className="w-3.5 h-3.5 text-emerald-600" />
                  Evaluation Demo Accounts
                </span>
                <span className="text-[11px] text-slate-400">Click to autofill</span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                {MOCK_DEMO_USERS.map((demo) => {
                  const isSelected = selectedDemoUser === demo.username;
                  return (
                    <button
                      key={demo.username}
                      type="button"
                      onClick={() => handleSelectDemo(demo)}
                      className={`p-2.5 text-left rounded-xl border transition-all text-xs flex flex-col justify-between ${
                        isSelected
                          ? 'border-emerald-500 bg-emerald-50/70 text-emerald-950 font-semibold shadow-xs ring-1 ring-emerald-500/20'
                          : 'border-slate-200 bg-slate-50/50 hover:bg-slate-100/70 text-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold">{demo.role.replace('_', ' ')}</span>
                        {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />}
                      </div>
                      <span className="text-[11px] text-slate-500 font-mono mt-0.5">{demo.username}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Back to Landing */}
            <div className="mt-6 text-center">
              <button
                onClick={() => onNavigate('landing')}
                className="text-xs text-slate-500 hover:text-slate-800 transition-colors"
              >
                ← Back to Landing Page
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
