"use client";

import Link from "next/link";
import { FlaskConical } from "lucide-react";

interface SimLabButtonProps {
  playId: string;
  playName: string;
  opponentName: string;
}

export default function SimLabButton({
  playId,
  playName,
  opponentName,
}: SimLabButtonProps) {
  return (
    <Link
      href={`/drills/simlab?play=${playId}&opponent=${opponentName}`}
      title={`Test ${playName} vs. ${opponentName}'s coverage tendencies in SimLab`}
      className="inline-flex items-center gap-2 rounded-lg border border-dark-600 bg-dark-800/50 px-3 py-1.5 text-xs font-medium text-dark-200 transition-colors hover:border-forge-500/50 hover:bg-dark-800 hover:text-forge-400"
    >
      <FlaskConical className="h-3.5 w-3.5" />
      Simulate
    </Link>
  );
}
