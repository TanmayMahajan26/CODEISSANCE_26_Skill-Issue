import React from 'react';
import {
  Shield,
  Layers,
  Sparkles,
  TrendingUp,
  Landmark,
  PieChart,
  ArrowRight,
  FileCheck2,
  Lock,
  EyeOff,
  History,
  CheckCircle2,
  ChevronRight,
  Database,
  Search,
  Scale,
  Users,
  Compass,
} from 'lucide-react';
import { FinancialTreeHero } from '../components/hero/FinancialTreeHero';
import { useAuth } from '../context/AuthContext';

export function LandingPage({ onNavigate }) {
  const { user, backendStatus } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900 selection:bg-emerald-100 selection:text-emerald-900">
      {/* ── 1. Top Enterprise Navbar ────────────────────────────── */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => onNavigate('landing')}>
            <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center shadow-subtle">
              <Compass className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold text-slate-900 tracking-tight font-display">Nexus<span className="text-emerald-600">360</span></span>
              <span className="block text-[10px] uppercase font-semibold tracking-wider text-slate-400 -mt-1">Financial Intelligence</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <a href="#solutions" className="hover:text-emerald-700 transition-colors">Investment Solutions</a>
            <a href="#how-it-works" className="hover:text-emerald-700 transition-colors">How It Works</a>
            <a href="#security" className="hover:text-emerald-700 transition-colors">Security & Trust</a>
            <a href="#architecture" className="hover:text-emerald-700 transition-colors">Architecture</a>
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            {/* Backend Health Badge */}
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 border border-slate-200 text-slate-600">
              <span className={`w-2 h-2 rounded-full ${backendStatus.online ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
              <span>{backendStatus.online ? 'FastAPI Connected' : 'Demo Mode Active'}</span>
            </div>

            {user ? (
              <button
                onClick={() => onNavigate('overview')}
                className="px-5 py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 transition-all shadow-subtle hover:shadow-emerald-glow flex items-center gap-2"
              >
                Go to Dashboard
                <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <>
                <button
                  onClick={() => onNavigate('login')}
                  className="px-4 py-2 text-sm font-semibold text-slate-700 hover:text-slate-900 transition-colors border border-slate-300 rounded-xl hover:bg-slate-50"
                >
                  Sign In
                </button>
                <button
                  onClick={() => onNavigate('overview')}
                  className="px-5 py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-700 transition-all shadow-subtle hover:shadow-emerald-glow flex items-center gap-2"
                >
                  Explore Platform
                  <ArrowRight className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── 2. Hero Section ──────────────────────────────────────── */}
      <section className="relative pt-12 pb-20 overflow-hidden bg-gradient-to-b from-white via-slate-50 to-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-10">
            {/* Pill Tag */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold uppercase tracking-wider mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600" />
              Unified. Intelligent. Customer-Centric.
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-slate-900 tracking-tight leading-[1.15] font-display">
              Grow Relationships. <br className="hidden sm:inline" />
              <span className="text-emerald-600">Grow Value.</span>
            </h1>

            {/* Subheadline */}
            <p className="mt-5 text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto">
              Nexus360 is the AI-powered Customer 360 and Relationship Intelligence platform for financial institutions. Unify fragmented data across banking, investments, insurance and wealth systems into a trusted, explainable view.
            </p>

            {/* CTA Buttons */}
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => onNavigate('overview')}
                className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-emerald-600 text-white text-base font-semibold hover:bg-emerald-700 transition-all shadow-md hover:shadow-emerald-glow flex items-center justify-center gap-2"
              >
                Explore Dashboard
                <ArrowRight className="w-4 h-4" />
              </button>
              <a
                href="#how-it-works"
                className="w-full sm:w-auto px-7 py-3.5 rounded-xl bg-white border border-slate-300 text-slate-700 text-base font-semibold hover:bg-slate-50 transition-all flex items-center justify-center gap-2"
              >
                How It Works
              </a>
            </div>

            {/* Micro Feature Indicators */}
            <div className="mt-10 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-2xl mx-auto text-left">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                <Sparkles className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>AI-Powered Insights</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                <Shield className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Secure & Compliant</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                <TrendingUp className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Real-time Opportunities</span>
              </div>
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                <Users className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>360° Customer View</span>
              </div>
            </div>
          </div>

          {/* Interactive Financial Visual Hero Graphic */}
          <div className="mt-6">
            <FinancialTreeHero onExplore={() => onNavigate('overview')} />
          </div>
        </div>
      </section>

      {/* ── 3. Investment & Domain Solutions ──────────────────────── */}
      <section id="solutions" className="py-20 bg-white border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mb-12">
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight font-display">Investment Solutions</h2>
            <p className="text-slate-600 mt-2 text-base">Comprehensive multi-asset coverage across retail, HNI, and corporate holdings.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Card 1: Equity */}
            <div className="bg-slate-50/80 border border-slate-200 rounded-2xl p-6 hover:shadow-card-hover transition-all duration-300 hover:border-blue-400 group">
              <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center mb-5 text-blue-600 group-hover:scale-110 transition-transform">
                <TrendingUp className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 font-display">Equity</h3>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">Direct stocks, demat accounts, and institutional trading portfolios.</p>
              <div className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">1Y Avg Return</span>
                <span className="font-bold text-emerald-600 text-sm">+18.5%</span>
              </div>
              <button onClick={() => onNavigate('overview')} className="mt-3 text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 group-hover:underline">
                Explore Equity <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Card 2: Mutual Funds */}
            <div className="bg-slate-50/80 border border-slate-200 rounded-2xl p-6 hover:shadow-card-hover transition-all duration-300 hover:border-amber-400 group">
              <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center mb-5 text-amber-600 group-hover:scale-110 transition-transform">
                <PieChart className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 font-display">Mutual Funds</h3>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">Diversified portfolios, SIP mandates, and active fund manager relationships.</p>
              <div className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">1Y Avg Return</span>
                <span className="font-bold text-emerald-600 text-sm">+14.2%</span>
              </div>
              <button onClick={() => onNavigate('overview')} className="mt-3 text-xs font-semibold text-amber-600 hover:text-amber-800 flex items-center gap-1 group-hover:underline">
                Explore Mutual Funds <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Card 3: Fixed Income / Banking */}
            <div className="bg-slate-50/80 border border-slate-200 rounded-2xl p-6 hover:shadow-card-hover transition-all duration-300 hover:border-emerald-400 group">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center mb-5 text-emerald-600 group-hover:scale-110 transition-transform">
                <Landmark className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 font-display">Fixed Income</h3>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">Corporate deposits, sovereign bonds, debentures, and savings relationships.</p>
              <div className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">1Y Avg Return</span>
                <span className="font-bold text-emerald-600 text-sm">+7.8%</span>
              </div>
              <button onClick={() => onNavigate('overview')} className="mt-3 text-xs font-semibold text-emerald-600 hover:text-emerald-800 flex items-center gap-1 group-hover:underline">
                Explore Fixed Income <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Card 4: Gold & Commodities / Wealth */}
            <div className="bg-slate-50/80 border border-slate-200 rounded-2xl p-6 hover:shadow-card-hover transition-all duration-300 hover:border-yellow-400 group">
              <div className="w-12 h-12 rounded-xl bg-yellow-50 border border-yellow-200 flex items-center justify-center mb-5 text-yellow-600 group-hover:scale-110 transition-transform">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 font-display">Gold & Wealth</h3>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">Sovereign Gold Bonds, digital bullion, and bespoke private wealth advisory.</p>
              <div className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">1Y Avg Return</span>
                <span className="font-bold text-emerald-600 text-sm">+9.3%</span>
              </div>
              <button onClick={() => onNavigate('overview')} className="mt-3 text-xs font-semibold text-yellow-700 hover:text-yellow-900 flex items-center gap-1 group-hover:underline">
                Explore Commodities <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── 4. Impact Metric Banner (Dark Emerald) ────────────────── */}
      <section className="py-12 bg-emerald-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center">
            <div className="border-r border-emerald-800/80 last:border-none">
              <div className="text-3xl sm:text-4xl font-extrabold tracking-tight font-display">50K+</div>
              <div className="text-xs sm:text-sm text-emerald-200 mt-1 font-medium">Customers Served</div>
            </div>
            <div className="border-r border-emerald-800/80 last:border-none">
              <div className="text-3xl sm:text-4xl font-extrabold tracking-tight font-display">₹15,000 Cr+</div>
              <div className="text-xs sm:text-sm text-emerald-200 mt-1 font-medium">Assets Under Management</div>
            </div>
            <div className="border-r border-emerald-800/80 last:border-none">
              <div className="text-3xl sm:text-4xl font-extrabold tracking-tight font-display">25.4%</div>
              <div className="text-xs sm:text-sm text-emerald-200 mt-1 font-medium">Average Relationship Growth</div>
            </div>
            <div>
              <div className="text-3xl sm:text-4xl font-extrabold tracking-tight font-display">99.9%</div>
              <div className="text-xs sm:text-sm text-emerald-200 mt-1 font-medium">Data Integrity & Security</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 5. How Nexus360 Works (5-Step Horizontal Stepper) ─────── */}
      <section id="how-it-works" className="py-20 bg-slate-50 border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight font-display">How Nexus360 Works</h2>
            <p className="text-slate-600 mt-2 text-base">From fragmented business data to unified customer intelligence in 5 transparent steps.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 relative">
            {/* Step 1 */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-card transition-all">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm mb-4">
                01
              </div>
              <h3 className="font-bold text-slate-900 text-base">Ingest</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Connect incoming customer feeds across Banking, Equity, Mutual Funds, Insurance & Loans.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-card transition-all">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm mb-4">
                02
              </div>
              <h3 className="font-bold text-slate-900 text-base">Normalize</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Standardize PAN, 10-digit mobile, emails, city aliases, and generate 384-dim ML embeddings.
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-card transition-all">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm mb-4">
                03
              </div>
              <h3 className="font-bold text-slate-900 text-base">Resolve</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Evaluate deterministic rules, Jaro-Winkler distance, and cosine semantic similarities.
              </p>
            </div>

            {/* Step 4 */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-card transition-all">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm mb-4">
                04
              </div>
              <h3 className="font-bold text-slate-900 text-base">Unify</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Construct single Golden Customer records with source precedence and complete attribute lineage.
              </p>
            </div>

            {/* Step 5 */}
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-card transition-all">
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm mb-4">
                05
              </div>
              <h3 className="font-bold text-slate-900 text-base">Act</h3>
              <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                Surface Next-Best-Opportunity cross-sells, manage human review queue, and empower RMs.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── 6. Security & Enterprise Trust ───────────────────────── */}
      <section id="security" className="py-20 bg-white border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mb-12">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold uppercase tracking-wider mb-3">
              <Lock className="w-3.5 h-3.5 text-emerald-600" />
              Institutional Grade
            </div>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight font-display">Enterprise Security & Compliance</h2>
            <p className="text-slate-600 mt-2 text-base">Built to comply with strict financial data governance, KYC, and regulatory standards.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-50/50">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-4">
                <Shield className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Role-Based Access Control (RBAC)</h3>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">
                Granular permissions across 4 distinct operational roles: Administrator, Lead Reviewer, Relationship Manager, and Compliance Analyst.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-50/50">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-4">
                <EyeOff className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Sensitive PII Data Masking</h3>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">
                Automatic cryptographic masking for PAN (<span className="font-mono text-xs">ABCDE****F</span>), mobile numbers, emails, and DOBs on read-only views.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-50/50">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-4">
                <History className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Immutable Audit Trail</h3>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">
                Every login, ingestion run, auto-match, manual review approval, and BRE rule update is permanently logged with IP and actor identity.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── 7. Call To Action Banner ─────────────────────────────── */}
      <section className="py-16 bg-gradient-to-r from-navy-950 via-navy-900 to-navy-950 text-white border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-8">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight font-display">Ready to transform your customer relationships?</h2>
            <p className="text-slate-400 mt-2 text-sm sm:text-base">Experience the full power of Nexus360 with preloaded multi-asset financial test data.</p>
          </div>
          <button
            onClick={() => onNavigate('overview')}
            className="px-8 py-3.5 rounded-xl bg-emerald-500 text-white font-bold text-base hover:bg-emerald-600 transition-all shadow-md hover:shadow-emerald-glow shrink-0 flex items-center gap-2"
          >
            Launch Interactive Platform
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* ── 8. Footer ────────────────────────────────────────────── */}
      <footer className="py-8 bg-white border-t border-slate-200 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-emerald-600 flex items-center justify-center">
              <Compass className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-bold text-slate-800">Nexus360</span>
            <span>— Enterprise Customer Identity Resolution & Next-Best-Opportunity Platform</span>
          </div>
          <div className="flex items-center gap-6">
            <button onClick={() => onNavigate('login')} className="hover:text-emerald-700">Login Portal</button>
            <button onClick={() => onNavigate('overview')} className="hover:text-emerald-700">App Dashboard</button>
            <span>v0.1.0 (Hackathon Edition)</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
