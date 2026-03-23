'use client';

import { useEffect, useState } from 'react';
import { X, Bell, FileText, Clock, AlertTriangle, Award, Trophy, Info } from 'lucide-react';
import type { NotificationType } from '@/types/settings';

interface NotificationToastProps {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  duration?: number;
  onDismiss: (id: string) => void;
}

const typeConfig: Record<
  NotificationType,
  { icon: typeof Bell; color: string; bgColor: string; borderColor: string }
> = {
  'meta-alert': {
    icon: Bell,
    color: 'text-forge-400',
    bgColor: 'bg-forge-500/10',
    borderColor: 'border-forge-800/50',
  },
  'patch-note': {
    icon: FileText,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-800/50',
  },
  'session-reminder': {
    icon: Clock,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-800/50',
  },
  'tilt-warning': {
    icon: AlertTriangle,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-800/50',
  },
  milestone: {
    icon: Award,
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-800/50',
  },
  'tournament-reminder': {
    icon: Trophy,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-800/50',
  },
  system: {
    icon: Info,
    color: 'text-dark-400',
    bgColor: 'bg-dark-800',
    borderColor: 'border-dark-600',
  },
};

export default function NotificationToast({
  id,
  type,
  title,
  message,
  duration = 5000,
  onDismiss,
}: NotificationToastProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);

  const config = typeConfig[type];
  const Icon = config.icon;

  useEffect(() => {
    // Trigger entrance animation
    const enterTimer = setTimeout(() => setIsVisible(true), 10);

    // Auto-dismiss
    const dismissTimer = setTimeout(() => {
      setIsLeaving(true);
      setTimeout(() => onDismiss(id), 300);
    }, duration);

    return () => {
      clearTimeout(enterTimer);
      clearTimeout(dismissTimer);
    };
  }, [id, duration, onDismiss]);

  const handleDismiss = () => {
    setIsLeaving(true);
    setTimeout(() => onDismiss(id), 300);
  };

  return (
    <div
      className={`max-w-sm w-full rounded-lg border shadow-xl backdrop-blur-sm transition-all duration-300 ${
        config.bgColor
      } ${config.borderColor} ${
        isVisible && !isLeaving
          ? 'opacity-100 translate-x-0'
          : 'opacity-0 translate-x-full'
      }`}
    >
      <div className="flex items-start gap-3 p-4">
        <div className={`shrink-0 mt-0.5 ${config.color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-dark-100">{title}</p>
          <p className="text-xs text-dark-400 mt-0.5 line-clamp-2">{message}</p>
        </div>
        <button
          onClick={handleDismiss}
          className="shrink-0 text-dark-500 hover:text-dark-300 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Progress bar for auto-dismiss */}
      <div className="h-0.5 bg-dark-800/50 overflow-hidden rounded-b-lg">
        <div
          className={`h-full ${config.color.replace('text-', 'bg-')} transition-all ease-linear`}
          style={{
            width: isVisible && !isLeaving ? '0%' : '100%',
            transitionDuration: isVisible && !isLeaving ? `${duration}ms` : '0ms',
          }}
        />
      </div>
    </div>
  );
}
