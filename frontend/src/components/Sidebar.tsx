import React from 'react';
import { Shield, ShieldAlert, FileText, Settings, BarChart2, LucideIcon } from 'lucide-react';

import { AIStatus } from '../types';

interface SidebarProps {
  currentTab: 'dashboard' | 'findings' | 'reports' | 'settings';
  setCurrentTab: (tab: 'dashboard' | 'findings' | 'reports' | 'settings') => void;
  unverifiedCount: number;
  aiStatus: AIStatus | null;
}

interface NavItem {
  id: 'dashboard' | 'findings' | 'reports' | 'settings';
  label: string;
  icon: LucideIcon;
  badge?: number | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, setCurrentTab, unverifiedCount, aiStatus }) => {
  const navItems: NavItem[] = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart2 },
    { id: 'findings', label: 'Findings Triage', icon: ShieldAlert, badge: unverifiedCount > 0 ? unverifiedCount : null },
    { id: 'reports', label: 'Validated Reports', icon: FileText },
    { id: 'settings', label: 'AI Configuration', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-[#0d1527] border-r border-slate-800 flex flex-col justify-between flex-shrink-0 h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="p-6 flex items-center space-x-3 border-b border-slate-800">
          <div className="bg-gradient-to-tr from-sky-500 to-indigo-600 p-2.5 rounded-xl shadow-lg shadow-sky-500/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-slate-100 tracking-tight">AutoValidate</h1>
            <p className="text-xs text-sky-400 font-medium">AI Pentest Validator</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== null && item.badge !== undefined && (
                  <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs px-2 py-0.5 rounded-full font-bold">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Engine Status Footer */}
      <div className="p-4 border-t border-slate-800">
        <button
          onClick={() => setCurrentTab('settings')}
          className={`w-full text-left p-3 rounded-xl border transition-all ${
            aiStatus?.connected
              ? 'bg-emerald-950/30 border-emerald-500/30 hover:bg-emerald-950/50'
              : 'bg-rose-950/30 border-rose-500/30 hover:bg-rose-950/50'
          }`}
          title="Click to manage GLM-5.3 credentials in Settings"
        >
          <div className="flex items-center space-x-2.5">
            <div className="relative flex h-2.5 w-2.5 flex-shrink-0">
              {aiStatus?.connected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span
                className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                  aiStatus?.connected ? 'bg-emerald-500' : 'bg-rose-500'
                }`}
              ></span>
            </div>
            <div className="text-xs overflow-hidden">
              <p
                className={`font-bold truncate text-[11px] ${
                  aiStatus?.connected ? 'text-emerald-400' : 'text-rose-400'
                }`}
              >
                {aiStatus?.connected
                  ? 'GLM-5.3 Engine: LIVE & CONNECTED'
                  : 'GLM-5.3: DISCONNECTED'}
              </p>
              <p className="text-[10px] text-slate-400 truncate mt-0.5">
                {aiStatus?.connected
                  ? `${aiStatus.model || 'glm-5.3'} Active`
                  : 'Real API Required (Click to Config)'}
              </p>
            </div>
          </div>
        </button>
      </div>
    </aside>
  );
};
