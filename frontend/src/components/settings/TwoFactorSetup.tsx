'use client';

import { useState, useEffect } from 'react';
import { Shield, ShieldCheck, ShieldOff, Loader2 } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

interface TwoFactorSetupProps {
  token: string;
}

export default function TwoFactorSetup({ token }: TwoFactorSetupProps) {
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [setupData, setSetupData] = useState<{ secret: string; qr_code: string } | null>(null);
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  async function fetchStatus() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/2fa/status`, { headers });
      const data = await res.json();
      setEnabled(data.enabled);
    } catch {
      setError('Failed to fetch 2FA status.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSetup() {
    setError('');
    setSuccess('');
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/2fa/setup`, {
        method: 'POST',
        headers,
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Setup failed');
      }
      const data = await res.json();
      setSetupData(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Setup failed');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerify() {
    setError('');
    setSuccess('');
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/2fa/verify`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ code }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Verification failed');
      }
      setEnabled(true);
      setSetupData(null);
      setCode('');
      setSuccess('Two-factor authentication enabled successfully.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDisable() {
    if (!code) {
      setError('Enter your current TOTP code to disable 2FA.');
      return;
    }
    setError('');
    setSuccess('');
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/2fa/disable`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ code }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Disable failed');
      }
      setEnabled(false);
      setCode('');
      setSuccess('Two-factor authentication has been disabled.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Disable failed');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-dark-400 py-8">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span className="text-sm">Loading 2FA status...</span>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-dark-700 bg-dark-900 p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        {enabled ? (
          <ShieldCheck className="w-6 h-6 text-forge-400" />
        ) : (
          <Shield className="w-6 h-6 text-dark-500" />
        )}
        <div>
          <h3 className="text-lg font-semibold text-dark-100">
            Two-Factor Authentication
          </h3>
          <p className="text-sm text-dark-400">
            {enabled
              ? 'Your account is protected with 2FA.'
              : 'Add an extra layer of security to your account.'}
          </p>
        </div>
      </div>

      {/* Status badge */}
      <div className="mb-6">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
            enabled
              ? 'bg-forge-400/10 text-forge-400'
              : 'bg-dark-700 text-dark-400'
          }`}
        >
          {enabled ? 'Enabled' : 'Disabled'}
        </span>
      </div>

      {/* Feedback messages */}
      {error && (
        <div className="mb-4 rounded-md bg-red-900/20 border border-red-800 p-3 text-sm text-red-400">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 rounded-md bg-forge-400/10 border border-forge-700 p-3 text-sm text-forge-400">
          {success}
        </div>
      )}

      {/* Setup flow: not enabled, no setup data yet */}
      {!enabled && !setupData && (
        <button
          onClick={handleSetup}
          disabled={submitting}
          className="inline-flex items-center gap-2 rounded-md bg-forge-600 px-4 py-2 text-sm font-medium text-white hover:bg-forge-500 disabled:opacity-50 transition-colors"
        >
          {submitting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Shield className="w-4 h-4" />
          )}
          Enable 2FA
        </button>
      )}

      {/* QR code display + verify */}
      {!enabled && setupData && (
        <div className="space-y-4">
          <p className="text-sm text-dark-300">
            Scan the QR code below with your authenticator app (Google
            Authenticator, Authy, etc.), then enter the 6-digit code to verify.
          </p>
          <div className="flex justify-center rounded-lg bg-white p-4 w-fit mx-auto">
            <img
              src={`data:image/png;base64,${setupData.qr_code}`}
              alt="2FA QR Code"
              className="w-48 h-48"
            />
          </div>
          <p className="text-xs text-dark-500 text-center break-all">
            Manual entry key: <span className="font-mono text-dark-300">{setupData.secret}</span>
          </p>
          <div className="flex gap-3 items-center">
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              placeholder="Enter 6-digit code"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              className="flex-1 rounded-md border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:border-forge-400 focus:outline-none focus:ring-1 focus:ring-forge-400"
            />
            <button
              onClick={handleVerify}
              disabled={submitting || code.length !== 6}
              className="rounded-md bg-forge-600 px-4 py-2 text-sm font-medium text-white hover:bg-forge-500 disabled:opacity-50 transition-colors"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Verify'}
            </button>
          </div>
        </div>
      )}

      {/* Disable flow */}
      {enabled && (
        <div className="space-y-4">
          <p className="text-sm text-dark-300">
            Enter your current authenticator code to disable two-factor authentication.
          </p>
          <div className="flex gap-3 items-center">
            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              placeholder="Enter 6-digit code"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              className="flex-1 rounded-md border border-dark-700 bg-dark-800 px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:border-forge-400 focus:outline-none focus:ring-1 focus:ring-forge-400"
            />
            <button
              onClick={handleDisable}
              disabled={submitting || code.length !== 6}
              className="inline-flex items-center gap-2 rounded-md bg-red-900/40 border border-red-800 px-4 py-2 text-sm font-medium text-red-400 hover:bg-red-900/60 disabled:opacity-50 transition-colors"
            >
              {submitting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <ShieldOff className="w-4 h-4" />
              )}
              Disable 2FA
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
