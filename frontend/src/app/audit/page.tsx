"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { FileText, Clock, Search, Lock } from "lucide-react";
import { useState } from "react";
import { useAuthStore } from "@/stores/auth";

export default function AuditPage() {
  const [filter, setFilter] = useState("");
  const { user } = useAuthStore();

  const { data: auditData, isLoading } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: async () => {
      try {
        const res = await api.get("/audit/logs");
        return res.data;
      } catch {
        return { total: 0, logs: [] };
      }
    }
  });

  if (user?.role !== "ADMIN") {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-white rounded-3xl card-shadow p-12 text-center">
        <div className="w-16 h-16 bg-red-50 text-red-500 rounded-full flex items-center justify-center mb-6">
          <Lock size={32} />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Restricted</h2>
        <p className="text-gray-500 max-w-md">
          The Audit Logs are restricted to System Administrators. Your current role ({user?.role}) does not have permission to view system audit events.
        </p>
      </div>
    );
  }

  const logs = auditData?.logs || [];
  const filteredLogs = logs.filter((log: any) =>
    (log.action_type || "").toLowerCase().includes(filter.toLowerCase()) ||
    (log.description || "").toLowerCase().includes(filter.toLowerCase()) ||
    (log.actor_role || "").toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="bg-white p-6 rounded-3xl card-shadow flex justify-between items-center">
        <div className="flex items-center gap-3">
          <FileText size={24} className="text-[#E2604B]" />
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">Audit Trail</h2>
            <p className="text-gray-500 text-sm mt-0.5">
              {auditData?.total || 0} total events recorded
            </p>
          </div>
        </div>
        <div className="relative w-72">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="Filter by action or role..."
            className="w-full pl-10 pr-4 py-2.5 bg-gray-50 rounded-xl text-sm border-none focus:ring-2 focus:ring-[#E2604B]"
          />
        </div>
      </div>

      <div className="flex-1 bg-white rounded-3xl p-2 card-shadow overflow-y-auto">
        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#E2604B]"></div>
          </div>
        ) : (
          <table className="w-full text-left">
            <thead>
              <tr className="text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-gray-100">
                <th className="p-4 pl-6">Timestamp</th>
                <th className="p-4">Actor</th>
                <th className="p-4">Action</th>
                <th className="p-4">Entity</th>
                <th className="p-4">Description</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log: any) => (
                <tr key={log.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="p-4 pl-6 text-sm text-gray-500 font-mono">
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="text-gray-400" />
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : "—"}
                    </div>
                  </td>
                  <td className="p-4">
                    <span className="font-semibold text-gray-900 text-sm">{log.actor_role || "System"}</span>
                  </td>
                  <td className="p-4">
                    <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-bold">
                      {log.action_type || "—"}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-gray-500 font-mono">
                    {log.entity_type ? `${log.entity_type}#${log.entity_id || ""}` : "—"}
                  </td>
                  <td className="p-4 text-sm text-gray-600 max-w-xs truncate">
                    {log.description || "—"}
                  </td>
                </tr>
              ))}
              {filteredLogs.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-10 text-center text-gray-500">
                    No audit logs found. Events are recorded when you change config or run the pipeline.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
