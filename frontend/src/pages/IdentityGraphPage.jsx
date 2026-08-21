import React, { useState, useEffect, useRef, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import {
  Search,
  Filter,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  Share2,
  User,
  Layers,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  X,
  ChevronRight,
  Sparkles,
  Database,
  Building2,
  CreditCard,
  TrendingUp,
  PieChart,
  Briefcase,
  Eye,
  EyeOff,
  ExternalLink,
  Info,
  Check,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { getIdentityGraphAll } from '../api';
import { formatINR, formatPercent, maskPAN, maskMobile } from '../utils/formatters';

export function IdentityGraphPage({ onNavigate, initialCustomerSearch = '' }) {
  const { user } = useAuth();
  const role = user?.role || 'ADMIN';
  const isAnalyst = role === 'ANALYST';

  const [loading, setLoading] = useState(true);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [searchQuery, setSearchQuery] = useState(initialCustomerSearch);
  const [selectedSystem, setSelectedSystem] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');

  const [selectedNode, setSelectedNode] = useState(null);
  const fgRef = useRef();

  // System Legend & Styles
  const systemColors = {
    GOLDEN: { bg: '#059669', label: 'Golden Master Profile' },
    EQUITY: { bg: '#2563eb', label: 'Equity Broking' },
    MUTUAL_FUND: { bg: '#9333ea', label: 'Mutual Funds' },
    WEALTH: { bg: '#0d9488', label: 'Wealth Management' },
    INSURANCE: { bg: '#d97706', label: 'Insurance Policies' },
    LOAN: { bg: '#e11d48', label: 'Lending & Loans' },
    CORE_BANKING: { bg: '#4f46e5', label: 'Core Banking' },
    DEFAULT: { bg: '#475569', label: 'Source Record' },
  };

  const fetchGraph = async () => {
    setLoading(true);
    try {
      const data = await getIdentityGraphAll({
        search: searchQuery,
        source_system: selectedSystem,
        status_filter: selectedStatus,
      });

      if (data && data.nodes) {
        // Map edges to links for react-force-graph
        const links = (data.edges || []).map(e => ({
          ...e,
          source: typeof e.source === 'object' ? e.source.id : e.source,
          target: typeof e.target === 'object' ? e.target.id : e.target,
        }));
        setGraphData({ nodes: data.nodes, links });
      }
    } catch (err) {
      console.error('Failed to load identity graph:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [selectedSystem, selectedStatus]);

  const handleSearchSubmit = (e) => {
    if (e) e.preventDefault();
    fetchGraph();
  };

  // Node drawing
  const drawNode = (node, ctx, globalScale) => {
    const isGolden = node.type === 'GOLDEN';
    const sysConfig = systemColors[node.source_system] || (isGolden ? systemColors.GOLDEN : systemColors.DEFAULT);
    const radius = isGolden ? 12 : 8;

    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
    ctx.fillStyle = sysConfig.bg;
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = selectedNode?.id === node.id ? 2 : 1;
    ctx.stroke();

    const label = isAnalyst && !isGolden ? `${node.source_system} Feed` : node.label;
    const fontSize = isGolden ? 14 / globalScale : 10 / globalScale;
    ctx.font = `${fontSize}px Sans-Serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#1e293b';
    ctx.fillText(label, node.x, node.y + radius + 4 + fontSize/2);
  };

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 1000);
      fgRef.current.zoom(2, 1000);
    }
  };

  const handleFitScreen = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400);
    }
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 select-none overflow-hidden">
      {/* ── Top Header & Filter Toolbar ──────────────────────────────── */}
      <div className="px-6 py-4 bg-white border-b border-slate-200 shadow-xs space-y-3 shrink-0">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-xl font-bold text-slate-900 font-display tracking-tight">
                Customer Identity Resolution Graph
              </h2>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold border border-emerald-300 font-mono">
                Interactive Map
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Visualizes connections between sources and Golden Master profiles.
            </p>
          </div>

          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
            <div className="relative w-64 sm:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search name, PAN, or Golden ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-medium shadow-xs"
              />
            </div>
            <button
              type="submit"
              className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs transition-all shadow-xs"
            >
              Focus Node
            </button>
          </form>
        </div>

        {/* Filter Row */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-100 text-xs">
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-xl">
              <span className="text-[10px] uppercase font-bold text-slate-400 px-2">Feeder System:</span>
              {['ALL', 'EQUITY', 'MUTUAL_FUND', 'WEALTH', 'INSURANCE', 'LOAN'].map((sys) => (
                <button
                  key={sys}
                  onClick={() => setSelectedSystem(sys)}
                  className={`px-2.5 py-1 rounded-lg font-bold text-[11px] transition-all ${
                    selectedSystem === sys
                      ? 'bg-white text-slate-900 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {sys === 'ALL' ? 'All Systems' : sys.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>
          
          <div className="flex items-center gap-2 overflow-x-auto text-[10px] font-semibold text-slate-600">
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{backgroundColor: systemColors.GOLDEN.bg}} />Golden Master</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{backgroundColor: systemColors.EQUITY.bg}} />Equity</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{backgroundColor: systemColors.MUTUAL_FUND.bg}} />Mutual Funds</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{backgroundColor: systemColors.INSURANCE.bg}} />Insurance</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{backgroundColor: systemColors.LOAN.bg}} />Loans</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full" style={{backgroundColor: systemColors.WEALTH.bg}} />Wealth</span>
          </div>
        </div>
      </div>

      {/* ── Main Graph Body Area ────────────────────────────────────── */}
      <div className="relative flex-1 bg-slate-100 overflow-hidden cursor-grab active:cursor-grabbing">
        
        {/* Controls */}
        <div className="absolute top-4 left-4 z-20 bg-white border border-slate-200 rounded-xl shadow-md p-1.5 flex flex-col gap-1">
          <button
            onClick={() => fgRef.current?.zoom(fgRef.current.zoom() * 1.2, 400)}
            title="Zoom In"
            className="p-2 hover:bg-slate-100 text-slate-700 rounded-lg transition-colors"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => fgRef.current?.zoom(fgRef.current.zoom() * 0.8, 400)}
            title="Zoom Out"
            className="p-2 hover:bg-slate-100 text-slate-700 rounded-lg transition-colors"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleFitScreen}
            title="Fit to Screen"
            className="p-2 hover:bg-slate-100 text-slate-700 rounded-lg transition-colors border-t border-slate-100"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>

        {/* Force Graph */}
        <div className="w-full h-full">
          <ForceGraph2D
            ref={fgRef}
            graphData={graphData}
            nodeLabel={() => ''}
            nodeCanvasObject={drawNode}
            onNodeClick={handleNodeClick}
            linkColor={(link) => {
              if (link.status === 'CONFLICT') return '#e11d48';
              if (link.status === 'REVIEW') return '#d97706';
              return '#94a3b8';
            }}
            linkLineDash={(link) => link.status === 'CONFLICT' ? [4,4] : link.status === 'REVIEW' ? [6,4] : null}
            linkWidth={(link) => (link.confidence && link.confidence > 0.8) ? 2 : 1}
          />
        </div>
      </div>

      {/* ── Right-Side Detail Drawer (Node Clicked) ────────────────── */}
      {selectedNode && (
        <div className="fixed inset-y-0 right-0 z-40 w-full sm:w-96 bg-white border-l border-slate-200 shadow-2xl flex flex-col animate-slide-left">
          {/* Drawer Header */}
          <div className="p-6 bg-slate-900 text-white flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-800 font-mono">
                  {selectedNode.id}
                </span>
                <span className="text-xs text-slate-400 font-semibold">
                  {selectedNode.type === 'GOLDEN' ? 'Golden Master Profile' : selectedNode.source_system}
                </span>
              </div>
              <h3 className="text-lg font-bold text-white font-display mt-1 truncate">
                {isAnalyst && selectedNode.type === 'SOURCE'
                  ? 'Source Feeder Record'
                  : selectedNode.label}
              </h3>
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Content */}
          <div className="p-6 space-y-6 flex-1 overflow-y-auto text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">
                  {selectedNode.type === 'GOLDEN' ? 'Relationship Value' : 'Feeder AUM'}
                </span>
                <div className="text-base font-extrabold text-emerald-700 font-mono mt-0.5">
                  {formatINR(selectedNode.total_relationship_value || selectedNode.balance_aum || 0)}
                </div>
              </div>

              <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-[10px] font-bold text-slate-400 uppercase">
                  {selectedNode.type === 'GOLDEN' ? 'Linked Feeds' : 'Match Method'}
                </span>
                <div className="text-sm font-bold text-slate-900 font-mono mt-0.5">
                  {selectedNode.type === 'GOLDEN'
                    ? `${selectedNode.source_count || 1} Feeder Accounts`
                    : 'Deterministic PAN'}
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Entity Identification Attributes
              </div>
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2.5 font-mono">
                <div className="flex items-center justify-between pb-2 border-b border-slate-200/80">
                  <span className="text-slate-500 font-sans">Full Name:</span>
                  <span className="font-bold text-slate-900">
                    {selectedNode.canonical_name || selectedNode.original_name || 'N/A'}
                  </span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-slate-200/80">
                  <span className="text-slate-500 font-sans">PAN Card:</span>
                  <span className="font-bold text-slate-900">
                    {isAnalyst
                      ? maskPAN(selectedNode.canonical_pan || selectedNode.original_pan)
                      : selectedNode.canonical_pan || selectedNode.original_pan || 'N/A'}
                  </span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-slate-200/80">
                  <span className="text-slate-500 font-sans">Mobile:</span>
                  <span className="font-bold text-slate-900">
                    {isAnalyst
                      ? maskMobile(selectedNode.canonical_mobile || selectedNode.original_mobile)
                      : selectedNode.canonical_mobile || selectedNode.original_mobile || 'N/A'}
                  </span>
                </div>
                <div className="flex items-center justify-between pb-2 border-b border-slate-200/80">
                  <span className="text-slate-500 font-sans">Email:</span>
                  <span className="font-bold text-slate-900 truncate max-w-[180px]">
                    {selectedNode.canonical_email || selectedNode.original_email || 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {selectedNode.type === 'GOLDEN' && (
              <button
                onClick={() => {
                  setSelectedNode(null);
                  if (onNavigate) onNavigate('customers');
                }}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-subtle flex items-center justify-center gap-2 text-xs transition-all"
              >
                Open Full Customer 360 Dossier
                <ExternalLink className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
