'use client';

import React, { Component, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center rounded-xl border border-dark-700 bg-dark-900 p-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-500/10 mb-4">
            <AlertTriangle className="h-6 w-6 text-amber-400" />
          </div>
          <h3 className="text-lg font-semibold text-dark-100 mb-2">
            Something went wrong
          </h3>
          <p className="text-sm text-dark-400 mb-4 max-w-sm">
            An unexpected error occurred. Please try again or contact support if the problem persists.
          </p>
          <button
            onClick={this.handleRetry}
            className="rounded-lg bg-forge-500 px-4 py-2 text-sm font-semibold text-dark-950 transition-colors hover:bg-forge-400"
          >
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
