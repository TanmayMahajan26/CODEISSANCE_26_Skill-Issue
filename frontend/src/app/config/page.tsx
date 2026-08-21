"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Settings, Save, RefreshCw, Play, AlertTriangle, CheckCircle, Lock } from "lucide-react";
import { useAuthStore } from "@/stores/auth";

const TABS = ["Matching Weights", "Thresholds", "Opportunity Rules", "Source Precedence"];

const DEFAULT_WEIGHTS: Record<string, number> = {
  pan: 0.35, mobile: 0.20, email: 0.15, name_jaro: 0.12, name_semantic: 0.08, dob: 0.05, city: 0.03, segment: 0.02
};

const DEFAULT_THRESHOLDS = { auto_merge: 0.85, manual_review: 0.60 };

export default function ConfigPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [weights, setWeights] = useState(DEFAULT_WEIGHTS);
  const [thresholds, setThresholds] = useState(DEFAULT_THRESHOLDS);
  const [pipelineResult, setPipelineResult] = useState<any>(null);
  const queryClient = useQueryClient();
  const { user } = useAuthStore();

  const { data: rulesData } = useQuery({
    queryKey: ["config-rules-all"],
    queryFn: async () => {
      try {
        const res = await api.get("/config/rules");
        return res.data;
      } catch { return { rules: [] }; }
    }
  });

  useEffect(() => {
    if (rulesData?.rules) {
      const matchRule = rulesData.rules.find((r: any) => r.rule_type === "matching_thresholds");
      if (matchRule?.config) {
        setThresholds({
          auto_merge: matchRule.config.auto_merge || 0.85,
          manual_review: matchRule.config.manual_review || 0.60,
        });
      }
    }
  }, [rulesData]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      await api.put("/config/rules/matching_thresholds", {
        config: thresholds,
        description: `Updated thresholds: auto_merge=${thresholds.auto_merge}, manual_review=${thresholds.manual_review}`
      });
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["config-rules-all"] }),
  });

  const pipelineMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post("/resolution/run");
      return res.data;
    },
    onSuccess: (data) => {
      setPipelineResult(data);
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  if (user?.role !== "ADMIN") {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-white rounded-3xl card-shadow p-12 text-center">
        <div className="w-16 h-16 bg-red-50 text-red-500 rounded-full flex items-center justify-center mb-6">
          <Lock size={32} />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Restricted</h2>
        <p className="text-gray-500 max-w-md">
          The Configuration Console is restricted to System Administrators. Your current role ({user?.role}) does not have permission to modify business rules or run the resolution pipeline.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 h-full">
      {/* Header */}
      <div className="bg-white p-6 rounded-3xl card-shadow flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Settings size={24} className="text-[#E2604B]" />
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">Configuration Console</h2>
            <p className="text-gray-500 text-sm mt-0.5">Adjust matching rules and thresholds — changes take effect on next pipeline run</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending}
            className="flex items-center gap-2 px-5 py-2.5 bg-white border border-gray-200 rounded-xl font-semibold text-sm hover:bg-gray-50 transition-colors"
          >
            {saveMutation.isPending ? <RefreshCw size={16} className="animate-spin" /> : <Save size={16} />}
            {saveMutation.isSuccess ? "Saved!" : "Save Config"}
          </button>
          <button 
            onClick={() => pipelineMutation.mutate()}
            disabled={pipelineMutation.isPending}
            className="flex items-center gap-2 px-5 py-2.5 accent-coral text-white rounded-xl font-semibold text-sm shadow-lg hover:opacity-90 transition-opacity"
          >
            {pipelineMutation.isPending ? <RefreshCw size={16} className="animate-spin" /> : <Play size={16} />}
            Apply & Re-run Pipeline
          </button>
        </div>
      </div>

      {/* Pipeline Result Banner */}
      {pipelineResult && (
        <div className="bg-green-50 border border-green-200 rounded-2xl p-4 flex items-center gap-4">
          <CheckCircle className="text-green-600 shrink-0" size={20} />
          <div className="flex-1">
            <p className="text-sm font-semibold text-green-800">Pipeline completed successfully</p>
            <p className="text-xs text-green-600 mt-0.5">
              {pipelineResult.metrics?.golden_records_created || 0} golden records created · {pipelineResult.metrics?.opportunities_created || 0} opportunities generated · {pipelineResult.metrics?.edges_created?.total || 0} identity edges found
            </p>
          </div>
          <button onClick={() => setPipelineResult(null)} className="text-green-400 hover:text-green-600">✕</button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-2xl w-fit">
        {TABS.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(i)}
            className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all ${
              activeTab === i ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 bg-white rounded-3xl card-shadow p-8 overflow-y-auto">
        {activeTab === 0 && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-lg font-semibold text-gray-900">Matching Attribute Weights</h3>
              <span className="text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded-full">Must sum to 1.0</span>
            </div>
            <p className="text-sm text-gray-500 mb-6">
              Configure the relative importance of each attribute during probabilistic identity resolution. Higher weight = more influence on match confidence.
            </p>
            <div className="space-y-5">
              {Object.entries(weights).map(([key, value]) => (
                <div key={key} className="flex items-center gap-6">
                  <span className="w-36 text-sm font-semibold text-gray-700 capitalize">{key.replace("_", " ")}</span>
                  <div className="flex-1">
                    <input 
                      type="range" min="0" max="0.5" step="0.01" value={value}
                      onChange={e => setWeights(prev => ({ ...prev, [key]: parseFloat(e.target.value) }))}
                      className="w-full accent-[#E2604B]"
                    />
                  </div>
                  <span className="w-16 text-right text-sm font-bold text-[#E2604B]">{(value * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs text-gray-400">
                Current sum: <span className={`font-bold ${Math.abs(Object.values(weights).reduce((a, b) => a + b, 0) - 1) < 0.01 ? "text-green-600" : "text-red-500"}`}>
                  {(Object.values(weights).reduce((a, b) => a + b, 0) * 100).toFixed(0)}%
                </span>
              </p>
            </div>
          </div>
        )}

        {activeTab === 1 && (
          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">Decision Thresholds</h3>
              <p className="text-sm text-gray-500 mb-6">
                Control when matches are automatically merged vs. sent for human review. Lowering auto-merge catches more matches but may increase false positives.
              </p>
            </div>

            <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100">
              <div className="flex justify-between items-center mb-3">
                <div>
                  <p className="text-sm font-semibold text-gray-700">Auto-Merge Threshold</p>
                  <p className="text-xs text-gray-500 mt-0.5">Records above this score merge automatically</p>
                </div>
                <span className="text-2xl font-bold text-[#E2604B]">{(thresholds.auto_merge * 100).toFixed(0)}%</span>
              </div>
              <input 
                type="range" min="0.50" max="0.99" step="0.01" value={thresholds.auto_merge}
                onChange={e => setThresholds(prev => ({ ...prev, auto_merge: parseFloat(e.target.value) }))}
                className="w-full accent-[#E2604B]"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>50% (Aggressive)</span>
                <span>99% (Conservative)</span>
              </div>
            </div>

            <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100">
              <div className="flex justify-between items-center mb-3">
                <div>
                  <p className="text-sm font-semibold text-gray-700">Manual Review Threshold</p>
                  <p className="text-xs text-gray-500 mt-0.5">Records between this and auto-merge go to review queue</p>
                </div>
                <span className="text-2xl font-bold text-amber-600">{(thresholds.manual_review * 100).toFixed(0)}%</span>
              </div>
              <input 
                type="range" min="0.30" max="0.90" step="0.01" value={thresholds.manual_review}
                onChange={e => setThresholds(prev => ({ ...prev, manual_review: parseFloat(e.target.value) }))}
                className="w-full accent-amber-500"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>30%</span>
                <span>90%</span>
              </div>
            </div>

            {/* Impact Preview */}
            <div className="bg-blue-50 rounded-2xl p-5 border border-blue-100">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={16} className="text-blue-600" />
                <h4 className="text-sm font-semibold text-blue-900">Impact Preview</h4>
              </div>
              <p className="text-sm text-blue-700">
                With auto-merge at <strong>{(thresholds.auto_merge * 100).toFixed(0)}%</strong> and review threshold at <strong>{(thresholds.manual_review * 100).toFixed(0)}%</strong>:
              </p>
              <ul className="text-sm text-blue-600 mt-2 space-y-1 list-disc list-inside">
                <li>Scores ≥ {(thresholds.auto_merge * 100).toFixed(0)}% → <strong>Auto-merge</strong></li>
                <li>Scores {(thresholds.manual_review * 100).toFixed(0)}%–{(thresholds.auto_merge * 100).toFixed(0)}% → <strong>Review queue</strong></li>
                <li>Scores &lt; {(thresholds.manual_review * 100).toFixed(0)}% → <strong>No match</strong></li>
              </ul>
            </div>
          </div>
        )}

        {activeTab === 2 && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Opportunity Generation Rules</h3>
            <p className="text-sm text-gray-500 mb-4">
              Define eligibility criteria for cross-sell opportunity generation. These rules determine which products are recommended to each golden record.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {["Insurance Cross-Sell", "Wealth Management Upsell", "Personal Loan", "Credit Card"].map(product => (
                <div key={product} className="bg-gray-50 rounded-2xl p-5 border border-gray-100">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="font-semibold text-gray-900">{product}</h4>
                    <span className="text-xs font-bold px-2 py-1 bg-green-50 text-green-700 rounded-full">Active</span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Min TRV</span>
                      <span className="font-medium">₹1,00,000</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Min Tenure</span>
                      <span className="font-medium">6 months</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Required Products</span>
                      <span className="font-medium">Any existing</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 3 && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Source System Precedence</h3>
            <p className="text-sm text-gray-500 mb-4">
              When attributes conflict between source systems, precedence determines which system's value wins for the golden record (survivorship rules).
            </p>
            <div className="space-y-3">
              {[
                { sys: "WEALTH", priority: 1, color: "bg-purple-50 border-purple-200 text-purple-700" },
                { sys: "INSURANCE", priority: 2, color: "bg-red-50 border-red-200 text-red-700" },
                { sys: "CORE_BANKING", priority: 3, color: "bg-blue-50 border-blue-200 text-blue-700" },
                { sys: "LOAN_ORIGINATION", priority: 4, color: "bg-amber-50 border-amber-200 text-amber-700" },
                { sys: "CRM", priority: 5, color: "bg-green-50 border-green-200 text-green-700" },
              ].map(({ sys, priority, color }) => (
                <div key={sys} className={`flex items-center justify-between p-4 rounded-2xl border ${color}`}>
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-full bg-white flex items-center justify-center text-sm font-bold shadow-sm">{priority}</span>
                    <span className="font-semibold">{sys.replace("_", " ")}</span>
                  </div>
                  <span className="text-xs font-medium">Priority {priority}</span>
                </div>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-2">Drag to reorder (coming soon). Higher priority systems win during attribute conflicts.</p>
          </div>
        )}
      </div>
    </div>
  );
}
