/**
 * Dashboard layout — Sidebar on left (collapsible), TopBar at top,
 * main content area with padding, responsive with mobile bottom nav.
 */

"use client";

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  Gamepad2,
  Users,
  Target,
  BarChart3,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Sidebar } from '@/components/shared/Sidebar';
import { TopBar } from '@/components/shared/TopBar';
import { useUIStore } from '@/lib/store';

interface MobileNavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const MOBILE_NAV: MobileNavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Gameplan', href: '/gameplan', icon: Gamepad2 },
  { label: 'Opponents', href: '/opponents', icon: Users },
  { label: 'Drills', href: '/drills', icon: Target },
  { label: 'Analytics', href: '/analytics', icon: BarChart3 },
];

function MobileBottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 border-t border-dark-700/50 bg-dark-950/95 backdrop-blur-sm lg:hidden">
      <div className="flex items-center justify-around py-2">
        {MOBILE_NAV.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + '/');

          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                'flex flex-col items-center gap-0.5 px-3 py-1 text-[10px] font-medium transition-colors',
                isActive ? 'text-forge-400' : 'text-dark-500'
              )}
            >
              <Icon className="h-5 w-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);

  return (
    <div className="flex h-screen overflow-hidden bg-dark-950">
      {/* Sidebar */}
      <Sidebar />

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar />

        {/* Content */}
        <main className="flex-1 overflow-y-auto pb-20 lg:pb-0">
          <div className="mx-auto max-w-7xl px-4 py-6 lg:px-6">
            {children}
          </div>
        </main>
      </div>

      {/* Mobile bottom nav */}
      <MobileBottomNav />
    </div>
  );
}
