import React, { useState } from 'react';
import { Finding } from '../types';
import { ConfidenceMeter } from './ConfidenceMeter';
import { X, ShieldAlert, CheckCircle2, XCircle, AlertTriangle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

interface FindingDetailModalProps {
  finding: Finding | null;
  onClose: () => void;
  onUpdated: () => void;
}

export const FindingDetailModal: React.FC<FindingDetailModalProps> = ({ finding, onClose, onUpdated }) => {
  const [revalidating, setRevalidating] = useState(false);

  if (!finding) return null;

  const result = finding.latest_result;

  const handleRevalidate = async () => {
    setRevalidating(true);
    try {
      await api.validateSingleFinding(finding.id);
      onUpdated();
    } catch (e) {
      console.error(e);
    } finally {
      setRevalidating(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    const s = sev.toLowerCase();
    if (s === 'critical') return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
    if (s === 'high') return 'bg-orange-500/15 text-orange-400 border-orange-500/30';
    if (s === 'medium') return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
    return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
  };

  const getVerdictBadge = (status: string) => {
    if (status === 'TRUE_POSITIVE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <CheckCircle2 className="w-3.5 h-3.5" /> TRUE POSITIVE
        </span>
      );
    }
    if (status === 'FALSE_POSITIVE') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
          <XCircle className="w-3.5 h-3.5" /> FALSE POSITIVE
        </span>
      );
    }
    if (status === 'NEEDS_MANUAL_REVIEW') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-3.5 h-3.5" /> NEEDS REVIEW
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700">
        UNVERIFIED
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="bg-[#111827] border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`text-xs px-2.5 py-0.5 rounded-full font-bold border ${getSeverityBadge(finding.severity)}`}>
                {finding.severity}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono border border-slate-700">
                {finding.scan_source.toUpperCase()}
              </span>
              {finding.scanner_id && (
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono border border-slate-700">
                  {finding.scanner_id}
                </span>
              )}
              {getVerdictBadge(finding.status)}
            </div>
            <h2 className="text-xl font-bold text-slate-100">{finding.title}</h2>
            <div className="text-xs text-slate-400 flex flex-wrap gap-4">
              <span>Target: <strong className="text-slate-200">{finding.target_url || finding.target_host}</strong></span>
              {finding.target_port && <span>Port: <strong className="text-slate-200">{finding.target_port}</strong></span>}
              {finding.cve_list.length > 0 && (
                <span>CVEs: <strong className="text-sky-400">{finding.cve_list.join(', ')}</strong></span>
              )}
              {finding.cvss_score !== null && finding.cvss_score !== undefined && (
                <span>CVSS: <strong className="text-amber-400">{finding.cvss_score}</strong></span>
              )}
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* AI Analysis Card */}
          <div className="bg-slate-900/90 border border-sky-500/20 rounded-xl p-5 shadow-lg">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <span className="p-1.5 bg-sky-500/20 text-sky-400 rounded-md">
                  <ShieldAlert className="w-4 h-4" />
                </span>
                <h3 className="text-sm font-semibold text-sky-400">GLM-5.3 Validation Analysis</h3>
              </div>
              <div className="flex items-center space-x-3">
                <ConfidenceMeter score={finding.confidence_score} size="lg" showBar={false} />
                <button
                  onClick={handleRevalidate}
                  disabled={revalidating}
                  className="flex items-center space-x-1.5 text-xs bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/30 px-3 py-1.5 rounded-lg transition"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${revalidating ? 'animate-spin' : ''}`} />
                  <span>{revalidating ? 'Analyzing...' : 'Re-Validate'}</span>
                </button>
              </div>
            </div>

            {result ? (
              <div className="mt-4 space-y-4">
                {/* Score Breakdown Bar */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/60 text-center">
                    <span className="text-[11px] text-slate-400 uppercase font-medium">Technical Feasibility</span>
                    <p className="text-base font-bold font-mono text-emerald-400 mt-0.5">
                      {Math.round(result.feasibility_score * 100)}%
                    </p>
                  </div>
                  <div className="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/60 text-center">
                    <span className="text-[11px] text-slate-400 uppercase font-medium">Environmental Context</span>
                    <p className="text-base font-bold font-mono text-sky-400 mt-0.5">
                      {Math.round(result.context_score * 100)}%
                    </p>
                  </div>
                  <div className="bg-slate-800/60 p-2.5 rounded-lg border border-slate-700/60 text-center">
                    <span className="text-[11px] text-slate-400 uppercase font-medium">Evidence Credibility</span>
                    <p className="text-base font-bold font-mono text-indigo-400 mt-0.5">
                      {Math.round(result.evidence_score * 100)}%
                    </p>
                  </div>
                </div>

                {/* Reasoning Box */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Technical Reasoning:
                  </h4>
                  <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
                    {result.reasoning}
                  </div>
                </div>

                {/* False Positive Explanation Box (if applicable) */}
                {result.verdict === 'FALSE_POSITIVE' && (
                  <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                    <h4 className="text-xs font-semibold text-rose-400 uppercase tracking-wider flex items-center gap-1.5 mb-1">
                      <XCircle className="w-4 h-4 text-rose-400" />
                      False Positive Elimination Rationale:
                    </h4>
                    <p className="text-xs text-rose-200/90 leading-relaxed">
                      {result.false_positive_reason || 'Identified as non-exploitable based on scanner evidence analysis.'}
                    </p>
                  </div>
                )}

                {/* Recommendation */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Remediation / Next Steps:
                  </h4>
                  <div className="bg-sky-500/10 border border-sky-500/20 p-3 rounded-lg text-xs text-sky-300 font-sans">
                    {result.recommended_action || finding.solution || 'Verify patch baseline and server configurations.'}
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-4 text-center py-6 text-slate-500 text-xs">
                Finding has not yet been validated by the AI engine. Click "Re-Validate" above to run triage.
              </div>
            )}
          </div>

          {/* Raw Scanner Evidence */}
          <div>
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Raw Scanner Evidence / Artifacts:
            </h3>
            {finding.raw_evidence ? (
              <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs font-mono text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-60">
                {finding.raw_evidence}
              </pre>
            ) : (
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-xs text-slate-500 italic">
                No raw response payload or banner captured by the scanner.
              </div>
            )}
          </div>

          {/* Description */}
          {finding.description && (
            <div>
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Scanner Description & Synopsis:
              </h3>
              <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                {finding.description}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
