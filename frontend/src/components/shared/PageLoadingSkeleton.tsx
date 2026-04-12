export default function PageLoadingSkeleton({ variant = 'dashboard' }: { variant?: 'dashboard' | 'list' | 'detail' | 'grid' | 'form' }) {
  const Bone = ({ className = '' }: { className?: string }) => (
    <div className={`animate-pulse rounded-lg bg-dark-700 ${className}`} />
  );

  if (variant === 'list') return (
    <div className="space-y-3 p-6">{Array.from({ length: 6 }).map((_, i) => <Bone key={i} className="h-16 w-full" />)}</div>
  );
  if (variant === 'detail') return (
    <div className="p-6 space-y-4"><Bone className="h-10 w-1/3" /><Bone className="h-64 w-full" /><Bone className="h-32 w-full" /></div>
  );
  if (variant === 'grid') return (
    <div className="p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">{Array.from({ length: 6 }).map((_, i) => <Bone key={i} className="h-48" />)}</div>
  );
  if (variant === 'form') return (
    <div className="p-6 space-y-4 max-w-2xl">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="space-y-2"><Bone className="h-4 w-24" /><Bone className="h-10 w-full" /></div>)}</div>
  );
  // dashboard
  return (
    <div className="p-6 space-y-4">
      <Bone className="h-10 w-1/3" />
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">{Array.from({ length: 4 }).map((_, i) => <Bone key={i} className="h-28" />)}</div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4"><Bone className="h-64" /><Bone className="h-64" /></div>
    </div>
  );
}
