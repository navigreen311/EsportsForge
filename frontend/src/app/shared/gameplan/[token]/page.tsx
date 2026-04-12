"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

interface SharedPlay {
  name?: string;
  formation?: string;
  concept?: string;
  notes?: string;
  [key: string]: unknown;
}

interface SharedGameplan {
  title: string;
  plays: SharedPlay[] | null;
  meta_snapshot: string | null;
  share_views: number;
  shared_by: string;
}

export default function SharedGameplanPage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const [gameplan, setGameplan] = useState<SharedGameplan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    async function fetchGameplan() {
      try {
        const res = await fetch(`/api/v1/share/gameplans/${params.token}`);
        if (!res.ok) {
          const data = await res.json().catch(() => null);
          throw new Error(data?.detail || "Gameplan not found or link has expired");
        }
        const data: SharedGameplan = await res.json();
        setGameplan(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load gameplan");
      } finally {
        setLoading(false);
      }
    }
    fetchGameplan();
  }, [params.token]);

  async function handleImport() {
    setImporting(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        router.push(`/auth/login?redirect=/shared/gameplan/${params.token}`);
        return;
      }
      const res = await fetch(`/api/v1/share/gameplans/${params.token}/import`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || "Import failed");
      }
      router.push("/dashboard/gameplan");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setImporting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-dark-300 text-lg">Loading shared gameplan...</div>
      </div>
    );
  }

  if (error || !gameplan) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-dark-100 mb-2">Gameplan Not Available</h1>
          <p className="text-dark-400">{error || "This share link is invalid or has expired."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 text-dark-50">
      {/* Header */}
      <header className="border-b border-dark-800 bg-dark-900/80 backdrop-blur">
        <div className="mx-auto max-w-4xl px-4 py-4 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-wider text-dark-400 mb-1">
              Shared by EsportsForge player
            </p>
            <h1 className="text-2xl font-bold text-dark-50">{gameplan.title}</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-dark-500">{gameplan.share_views} views</span>
            <button
              onClick={handleImport}
              disabled={importing}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-500 transition-colors disabled:opacity-50"
            >
              {importing ? "Importing..." : "Import to Your Account"}
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="mx-auto max-w-4xl px-4 py-8">
        {/* Meta Snapshot */}
        {gameplan.meta_snapshot && (
          <section className="mb-8 rounded-xl border border-dark-800 bg-dark-900 p-6">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-dark-400 mb-3">
              Meta Context
            </h2>
            <p className="text-dark-200 whitespace-pre-wrap">{gameplan.meta_snapshot}</p>
          </section>
        )}

        {/* Plays */}
        <section className="rounded-xl border border-dark-800 bg-dark-900 p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-dark-400 mb-4">
            Plays ({gameplan.plays?.length ?? 0})
          </h2>
          {gameplan.plays && gameplan.plays.length > 0 ? (
            <div className="space-y-3">
              {gameplan.plays.map((play, idx) => (
                <div
                  key={idx}
                  className="rounded-lg border border-dark-700 bg-dark-800 p-4"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs text-dark-500 mr-2">#{idx + 1}</span>
                      <span className="font-semibold text-dark-100">
                        {play.name || "Unnamed Play"}
                      </span>
                    </div>
                    {play.formation && (
                      <span className="rounded bg-dark-700 px-2 py-0.5 text-xs text-dark-300">
                        {play.formation}
                      </span>
                    )}
                  </div>
                  {play.concept && (
                    <p className="mt-2 text-sm text-dark-300">{play.concept}</p>
                  )}
                  {play.notes && (
                    <p className="mt-1 text-xs text-dark-500 italic">{play.notes}</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-dark-500">No plays in this gameplan.</p>
          )}
        </section>
      </main>
    </div>
  );
}
