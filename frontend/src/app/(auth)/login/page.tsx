/**
 * Login page — email/password form with dark theme and forge-green accents.
 */

"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const result = await signIn("credentials", {
        redirect: false,
        email,
        password,
      });

      if (result?.error) {
        setError("Invalid email or password. Please try again.");
      } else {
        router.push(callbackUrl);
        router.refresh();
      }
    } catch {
      setError("An unexpected error occurred. Please try again.");
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
          <p className="mt-2 text-dark-400">Sign in to your account</p>
        </div>

        {/* Form Card */}
        <div className="rounded-xl border border-dark-700 bg-dark-900 p-8 shadow-lg">
          <form onSubmit={handleSubmit} className="space-y-6">
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
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-dark-200">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full rounded-lg border border-dark-600 bg-dark-800 px-4 py-2.5 text-dark-50 placeholder-dark-500 transition-colors focus:border-forge-500 focus:outline-none focus:ring-1 focus:ring-forge-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-forge-500 px-4 py-2.5 font-semibold text-dark-950 transition-colors hover:bg-forge-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-dark-400">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-medium text-forge-400 hover:text-forge-300">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
