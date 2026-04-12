/**
 * FeedbackButton — Fixed-position feedback link that opens a minimal modal.
 * Submits to POST /api/v1/support/feedback.
 */

'use client';

import { useState } from 'react';
import { usePathname } from 'next/navigation';
import { X, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import api from '@/lib/api';

type Rating = 'good' | 'okay' | 'bad';

const RATINGS: { value: Rating; emoji: string; label: string }[] = [
  { value: 'good', emoji: '\u{1F44D}', label: 'Good' },
  { value: 'okay', emoji: '\u{1F44C}', label: 'Okay' },
  { value: 'bad', emoji: '\u{1F44E}', label: 'Bad' },
];

export function FeedbackButton() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [rating, setRating] = useState<Rating | null>(null);
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const reset = () => {
    setRating(null);
    setMessage('');
    setSubmitted(false);
  };

  const handleClose = () => {
    setOpen(false);
    setTimeout(reset, 200);
  };

  const handleSend = async () => {
    if (!rating) return;
    setSubmitting(true);
    try {
      await api.post('/support/feedback', {
        rating,
        message: message.trim() || null,
        page: pathname,
      });
      setSubmitted(true);
      setTimeout(handleClose, 1500);
    } catch {
      // fail silently — feedback is low-priority
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      {/* Trigger */}
      <button
        type="button"
        onClick={() => {
          reset();
          setOpen(true);
        }}
        className="fixed bottom-4 left-4 z-40 text-xs font-medium text-dark-500 transition hover:text-dark-300"
      >
        Feedback
      </button>

      {/* Modal overlay */}
      {open && (
        <div className="fixed inset-0 z-50 flex items-end justify-start p-4 sm:items-end sm:justify-start">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/40"
            onClick={handleClose}
          />

          {/* Card */}
          <div className="relative w-full max-w-xs rounded-xl border border-dark-700/50 bg-dark-900 p-4 shadow-xl">
            {/* Close */}
            <button
              type="button"
              onClick={handleClose}
              className="absolute right-3 top-3 text-dark-500 hover:text-dark-300"
            >
              <X className="h-4 w-4" />
            </button>

            {submitted ? (
              <p className="py-4 text-center text-sm text-green-400">
                Thanks for the feedback!
              </p>
            ) : (
              <>
                <p className="mb-3 text-sm font-medium text-white">
                  How is your experience?
                </p>

                {/* Rating buttons */}
                <div className="mb-3 flex gap-2">
                  {RATINGS.map((r) => (
                    <button
                      key={r.value}
                      type="button"
                      onClick={() => setRating(r.value)}
                      className={clsx(
                        'flex flex-1 flex-col items-center gap-1 rounded-lg border px-3 py-2 text-xs transition',
                        rating === r.value
                          ? 'border-forge-500 bg-forge-500/10 text-white'
                          : 'border-dark-700 bg-dark-800 text-dark-400 hover:border-dark-600'
                      )}
                    >
                      <span className="text-lg">{r.emoji}</span>
                      {r.label}
                    </button>
                  ))}
                </div>

                {/* Optional message */}
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  maxLength={2000}
                  rows={2}
                  placeholder="Anything else? (optional)"
                  className="mb-3 w-full resize-none rounded-lg border border-dark-700 bg-dark-800 px-3 py-2 text-xs text-white placeholder-dark-500 outline-none transition focus:border-forge-500"
                />

                {/* Send */}
                <button
                  type="button"
                  disabled={!rating || submitting}
                  onClick={handleSend}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-forge-500 px-4 py-2 text-xs font-medium text-white transition hover:bg-forge-600 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : null}
                  {submitting ? 'Sending...' : 'Send'}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
}
