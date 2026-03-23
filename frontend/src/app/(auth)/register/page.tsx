/**
 * Registration page — dark theme with forge-green accents.
 */

"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RegisterPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);

    try {
      // Register with FastAPI
      await axios.post(`${API_BASE_URL}/api/v1/auth/register`, {
        email,
        username,
        password,
        display_name: displayName || undefined,
      });

      // Auto-login after registration
      const result = await signIn("credentials", {
        redirect: false,
        email,
        password,
      });

      if (result?.error) {
        setError("Registration succeeded but auto-login failed. Please sign in manually.");
      } else {
        router.push("/");
        router.refresh();
      }
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-dark-950 px-4">
      <div className="w-full max-w-md space-y-8">
        {/* Logo / Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-forge-400">EsportsForge</h1>
          <p className="mt-2 text-dark-400">Create your account</p>
        </div>

        {/* Form Card */}
        <div className="rounded-xl border border-dark-700 bg-dark-900 p-8 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-dark-200">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-lg border border-dark-600 bg-dark-800 px-4 py-2.5 text-dark-50 placeholder-dark-500 transition-colors focus:border-forge-500 focus:outline-none focus:ring-1 focus:ring-forge-500"
              />
            </div>

            <div>
              <label htmlFor="username" className="mb-1.5 block text-sm font-medium text-dark-200">
                Username
              </label>
              <input
                id="username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="forge_player"
                pattern="^[a-zA-Z0-9_-]+$"
                minLength={3}
                maxLength={50}
                className="w-full rounded-lg border border-dark-600 bg-dark-800 px-4 py-2.5 text-dark-50 placeholder-dark-500 transition-colors focus:border-forge-500 focus:outline-none focus:ring-1 focus:ring-forge-500"
              />
              <p className="mt-1 text-xs text-dark-500">Letters, numbers, hyphens, and underscores only.</p>
            </div>

            <div>
              <label htmlFor="displayName" className="mb-1.5 block text-sm font-medium text-dark-200">
                Display Name <span className="text-dark-500">(optional)</span>
              </label>
              <input
                id="displayName"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Your display name"
                maxLength={100}
                className="w-full rounded-lg border border-dark-600 bg-dark-800 px-4 py-2.5 text-dark-50 placeholder-dark-500 transition-colors focus:border-forge-500 focus:outline-none focus:ring-1 focus:ring-forge-500"
              />
            </div>

            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-dark-200">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min. 8 characters"
                minLength={8}
                className="w-full rounded-lg border border-dark-600 bg-dark-800 px-4 py-2.5 text-dark-50 placeholder-dark-500 transition-colors focus:border-forge-500 focus:outline-none focus:ring-1 focus:ring-forge-500"
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="mb-1.5 block text-sm font-medium text-dark-200">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat your password"
                minLength={8}
                className="w-full rounded-lg border border-dark-600 bg-dark-800 px-4 py-2.5 text-dark-50 placeholder-dark-500 transition-colors focus:border-forge-500 focus:outline-none focus:ring-1 focus:ring-forge-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-forge-500 px-4 py-2.5 font-semibold text-dark-950 transition-colors hover:bg-forge-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-dark-400">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-forge-400 hover:text-forge-300">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
