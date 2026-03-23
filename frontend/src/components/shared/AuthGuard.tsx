/**
 * Protected route wrapper — redirects unauthenticated users to /login.
 */

"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

interface AuthGuardProps {
  children: React.ReactNode;
  requiredTier?: string;
}

export function AuthGuard({ children, requiredTier }: AuthGuardProps) {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === "loading") return;
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  // Tier check
  useEffect(() => {
    if (!requiredTier || status !== "authenticated" || !session?.user) return;

    const tierOrder = ["free", "competitive", "elite", "team"];
    const userLevel = tierOrder.indexOf(session.user.tier);
    const requiredLevel = tierOrder.indexOf(requiredTier);

    if (userLevel < requiredLevel) {
      router.push("/?upgrade=true");
    }
  }, [requiredTier, session, status, router]);

  if (status === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-dark-950">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-forge-500 border-t-transparent" />
      </div>
    );
  }

  if (status === "unauthenticated") {
    return null;
  }

  return <>{children}</>;
}
