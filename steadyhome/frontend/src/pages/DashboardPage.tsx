import React, { useState, useEffect } from 'react';
import {
  Users,
  CreditCard,
  Clock,
  CheckCircle2,
  IndianRupee,
  AlertTriangle,
  RefreshCw,
  Calendar,
  ArrowUpRight,
  TrendingUp,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { StatCard } from '../components/StatCard';
import { StatusBadge } from '../components/Badge';
import { fetchDashboard } from '../services/api';
import { DashboardStats, CollectionTrend, PaymentModeDist, LoanStatusDist, RecentInteraction, EscalationItem } from '../types';

export const DashboardPage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [collectionTrends, setCollectionTrends] = useState<CollectionTrend[]>([]);
  const [paymentModeDist, setPaymentModeDist] = useState<PaymentModeDist[]>([]);
  const [loanStatusDist, setLoanStatusDist] = useState<LoanStatusDist[]>([]);
  const [recentInteractions, setRecentInteractions] = useState<RecentInteraction[]>([]);
  const [recentEscalations, setRecentEscalations] = useState<EscalationItem[]>([]);
  const [filterPeriod, setFilterPeriod] = useState<string>('Q4 2026');

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await fetchDashboard();
      setStats(data.stats);
      setCollectionTrends(data.collection_trends || []);
      setPaymentModeDist(data.payment_mode_distribution || []);
      setLoanStatusDist(data.loan_status_distribution || []);
      setRecentInteractions(data.recent_interactions || []);
      setRecentEscalations(data.recent_escalations || []);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatINR = (val: number) => {
    if (val >= 10000000) {
      return `₹${(val / 10000000).toFixed(2)} Cr`;
    }
    if (val >= 100000) {
      return `₹${(val / 100000).toFixed(2)} L`;
    }
    return `₹${val.toLocaleString('en-IN')}`;
  };

  const PIE_COLORS = ['#315E9E', '#6D91BE', '#24865B', '#D99A32', '#D9534F'];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-borderCustom">
        <div>
          <h2 className="text-xl font-semibold text-primaryText tracking-tight">
            SteadyHome Operations Overview
          </h2>
          <p className="text-xs text-secondaryText mt-0.5">
            Monitor loan activity, EMI collections, and customer-support operations.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-borderCustom rounded text-xs text-secondaryText">
            <Calendar size={13} className="text-brand-blue" />
            <span className="font-medium text-primaryText">Fiscal Period:</span>
            <span>{filterPeriod}</span>
          </div>
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-borderCustom rounded text-xs text-primaryText hover:bg-background-secondary transition-colors"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin text-brand-blue' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* 6 Statistic Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          title="Total Borrowers"
          value={stats?.total_borrowers ?? '--'}
          subtitle="Registered accounts"
          icon={Users}
          badge="+12% YoY"
          badgeVariant="blue"
        />
        <StatCard
          title="Active Loans"
          value={stats?.active_loans ?? '--'}
          subtitle="Portfolios in repayment"
          icon={CreditCard}
          badge="Live"
          badgeVariant="green"
        />
        <StatCard
          title="Pending EMIs"
          value={stats?.pending_emis ?? '--'}
          subtitle="Current cycle due"
          icon={Clock}
          badge="Actionable"
          badgeVariant="orange"
        />
        <StatCard
          title="Successful Payments"
          value={stats?.successful_payments ?? '--'}
          subtitle="Cleared installments"
          icon={CheckCircle2}
          badge="98.2%"
          badgeVariant="green"
        />
        <StatCard
          title="Total Collections"
          value={stats ? formatINR(stats.total_collections) : '--'}
          subtitle="Settled funds"
          icon={IndianRupee}
          badge="INR"
          badgeVariant="blue"
        />
        <StatCard
          title="Human Escalations"
          value={stats?.human_escalations ?? '--'}
          subtitle="Agent handoffs"
          icon={AlertTriangle}
          badge={stats && stats.human_escalations > 0 ? 'Active Queue' : 'Zero'}
          badgeVariant="red"
        />
      </div>

      {/* Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* A. EMI Collection Trends */}
        <div className="lg:col-span-2 bg-white border border-borderCustom rounded-lg p-5 shadow-subtle">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-primaryText">
                EMI Collection Trends (FY 2026-27)
              </h3>
              <p className="text-[11px] text-secondaryText">
                Monthly comparison of successfully cleared vs outstanding EMIs
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-brand-green font-medium">
              <TrendingUp size={14} />
              <span>Real-time DB query</span>
            </div>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={collectionTrends} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#737B89' }} />
                <YAxis
                  tick={{ fontSize: 11, fill: '#737B89' }}
                  tickFormatter={(val) => `₹${val / 1000}k`}
                />
                <Tooltip
                  formatter={(val: any) => [`₹${Number(val).toLocaleString('en-IN')}`, '']}
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E8EBEF',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="collected" name="Collected (₹)" fill="#315E9E" radius={[4, 4, 0, 0]} />
                <Bar dataKey="pending" name="Pending (₹)" fill="#D99A32" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* B. Payment Mode Distribution */}
        <div className="bg-white border border-borderCustom rounded-lg p-5 shadow-subtle flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-primaryText">
              Payment Mode Distribution
            </h3>
            <p className="text-[11px] text-secondaryText mb-2">
              AutoDebit, NetPay, Cash Desk & legacy modes
            </p>
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={paymentModeDist}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={65}
                    paddingAngle={3}
                  >
                    {paymentModeDist.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderColor: '#E8EBEF',
                      borderRadius: '6px',
                      fontSize: '12px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="space-y-1.5 pt-2 border-t border-borderCustom">
            {paymentModeDist.map((item, i) => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }}
                  />
                  <span className="text-primaryText">{item.name}</span>
                </div>
                <span className="font-semibold text-secondaryText">{item.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Grid: Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* D. Recent Customer Interactions */}
        <div className="bg-white border border-borderCustom rounded-lg shadow-subtle overflow-hidden">
          <div className="px-5 py-4 border-b border-borderCustom flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-primaryText">
                Recent Customer Helpline Interactions
              </h3>
              <p className="text-[11px] text-secondaryText">
                Live interaction trace and intent classification
              </p>
            </div>
            <span className="text-[11px] font-medium text-brand-blue bg-brand-lightBlue px-2 py-0.5 rounded">
              Audited Logs
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-background-secondary text-secondaryText border-b border-borderCustom font-medium">
                <tr>
                  <th className="py-2.5 px-4">Borrower</th>
                  <th className="py-2.5 px-4">Event Type</th>
                  <th className="py-2.5 px-4">Agent Role</th>
                  <th className="py-2.5 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borderCustom text-primaryText">
                {recentInteractions.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-secondaryText">
                      No customer interactions recorded yet.
                    </td>
                  </tr>
                ) : (
                  recentInteractions.slice(0, 5).map((log) => (
                    <tr key={log.id} className="hover:bg-background-secondary/50">
                      <td className="py-2.5 px-4 font-mono font-medium text-brand-blue">
                        {log.borrower_id}
                      </td>
                      <td className="py-2.5 px-4">
                        <StatusBadge status={log.event_type} />
                      </td>
                      <td className="py-2.5 px-4 text-secondaryText">{log.agent_name}</td>
                      <td className="py-2.5 px-4 text-secondaryText font-mono text-[11px]">
                        {log.timestamp.replace('T', ' ').slice(0, 16)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* E. Recent Escalations */}
        <div className="bg-white border border-borderCustom rounded-lg shadow-subtle overflow-hidden">
          <div className="px-5 py-4 border-b border-borderCustom flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-primaryText">
                Human Agent Escalations Queue
              </h3>
              <p className="text-[11px] text-secondaryText">
                Cases requiring specialized manual resolution
              </p>
            </div>
            <span className="text-[11px] font-medium text-brand-red bg-brand-lightRed px-2 py-0.5 rounded">
              Priority Escalations
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-background-secondary text-secondaryText border-b border-borderCustom font-medium">
                <tr>
                  <th className="py-2.5 px-4">ID</th>
                  <th className="py-2.5 px-4">Borrower</th>
                  <th className="py-2.5 px-4">Reason</th>
                  <th className="py-2.5 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borderCustom text-primaryText">
                {recentEscalations.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-secondaryText">
                      No active escalations in queue.
                    </td>
                  </tr>
                ) : (
                  recentEscalations.slice(0, 5).map((esc) => (
                    <tr key={esc.escalation_id} className="hover:bg-background-secondary/50">
                      <td className="py-2.5 px-4 font-mono font-medium text-primaryText">
                        {esc.escalation_id}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-secondaryText">
                        {esc.borrower_id || 'Unverified'}
                      </td>
                      <td className="py-2.5 px-4 max-w-[200px] truncate" title={esc.reason}>
                        {esc.reason}
                      </td>
                      <td className="py-2.5 px-4">
                        <StatusBadge status={esc.status} />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

