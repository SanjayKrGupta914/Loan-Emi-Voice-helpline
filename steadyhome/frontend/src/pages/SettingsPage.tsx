import React, { useState, useEffect } from 'react';
import {
  Clock,
  RotateCcw,
  CheckCircle2,
  CloudSun,
  Shield,
  Sliders,
  RefreshCw,
  Calendar,
  Save,
} from 'lucide-react';
import {
  fetchSystemSettings,
  updateSimulatedClock,
  resetSimulatedClock,
  fetchAdvisory,
  fetchIntegrationsStatus,
} from '../services/api';

interface SettingsPageProps {
  onClockChanged: (newClock: string) => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ onClockChanged }) => {
  const [currentClock, setCurrentClock] = useState<string>('2026-11-10T09:00:00');
  const [clockInput, setClockInput] = useState<string>('2026-11-10T09:00:00');
  const [settingsData, setSettingsData] = useState<any | null>(null);
  const [advisoryData, setAdvisoryData] = useState<any | null>(null);
  const [useMockAdvisory, setUseMockAdvisory] = useState<boolean>(false);
  const [city, setCity] = useState<string>('Mumbai');
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [integrations, setIntegrations] = useState<any | null>(null);

  const loadData = async () => {
    try {
      const s = await fetchSystemSettings();
      setSettingsData(s);
      setCurrentClock(s.current_simulated_now);
      setClockInput(s.current_simulated_now);

      const adv = await fetchAdvisory(city, useMockAdvisory);
      setAdvisoryData(adv);
    } catch (err) {
      console.error('Failed to load settings:', err);
    }
  };

  useEffect(() => {
    fetchIntegrationsStatus().then(setIntegrations).catch(() => setIntegrations(null));
  }, []);

  useEffect(() => {
    loadData();
  }, [useMockAdvisory, city]);

  const handleSaveClock = async () => {
    setLoading(true);
    try {
      const res = await updateSimulatedClock(clockInput);
      if (res && res.current_simulated_now) {
        setCurrentClock(res.current_simulated_now);
        onClockChanged(res.current_simulated_now);
        setMessage('Simulated clock updated successfully.');
        setTimeout(() => setMessage(null), 3000);
      }
    } catch (err: any) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleResetClock = async () => {
    setLoading(true);
    try {
      const res = await resetSimulatedClock();
      if (res && res.current_simulated_now) {
        setCurrentClock(res.current_simulated_now);
        setClockInput(res.current_simulated_now);
        onClockChanged(res.current_simulated_now);
        setMessage('Simulated clock reset to default: 10 November 2026, 09:00.');
        setTimeout(() => setMessage(null), 3000);
      }
    } catch (err: any) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn max-w-4xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-borderCustom">
        <div>
          <h2 className="text-xl font-semibold text-primaryText tracking-tight">
            System Configuration & Simulated Clock Settings
          </h2>
          <p className="text-xs text-secondaryText mt-0.5">
            Configure simulated reference time, payment-day advisory APIs, and banking policy parameters.
          </p>
        </div>
      </div>

      {message && (
        <div className="p-3 bg-brand-lightGreen border border-brand-green/30 text-brand-green rounded text-xs font-medium animate-fadeIn">
          {message}
        </div>
      )}

      {/* 0. Integrations: Gemini + Supabase */}
      <div className="bg-white border border-borderCustom rounded-lg p-6 shadow-subtle space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-borderCustom">
          <Shield size={16} className="text-brand-blue" />
          <h3 className="text-sm font-semibold text-primaryText">Integrations</h3>
        </div>
        {(['gemini', 'supabase'] as const).map((key) => {
          const st = integrations?.[key];
          const ok = st && st.configured && st.reachable && st.tables_ok !== false;
          return (
            <div key={key} className="flex items-start justify-between gap-3 text-xs">
              <div>
                <div className="font-semibold text-primaryText">
                  {key === 'gemini' ? 'Gemini (speech understanding)' : 'Supabase (cloud persistence)'}
                </div>
                <div className="text-secondaryText">{st ? st.detail : 'Backend unreachable'}</div>
              </div>
              <span className={`px-2 py-0.5 rounded font-semibold ${ok ? 'bg-brand-lightGreen text-brand-green' : 'bg-brand-lightOrange text-brand-orange'}`}>
                {ok ? 'CONNECTED' : st && !st.configured ? 'NOT CONFIGURED' : 'ATTENTION'}
              </span>
            </div>
          );
        })}
      </div>

      {/* 1. Simulated Clock Section (Section 5.I) */}
      <div className="bg-white border border-borderCustom rounded-lg p-6 shadow-subtle space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-borderCustom">
          <Clock size={16} className="text-brand-blue" />
          <h3 className="text-sm font-semibold text-primaryText">
            Simulated Clock Reference (Section 5.I)
          </h3>
        </div>

        <p className="text-xs text-secondaryText leading-relaxed">
          SteadyHome evaluates all date-based business rules—including overdue days, late fee tiers, and the 1 January 2027 NetPay Plus / Cash Desk cutoff—against this configurable reference clock. System never relies on host machine date.
        </p>

        <div className="p-4 bg-background-secondary/50 border border-borderCustom rounded-lg space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <span className="text-[11px] text-secondaryText block">Active Reference Time:</span>
              <span className="font-mono text-sm font-semibold text-brand-blue">
                {currentClock}
              </span>
            </div>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-white border border-borderCustom text-secondaryText">
              Default: 2026-11-10T09:00:00
            </span>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-2 pt-2">
            <input
              type="text"
              value={clockInput}
              onChange={(e) => setClockInput(e.target.value)}
              placeholder="YYYY-MM-DDTHH:MM:SS"
              className="flex-1 px-3 py-1.5 text-xs font-mono border border-borderCustom rounded bg-white focus:outline-none focus:border-brand-blue"
            />
            <button
              onClick={handleSaveClock}
              disabled={loading}
              className="px-4 py-1.5 bg-brand-blue text-white rounded text-xs font-medium hover:bg-brand-blue/90 disabled:opacity-50 flex items-center gap-1.5"
            >
              <Save size={13} />
              <span>Update Clock</span>
            </button>
            <button
              onClick={handleResetClock}
              disabled={loading}
              className="px-3 py-1.5 bg-white border border-borderCustom hover:bg-background-secondary text-secondaryText hover:text-primaryText rounded text-xs flex items-center gap-1.5"
            >
              <RotateCcw size={13} />
              <span>Reset Default</span>
            </button>
          </div>

          <div className="flex flex-wrap gap-2 pt-1 text-[11px] text-secondaryText">
            <span>Quick Presets:</span>
            <button
              onClick={() => setClockInput('2026-11-10T09:00:00')}
              className="underline hover:text-brand-blue font-mono"
            >
              10-Nov-2026 (Default)
            </button>
            <span>•</span>
            <button
              onClick={() => setClockInput('2026-12-31T15:00:00')}
              className="underline hover:text-brand-blue font-mono"
            >
              31-Dec-2026 (Cash Desk Last Day)
            </button>
            <span>•</span>
            <button
              onClick={() => setClockInput('2027-01-01T10:00:00')}
              className="underline hover:text-brand-blue font-mono"
            >
              01-Jan-2027 (NetPay Plus Active)
            </button>
          </div>
        </div>
      </div>

      {/* 2. Payment-Day Advisory API (Section 8) */}
      <div className="bg-white border border-borderCustom rounded-lg p-6 shadow-subtle space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-borderCustom">
          <CloudSun size={16} className="text-brand-orange" />
          <h3 className="text-sm font-semibold text-primaryText">
            Payment-Day Advisory Public API Integration (Section 8)
          </h3>
        </div>

        <p className="text-xs text-secondaryText leading-relaxed">
          Integrates with free HTTPS JSON API (Open-Meteo) to provide non-binding, contextual advisories about regional banking clearing networks and weather without affecting loan eligibility.
        </p>

        <div className="p-4 bg-background-secondary/50 border border-borderCustom rounded-lg space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-secondaryText">Target Center:</span>
              <select
                value={city}
                onChange={(e) => setCity(e.target.value)}
                className="px-2 py-1 text-xs border border-borderCustom rounded bg-white text-primaryText"
              >
                <option value="Mumbai">Mumbai (HQ)</option>
                <option value="New Delhi">New Delhi</option>
                <option value="Bengaluru">Bengaluru</option>
                <option value="Chennai">Chennai</option>
              </select>
            </div>

            <label className="flex items-center gap-2 text-xs text-secondaryText cursor-pointer">
              <input
                type="checkbox"
                checked={useMockAdvisory}
                onChange={(e) => setUseMockAdvisory(e.target.checked)}
                className="rounded border-borderCustom text-brand-blue"
              />
              <span>Force Deterministic Mock Fallback</span>
            </label>
          </div>

          {advisoryData && (
            <div className="p-3 bg-white border border-borderCustom rounded space-y-1 text-xs">
              <div className="flex justify-between text-[11px] text-secondaryText pb-1 border-b border-borderCustom">
                <span>Source: {advisoryData.source}</span>
                <span>Conditions: {advisoryData.weather_condition} ({advisoryData.temperature_c}°C)</span>
              </div>
              <p className="text-primaryText font-medium pt-1">
                "{advisoryData.advisory}"
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 3. Core Institutional Parameters Summary */}
      <div className="bg-white border border-borderCustom rounded-lg p-6 shadow-subtle space-y-3">
        <div className="flex items-center gap-2 pb-2 border-b border-borderCustom">
          <Shield size={16} className="text-brand-green" />
          <h3 className="text-sm font-semibold text-primaryText">
            Institutional Policy Thresholds (Locked by Governance)
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 bg-background-secondary/40 border border-borderCustom rounded">
            <span className="text-[11px] text-secondaryText block">Minimum Part-Payment:</span>
            <span className="font-semibold text-primaryText text-sm">₹500</span>
            <span className="text-[10px] text-secondaryText block mt-0.5">Below ₹500 is rejected</span>
          </div>
          <div className="p-3 bg-background-secondary/40 border border-borderCustom rounded">
            <span className="text-[11px] text-secondaryText block">Late Fee Tiers:</span>
            <span className="font-semibold text-primaryText text-sm">2% (1-5d) & 4% (6-30d)</span>
            <span className="text-[10px] text-secondaryText block mt-0.5">Round to nearest rupee</span>
          </div>
          <div className="p-3 bg-background-secondary/40 border border-borderCustom rounded">
            <span className="text-[11px] text-secondaryText block">Human Escalation Limit:</span>
            <span className="font-semibold text-primaryText text-sm">&gt; 30 Days Overdue</span>
            <span className="text-[10px] text-secondaryText block mt-0.5">Online resolution disabled</span>
          </div>
        </div>
      </div>
    </div>
  );
};

