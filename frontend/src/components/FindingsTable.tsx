import React, { useState } from 'react';
import { Finding } from '../types';
import { ConfidenceMeter } from './ConfidenceMeter';
import { Search, Play, CheckCircle2, XCircle, AlertTriangle, Trash2, Eye } from 'lucide-react';

interface FindingsTableProps {
  findings: Finding[];
  onSelectFinding: (finding: Finding) => void;
  onStartValidation: (ids: number[]) => void;
  onClearAll: () => void;
  isValidating: boolean;
  isAiConnected?: boolean;
}

export const FindingsTable: React.FC<FindingsTableProps> = ({
  findings,
  onSelectFinding,
  onStartValidation,
  onClearAll,
  isValidating,
  isAiConnected = true,
}) => {
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sourceFilter, setSourceFilter] = useState('ALL');
  const [selectedIds, setSelectedIds] = useState<number[]>([]);

  // Filtering logic
  const filtered = findings.filter((f) => {
    const matchesSearch =
      search === '' ||
      f.title.toLowerCase().includes(search.toLowerCase()) ||
      (f.target_host && f.target_host.toLowerCase().includes(search.toLowerCase())) ||
      (f.target_url && f.target_url.toLowerCase().includes(search.toLowerCase())) ||
      f.cve_list.some((c) => c.toLowerCase().includes(search.toLowerCase()));

    const matchesSeverity = severityFilter === 'ALL' || f.severity.toUpperCase() === severityFilter;
    const matchesStatus = statusFilter === 'ALL' || f.status === statusFilter;
    const matchesSource = sourceFilter === 'ALL' || f.scan_source.toUpperCase() === sourceFilter;

    return matchesSearch && matchesSeverity && matchesStatus && matchesSource;
  });

  const toggleSelectAll = () => {
    if (selectedIds.length === filtered.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filtered.map((f) => f.id));
    }
  };

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
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
        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <CheckCircle2 className="w-3 h-3" /> True Positive
        </span>
      );
    }
    if (status === 'FALSE_POSITIVE') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/30">
          <XCircle className="w-3 h-3" /> False Positive
        </span>
      );
    }
    if (status === 'NEEDS_MANUAL_REVIEW') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30">
          <AlertTriangle className="w-3 h-3" /> Review
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
        Unverified
      </span>
    );
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Table Toolbar */}
      <div className="p-4 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by title, host, URL, or CVE..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
        </div>

        {/* Filters and Actions */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Severity Filter */}
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-300 rounded-lg px-2.5 py-2 focus:outline-none"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-300 rounded-lg px-2.5 py-2 focus:outline-none"
          >
            <option value="ALL">All Verdicts</option>
            <option value="UNVERIFIED">Unverified</option>
            <option value="TRUE_POSITIVE">True Positive</option>
            <option value="FALSE_POSITIVE">False Positive</option>
            <option value="NEEDS_MANUAL_REVIEW">Needs Review</option>
          </select>

          {/* Scanner Source Filter */}
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-300 rounded-lg px-2.5 py-2 focus:outline-none"
          >
            <option value="ALL">All Scanners</option>
            <option value="NESSUS">Nessus</option>
            <option value="BURP">Burp Suite</option>
            <option value="QUALYS">Qualys</option>
            <option value="GENERIC">Generic</option>
          </select>

          {/* Action Buttons */}
          <button
            onClick={() => onStartValidation(selectedIds)}
            disabled={isValidating || findings.length === 0 || !isAiConnected}
            title={!isAiConnected ? "Real GLM-5.3 API key required" : ""}
            className="flex items-center space-x-1.5 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition disabled:opacity-50 shadow-md shadow-sky-500/20"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>
              {isValidating
                ? 'Validating...'
                : !isAiConnected
                ? 'Live API Required'
                : selectedIds.length > 0
                ? `Validate (${selectedIds.length})`
                : 'Validate All Unverified'}
            </span>
          </button>

          {findings.length > 0 && (
            <button
              onClick={onClearAll}
              title="Clear all ingested findings"
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition border border-slate-700"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
              <th className="p-3 w-8">
                <input
                  type="checkbox"
                  checked={filtered.length > 0 && selectedIds.length === filtered.length}
                  onChange={toggleSelectAll}
                  className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-0 cursor-pointer"
                />
              </th>
              <th className="p-3">Severity</th>
              <th className="p-3">Vulnerability Finding</th>
              <th className="p-3">Target</th>
              <th className="p-3">Scanner</th>
              <th className="p-3">AI Verdict</th>
              <th className="p-3">Confidence</th>
              <th className="p-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={8} className="p-8 text-center text-slate-500">
                  No vulnerability findings match the current filters or scanner input is empty.
                </td>
              </tr>
            ) : (
              filtered.map((f) => (
                <tr
                  key={f.id}
                  onClick={() => onSelectFinding(f)}
                  className="hover:bg-slate-800/40 cursor-pointer transition"
                >
                  <td className="p-3" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(f.id)}
                      onChange={() => toggleSelect(f.id)}
                      className="rounded bg-slate-900 border-slate-700 text-sky-500 focus:ring-0 cursor-pointer"
                    />
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded-full font-bold border text-[10px] ${getSeverityBadge(f.severity)}`}>
                      {f.severity}
                    </span>
                  </td>
                  <td className="p-3 font-medium text-slate-200 max-w-md">
                    <div className="truncate font-semibold">{f.title}</div>
                    {f.cve_list.length > 0 && (
                      <div className="text-[11px] text-sky-400 mt-0.5 truncate">
                        {f.cve_list.join(', ')}
                      </div>
                    )}
                  </td>
                  <td className="p-3 font-mono text-[11px] text-slate-400 max-w-xs truncate">
                    {f.target_url || f.target_host || 'unknown'}
                  </td>
                  <td className="p-3">
                    <span className="font-mono text-[11px] bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">
                      {f.scan_source.toUpperCase()}
                    </span>
                  </td>
                  <td className="p-3">{getVerdictBadge(f.status)}</td>
                  <td className="p-3">
                    <ConfidenceMeter score={f.confidence_score} size="sm" showBar={true} />
                  </td>
                  <td className="p-3 text-right" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => onSelectFinding(f)}
                      className="p-1.5 text-slate-400 hover:text-sky-400 hover:bg-slate-800 rounded transition"
                      title="Inspect finding details"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Table Footer info */}
      <div className="p-3 bg-slate-900/50 border-t border-slate-800 text-xs text-slate-400 flex justify-between items-center">
        <span>Showing {filtered.length} of {findings.length} findings</span>
        {selectedIds.length > 0 && (
          <span className="text-sky-400 font-medium">{selectedIds.length} findings selected</span>
        )}
      </div>
    </div>
  );
};
