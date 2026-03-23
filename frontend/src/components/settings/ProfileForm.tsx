'use client';

import { User, Camera } from 'lucide-react';
import type { ProfileSettings } from '@/types/settings';

interface ProfileFormProps {
  profile: ProfileSettings;
  onUpdate: (profile: Partial<ProfileSettings>) => void;
}

export default function ProfileForm({ profile, onUpdate }: ProfileFormProps) {
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
            className="w-full rounded-lg border border-dark-600 bg-dark-800 px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:border-forge-500 focus:ring-1 focus:ring-forge-500 focus:outline-none transition-colors"
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
            className="w-full rounded-lg border border-dark-600 bg-dark-800 px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:border-forge-500 focus:ring-1 focus:ring-forge-500 focus:outline-none transition-colors"
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
            className="w-full rounded-lg border border-dark-600 bg-dark-800 px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:border-forge-500 focus:ring-1 focus:ring-forge-500 focus:outline-none transition-colors"
            placeholder="Enter display name"
          />
          <p className="text-xs text-dark-500 mt-1">
            This is how your name appears to other players.
          </p>
        </div>
      </div>
    </div>
  );
}
