/**
 * Client-side NextAuth SessionProvider wrapper for the App Router.
 */

"use client";

import { useState } from "react";
import { SessionProvider as NextAuthSessionProvider } from "next-auth/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );
  return (
    <NextAuthSessionProvider>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </NextAuthSessionProvider>
  );
}
