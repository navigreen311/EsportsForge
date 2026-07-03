/**
 * Top bar with mode badge, integrity status, notifications, user avatar,
 * and breadcrumb navigation.
 */

"use client";

import { useState, useRef, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import VoiceCommandButton from '@/components/voice/VoiceCommandButton';
import VisionStatusIcon from '@/components/shared/VisionStatusIcon';
import { NotificationCenter } from '@/components/notifications/NotificationCenter';
import { clsx } from 'clsx';
import {
  Bell,
  Check,
  ChevronRight,
  Menu,
  Shield,
  ShieldAlert,
  ShieldCheck,
  User,
  LogOut,
  Settings,
  UserCircle,
} from 'lucide-react';
import { useUIStore, MODE_CONFIG } from '@/lib/store';
import type { IntegrityStatus, GameMode } from '@/lib/store';
import { Badge } from './Badge';

const INTEGRITY_CONFIG: Record<
  IntegrityStatus,
  { icon: typeof ShieldCheck; label: string; variant: 'success' | 'warning' | 'danger' }
> = {
  safe: { icon: ShieldCheck, label: 'Safe', variant: 'success' },
  caution: { icon: ShieldAlert, label: 'Caution', variant: 'warning' },
  restricted: { icon: Shield, label: 'Restricted', variant: 'danger' },
};

function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split('/').filter(Boolean);

  if (segments.length === 0) return null;

  return (
    <nav className="hidden items-center gap-1.5 text-sm md:flex" aria-label="Breadcrumb">
      <Link href="/" className="text-dark-500 transition-colors hover:text-dark-300">
        Home
      </Link>
      {segments.map((segment, i) => {
        const href = '/' + segments.slice(0, i + 1).join('/');
        const isLast = i === segments.length - 1;
        const label = segment.charAt(0).toUpperCase() + segment.slice(1);

        return (
          <span key={href} className="flex items-center gap-1.5">
            <ChevronRight className="h-3.5 w-3.5 text-dark-600" />
            {isLast ? (
              <span className="font-medium text-dark-200">{label}</span>
            ) : (
              <Link
                href={href}
                className="text-dark-500 transition-colors hover:text-dark-300"
              >
                {label}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}

function UserMenu() {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(!open)}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-forge-500/20 text-forge-400 transition-colors hover:bg-forge-500/30"
        aria-label="User menu"
      >
        <User className="h-4 w-4" />
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-48 overflow-hidden rounded-xl border border-dark-700/50 bg-dark-800 shadow-xl">
          <div className="border-b border-dark-700/50 px-4 py-3">
            <p className="text-sm font-medium text-dark-100">Player One</p>
            <p className="text-xs text-dark-400">player@esportsforge.io</p>
          </div>
          <div className="py-1">
            <button
              onClick={() => setOpen(false)}
              className="flex w-full items-center gap-2.5 px-4 py-2 text-sm text-dark-300 transition-colors hover:bg-dark-700 hover:text-dark-100"
            >
              <UserCircle className="h-4 w-4" />
              Profile
            </button>
            <button
              onClick={() => setOpen(false)}
              className="flex w-full items-center gap-2.5 px-4 py-2 text-sm text-dark-300 transition-colors hover:bg-dark-700 hover:text-dark-100"
            >
              <Settings className="h-4 w-4" />
              Settings
            </button>
            <div className="my-1 border-t border-dark-700/50" />
            <button
              onClick={() => setOpen(false)}
              className="flex w-full items-center gap-2.5 px-4 py-2 text-sm text-red-400 transition-colors hover:bg-dark-700"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function ModeSelector() {
  const currentMode = useUIStore((s) => s.currentMode);
  const setMode = useUIStore((s) => s.setMode);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const variantFor = (m: GameMode) =>
    m === 'ranked' ? 'success' : m === 'tournament' ? 'warning' : 'info';
  const dotFor = (m: GameMode) =>
    m === 'ranked' ? 'bg-emerald-400' : m === 'tournament' ? 'bg-amber-400' : 'bg-sky-400';

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="rounded-full transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-forge-500/50"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Game mode: ${MODE_CONFIG[currentMode].label}. Click to change.`}
      >
        <Badge variant={variantFor(currentMode)} size="sm" dot>
          {MODE_CONFIG[currentMode].label}
        </Badge>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-50 mt-2 w-44 overflow-hidden rounded-xl border border-dark-700/50 bg-dark-800 shadow-xl"
        >
          <div className="border-b border-dark-700/50 px-3 py-2 text-xs font-medium text-dark-400">
            Game Mode
          </div>
          <div className="py-1">
            {(Object.keys(MODE_CONFIG) as GameMode[]).map((m) => (
              <button
                key={m}
                type="button"
                role="menuitemradio"
                aria-checked={m === currentMode}
                onClick={() => {
                  setMode(m);
                  setOpen(false);
                }}
                className={clsx(
                  'flex w-full items-center justify-between px-3 py-2 text-sm transition-colors hover:bg-dark-700',
                  m === currentMode ? 'text-dark-100' : 'text-dark-300',
                )}
              >
                <span className="flex items-center gap-2">
                  <span className={clsx('h-2 w-2 rounded-full', dotFor(m))} />
                  {MODE_CONFIG[m].label}
                </span>
                {m === currentMode && <Check className="h-3.5 w-3.5 text-forge-400" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function TopBar() {
  const integrityStatus = useUIStore((s) => s.integrityStatus);
  const unreadCount = useUIStore((s) => s.unreadCount);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);

  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const notifRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotificationsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const integrity = INTEGRITY_CONFIG[integrityStatus];
  const IntegrityIcon = integrity.icon;

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-dark-700/50 bg-dark-950/95 px-4 backdrop-blur-sm lg:px-6">
      {/* Mobile menu button */}
      <button
        onClick={toggleSidebar}
        className="rounded-lg p-2 text-dark-400 transition-colors hover:bg-dark-800 hover:text-dark-200 lg:hidden"
        aria-label="Open sidebar"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Breadcrumbs */}
      <Breadcrumbs />

      {/* Spacer */}
      <div className="flex-1" />

      {/* Right section */}
      <div className="flex items-center gap-3">
        {/* Mode selector (click to change) */}
        <ModeSelector />

        {/* Integrity status */}
        <Badge variant={integrity.variant} size="sm">
          <IntegrityIcon className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">{integrity.label}</span>
        </Badge>

        {/* Notifications */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="relative rounded-lg p-2 text-dark-400 transition-colors hover:bg-dark-800 hover:text-dark-200"
            aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
          >
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-forge-500 px-1 text-[10px] font-bold text-dark-950">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>
          {notificationsOpen && (
            <NotificationCenter onClose={() => setNotificationsOpen(false)} />
          )}
        </div>

        {/* Voice Command */}
        <VoiceCommandButton />

        {/* VisionAudioForge Status */}
        <VisionStatusIcon />

        {/* User avatar / dropdown */}
        <UserMenu />
      </div>
    </header>
  );
}
