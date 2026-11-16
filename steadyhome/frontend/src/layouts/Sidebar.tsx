import React from 'react';
import {
  LayoutDashboard,
  Headphones,
  Users,
  CreditCard,
  Network,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Settings,
  Building2,
} from 'lucide-react';

export type PageId =
  | 'dashboard'
  | 'helpline'
  | 'borrowers'
  | 'emis'
  | 'architecture'
  | 'guardrails'
  | 'evaluate'
  | 'escalations'
  | 'settings';

interface SidebarProps {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
  escalationCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  escalationCount = 5,
}) => {
  const navItems = [
    { id: 'dashboard' as PageId, label: 'Overview', icon: LayoutDashboard },
    { id: 'helpline' as PageId, label: 'AI Voice Helpline', icon: Headphones, highlight: true },
    { id: 'borrowers' as PageId, label: 'Borrowers', icon: Users },
    { id: 'emis' as PageId, label: 'EMI Management', icon: CreditCard },
    { id: 'architecture' as PageId, label: 'Agent Architecture', icon: Network },
    { id: 'guardrails' as PageId, label: 'Guardrails & Safety', icon: ShieldCheck },
    { id: 'evaluate' as PageId, label: 'Evaluate & Testing', icon: CheckCircle2 },
    {
      id: 'escalations' as PageId,
      label: 'Escalations',
      icon: AlertTriangle,
      badge: escalationCount > 0 ? String(escalationCount) : undefined,
    },
    { id: 'settings' as PageId, label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-white border-r border-borderCustom flex flex-col h-screen select-none shrink-0">
      {/* Brand & Wordmark */}
      <div className="h-16 px-5 border-b border-borderCustom flex items-center gap-3">
        <div className="w-9 h-9 rounded bg-brand-blue flex items-center justify-center text-white shadow-sm">
          <Building2 size={20} />
        </div>
        <div>
          <div className="font-semibold text-[15px] text-primaryText tracking-tight">
            SteadyHome
          </div>
          <div className="text-[11px] text-secondaryText leading-tight">
            Loan EMI Voice Helpline
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-2 pb-2 text-[11px] font-semibold text-secondaryText uppercase tracking-wider">
          Main Menu
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded text-[13px] transition-colors ${
                isActive
                  ? 'bg-brand-lightBlue text-brand-blue font-medium'
                  : 'text-secondaryText hover:text-primaryText hover:bg-background-secondary'
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon
                  size={16}
                  className={isActive ? 'text-brand-blue' : 'text-secondaryText'}
                />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="bg-brand-lightRed text-brand-red text-[11px] font-semibold px-1.5 py-0.2 rounded-full border border-brand-red/20">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Institutional Footer */}
      <div className="p-4 border-t border-borderCustom bg-background-secondary/50">
        <div className="text-[11px] text-secondaryText flex items-center justify-between">
          <span>System Version</span>
          <span className="font-mono text-primaryText">v2.4.10-IN</span>
        </div>
        <div className="text-[11px] text-secondaryText flex items-center justify-between mt-1">
          <span>Core Banking</span>
          <span className="text-brand-green font-medium flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-green"></span> Connected
          </span>
        </div>
      </div>
    </aside>
  );
};

