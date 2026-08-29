import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { DashboardOverview } from './pages/DashboardOverview';
import { Customer360Page } from './pages/Customer360Page';
import { DataIngestionPage } from './pages/DataIngestionPage';
import { MatchingEnginePage } from './pages/MatchingEnginePage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { OpportunitiesPage } from './pages/OpportunitiesPage';
import { BusinessRulesPage } from './pages/BusinessRulesPage';
import { WhatIfSimulatorPage } from './pages/WhatIfSimulatorPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { MarketDashboardPage } from './pages/MarketDashboardPage';
import { IdentityVerificationCenter } from './pages/IdentityVerificationCenter';
import { IdentityGraphPage } from './pages/IdentityGraphPage';
import { Sidebar } from './components/common/Sidebar';
import { Topbar } from './components/common/Topbar';
import { NexusAIChat } from './components/NexusAIChat';

export default function App() {
  const { user } = useAuth();
  const [currentTab, setCurrentTab] = useState('landing');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Close mobile menu when navigating to a new tab
  const handleSelectTab = (tab) => {
    setCurrentTab(tab);
    setIsMobileMenuOpen(false);
  };

  // Handle keyboard shortcut '/' to jump to Customer 360 search
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === '/' && currentTab !== 'landing' && currentTab !== 'login') {
        e.preventDefault();
        setCurrentTab('customers');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentTab]);

  // If user logs out while in dashboard, route to landing
  useEffect(() => {
    if (!user && currentTab !== 'landing' && currentTab !== 'login') {
      setCurrentTab('landing');
    }
  }, [user, currentTab]);

  // Enforce role-based access to tabs
  useEffect(() => {
    if (user && currentTab !== 'landing' && currentTab !== 'login') {
      const role = user.role || 'ADMIN';
      const allowedRoles = {
        overview: ['ADMIN', 'REVIEWER', 'RELATIONSHIP_MANAGER', 'ANALYST'],
        customers: ['ADMIN', 'REVIEWER', 'RELATIONSHIP_MANAGER', 'ANALYST'],
        graph: ['ADMIN', 'REVIEWER', 'ANALYST'],
        matching: ['ADMIN'],
        reviews: ['ADMIN', 'REVIEWER'],
        verification: ['ADMIN', 'REVIEWER'],
        market: ['ADMIN', 'RELATIONSHIP_MANAGER'],
        opportunities: ['ADMIN', 'RELATIONSHIP_MANAGER'],
        ingestion: ['ADMIN'],
        config: ['ADMIN'],
        audit: ['ADMIN'],
        simulator: ['ADMIN', 'ANALYST']
      };
      
      const rolesForTab = allowedRoles[currentTab];
      if (rolesForTab && !rolesForTab.includes(role)) {
        setCurrentTab('overview');
      }
    }
  }, [user, currentTab]);

  // ── Render Landing Page ──────────────────────────────────────────
  if (currentTab === 'landing') {
    return <LandingPage onNavigate={setCurrentTab} />;
  }

  // ── Render Login Page ────────────────────────────────────────────
  if (currentTab === 'login') {
    return <LoginPage onNavigate={setCurrentTab} />;
  }

  // ── Main In-App Enterprise Layout ────────────────────────────────
  const pageTitles = {
    overview: { title: 'Executive Overview', subtitle: 'Portfolio KPIs and identity resolution pipeline summary' },
    customers: { title: 'Customer 360 Dossier', subtitle: 'Unified identity profile, multi-asset holdings & lineage graph' },
    graph: { title: 'Customer Identity Graph Network', subtitle: 'Interactive multi-source entity resolution topology & match evidence diagnostics' },
    ingestion: { title: 'Data Feed Ingestion', subtitle: 'CSV upload, synthetic seeding & data quality scorecard' },
    matching: { title: 'Identity Resolution Engine', subtitle: '7-stage candidate blocking, deterministic & semantic vector pipeline' },
    reviews: { title: 'Human-in-the-Loop Review Queue', subtitle: 'Split-screen side-by-side KYC review & manual attribute merge' },
    opportunities: { title: 'Next-Best-Opportunity Hub', subtitle: 'AI-driven cross-sell mandates for Relationship Managers' },
    market: { title: 'Market Intelligence & Portfolio Insights', subtitle: 'Live tracked instruments, price trend curves & client asset exposure alerts' },
    config: { title: 'Business Rules Engine (BRE)', subtitle: 'Source precedence hierarchy & matching threshold configuration' },
    verification: { title: 'Identity Verification Center', subtitle: 'Automated document verification and liveness checks' },
    simulator: { title: 'What-If Decision Simulator', subtitle: 'Safe threshold & feature weight impact projections' },
    audit: { title: 'Compliance & Audit Trail', subtitle: 'Immutable operations log for KYC operations and configuration changes' },
  };

  const currentHeader = pageTitles[currentTab] || { title: 'Nexus360 Portal', subtitle: '' };

  const renderActiveModule = () => {
    switch (currentTab) {
      case 'overview':
        return <DashboardOverview onNavigate={setCurrentTab} />;
      case 'customers':
        return <Customer360Page />;
      case 'graph':
        return <IdentityGraphPage onNavigate={setCurrentTab} />;
      case 'market':
        return <MarketDashboardPage onNavigate={setCurrentTab} />;
      case 'ingestion':
        return <DataIngestionPage onNavigate={setCurrentTab} />;
      case 'matching':
        return <MatchingEnginePage onNavigate={setCurrentTab} />;
      case 'reviews':
        return <ReviewQueuePage onNavigate={setCurrentTab} />;
      case 'opportunities':
        return <OpportunitiesPage onNavigate={setCurrentTab} />;
      case 'config':
        return <BusinessRulesPage />;
      case 'verification':
        return <IdentityVerificationCenter />;
      case 'simulator':
        return <WhatIfSimulatorPage />;
      case 'audit':
        return <AuditLogsPage />;
      default:
        return <DashboardOverview onNavigate={setCurrentTab} />;
    }
  };

  return (
    <div className="flex h-screen bg-slate-100 overflow-hidden font-sans selection:bg-emerald-100 selection:text-emerald-900">
      {/* Left Navigation Sidebar */}
      <Sidebar currentTab={currentTab} onSelectTab={handleSelectTab} isMobileMenuOpen={isMobileMenuOpen} setIsMobileMenuOpen={setIsMobileMenuOpen} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <Topbar
          title={currentHeader.title}
          subtitle={currentHeader.subtitle}
          onSearchClick={() => handleSelectTab('customers')}
          onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        />

        {/* Dynamic Page Module Container */}
        <main className="flex-1 overflow-y-auto bg-slate-50/70">
          {renderActiveModule()}
        </main>
      </div>

      {/* Reusable Nexus AI Institutional Assistant */}
      <NexusAIChat currentTab={currentTab} onNavigate={handleSelectTab} />
    </div>
  );
}
