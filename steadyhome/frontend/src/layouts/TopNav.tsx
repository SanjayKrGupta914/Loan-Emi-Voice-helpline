import React from 'react';
import { Clock, LogOut } from 'lucide-react';
import { PageId } from './Sidebar';

interface TopNavProps {
  currentPage: PageId;
  simulatedClock: string;
  onSearch?: (term: string) => void;
  onOpenSettings?: () => void;
  userName?: string;
  onLogout?: () => void;
}

export const TopNav: React.FC<TopNavProps> = ({
  currentPage,
  simulatedClock,
  onOpenSettings,
  userName = 'Administrator',
  onLogout,
}) => {
  const pageTitles: Record<PageId, { title: string; breadcrumb: string }> = {
    dashboard: { title: 'SteadyHome Operations Overview', breadcrumb: 'Banking Dashboard / Operations' },
    helpline: { title: 'AI Voice Helpline – Live Call Center', breadcrumb: 'Helpline / Voice & Audio Dispatch' },
    borrowers: { title: 'Borrower Portfolio Management', breadcrumb: 'Loan Operations / Borrowers' },
    emis: { title: 'EMI Schedule & Collections Desk', breadcrumb: 'Loan Operations / EMIs' },
    architecture: { title: 'Root Agent & EMI Sub-Agent Architecture', breadcrumb: 'AI Infrastructure / Topology' },
    guardrails: { title: 'Safety Guardrails & Regulatory Compliance', breadcrumb: 'Compliance & Safety / Guardrails' },
    evaluate: { title: 'Evaluation Dashboard & Automated Test Suite', breadcrumb: 'QA & Engineering / Test Suite' },
    escalations: { title: 'Human Agent Escalations Queue', breadcrumb: 'Call Center / Escalations' },
    settings: { title: 'System Configuration & Simulated Clock', breadcrumb: 'Configuration / Settings' },
  };

  const currentInfo = pageTitles[currentPage] || { title: 'SteadyHome', breadcrumb: 'Home' };

  const formatClock = (iso: string) => {
    try {
      const dt = new Date(iso);
      return dt.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });
    } catch (_) {
      return iso;
    }
  };

  return (
    <header className="h-16 bg-white border-b border-borderCustom px-6 flex items-center justify-between shrink-0">
      {/* Title & Breadcrumb */}
      <div>
        <div className="text-[11px] font-medium text-secondaryText tracking-wide">
          {currentInfo.breadcrumb}
        </div>
        <h1 className="text-lg font-semibold text-primaryText tracking-tight">
          {currentInfo.title}
        </h1>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3">
        {/* Simulated Clock Badge */}
        <button
          onClick={onOpenSettings}
          title="Click to adjust simulated clock reference"
          className="flex items-center gap-1.5 px-2.5 py-1.5 bg-background-secondary border border-borderCustom rounded text-xs text-primaryText hover:border-brand-blue transition-colors"
        >
          <Clock size={13} className="text-brand-blue" />
          <span className="font-mono text-[11px] font-medium">
            Simulated: {formatClock(simulatedClock)}
          </span>
        </button>

        {/* DEMO MODE Indicator (Section 16 requirement) */}
        <div className="flex items-center gap-1.5 px-2 py-1 bg-brand-lightGreen text-brand-green border border-brand-green/30 rounded text-[11px] font-semibold tracking-wide">
          <span className="w-1.5 h-1.5 rounded-full bg-brand-green animate-pulse"></span>
          DEMO MODE
        </div>

        {/* Signed-in user */}
        <div className="flex items-center gap-2 pl-3 border-l border-borderCustom">
          <div className="w-7 h-7 rounded-full bg-brand-lightBlue text-brand-blue flex items-center justify-center font-semibold text-xs border border-brand-blueSecondary/30">
            {userName.slice(0, 2).toUpperCase()}
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-semibold text-primaryText leading-none">{userName}</div>
            <div className="text-[10px] text-secondaryText mt-0.5 leading-none">Bank Operations</div>
          </div>
          {onLogout && (
            <button onClick={onLogout} title="Sign out"
              className="ml-1 p-1.5 text-secondaryText border border-borderCustom rounded hover:text-brand-red hover:border-brand-red/40">
              <LogOut size={14} />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

