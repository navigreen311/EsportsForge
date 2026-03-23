'use client';

import { AudibleNode, Play } from '@/types/gameplan';
import { GitBranch, ArrowRight, AlertTriangle } from 'lucide-react';

interface AudibleTreeProps {
  play: Play | null;
}

function AudibleBranch({ node, depth }: { node: AudibleNode; depth: number }) {
  return (
    <div className={`${depth > 0 ? 'ml-6 border-l border-dark-700 pl-4' : ''}`}>
      <div className="flex items-start gap-3 py-2">
        <div className="flex-shrink-0 mt-1">
          {depth === 0 ? (
            <div className="w-6 h-6 rounded-full bg-forge-500/20 border border-forge-500/30 flex items-center justify-center">
              <GitBranch className="w-3.5 h-3.5 text-forge-400" />
            </div>
          ) : (
            <ArrowRight className="w-4 h-4 text-dark-500" />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-dark-100">{node.label}</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <AlertTriangle className="w-3 h-3 text-yellow-500" />
            <span className="text-xs text-yellow-500/80">{node.trigger}</span>
          </div>
          <p className="text-xs text-dark-400 mt-0.5">
            Audible to: <span className="text-forge-400 font-medium">{node.targetPlay}</span>
          </p>
        </div>
      </div>
      {node.children?.map((child) => (
        <AudibleBranch key={child.id} node={child} depth={depth + 1} />
      ))}
    </div>
  );
}

export default function AudibleTree({ play }: AudibleTreeProps) {
  if (!play) {
    return (
      <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
        <div className="flex items-center gap-3 mb-4">
          <GitBranch className="w-5 h-5 text-dark-500" />
          <h2 className="text-lg font-bold text-dark-300">Audible Tree</h2>
        </div>
        <div className="text-center py-8 text-dark-500">
          <GitBranch className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Select a play to view its audible tree</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-dark-700 bg-dark-900/50 p-6">
      <div className="flex items-center gap-3 mb-4">
        <GitBranch className="w-5 h-5 text-forge-400" />
        <div>
          <h2 className="text-lg font-bold text-dark-100">Audible Tree</h2>
          <p className="text-sm text-dark-400">{play.name}</p>
        </div>
      </div>

      {play.audibleOptions && play.audibleOptions.length > 0 ? (
        <div className="space-y-1">
          {play.audibleOptions.map((node) => (
            <AudibleBranch key={node.id} node={node} depth={0} />
          ))}
        </div>
      ) : (
        <div className="text-center py-6 text-dark-500">
          <p className="text-sm">No audibles configured for this play</p>
        </div>
      )}
    </div>
  );
}
