/**
 * Layout for auth pages (login, register) — no session provider needed,
 * these are public pages.
 */

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
