"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { Play, CheckCircle, AlertCircle, RefreshCw } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

export function PipelineControlCard() {
  const queryClient = useQueryClient();
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const runPipeline = async () => {
    setIsRunning(true);
    setError(null);
    setResult(null);
    try {
      // Small timeout just to make it feel like an AI pipeline is running for the demo
      await new Promise(resolve => setTimeout(resolve, 800)); 
      const res = await api.post("/resolution/run");
      setResult(res.data);
      // Invalidate queries to refresh dashboard and other components
      queryClient.invalidateQueries();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to run pipeline");
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="bg-gradient-to-br from-blue-900 to-indigo-900 rounded-3xl p-6 shadow-xl flex flex-col justify-between text-white relative overflow-hidden h-full">
      <div className="absolute -top-10 -right-10 w-40 h-40 bg-white opacity-10 rounded-full blur-2xl"></div>
      
      <div>
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-semibold text-lg z-10 relative">Kovi Pipeline</h3>
          {isRunning && <RefreshCw size={18} className="animate-spin text-blue-200" />}
        </div>
        <p className="text-blue-200 text-sm mb-6 z-10 relative">
          Stitch 360 profiles across Source Systems, resolve identities, and compute Next-Best-Opportunities.
        </p>
      </div>

      <div className="z-10 relative">
        {result ? (
          <div className="bg-white/10 p-4 rounded-2xl backdrop-blur-md mb-4 border border-white/20">
            <p className="text-sm font-semibold flex items-center gap-2 mb-2 text-green-300">
              <CheckCircle size={16} /> Pipeline Complete!
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-black/20 p-2 rounded-lg">
                <span className="block text-blue-200">Stitched</span>
                <span className="font-bold text-lg">{result.metrics?.golden_records_created || 0}</span>
              </div>
              <div className="bg-black/20 p-2 rounded-lg">
                <span className="block text-blue-200">Opportunities</span>
                <span className="font-bold text-lg">{result.metrics?.opportunities_created || 0}</span>
              </div>
            </div>
          </div>
        ) : error ? (
          <div className="bg-red-500/20 p-3 rounded-xl mb-4 border border-red-500/30 text-red-100 text-sm flex items-center gap-2">
            <AlertCircle size={16} /> {error}
          </div>
        ) : null}

        <button 
          onClick={runPipeline} 
          disabled={isRunning}
          className={`w-full py-3 rounded-xl font-bold flex justify-center items-center gap-2 transition-all shadow-lg
            ${isRunning ? "bg-indigo-800 text-indigo-300 cursor-not-allowed" : "bg-white text-indigo-900 hover:bg-gray-100"}`}
        >
          {isRunning ? "Resolving Identities..." : <><Play size={18} fill="currentColor" /> Run Resolution Engine</>}
        </button>
      </div>
    </div>
  );
}
