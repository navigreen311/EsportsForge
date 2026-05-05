/**
 * Admin Dashboard layout — distinct from main dashboard.
 * Sidebar with admin-specific navigation, dark bg-dark-950 background.
 */

'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  Users,
  DollarSign,
  Brain,
  Swords,
  FileText,
  LifeBuoy,
  ArrowLeft,
  Shield,
  Film,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface AdminNavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const ADMIN_NAV: AdminNavItem[] = [
  { label: 'Overview',        href: '/admin',          icon: LayoutDashboard },
  { label: 'Users',           href: '/admin/users',    icon: Users },
  { label: 'Revenue',         href: '/admin/revenue',  icon: DollarSign },
  { label: 'AI Performance',  href: '/admin/ai',       icon: Brain },
  { label: 'AnimaForge',      href: '/admin/animaforge', icon: Film },
  { label: 'Meta Content',    href: '/admin/meta',     icon: Swords },
  { label: 'Patches',         href: '/admin/patches',  icon: FileText },
  { label: 'Support',         href: '/admin/support',  icon: LifeBuoy },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen overflow-hidden bg-dark-950">
      {/* Admin Sidebar */}
      <aside className="flex w-64 flex-col border-r border-dark-700/60 bg-dark-950">
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-dark-700/60 px-5 py-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-forge-400/10">
            <Shield className="h-5 w-5 text-forge-400" />
          </div>
          <span className="text-sm font-bold text-dark-100">Admin Panel</span>
        </div>

        {/* Return to App */}
        <Link
          href="/dashboard"
          className="mx-3 mt-3 flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-dark-400 transition-colors hover:bg-dark-800 hover:text-dark-100"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Return to App
        </Link>

        {/* Navigation */}
        <nav className="mt-4 flex-1 space-y-1 px-3">
          {ADMIN_NAV.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === '/admin'
                ? pathname === '/admin'
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-forge-400/10 text-forge-400'
                    : 'text-dark-400 hover:bg-dark-800 hover:text-dark-100'
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="border-t border-dark-700/60 px-5 py-3">
          <p className="text-[10px] text-dark-600">EsportsForge Admin v1.0</p>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-14 items-center border-b border-dark-700/60 bg-dark-900 px-6">
          <h2 className="text-sm font-semibold text-dark-100">
            EsportsForge Administration
          </h2>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-7xl px-6 py-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
