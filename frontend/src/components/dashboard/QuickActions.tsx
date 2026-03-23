/**
 * 4-card quick-action grid linking to primary workflows.
 */

'use client';

import Link from 'next/link';
import { Gamepad2, Target, Users, BarChart3 } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Card } from '@/components/shared/Card';
import type { QuickAction } from '@/types/dashboard';

const iconMap: Record<string, LucideIcon> = {
  Gamepad2,
  Target,
  Users,
  BarChart3,
};

interface QuickActionsProps {
  actions: QuickAction[];
}

export default function QuickActions({ actions }: QuickActionsProps) {
  return (
    <div>
      <h3 className="mb-4 text-sm font-bold uppercase tracking-wider text-dark-300">
        Quick Actions
      </h3>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {actions.map((action) => {
          const Icon = iconMap[action.icon] ?? Gamepad2;

          return (
            <Link key={action.id} href={action.href}>
              <Card
                hover
                className="flex flex-col items-center gap-2 text-center transition-all"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-forge-500/10">
                  <Icon className="h-5 w-5 text-forge-400" />
                </div>
                <span className="text-sm font-bold text-dark-100">
                  {action.label}
                </span>
                <span className="text-[11px] leading-tight text-dark-500">
                  {action.description}
                </span>
              </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
