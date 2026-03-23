'use client';

import { Zap } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Opponent } from '@/types/opponent';

interface PrepNowButtonProps {
  opponent: Opponent;
  variant: 'card' | 'full';
}

export default function PrepNowButton({ opponent, variant }: PrepNowButtonProps) {
  const router = useRouter();

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    router.push(`/gameplan?opponent=${opponent.id}`);
  };

  if (variant === 'card') {
    return (
      <>
        {/* Desktop: overlay on hover */}
        <button
          onClick={handleClick}
          className="hidden lg:block absolute bottom-0 left-0 right-0 rounded-b-xl bg-forge-500 px-4 py-2.5 text-sm font-bold text-dark-950 text-center opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <span className="inline-flex items-center justify-center gap-1.5">
            <Zap className="w-4 h-4" />
            Prep Now
          </span>
        </button>

        {/* Mobile: always visible, static position */}
        <button
          onClick={handleClick}
          className="lg:hidden w-full mt-3 rounded-xl bg-forge-500 px-4 py-2.5 text-sm font-bold text-dark-950 text-center"
        >
          <span className="inline-flex items-center justify-center gap-1.5">
            <Zap className="w-4 h-4" />
            Prep Now
          </span>
        </button>
      </>
    );
  }

  return (
    <button
      onClick={handleClick}
      className="w-full rounded-xl bg-forge-500 px-4 py-3 font-bold text-dark-950 text-center transition-colors hover:bg-forge-400"
    >
      <span className="inline-flex items-center justify-center gap-2">
        <Zap className="w-5 h-5" />
        Prep Now vs {opponent.gamertag}
      </span>
      <p className="text-xs font-medium text-dark-950/70 mt-1">
        Generate gameplan + load kill sheet
      </p>
    </button>
  );
}
