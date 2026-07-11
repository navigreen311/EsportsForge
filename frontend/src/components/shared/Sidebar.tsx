/**
 * Left sidebar navigation with title selector, nav items, and user tier badge.
 * Supports collapse/expand on desktop and slide-out drawer on mobile.
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
  Trophy,
  Settings,
  ChevronLeft,
  ChevronRight,
  Swords,
  X,
  Archive,
  Shield,
  Zap,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useUIStore, TIER_CONFIG } from '@/lib/store';
import { Badge } from './Badge';
import { TitleSwitcher } from './TitleSwitcher';

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Gameplan', href: '/gameplan', icon: Gamepad2 },
  { label: 'Arsenal', href: '/arsenal', icon: Zap, badge: 'NEW' },
  { label: 'Opponents', href: '/opponents', icon: Users },
  { label: 'Vault', href: '/vault', icon: Archive },
  { label: 'War Room', href: '/war-room', icon: Shield },
  { label: 'Drills', href: '/drills', icon: Target },
  { label: 'Analytics', href: '/analytics', icon: BarChart3 },
  { label: 'Tournament', href: '/tournament', icon: Trophy },
  { label: 'Settings', href: '/settings', icon: Settings },
];

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
      {!collapsed && item.badge && (
        <span className="ml-auto rounded-full bg-forge-500/20 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-forge-300">
          {item.badge}
        </span>
      )}
      {isActive && !collapsed && !item.badge && (
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
