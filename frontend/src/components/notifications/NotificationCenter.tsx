/**
 * Notification Center — dropdown panel with mock notifications.
 */

"use client";

import { useState } from "react";
import { clsx } from "clsx";
import {
  X,
  TrendingUp,
  Crosshair,
  UserSearch,
  Brain,
  Trophy,
  ShieldAlert,
  Flame,
} from "lucide-react";

interface Notification {
  id: string;
  type: string;
  icon: typeof TrendingUp;
  title: string;
  body: string;
  time: string;
  action: string;
  read: boolean;
}

const INITIAL_NOTIFICATIONS: Notification[] = [
  {
    id: "1",
    type: "impact-rank",
    icon: TrendingUp,
    title: "ImpactRank",
    body: "Priority changed — Coverage Read Speed now #1",
    time: "2m ago",
    action: "View Priority",
    read: false,
  },
  {
    id: "2",
    type: "meta-weapon",
    icon: Crosshair,
    title: "Meta Weapon",
    body: "PA Crossers hitting 91% this week",
    time: "15m ago",
    action: "Add to Gameplan",
    read: false,
  },
  {
    id: "3",
    type: "opponent-scouted",
    icon: UserSearch,
    title: "Opponent Scouted",
    body: "xXDragonSlayerXx dossier updated",
    time: "1h ago",
    action: "View Dossier",
    read: false,
  },
  {
    id: "4",
    type: "loop-ai",
    icon: Brain,
    title: "LoopAI",
    body: "PlayerTwin updated — Coverage baseline raised",
    time: "2h ago",
    action: "View PlayerTwin",
    read: false,
  },
  {
    id: "5",
    type: "tournament",
    icon: Trophy,
    title: "Tournament",
    body: "Weekend Cup starts in 2 hours",
    time: "3h ago",
    action: "Open War Room",
    read: true,
  },
  {
    id: "6",
    type: "tilt-guard",
    icon: ShieldAlert,
    title: "TiltGuard",
    body: "3 consecutive losses — consider a break",
    time: "4h ago",
    action: "View Mental",
    read: true,
  },
  {
    id: "7",
    type: "drill-streak",
    icon: Flame,
    title: "Drill Streak",
    body: "7-day streak! Read speed +12 points",
    time: "5h ago",
    action: "View Progress",
    read: true,
  },
];

export function NotificationCenter({ onClose }: { onClose: () => void }) {
  const [notifications, setNotifications] = useState<Notification[]>(INITIAL_NOTIFICATIONS);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const dismiss = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const markRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  return (
    <div className="absolute right-0 top-full z-50 mt-2 w-[380px] overflow-hidden rounded-xl border border-dark-700/50 bg-dark-900 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-dark-700/50 px-4 py-3">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-dark-100">Notifications</h3>
          {unreadCount > 0 && (
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-forge-500/20 px-1.5 text-[10px] font-bold text-forge-400">
              {unreadCount}
            </span>
          )}
        </div>
        <button
          onClick={markAllRead}
          className="text-xs font-medium text-forge-400 transition-colors hover:text-forge-300"
        >
          Mark All Read
        </button>
      </div>

      {/* Notification List */}
      <div className="max-h-[70vh] overflow-y-auto">
        {notifications.length === 0 ? (
          <div className="flex flex-col items-center gap-2 px-4 py-12">
            <p className="text-sm text-dark-400">No notifications</p>
            <p className="text-xs text-dark-500">You are all caught up!</p>
          </div>
        ) : (
          notifications.map((notification) => {
            const Icon = notification.icon;
            return (
              <div
                key={notification.id}
                className={clsx(
                  "group relative flex gap-3 border-b border-dark-800/50 px-4 py-3 transition-colors hover:bg-dark-800/50",
                  !notification.read && "bg-dark-800/30"
                )}
              >
                {/* Unread dot */}
                {!notification.read && (
                  <div className="absolute left-1.5 top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-full bg-forge-500" />
                )}

                {/* Icon */}
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-dark-800 text-forge-400">
                  <Icon className="h-4 w-4" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-semibold text-dark-200">{notification.title}</p>
                    <span className="shrink-0 text-[10px] text-dark-500">{notification.time}</span>
                  </div>
                  <p className="mt-0.5 text-xs text-dark-400">{notification.body}</p>
                  <button
                    onClick={() => markRead(notification.id)}
                    className="mt-1.5 text-[11px] font-medium text-forge-400 transition-colors hover:text-forge-300"
                  >
                    {notification.action}
                  </button>
                </div>

                {/* Dismiss */}
                <button
                  onClick={() => dismiss(notification.id)}
                  className="shrink-0 self-start text-dark-600 opacity-0 transition-opacity group-hover:opacity-100 hover:text-dark-300"
                  aria-label="Dismiss notification"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
