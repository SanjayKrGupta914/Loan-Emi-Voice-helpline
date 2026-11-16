import React, { useState, useEffect } from 'react';
import { AppLayout } from './layouts/AppLayout';
import { PageId } from './layouts/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { VoiceHelplinePage } from './pages/VoiceHelplinePage';
import { BorrowerManagementPage } from './pages/BorrowerManagementPage';
import { EMIManagementPage } from './pages/EMIManagementPage';
import { AgentArchitecturePage } from './pages/AgentArchitecturePage';
import { GuardrailsPage } from './pages/GuardrailsPage';
import { EvaluatePage } from './pages/EvaluatePage';
import { EscalationsPage } from './pages/EscalationsPage';
import { SettingsPage } from './pages/SettingsPage';
import { LoginPage } from './pages/LoginPage';
import { BorrowerPortalPage } from './pages/BorrowerPortalPage';
import { fetchSystemSettings, fetchEscalations, getStoredAuth, clearAuth, AuthUser } from './services/api';

export const App: React.FC = () => {
  const [user, setUser] = useState<AuthUser | null>(() => getStoredAuth()?.user ?? null);

  useEffect(() => {
    const onExpired = () => setUser(null);
    window.addEventListener('steadyhome-auth-expired', onExpired);
    return () => window.removeEventListener('steadyhome-auth-expired', onExpired);
  }, []);

  const logout = () => {
    clearAuth();
    setUser(null);
  };

  if (!user) return <LoginPage onLoggedIn={setUser} />;
  if (user.role === 'borrower') return <BorrowerPortalPage user={user} onLogout={logout} />;
  return <AdminApp user={user} onLogout={logout} />;
};

const AdminApp: React.FC<{ user: AuthUser; onLogout: () => void }> = ({ user, onLogout }) => {
  const [currentPage, setCurrentPage] = useState<PageId>('dashboard');
  const [simulatedClock, setSimulatedClock] = useState<string>('2026-11-10T09:00:00');
  const [escalationCount, setEscalationCount] = useState<number>(5);

  useEffect(() => {
    // Initial fetch of clock and escalations count
    fetchSystemSettings()
      .then((s) => {
        if (s && s.current_simulated_now) {
          setSimulatedClock(s.current_simulated_now);
        }
      })
      .catch((err) => console.warn('Settings load error:', err));

    fetchEscalations()
      .then((res) => {
        if (Array.isArray(res)) {
          setEscalationCount(res.length);
        }
      })
      .catch((err) => console.warn('Escalations load error:', err));
  }, []);

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardPage />;
      case 'helpline':
        return <VoiceHelplinePage />;
      case 'borrowers':
        return <BorrowerManagementPage />;
      case 'emis':
        return <EMIManagementPage />;
      case 'architecture':
        return <AgentArchitecturePage />;
      case 'guardrails':
        return <GuardrailsPage />;
      case 'evaluate':
        return <EvaluatePage />;
      case 'escalations':
        return <EscalationsPage />;
      case 'settings':
        return (
          <SettingsPage
            onClockChanged={(newClock) => setSimulatedClock(newClock)}
          />
        );
      default:
        return <DashboardPage />;
    }
  };

  return (
    <AppLayout
      currentPage={currentPage}
      onNavigate={(page) => setCurrentPage(page)}
      simulatedClock={simulatedClock}
      escalationCount={escalationCount}
      userName={user.name}
      onLogout={onLogout}
    >
      {renderCurrentPage()}
    </AppLayout>
  );
};

export default App;

