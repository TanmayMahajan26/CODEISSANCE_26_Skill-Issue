"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Briefcase, Sparkles, AlertCircle } from "lucide-react";
import { useState } from "react";
import { AIExplanationDrawer } from "@/components/ui/AIExplanationDrawer";
import Link from "next/link";

export default function OpportunitiesPage() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedOpp, setSelectedOpp] = useState<any>(null);

  // In a real implementation we would fetch all active opportunities
  // Mocking endpoint if not fully available
  const { data: opportunities, isLoading } = useQuery({
    queryKey: ["all-opportunities"],
    queryFn: async () => {
      try {
        const res = await api.get("/opportunities");
        return res.data?.opportunities || [];
      } catch {
        return [];
      }
    }
  });

  const handleExplain = (opp: any) => {
    setSelectedOpp(opp);
    setDrawerOpen(true);
  };

  return (
    <div className="flex flex-col gap-6 h-full">
      <AIExplanationDrawer 
        isOpen={drawerOpen} 
        onClose={() => setDrawerOpen(false)} 
        goldenId={selectedOpp?.golden_record_id || ""}
        contextType="opportunity"
        opportunityId={selectedOpp?.id}
      />

      <div className="bg-white p-6 rounded-3xl card-shadow flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Next Best Opportunities</h2>
          <p className="text-gray-500 text-sm mt-1">AI-driven cross-sell recommendations</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex justify-center items-center h-64 bg-white rounded-3xl card-shadow">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#E2604B]"></div>
          </div>
        ) : opportunities?.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {opportunities.map((opp: any) => (
              <div key={opp.id} className="bg-white p-6 rounded-3xl card-shadow flex flex-col justify-between group hover:border-[#E2604B] border border-transparent transition-colors">
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <div className="w-12 h-12 rounded-full bg-orange-50 text-[#E2604B] flex items-center justify-center">
                      <Briefcase size={24} />
                    </div>
                    <span className="text-xs font-bold px-3 py-1 bg-green-50 text-green-700 rounded-full">
                      {((opp.score || 0) * 100).toFixed(0)}% Score
                    </span>
                  </div>
                  
                  <h3 className="font-semibold text-gray-900 text-lg mb-1">{opp.product_name || opp.opportunity_type}</h3>
                  <Link href={`/customers/${opp.golden_record_id}`} className="text-sm font-medium text-gray-500 hover:text-[#E2604B] transition-colors font-mono">
                    Customer: G-00{opp.golden_record_id}
                  </Link>
                  
                  <div className="mt-4 pt-4 border-t border-gray-50">
                    <p className="text-sm text-gray-600 line-clamp-2">{opp.explanation}</p>
                  </div>
                </div>
                
                <div className="flex justify-between items-center mt-6">
                  <button 
                    onClick={() => handleExplain(opp)}
                    className="flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                  >
                    <Sparkles size={16} /> AI Logic
                  </button>
                  <button className="accent-coral text-white text-sm font-semibold px-5 py-2 rounded-xl shadow hover:opacity-90 transition-opacity">
                    Action
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-20 bg-white rounded-3xl card-shadow flex flex-col items-center">
            <AlertCircle className="text-gray-300 mb-4" size={48} />
            <h3 className="text-xl font-semibold text-gray-900">No opportunities found</h3>
            <p className="text-gray-500 mt-2">The engine hasn't identified any cross-sell opportunities yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
