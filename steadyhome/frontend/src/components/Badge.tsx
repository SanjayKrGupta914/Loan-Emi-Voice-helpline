import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'blue' | 'green' | 'orange' | 'red' | 'gray';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'blue',
  size = 'md',
}) => {
  const variantStyles = {
    blue: 'bg-brand-lightBlue text-brand-blue border-brand-blueSecondary/30',
    green: 'bg-brand-lightGreen text-brand-green border-brand-green/30',
    orange: 'bg-brand-lightOrange text-brand-orange border-brand-orange/30',
    red: 'bg-brand-lightRed text-brand-red border-brand-red/30',
    gray: 'bg-gray-100 text-secondaryText border-borderCustom',
  };

  const sizeStyles = {
    sm: 'px-1.5 py-0.5 text-[11px]',
    md: 'px-2 py-0.5 text-xs',
  };

  return (
    <span
      className={`inline-flex items-center font-medium border rounded ${sizeStyles[size]} ${variantStyles[variant]}`}
    >
      {children}
    </span>
  );
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const s = (status || '').toUpperCase();

  if (['ACTIVE', 'PAID', 'SUCCESS', 'VERIFIED', 'RESOLVED', 'PASSED'].includes(s)) {
    return <Badge variant="green">{status}</Badge>;
  }
  if (['PENDING', 'OVERDUE', 'ASSIGNED'].includes(s)) {
    return <Badge variant="orange">{status}</Badge>;
  }
  if (['BLOCKED', 'CLOSED', 'DEFAULT', 'FAILED', 'FAILED_VERIFICATION', 'REJECTED'].includes(s)) {
    return <Badge variant="red">{status}</Badge>;
  }
  if (['INITIATED', 'ESCALATED', 'SPECIALIST', 'PRIMARY'].includes(s)) {
    return <Badge variant="blue">{status}</Badge>;
  }
  return <Badge variant="gray">{status || 'UNKNOWN'}</Badge>;
};

