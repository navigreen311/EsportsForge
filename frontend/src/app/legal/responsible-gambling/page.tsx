export const metadata = {
  title: 'Responsible Gaming | EsportsForge',
};

export default function ResponsibleGamblingPage() {
  return (
    <article className="space-y-8 text-dark-300">
      <header>
        <h1 className="text-3xl font-bold text-dark-50 mb-2">Responsible Gaming</h1>
        <p className="text-sm text-dark-500">Last updated: April 11, 2026</p>
      </header>

      <p>
        EsportsForge includes a Video Poker training module designed to help users understand
        poker strategy through simulated, no-stakes gameplay. While no real money is wagered
        within our platform, we recognize the importance of responsible gaming practices and are
        committed to providing tools and resources to keep your experience healthy.
      </p>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">1. Session Limits</h2>
        <p>
          Our Video Poker module includes built-in session management tools to help you maintain
          healthy play habits:
        </p>
        <ul className="list-disc pl-6 space-y-1 text-dark-400">
          <li>
            <strong className="text-dark-200">Time Limits</strong> — Set a maximum session duration
            (e.g., 30 minutes, 1 hour, 2 hours). You will receive a notification when your time
            limit is approaching and the session will pause when reached.
          </li>
          <li>
            <strong className="text-dark-200">Hand Limits</strong> — Set a maximum number of hands
            per session. The module will pause and prompt you to take a break once the limit is hit.
          </li>
          <li>
            <strong className="text-dark-200">Cool-down Periods</strong> — After extended sessions,
            a mandatory 15-minute cool-down period is enforced before you can start a new session.
          </li>
          <li>
            <strong className="text-dark-200">Daily Reminders</strong> — Receive daily summaries of
            your play time to maintain awareness of your habits.
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">2. Self-Exclusion</h2>
        <p>
          If you feel that your gaming habits are becoming unhealthy, you can activate self-exclusion
          at any time through Settings &gt; Responsible Gaming &gt; Self-Exclusion. Options include:
        </p>
        <ul className="list-disc pl-6 space-y-1 text-dark-400">
          <li>
            <strong className="text-dark-200">Temporary Exclusion</strong> — Block access to the
            Video Poker module for 24 hours, 7 days, 30 days, or 90 days.
          </li>
          <li>
            <strong className="text-dark-200">Permanent Exclusion</strong> — Permanently disable
            your access to the Video Poker module. This action requires a 7-day cooling-off period
            to reverse.
          </li>
        </ul>
        <p>
          During a self-exclusion period, you will not be able to access the Video Poker module,
          but all other EsportsForge features remain available.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">3. Recognizing Problem Gambling</h2>
        <p>Warning signs that gaming habits may be becoming problematic:</p>
        <ul className="list-disc pl-6 space-y-1 text-dark-400">
          <li>Spending more time playing than intended on a regular basis</li>
          <li>Neglecting responsibilities, relationships, or self-care due to play</li>
          <li>Feeling irritable or anxious when unable to play</li>
          <li>Chasing losses or feeling compelled to continue playing after setbacks</li>
          <li>Lying about the amount of time spent playing</li>
          <li>Using gaming as a primary coping mechanism for stress or emotional difficulties</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">4. Resources & Support</h2>
        <p>
          If you or someone you know is struggling with problem gambling, the following resources
          are available 24/7:
        </p>
        <div className="rounded-lg border border-dark-700 bg-dark-800 p-4 space-y-3">
          <div>
            <p className="font-medium text-dark-100">National Council on Problem Gambling (NCPG)</p>
            <p className="text-dark-400">
              Helpline:{' '}
              <a href="tel:1-800-522-4700" className="text-forge-400 hover:text-forge-300 font-medium">
                1-800-522-4700
              </a>
            </p>
            <p className="text-dark-400">
              Text: <span className="text-forge-400 font-medium">741741</span>
            </p>
            <p className="text-dark-400">
              Chat:{' '}
              <a href="https://www.ncpgambling.org/help-treatment/chat/" className="text-forge-400 hover:text-forge-300" target="_blank" rel="noopener noreferrer">
                ncpgambling.org/chat
              </a>
            </p>
          </div>
          <div>
            <p className="font-medium text-dark-100">Gamblers Anonymous</p>
            <p className="text-dark-400">
              <a href="https://www.gamblersanonymous.org" className="text-forge-400 hover:text-forge-300" target="_blank" rel="noopener noreferrer">
                gamblersanonymous.org
              </a>
            </p>
          </div>
          <div>
            <p className="font-medium text-dark-100">SAMHSA National Helpline</p>
            <p className="text-dark-400">
              <a href="tel:1-800-662-4357" className="text-forge-400 hover:text-forge-300 font-medium">
                1-800-662-4357
              </a>{' '}
              (free, confidential, 24/7)
            </p>
          </div>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold text-dark-100">5. Our Commitment</h2>
        <p>
          EsportsForge is committed to maintaining a safe and healthy gaming environment. Our
          Video Poker module is designed as a skill-training tool with no real-money wagering.
          We actively monitor for signs of unhealthy patterns and will proactively suggest breaks
          and resources when our systems detect extended play sessions.
        </p>
        <p>
          For questions or concerns about our responsible gaming practices, contact us at:{' '}
          <a href="mailto:support@esportsforge.com" className="text-forge-400 hover:text-forge-300">
            support@esportsforge.com
          </a>
        </p>
      </section>
    </article>
  );
}
