/**
 * Support — Submit tickets and view ticket history.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  LifeBuoy,
  Send,
  Clock,
  CheckCircle2,
  Loader2,
  AlertCircle,
  ChevronDown,
} from 'lucide-react';
import { clsx } from 'clsx';
import api from '@/lib/api';

// ---------- Types ----------

interface Ticket {
  id: string;
  subject: string;
  body: string;
  category: string;
  priority: string;
  status: string;
  created_at: string;
  updated_at: string;
  admin_notes: string | null;
}

type Category = 'billing' | 'bug' | 'account' | 'feature' | 'other';

const CATEGORIES: { value: Category; label: string }[] = [
  { value: 'billing', label: 'Billing' },
  { value: 'bug', label: 'Bug Report' },
  { value: 'account', label: 'Account Issue' },
  { value: 'feature', label: 'Feature Request' },
  { value: 'other', label: 'Other' },
];

const STATUS_STYLES: Record<string, string> = {
  open: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  in_progress: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  resolved: 'bg-green-500/20 text-green-400 border-green-500/30',
};

const STATUS_LABELS: Record<string, string> = {
  open: 'Open',
  in_progress: 'In Progress',
  resolved: 'Resolved',
};

// ---------- Component ----------

export default function SupportPage() {
  // Form state
  const [subject, setSubject] = useState('');
  const [category, setCategory] = useState<Category>('other');
  const [body, setBody] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Tickets state
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchTickets = useCallback(async () => {
    try {
      const res = await api.get('/support/tickets');
      setTickets(res.data.tickets ?? []);
    } catch {
      // silent — tickets section just stays empty
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !body.trim()) return;

    setSubmitting(true);
    setSubmitError('');
    setSubmitSuccess(false);

    try {
      await api.post('/support/tickets', { subject, category, body });
      setSubject('');
      setCategory('other');
      setBody('');
      setSubmitSuccess(true);
      fetchTickets();
      setTimeout(() => setSubmitSuccess(false), 4000);
    } catch (err: any) {
      setSubmitError(err?.response?.data?.detail || 'Failed to submit ticket. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-forge-500/20">
          <LifeBuoy className="h-5 w-5 text-forge-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Support</h1>
          <p className="text-sm text-dark-400">Submit a ticket and we'll get back to you.</p>
        </div>
      </div>

      {/* Ticket Form */}
      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-xl border border-dark-700/50 bg-dark-900/80 p-6"
      >
        <h2 className="text-lg font-semibold text-white">New Ticket</h2>

        {/* Subject */}
        <div>
          <label htmlFor="subject" className="mb-1 block text-sm font-medium text-dark-300">
            Subject
          </label>
          <input
            id="subject"
            type="text"
            maxLength={500}
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Brief description of your issue"
            className="w-full rounded-lg border border-dark-700 bg-dark-800 px-4 py-2.5 text-sm text-white placeholder-dark-500 outline-none transition focus:border-forge-500 focus:ring-1 focus:ring-forge-500"
            required
          />
        </div>

        {/* Category */}
        <div>
          <label htmlFor="category" className="mb-1 block text-sm font-medium text-dark-300">
            Category
          </label>
          <div className="relative">
            <select
              id="category"
              value={category}
              onChange={(e) => setCategory(e.target.value as Category)}
              className="w-full appearance-none rounded-lg border border-dark-700 bg-dark-800 px-4 py-2.5 pr-10 text-sm text-white outline-none transition focus:border-forge-500 focus:ring-1 focus:ring-forge-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dark-500" />
          </div>
        </div>

        {/* Body */}
        <div>
          <label htmlFor="body" className="mb-1 block text-sm font-medium text-dark-300">
            Message
          </label>
          <textarea
            id="body"
            maxLength={2000}
            rows={5}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Describe your issue in detail..."
            className="w-full resize-none rounded-lg border border-dark-700 bg-dark-800 px-4 py-2.5 text-sm text-white placeholder-dark-500 outline-none transition focus:border-forge-500 focus:ring-1 focus:ring-forge-500"
            required
          />
          <p className="mt-1 text-right text-xs text-dark-500">{body.length}/2000</p>
        </div>

        {/* Errors / Success */}
        {submitError && (
          <div className="flex items-center gap-2 text-sm text-red-400">
            <AlertCircle className="h-4 w-4" />
            {submitError}
          </div>
        )}
        {submitSuccess && (
          <div className="flex items-center gap-2 text-sm text-green-400">
            <CheckCircle2 className="h-4 w-4" />
            Ticket submitted successfully!
          </div>
        )}

        {/* Submit */}
        <button
          type="submit"
          disabled={submitting || !subject.trim() || !body.trim()}
          className="inline-flex items-center gap-2 rounded-lg bg-forge-500 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-forge-600 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {submitting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
          {submitting ? 'Submitting...' : 'Submit Ticket'}
        </button>
      </form>

      {/* Ticket History */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-white">Your Tickets</h2>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-dark-500" />
          </div>
        ) : tickets.length === 0 ? (
          <div className="rounded-xl border border-dark-700/50 bg-dark-900/80 px-6 py-12 text-center">
            <LifeBuoy className="mx-auto h-8 w-8 text-dark-600" />
            <p className="mt-2 text-sm text-dark-400">No tickets yet.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {tickets.map((ticket) => (
              <div
                key={ticket.id}
                className="rounded-xl border border-dark-700/50 bg-dark-900/80 transition hover:border-dark-600/50"
              >
                <button
                  type="button"
                  onClick={() => setExpandedId(expandedId === ticket.id ? null : ticket.id)}
                  className="flex w-full items-center justify-between px-5 py-4 text-left"
                >
                  <div className="flex flex-1 items-center gap-3 overflow-hidden">
                    <span
                      className={clsx(
                        'inline-flex shrink-0 items-center rounded-full border px-2.5 py-0.5 text-xs font-medium',
                        STATUS_STYLES[ticket.status] ?? STATUS_STYLES.open
                      )}
                    >
                      {STATUS_LABELS[ticket.status] ?? ticket.status}
                    </span>
                    <span className="truncate text-sm font-medium text-white">
                      {ticket.subject}
                    </span>
                  </div>
                  <div className="ml-4 flex shrink-0 items-center gap-3">
                    <span className="hidden text-xs text-dark-500 sm:inline">
                      <Clock className="mr-1 inline h-3 w-3" />
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </span>
                    <ChevronDown
                      className={clsx(
                        'h-4 w-4 text-dark-500 transition-transform',
                        expandedId === ticket.id && 'rotate-180'
                      )}
                    />
                  </div>
                </button>

                {expandedId === ticket.id && (
                  <div className="border-t border-dark-700/50 px-5 py-4">
                    <div className="mb-2 flex flex-wrap gap-2 text-xs text-dark-400">
                      <span className="rounded bg-dark-800 px-2 py-0.5 capitalize">
                        {ticket.category}
                      </span>
                      <span className="rounded bg-dark-800 px-2 py-0.5 capitalize">
                        {ticket.priority} priority
                      </span>
                    </div>
                    <p className="whitespace-pre-wrap text-sm text-dark-300">{ticket.body}</p>
                    {ticket.admin_notes && (
                      <div className="mt-3 rounded-lg border border-forge-500/20 bg-forge-500/5 p-3">
                        <p className="text-xs font-medium text-forge-400">Admin Response</p>
                        <p className="mt-1 whitespace-pre-wrap text-sm text-dark-300">
                          {ticket.admin_notes}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
