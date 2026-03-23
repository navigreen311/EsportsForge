import type { Metadata } from 'next';
import '@/styles/globals.css';
import { SessionProvider } from '@/components/shared/SessionProvider';

export const metadata: Metadata = {
  title: 'EsportsForge — Built to Win',
  description: 'AI-powered competitive gaming intelligence platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-dark-950 text-dark-50">
        <SessionProvider>{children}</SessionProvider>
      </body>
    </html>
  );
}
