'use client';

import { Check, CreditCard, Download } from 'lucide-react';
import type { UserTier } from '@/types/auth';

interface SubscriptionManagementProps {
  currentTier: UserTier;
}

const tierData: Record<
  UserTier,
  { name: string; price: number; features: string[] }
> = {
  free: {
    name: 'Free Tier',
    price: 0,
    features: [
      'Single game title tracking',
      'Basic analytics dashboard',
      'Community meta reports',
      'Standard opponent scouting',
      'Limited drill library access',
    ],
  },
  competitive: {
    name: 'Competitive Tier',
    price: 19.99,
    features: [
      'Up to 3 game titles',
      'Full AI agent suite',
      'Advanced analytics & LoopAI',
      'Kill sheet generator',
      'Unlimited drill access',
      'ImpactRank tracking',
      'Priority opponent scouting',
    ],
  },
  elite: {
    name: 'Elite Tier',
    price: 49.99,
    features: [
      'All 11 game titles',
      'Everything in Competitive',
      'TournaOps tournament hub',
      'VoiceForge AI callouts',
      'ForgeVault replay storage',
      'Full ImpactRank analytics',
      'TransferAI cross-game insights',
      'Custom AI model tuning',
    ],
  },
  team: {
    name: 'Team Tier',
    price: 149.99,
    features: [
      'Everything in Elite',
      'Coach Portal & War Room',
      'SquadOps team management',
      '6 team member seats',
      'Team analytics & comparisons',
      'Shared gameplans & strategies',
      'Bulk opponent scouting',
      'Dedicated account manager',
    ],
  },
};

const upgradeCards: {
  tier: UserTier;
  price: string;
  tagline: string;
  missingFeatures: string[];
}[] = [
  {
    tier: 'elite',
    price: '$49.99/mo',
    tagline:
      'All 11 titles, TournaOps, VoiceForge, ForgeVault, full ImpactRank',
    missingFeatures: [
      'Unlock all 11 supported game titles',
      'VoiceForge AI callouts in real-time',
      'ForgeVault cloud replay storage',
    ],
  },
  {
    tier: 'team',
    price: '$149.99/mo',
    tagline:
      'Everything in Elite + Coach Portal, War Room, SquadOps, 6 seats',
    missingFeatures: [
      'Coach Portal with full War Room access',
      'SquadOps team coordination tools',
      '6 team member seats included',
    ],
  },
];

const tierOrder: UserTier[] = ['free', 'competitive', 'elite', 'team'];

const invoices = [
  { date: 'Mar 15, 2026', amount: '$19.99', status: 'Paid' },
  { date: 'Feb 15, 2026', amount: '$19.99', status: 'Paid' },
  { date: 'Jan 15, 2026', amount: '$19.99', status: 'Paid' },
];

export default function SubscriptionManagement({
  currentTier,
}: SubscriptionManagementProps) {
  const plan = tierData[currentTier];
  const currentIndex = tierOrder.indexOf(currentTier);

  const availableUpgrades = upgradeCards.filter(
    (card) => tierOrder.indexOf(card.tier) > currentIndex
  );

  return (
    <div className="space-y-6">
      {/* Section A: Current Plan */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h2 className="text-lg font-bold text-dark-100 mb-4">Current Plan</h2>

        <div className="flex items-baseline gap-2 mb-2">
          <span className="text-xl font-bold text-dark-50">{plan.name}</span>
          <span className="text-dark-400">—</span>
          <span className="text-xl font-bold text-forge-400">
            {plan.price === 0 ? 'Free' : `$${plan.price.toFixed(2)}/month`}
          </span>
        </div>

        <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-dark-400 mb-5">
          <span>Active since: January 15, 2026</span>
          <span>Next billing: April 15, 2026</span>
        </div>

        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {plan.features.map((feature) => (
            <li
              key={feature}
              className="flex items-start gap-2 text-sm text-dark-300"
            >
              <Check className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
              {feature}
            </li>
          ))}
        </ul>
      </div>

      {/* Section B: Available Upgrades */}
      {currentTier !== 'team' && availableUpgrades.length > 0 && (
        <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
          <h2 className="text-lg font-bold text-dark-100 mb-4">
            Available Upgrades
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {availableUpgrades.map((card) => (
              <div
                key={card.tier}
                className="rounded-xl border border-dark-600 bg-dark-800/60 p-5"
              >
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-lg font-bold text-dark-50 capitalize">
                    {card.tier}
                  </span>
                  <span className="text-sm font-semibold text-forge-400">
                    {card.price}
                  </span>
                </div>

                <p className="text-sm text-dark-400 mb-4">{card.tagline}</p>

                <p className="text-xs font-medium text-dark-500 uppercase tracking-wider mb-2">
                  Features you're missing
                </p>
                <ul className="space-y-2 mb-5">
                  {card.missingFeatures.map((feat) => (
                    <li
                      key={feat}
                      className="flex items-start gap-2 text-sm text-dark-300"
                    >
                      <Check className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                      {feat}
                    </li>
                  ))}
                </ul>

                <button className="w-full rounded-lg bg-forge-600 py-2.5 text-sm font-medium text-white hover:bg-forge-500 transition-colors">
                  Upgrade to {card.tier.charAt(0).toUpperCase() + card.tier.slice(1)}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Section C: Billing */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <h2 className="text-lg font-bold text-dark-100 mb-4">Billing</h2>

        {/* Payment Method */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <CreditCard className="w-5 h-5 text-dark-400" />
            <span className="text-sm text-dark-300">
              Visa ending in 4242
            </span>
          </div>
          <button className="rounded-lg border border-dark-600 bg-dark-800 px-4 py-2 text-sm font-medium text-dark-200 hover:bg-dark-700 transition-colors">
            Update Payment Method
          </button>
        </div>

        {/* Invoice History */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-dark-300 mb-3">
            Invoice History
          </h3>
          <div className="space-y-2">
            {invoices.map((invoice) => (
              <div
                key={invoice.date}
                className="flex items-center justify-between rounded-lg border border-dark-700 bg-dark-800/40 px-4 py-3"
              >
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-dark-300">{invoice.date}</span>
                  <span className="text-dark-400">—</span>
                  <span className="font-medium text-dark-200">
                    {invoice.amount}
                  </span>
                  <span className="text-dark-400">—</span>
                  <span className="text-green-500">{invoice.status}</span>
                </div>
                <button className="flex items-center gap-1.5 text-sm text-forge-400 hover:text-forge-300 transition-colors">
                  <Download className="w-4 h-4" />
                  Download
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Cancel Subscription */}
        {currentTier !== 'free' && (
          <div>
            <button className="rounded-lg border border-red-500/50 bg-transparent px-4 py-2 text-sm font-medium text-red-400 hover:bg-red-500/10 transition-colors">
              Cancel Subscription
            </button>
            <p className="mt-2 text-xs text-dark-500">
              Your plan will remain active until the end of the current billing
              period. You can resubscribe at any time.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
