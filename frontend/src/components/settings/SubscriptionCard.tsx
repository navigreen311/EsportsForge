'use client';

import { Check, Crown, Zap, Users, Star } from 'lucide-react';
import type { UserTier } from '@/types/auth';
import type { SubscriptionTier } from '@/types/settings';

interface SubscriptionCardProps {
  currentTier: UserTier;
}

const tiers: SubscriptionTier[] = [
  {
    id: 'free',
    name: 'Free',
    price: 0,
    priceLabel: '$0/mo',
    titleLimit: 1,
    features: [
      '1 game title',
      'Basic analytics dashboard',
      'Community meta reports',
      'Limited drill access',
      'Standard opponent scouting',
    ],
  },
  {
    id: 'competitive',
    name: 'Competitive',
    price: 19.99,
    priceLabel: '$19.99/mo',
    titleLimit: 3,
    highlighted: true,
    features: [
      '3 game titles',
      'Full AI agent suite',
      'Advanced analytics & LoopAI',
      'Kill sheet generator',
      'Unlimited drills',
      'ImpactRank tracking',
      'Priority opponent scouting',
    ],
  },
  {
    id: 'elite',
    name: 'Elite',
    price: 49.99,
    priceLabel: '$49.99/mo',
    titleLimit: 'All 11',
    features: [
      'All 11 game titles',
      'Everything in Competitive',
      'Tournament operations hub',
      'VoiceForge AI callouts',
      'TransferAI cross-game insights',
      'Custom AI model tuning',
      'Priority support',
    ],
  },
  {
    id: 'team',
    name: 'Team',
    price: 149.99,
    priceLabel: '$149.99/mo',
    titleLimit: 'All 11',
    features: [
      'Everything in Elite',
      'Coach portal & war room',
      '6 team member seats',
      'Team analytics & comparisons',
      'Shared gameplans & strategies',
      'Bulk opponent scouting',
      'Dedicated account manager',
    ],
  },
];

const tierIcons: Record<UserTier, typeof Star> = {
  free: Star,
  competitive: Zap,
  elite: Crown,
  team: Users,
};

const tierColors: Record<UserTier, string> = {
  free: 'border-dark-600',
  competitive: 'border-forge-500',
  elite: 'border-yellow-500',
  team: 'border-purple-500',
};

export default function SubscriptionCard({ currentTier }: SubscriptionCardProps) {
  return (
    <div className="space-y-6">
      {/* Current Tier Display */}
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-5">
        <div className="flex items-center gap-3 mb-2">
          {(() => {
            const Icon = tierIcons[currentTier];
            return <Icon className="w-5 h-5 text-forge-400" />;
          })()}
          <div>
            <p className="text-xs text-dark-500 uppercase tracking-wider">Current Plan</p>
            <p className="text-lg font-bold text-dark-100 capitalize">{currentTier}</p>
          </div>
        </div>
        <p className="text-sm text-dark-400">
          {currentTier === 'free' && 'Upgrade to unlock AI agents and advanced analytics.'}
          {currentTier === 'competitive' && 'Full AI suite active. Upgrade to Elite for all titles.'}
          {currentTier === 'elite' && 'All titles unlocked. Add Team for coach portal.'}
          {currentTier === 'team' && 'Maximum tier. All features unlocked for your team.'}
        </p>
      </div>

      {/* Tier Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {tiers.map((tier) => {
          const isCurrent = tier.id === currentTier;
          const Icon = tierIcons[tier.id];
          return (
            <div
              key={tier.id}
              className={`rounded-xl border-2 p-5 transition-all ${
                isCurrent
                  ? `${tierColors[tier.id]} bg-dark-800/80`
                  : 'border-dark-700 bg-dark-900/50'
              } ${tier.highlighted && !isCurrent ? 'ring-1 ring-forge-500/30' : ''}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon
                  className={`w-4 h-4 ${
                    isCurrent ? 'text-forge-400' : 'text-dark-400'
                  }`}
                />
                <h3 className="text-sm font-bold text-dark-100">{tier.name}</h3>
                {isCurrent && (
                  <span className="ml-auto text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-forge-500/20 text-forge-400 border border-forge-800/50">
                    Current
                  </span>
                )}
              </div>

              <div className="mb-4">
                <span className="text-2xl font-bold text-dark-50">${tier.price}</span>
                <span className="text-sm text-dark-500">/mo</span>
              </div>

              <p className="text-xs text-dark-400 mb-3">
                {typeof tier.titleLimit === 'number'
                  ? `${tier.titleLimit} title${tier.titleLimit > 1 ? 's' : ''}`
                  : `${tier.titleLimit} titles`}
              </p>

              <ul className="space-y-2 mb-5">
                {tier.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-xs text-dark-300">
                    <Check className="w-3.5 h-3.5 text-forge-500 mt-0.5 shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>

              {!isCurrent && (
                <button
                  className={`w-full rounded-lg py-2 text-sm font-medium transition-colors ${
                    tier.highlighted
                      ? 'bg-forge-600 text-white hover:bg-forge-500'
                      : 'bg-dark-700 text-dark-200 hover:bg-dark-600'
                  }`}
                >
                  {tiers.findIndex((t) => t.id === tier.id) >
                  tiers.findIndex((t) => t.id === currentTier)
                    ? 'Upgrade'
                    : 'Downgrade'}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
