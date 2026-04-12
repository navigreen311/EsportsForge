/**
 * Admin Support — open tickets table with status filtering and expandable rows.
 */

'use client';

import { useState } from 'react';
import { LifeBuoy, ChevronDown, ChevronRight } from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Types & mock data                                                  */
/* ------------------------------------------------------------------ */

interface Ticket {
  id: string;
  date: string;
  user: string;
  subject: string;
  status: 'open' | 'in_progress' | 'resolved';
  priority: 'low' | 'medium' | 'high';
  details: string;
}

const MOCK_TICKETS: Ticket[] = [
  {
    id: 'TKT-001',
    date: '2026-04-12',
    user: 'AlexGrind',
    subject: 'ForgeCore chat not loading on mobile',
    status: 'open',
    priority: 'high',
    details: 'User reports the ForgeCore chat component fails to render on iOS Safari. No errors in console. Happens consistently after the latest app update. Device: iPhone 15 Pro, iOS 19.2.',
  },
  {
    id: 'TKT-002',
    date: '2026-04-11',
    user: 'JMoney99',
    subject: 'Billing charged twice for Competitive tier',
    status: 'in_progress',
    priority: 'high',
    details: 'User was charged $9.99 twice on April 10. Payment IDs: txn_a1b2c3 and txn_d4e5f6. Stripe dashboard confirms duplicate. Refund initiated for second charge, awaiting processing.',
  },
  {
    id: 'TKT-003',
    date: '2026-04-10',
    user: 'SamSlam',
    subject: 'Can\'t link Xbox account for data import',
    status: 'open',
    priority: 'medium',
    details: 'User attempts to link Xbox Live account via settings page. OAuth flow redirects back but no account appears linked. User has tried clearing cookies and using incognito mode.',
  },
  {
    id: 'TKT-004',
    date: '2026-04-08',
    user: 'MorganFPS',
    subject: 'LoopAI debrief shows wrong game data',
    status: 'resolved',
    priority: 'medium',
    details: 'LoopAI was pulling data from a previous Warzone session instead of the latest one. Root cause: session timestamp collision in the cache layer. Fix deployed in v1.3.8.',
  },
  {
    id: 'TKT-005',
    date: '2026-04-07',
    user: 'RileyDubs',
    subject: 'Feature request: dark mode toggle',
    status: 'resolved',
    priority: 'low',
    details: 'User requests ability to toggle between dark and light themes. Noted as a feature request. Dark mode is currently the default and only theme. Added to backlog for consideration.',
  },
];

const STATUS_BADGE: Record<Ticket['status'], { label: string; className: string }> = {
  open:        { label: 'Open',        className: 'bg-red-500/10 text-red-400' },
  in_progress: { label: 'In Progress', className: 'bg-amber-500/10 text-amber-400' },
  resolved:    { label: 'Resolved',    className: 'bg-green-500/10 text-green-400' },
};

const PRIORITY_BADGE: Record<Ticket['priority'], string> = {
  low:    'bg-dark-700 text-dark-300',
  medium: 'bg-amber-500/10 text-amber-400',
  high:   'bg-red-500/10 text-red-400',
};

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function AdminSupportPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = MOCK_TICKETS.filter(
    (t) => statusFilter === 'all' || t.status === statusFilter,
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <LifeBuoy className="h-6 w-6 text-forge-400" />
        <h1 className="text-2xl font-bold text-dark-50">Support</h1>
        <span className="ml-auto text-sm text-dark-400">
          {filtered.length} ticket{filtered.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Status filter */}
      <div className="flex gap-2">
        {(['all', 'open', 'in_progress', 'resolved'] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
              statusFilter === s
                ? 'bg-forge-400/10 text-forge-400'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700 hover:text-dark-100'
            }`}
          >
            {s === 'all' ? 'All' : s === 'in_progress' ? 'In Progress' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Tickets Table */}
      <div className="overflow-x-auto rounded-xl border border-dark-700/60 bg-dark-900">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700/60 text-left text-xs text-dark-400">
              <th className="w-8 px-4 py-3" />
              <th className="px-4 py-3 font-medium">ID</th>
              <th className="px-4 py-3 font-medium">Date</th>
              <th className="px-4 py-3 font-medium">User</th>
              <th className="px-4 py-3 font-medium">Subject</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Priority</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((t) => {
              const isExpanded = expandedId === t.id;
              const s = STATUS_BADGE[t.status];
              return (
                <>
                  <tr
                    key={t.id}
                    onClick={() => setExpandedId(isExpanded ? null : t.id)}
                    className="cursor-pointer border-b border-dark-700/30 transition-colors hover:bg-dark-800/40"
                  >
                    <td className="px-4 py-3 text-dark-500">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4" />
                      ) : (
                        <ChevronRight className="h-4 w-4" />
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-dark-400">{t.id}</td>
                    <td className="px-4 py-3 text-dark-300">{t.date}</td>
                    <td className="px-4 py-3 font-medium text-dark-100">{t.user}</td>
                    <td className="px-4 py-3 text-dark-100">{t.subject}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${s.className}`}>
                        {s.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${PRIORITY_BADGE[t.priority]}`}>
                        {t.priority}
                      </span>
                    </td>
                  </tr>
                  {isExpanded && (
                    <tr key={`${t.id}-details`} className="border-b border-dark-700/30">
                      <td colSpan={7} className="bg-dark-800/30 px-8 py-4">
                        <p className="text-xs font-medium text-dark-400">Details</p>
                        <p className="mt-1 text-sm text-dark-300">{t.details}</p>
                      </td>
                    </tr>
                  )}
                </>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-dark-500">
                  No tickets match this filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
