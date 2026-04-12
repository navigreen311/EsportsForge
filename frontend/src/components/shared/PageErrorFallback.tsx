'use client';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import Link from 'next/link';

export default function PageErrorFallback({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
      <AlertTriangle className="w-12 h-12 text-red-400 mb-4" />
      <h2 className="text-xl font-bold text-dark-100 mb-2">Something went wrong</h2>
      <p className="text-dark-400 text-sm mb-6 text-center max-w-md">{error.message || 'An unexpected error occurred. Please try again.'}</p>
      <div className="flex gap-3">
        <button onClick={reset} className="flex items-center gap-2 rounded-lg bg-forge-600 px-4 py-2 text-sm font-medium text-white hover:bg-forge-500 transition-colors">
          <RefreshCw className="w-4 h-4" /> Try Again
        </button>
        <Link href="/dashboard" className="flex items-center gap-2 rounded-lg border border-dark-600 bg-dark-800 px-4 py-2 text-sm font-medium text-dark-200 hover:bg-dark-700 transition-colors">
          <Home className="w-4 h-4" /> Dashboard
        </Link>
      </div>
    </div>
  );
}
