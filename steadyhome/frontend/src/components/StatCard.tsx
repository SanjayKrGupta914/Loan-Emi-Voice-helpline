import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  badge?: string;
  badgeVariant?: 'blue' | 'green' | 'orange' | 'red';
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  badge,
  badgeVariant = 'green',
}) => {
  return (
    <div className="bg-white border border-borderCustom rounded-lg p-4 shadow-subtle flex flex-col justify-between">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-secondaryText uppercase tracking-wider">
          {title}
        </span>
        {Icon && (
          <div className="w-8 h-8 rounded bg-background-secondary flex items-center justify-center text-brand-blue">
            <Icon size={16} />
          </div>
        )}
      </div>
      <div>
        <div className="text-2xl font-semibold text-primaryText tracking-tight">
          {value}
        </div>
        <div className="flex items-center gap-2 mt-1.5">
          {badge && (
            <span
              className={`text-[11px] font-medium px-1.5 py-0.5 rounded ${
                badgeVariant === 'green'
                  ? 'bg-brand-lightGreen text-brand-green'
                  : badgeVariant === 'orange'
                  ? 'bg-brand-lightOrange text-brand-orange'
                  : badgeVariant === 'red'
                  ? 'bg-brand-lightRed text-brand-red'
                  : 'bg-brand-lightBlue text-brand-blue'
              }`}
            >
              {badge}
            </span>
          )}
          {subtitle && (
            <span className="text-xs text-secondaryText truncate">{subtitle}</span>
          )}
        </div>
      </div>
    </div>
  );
};

