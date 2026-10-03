import React, { useState, useRef } from 'react';
import { UploadCloud, CheckCircle, AlertCircle, RefreshCw, Sparkles } from 'lucide-react';
import { api } from '../services/api';

interface FileUploadProps {
  onUploadSuccess: () => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [scannerType, setScannerType] = useState('auto');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await processUpload(e.target.files[0]);
    }
  };

  const processUpload = async (file: File) => {
    setUploading(true);
    setError(null);
    setUploadResult(null);
    try {
      const res = await api.uploadScannerFile(file, scannerType);
      if (res.total_imported === 0) {
        setUploadResult(res.message || 'No findings identified in the uploaded file.');
      } else {
        const detected = (res.scanner_detected || 'generic').toUpperCase();
        setUploadResult(`Successfully parsed ${res.total_imported} findings (${detected})`);
      }
      onUploadSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const loadSampleScan = async (sampleName: string, type: string) => {
    setUploading(true);
    setError(null);
    setUploadResult(null);
    try {
      // Fetch sample file from public or direct API trigger
      const response = await fetch(`/sample_scans/${sampleName}`);
      let blob: Blob;
      if (response.ok) {
        blob = await response.blob();
      } else {
        // Fallback: embedded quick sample
        const genericJson = JSON.stringify({
          findings: [
            {
              title: "OpenSSL Remote Version Detection",
              severity: "High",
              cve: "CVE-2021-3450",
              target: "192.168.1.100:443",
              evidence: "Remote banner: OpenSSL/1.1.1n-0+deb11u5 (Debian-11+deb11u5) backported security patch",
              description: "Vulnerable version detected by banner inspection."
            },
            {
              title: "Apache Log4j Remote Code Execution (Log4Shell)",
              severity: "Critical",
              cve: "CVE-2021-44228",
              target: "192.168.1.100:8080",
              evidence: "Executed command 'id': uid=0(root) gid=0(root)",
              description: "JNDI LDAP callback confirmed command execution."
            },
            {
              title: "Path Traversal (WAF Blocked)",
              severity: "High",
              target: "https://api.example.com/download?file=../../../../etc/passwd",
              evidence: "HTTP 403 Forbidden - Access Denied by Perimeter Cloudflare WAF",
              description: "Automated scan flagged path traversal but target rejected payload."
            }
          ]
        });
        blob = new Blob([genericJson], { type: 'application/json' });
      }

      const testFile = new File([blob], sampleName, { type: 'text/plain' });
      const res = await api.uploadScannerFile(testFile, type);
      setUploadResult(`Loaded sample scan: ${res.total_imported} findings imported.`);
      onUploadSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to load sample');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-xl p-6 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-sky-400" />
            Scanner Ingestion Engine
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Ingest Nessus (.nessus/xml/csv), Qualys (xml/csv), Burp Suite (xml/json), or Generic JSON.
          </p>
        </div>

        {/* Scanner Selection */}
        <div className="flex items-center space-x-2">
          <label className="text-xs text-slate-400 font-medium">Format:</label>
          <select
            value={scannerType}
            onChange={(e) => setScannerType(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-sky-500"
          >
            <option value="auto">⚡ Auto-Detect</option>
            <option value="nessus">Nessus (XML/CSV)</option>
            <option value="qualys">Qualys (XML/CSV)</option>
            <option value="burp">Burp Suite (JSON/XML)</option>
            <option value="generic">Generic JSON</option>
          </select>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-sky-500 bg-sky-500/10'
            : 'border-slate-700 hover:border-slate-500 bg-slate-900/50 hover:bg-slate-900/80'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".nessus,.xml,.json,.csv"
          onChange={handleFileInput}
        />
        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="p-3 bg-sky-500/10 border border-sky-500/20 rounded-full text-sky-400">
            {uploading ? (
              <RefreshCw className="w-6 h-6 animate-spin text-sky-400" />
            ) : (
              <UploadCloud className="w-6 h-6" />
            )}
          </div>
          <div>
            <p className="text-sm font-medium text-slate-200">
              {uploading ? 'Parsing and extracting findings...' : 'Click to browse or drop scanner output file here'}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Supports .nessus, .xml, .json, and .csv export files
            </p>
          </div>
        </div>
      </div>

      {/* Quick Sample Buttons */}
      <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          Quick Test Samples:
        </span>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => loadSampleScan('nessus_sample.xml', 'nessus')}
            disabled={uploading}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition"
          >
            + Nessus Sample
          </button>
          <button
            type="button"
            onClick={() => loadSampleScan('burp_sample.json', 'burp')}
            disabled={uploading}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition"
          >
            + Burp Suite Sample
          </button>
          <button
            type="button"
            onClick={() => loadSampleScan('qualys_sample.xml', 'qualys')}
            disabled={uploading}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition"
          >
            + Qualys Sample
          </button>
        </div>
      </div>

      {/* Alerts */}
      {uploadResult && (
        <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center space-x-2 text-xs text-emerald-400">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>{uploadResult}</span>
        </div>
      )}
      {error && (
        <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg flex items-center space-x-2 text-xs text-rose-400">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
