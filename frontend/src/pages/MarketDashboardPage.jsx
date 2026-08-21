import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  LineChart,
  Target,
  Users,
  ShieldCheck,
  AlertCircle,
  Briefcase,
  ExternalLink,
  ChevronRight,
  ArrowRight,
  Sparkles,
  Info,
} from 'lucide-react';
import { getMarketQuotes, getMarketTimeSeries, getMarketPortfolioContext } from '../api';
import { formatINR, formatNumber, formatPercent } from '../utils/formatters';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';

export function MarketDashboardPage({ onNavigate }) {
  const [quotes, setQuotes] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('TCS');
  const [timeRange, setTimeRange] = useState('1M');
  const [timeSeries, setTimeSeries] = useState(null);
  const [portfolioContext, setPortfolioContext] = useState(null);
  const [loadingQuotes, setLoadingQuotes] = useState(true);
  const [loadingChart, setLoadingChart] = useState(false);

  // Fetch quotes and portfolio context on mount
  const fetchMarketData = async () => {
    setLoadingQuotes(true);
    try {
      const [qData, ctxData] = await Promise.all([
        getMarketQuotes(),
        getMarketPortfolioContext(),
      ]);
      setQuotes(qData || []);
      setPortfolioContext(ctxData);
      if (qData && qData.length > 0 && !selectedSymbol) {
        setSelectedSymbol(qData[0].symbol);
      }
    } catch (err) {
      console.error('Failed to load market data:', err);
    } finally {
      setLoadingQuotes(false);
    }
  };

  // Fetch time series when symbol or range changes
  const fetchTimeSeriesData = async (sym, range) => {
    setLoadingChart(true);
    try {
      const ts = await getMarketTimeSeries(sym, range);
      setTimeSeries(ts);
    } catch (err) {
      console.error('Failed to load time series:', err);
    } finally {
      setLoadingChart(false);
    }
  };

  useEffect(() => {
    fetchMarketData();
  }, []);

  useEffect(() => {
    if (selectedSymbol) {
      fetchTimeSeriesData(selectedSymbol, timeRange);
    }
  }, [selectedSymbol, timeRange]);

  const activeQuote = quotes.find((q) => q.symbol === selectedSymbol) || quotes[0] || {
    symbol: 'TCS',
    name: 'Tata Consultancy Services',
    price: 3842.50,
    change: 42.30,
    change_percent: 1.11,
    is_positive: true,
    currency: 'INR',
  };

  return (
    <div className="p-6 sm:p-8 space-y-8 max-w-7xl mx-auto font-sans">
      {/* ── Page Header ──────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight font-display">Market Intelligence</h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Live market overview and portfolio context for Relationship Managers.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              fetchMarketData();
              fetchTimeSeriesData(selectedSymbol, timeRange);
            }}
            className="px-4 py-2 bg-white border border-slate-200 text-slate-700 hover:text-slate-900 rounded-xl hover:bg-slate-50 transition-all text-xs font-semibold shadow-xs flex items-center gap-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingQuotes ? 'animate-spin' : ''}`} />
            Refresh Quotes
          </button>
          <span className={`px-3 py-1 border text-[11px] font-bold rounded-lg flex items-center gap-1.5 ${
            quotes.some(q => q.source?.includes('Live'))
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-amber-50 border-amber-200 text-amber-800'
          }`}>
            <span className={`w-2 h-2 rounded-full ${quotes.some(q => q.source?.includes('Live')) ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
            {quotes.some(q => q.source?.includes('Live')) ? 'Alpha Vantage — Live' : 'Last Close Prices (API Rate Limit)'}
          </span>
        </div>
      </div>

      {/* ── SECTION 1 — MARKET SNAPSHOT (Cards) ──────────────────── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Tracked Equities & Benchmarks
          </h3>
          <span className="text-[11px] text-slate-400">Click any card to load price trend chart</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quotes.length > 0 ? (
            quotes.map((q) => {
              const isSelected = selectedSymbol === q.symbol;
              const isPositive = q.change >= 0;

              return (
                <div
                  key={q.symbol}
                  onClick={() => setSelectedSymbol(q.symbol)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all shadow-card hover:shadow-card-hover ${
                    isSelected
                      ? 'border-emerald-600 bg-emerald-50/50 ring-2 ring-emerald-500/20'
                      : 'border-slate-200 bg-white hover:bg-slate-50/80'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-mono font-bold text-slate-900 text-base">{q.symbol}</div>
                      <div className="text-[11px] text-slate-500 truncate max-w-[140px]">{q.name}</div>
                    </div>
                    <div className="flex flex-col items-end gap-0.5">
                      <span className="text-[10px] font-mono font-bold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                        {q.exchange || 'NSE'}
                      </span>
                      {q.source && q.source.includes('Live') && (
                        <span className="text-[9px] font-bold text-emerald-700 bg-emerald-50 px-1 py-0.5 rounded border border-emerald-200">LIVE</span>
                      )}
                    </div>
                  </div>

                  <div className="mt-3 flex items-baseline justify-between">
                    <div className="text-lg font-bold font-mono text-slate-900">
                      {q.currency === 'INR' ? `₹${q.price.toLocaleString('en-IN')}` : `$${q.price.toFixed(2)}`}
                    </div>

                    {q.change !== 0 ? (
                      <div className={`flex items-center gap-0.5 text-xs font-bold font-mono ${isPositive ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                        <span>{isPositive ? `+${q.change_percent}%` : `${q.change_percent}%`}</span>
                      </div>
                    ) : (
                      <span className="text-[11px] text-slate-400 font-mono">Last Close</span>
                    )}
                  </div>

                  <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                    <span>{q.volume && q.volume !== '—' ? `Vol: ${q.volume}` : q.source || ''}</span>
                    <span>{q.last_updated}</span>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="col-span-4 p-8 text-center bg-white rounded-2xl border border-slate-200 text-slate-400 text-xs">
              Loading tracked market quotes...
            </div>
          )}
        </div>
      </div>

      {/* ── SECTION 2 — PRICE TREND CHART ─────────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2.5">
              <h3 className="text-lg font-bold text-slate-900 font-display">
                {activeQuote.symbol} — {activeQuote.name}
              </h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700 font-mono">
                {activeQuote.exchange || 'NSE'}:{activeQuote.symbol}
              </span>
            </div>
            <div className="flex items-center gap-3 mt-1 text-xs">
              <span className="font-mono text-xl font-bold text-slate-900">
                {activeQuote.currency === 'INR' ? `₹${activeQuote.price.toLocaleString('en-IN')}` : `$${activeQuote.price.toFixed(2)}`}
              </span>
              <span className={`font-mono font-bold ${activeQuote.change >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                {activeQuote.change >= 0 ? `+${activeQuote.change}` : activeQuote.change} ({activeQuote.change_percent}%)
              </span>
              <span className="text-slate-400">• Sector: {activeQuote.sector || 'Financial / Tech'}</span>
            </div>
          </div>

          {/* Time Range Selector: 1D | 1W | 1M | 3M | 6M */}
          <div className="flex items-center p-1 bg-slate-100 rounded-xl gap-1">
            {['1D', '1W', '1M', '3M', '6M'].map((rng) => (
              <button
                key={rng}
                onClick={() => setTimeRange(rng)}
                className={`px-3 py-1 rounded-lg text-xs font-bold font-mono transition-all ${
                  timeRange === rng
                    ? 'bg-emerald-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                {rng}
              </button>
            ))}
          </div>
        </div>

        {/* Clean Line Chart Visualization */}
        <div className="space-y-3">
          <div className="h-56 w-full bg-slate-50 rounded-xl border border-slate-200/80 p-4 relative flex flex-col justify-between">
            {loadingChart ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-400 gap-2">
                <span className="w-4 h-4 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin" />
                Loading price history for {selectedSymbol}...
              </div>
            ) : timeSeries && timeSeries.data_points ? (
              <>
                {/* Header Metrics in Chart */}
                <div className="flex items-center justify-between text-xs text-slate-500 font-mono">
                  <span>High: ₹{timeSeries.high?.toLocaleString()}</span>
                  <span>Low: ₹{timeSeries.low?.toLocaleString()}</span>
                  <span>Period Net: <strong className={timeSeries.is_positive ? 'text-emerald-700' : 'text-rose-700'}>{timeSeries.period_change_percent}%</strong></span>
                </div>

                {/* Recharts Area Graph */}
                <div className="flex-1 w-full relative py-2" style={{ height: '144px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={timeSeries.data_points} margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#059669" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#059669" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="date" hide />
                      <YAxis domain={['dataMin', 'dataMax']} hide />
                      <Tooltip 
                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                        labelStyle={{ color: '#64748b', fontSize: '12px' }}
                        itemStyle={{ color: '#0f172a', fontWeight: 'bold', fontSize: '14px' }}
                        formatter={(value) => [`₹${value.toLocaleString()}`, 'Price']}
                      />
                      <Area type="monotone" dataKey="price" stroke="#059669" strokeWidth={2.5} fillOpacity={1} fill="url(#colorPrice)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* X-Axis Date Labels */}
                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono border-t border-slate-200 pt-1">
                  <span>{timeSeries.data_points[0]?.date}</span>
                  <span>{timeSeries.data_points[Math.floor(timeSeries.data_points.length / 2)]?.date}</span>
                  <span>{timeSeries.data_points[timeSeries.data_points.length - 1]?.date}</span>
                </div>
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">
                No time-series data available.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── SECTION 3 — CLIENT PORTFOLIO CONTEXT ──────────────────── */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 font-display">Client Portfolio Opportunities</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Relationship manager intelligence and client servicing alerts based on unified customer holdings.
            </p>
          </div>
          <button
            onClick={() => onNavigate('opportunities')}
            className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 flex items-center gap-1"
          >
            All Client Mandates <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Card 1: High Equity Exposure */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-1 rounded-md bg-blue-50 border border-blue-200 text-blue-800 text-[11px] font-bold">
                Asset Allocation
              </span>
              <Briefcase className="w-4 h-4 text-blue-600" />
            </div>

            <div>
              <div className="text-sm font-bold text-slate-900">High Equity Exposure</div>
              <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
                {portfolioContext?.high_equity_exposure_clients ?? 24} <span className="text-xs text-slate-500 font-normal">Clients</span>
              </div>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              Clients with &gt;80% allocation in Direct Demat Equities and no hedging or debt mutual fund instruments.
            </p>

            <button
              onClick={() => onNavigate('opportunities')}
              className="w-full py-2 bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5"
            >
              Recommend Debt & SIP Funds <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Card 2: Potential Diversification */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-1 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-bold">
                Cross-Sell Mandate
              </span>
              <Target className="w-4 h-4 text-emerald-600" />
            </div>

            <div>
              <div className="text-sm font-bold text-slate-900">Potential Diversification</div>
              <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
                {portfolioContext?.diversification_opportunities ?? 18} <span className="text-xs text-slate-500 font-normal">Clients</span>
              </div>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              Single-product customers eligible for Wealth PMS, Structured Credit, or Term Insurance coverage.
            </p>

            <button
              onClick={() => onNavigate('opportunities')}
              className="w-full py-2 bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5"
            >
              View Wealth Upgrades <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Card 3: Upcoming Reviews */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-card space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-1 rounded-md bg-amber-50 border border-amber-200 text-amber-800 text-[11px] font-bold">
                Relationship Review
              </span>
              <Users className="w-4 h-4 text-amber-600" />
            </div>

            <div>
              <div className="text-sm font-bold text-slate-900">Upcoming Portfolio Reviews</div>
              <div className="text-2xl font-bold font-mono text-slate-900 mt-1">
                {portfolioContext?.upcoming_portfolio_reviews ?? 12} <span className="text-xs text-slate-500 font-normal">Clients</span>
              </div>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              High-net-worth accounts requiring quarterly rebalancing or flagged with unresolved KYC address updates.
            </p>

            <button
              onClick={() => onNavigate('customers')}
              className="w-full py-2 bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5"
            >
              Open Client Dossiers <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
