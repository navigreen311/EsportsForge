/**
 * Onboarding layout — minimal, no sidebar, dark background only.
 */

export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-dark-950">
      {children}
    </div>
  );
}
