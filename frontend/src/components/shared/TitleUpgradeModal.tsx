"use client";

import Link from "next/link";
import { Lock } from "lucide-react";
import { Modal } from "@/components/shared/Modal";

interface TitleUpgradeModalProps {
  open: boolean;
  onClose: () => void;
  titleName: string;
  titleIcon: string;
  requiredTier: string;
}

const tierConfig: Record<string, { price: string; features: string[] }> = {
  competitive: {
    price: "19.99",
    features: [
      "Access to 7 titles",
      "Full OpponentScout",
      "Tournament Mode",
    ],
  },
  elite: {
    price: "49.99",
    features: [
      "Access to all 11 titles",
      "VoiceForge layer",
      "ForgeVault",
    ],
  },
};

export function TitleUpgradeModal({
  open,
  onClose,
  titleName,
  titleIcon,
  requiredTier,
}: TitleUpgradeModalProps) {
  const tier = tierConfig[requiredTier];
  const tierLabel = requiredTier.charAt(0).toUpperCase() + requiredTier.slice(1);

  if (!tier) return null;

  return (
    <Modal open={open} onClose={onClose} title={`Unlock ${titleName}`} size="sm">
      <div className="flex flex-col items-center gap-4">
        {/* Title icon */}
        <span className="text-4xl">{titleIcon}</span>

        {/* Lock indicator */}
        <div className="flex items-center gap-2 text-dark-400">
          <Lock className="h-4 w-4" />
          <span className="text-sm font-medium">{tierLabel} Tier Required</span>
        </div>

        {/* Description */}
        <p className="text-center text-sm text-dark-300">
          Upgrade to {tierLabel} to access {titleName} and all {tierLabel} features.
        </p>

        {/* Feature highlights */}
        <ul className="w-full space-y-2">
          {tier.features.map((feature) => (
            <li
              key={feature}
              className="flex items-center gap-2 text-sm text-dark-200"
            >
              <span className="text-forge-500">&#10003;</span>
              {feature}
            </li>
          ))}
        </ul>

        {/* CTA button */}
        <Link
          href="/settings?tab=subscription"
          onClick={onClose}
          className="mt-2 w-full rounded-lg bg-forge-500 px-4 py-3 text-center text-sm font-semibold text-white transition-colors hover:bg-forge-600"
        >
          Upgrade to {tierLabel} &mdash; ${tier.price}/mo
        </Link>
      </div>
    </Modal>
  );
}
