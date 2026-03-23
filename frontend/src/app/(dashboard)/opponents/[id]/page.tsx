'use client';

import { useParams, useRouter } from 'next/navigation';
import { useOpponents } from '@/hooks/useOpponents';
import DossierView from '@/components/opponents/DossierView';
import { ArrowLeft, Users } from 'lucide-react';

export default function OpponentDossierPage() {
  const params = useParams();
  const router = useRouter();
  const { getOpponentById } = useOpponents();

  const opponent = getOpponentById(params.id as string);

  if (!opponent) {
    return (
      <div className="text-center py-16">
        <Users className="w-12 h-12 text-dark-600 mx-auto mb-3" />
        <p className="text-dark-400 font-medium">Opponent not found</p>
        <p className="text-dark-500 text-sm mt-1">
          This opponent may have been removed or the link is invalid.
        </p>
        <button
          onClick={() => router.push('/opponents')}
          className="mt-4 px-4 py-2 text-sm font-medium text-forge-400 hover:text-forge-300 transition-colors"
        >
          Back to Opponents
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={() => router.push('/opponents')}
        className="flex items-center gap-2 text-sm text-dark-400 hover:text-dark-200 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Opponents
      </button>

      {/* Dossier View */}
      <DossierView opponent={opponent} />
    </div>
  );
}
