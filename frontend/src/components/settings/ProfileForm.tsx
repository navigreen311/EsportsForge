'use client';

import { useState, useRef, useEffect } from 'react';
import { User, Camera, Lock, Link2, Check, AlertCircle, Mail } from 'lucide-react';
import { useSession, signIn } from 'next-auth/react';
import type { ProfileSettings } from '@/types/settings';
import TwoFactorSetup from './TwoFactorSetup';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://127.0.0.1:8001';

interface ProfileFormProps {
  profile: ProfileSettings;
  onUpdate: (profile: Partial<ProfileSettings>) => void;
}

const inputClass =
  'w-full rounded-lg border border-dark-600 bg-dark-800 px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:border-forge-500 focus:ring-1 focus:ring-forge-500 focus:outline-none transition-colors';

export default function ProfileForm({ profile, onUpdate }: ProfileFormProps) {
  const { data: session } = useSession();
  const accessToken = session?.accessToken ?? '';

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [submittingPassword, setSubmittingPassword] = useState(false);

  // Photo upload (C15)
  const fileRef = useRef<HTMLInputElement>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [photoError, setPhotoError] = useState('');

  // Username uniqueness (C15)
  const [usernameStatus, setUsernameStatus] = useState<'idle' | 'checking' | 'available' | 'taken'>('idle');

  // Email change verification (C15)
  const [emailVerifySent, setEmailVerifySent] = useState(false);
  const [emailVerifyError, setEmailVerifyError] = useState('');
  const initialEmailRef = useRef(profile.email);
  const emailChanged = profile.email !== initialEmailRef.current;

  // OAuth status (C15)
  const [oauth, setOauth] = useState<{ google: string | null; discord: string | null }>({ google: null, discord: null });
  useEffect(() => {
    if (!accessToken) return;
    fetch(`${API_BASE}/api/v1/users/me/oauth`, { headers: { Authorization: `Bearer ${accessToken}` } })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d) setOauth({ google: d.google ?? null, discord: d.discord ?? null }); })
      .catch(() => { /* endpoint may not exist yet — stays null */ });
  }, [accessToken]);

  function handlePhotoPick() {
    fileRef.current?.click();
  }

  async function handlePhotoChange(e: React.ChangeEvent<HTMLInputElement>) {
    setPhotoError('');
    const f = e.target.files?.[0];
    if (!f) return;
    if (!['image/jpeg', 'image/png', 'image/gif'].includes(f.type)) {
      setPhotoError('JPG, PNG, or GIF only.');
      return;
    }
    if (f.size > 2 * 1024 * 1024) {
      setPhotoError('Max 2 MB.');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => setPhotoPreview(reader.result as string);
    reader.readAsDataURL(f);
    const fd = new FormData();
    fd.append('photo', f);
    try {
      const res = await fetch(`${API_BASE}/api/v1/users/me/photo`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${accessToken}` },
        body: fd,
      });
      if (res.ok) {
        const data = await res.json().catch(() => null);
        if (data?.avatar_url) onUpdate({ avatarUrl: data.avatar_url });
      } else {
        setPhotoError('Upload failed — backend stub may not be wired yet.');
      }
    } catch {
      setPhotoError('Upload failed — network error.');
    }
  }

  async function checkUsernameAvailability(value: string) {
    if (!value || value === profile.username) {
      setUsernameStatus('idle');
      return;
    }
    setUsernameStatus('checking');
    try {
      const res = await fetch(`${API_BASE}/api/v1/users/check-username?username=${encodeURIComponent(value)}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) { setUsernameStatus('idle'); return; }
      const data = await res.json();
      setUsernameStatus(data.available === false ? 'taken' : 'available');
    } catch {
      setUsernameStatus('idle');
    }
  }

  async function requestEmailVerification() {
    setEmailVerifyError('');
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/email/request-change`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ new_email: profile.email }),
      });
      if (!res.ok) throw new Error('Failed');
      setEmailVerifySent(true);
    } catch {
      setEmailVerifyError('Could not send verification email (provider not configured).');
    }
  }

  async function connectOAuth(provider: 'google' | 'discord') {
    try {
      await signIn(provider, { callbackUrl: '/settings?tab=profile' });
    } catch {
      alert(`OAuth provider '${provider}' not configured in NextAuth — wire NEXT_PUBLIC_${provider.toUpperCase()}_CLIENT_ID first.`);
    }
  }

  async function disconnectOAuth(provider: 'google' | 'discord') {
    try {
      await fetch(`${API_BASE}/api/v1/users/me/oauth/${provider}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      setOauth((prev) => ({ ...prev, [provider]: null }));
    } catch { /* ignore */ }
  }

  function resetPasswordForm() {
    setShowPasswordForm(false);
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
    setPasswordError('');
  }

  async function handleChangePassword() {
    setPasswordError('');
    setPasswordSuccess('');

    if (newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match.');
      return;
    }

    setSubmittingPassword(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Failed to change password');
      }
      setPasswordSuccess('Password updated');
      resetPasswordForm();
    } catch (err: unknown) {
      setPasswordError(
        err instanceof Error ? err.message : 'Failed to change password'
      );
    } finally {
      setSubmittingPassword(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Avatar Upload */}
      <div className="flex items-center gap-6">
        <div className="relative">
          <div className="w-20 h-20 rounded-full bg-dark-800 border-2 border-dark-600 flex items-center justify-center overflow-hidden">
            {photoPreview || profile.avatarUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={photoPreview ?? profile.avatarUrl ?? ''}
                alt="Avatar"
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              <User className="w-8 h-8 text-dark-500" />
            )}
          </div>
          <button
            type="button"
            onClick={handlePhotoPick}
            className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-forge-600 hover:bg-forge-500 border-2 border-dark-900 flex items-center justify-center transition-colors"
            title="Upload avatar"
          >
            <Camera className="w-3.5 h-3.5 text-white" />
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/jpeg,image/png,image/gif"
            onChange={handlePhotoChange}
            className="hidden"
          />
        </div>
        <div>
          <p className="text-sm font-medium text-dark-200">Profile Photo</p>
          <p className="text-xs text-dark-500 mt-0.5">JPG, PNG or GIF. Max 2 MB.</p>
          {photoError && <p className="text-xs text-red-400 mt-1">{photoError}</p>}
        </div>
      </div>

      {/* Form Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-1.5">
            Username
          </label>
          <div className="relative">
            <input
              type="text"
              value={profile.username}
              onChange={(e) => { onUpdate({ username: e.target.value }); setUsernameStatus('idle'); }}
              onBlur={(e) => checkUsernameAvailability(e.target.value)}
              className={inputClass}
              placeholder="Enter username"
            />
            {usernameStatus === 'checking' && (
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-dark-500">checking…</span>
            )}
            {usernameStatus === 'available' && (
              <span className="absolute right-3 top-1/2 -translate-y-1/2 inline-flex items-center gap-1 text-xs text-forge-400"><Check className="w-3 h-3" /> available</span>
            )}
            {usernameStatus === 'taken' && (
              <span className="absolute right-3 top-1/2 -translate-y-1/2 inline-flex items-center gap-1 text-xs text-red-400"><AlertCircle className="w-3 h-3" /> taken</span>
            )}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-dark-300 mb-1.5">
            Email
          </label>
          <input
            type="email"
            value={profile.email}
            onChange={(e) => { onUpdate({ email: e.target.value }); setEmailVerifySent(false); setEmailVerifyError(''); }}
            className={inputClass}
            placeholder="Enter email"
          />
          {emailChanged && !emailVerifySent && (
            <button
              type="button"
              onClick={requestEmailVerification}
              className="mt-1.5 inline-flex items-center gap-1 text-xs font-medium text-forge-400 hover:text-forge-300"
            >
              <Mail className="w-3 h-3" /> Send verification email to new address
            </button>
          )}
          {emailVerifySent && <p className="text-xs text-forge-400 mt-1.5">Verification email sent — old address remains active until verified.</p>}
          {emailVerifyError && <p className="text-xs text-red-400 mt-1.5">{emailVerifyError}</p>}
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-dark-300 mb-1.5">
            Display Name
          </label>
          <input
            type="text"
            value={profile.displayName}
            onChange={(e) => onUpdate({ displayName: e.target.value })}
            className={inputClass}
            placeholder="Enter display name"
          />
          <p className="text-xs text-dark-500 mt-1">
            This is how your name appears to other players.
          </p>
        </div>
      </div>

      {/* ── Security Section ── */}
      <div className="border-t border-dark-700 pt-6 mt-6">
        <h2 className="text-lg font-semibold text-white mb-6">Security</h2>

        {/* Password */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <Lock className="w-4 h-4 text-dark-400" />
            <span className="text-sm font-medium text-dark-200">Password</span>
          </div>
          <p className="text-xs text-dark-500 mb-3">Last changed: Never</p>

          {passwordSuccess && (
            <div className="mb-3 rounded-md bg-forge-400/10 border border-forge-700 p-3 text-sm text-forge-400">
              {passwordSuccess}
            </div>
          )}

          {!showPasswordForm ? (
            <button
              onClick={() => {
                setPasswordSuccess('');
                setShowPasswordForm(true);
              }}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-forge-400 hover:text-forge-300 transition-colors"
            >
              Change Password &rarr;
            </button>
          ) : (
            <div className="space-y-3 rounded-lg border border-dark-700 bg-dark-900 p-4">
              {passwordError && (
                <div className="rounded-md bg-red-900/20 border border-red-800 p-3 text-sm text-red-400">
                  {passwordError}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-1.5">
                  Current Password
                </label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className={inputClass}
                  placeholder="Enter current password"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-1.5">
                  New Password
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className={inputClass}
                  placeholder="Min 8 characters"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-300 mb-1.5">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className={inputClass}
                  placeholder="Re-enter new password"
                />
              </div>

              <div className="flex items-center gap-3 pt-1">
                <button
                  onClick={resetPasswordForm}
                  className="rounded-md border border-dark-600 px-4 py-2 text-sm font-medium text-dark-300 hover:bg-dark-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleChangePassword}
                  disabled={submittingPassword}
                  className="rounded-md bg-forge-600 px-4 py-2 text-sm font-medium text-white hover:bg-forge-500 disabled:opacity-50 transition-colors"
                >
                  {submittingPassword ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Two-Factor Authentication */}
        <div className="mb-6">
          <TwoFactorSetup token={accessToken} />
        </div>

        {/* Connected Accounts */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Link2 className="w-4 h-4 text-dark-400" />
            <span className="text-sm font-medium text-dark-200">
              Connected Accounts
            </span>
          </div>

          <div className="space-y-3">
            {([
              { id: 'google', label: 'Google' },
              { id: 'discord', label: 'Discord' },
            ] as const).map((provider) => {
              const handle = oauth[provider.id];
              return (
                <div
                  key={provider.id}
                  className="flex items-center justify-between rounded-lg border border-dark-700 bg-dark-900 px-4 py-3"
                >
                  <div className="text-sm text-dark-300">
                    <span className="font-medium text-dark-200">{provider.label}:</span>{' '}
                    {handle ? <span className="text-forge-400">{handle}</span> : 'Not connected'}
                  </div>
                  {handle ? (
                    <button
                      onClick={() => disconnectOAuth(provider.id)}
                      className="rounded-md border border-red-500/30 px-3 py-1 text-xs font-medium text-red-300 hover:bg-red-500/10 transition-colors"
                    >
                      Disconnect
                    </button>
                  ) : (
                    <button
                      onClick={() => connectOAuth(provider.id)}
                      className="rounded-md border border-dark-600 px-3 py-1 text-xs font-medium text-dark-300 hover:border-forge-500 hover:text-forge-400 transition-colors"
                    >
                      Connect
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
