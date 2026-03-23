'use client';

import { Brain } from 'lucide-react';
import clsx from 'clsx';

interface Prediction {
  situation: string;
  predictedPlay: string;
  frequency: number;
  confidence: number;
}

interface PredictionEngineProps {
  opponentId: string;
  gamesAnalyzed: number;
}

const predictionsByOpponent: Record<string, Prediction[]> = {
  'opp-1': [
    { situation: '3rd & 7, trailing', predictedPlay: 'Cover 0 Blitz', frequency: 73, confidence: 88 },
    { situation: 'Red zone, tied', predictedPlay: 'Pinch Buck O', frequency: 61, confidence: 82 },
    { situation: '2-min drill', predictedPlay: 'Mid Blitz', frequency: 58, confidence: 75 },
    { situation: '1st down, leading', predictedPlay: 'Tampa 2', frequency: 52, confidence: 71 },
  ],
  'opp-2': [
    { situation: '3rd & long, trailing', predictedPlay: 'Cover 3 Sky', frequency: 68, confidence: 85 },
    { situation: 'Goal line, leading', predictedPlay: 'Goal Line Bear', frequency: 64, confidence: 80 },
    { situation: '2-min drill', predictedPlay: 'Dime Flat', frequency: 55, confidence: 72 },
    { situation: '1st down, tied', predictedPlay: 'Cover 4 Palms', frequency: 49, confidence: 65 },
  ],
  'opp-3': [
    { situation: '2nd & short, leading', predictedPlay: 'Under Smoke', frequency: 70, confidence: 90 },
    { situation: 'Red zone, trailing', predictedPlay: 'Fire Zone 3', frequency: 62, confidence: 78 },
    { situation: '3rd & medium', predictedPlay: 'Cover 2 Man', frequency: 57, confidence: 74 },
    { situation: '1st down, trailing', predictedPlay: 'Nickel Blitz', frequency: 50, confidence: 58 },
  ],
  'opp-4': [
    { situation: '3rd & 10+, tied', predictedPlay: 'Prevent', frequency: 77, confidence: 92 },
    { situation: 'Red zone, leading', predictedPlay: 'Cover 1 Robber', frequency: 63, confidence: 81 },
    { situation: '2-min drill', predictedPlay: 'Quarters', frequency: 54, confidence: 69 },
    { situation: '2nd & long, trailing', predictedPlay: 'Storm Brave', frequency: 48, confidence: 62 },
  ],
  'opp-5': [
    { situation: '1st down, tied', predictedPlay: 'Cover 6', frequency: 66, confidence: 84 },
    { situation: '3rd & short, leading', predictedPlay: 'Pinch Dog 2 Press', frequency: 60, confidence: 77 },
    { situation: 'Red zone, trailing', predictedPlay: 'Man Blitz 3', frequency: 53, confidence: 70 },
    { situation: '2-min drill', predictedPlay: 'Dime 3-2-6', frequency: 47, confidence: 55 },
  ],
  'opp-6': [
    { situation: '3rd & 5, trailing', predictedPlay: 'Cover 3 Match', frequency: 71, confidence: 87 },
    { situation: 'Goal line, tied', predictedPlay: '5-2 Goal Line', frequency: 65, confidence: 83 },
    { situation: '2nd & medium, leading', predictedPlay: 'Tampa 2 Under', frequency: 56, confidence: 73 },
    { situation: '1st down, trailing', predictedPlay: 'Nickel 2-4-5', frequency: 51, confidence: 67 },
  ],
};

function confidenceBadgeClass(confidence: number): string {
  if (confidence >= 80) return 'bg-green-500/20 text-green-400';
  if (confidence >= 60) return 'bg-amber-500/20 text-amber-400';
  return 'bg-red-500/20 text-red-400';
}

export default function PredictionEngine({ opponentId, gamesAnalyzed }: PredictionEngineProps) {
  const predictions = predictionsByOpponent[opponentId] ?? [];

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center gap-3 mb-4">
        <Brain className="h-5 w-5 text-forge-400" />
        <div>
          <h2 className="text-lg font-semibold text-dark-50">Opponent Prediction Engine</h2>
          <p className="text-sm text-dark-400">Based on {gamesAnalyzed} games</p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="pb-2 text-xs font-medium uppercase tracking-wider text-dark-400">Situation</th>
              <th className="pb-2 text-xs font-medium uppercase tracking-wider text-dark-400">Predicted Play</th>
              <th className="pb-2 text-xs font-medium uppercase tracking-wider text-dark-400">Freq%</th>
              <th className="pb-2 text-xs font-medium uppercase tracking-wider text-dark-400">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-800">
            {predictions.map((p) => (
              <tr key={p.situation}>
                <td className="py-3 pr-4 text-sm text-dark-200">{p.situation}</td>
                <td className="py-3 pr-4 text-sm font-medium text-dark-100">{p.predictedPlay}</td>
                <td className="py-3 pr-4 text-sm tabular-nums text-dark-300">{p.frequency}%</td>
                <td className="py-3">
                  <span
                    className={clsx(
                      'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                      confidenceBadgeClass(p.confidence),
                    )}
                  >
                    {p.confidence}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
