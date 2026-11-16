import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  User,
  RefreshCw,
  FileText,
} from 'lucide-react';
import { StatusBadge } from '../components/Badge';
import { Modal } from '../components/Modal';
import { fetchEscalations } from '../services/api';
import { EscalationItem } from '../types';

export const EscalationsPage: React.FC = () => {
  const [escalations, setEscalations] = useState<EscalationItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [selectedEsc, setSelectedEsc] = useState<EscalationItem | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await fetchEscalations();
      setEscalations(res || []);
    } catch (err) {
      console.error('Failed to load escalations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filtered = escalations.filter((e) => {
    if (!search) return true;
    const s = search.toLowerCase();
    return (
      e.escalation_id.toLowerCase().includes(s) ||
      (e.borrower_id && e.borrower_id.toLowerCase().includes(s)) ||
      e.reason.toLowerCase().includes(s) ||
      e.intent.toLowerCase().includes(s)
    );
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-borderCustom">
        <div>
          <h2 className="text-xl font-semibold text-primaryText tracking-tight">
            Human Agent Escalations Queue
          </h2>
          <p className="text-xs text-secondaryText mt-0.5">
            Specialized resolution queue for account blocks, high overdue (&gt;30 days), crisis, and customer requests.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-secondaryText">Active Cases:</span>
          <span className="font-mono text-xs font-semibold px-2 py-0.5 bg-brand-lightRed text-brand-red border border-brand-red/30 rounded">
            {escalations.length}
          </span>
          <button
            onClick={loadData}
            className="p-1.5 border border-borderCustom rounded hover:bg-background-secondary text-secondaryText"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="bg-white border border-borderCustom rounded-lg p-4 shadow-subtle flex items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-secondaryText" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by Escalation ID, Borrower, or Reason..."
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-borderCustom rounded bg-background-secondary/30 focus:bg-white focus:outline-none focus:border-brand-blue"
          />
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-borderCustom rounded-lg shadow-subtle overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-background-secondary text-secondaryText border-b border-borderCustom font-medium">
              <tr>
                <th className="py-3 px-4">Escalation ID</th>
                <th className="py-3 px-4">Borrower</th>
                <th className="py-3 px-4">Intent</th>
                <th className="py-3 px-4">Escalation Reason</th>
                <th className="py-3 px-4">Payment Mode</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-borderCustom text-primaryText">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-secondaryText">
                    Loading escalations...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-secondaryText">
                    No escalations in queue.
                  </td>
                </tr>
              ) : (
                filtered.map((esc) => (
                  <tr key={esc.escalation_id} className="hover:bg-background-secondary/40 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-brand-red">
                      {esc.escalation_id}
                    </td>
                    <td className="py-3 px-4 font-mono text-primaryText">
                      {esc.borrower_id || 'Unverified'}
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-secondaryText">
                      {esc.intent}
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate" title={esc.reason}>
                      {esc.reason}
                    </td>
                    <td className="py-3 px-4 text-secondaryText">
                      {esc.payment_mode || '--'}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={esc.status} />
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-secondaryText">
                      {esc.timestamp.replace('T', ' ').slice(0, 16)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedEsc(esc)}
                        className="px-2.5 py-1 bg-white border border-borderCustom hover:border-brand-blue text-brand-blue rounded text-[11px] font-medium transition-colors"
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Escalation Details Modal */}
      <Modal
        isOpen={!!selectedEsc}
        onClose={() => setSelectedEsc(null)}
        title={`Escalation Dossier – ${selectedEsc?.escalation_id || ''}`}
        subtitle={`Borrower: ${selectedEsc?.borrower_id || 'Unverified'}`}
        maxWidth="max-w-xl"
      >
        {selectedEsc && (
          <div className="space-y-4 text-xs">
            <div className="p-3 bg-background-secondary/50 border border-borderCustom rounded space-y-2">
              <div className="flex justify-between">
                <span className="text-secondaryText">Intent Tag:</span>
                <span className="font-mono font-medium text-primaryText">{selectedEsc.intent}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondaryText">Payment Mode:</span>
                <span className="text-primaryText">{selectedEsc.payment_mode || 'None'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-secondaryText">Status:</span>
                <StatusBadge status={selectedEsc.status} />
              </div>
              <div className="flex justify-between">
                <span className="text-secondaryText">Logged At:</span>
                <span className="font-mono text-primaryText">{selectedEsc.timestamp}</span>
              </div>
            </div>

            <div>
              <span className="font-semibold text-primaryText block mb-1">Escalation Reason:</span>
              <div className="p-2.5 bg-brand-lightRed/20 border border-brand-red/30 rounded text-brand-red font-medium">
                {selectedEsc.reason}
              </div>
            </div>

            <div>
              <span className="font-semibold text-primaryText block mb-1">Handoff Conversation Summary:</span>
              <div className="p-3 bg-white border border-borderCustom rounded text-secondaryText leading-relaxed">
                {selectedEsc.conversation_summary || 'Transferred by SteadyHome Voice Helpline engine.'}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
