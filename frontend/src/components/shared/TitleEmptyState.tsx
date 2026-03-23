"use client";

import Link from "next/link";
import { Sparkles } from "lucide-react";

interface TitleEmptyStateProps {
  titleName: string;
  titleIcon: string;
}

export function TitleEmptyState({ titleName, titleIcon }: TitleEmptyStateProps) {
  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-12">
      <div className="flex min-h-[400px] flex-col items-center justify-center text-center">
        <span className="mb-4 text-5xl">{titleIcon}</span>
        <h3 className="mb-2 text-lg font-bold text-dark-300">
          No data yet for {titleName}
        </h3>
        <p className="mb-8 max-w-sm text-sm text-dark-500">
          Start your first session to activate AI agents for this title.
        </p>
        <Link
          href="/gameplan"
          className="inline-flex items-center gap-2 rounded-lg bg-forge-500 px-5 py-2.5 text-sm font-medium text-dark-950 transition-colors hover:bg-forge-400"
        >
          <Sparkles className="h-4 w-4" />
          Generate First Gameplan
        </Link>
      </div>
    </div>
  );
}
