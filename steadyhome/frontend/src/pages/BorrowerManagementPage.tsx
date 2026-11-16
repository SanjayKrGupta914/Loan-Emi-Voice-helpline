import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  User,
  CreditCard,
  Calendar,
  Eye,
  Building2,
  FileText,
  Phone,
  Mail,
  MapPin,
  RefreshCw,
} from 'lucide-react';
import { StatusBadge } from '../components/Badge';
import { Modal } from '../components/Modal';
import { fetchBorrowers, fetchBorrowerProfile } from '../services/api';
import { BorrowerItem } from '../types';

export const BorrowerManagementPage: React.FC = () => {
  const [borrowers, setBorrowers] = useState<BorrowerItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Profile modal state
  const [selectedBorrower, setSelectedBorrower] = useState<any | null>(null);
  const [modalLoading, setModalLoading] = useState<boolean>(false);

  const loadBorrowers = async () => {
    try {
      setLoading(true);
      const res = await fetchBorrowers(search, statusFilter);
      setBorrowers(res.borrowers || []);
    } catch (err) {
      console.error('Failed to load borrowers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const handler = setTimeout(() => {
      loadBorrowers();
    }, 250);
    return () => clearTimeout(handler);
  }, [search, statusFilter]);

  const handleOpenProfile = async (borrowerId: string) => {
    try {
      setModalLoading(true);
      const profile = await fetchBorrowerProfile(borrowerId);
      setSelectedBorrower(profile);
    } catch (err) {
      console.error('Failed to fetch profile:', err);
    } finally {
      setModalLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-borderCustom">
        <div>
          <h2 className="text-xl font-semibold text-primaryText tracking-tight">
            Borrower Portfolio Management
          </h2>
          <p className="text-xs text-secondaryText mt-0.5">
            Search, inspect loan profiles, EMI obligations, and account statuses.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-secondaryText">Total Records:</span>
          <span className="font-mono text-xs font-semibold px-2 py-0.5 bg-white border border-borderCustom rounded">
            {borrowers.length}
          </span>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white border border-borderCustom rounded-lg p-4 shadow-subtle flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondaryText" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by Borrower ID or Name..."
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-borderCustom rounded bg-background-secondary/30 focus:bg-white focus:outline-none focus:border-brand-blue"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="flex items-center gap-1.5 text-xs text-secondaryText">
            <Filter size={13} />
            <span>Account Status:</span>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 text-xs border border-borderCustom rounded bg-white text-primaryText focus:outline-none focus:border-brand-blue"
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="BLOCKED">BLOCKED</option>
          </select>
          <button
            onClick={loadBorrowers}
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
                <th className="py-3 px-4">Borrower ID</th>
                <th className="py-3 px-4">Borrower Name</th>
                <th className="py-3 px-4">Loan ID</th>
                <th className="py-3 px-4">Loan Amount</th>
                <th className="py-3 px-4">Loan Status</th>
                <th className="py-3 px-4">Account Status</th>
                <th className="py-3 px-4">Next EMI Date</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-borderCustom text-primaryText">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-secondaryText">
                    Loading borrower records...
                  </td>
                </tr>
              ) : borrowers.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-secondaryText">
                    No borrowers match the current search filters.
                  </td>
                </tr>
              ) : (
                borrowers.map((b) => (
                  <tr key={b.borrower_id} className="hover:bg-background-secondary/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-brand-blue">
                      {b.borrower_id}
                    </td>
                    <td className="py-3 px-4 font-medium text-primaryText">
                      {b.name}
                    </td>
                    <td className="py-3 px-4 font-mono text-secondaryText">
                      {b.loan_id || 'N/A'}
                    </td>
                    <td className="py-3 px-4 font-medium">
                      ₹{b.loan_amount.toLocaleString('en-IN')}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={b.loan_status} />
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={b.borrower_status} />
                    </td>
                    <td className="py-3 px-4 font-mono text-secondaryText">
                      {b.next_due_date}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleOpenProfile(b.borrower_id)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 bg-white border border-borderCustom hover:border-brand-blue text-brand-blue rounded text-[11px] font-medium transition-colors"
                      >
                        <Eye size={12} />
                        <span>View Profile</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Borrower Profile Modal */}
      <Modal
        isOpen={!!selectedBorrower}
        onClose={() => setSelectedBorrower(null)}
        title={`Borrower Profile – ${selectedBorrower?.name || ''}`}
        subtitle={`Borrower ID: ${selectedBorrower?.borrower_id || ''}`}
        maxWidth="max-w-3xl"
      >
        {selectedBorrower && (
          <div className="space-y-6 text-xs">
            {/* Identity & Status */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 bg-background-secondary/50 border border-borderCustom rounded">
              <div>
                <span className="text-[11px] text-secondaryText block">Full Name</span>
                <span className="font-semibold text-primaryText text-sm">{selectedBorrower.name}</span>
              </div>
              <div>
                <span className="text-[11px] text-secondaryText block">Date of Birth</span>
                <span className="font-mono text-primaryText">{selectedBorrower.date_of_birth}</span>
              </div>
              <div>
                <span className="text-[11px] text-secondaryText block">Status</span>
                <StatusBadge status={selectedBorrower.status} />
              </div>
              <div>
                <span className="text-[11px] text-secondaryText block">Phone</span>
                <span className="font-mono text-primaryText">{selectedBorrower.phone}</span>
              </div>
              <div>
                <span className="text-[11px] text-secondaryText block">Email</span>
                <span className="text-primaryText">{selectedBorrower.email}</span>
              </div>
              <div>
                <span className="text-[11px] text-secondaryText block">Address</span>
                <span className="text-secondaryText truncate block" title={selectedBorrower.address}>
                  {selectedBorrower.address}
                </span>
              </div>
            </div>

            {/* Active Loan Details */}
            {selectedBorrower.loans && selectedBorrower.loans.map((loan: any) => (
              <div key={loan.loan_id} className="space-y-3">
                <div className="flex items-center justify-between border-b border-borderCustom pb-1">
                  <div className="flex items-center gap-2">
                    <CreditCard size={14} className="text-brand-blue" />
                    <span className="font-semibold text-primaryText">
                      Home Loan: {loan.loan_id}
                    </span>
                  </div>
                  <StatusBadge status={loan.status} />
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 bg-white border border-borderCustom rounded">
                  <div>
                    <span className="text-[10px] text-secondaryText block">Sanctioned Amount</span>
                    <span className="font-semibold text-primaryText">₹{loan.amount.toLocaleString('en-IN')}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-secondaryText block">Monthly EMI</span>
                    <span className="font-semibold text-brand-blue">₹{loan.emi_amount.toLocaleString('en-IN')}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-secondaryText block">Interest Rate</span>
                    <span className="font-mono text-primaryText">{loan.interest_rate}% p.a.</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-secondaryText block">Tenure</span>
                    <span className="text-primaryText">{loan.tenure_months} months</span>
                  </div>
                </div>

                {/* EMI Schedule Table */}
                <div>
                  <h4 className="text-xs font-semibold text-primaryText mb-2">EMI Schedule & Clearance History</h4>
                  <div className="border border-borderCustom rounded overflow-hidden">
                    <table className="w-full text-left text-[11px]">
                      <thead className="bg-background-secondary text-secondaryText">
                        <tr>
                          <th className="py-2 px-3">EMI ID</th>
                          <th className="py-2 px-3">Amount</th>
                          <th className="py-2 px-3">Due Date</th>
                          <th className="py-2 px-3">Status</th>
                          <th className="py-2 px-3">Mode</th>
                          <th className="py-2 px-3">Late Fee</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-borderCustom">
                        {loan.emis && loan.emis.map((emi: any) => (
                          <tr key={emi.emi_id}>
                            <td className="py-2 px-3 font-mono">{emi.emi_id}</td>
                            <td className="py-2 px-3 font-medium">₹{emi.amount.toLocaleString('en-IN')}</td>
                            <td className="py-2 px-3 font-mono">{emi.due_date}</td>
                            <td className="py-2 px-3">
                              <StatusBadge status={emi.payment_status} />
                            </td>
                            <td className="py-2 px-3">{emi.payment_mode}</td>
                            <td className="py-2 px-3 font-mono">₹{emi.late_fee}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </div>
  );
};

