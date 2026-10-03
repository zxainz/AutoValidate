import React, { useState, useEffect } from 'react';
import { SettingsConfig, AIStatus } from '../types';
import { api } from '../services/api';
import { Settings, Save, CheckCircle, Key, Server, RefreshCw } from 'lucide-react';

interface SettingsPageProps {
  onSettingsUpdated?: () => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ onSettingsUpdated }) => {
  const [config, setConfig] = useState<SettingsConfig | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('https://api.z.ai/api/coding/paas/v4');
  const [modelName, setModelName] = useState('glm-5.3');
  const [reasoningEffort, setReasoningEffort] = useState('max');
  const [temperature, setTemperature] = useState(0.2);

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<AIStatus | null>(null);
  const [success, setSuccess] = useState(false);
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setConfig(data);
      setModelName(data.model_name || 'glm-5.3');
      setBaseUrl(data.base_url || 'https://api.z.ai/api/coding/paas/v4');
      setReasoningEffort(data.reasoning_effort || 'max');
      setTemperature(data.temperature ?? 0.2);

      // Check live status
      const status = await api.getAIStatus();
      setTestResult(status);
    } catch (e) {
      console.error(e);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    try {
      const result = await api.testAiConnection({
        api_key: apiKey.trim() || undefined,
        base_url: baseUrl.trim() || undefined,
        model_name: modelName.trim() || undefined,
      });
      setTestResult(result);
    } catch (err: any) {
      setTestResult({
        connected: false,
        status: 'error',
        message: err.response?.data?.detail || err.message || 'Connection test failed',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);
    try {
      const res = await api.updateSettings({
        zai_api_key: apiKey.trim() || undefined,
        zai_base_url: baseUrl.trim() || undefined,
        model_name: modelName.trim() || undefined,
        reasoning_effort: reasoningEffort,
        temperature: temperature,
      });
      setSuccess(true);
      setApiKey('');
      if (res.connection_status) {
        setTestResult(res.connection_status);
      }
      await loadSettings();
      if (onSettingsUpdated) {
        onSettingsUpdated();
      }
      setTimeout(() => setSuccess(false), 3000);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="border-b border-slate-800 pb-4">
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <Settings className="w-5 h-5 text-sky-400" />
          GLM-5.3 Live API Configuration
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          AutoValidate Pro operates <strong className="text-amber-400">exclusively on live GLM-5.3 API calls</strong>. All offline simulations and mock modes are disabled.
        </p>
      </div>

      {/* Live Status Banner */}
      <div
        className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
          testResult?.connected
            ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
            : 'bg-rose-950/20 border-rose-500/30 text-rose-300'
        }`}
      >
        <div className="flex items-center space-x-3">
          <div className="relative flex h-3 w-3 flex-shrink-0">
            {testResult?.connected && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            )}
            <span
              className={`relative inline-flex rounded-full h-3 w-3 ${
                testResult?.connected ? 'bg-emerald-500' : 'bg-rose-500'
              }`}
            ></span>
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider">
              {testResult?.connected
                ? 'GLM-5.3 Engine: LIVE & CONNECTED'
                : 'GLM-5.3 Engine: DISCONNECTED (Real API Key Required)'}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              {testResult?.message || 'Checking connection status...'}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleTestConnection}
          disabled={testing}
          className="flex items-center space-x-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3 py-1.5 rounded-lg transition disabled:opacity-50 flex-shrink-0"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${testing ? 'animate-spin' : ''}`} />
          <span>{testing ? 'Testing...' : 'Test Connection'}</span>
        </button>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* API Credentials */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Key className="w-4 h-4 text-sky-400" />
            Z.ai API Key
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Z.ai GLM-5.3 API Key <span className="text-rose-400">*</span>
              </label>
              <div className="relative flex items-center">
                <input
                  type={showKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={config?.api_key_configured ? `Current Key: ${config.masked_api_key}` : 'Enter your Z.ai API key...'}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-4 pr-20 py-2.5 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 text-[11px] text-slate-400 hover:text-slate-200 uppercase font-semibold"
                >
                  {showKey ? 'Hide' : 'Show'}
                </button>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Your key is stored securely in your local environment. Leave empty to preserve your current key.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  API Base URL
                </label>
                <input
                  type="text"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Model Identifier
                </label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono"
                  required
                />
              </div>
            </div>
          </div>
        </div>

        {/* Reasoning Parameters */}
        <div className="bg-[#111827] border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
          <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Server className="w-4 h-4 text-sky-400" />
            Reasoning Hyperparameters
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Reasoning Effort
              </label>
              <select
                value={reasoningEffort}
                onChange={(e) => setReasoningEffort(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-sky-500"
              >
                <option value="max">Max (Deep Technical Triage)</option>
                <option value="high">High (Balanced)</option>
                <option value="low">Low (Fast Response)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Temperature ({temperature})
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-sky-500 cursor-pointer"
              />
              <span className="text-[10px] text-slate-500">Lower temperature ensures deterministic, defensible pentest validation.</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-2">
          {success && (
            <div className="flex items-center space-x-1.5 text-xs text-emerald-400">
              <CheckCircle className="w-4 h-4" />
              <span>Settings successfully updated!</span>
            </div>
          )}
          {!success && <div />}

          <button
            type="submit"
            disabled={saving}
            className="flex items-center space-x-2 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white text-xs font-semibold px-6 py-2.5 rounded-xl shadow-lg shadow-sky-500/20 transition disabled:opacity-50 ml-auto"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? 'Saving...' : 'Save Configuration'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
