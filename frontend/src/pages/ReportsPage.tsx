import React, { useState, useEffect } from 'react';
import { ReportSummary } from '../types';
import { api } from '../services/api';
import { FileText, Download, Eye, Clock, ShieldCheck, XCircle, Plus, RefreshCw, X } from 'lucide-react';

export const ReportsPage: React.FC = () => {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [reportTitle, setReportTitle] = useState('External Pentest Findings Validation Report');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const data = await api.listReports();
      setReports(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    try {
      await api.generateReport(reportTitle);
      await fetchReports();
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-sky-400" />
            Validated Security Reports
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Export client-ready penetration test deliverables in PDF, HTML, CSV, or machine-readable JSON.
          </p>
        </div>
      </div>

      {/* Report Generator Box */}
      <div className="bg-[#111827] border border-slate-800 rounded-xl p-6 shadow-xl">
        <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
          <Plus className="w-4 h-4 text-sky-400" />
          Generate New Report Snapshot
        </h2>
        <form onSubmit={handleGenerate} className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={reportTitle}
            onChange={(e) => setReportTitle(e.target.value)}
            placeholder="Engagement Report Title..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
            required
          />
          <button
            type="submit"
            disabled={generating}
            className="flex items-center justify-center space-x-2 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-semibold px-5 py-2 rounded-lg transition disabled:opacity-50"
          >
            {generating ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Compiling Snapshot...</span>
              </>
            ) : (
              <span>Create Report</span>
            )}
          </button>
        </form>
      </div>

      {/* Reports List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Generated Reports ({reports.length})
          </h2>
          <button
            onClick={fetchReports}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded transition"
            title="Refresh reports"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {reports.length === 0 ? (
          <div className="bg-[#111827] border border-slate-800 rounded-xl p-12 text-center text-slate-500 text-xs">
            No reports generated yet. Click "Create Report" above to generate a client-ready snapshot.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {reports.map((report) => {
              const fpRate =
                report.total_findings > 0
                  ? Math.round((report.false_positives / report.total_findings) * 100)
                  : 0;

              return (
                <div
                  key={report.id}
                  className="bg-[#111827] border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-lg transition"
                >
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    {/* Left: Title & Meta */}
                    <div className="space-y-1.5">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-base font-bold text-slate-100">{report.title}</h3>
                        <span className="text-xs bg-slate-800 text-slate-400 font-mono px-2 py-0.5 rounded border border-slate-700">
                          #{report.id}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">
                        Generated on {new Date(report.created_at).toLocaleString()}
                      </p>

                      {/* Badges */}
                      <div className="flex flex-wrap items-center gap-2 pt-1">
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          <ShieldCheck className="w-3 h-3" /> {report.true_positives} True Positives
                        </span>
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-md bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          <XCircle className="w-3 h-3" /> {report.false_positives} FPs Filtered ({fpRate}%)
                        </span>
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-md bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                          <Clock className="w-3 h-3" /> {report.time_saved_hours}h Saved
                        </span>
                      </div>
                    </div>

                    {/* Right: Export Buttons */}
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        onClick={() => setPreviewUrl(api.getExportUrl(report.id, 'html'))}
                        className="flex items-center space-x-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3 py-1.5 rounded-lg transition"
                      >
                        <Eye className="w-3.5 h-3.5 text-sky-400" />
                        <span>Preview</span>
                      </button>

                      <a
                        href={api.getExportUrl(report.id, 'pdf')}
                        download
                        className="flex items-center space-x-1.5 text-xs bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/30 px-3 py-1.5 rounded-lg transition font-medium"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>PDF</span>
                      </a>

                      <a
                        href={api.getExportUrl(report.id, 'html')}
                        download
                        className="flex items-center space-x-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg transition font-medium"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>HTML</span>
                      </a>

                      <a
                        href={api.getExportUrl(report.id, 'csv')}
                        download
                        className="flex items-center space-x-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg transition font-medium"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>CSV</span>
                      </a>

                      <a
                        href={api.getExportUrl(report.id, 'json')}
                        download
                        className="flex items-center space-x-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg transition font-medium"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>JSON</span>
                      </a>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* In-App Live HTML Report Preview Modal */}
      {previewUrl && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-[#0f172a] border border-slate-700 rounded-2xl w-full max-w-5xl h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-[#111827]">
              <span className="text-sm font-semibold text-slate-200">Interactive Report Preview</span>
              <button
                onClick={() => setPreviewUrl(null)}
                className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <iframe src={previewUrl} className="w-full flex-1 border-none bg-slate-900" title="Report Preview" />
          </div>
        </div>
      )}
    </div>
  );
};
