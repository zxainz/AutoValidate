import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { FindingDetailModal } from './components/FindingDetailModal';
import { Dashboard } from './pages/Dashboard';
import { FindingsPage } from './pages/FindingsPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';
import { Finding, DashboardMetrics, AIStatus } from './types';
import { api } from './services/api';
import { wsClient } from './services/websocket';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'dashboard' | 'findings' | 'reports' | 'settings'>('dashboard');
  const [findings, setFindings] = useState<Finding[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [findingsData, metricsData] = await Promise.all([
        api.getFindings(),
        api.getMetrics(),
      ]);
      setFindings(findingsData);
      setMetrics(metricsData);
    } catch (e) {
      console.error('Error fetching data:', e);
    }
  }, []);

  const loadAiStatus = useCallback(async () => {
    try {
      const status = await api.getAIStatus();
      setAiStatus(status);
    } catch (e) {
      console.error('Error fetching AI status:', e);
    }
  }, []);

  useEffect(() => {
    loadData();
    loadAiStatus();

    // Subscribe to WebSocket events
    const unsubscribe = wsClient.subscribe((data) => {
      if (data.type === 'progress') {
        setIsValidating(true);
      } else if (data.type === 'completed') {
        setIsValidating(false);
        loadData();
      }
    });

    return () => unsubscribe();
  }, [loadData, loadAiStatus]);

  const handleStartValidation = async (ids: number[] = []) => {
    setIsValidating(true);
    try {
      await api.startValidation(ids);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to start validation');
      setIsValidating(false);
    }
  };

  const handleClearAll = async () => {
    if (window.confirm('Are you sure you want to delete all findings and start fresh?')) {
      await api.clearAllFindings();
      await loadData();
    }
  };

  const handleGenerateReport = async () => {
    setCurrentTab('reports');
  };

  return (
    <div className="flex bg-[#0a0f1d] min-h-screen text-slate-100 font-sans">
      {/* Navigation Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        unverifiedCount={metrics?.unverified_findings || 0}
        aiStatus={aiStatus}
      />

      {/* Main Workspace */}
      <main className="flex-1 p-8 overflow-y-auto max-w-7xl mx-auto w-full">
        {currentTab === 'dashboard' && (
          <Dashboard
            metrics={metrics}
            findings={findings}
            isValidating={isValidating}
            aiStatus={aiStatus}
            onRefresh={loadData}
            onSelectFinding={setSelectedFinding}
            onStartValidation={handleStartValidation}
            onClearAll={handleClearAll}
            onGenerateReport={handleGenerateReport}
            onNavigateSettings={() => setCurrentTab('settings')}
          />
        )}

        {currentTab === 'findings' && (
          <FindingsPage
            findings={findings}
            isValidating={isValidating}
            aiStatus={aiStatus}
            onRefresh={loadData}
            onSelectFinding={setSelectedFinding}
            onStartValidation={handleStartValidation}
            onClearAll={handleClearAll}
          />
        )}

        {currentTab === 'reports' && <ReportsPage />}

        {currentTab === 'settings' && (
          <SettingsPage
            onSettingsUpdated={() => {
              loadData();
              loadAiStatus();
            }}
          />
        )}
      </main>

      {/* Deep-Dive Investigation Modal */}
      {selectedFinding && (
        <FindingDetailModal
          finding={selectedFinding}
          onClose={() => setSelectedFinding(null)}
          onUpdated={() => {
            loadData();
            // Refresh modal finding
            api.getFinding(selectedFinding.id).then(setSelectedFinding);
          }}
        />
      )}
    </div>
  );
};

export default App;
