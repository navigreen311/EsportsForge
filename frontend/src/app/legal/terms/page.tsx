export const metadata = {
  title: 'Terms of Service | EsportsForge',
};

export default function TermsOfServicePage() {
  return (
    <article className="space-y-8 text-dark-300">
      <header>
        <h1 className="text-3xl font-bold text-dark-50 mb-2">Terms of Service</h1>
        <p className="text-sm text-dark-500">Last updated: April 11, 2026</p>
      </header>

      <p className="text-dark-300">
        These Terms of Service (&quot;Terms&quot;) govern your access to and use of the EsportsForge platform
        (&quot;Service&quot;), operated by Green Companies LLC (&quot;Company&quot;, &quot;we&quot;, &quot;us&quot;, or &quot;our&quot;). By creating
        an account or using the Service, you agree to be bound by these Terms. If you do not agree,
        do not use the Service.
      </p>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">1. Account Terms</h2>
        <p>
          You must be at least 13 years of age to use EsportsForge. If you are under 18, you must have
          the consent of a parent or legal guardian. You are responsible for maintaining the confidentiality
          of your account credentials and for all activity that occurs under your account. You agree to
          provide accurate, current, and complete information during registration and to update such
          information as necessary.
        </p>
        <p>
          You may not share your account with others or allow multiple individuals to use a single account.
          We reserve the right to suspend or terminate accounts that violate these provisions.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">2. Subscription Terms</h2>
        <p>
          EsportsForge offers tiered subscription plans with varying levels of access to AI coaching
          features, analytics, and tournament tools. Subscriptions are billed on a recurring basis
          (monthly or annually) through our payment processor, Stripe. All fees are stated in U.S.
          dollars and are non-refundable except as required by applicable law.
        </p>
        <p>
          You may cancel your subscription at any time through your account settings. Cancellation
          takes effect at the end of the current billing period. We reserve the right to modify
          pricing with 30 days&apos; advance notice.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">3. Acceptable Use</h2>
        <p>You agree not to:</p>
        <ul className="list-disc pl-6 space-y-1 text-dark-400">
          <li>Use the Service to cheat, exploit, or gain unfair advantages in competitive games in violation of their terms of service</li>
          <li>Reverse-engineer, decompile, or attempt to extract the source code of the Service or its AI models</li>
          <li>Harass, abuse, or threaten other users</li>
          <li>Upload malicious code or interfere with the Service&apos;s infrastructure</li>
          <li>Use automated tools (bots, scrapers) to access the Service without prior written permission</li>
          <li>Resell, sublicense, or redistribute access to the Service</li>
          <li>Use the AI coaching outputs to train competing machine learning models</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">4. Intellectual Property</h2>
        <p>
          The Service, including its AI models (ForgeCore, LoopAI, PlayerTwin, ImpactRank, TruthEngine),
          algorithms, user interface, graphics, and documentation, is the exclusive property of Green
          Companies LLC and is protected by copyright, trade secret, and other intellectual property laws.
        </p>
        <p>
          You retain ownership of your gameplay data and user-generated content. By using the Service,
          you grant us a limited license to process your data solely for the purpose of providing and
          improving the Service. AI-generated insights, recommendations, and coaching outputs are
          licensed to you for personal, non-commercial use during your active subscription.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">5. Disclaimers</h2>
        <p>
          THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES OF ANY KIND, EITHER
          EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO IMPLIED WARRANTIES OF MERCHANTABILITY,
          FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT.
        </p>
        <p>
          AI-generated coaching recommendations are for informational and entertainment purposes only.
          We do not guarantee specific competitive outcomes, rank improvements, or win rates. The
          accuracy of AI predictions depends on the quality and completeness of input data.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">6. Limitation of Liability</h2>
        <p>
          TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, GREEN COMPANIES LLC SHALL NOT BE LIABLE
          FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, OR ANY LOSS OF
          PROFITS OR REVENUES, WHETHER INCURRED DIRECTLY OR INDIRECTLY, OR ANY LOSS OF DATA, USE,
          GOODWILL, OR OTHER INTANGIBLE LOSSES RESULTING FROM YOUR USE OF THE SERVICE.
        </p>
        <p>
          IN NO EVENT SHALL OUR AGGREGATE LIABILITY EXCEED THE GREATER OF ONE HUNDRED DOLLARS ($100)
          OR THE AMOUNT YOU PAID US IN THE TWELVE (12) MONTHS PRECEDING THE CLAIM.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">7. Termination</h2>
        <p>
          We may suspend or terminate your access to the Service at any time, with or without cause,
          and with or without notice. Upon termination, your right to use the Service ceases immediately.
          You may request export of your personal data within 30 days of termination.
        </p>
        <p>
          Sections regarding Intellectual Property, Disclaimers, Limitation of Liability, and
          Governing Law survive termination.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">8. Governing Law</h2>
        <p>
          These Terms shall be governed by and construed in accordance with the laws of the State of
          Delaware, United States, without regard to its conflict of law provisions. Any disputes
          arising under these Terms shall be resolved exclusively in the state or federal courts
          located in Delaware. You waive any objections to the exercise of jurisdiction by such
          courts and to venue in such courts.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">9. Changes to Terms</h2>
        <p>
          We reserve the right to modify these Terms at any time. We will notify you of material
          changes by posting the updated Terms on the Service and updating the &quot;Last updated&quot; date.
          Continued use of the Service after changes constitutes acceptance of the revised Terms.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">10. Contact</h2>
        <p>
          For questions about these Terms, contact us at:{' '}
          <a href="mailto:legal@esportsforge.com" className="text-forge-400 hover:text-forge-300">
            legal@esportsforge.com
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
