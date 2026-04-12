/**
 * ForgeCore Chat — Floating chat button + slide-up panel.
 * Provides quick access to ForgeCore AI assistant from any dashboard page.
 */

'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { MessageCircle, Send, X, Sparkles } from 'lucide-react';
import { clsx } from 'clsx';

interface ChatAction {
  label: string;
  route: string;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  actions?: ChatAction[];
  timestamp: Date;
}

const QUICK_PILLS = [
  'What should I run against Cover 3?',
  'Build me a gameplan',
  'What is my biggest weakness?',
];

export function ForgeCoreChat() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [unread, setUnread] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const pathname = usePathname();
  const router = useRouter();

  const currentPage = pathname.split('/').filter(Boolean).pop() || 'dashboard';

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (isOpen) {
      setUnread(0);
      inputRef.current?.focus();
    }
  }, [isOpen]);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text.trim(), context: currentPage }),
      });

      if (!res.ok) throw new Error('Chat request failed');

      const data = await res.json();

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.response,
        actions: data.actions || [],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      if (!isOpen) {
        setUnread((prev) => prev + 1);
      }
    } catch {
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Sorry, I couldn\'t process that request. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, currentPage, isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleActionClick = (route: string) => {
    router.push(route);
    setIsOpen(false);
  };

  return (
    <>
      {/* Floating Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          'fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center',
          'rounded-full bg-forge-500 shadow-lg shadow-forge-500/25',
          'transition-all hover:bg-forge-400 hover:scale-105 active:scale-95',
          'group lg:bottom-8 lg:right-8',
          isOpen && 'bg-dark-700 hover:bg-dark-600'
        )}
        title="Ask ForgeCore"
      >
        {isOpen ? (
          <X className="h-6 w-6 text-white" />
        ) : (
          <MessageCircle className="h-6 w-6 text-white" />
        )}

        {/* Tooltip */}
        <span className="absolute bottom-full right-0 mb-2 hidden whitespace-nowrap rounded-md bg-dark-800 px-3 py-1.5 text-xs text-dark-200 shadow-lg group-hover:block">
          Ask ForgeCore
        </span>

        {/* Unread Badge */}
        {unread > 0 && !isOpen && (
          <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
            {unread}
          </span>
        )}
      </button>

      {/* Chat Panel */}
      <div
        className={clsx(
          'fixed bottom-24 right-6 z-50 flex w-[380px] flex-col overflow-hidden',
          'rounded-2xl border border-dark-700/50 bg-dark-900 shadow-2xl',
          'transition-all duration-300 ease-out lg:right-8',
          isOpen
            ? 'h-[500px] translate-y-0 opacity-100'
            : 'pointer-events-none h-0 translate-y-4 opacity-0'
        )}
      >
        {/* Panel Header */}
        <div className="flex items-center gap-3 border-b border-dark-700/50 px-4 py-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-forge-500/10">
            <Sparkles className="h-4 w-4 text-forge-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-dark-100">ForgeCore</h3>
            <p className="text-[10px] text-dark-500">AI Assistant</p>
          </div>
          {/* Context Badge */}
          <span className="rounded-full bg-dark-800 px-2.5 py-0.5 text-[10px] font-medium text-dark-400">
            {currentPage}
          </span>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
              <Sparkles className="h-8 w-8 text-forge-400/50" />
              <div>
                <p className="text-sm font-medium text-dark-300">
                  How can I help you today?
                </p>
                <p className="mt-1 text-xs text-dark-500">
                  Ask about strategies, gameplans, or analysis.
                </p>
              </div>

              {/* Quick Pills */}
              <div className="flex flex-col gap-2 w-full mt-2">
                {QUICK_PILLS.map((pill) => (
                  <button
                    key={pill}
                    onClick={() => sendMessage(pill)}
                    className="w-full rounded-lg border border-dark-700 bg-dark-800/50 px-3 py-2 text-left text-xs text-dark-300 transition-colors hover:border-forge-500/50 hover:text-dark-200"
                  >
                    {pill}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={clsx(
                'flex',
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={clsx(
                  'max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed',
                  msg.role === 'user'
                    ? 'bg-dark-700 text-dark-100'
                    : 'border border-forge-400/20 bg-dark-800 text-dark-200'
                )}
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>

                {/* Action Buttons */}
                {msg.actions && msg.actions.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {msg.actions.map((action) => (
                      <button
                        key={action.route}
                        onClick={() => handleActionClick(action.route)}
                        className="rounded-md bg-forge-500/10 px-2 py-1 text-[10px] font-medium text-forge-400 transition-colors hover:bg-forge-500/20"
                      >
                        {action.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="rounded-xl border border-forge-400/20 bg-dark-800 px-3 py-2">
                <div className="flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-forge-400/60" style={{ animationDelay: '0ms' }} />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-forge-400/60" style={{ animationDelay: '150ms' }} />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-forge-400/60" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <form
          onSubmit={handleSubmit}
          className="flex items-center gap-2 border-t border-dark-700/50 px-4 py-3"
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask ForgeCore anything..."
            disabled={isLoading}
            className="flex-1 rounded-lg bg-dark-800 px-3 py-2 text-xs text-dark-100 placeholder-dark-500 outline-none ring-1 ring-dark-700 transition-all focus:ring-forge-500/50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-forge-500 text-white transition-all hover:bg-forge-400 disabled:opacity-40 disabled:hover:bg-forge-500"
          >
            <Send className="h-3.5 w-3.5" />
          </button>
        </form>
      </div>
    </>
  );
}
