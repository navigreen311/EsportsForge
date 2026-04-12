'use client';
import PageErrorFallback from '@/components/shared/PageErrorFallback';
export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return <PageErrorFallback error={error} reset={reset} />;
}

