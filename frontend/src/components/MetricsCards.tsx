import React from 'react';
import { DashboardMetrics } from '../types';
import { CheckCircle2, Clock, ShieldAlert, Filter } from 'lucide-react';

interface MetricsCardsProps {
  metrics: DashboardMetrics | null;
}

export const MetricsCards: React.FC<MetricsCardsProps> = ({ metrics }) => {
  if (!metrics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 bg-slate-800/40 rounded-xl border border-slate-800" />
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'Triage Time Saved',
      value: `${metrics.time_saved_hours}h`,
      subtitle: `${metrics.validated_findings} findings evaluated`,
      icon: Clock,
      color: 'from-indigo-500/20 to-indigo-600/10 border-indigo-500/30 text-indigo-400',
      iconBg: 'bg-indigo-500/20 text-indigo-400',
    },
    {
      title: 'False Positives Filtered',
      value: `${metrics.false_positives}`,
      subtitle: `${metrics.false_positive_rate}% FP elimination rate`,
      icon: Filter,
      color: 'from-rose-500/20 to-rose-600/10 border-rose-500/30 text-rose-400',
      iconBg: 'bg-rose-500/20 text-rose-400',
    },
    {
      title: 'Verified True Positives',
      value: `${metrics.true_positives}`,
      subtitle: 'Client deliverable findings',
      icon: CheckCircle2,
      color: 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30 text-emerald-400',
      iconBg: 'bg-emerald-500/20 text-emerald-400',
    },
    {
      title: 'Total Ingested Findings',
      value: `${metrics.total_findings}`,
      subtitle: `${metrics.unverified_findings} pending triage`,
      icon: ShieldAlert,
      color: 'from-sky-500/20 to-sky-600/10 border-sky-500/30 text-sky-400',
      iconBg: 'bg-sky-500/20 text-sky-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-5 rounded-xl border bg-gradient-to-br backdrop-blur-sm ${card.color} transition-all duration-200 hover:translate-y-[-2px]`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">{card.title}</span>
              <div className={`p-2 rounded-lg ${card.iconBg}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-3xl font-extrabold text-white tracking-tight">{card.value}</span>
            </div>
            <p className="mt-1 text-xs text-slate-400 font-medium">{card.subtitle}</p>
          </div>
        );
      })}
    </div>
  );
};
