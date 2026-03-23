/**
 * Left sidebar navigation with title selector, nav items, and user tier badge.
 * Supports collapse/expand on desktop and slide-out drawer on mobile.
 */

"use client";

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { clsx } from 'clsx';
import {
  LayoutDashboard,
  Gamepad2,
  Users,
  Target,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Swords,
  X,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useUIStore, TITLE_OPTIONS, TIER_CONFIG } from '@/lib/store';
import { Badge } from './Badge';
import { TitleSwitcher } from './TitleSwitcher';

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Gameplan', href: '/gameplan', icon: Gamepad2 },
  { label: 'Opponents', href: '/opponents', icon: Users },
  { label: 'Drills', href: '/drills', icon: Target },
  { label: 'Analytics', href: '/analytics', icon: BarChart3 },
  { label: 'Settings', href: '/settings', icon: Settings },
];

function TitleSelector({ collapsed }: { collapsed: boolean }) {
  const [open, setOpen] = useState(false);
  const selectedTitle = useUIStore((s) => s.selectedTitle);
  const setTitle = useUIStore((s) => s.setTitle);

  const current = TITLE_OPTIONS.find((t) => t.id === selectedTitle) ?? TITLE_OPTIONS[0];

  if (collapsed) {
    return (
      <button
        onClick={() => {
          const next = TITLE_OPTIONS.find((t) => t.id !== selectedTitle);
          if (next) setTitle(next.id);
        }}
        className="flex h-10 w-10 items-center justify-center rounded-lg bg-dark-800/50 text-lg transition-colors hover:bg-dark-700"
        title={current.label}
      >
        {current.icon}
      </button>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 rounded-lg bg-dark-800/50 px-3 py-2 text-sm text-dark-200 transition-colors hover:bg-dark-700"
      >
        <span className="text-lg">{current.icon}</span>
        <span className="flex-1 text-left font-medium">{current.label}</span>
        <ChevronDown
          className={clsx(
            'h-4 w-4 text-dark-400 transition-transform',
            open && 'rotate-180'
          )}
        />
      </button>

      {open && (
        <div className="absolute left-0 right-0 z-10 mt-1 overflow-hidden rounded-lg border border-dark-700/50 bg-dark-800 shadow-xl">
          {TITLE_OPTIONS.map((title) => (
            <button
              key={title.id}
              onClick={() => {
                setTitle(title.id);
                setOpen(false);
              }}
              className={clsx(
                'flex w-full items-center gap-2 px-3 py-2 text-sm transition-colors hover:bg-dark-700',
                title.id === selectedTitle
                  ? 'bg-forge-500/10 text-forge-400'
                  : 'text-dark-300'
              )}
            >
              <span className="text-lg">{title.icon}</span>
              <span>{title.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function NavLink({
  item,
  collapsed,
  isActive,
}: {
  item: NavItem;
  collapsed: boolean;
  isActive: boolean;
}) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      className={clsx(
        'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
        isActive
          ? 'bg-forge-500/15 text-forge-400'
          : 'text-dark-400 hover:bg-dark-800/50 hover:text-dark-200',
        collapsed && 'justify-center px-2'
      )}
      title={collapsed ? item.label : undefined}
    >
      <Icon
        className={clsx(
          'h-5 w-5 flex-shrink-0 transition-colors',
          isActive ? 'text-forge-400' : 'text-dark-500 group-hover:text-dark-300'
        )}
      />
      {!collapsed && <span>{item.label}</span>}
      {isActive && !collapsed && (
        <div className="ml-auto h-1.5 w-1.5 rounded-full bg-forge-400" />
      )}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const sidebarOpen = useUIStore((s) => s.sidebarOpen);
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const setSidebarOpen = useUIStore((s) => s.setSidebarOpen);
  const toggleSidebarCollapse = useUIStore((s) => s.toggleSidebarCollapse);
  const userTier = useUIStore((s) => s.userTier);

  const tierConfig = TIER_CONFIG[userTier];

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-dark-950/80 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex flex-col border-r border-dark-700/50 bg-dark-950 transition-all duration-300 lg:static lg:z-auto',
          // Mobile: slide in/out
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
          // Desktop: collapsed or expanded
          sidebarCollapsed ? 'w-[68px]' : 'w-64'
        )}
      >
        {/* Logo */}
        <div
          className={clsx(
            'flex h-16 items-center border-b border-dark-700/50 px-4',
            sidebarCollapsed ? 'justify-center' : 'gap-3'
          )}
        >
          <Swords className="h-7 w-7 flex-shrink-0 text-forge-500" />
          {!sidebarCollapsed && (
            <span className="text-lg font-bold text-dark-50">
              Esports<span className="text-forge-500">Forge</span>
            </span>
          )}

          {/* Mobile close button */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="ml-auto rounded-lg p-1 text-dark-400 hover:text-dark-200 lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Title selector — 11-title grouped dropdown */}
        <div className={clsx('border-b border-dark-700/50', sidebarCollapsed ? 'px-2 py-3' : 'px-4 py-3')}>
          <TitleSwitcher collapsed={sidebarCollapsed} />
        </div>

        {/* Navigation */}
        <nav className={clsx('flex-1 overflow-y-auto py-4', sidebarCollapsed ? 'px-2' : 'px-3')}>
          <div className="flex flex-col gap-1">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.href}
                item={item}
                collapsed={sidebarCollapsed}
                isActive={pathname === item.href || pathname.startsWith(item.href + '/')}
              />
            ))}
          </div>
        </nav>

        {/* User tier badge */}
        <div
          className={clsx(
            'border-t border-dark-700/50',
            sidebarCollapsed ? 'px-2 py-3' : 'px-4 py-3'
          )}
        >
          {sidebarCollapsed ? (
            <div
              className={clsx(
                'flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold mx-auto',
                tierConfig.color,
                tierConfig.textColor
              )}
              title={tierConfig.label}
            >
              {tierConfig.label[0]}
            </div>
          ) : (
            <Badge
              variant={userTier === 'elite' ? 'warning' : userTier === 'team' ? 'tier' : userTier === 'competitive' ? 'success' : 'neutral'}
              size="sm"
              dot
            >
              {tierConfig.label} Tier
            </Badge>
          )}
        </div>

        {/* Collapse toggle (desktop only) */}
        <div className="hidden border-t border-dark-700/50 p-2 lg:block">
          <button
            onClick={toggleSidebarCollapse}
            className="flex w-full items-center justify-center rounded-lg p-2 text-dark-400 transition-colors hover:bg-dark-800 hover:text-dark-200"
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>
        </div>
      </aside>
    </>
  );
}
