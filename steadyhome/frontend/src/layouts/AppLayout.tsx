import React, { useState } from 'react';
import { Sidebar, PageId } from './Sidebar';
import { TopNav } from './TopNav';

interface AppLayoutProps {
  currentPage: PageId;
  onNavigate: (page: PageId) => void;
  simulatedClock: string;
  escalationCount?: number;
  userName?: string;
  onLogout?: () => void;
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  currentPage,
  onNavigate,
  simulatedClock,
  escalationCount = 5,
  userName,
  onLogout,
  children,
}) => {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white text-primaryText antialiased">
      {/* Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onNavigate={onNavigate}
        escalationCount={escalationCount}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-background-secondary/30">
        <TopNav
          currentPage={currentPage}
          simulatedClock={simulatedClock}
          onOpenSettings={() => onNavigate('settings')}
          userName={userName}
          onLogout={onLogout}
        />

        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
};

