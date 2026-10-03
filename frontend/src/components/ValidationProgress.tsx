import React, { useEffect, useState } from 'react';
import { wsClient } from '../services/websocket';
import { RefreshCw } from 'lucide-react';

interface ValidationProgressProps {
  isRunning: boolean;
  onFinished: () => void;
}

export const ValidationProgress: React.FC<ValidationProgressProps> = ({ isRunning, onFinished }) => {
  const [progress, setProgress] = useState<{
    percent: number;
    processed: number;
    total: number;
    title: string;
    verdict: string;
  } | null>(null);

  useEffect(() => {
    const unsubscribe = wsClient.subscribe((data) => {
      if (data.type === 'progress') {
        setProgress({
          percent: data.percent,
          processed: data.processed,
          total: data.total,
          title: data.title,
          verdict: data.verdict,
        });
      } else if (data.type === 'completed') {
        onFinished();
      }
    });

    return () => unsubscribe();
  }, [onFinished]);

  if (!isRunning && !progress) return null;

  return (
    <div className="bg-[#111827] border border-sky-500/30 rounded-xl p-5 shadow-2xl relative overflow-hidden">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-sky-500/20 text-sky-400 rounded-lg animate-spin">
            <RefreshCw className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              AI Validation Engine Running
              <span className="text-xs font-mono bg-sky-500/10 text-sky-400 border border-sky-500/20 px-2 py-0.5 rounded">
                GLM-5.3 Reasoning
              </span>
            </h3>
            <p className="text-xs text-slate-400 truncate max-w-md">
              {progress ? `Analyzing: ${progress.title}` : 'Evaluating scanner evidence and technical feasibility...'}
            </p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-xl font-bold font-mono text-sky-400">
            {progress ? `${Math.round(progress.percent)}%` : '0%'}
          </span>
          <p className="text-xs text-slate-400 font-mono">
            {progress ? `${progress.processed} of ${progress.total}` : 'Queued'}
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
        <div
          className="bg-gradient-to-r from-sky-500 to-indigo-500 h-full rounded-full transition-all duration-300 shadow-lg shadow-sky-500/50"
          style={{ width: `${progress ? progress.percent : 5}%` }}
        />
      </div>
    </div>
  );
};
