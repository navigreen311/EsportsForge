/**
 * Admin Overview — top-level dashboard with key metrics and service health.
 */

'use client';

import {
  Users,
  Activity,
  DollarSign,
  TrendingDown,
  CheckCircle,
  AlertCircle,
  Server,
} from 'lucide-react';

/* ------------------------------------------------------------------ */
/*  Mock data                                                          */
/* ------------------------------------------------------------------ */

const METRICS = [
  { label: 'Total Users',  value: '12,847', change: '+342 this month', icon: Users,        color: 'text-blue-400',   bg: 'bg-blue-400/10' },
  { label: 'Daily Active', value: '3,219',  change: '+8.2% vs last week', icon: Activity,  color: 'text-green-400',  bg: 'bg-green-400/10' },
  { label: 'Revenue MRR',  value: '$87,420', change: '+$4,200 MoM',  icon: DollarSign,    color: 'text-forge-400',  bg: 'bg-forge-400/10' },
  { label: 'Churn Rate',   value: '2.1%',   change: '-0.3% vs last month', icon: TrendingDown, color: 'text-amber-400', bg: 'bg-amber-400/10' },
];

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'degraded' | 'down';
  latency?: string;
}

const SERVICES: ServiceStatus[] = [
  { name: 'Database',         status: 'healthy',  latency: '4ms' },
  { name: 'Redis',            status: 'healthy',  latency: '1ms' },
  { name: 'Claude API',       status: 'healthy',  latency: '320ms' },
  { name: 'VoiceForge',       status: 'degraded', latency: '1.2s' },
  { name: 'VisionAudioForge', status: 'healthy',  latency: '180ms' },
];

const STATUS_STYLES: Record<ServiceStatus['status'], { dot: string; label: string }> = {
  healthy:  { dot: 'bg-green-400', label: 'Healthy' },
  degraded: { dot: 'bg-amber-400', label: 'Degraded' },
  down:     { dot: 'bg-red-400',   label: 'Down' },
};

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export default function AdminOverviewPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-dark-50">Overview</h1>

      {/* Metric cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {METRICS.map((m) => {
          const Icon = m.icon;
          return (
            <div
              key={m.label}
              className="rounded-xl border border-dark-700/60 bg-dark-900 p-5"
            >
              <div className="flex items-center gap-3">
                <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${m.bg}`}>
                  <Icon className={`h-5 w-5 ${m.color}`} />
                </div>
                <div>
                  <p className="text-xs text-dark-400">{m.label}</p>
                  <p className="text-xl font-bold text-dark-50">{m.value}</p>
                </div>
              </div>
              <p className="mt-3 text-xs text-dark-400">{m.change}</p>
            </div>
          );
        })}
      </div>

      {/* Service Health */}
      <div className="rounded-xl border border-dark-700/60 bg-dark-900 p-5">
        <div className="mb-4 flex items-center gap-2">
          <Server className="h-5 w-5 text-dark-300" />
          <h2 className="text-sm font-semibold text-dark-100">Service Health</h2>
        </div>
        <div className="space-y-3">
          {SERVICES.map((svc) => {
            const s = STATUS_STYLES[svc.status];
            return (
              <div
                key={svc.name}
                className="flex items-center justify-between rounded-lg bg-dark-800/50 px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <span className={`h-2.5 w-2.5 rounded-full ${s.dot}`} />
                  <span className="text-sm text-dark-100">{svc.name}</span>
                </div>
                <div className="flex items-center gap-4">
                  {svc.latency && (
                    <span className="text-xs text-dark-400">{svc.latency}</span>
                  )}
                  <span
                    className={`text-xs font-medium ${
                      svc.status === 'healthy'
                        ? 'text-green-400'
                        : svc.status === 'degraded'
                          ? 'text-amber-400'
                          : 'text-red-400'
                    }`}
                  >
                    {s.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Environment info */}
      <div className="rounded-xl border border-dark-700/60 bg-dark-900 p-5">
        <h2 className="mb-3 text-sm font-semibold text-dark-100">Environment</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <p className="text-xs text-dark-400">Version</p>
            <p className="text-sm font-medium text-dark-100">1.0.0-beta</p>
          </div>
          <div>
            <p className="text-xs text-dark-400">Environment</p>
            <p className="text-sm font-medium text-dark-100">Production</p>
          </div>
          <div>
            <p className="text-xs text-dark-400">Region</p>
            <p className="text-sm font-medium text-dark-100">US-East-1</p>
          </div>
          <div>
            <p className="text-xs text-dark-400">Last Deploy</p>
            <p className="text-sm font-medium text-dark-100">2026-04-11 14:32 UTC</p>
          </div>
        </div>
      </div>
    </div>
  );
}
