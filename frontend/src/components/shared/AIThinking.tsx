'use client';

export function AIThinking() {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-dark-700 bg-dark-900 px-4 py-3">
      <div className="relative h-5 w-5">
        <div className="absolute inset-0 animate-spin rounded-full border-2 border-forge-400 border-t-transparent" />
      </div>
      <span className="text-sm font-medium text-dark-200">
        ForgeCore is thinking...
      </span>
    </div>
  );
}
