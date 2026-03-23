"use client";

import Link from "next/link";
import { Crosshair, FlaskConical } from "lucide-react";

interface SimLabLaunchButtonProps {
  drillId: string;
  drillName: string;
  variant: "icon" | "full";
}

export default function SimLabLaunchButton({
  drillId,
  drillName,
  variant,
}: SimLabLaunchButtonProps) {
  const href = `/drills/simlab?drill=${drillId}`;

  if (variant === "icon") {
    return (
      <Link
        href={href}
        title="Test this skill in SimLab"
        className="p-1.5 rounded-md bg-dark-800/50 border border-dark-700/50 text-dark-400 hover:text-forge-400 hover:border-forge-500/50 transition-colors"
      >
        <Crosshair className="h-3.5 w-3.5" />
      </Link>
    );
  }

  return (
    <Link
      href={href}
      className="flex items-center gap-2 px-4 py-2 bg-dark-800 hover:bg-dark-700 text-dark-300 hover:text-forge-400 font-medium rounded-lg border border-dark-600 transition-colors text-sm"
    >
      <FlaskConical className="h-4 w-4" />
      Simulate in SimLab &rarr;
    </Link>
  );
}
