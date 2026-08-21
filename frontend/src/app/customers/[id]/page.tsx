"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { User, ShieldCheck, Link2, Sparkles, AlertCircle, Briefcase, ArrowLeft, Database, TrendingUp, Shield } from "lucide-react";
import { AIExplanationDrawer } from "@/components/ui/AIExplanationDrawer";

const SYSTEM_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CORE_BANKING: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200" },
  CRM: { bg: "bg-green-50", text: "text-green-700", border: "border-green-200" },
  LOAN_ORIGINATION: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200" },
  INSURANCE: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200" },
  WEALTH: { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
};

const ALL_PRODUCTS = ["SAVINGS", "CURRENT", "FIXED_DEPOSIT", "HOME_LOAN", "AUTO_LOAN", "PERSONAL_LOAN", "SALARY_ACCOUNT", "Equity", "Mutual Fund", "TERM_LIFE", "Credit Card"];

function maskPan(pan: string | null) {
  if (!pan) return "—";
  return `${pan.slice(0, 5)}****${pan.slice(-1)}`;
}

function maskMobile(mobile: string | null) {
  if (!mobile) return "—";
  return `******${mobile.slice(-4)}`;
}

function maskEmail(email: string | null) {
  if (!email) return "—";
  const [user, domain] = email.split("@");
  return `${user.slice(0, 2)}****@${domain}`;
}

export default function Customer360Page() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerContext, setDrawerContext] = useState<"match" | "opportunity">("match");
  const [selectedOppId, setSelectedOppId] = useState<string | undefined>();

  const { data: customer, isLoading: loadingCustomer } = useQuery({
    queryKey: ["customer", id],
    queryFn: async () => {
      const res = await api.get(`/resolution/golden-records/${id}`);
      return res.data;
    }
  });

  const { data: opportunities, isLoading: loadingOpps } = useQuery({
    queryKey: ["opportunities", id],
    queryFn: async () => {
      try {
        const res = await api.get(`/opportunities/golden-record/${id}`);
        return res.data;
      } catch {
        return [];
      }
    }
  });

  const handleOpenExplanation = (type: "match" | "opportunity", oppId?: string) => {
    setDrawerContext(type);
    setSelectedOppId(oppId);
    setDrawerOpen(true);
  };

  if (loadingCustomer) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#E2604B]"></div>
      </div>
    );
  }

  if (!customer) {
    return <div className="text-center mt-20 text-gray-500">Customer not found.</div>;
  }

  // Collect all unique products from source records
  const heldProducts = new Set<string>();
  customer.source_records?.forEach((sr: any) => {
    (sr.products || []).forEach((p: string) => heldProducts.add(p));
  });

  const totalTRV = customer.total_relationship_value || 
    customer.source_records?.reduce((sum: number, sr: any) => sum + (sr.account_value || 0), 0) || 0;

  const confidence = customer.match_confidence || 0.95;

  return (
    <div className="flex flex-col gap-6">
      <AIExplanationDrawer 
        isOpen={drawerOpen} 
        onClose={() => setDrawerOpen(false)} 
        goldenId={id} 
        contextType={drawerContext}
        opportunityId={selectedOppId}
      />

      {/* Back + Title Bar */}
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="w-10 h-10 rounded-xl bg-white card-shadow flex items-center justify-center text-gray-500 hover:text-gray-900 transition-colors">
          <ArrowLeft size={18} />
        </button>
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Customer 360</p>
          <h1 className="text-xl font-bold text-gray-900">Golden Record #{id}</h1>
        </div>
      </div>

      {/* ─── Profile Header ─── */}
      <div className="bg-white p-8 rounded-3xl card-shadow relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-orange-50 via-orange-25 to-transparent rounded-full -mr-32 -mt-32 opacity-80"></div>
        
        <div className="flex justify-between items-start relative z-10">
          <div className="flex items-start gap-6">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-50 flex items-center justify-center text-gray-400 shadow-inner">
              <User size={36} />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-gray-900">{customer.name || "Unknown Customer"}</h2>
              <div className="flex items-center gap-3 mt-2 flex-wrap">
                <span className="text-sm text-gray-500 font-mono bg-gray-50 px-2 py-0.5 rounded">PAN: {maskPan(customer.pan)}</span>
                <span className="text-sm text-gray-500 font-mono bg-gray-50 px-2 py-0.5 rounded">📱 {maskMobile(customer.mobile)}</span>
                <span className="text-sm text-gray-500 font-mono bg-gray-50 px-2 py-0.5 rounded">✉️ {maskEmail(customer.email)}</span>
              </div>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-xs text-gray-500">📍 {customer.city || "—"}</span>
                <span className="text-xs font-semibold px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full">{customer.segment || "—"}</span>
              </div>
            </div>
          </div>
          
          {/* Match Confidence */}
          <div className="flex flex-col items-end gap-3">
            <div className="bg-green-50 border border-green-100 rounded-2xl p-4 min-w-[200px]">
              <div className="flex items-center gap-2 mb-2">
                <ShieldCheck size={16} className="text-green-600" />
                <span className="text-sm font-semibold text-green-800">Match Confidence</span>
              </div>
              <div className="w-full bg-green-200 rounded-full h-3 mb-1">
                <div className="bg-green-500 h-3 rounded-full transition-all duration-1000" style={{ width: `${confidence * 100}%` }}></div>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-green-600 font-bold">{(confidence * 100).toFixed(0)}%</span>
                <span className="text-green-500">Matched across {customer.source_records?.length || 0} systems</span>
              </div>
            </div>
            <button 
              onClick={() => handleOpenExplanation("match")}
              className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-600 font-semibold text-sm rounded-xl hover:bg-blue-100 transition-colors"
            >
              <Sparkles size={14} /> Explain Match Logic
            </button>
          </div>
        </div>
      </div>

      {/* ─── Source Lineage ─── */}
      <div className="bg-white p-6 rounded-3xl card-shadow">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <Database size={18} className="text-gray-400" />
            <h3 className="font-semibold text-gray-900">Source Lineage</h3>
          </div>
          <span className="text-xs font-medium text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
            {customer.source_records?.length || 0} Records Stitched
          </span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {customer.source_records?.map((record: any, idx: number) => {
            const colors = SYSTEM_COLORS[record.source_system] || SYSTEM_COLORS.CORE_BANKING;
            return (
              <div key={idx} className={`rounded-2xl border ${colors.border} p-4 ${colors.bg}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-xs font-bold px-2 py-1 rounded-lg ${colors.text} bg-white/70`}>
                    {record.source_system?.replace("_", " ")}
                  </span>
                  <span className="text-xs font-mono text-gray-500">{record.source_id}</span>
                </div>
                <div className="space-y-1.5 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Name</span>
                    <span className="font-medium text-gray-900 flex items-center gap-1">
                      {record.name || record.raw_name || "—"}
                      {record.name === customer.name ? 
                        <span className="text-green-500 text-xs">✓</span> : 
                        <span className="text-amber-500 text-xs">⚠️</span>
                      }
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Email</span>
                    <span className="font-mono text-xs text-gray-700">{maskEmail(record.email)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">City</span>
                    <span className="text-gray-700">{record.city || "—"}</span>
                  </div>
                  <div className="flex justify-between border-t border-white/50 pt-1.5 mt-1.5">
                    <span className="text-gray-500">Value</span>
                    <span className="font-bold text-gray-900">₹{(record.account_value || 0).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ─── Products & Value ─── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-3xl card-shadow col-span-1">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={18} className="text-gray-400" />
            <p className="text-sm font-semibold text-gray-500">Total Relationship Value</p>
          </div>
          <h3 className="text-4xl font-bold text-gray-900">₹{totalTRV.toLocaleString()}</h3>
          <p className="text-xs text-gray-400 mt-1">Aggregated across all source systems</p>
        </div>

        <div className="bg-white p-6 rounded-3xl card-shadow col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <Shield size={18} className="text-gray-400" />
            <p className="text-sm font-semibold text-gray-500">Products Held</p>
          </div>
          <div className="flex flex-wrap gap-3">
            {ALL_PRODUCTS.map(product => {
              const held = heldProducts.has(product);
              return (
                <div key={product} className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                  held 
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200" 
                    : "bg-gray-50 text-gray-300 border border-dashed border-gray-200"
                }`}>
                  {held ? "●" : "○"} {product.replace("_", " ")}
                </div>
              );
            })}
          </div>
          <p className="text-xs text-gray-400 mt-3">
            {ALL_PRODUCTS.length - heldProducts.size} products missing — potential cross-sell targets
          </p>
        </div>
      </div>

      {/* ─── Next Best Opportunities ─── */}
      <div className="bg-white p-6 rounded-3xl card-shadow">
        <div className="flex items-center gap-2 mb-6">
          <Briefcase size={18} className="text-[#E2604B]" />
          <h3 className="font-semibold text-gray-900">Next Best Opportunities</h3>
        </div>
        
        {loadingOpps ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#E2604B]"></div>
          </div>
        ) : opportunities?.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {opportunities.map((opp: any) => (
              <div key={opp.id} className="p-5 rounded-2xl border border-gray-100 hover:border-orange-200 transition-all group flex flex-col justify-between">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-orange-50 text-[#E2604B] flex items-center justify-center">
                      <Briefcase size={20} />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">{opp.product_name || opp.opportunity_type}</h4>
                      <div className="flex items-center gap-2 mt-1">
                        <div className="w-16 bg-gray-200 rounded-full h-1.5">
                          <div className="bg-[#E2604B] h-1.5 rounded-full" style={{ width: `${(opp.score || 0) * 100}%` }}></div>
                        </div>
                        <span className="text-xs text-gray-500 font-bold">{((opp.score || 0) * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                  <span className="text-xs font-bold px-2 py-1 bg-emerald-50 text-emerald-700 rounded">
                    Est. ₹{(opp.potential_value || 0).toLocaleString()}
                  </span>
                </div>
                
                {opp.explanation && (
                  <p className="text-xs text-gray-500 mt-3 italic bg-blue-50 p-2 rounded-lg">
                    💡 {opp.explanation}
                  </p>
                )}
                
                <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-50">
                  <button 
                    onClick={() => handleOpenExplanation("opportunity", opp.id)}
                    className="text-xs font-medium text-blue-600 flex items-center gap-1 hover:underline"
                  >
                    <Sparkles size={12} /> AI Logic
                  </button>
                  <button className="text-xs font-semibold text-white bg-[#E2604B] px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors">
                    Take Action
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-10 bg-gray-50 rounded-2xl border border-dashed border-gray-200">
            <AlertCircle className="mx-auto text-gray-400 mb-2" size={24} />
            <p className="text-sm font-medium text-gray-900">No active opportunities</p>
            <p className="text-xs text-gray-500 mt-1">This customer already holds all available products</p>
          </div>
        )}
      </div>
    </div>
  );
}
