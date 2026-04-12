'use client';

interface LoadingSkeletonProps {
  variant?: 'card' | 'list' | 'text' | 'chart';
  count?: number;
}

function SkeletonPulse({ className }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded bg-dark-800 ${className ?? ''}`}
    />
  );
}

function CardSkeleton() {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900 p-6 space-y-4">
      <SkeletonPulse className="h-4 w-1/3" />
      <SkeletonPulse className="h-8 w-1/2" />
      <SkeletonPulse className="h-3 w-full" />
      <SkeletonPulse className="h-3 w-2/3" />
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="flex items-center gap-3 rounded-lg border border-dark-700 bg-dark-900 p-4">
          <SkeletonPulse className="h-10 w-10 rounded-full" />
          <div className="flex-1 space-y-2">
            <SkeletonPulse className="h-4 w-2/5" />
            <SkeletonPulse className="h-3 w-3/5" />
          </div>
        </div>
      ))}
    </div>
  );
}

function TextSkeleton() {
  return (
    <div className="space-y-2">
      <SkeletonPulse className="h-4 w-full" />
      <SkeletonPulse className="h-4 w-5/6" />
      <SkeletonPulse className="h-4 w-4/6" />
      <SkeletonPulse className="h-4 w-full" />
      <SkeletonPulse className="h-4 w-3/4" />
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900 p-6">
      <SkeletonPulse className="h-4 w-1/4 mb-4" />
      <div className="flex items-end gap-2 h-40">
        {[40, 65, 30, 80, 55, 70, 45, 90, 60, 75].map((h, i) => (
          <SkeletonPulse key={i} className="flex-1" style={{ height: `${h}%` }} />
        ))}
      </div>
    </div>
  );
}

export function LoadingSkeleton({ variant = 'card', count = 1 }: LoadingSkeletonProps) {
  const Component = {
    card: CardSkeleton,
    list: ListSkeleton,
    text: TextSkeleton,
    chart: ChartSkeleton,
  }[variant];

  return (
    <div className="space-y-4">
      {[...Array(count)].map((_, i) => (
        <Component key={i} />
      ))}
    </div>
  );
}
