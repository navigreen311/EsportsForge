'use client';

import { useState } from 'react';
import { User, Camera, Lock, Shield, Link2 } from 'lucide-react';
import type { ProfileSettings } from '@/types/settings';
import TwoFactorSetup from './TwoFactorSetup';

interface ProfileFormProps {
  profile: ProfileSettings;
  onUpdate: (profile: Partial<ProfileSettings>) => void;
}

const inputClass =
  'w-full rounded-lg border border-dark-600 bg-dark-800 px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:border-forge-500 focus:ring-1 focus:ring-forge-500 focus:outline-none transition-colors';

export default function ProfileForm({ profile, onUpdate }: ProfileFormProps) {
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [submittingPassword, setSubmittingPassword] = useState(false);

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
      const res = await fetch('/api/v1/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
      {/* Avatar Upload Placeholder */}
      <div className="flex items-center gap-6">
        <div className="relative">
          <div className="w-20 h-20 rounded-full bg-dark-800 border-2 border-dark-600 flex items-center justify-center">
            {profile.avatarUrl ? (
              <img
                src={profile.avatarUrl}
                alt="Avatar"
                className="w-full h-full rounded-full object-cover"
              />
            ) : (
              <User className="w-8 h-8 text-dark-500" />
            )}
          </div>
          <button
            className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-forge-600 hover:bg-forge-500 border-2 border-dark-900 flex items-center justify-center transition-colors"
            title="Upload avatar"
          >
            <Camera className="w-3.5 h-3.5 text-white" />
          </button>
        </div>
        <div>
          <p className="text-sm font-medium text-dark-200">Profile Photo</p>
          <p className="text-xs text-dark-500 mt-0.5">JPG, PNG or GIF. Max 2MB.</p>
        </div>
      </div>

      {/* Form Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-1.5">
            Username
          </label>
          <input
            type="text"
            value={profile.username}
            onChange={(e) => onUpdate({ username: e.target.value })}
            className={inputClass}
            placeholder="Enter username"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-dark-300 mb-1.5">
            Email
          </label>
          <input
            type="email"
            value={profile.email}
            onChange={(e) => onUpdate({ email: e.target.value })}
            className={inputClass}
            placeholder="Enter email"
          />
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
          <TwoFactorSetup token="" />
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
            {(['Google', 'Discord'] as const).map((provider) => (
              <div
                key={provider}
                className="flex items-center justify-between rounded-lg border border-dark-700 bg-dark-900 px-4 py-3"
              >
                <div className="text-sm text-dark-300">
                  <span className="font-medium text-dark-200">{provider}:</span>{' '}
                  Not connected
                </div>
                <button
                  onClick={() => alert('Coming soon')}
                  className="rounded-md border border-dark-600 px-3 py-1 text-xs font-medium text-dark-300 hover:border-forge-500 hover:text-forge-400 transition-colors"
                >
                  Connect
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
