import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function LegalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-dark-950">
      <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
        <Link
          href="/dashboard"
          className="mb-8 inline-flex items-center gap-2 text-sm text-dark-400 transition-colors hover:text-forge-400"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to EsportsForge
        </Link>
        <div className="prose prose-invert max-w-none">
          {children}
        </div>
      </div>
    </div>
  );
}
