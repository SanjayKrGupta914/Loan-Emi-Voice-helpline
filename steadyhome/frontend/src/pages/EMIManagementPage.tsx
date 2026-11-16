import React, { useState, useEffect } from 'react';
import {
  CreditCard,
  Search,
  Filter,
  Calculator,
  Calendar,
  AlertCircle,
  RefreshCw,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { StatusBadge } from '../components/Badge';
import { Modal } from '../components/Modal';
import { fetchEMIs, calculateLateFeeDirect } from '../services/api';
import { EMIItem } from '../types';

export const EMIManagementPage: React.FC = () => {
  const [emis, setEmis] = useState<EMIItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [modeFilter, setModeFilter] = useState<string>('ALL');

  // Breakdown modal
  const [selectedEMI, setSelectedEMI] = useState<EMIItem | null>(null);
  const [calcResult, setCalcResult] = useState<any | null>(null);
  const [calculating, setCalculating] = useState<boolean>(false);

  const loadEMIs = async () => {
    try {
      setLoading(true);
      const res = await fetchEMIs(statusFilter, modeFilter);
      setEmis(res.emis || []);
    } catch (err) {
      console.error('Failed to load EMIs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEMIs();
  }, [statusFilter, modeFilter]);

  const handleInspect = async (emi: EMIItem) => {
    setSelectedEMI(emi);
    try {
      setCalculating(true);
      const res = await calculateLateFeeDirect(emi.emi_amount, emi.due_date, emi.payment_status);
      setCalcResult(res);
    } catch (err) {
      console.error('Calculation error:', err);
    } finally {
      setCalculating(false);
    }
  };

  const filteredEMIs = emis.filter((e) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      e.emi_id.toLowerCase().includes(s) ||
      e.loan_id.toLowerCase().includes(s) ||
      e.borrower_id.toLowerCase().includes(s)
    );
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-borderCustom">
        <div>
          <h2 className="text-xl font-semibold text-primaryText tracking-tight">
            EMI Schedule & Collections Desk
          </h2>
          <p className="text-xs text-secondaryText mt-0.5">
            Audit upcoming, paid, and overdue installments against banking rules.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-secondaryText">Total Schedules:</span>
          <span className="font-mono text-xs font-semibold px-2 py-0.5 bg-white border border-borderCustom rounded">
            {filteredEMIs.length}
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white border border-borderCustom rounded-lg p-4 shadow-subtle flex flex-wrap items-center justify-between gap-4">
        <div className="relative w-full sm:w-72">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondaryText" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search EMI, Loan, or Borrower ID..."
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-borderCustom rounded bg-background-secondary/30 focus:bg-white focus:outline-none focus:border-brand-blue"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-secondaryText">
            <Filter size={13} />
            <span>Status:</span>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs border border-borderCustom rounded bg-white text-primaryText focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">PENDING</option>
            <option value="OVERDUE">OVERDUE</option>
            <option value="PAID">PAID</option>
          </select>

          <div className="flex items-center gap-1.5 text-xs text-secondaryText">
            <span>Mode:</span>
          </div>
          <select
            value={modeFilter}
            onChange={(e) => setModeFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs border border-borderCustom rounded bg-white text-primaryText focus:outline-none"
          >
            <option value="ALL">All Modes</option>
            <option value="AutoDebit">AutoDebit</option>
            <option value="NetPay">NetPay</option>
            <option value="Branch Cash Desk">Branch Cash Desk</option>
            <option value="KiteWallet">KiteWallet</option>
          </select>

          <button
            onClick={loadEMIs}
            className="p-1.5 border border-borderCustom rounded hover:bg-background-secondary text-secondaryText"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-borderCustom rounded-lg shadow-subtle overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-background-secondary text-secondaryText border-b border-borderCustom font-medium">
              <tr>
                <th className="py-3 px-4">EMI ID</th>
                <th className="py-3 px-4">Loan ID</th>
                <th className="py-3 px-4">Borrower</th>
                <th className="py-3 px-4">EMI Amount</th>
                <th className="py-3 px-4">Due Date</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Days Overdue</th>
                <th className="py-3 px-4">Late Fee</th>
                <th className="py-3 px-4">Payment Mode</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-borderCustom text-primaryText">
              {loading ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-secondaryText">
                    Loading EMI schedule...
                  </td>
                </tr>
              ) : filteredEMIs.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-8 text-center text-secondaryText">
                    No EMI schedules match the selected filters.
                  </td>
                </tr>
              ) : (
                filteredEMIs.map((e) => (
                  <tr key={e.emi_id} className="hover:bg-background-secondary/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-brand-blue">
                      {e.emi_id}
                    </td>
                    <td className="py-3 px-4 font-mono text-secondaryText">
                      {e.loan_id}
                    </td>
                    <td className="py-3 px-4 font-mono font-medium text-primaryText">
                      {e.borrower_id}
                    </td>
                    <td className="py-3 px-4 font-semibold">
                      ₹{e.emi_amount.toLocaleString('en-IN')}
                    </td>
                    <td className="py-3 px-4 font-mono text-secondaryText">
                      {e.due_date}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={e.payment_status} />
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {e.days_overdue > 0 ? (
                        <span className="text-brand-orange font-semibold">
                          +{e.days_overdue} days
                        </span>
                      ) : (
                        <span className="text-secondaryText">0 days</span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono font-medium">
                      {e.late_fee > 0 ? `₹${e.late_fee}` : '₹0'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded bg-background-secondary text-primaryText text-[11px] font-medium border border-borderCustom">
                        {e.payment_mode}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleInspect(e)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 bg-white border border-borderCustom hover:border-brand-blue text-brand-blue rounded text-[11px] font-medium transition-colors"
                      >
                        <Calculator size={12} />
                        <span>Inspect Breakdown</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Breakdown Modal */}
      <Modal
        isOpen={!!selectedEMI}
        onClose={() => setSelectedEMI(null)}
        title={`Late Fee Breakdown – ${selectedEMI?.emi_id || ''}`}
        subtitle={`Loan Reference: ${selectedEMI?.loan_id || ''}`}
        maxWidth="max-w-xl"
      >
        {selectedEMI && (
          <div className="space-y-4 text-xs">
            <div className="p-3 bg-background-secondary/50 border border-borderCustom rounded space-y-2">
              <div className="flex justify-between">
                <span className="text-secondaryText">Borrower ID:</span>
                <span className="font-mono font-medium text-primaryText">{selectedEMI.borrower_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondaryText">Monthly Installment:</span>
                <span className="font-semibold text-primaryText">₹{selectedEMI.emi_amount.toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondaryText">Due Date:</span>
                <span className="font-mono text-primaryText">{selectedEMI.due_date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondaryText">Payment Status:</span>
                <StatusBadge status={selectedEMI.payment_status} />
              </div>
            </div>

            {calculating ? (
              <div className="py-4 text-center text-secondaryText">
                Evaluating late fee calculation rules...
              </div>
            ) : calcResult ? (
              <div className="space-y-3">
                <div className="p-4 bg-white border border-borderCustom rounded space-y-2">
                  <div className="text-xs font-semibold text-primaryText pb-1 border-b border-borderCustom">
                    Rule-Based Calculation Details (Section 5.E)
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondaryText">Days Overdue (Simulated):</span>
                    <span className="font-mono font-semibold text-primaryText">{calcResult.days_overdue} days</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondaryText">Applicable Fee Tier:</span>
                    <span className="font-semibold text-brand-blue">{calcResult.late_fee_percentage}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-secondaryText">Late Fee Calculated:</span>
                    <span className="font-bold text-sm text-brand-orange">₹{calcResult.late_fee_amount}</span>
                  </div>
                  <div className="flex justify-between pt-1 border-t border-borderCustom">
                    <span className="text-secondaryText">Online Resolution Permitted:</span>
                    <span className={`font-semibold ${calcResult.can_process_online ? 'text-brand-green' : 'text-brand-red'}`}>
                      {calcResult.can_process_online ? 'YES (Self-Service)' : 'NO (> 30 days overdue; Human Agent required)'}
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-brand-lightBlue border border-brand-blueSecondary/30 rounded text-brand-blue text-[11px]">
                  <strong>System Message:</strong> {calcResult.message}
                </div>
              </div>
            ) : null}
          </div>
        )}
      </Modal>
    </div>
  );
};

