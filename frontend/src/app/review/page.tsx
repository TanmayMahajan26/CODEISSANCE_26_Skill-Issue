"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useState } from "react";
import { CheckCircle, XCircle, Sparkles, AlertTriangle, ChevronDown, ChevronUp, Lock } from "lucide-react";
import { useAuthStore } from "@/stores/auth";

function maskPan(pan: string | null) {
  if (!pan) return "—";
  return `${pan.slice(0, 5)}****${pan.slice(-1)}`;
}

export default function ReviewPage() {
  const queryClient = useQueryClient();
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const { user } = useAuthStore();

  const { data: reviewData, isLoading } = useQuery({
    queryKey: ["review-queue"],
    queryFn: async () => {
      try {
        const res = await api.get("/review/queue");
        return res.data;
      } catch {
        return { items: [] };
      }
    }
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) => api.post(`/review/${id}/approve`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["review-queue"] }),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: number) => api.post(`/review/${id}/reject`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["review-queue"] }),
  });

  if (user?.role === "RM") {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-white rounded-3xl card-shadow p-12 text-center">
        <div className="w-16 h-16 bg-red-50 text-red-500 rounded-full flex items-center justify-center mb-6">
          <Lock size={32} />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Restricted</h2>
        <p className="text-gray-500 max-w-md">
          The Identity Review Queue is restricted to Managers and Administrators. RMs cannot manually approve or reject identity merges.
        </p>
      </div>
    );
  }

  const items = reviewData?.items || [];

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="bg-white p-6 rounded-3xl card-shadow flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Review Queue</h2>
          <p className="text-gray-500 text-sm mt-1">Low-confidence matches and conflicts requiring human review</p>
        </div>
        <span className="text-sm font-bold px-4 py-2 bg-amber-50 text-amber-700 rounded-xl">
          {items.filter((i: any) => i.status === "PENDING").length} Pending
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        {isLoading ? (
          <div className="flex justify-center items-center h-64 bg-white rounded-3xl card-shadow">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#E2604B]"></div>
          </div>
        ) : Array.isArray(items) && items.length > 0 ? (
          items.map((item: any) => (
            <div key={item.id} className="bg-white rounded-3xl card-shadow overflow-hidden">
              {/* Header */}
              <div 
                className="p-5 flex justify-between items-center cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${
                    (item.match_score?.total_score || 0) < 0.5 ? "bg-red-500" :
                    (item.match_score?.total_score || 0) < 0.7 ? "bg-amber-500" : "bg-blue-500"
                  }`}></div>
                  <div>
                    <p className="font-semibold text-gray-900">
                      {item.record_a?.name || "Unknown"} ↔ {item.record_b?.name || "Unknown"}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {item.record_a?.source_system} vs {item.record_b?.source_system} · Match Score: {((item.match_score?.total_score || 0) * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-bold px-3 py-1 rounded-full ${
                    item.status === "PENDING" ? "bg-amber-50 text-amber-700" :
                    item.status === "APPROVED" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
                  }`}>{item.status || "PENDING"}</span>
                  {expandedId === item.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
              </div>

              {/* Expanded details */}
              {expandedId === item.id && (
                <div className="border-t border-gray-100 p-5">
                  {/* Side-by-side comparison */}
                  <div className="grid grid-cols-2 gap-4 mb-5">
                    <div className="bg-blue-50 rounded-2xl p-4 border border-blue-100">
                      <p className="text-xs font-bold text-blue-700 mb-3">Record A — {item.record_a?.source_system}</p>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Name</span>
                          <span className="font-medium">{item.record_a?.name || "—"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">PAN</span>
                          <span className="font-mono text-xs">{maskPan(item.record_a?.pan)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Mobile</span>
                          <span className="font-mono text-xs">{item.record_a?.mobile ? `******${item.record_a.mobile.slice(-4)}` : "—"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Email</span>
                          <span className="font-mono text-xs">{item.record_a?.email || "—"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">City</span>
                          <span className="font-medium">{item.record_a?.city || "—"}</span>
                        </div>
                      </div>
                    </div>
                    <div className="bg-green-50 rounded-2xl p-4 border border-green-100">
                      <p className="text-xs font-bold text-green-700 mb-3">Record B — {item.record_b?.source_system}</p>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Name</span>
                          <span className="font-medium">{item.record_b?.name || "—"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">PAN</span>
                          <span className="font-mono text-xs">{maskPan(item.record_b?.pan)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Mobile</span>
                          <span className="font-mono text-xs">{item.record_b?.mobile ? `******${item.record_b.mobile.slice(-4)}` : "—"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Email</span>
                          <span className="font-mono text-xs">{item.record_b?.email || "—"}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">City</span>
                          <span className="font-medium">{item.record_b?.city || "—"}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Conflict Highlights */}
                  <div className="bg-amber-50 rounded-2xl p-4 border border-amber-100 mb-5">
                    <p className="text-xs font-bold text-amber-700 mb-2">⚠ Conflicts Detected</p>
                    <div className="space-y-1 text-sm text-amber-800">
                      {item.record_a?.name !== item.record_b?.name && (
                        <p>• Name mismatch: <strong>{item.record_a?.name}</strong> vs <strong>{item.record_b?.name}</strong></p>
                      )}
                      {item.record_a?.pan !== item.record_b?.pan && (
                        <p>• PAN differs between systems</p>
                      )}
                      {item.record_a?.city !== item.record_b?.city && (
                        <p>• City mismatch: <strong>{item.record_a?.city}</strong> vs <strong>{item.record_b?.city}</strong></p>
                      )}
                      {item.record_a?.email === item.record_b?.email && item.record_a?.email && (
                        <p>✓ Shared email: <strong>{item.record_a?.email}</strong></p>
                      )}
                      {item.record_a?.mobile === item.record_b?.mobile && item.record_a?.mobile && (
                        <p>✓ Shared mobile: <strong>******{item.record_a?.mobile?.slice(-4)}</strong></p>
                      )}
                    </div>
                  </div>

                  {/* AI Suggestion */}
                  <div className="bg-indigo-50 rounded-2xl p-4 border border-indigo-100 mb-5">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles size={14} className="text-indigo-600" />
                      <p className="text-xs font-bold text-indigo-700">AI Suggestion</p>
                    </div>
                    <p className="text-sm text-indigo-800">
                      {item.ai_suggestions || `These records share the same mobile number and email address but have different names and PANs. This could indicate a shared household account or a data entry error. Manual verification recommended before merging.`}
                    </p>
                  </div>

                  {/* Actions */}
                  {item.status === "PENDING" && (
                    <div className="flex gap-3">
                      <button
                        onClick={() => approveMutation.mutate(item.id)}
                        disabled={approveMutation.isPending}
                        className="flex-1 flex items-center justify-center gap-2 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors"
                      >
                        <CheckCircle size={18} /> Approve Merge
                      </button>
                      <button
                        onClick={() => rejectMutation.mutate(item.id)}
                        disabled={rejectMutation.isPending}
                        className="flex-1 flex items-center justify-center gap-2 py-3 bg-red-50 text-red-600 font-semibold rounded-xl hover:bg-red-100 transition-colors border border-red-200"
                      >
                        <XCircle size={18} /> Reject
                      </button>
                    </div>
                  )}
                  {item.status !== "PENDING" && (
                    <div className={`text-center py-3 rounded-xl text-sm font-semibold ${
                      item.status === "APPROVED" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
                    }`}>
                      {item.status === "APPROVED" ? "✓ Merge Approved" : "✕ Merge Rejected"}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="text-center py-20 bg-white rounded-3xl card-shadow flex flex-col items-center">
            <AlertTriangle className="text-gray-300 mb-4" size={48} />
            <h3 className="text-xl font-semibold text-gray-900">All Clear</h3>
            <p className="text-gray-500 mt-2">No items pending review at this time.</p>
          </div>
        )}
      </div>
    </div>
  );
}
