"use client";

import { X, Loader2, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface AIExplanationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  goldenId: string;
  contextType: "match" | "opportunity";
  opportunityId?: string;
}

export function AIExplanationDrawer({ isOpen, onClose, goldenId, contextType, opportunityId }: AIExplanationDrawerProps) {
  
  const { data, isLoading, error } = useQuery({
    queryKey: ["ai-explanation", goldenId, contextType, opportunityId],
    queryFn: async () => {
      let endpoint = `/ai/explain-match/${goldenId}`;
      if (contextType === "opportunity") {
        endpoint = `/ai/explain-opportunity/${opportunityId}`;
      }
      const res = await api.post(endpoint, {
        customer_context: "Explain in simple terms for the RM",
        include_source_lineage: true
      });
      return res.data;
    },
    enabled: isOpen,
  });

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
          />
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed top-0 right-0 h-full w-[450px] bg-white shadow-2xl z-50 flex flex-col"
          >
            <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
                  <Sparkles size={20} />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">AI Explanation</h3>
                  <p className="text-xs text-gray-500">
                    {contextType === "match" ? "Identity Resolution Reasoning" : "Opportunity Logic"}
                  </p>
                </div>
              </div>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-900 transition-colors p-2 rounded-full hover:bg-gray-100">
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {isLoading ? (
                <div className="flex flex-col items-center justify-center h-64 gap-4">
                  <Loader2 className="animate-spin text-[#E2604B]" size={32} />
                  <p className="text-sm text-gray-500 font-medium animate-pulse">Generating reasoning...</p>
                </div>
              ) : error ? (
                <div className="bg-red-50 p-4 rounded-2xl text-red-600 text-sm">
                  Failed to load explanation. Please try again later.
                </div>
              ) : (
                <div className="prose prose-sm prose-p:text-gray-600 prose-headings:text-gray-900 prose-headings:font-semibold">
                  {/* Basic markdown rendering since the response might be markdown */}
                  {data?.explanation?.split('\n').map((line: string, i: number) => {
                    if (line.startsWith('##')) return <h3 key={i} className="mt-4 mb-2">{line.replace('##', '')}</h3>;
                    if (line.startsWith('-')) return <li key={i} className="ml-4 mb-1 text-gray-600">{line.replace('-', '')}</li>;
                    if (line.trim() === '') return <br key={i} />;
                    return <p key={i} className="mb-2">{line}</p>;
                  })}
                  
                  {data?.confidence_score && (
                    <div className="mt-8 p-4 bg-gray-50 rounded-2xl border border-gray-100">
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">Engine Confidence</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {(data.confidence_score * 100).toFixed(1)}%
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
