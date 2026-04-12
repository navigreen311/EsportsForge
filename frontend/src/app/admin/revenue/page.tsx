/**
 * Admin Revenue — MRR, subscriptions, cancellations, revenue by tier,
 * and recent transactions.
 */

'use client';

import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  CreditCard,
  AlertTriangle,
} from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Mock data                                                          */
/* ------------------------------------------------------------------ */

const REVENUE_METRICS = [
  { label: 'Monthly Recurring Revenue', value: '$87,420',  change: '+$4,200 MoM', icon: DollarSign,   color: 'text-forge-400',  bg: 'bg-forge-400/10' },
  { label: 'New Subscriptions',         value: '218',      change: '+12% this month', icon: TrendingUp, color: 'text-green-400',  bg: 'bg-green-400/10' },
  { label: 'Cancellations',             value: '34',       change: '-8% vs last month', icon: TrendingDown, color: 'text-amber-400', bg: 'bg-amber-400/10' },
  { label: 'Failed Payments',           value: '7',        change: '0.6% failure rate', icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-400/10' },
];

const REVENUE_BY_TIER = [
  { tier: 'Free',        users: 6412,  revenue: '$0',      share: '0%' },
  { tier: 'Competitive', users: 4180,  revenue: '$41,800',  share: '47.8%' },
  { tier: 'Elite',       users: 1890,  revenue: '$37,800',  share: '43.3%' },
  { tier: 'Team',        users: 365,   revenue: '$7,820',   share: '8.9%' },
];

interface Transaction {
  id: string;
  user: string;
  type: 'subscription' | 'upgrade' | 'refund' | 'renewal';
  amount: string;
  tier: string;
  date: string;
}

const RECENT_TRANSACTIONS: Transaction[] = [
  { id: 'txn_001', user: 'AlexGrind',    type: 'renewal',      amount: '$19.99',  tier: 'Elite',       date: '2026-04-12' },
  { id: 'txn_002', user: 'JMoney99',     type: 'upgrade',      amount: '$9.99',   tier: 'Competitive', date: '2026-04-12' },
  { id: 'txn_003', user: 'SamSlam',      type: 'subscription', amount: '$9.99',   tier: 'Competitive', date: '2026-04-11' },
  { id: 'txn_004', user: 'MorganFPS',    type: 'refund',       amount: '-$9.99',  tier: 'Competitive', date: '2026-04-11' },
  { id: 'txn_005', user: 'TaylorMade',   type: 'renewal',      amount: '$29.99',  tier: 'Team',        date: '2026-04-10' },
  { id: 'txn_006', user: 'CaseyW',       type: 'subscription', amount: '$19.99',  tier: 'Elite',       date: '2026-04-10' },
  { id: 'txn_007', user: 'DrewChamp',    type: 'upgrade',      amount: '$19.99',  tier: 'Elite',       date: '2026-04-09' },
];

const TXN_BADGE: Record<Transaction['type'], string> = {
  subscription: 'bg-green-500/10 text-green-400',
  upgrade:      'bg-blue-500/10 text-blue-400',
  refund:       'bg-red-500/10 text-red-400',
  renewal:      'bg-forge-400/10 text-forge-400',
};

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function AdminRevenuePage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <DollarSign className="h-6 w-6 text-forge-400" />
        <h1 className="text-2xl font-bold text-dark-50">Revenue</h1>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {REVENUE_METRICS.map((m) => {
          const Icon = m.icon;
          return (
            <div
              key={m.label}
              className="rounded-xl border border-dark-700/60 bg-dark-900 p-5"
            >
              <div className="flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${m.bg}`}>
                  <Icon className={`h-5 w-5 ${m.color}`} />
                </div>
                <div>
                  <p className="text-xs text-dark-400">{m.label}</p>
                  <p className="text-xl font-bold text-dark-50">{m.value}</p>
                </div>
              </div>
              <p className="mt-3 text-xs text-dark-400">{m.change}</p>
            </div>
          );
        })}
      </div>

      {/* Revenue by Tier */}
      <div className="rounded-xl border border-dark-700/60 bg-dark-900 p-5">
        <h2 className="mb-4 text-sm font-semibold text-dark-100">Revenue by Tier</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700/60 text-left text-xs text-dark-400">
                <th className="px-4 py-3 font-medium">Tier</th>
                <th className="px-4 py-3 font-medium">Users</th>
                <th className="px-4 py-3 font-medium">Revenue</th>
                <th className="px-4 py-3 font-medium">Share</th>
              </tr>
            </thead>
            <tbody>
              {REVENUE_BY_TIER.map((row) => (
                <tr
                  key={row.tier}
                  className="border-b border-dark-700/30 transition-colors hover:bg-dark-800/40"
                >
                  <td className="px-4 py-3 font-medium text-dark-100">{row.tier}</td>
                  <td className="px-4 py-3 text-dark-300">{row.users.toLocaleString()}</td>
                  <td className="px-4 py-3 text-dark-100">{row.revenue}</td>
                  <td className="px-4 py-3 text-dark-300">{row.share}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Transactions */}
      <div className="rounded-xl border border-dark-700/60 bg-dark-900 p-5">
        <div className="mb-4 flex items-center gap-2">
          <CreditCard className="h-5 w-5 text-dark-300" />
          <h2 className="text-sm font-semibold text-dark-100">Recent Transactions</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700/60 text-left text-xs text-dark-400">
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">User</th>
                <th className="px-4 py-3 font-medium">Type</th>
                <th className="px-4 py-3 font-medium">Amount</th>
                <th className="px-4 py-3 font-medium">Tier</th>
                <th className="px-4 py-3 font-medium">Date</th>
              </tr>
            </thead>
            <tbody>
              {RECENT_TRANSACTIONS.map((txn) => (
                <tr
                  key={txn.id}
                  className="border-b border-dark-700/30 transition-colors hover:bg-dark-800/40"
                >
                  <td className="px-4 py-3 font-mono text-xs text-dark-400">{txn.id}</td>
                  <td className="px-4 py-3 font-medium text-dark-100">{txn.user}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${TXN_BADGE[txn.type]}`}>
                      {txn.type}
                    </span>
                  </td>
                  <td className={`px-4 py-3 font-medium ${txn.type === 'refund' ? 'text-red-400' : 'text-dark-100'}`}>
                    {txn.amount}
                  </td>
                  <td className="px-4 py-3 text-dark-300">{txn.tier}</td>
                  <td className="px-4 py-3 text-dark-300">{txn.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
