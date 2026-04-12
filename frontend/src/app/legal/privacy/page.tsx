export const metadata = {
  title: 'Privacy Policy | EsportsForge',
};

export default function PrivacyPolicyPage() {
  return (
    <article className="space-y-8 text-dark-300">
      <header>
        <h1 className="text-3xl font-bold text-dark-50 mb-2">Privacy Policy</h1>
        <p className="text-sm text-dark-500">Last updated: April 11, 2026</p>
      </header>

      <p>
        Green Companies LLC (&quot;Company&quot;, &quot;we&quot;, &quot;us&quot;) operates the EsportsForge platform. This
        Privacy Policy explains how we collect, use, disclose, and safeguard your information
        when you use our Service.
      </p>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">1. Data We Collect</h2>
        <h3 className="text-base font-medium text-dark-200">Account Information</h3>
        <p>
          Email address, username, display name, hashed password, and profile preferences provided
          during registration.
        </p>
        <h3 className="text-base font-medium text-dark-200">Gameplay Data</h3>
        <p>
          Match results, performance statistics, replay data, and game-specific metrics that you
          connect or upload to the platform. This may include data retrieved from game APIs on
          your behalf.
        </p>
        <h3 className="text-base font-medium text-dark-200">Usage Data</h3>
        <p>
          Device information, browser type, IP address, pages visited, feature usage patterns,
          session duration, and interaction logs collected automatically through cookies and
          similar technologies.
        </p>
        <h3 className="text-base font-medium text-dark-200">Payment Information</h3>
        <p>
          Billing details are processed and stored by Stripe. We do not store full credit card
          numbers on our servers. We retain only a tokenized reference and the last four digits
          for display purposes.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">2. How We Use Your Data</h2>
        <ul className="list-disc pl-6 space-y-1 text-dark-400">
          <li>Provide, maintain, and improve the EsportsForge platform and AI coaching features</li>
          <li>Generate personalized coaching insights, recommendations, and analytics through our AI models</li>
          <li>Process subscription payments and manage your account</li>
          <li>Communicate service updates, security alerts, and support messages</li>
          <li>Detect and prevent fraud, abuse, and security incidents</li>
          <li>Conduct anonymized research to improve AI model accuracy and platform quality</li>
          <li>Comply with legal obligations</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">3. Third-Party Services</h2>
        <p>We share data with the following third-party providers as necessary to operate the Service:</p>
        <ul className="list-disc pl-6 space-y-2 text-dark-400">
          <li>
            <strong className="text-dark-200">Anthropic</strong> — Our AI coaching engine (ForgeCore) is
            powered by Anthropic&apos;s Claude models. Gameplay data and session context are sent to
            Anthropic&apos;s API for processing. Anthropic does not use your data to train their models
            when accessed via API. See{' '}
            <a href="https://www.anthropic.com/privacy" className="text-forge-400 hover:text-forge-300" target="_blank" rel="noopener noreferrer">
              Anthropic&apos;s Privacy Policy
            </a>.
          </li>
          <li>
            <strong className="text-dark-200">Stripe</strong> — Handles all payment processing. Stripe
            collects and stores payment information under their own privacy policy. See{' '}
            <a href="https://stripe.com/privacy" className="text-forge-400 hover:text-forge-300" target="_blank" rel="noopener noreferrer">
              Stripe&apos;s Privacy Policy
            </a>.
          </li>
          <li>
            <strong className="text-dark-200">Hosting & Infrastructure</strong> — We use cloud service
            providers to host the platform. Data is encrypted in transit (TLS 1.3) and at rest.
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">4. Data Retention</h2>
        <p>
          We retain your account data and gameplay history for as long as your account is active.
          After account deletion, we retain anonymized analytics data for up to 24 months for
          service improvement purposes. Payment records are retained for 7 years as required for
          tax and legal compliance.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">5. Your Rights (GDPR & CCPA)</h2>
        <p>Depending on your jurisdiction, you may have the right to:</p>
        <ul className="list-disc pl-6 space-y-1 text-dark-400">
          <li><strong className="text-dark-200">Access</strong> — Request a copy of all personal data we hold about you</li>
          <li><strong className="text-dark-200">Rectification</strong> — Correct inaccurate personal data</li>
          <li><strong className="text-dark-200">Erasure</strong> — Request deletion of your personal data (&quot;right to be forgotten&quot;)</li>
          <li><strong className="text-dark-200">Portability</strong> — Receive your data in a structured, machine-readable format</li>
          <li><strong className="text-dark-200">Restriction</strong> — Restrict processing of your personal data</li>
          <li><strong className="text-dark-200">Objection</strong> — Object to processing based on legitimate interests</li>
          <li><strong className="text-dark-200">Opt-out of sale</strong> — We do not sell personal data. We do not engage in &quot;sharing&quot; for cross-context behavioral advertising.</li>
        </ul>
        <p>
          To exercise any of these rights, contact us at{' '}
          <a href="mailto:privacy@esportsforge.com" className="text-forge-400 hover:text-forge-300">
            privacy@esportsforge.com
          </a>. We will respond within 30 days.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">6. Account Deletion</h2>
        <p>
          You may delete your account at any time through Settings &gt; Account &gt; Delete Account.
          Upon deletion, we will permanently remove your personal data within 30 days, except where
          retention is required by law. Anonymized, aggregated data may be retained indefinitely.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">7. Security</h2>
        <p>
          We implement industry-standard security measures including encryption at rest and in
          transit, secure authentication (bcrypt password hashing, JWT tokens), rate limiting,
          and regular security audits. However, no method of transmission over the Internet is
          100% secure, and we cannot guarantee absolute security.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">8. Contact</h2>
        <p>
          For privacy-related inquiries, contact our Data Protection team at:{' '}
          <a href="mailto:privacy@esportsforge.com" className="text-forge-400 hover:text-forge-300">
            privacy@esportsforge.com
          </a>
        </p>
        <p className="text-dark-500">
          Green Companies LLC<br />
          Wilmington, Delaware, United States
        </p>
      </section>
    </article>
  );
}
