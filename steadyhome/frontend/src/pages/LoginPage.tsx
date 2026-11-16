import React, { useState } from 'react';
import { Building2, ShieldCheck, UserRound, Lock, Loader2, Info } from 'lucide-react';
import { adminLogin, borrowerLogin, storeAuth, AuthUser } from '../services/api';

interface LoginPageProps {
  onLoggedIn: (user: AuthUser) => void;
}

const DEMO_ADMIN = { username: 'admin', password: 'SteadyAdmin@2026' };
const DEMO_BORROWER = { id: 'SH-BOR-1001', dob: '1985-06-15', last4: '1001' };

const inputCls =
  'w-full px-3 py-2 text-sm border border-borderCustom rounded bg-white focus:outline-none focus:border-brand-blue focus:ring-1 focus:ring-brand-blue/30';
const labelCls = 'block text-xs font-medium text-primaryText mb-1';

export const LoginPage: React.FC<LoginPageProps> = ({ onLoggedIn }) => {
  const [mode, setMode] = useState<'borrower' | 'admin'>('borrower');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [borrowerId, setBorrowerId] = useState('');
  const [dob, setDob] = useState('');
  const [last4, setLast4] = useState('');

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res =
        mode === 'borrower'
          ? await borrowerLogin(borrowerId.trim(), dob, last4.trim())
          : await adminLogin(username.trim(), password);
      storeAuth(res.token, res.user);
      onLoggedIn(res.user);
    } catch (err: any) {
      setError(err.message || 'Sign-in failed.');
    } finally {
      setBusy(false);
    }
  };

  const switchMode = (m: 'borrower' | 'admin') => {
    setMode(m);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-background-secondary flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-brand-blue text-white flex items-center justify-center shadow-subtle">
            <Building2 size={24} />
          </div>
          <h1 className="mt-3 text-xl font-semibold text-primaryText tracking-tight">SteadyHome Home Loans</h1>
          <p className="text-xs text-secondaryText mt-0.5">Sign in to view your loan and EMI details</p>
        </div>

        <div className="bg-white border border-borderCustom rounded-lg shadow-subtle overflow-hidden">
          <div className="grid grid-cols-2 text-xs font-semibold border-b border-borderCustom">
            {(['borrower', 'admin'] as const).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => switchMode(m)}
                className={`py-3 flex items-center justify-center gap-1.5 transition-colors ${
                  mode === m
                    ? 'text-brand-blue bg-brand-lightBlue border-b-2 border-brand-blue'
                    : 'text-secondaryText hover:bg-background-secondary'
                }`}
              >
                {m === 'borrower' ? <UserRound size={14} /> : <ShieldCheck size={14} />}
                {m === 'borrower' ? 'Borrower' : 'Administrator'}
              </button>
            ))}
          </div>

          <form onSubmit={submit} className="p-6 space-y-4">
            {mode === 'borrower' ? (
              <>
                <p className="text-xs text-secondaryText leading-relaxed">
                  For your security we verify three details before showing any loan information.
                </p>
                <div>
                  <label className={labelCls} htmlFor="bid">Borrower ID</label>
                  <input id="bid" className={inputCls} placeholder="SH-BOR-1001" value={borrowerId}
                    onChange={(e) => setBorrowerId(e.target.value)} required autoComplete="off" />
                </div>
                <div>
                  <label className={labelCls} htmlFor="dob">Date of birth</label>
                  <input id="dob" type="date" className={inputCls} value={dob}
                    onChange={(e) => setDob(e.target.value)} required />
                </div>
                <div>
                  <label className={labelCls} htmlFor="l4">Last 4 digits of loan number</label>
                  <input id="l4" className={inputCls} placeholder="1001" inputMode="numeric" maxLength={4}
                    pattern="\d{4}" title="Enter exactly 4 digits" value={last4}
                    onChange={(e) => setLast4(e.target.value.replace(/\D/g, ''))} required autoComplete="off" />
                </div>
              </>
            ) : (
              <>
                <p className="text-xs text-secondaryText leading-relaxed">
                  Bank operations console: dashboard, borrowers, escalations and the AI helpline.
                </p>
                <div>
                  <label className={labelCls} htmlFor="u">Username</label>
                  <input id="u" className={inputCls} value={username}
                    onChange={(e) => setUsername(e.target.value)} required autoComplete="username" />
                </div>
                <div>
                  <label className={labelCls} htmlFor="p">Password</label>
                  <input id="p" type="password" className={inputCls} value={password}
                    onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
                </div>
              </>
            )}

            {error && (
              <div role="alert" className="px-3 py-2 text-xs text-brand-red bg-brand-lightRed border border-brand-red/30 rounded">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full py-2.5 bg-brand-blue text-white text-sm font-medium rounded hover:bg-brand-blue/90 disabled:opacity-60 flex items-center justify-center gap-2"
            >
              {busy ? <Loader2 size={15} className="animate-spin" /> : <Lock size={14} />}
              {mode === 'borrower' ? 'View my loan' : 'Sign in as administrator'}
            </button>

            <div className="flex items-start gap-2 p-3 bg-brand-lightBlue border border-brand-blueSecondary/30 rounded text-[11px] text-secondaryText">
              <Info size={13} className="text-brand-blue shrink-0 mt-0.5" />
              <div className="flex-1">
                <span className="font-semibold text-primaryText">Demo mode.</span>{' '}
                {mode === 'borrower' ? (
                  <>Sample borrower SH-BOR-1001 · 1985-06-15 · 1001.</>
                ) : (
                  <>Sample login admin / SteadyAdmin@2026.</>
                )}{' '}
                <button
                  type="button"
                  className="text-brand-blue font-semibold underline"
                  onClick={() => {
                    if (mode === 'borrower') {
                      setBorrowerId(DEMO_BORROWER.id); setDob(DEMO_BORROWER.dob); setLast4(DEMO_BORROWER.last4);
                    } else {
                      setUsername(DEMO_ADMIN.username); setPassword(DEMO_ADMIN.password);
                    }
                  }}
                >
                  Fill demo details
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
