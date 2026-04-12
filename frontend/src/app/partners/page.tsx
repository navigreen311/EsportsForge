'use client';

import { useState } from 'react';
import {
  Users,
  DollarSign,
  Palette,
  BadgeCheck,
  Send,
  Handshake,
  ChevronRight,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Benefits
// ---------------------------------------------------------------------------

const BENEFITS = [
  {
    icon: Users,
    title: 'Bulk Seats',
    description:
      'Discounted team and organization-wide pricing. Scale your roster without scaling your costs.',
  },
  {
    icon: DollarSign,
    title: 'Affiliate Commission',
    description:
      'Earn recurring commissions for every player who signs up through your referral link.',
  },
  {
    icon: Palette,
    title: 'Co-Branded Exports',
    description:
      'Generate gameplans, scouting reports, and analytics branded with your logo.',
  },
  {
    icon: BadgeCheck,
    title: 'Featured Badge',
    description:
      'Stand out with a verified partner badge on your profile and all shared content.',
  },
];

const PLATFORMS = [
  'YouTube',
  'Twitch',
  'Twitter / X',
  'TikTok',
  'Discord',
  'Other',
];

const ROLES = [
  'Esports Org',
  'Coach',
  'Content Creator',
  'Tournament Organizer',
  'Other',
];

const AUDIENCE_SIZES = [
  'Under 1K',
  '1K - 10K',
  '10K - 50K',
  '50K - 100K',
  '100K+',
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function PartnersPage() {
  const [formData, setFormData] = useState({
    name: '',
    org: '',
    role: '',
    platform: '',
    audienceSize: '',
  });
  const [submitted, setSubmitted] = useState(false);

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // Mock submit
    setSubmitted(true);
  }

  return (
    <div className="min-h-screen bg-[#0A0C10] text-zinc-100">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-green-500/5 to-transparent pointer-events-none" />
        <div className="max-w-4xl mx-auto px-6 py-20 text-center relative z-10">
          <div className="inline-flex items-center gap-2 bg-green-500/10 border border-green-500/20 rounded-full px-4 py-1.5 mb-6">
            <Handshake className="h-4 w-4 text-green-400" />
            <span className="text-sm text-green-400 font-medium">
              Partner Program
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Are you an esports org, coach,
            <br />
            or content creator?
          </h1>
          <p className="text-lg text-zinc-400 max-w-2xl mx-auto">
            Partner with EsportsForge to give your audience the competitive edge.
            Earn while you grow your community.
          </p>
        </div>
      </section>

      {/* Benefits */}
      <section className="max-w-5xl mx-auto px-6 pb-16">
        <h2 className="text-xl font-semibold mb-8 text-center">
          Partner Benefits
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {BENEFITS.map((b) => (
            <div
              key={b.title}
              className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-6 flex gap-4 hover:border-green-500/30 transition-colors"
            >
              <div className="bg-green-500/10 rounded-lg p-3 h-fit">
                <b.icon className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <h3 className="font-semibold mb-1">{b.title}</h3>
                <p className="text-sm text-zinc-400">{b.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Application Form */}
      <section className="max-w-xl mx-auto px-6 pb-20">
        <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-8">
          <h2 className="text-xl font-semibold mb-6 text-center">
            Apply to Partner
          </h2>

          {submitted ? (
            <div className="text-center py-8">
              <div className="bg-green-500/10 rounded-full p-4 w-fit mx-auto mb-4">
                <BadgeCheck className="h-8 w-8 text-green-400" />
              </div>
              <h3 className="text-lg font-semibold mb-2">
                Application Received!
              </h3>
              <p className="text-sm text-zinc-400">
                We will review your application and get back to you within 48
                hours.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm text-zinc-400 mb-1.5">
                  Your Name
                </label>
                <input
                  type="text"
                  name="name"
                  required
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-green-500/40"
                  placeholder="John Doe"
                />
              </div>

              {/* Org */}
              <div>
                <label className="block text-sm text-zinc-400 mb-1.5">
                  Organization
                </label>
                <input
                  type="text"
                  name="org"
                  required
                  value={formData.org}
                  onChange={handleChange}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-green-500/40"
                  placeholder="FaZe Clan, NRG, etc."
                />
              </div>

              {/* Role */}
              <div>
                <label className="block text-sm text-zinc-400 mb-1.5">
                  Role
                </label>
                <select
                  name="role"
                  required
                  value={formData.role}
                  onChange={handleChange}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-green-500/40"
                >
                  <option value="" disabled>
                    Select your role
                  </option>
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>

              {/* Platform */}
              <div>
                <label className="block text-sm text-zinc-400 mb-1.5">
                  Primary Platform
                </label>
                <select
                  name="platform"
                  required
                  value={formData.platform}
                  onChange={handleChange}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-green-500/40"
                >
                  <option value="" disabled>
                    Select a platform
                  </option>
                  {PLATFORMS.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>

              {/* Audience Size */}
              <div>
                <label className="block text-sm text-zinc-400 mb-1.5">
                  Audience Size
                </label>
                <select
                  name="audienceSize"
                  required
                  value={formData.audienceSize}
                  onChange={handleChange}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2.5 text-sm text-zinc-100 focus:outline-none focus:ring-2 focus:ring-green-500/40"
                >
                  <option value="" disabled>
                    Select audience size
                  </option>
                  {AUDIENCE_SIZES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              {/* Submit */}
              <button
                type="submit"
                className="w-full bg-green-500 hover:bg-green-600 text-black font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2 mt-6"
              >
                <Send className="h-4 w-4" />
                Apply Now
                <ChevronRight className="h-4 w-4" />
              </button>
            </form>
          )}
        </div>
      </section>
    </div>
  );
}
