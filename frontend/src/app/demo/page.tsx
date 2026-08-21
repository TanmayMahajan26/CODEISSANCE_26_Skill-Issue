"use client";

import { useState, useRef } from "react";
import { useAuthStore } from "@/stores/auth";
import { Lock, UploadCloud, Play, CheckCircle, Database, Users, Link2, AlertTriangle, FileText, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export default function DemoPage() {
  const { user } = useAuthStore();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [pipelineState, setPipelineState] = useState<"IDLE" | "UPLOADING" | "PROCESSING" | "DONE">("IDLE");
  const [result, setResult] = useState<any>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const processMutation = useMutation({
    mutationFn: async (uploadFile: File) => {
      const formData = new FormData();
      formData.append("file", uploadFile);
      const res = await api.post("/demo/upload_and_process", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      return res.data;
    },
    onSuccess: (data) => {
      setPipelineState("DONE");
      setResult(data);
      queryClient.invalidateQueries();
    },
    onError: (err) => {
      console.error(err);
      setPipelineState("IDLE");
      alert("Failed to process file.");
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
          The Demo Environment is restricted to System Administrators.
        </p>
      </div>
    );
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleProcess = () => {
    if (!file) return;
    setPipelineState("PROCESSING");
    // Simulate pipeline delay
    setTimeout(() => {
      processMutation.mutate(file);
    }, 2000);
  };

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto w-full">
      <div className="bg-gradient-to-r from-gray-900 to-indigo-900 p-8 rounded-3xl text-white relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500 opacity-20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
        <div className="relative z-10">
          <h2 className="text-3xl font-bold">Identity Resolution Engine Demo</h2>
          <p className="text-indigo-200 mt-2 text-sm max-w-xl">
            Upload a CSV containing raw customer records. Watch the AI engine automatically parse, match, and resolve identities using deterministic, probabilistic, and semantic models.
          </p>
        </div>
      </div>

      {pipelineState === "IDLE" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div 
            className={`border-2 border-dashed rounded-3xl p-12 flex flex-col items-center justify-center text-center transition-colors cursor-pointer bg-white
              ${isDragging ? "border-indigo-500 bg-indigo-50" : "border-gray-200 hover:border-indigo-400"}`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input type="file" ref={fileInputRef} className="hidden" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <UploadCloud size={48} className={`mb-4 ${file ? "text-indigo-500" : "text-gray-300"}`} />
            <h3 className="text-lg font-bold text-gray-900 mb-1">{file ? file.name : "Upload Raw Data (CSV)"}</h3>
            <p className="text-sm text-gray-500">{file ? "Ready to process" : "Drag and drop your file here, or click to browse"}</p>
            
            {file && (
              <button 
                onClick={(e) => { e.stopPropagation(); handleProcess(); }}
                className="mt-6 px-6 py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 flex items-center gap-2"
              >
                <Play size={18} /> Run Pipeline
              </button>
            )}
          </div>

          <div className="bg-white rounded-3xl p-8 card-shadow">
            <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
              <FileText size={20} className="text-indigo-500"/> Demo Assets
            </h3>
            <div className="space-y-4">
              <a href="http://localhost:8000/api/demo/download/demo_kyc.csv" download className="block p-4 border border-gray-100 rounded-xl hover:bg-gray-50 transition-colors">
                <p className="font-semibold text-sm text-indigo-600">demo_kyc.csv</p>
                <p className="text-xs text-gray-500 mt-1">Contains exact matches, typos, and semantic discrepancies.</p>
              </a>
              <a href="http://localhost:8000/api/demo/download/demo_crm.csv" download className="block p-4 border border-gray-100 rounded-xl hover:bg-gray-50 transition-colors">
                <p className="font-semibold text-sm text-indigo-600">demo_crm.csv</p>
                <p className="text-xs text-gray-500 mt-1">Contains incomplete records and swapped fields.</p>
              </a>
            </div>
          </div>
        </div>
      )}

      {pipelineState === "PROCESSING" && (
        <div className="bg-white p-12 rounded-3xl card-shadow flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 rounded-full border-4 border-indigo-100 border-t-indigo-600 animate-spin mb-6"></div>
          <h3 className="text-xl font-bold text-gray-900">Pipeline Running...</h3>
          <p className="text-gray-500 mt-2 max-w-sm">Parsing CSV → Extracting Features → Deterministic Matching → Probabilistic Scoring → Graph Resolution</p>
        </div>
      )}

      {pipelineState === "DONE" && result && (
        <div className="space-y-6">
          <div className="bg-white p-8 rounded-3xl card-shadow flex justify-between items-center border-l-4 border-green-500">
            <div>
              <h3 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <CheckCircle className="text-green-500" /> Resolution Complete
              </h3>
              <p className="text-gray-500 mt-1 text-sm">Processed {result.metrics?.records_ingested || 0} records in {result.metrics?.processing_time_ms || 120}ms</p>
            </div>
            <button onClick={() => { setFile(null); setPipelineState("IDLE"); setResult(null); }} className="px-4 py-2 bg-gray-100 rounded-lg text-sm font-medium hover:bg-gray-200">
              Run Another
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-6 rounded-2xl border border-gray-100">
              <p className="text-sm text-gray-500 font-medium mb-2">Raw Records</p>
              <p className="text-3xl font-bold text-gray-900">{result.metrics?.records_ingested || 0}</p>
            </div>
            <div className="hidden md:flex items-center justify-center">
              <ArrowRight size={32} className="text-gray-300" />
            </div>
            <div className="bg-white p-6 rounded-2xl border border-indigo-100 bg-indigo-50/30">
              <p className="text-sm text-indigo-600 font-medium mb-2">Golden Profiles</p>
              <p className="text-3xl font-bold text-indigo-900">{result.metrics?.golden_records_created || 0}</p>
            </div>
            <div className="bg-white p-6 rounded-2xl border border-amber-100 bg-amber-50/30">
              <p className="text-sm text-amber-600 font-medium mb-2">Requires Review</p>
              <p className="text-3xl font-bold text-amber-900">{result.metrics?.reviews_flagged || 0}</p>
            </div>
          </div>

          <div className="bg-white rounded-3xl card-shadow overflow-hidden">
            <div className="p-6 border-b border-gray-100 bg-gray-50">
              <h3 className="font-bold text-gray-900">Discrepancy Explanations</h3>
            </div>
            <div className="p-6">
              {result.explanations && result.explanations.length > 0 ? (
                <div className="space-y-4">
                  {result.explanations.map((exp: any, i: number) => (
                    <div key={i} className="p-4 border border-gray-100 rounded-xl bg-gray-50/50">
                      <div className="flex items-center gap-2 mb-2">
                        {exp.type === "MERGE" ? <Link2 size={16} className="text-green-500" /> : <AlertTriangle size={16} className="text-amber-500" />}
                        <p className="font-semibold text-sm text-gray-900">{exp.title}</p>
                      </div>
                      <p className="text-xs text-gray-600">{exp.description}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm italic">No specific discrepancies flagged in this batch.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
