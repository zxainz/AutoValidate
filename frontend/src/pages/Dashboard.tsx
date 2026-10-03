import React from 'react';
import { DashboardMetrics, Finding, AIStatus } from '../types';
import { MetricsCards } from '../components/MetricsCards';
import { FileUpload } from '../components/FileUpload';
import { ValidationProgress } from '../components/ValidationProgress';
import { FindingsTable } from '../components/FindingsTable';
import { ShieldCheck, Play, FileDown, AlertTriangle } from 'lucide-react';

interface DashboardProps {
  metrics: DashboardMetrics | null;
  findings: Finding[];
  isValidating: boolean;
  aiStatus: AIStatus | null;
  onRefresh: () => void;
  onSelectFinding: (finding: Finding) => void;
  onStartValidation: (ids: number[]) => void;
  onClearAll: () => void;
  onGenerateReport: () => void;
  onNavigateSettings?: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  metrics,
  findings,
  isValidating,
  aiStatus,
  onRefresh,
  onSelectFinding,
  onStartValidation,
  onClearAll,
  onGenerateReport,
  onNavigateSettings,
}) => {
  return (
    <div className="space-y-6">
      {/* Disconnected Warning Banner */}
      {!aiStatus?.connected && (
        <div className="p-4 bg-rose-950/40 border border-rose-500/40 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-lg shadow-rose-950/30">
          <div className="flex items-center space-x-3 text-xs text-rose-200">
            <div className="p-2 bg-rose-500/20 rounded-lg text-rose-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <p className="font-bold text-sm text-rose-300">Live GLM-5.3 API Key Required</p>
              <p className="text-slate-400 mt-0.5">
                Offline simulation and mock results are strictly disabled. Please enter your Z.ai API key in settings to enable validation.
              </p>
            </div>
          </div>
          {onNavigateSettings && (
            <button
              onClick={onNavigateSettings}
              className="text-xs bg-rose-500 hover:bg-rose-400 text-white font-bold px-4 py-2 rounded-xl transition flex-shrink-0 shadow"
            >
              Configure API Key →
            </button>
          )}
        </div>
      )}

      {/* Top Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-sky-950/40 via-slate-900 to-indigo-950/40 border border-slate-800 p-6 rounded-2xl">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            Pentest Findings Triage Dashboard
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Automate false-positive elimination across Nessus, Qualys, and Burp Suite scanner results using live GLM-5.3 deep technical reasoning.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => onStartValidation([])}
            disabled={isValidating || findings.length === 0 || !aiStatus?.connected}
            title={!aiStatus?.connected ? "Configure real Z.ai API key in Settings" : ""}
            className="flex items-center space-x-2 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow-lg shadow-sky-500/20 transition disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>
              {isValidating
                ? 'Validating Findings...'
                : !aiStatus?.connected
                ? 'Live API Required'
                : 'Validate Unverified'}
            </span>
          </button>

          <button
            onClick={onGenerateReport}
            disabled={findings.length === 0}
            className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold px-4 py-2.5 rounded-xl transition disabled:opacity-50"
          >
            <FileDown className="w-3.5 h-3.5 text-sky-400" />
            <span>Generate Client Report</span>
          </button>
        </div>
      </div>

      {/* KPI Metrics */}
      <MetricsCards metrics={metrics} />

      {/* Real-time Validation Progress Banner */}
      {isValidating && (
        <ValidationProgress isRunning={isValidating} onFinished={onRefresh} />
      )}

      {/* Ingestion Dropzone */}
      <FileUpload onUploadSuccess={onRefresh} />

      {/* Ingested Findings Preview */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
            Triage & Verification Table
          </h2>
        </div>

        <FindingsTable
          findings={findings}
          onSelectFinding={onSelectFinding}
          onStartValidation={onStartValidation}
          onClearAll={onClearAll}
          isValidating={isValidating}
        />
      </div>
    </div>
  );
};
