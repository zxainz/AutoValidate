import React from 'react';

interface ConfidenceMeterProps {
  score: number | null | undefined;
  size?: 'sm' | 'md' | 'lg';
  showBar?: boolean;
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({ score, size = 'md', showBar = true }) => {
  if (score === null || score === undefined) {
    return <span className="text-xs text-slate-500 font-mono">Unscored</span>;
  }

  const rounded = Math.round(score);

  // Color selection
  let colorClass = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
  let barColor = 'bg-emerald-500';
  if (score < 40) {
    colorClass = 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    barColor = 'bg-rose-500';
  } else if (score < 75) {
    colorClass = 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    barColor = 'bg-amber-500';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3.5 py-1.5 font-bold',
  }[size];

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center space-x-2">
        <span className={`inline-flex items-center font-mono font-semibold rounded-md border ${colorClass} ${sizeClasses}`}>
          {rounded}% Conf.
        </span>
      </div>
      {showBar && (
        <div className="w-20 bg-slate-800 h-1.5 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${barColor}`}
            style={{ width: `${rounded}%` }}
          />
        </div>
      )}
    </div>
  );
};
