'use client';

import Link from 'next/link';

export function Footer() {
  return (
    <footer className="border-t border-dark-800 bg-dark-950 px-6 py-4">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-2 sm:flex-row">
        <p className="text-xs text-dark-500">
          &copy; 2026 Green Companies LLC. All rights reserved.
        </p>
        <nav className="flex items-center gap-4">
          <Link href="/legal/terms" className="text-xs text-dark-500 hover:text-dark-300 transition-colors">
            Terms of Service
          </Link>
          <Link href="/legal/privacy" className="text-xs text-dark-500 hover:text-dark-300 transition-colors">
            Privacy Policy
          </Link>
          <Link href="/legal/responsible-gambling" className="text-xs text-dark-500 hover:text-dark-300 transition-colors">
            Responsible Gaming
          </Link>
        </nav>
      </div>
    </footer>
  );
}
