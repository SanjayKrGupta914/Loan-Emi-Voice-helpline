import React, { useEffect, useState } from 'react';
import { Building2, LogOut, Headphones, Home, Calendar, IndianRupee, AlertTriangle, Loader2 } from 'lucide-react';
import { Badge } from '../components/Badge';
import { VoiceHelplinePage } from './VoiceHelplinePage';
import { fetchPortal, AuthUser } from '../services/api';

interface Props {
  user: AuthUser;
  onLogout: () => void;
}

const inr = (n: number) => `₹${Math.round(n).toLocaleString('en-IN')}`;
const fmtDate = (iso?: string) =>
  iso ? new Date(iso).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : '--';

const statusVariant = (s: string): 'green' | 'orange' | 'red' | 'gray' =>
  s === 'PAID' || s === 'ACTIVE' ? 'green' : s === 'PENDING' ? 'orange' : s === 'OVERDUE' || s === 'DEFAULT' ? 'red' : 'gray';

export const BorrowerPortalPage: React.FC<Props> = ({ user, onLogout }) => {
  const [data, setData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<'loan' | 'helpline'>('loan');

  useEffect(() => {
    fetchPortal().then(setData).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="min-h-screen bg-background-secondary/40 text-primaryText">
      <header className="bg-white border-b border-borderCustom">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-blue text-white flex items-center justify-center">
              <Building2 size={17} />
            </div>
            <span className="font-semibold tracking-tight">SteadyHome</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-xs font-semibold leading-none">{user.name}</div>
              <div className="text-[10px] text-secondaryText mt-0.5 font-mono">{user.borrower_id}</div>
            </div>
            <button onClick={onLogout}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-borderCustom rounded hover:bg-background-secondary">
              <LogOut size={13} /> Sign out
            </button>
          </div>
        </div>
        <div className="max-w-6xl mx-auto px-4 flex gap-1 text-xs font-semibold">
          {([['loan', 'My Loan', Home], ['helpline', 'AI Helpline', Headphones]] as const).map(([id, label, Icon]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-4 py-2.5 flex items-center gap-1.5 border-b-2 ${
                tab === id ? 'border-brand-blue text-brand-blue' : 'border-transparent text-secondaryText hover:text-primaryText'}`}>
              <Icon size={14} /> {label}
            </button>
          ))}
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-5">
        {tab === 'helpline' && (
          <>
            <p className="text-xs text-secondaryText">
              Talk to the SteadyHome AI assistant. It will ask you to verify your identity again, as on a real phone call.
            </p>
            <VoiceHelplinePage />
          </>
        )}

        {tab === 'loan' && !data && !error && (
          <div className="flex items-center gap-2 text-sm text-secondaryText"><Loader2 size={16} className="animate-spin" /> Loading your loan details…</div>
        )}
        {tab === 'loan' && error && (
          <div className="p-3 text-sm text-brand-red bg-brand-lightRed border border-brand-red/30 rounded">{error}</div>
        )}

        {tab === 'loan' && data && (
          <>
            <div>
              <h1 className="text-xl font-semibold tracking-tight">Welcome, {data.borrower.name}</h1>
              <p className="text-xs text-secondaryText mt-0.5">
                As of {fmtDate(data.simulated_now)} · {data.borrower.email} · {data.borrower.phone}
              </p>
            </div>

            {data.loans.map((loan: any) => {
              const nextEmi = loan.emis.find((e: any) => e.payment_status !== 'PAID');
              const overdue = loan.emis.filter((e: any) => e.days_overdue > 0 && e.payment_status !== 'PAID');
              return (
                <section key={loan.loan_id} className="space-y-4">
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {[
                      { label: 'Loan amount', value: inr(loan.amount), icon: IndianRupee },
                      { label: 'Monthly EMI', value: inr(loan.emi_amount), icon: IndianRupee },
                      { label: 'Next due date', value: fmtDate(nextEmi?.due_date || loan.next_due_date), icon: Calendar },
                      { label: 'Late fees', value: inr(loan.total_late_fees), icon: AlertTriangle },
                    ].map((c) => (
                      <div key={c.label} className="bg-white border border-borderCustom rounded-lg p-4 shadow-subtle">
                        <div className="flex items-center gap-1.5 text-[11px] text-secondaryText"><c.icon size={12} />{c.label}</div>
                        <div className="mt-1 text-lg font-semibold">{c.value}</div>
                      </div>
                    ))}
                  </div>

                  {overdue.length > 0 && (
                    <div className="p-3 text-xs bg-brand-lightOrange border border-brand-orange/30 rounded text-primaryText">
                      <span className="font-semibold">Payment overdue:</span> {overdue.length} EMI{overdue.length > 1 ? 's are' : ' is'} overdue.
                      {overdue.some((e: any) => e.needs_human_help)
                        ? ' Please contact a customer care representative through the AI Helpline to resolve this.'
                        : ' Late fees apply until it is paid. Use the AI Helpline for part-payment options.'}
                    </div>
                  )}

                  <div className="bg-white border border-borderCustom rounded-lg shadow-subtle overflow-hidden">
                    <div className="px-4 py-3 border-b border-borderCustom flex flex-wrap items-center justify-between gap-2">
                      <div className="text-sm font-semibold">Loan {loan.loan_id}</div>
                      <div className="flex items-center gap-2 text-[11px] text-secondaryText">
                        <Badge variant={statusVariant(loan.status)} size="sm">{loan.status}</Badge>
                        <span>{loan.interest_rate}% p.a.</span>·<span>{loan.tenure_months} months</span>·<span>Sanctioned {fmtDate(loan.sanction_date)}</span>
                      </div>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead className="bg-background-secondary text-secondaryText text-left">
                          <tr>
                            {['EMI', 'Due date', 'Amount', 'Mode', 'Status', 'Days overdue', 'Late fee'].map((h) => (
                              <th key={h} className="px-4 py-2 font-medium whitespace-nowrap">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {loan.emis.map((e: any) => (
                            <tr key={e.emi_id} className="border-t border-borderCustom">
                              <td className="px-4 py-2 font-mono">{e.emi_id}</td>
                              <td className="px-4 py-2">{fmtDate(e.due_date)}</td>
                              <td className="px-4 py-2 font-medium">{inr(e.amount)}</td>
                              <td className="px-4 py-2">{e.payment_mode}</td>
                              <td className="px-4 py-2"><Badge variant={statusVariant(e.payment_status)} size="sm">{e.payment_status}</Badge></td>
                              <td className="px-4 py-2 font-mono">{e.payment_status === 'PAID' ? '--' : e.days_overdue}</td>
                              <td className="px-4 py-2 font-mono">{e.late_fee ? inr(e.late_fee) : '--'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </section>
              );
            })}
          </>
        )}
      </main>
    </div>
  );
};
