'use client';

import { useState, useCallback, useMemo } from 'react';
import type { AppNotification } from '@/types/settings';

const mockNotifications: AppNotification[] = [
  {
    id: 'n1',
    type: 'meta-alert',
    title: 'Meta Shift Detected',
    message: 'Madden 26 meta update: Gun Bunch is trending after patch 1.4.2. GameplanAgent has new counters ready.',
    timestamp: '2026-03-22T10:30:00Z',
    read: false,
  },
  {
    id: 'n2',
    type: 'milestone',
    title: 'Milestone Achieved',
    message: 'You hit a 10-game win streak in Ranked! Your ImpactRank rose to Diamond II.',
    timestamp: '2026-03-22T08:15:00Z',
    read: false,
  },
  {
    id: 'n3',
    type: 'tournament-reminder',
    title: 'Tournament Starting Soon',
    message: 'EsportsForge Weekly #47 starts in 2 hours. Your bracket is set — check your gameplan.',
    timestamp: '2026-03-22T06:00:00Z',
    read: false,
  },
  {
    id: 'n4',
    type: 'patch-note',
    title: 'Patch Notes: v2.3.1',
    message: 'New LoopAI calibration improvements and DrillRunner adaptive difficulty released.',
    timestamp: '2026-03-21T14:00:00Z',
    read: true,
  },
  {
    id: 'n5',
    type: 'tilt-warning',
    title: 'Tilt Warning',
    message: 'LoopAI detected declining performance over your last 3 sessions. Consider taking a break.',
    timestamp: '2026-03-21T11:30:00Z',
    read: true,
  },
];

export function useNotifications() {
  const [notifications, setNotifications] = useState<AppNotification[]>(mockNotifications);

  const unreadCount = useMemo(
    () => notifications.filter((n) => !n.read).length,
    [notifications]
  );

  const markAsRead = useCallback((id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  }, []);

  const dismissNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const addNotification = useCallback((notification: Omit<AppNotification, 'id'>) => {
    const id = `n${Date.now()}`;
    setNotifications((prev) => [{ ...notification, id }, ...prev]);
  }, []);

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    dismissNotification,
    addNotification,
  };
}
