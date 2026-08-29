import React, { useState } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  Database,
  Layers,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Clock,
} from 'lucide-react';
import { uploadCSV, seedSyntheticData, getDataQualityReport } from '../api';
import { formatNumber } from '../utils/formatters';

export function DataIngestionPage({ onNavigate }) {
  const [sourceSystem, setSourceSystem] = useState('EQUITY');
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [seeding, setSeeding] = useState(false);
  const [seedResult, setSeedResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const sourceSystems = [
    { id: 'EQUITY', label: 'Equity Broking', desc: 'Demat holdings, direct stocks, trades' },
    { id: 'MUTUAL_FUND', label: 'Mutual Funds', desc: 'Folios, SIPs, lump-sum investments' },
    { id: 'INSURANCE', label: 'Insurance (Life & General)', desc: 'Policies, coverage, premium payments' },
    { id: 'LOAN', label: 'Lending & Mortgages', desc: 'Term loans, home loans, collateral' },
    { id: 'WEALTH', label: 'Wealth Management', desc: 'Bespoke PMS, family office portfolios' },
  ];

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.endsWith('.csv')) {
        setErrorMessage('Please select a valid .csv file.');
        return;
      }
      setSelectedFile(file);
      setErrorMessage('');
      setUploadResult(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (!file.name.endsWith('.csv')) {
        setErrorMessage('Please drop a valid .csv file.');
        return;
      }
      setSelectedFile(file);
      setErrorMessage('');
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setUploadProgress(15);
    setErrorMessage('');

    // Simulate animated upload progress steps
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 25;
      });
    }, 200);

    try {
      const res = await uploadCSV(sourceSystem, selectedFile);
      clearInterval(interval);
      setUploadProgress(100);
      setUploadResult(res);
    } catch (err) {
      clearInterval(interval);
      setErrorMessage(err.message || 'CSV upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    setErrorMessage('');
    try {
      const res = await seedSyntheticData();
      setSeedResult(res);
    } catch (err) {
      setErrorMessage(err.message || 'Seeding failed');
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="p-3 sm:p-5 lg:p-8 space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight font-display">Data Ingestion Engine</h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Ingest and normalize incoming CSV feeds from external financial business systems.
          </p>
        </div>

        {/* Quick Seed Button */}
        <button
          onClick={handleSeed}
          disabled={seeding}
          className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl transition-all shadow-xs flex items-center gap-2"
        >
          <Sparkles className={`w-4 h-4 text-emerald-400 ${seeding ? 'animate-spin' : ''}`} />
          {seeding ? 'Seeding Datasets...' : 'Seed All 5 Synthetic Feeds'}
        </button>
      </div>

      {/* Seeding Success Banner */}
      {seedResult && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between text-xs text-emerald-900 animate-fade-in">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <div>
              <div className="font-bold">{seedResult.message}</div>
              <div className="text-[11px] text-emerald-700 mt-0.5">
                Ready for identity resolution & candidate blocking.
              </div>
            </div>
          </div>
          <button
            onClick={() => onNavigate('matching')}
            className="px-3.5 py-1.5 bg-emerald-600 text-white font-bold rounded-lg text-xs hover:bg-emerald-700 transition-colors flex items-center gap-1"
          >
            Run Matching Engine <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Error Alert */}
      {errorMessage && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex items-center gap-3 text-xs text-red-800">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* ── Main Ingestion Grid ──────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Source System Selection */}
        <div className="lg:col-span-5 space-y-3">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            1. Select Target Source System
          </label>

          <div className="space-y-2">
            {sourceSystems.map((sys) => {
              const isSelected = sourceSystem === sys.id;
              return (
                <div
                  key={sys.id}
                  onClick={() => setSourceSystem(sys.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-emerald-500 bg-emerald-50/60 shadow-xs ring-1 ring-emerald-500/20'
                      : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between text-xs font-bold text-slate-900">
                    <span>{sys.label}</span>
                    {isSelected && <span className="w-2 h-2 rounded-full bg-emerald-600" />}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">{sys.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: File Upload & Progress */}
        <div className="lg:col-span-7 space-y-4">
          <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
            2. Upload Customer Records CSV
          </label>

          {/* Drag & Drop Card */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all bg-white ${
              dragOver
                ? 'border-emerald-500 bg-emerald-50/40'
                : 'border-slate-300 hover:border-slate-400'
            }`}
          >
            <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-600 flex items-center justify-center mx-auto mb-3">
              <UploadCloud className="w-6 h-6 text-emerald-600" />
            </div>

            <div className="text-sm font-semibold text-slate-800">
              {selectedFile ? selectedFile.name : 'Drag & drop your CSV file here'}
            </div>
            <p className="text-xs text-slate-500 mt-1">Supports standard UTF-8 encoded files up to 10MB</p>

            <div className="mt-4">
              <input
                type="file"
                id="csvFileInput"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
              />
              <label
                htmlFor="csvFileInput"
                className="inline-block px-4 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-xl cursor-pointer transition-all shadow-xs"
              >
                {selectedFile ? 'Change File' : 'Browse Files'}
              </label>
            </div>
          </div>

          {/* Upload Button */}
          {selectedFile && !uploadResult && (
            <div className="flex items-center justify-between p-4 bg-slate-50 border border-slate-200 rounded-xl">
              <div className="flex items-center gap-2.5 text-xs text-slate-700">
                <FileText className="w-4 h-4 text-emerald-600" />
                <span className="font-semibold">{selectedFile.name}</span>
                <span className="text-slate-400">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
              </div>

              <button
                onClick={handleUpload}
                disabled={uploading}
                className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-lg transition-all flex items-center gap-1.5 shadow-xs"
              >
                {uploading ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    Start Ingestion <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          )}

          {/* Progress & Verification Checklist */}
          {uploading && (
            <div className="p-5 bg-white border border-slate-200 rounded-xl space-y-3">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                <span>Ingestion Progress</span>
                <span className="font-mono">{uploadProgress}%</span>
              </div>
              <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-emerald-600 animate-spin" />
                Normalizing attributes & generating 384-dim semantic embeddings...
              </div>
            </div>
          )}

          {/* Success Summary */}
          {uploadResult && (
            <div className="p-6 bg-white border border-emerald-200 rounded-2xl shadow-card space-y-4 animate-fade-in">
              <div className="flex items-center gap-2.5 text-emerald-900 font-bold text-sm">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                <span>{uploadResult.message}</span>
              </div>

              {/* 4 Pipeline Milestones */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-xs">
                  <div className="text-emerald-600 font-bold flex items-center gap-1">
                    ✓ Records Processed
                  </div>
                  <div className="text-slate-900 font-semibold mt-1">
                    {uploadResult.records_ingested} records
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-xs">
                  <div className="text-emerald-600 font-bold flex items-center gap-1">
                    ✓ Normalized
                  </div>
                  <div className="text-slate-900 font-semibold mt-1">PAN, Mobile, DOB</div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-xs">
                  <div className="text-emerald-600 font-bold flex items-center gap-1">
                    ✓ ML Vectors
                  </div>
                  <div className="text-slate-900 font-semibold mt-1">384-dim Embeddings</div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 text-xs">
                  <div className="text-emerald-600 font-bold flex items-center gap-1">
                    ✓ Ready
                  </div>
                  <div className="text-slate-900 font-semibold mt-1">Candidate Generation</div>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => onNavigate('matching')}
                  className="px-6 py-2.5 bg-emerald-600 text-white text-xs font-bold rounded-xl hover:bg-emerald-700 transition-all flex items-center gap-2 shadow-xs"
                >
                  Proceed to Matching Pipeline <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
