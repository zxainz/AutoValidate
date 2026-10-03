import React from 'react';
import { Finding, AIStatus } from '../types';
import { FindingsTable } from '../components/FindingsTable';
import { ValidationProgress } from '../components/ValidationProgress';
import { ShieldAlert } from 'lucide-react';

interface FindingsPageProps {
  findings: Finding[];
  isValidating: boolean;
  aiStatus: AIStatus | null;
  onRefresh: () => void;
  onSelectFinding: (finding: Finding) => void;
  onStartValidation: (ids: number[]) => void;
  onClearAll: () => void;
}

export const FindingsPage: React.FC<FindingsPageProps> = ({
  findings,
  isValidating,
  aiStatus,
  onRefresh,
  onSelectFinding,
  onStartValidation,
  onClearAll,
}) => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-sky-400" />
            Scanner Findings Triage Hub
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Filter, inspect raw evidence, examine AI verification reasoning, and eliminate false positives.
          </p>
        </div>
      </div>

      {isValidating && (
        <ValidationProgress isRunning={isValidating} onFinished={onRefresh} />
      )}

      <FindingsTable
        findings={findings}
        onSelectFinding={onSelectFinding}
        onStartValidation={onStartValidation}
        onClearAll={onClearAll}
        isValidating={isValidating}
        isAiConnected={aiStatus?.connected ?? false}
      />
    </div>
  );
};
