import React, { useState, useEffect } from 'react';
import {
  History,
  Shield,
  Search,
  Filter,
  CheckCircle2,
  Calendar,
  User,
  Activity,
  ChevronDown,
  RefreshCw,
} from 'lucide-react';
import { getAuditLogs } from '../api';
import { formatDateTime } from '../utils/formatters';

export function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [actionFilter, setActionFilter] = useState('ALL');
  const [selectedLog, setSelectedLog] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await getAuditLogs(actionFilter !== 'ALL' ? { action: actionFilter } : {});
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter]);

  const getActionBadge = (act) => {
    switch (act) {
      case 'MERGE_APPROVE':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'MERGE_REJECT':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'MANUAL_MERGE':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'MATCHING_RUN':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'DATA_INGEST':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'CONFIG_CHANGE':
        return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  return (
    <div className="p-3 sm:p-5 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight font-display">Compliance & Audit Trail</h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Immutable system logs for KYC reviews, manual attribute overrides, configuration updates, and ingestion.
          </p>
        </div>

        <button
          onClick={fetchLogs}
          className="p-2.5 bg-white border border-slate-200 text-slate-600 hover:text-slate-900 rounded-xl hover:bg-slate-50 transition-all shadow-xs self-start sm:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* ── Table & Filter ───────────────────────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3 className="text-base font-bold text-slate-900 font-display">System Operations Log</h3>

          {/* Action Filter */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-500 font-medium">Filter Action:</span>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-50 border border-slate-300 rounded-xl font-bold text-slate-800 focus:ring-1 focus:ring-emerald-500"
            >
              <option value="ALL">ALL ACTIONS</option>
              <option value="LOGIN">LOGIN</option>
              <option value="MERGE_APPROVE">MERGE_APPROVE</option>
              <option value="MERGE_REJECT">MERGE_REJECT</option>
              <option value="MANUAL_MERGE">MANUAL_MERGE</option>
              <option value="DATA_INGEST">DATA_INGEST</option>
              <option value="MATCHING_RUN">MATCHING_RUN</option>
              <option value="CONFIG_CHANGE">CONFIG_CHANGE</option>
            </select>
          </div>
        </div>

        {/* Logs Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Target Entity</th>
                <th className="py-3 px-4">IP Address</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map((log) => (
                <tr
                  key={log.id}
                  onClick={() => setSelectedLog(selectedLog?.id === log.id ? null : log)}
                  className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                >
                  <td className="py-3 px-4 font-mono text-slate-600">
                    {formatDateTime(log.timestamp)}
                  </td>
                  <td className="py-3 px-4 font-bold text-slate-900">
                    {log.actor_username || 'system'}
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[10px]">
                      {log.actor_role || 'ADMIN'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded font-bold text-[10px] border ${getActionBadge(log.action)}`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-700">
                    {log.entity_type} {log.entity_id ? `(${log.entity_id})` : ''}
                  </td>
                  <td className="py-3 px-4 font-mono text-slate-500 text-[11px]">
                    {log.ip_address || '127.0.0.1'}
                  </td>
                  <td className="py-3 px-4 text-right text-emerald-700 font-semibold">
                    {selectedLog?.id === log.id ? 'Hide ▲' : 'Inspect ▼'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Selected Log JSON Details Drawer */}
        {selectedLog && (
          <div className="p-5 bg-slate-900 text-white rounded-2xl space-y-3 animate-fade-in text-xs font-mono">
            <div className="flex items-center justify-between text-slate-400 pb-2 border-b border-slate-800 text-[11px]">
              <span>Audit Entry #{selectedLog.id} Payload Inspection</span>
              <span>Action: {selectedLog.action}</span>
            </div>
            <pre className="text-emerald-400 overflow-x-auto text-[11px] leading-relaxed p-2 bg-slate-950/60 rounded-xl">
              {JSON.stringify(selectedLog.new_value || selectedLog, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
