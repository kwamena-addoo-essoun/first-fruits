import React from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingPage.css';

const FEATURES = [
  {
    icon: '⏱',
    title: 'Time Tracking',
    desc: 'Log billable hours with one click. Start, stop, and review sessions — all in one place.',
  },
  {
    icon: '📄',
    title: 'Auto-Generated Invoices',
    desc: 'Turn tracked hours into professional PDF invoices in seconds. No spreadsheets needed.',
  },
  {
    icon: '📧',
    title: 'Email Invoices to Clients',
    desc: 'Send polished invoices directly from HourStack. PDF attached, no extra tools required.',
  },
  {
    icon: '📊',
    title: 'Earnings Dashboard',
    desc: 'See total invoiced, paid, and pending amounts at a glance. Know exactly where you stand.',
  },
  {
    icon: '👥',
    title: 'Client Management',
    desc: 'Organize projects by client. Track rates, hours earned, and invoice history per client.',
  },
  {
    icon: '🔒',
    title: 'Secure & Private',
    desc: 'JWT-authenticated. Your data belongs to you — nothing shared, nothing sold.',
  },
];

const TESTIMONIALS = [
  {
    quote: 'I stopped losing track of billable hours the day I switched to HourStack. My invoices now go out the same day.',
    name: 'Sarah K.',
    role: 'Freelance Designer',
  },
  {
    quote: 'From logging time to emailing an invoice takes me under 2 minutes. This is exactly what solo devs need.',
    name: 'Marcus T.',
    role: 'Independent Developer',
  },
  {
    quote: 'Clean, fast, and no bloat. I manage three ongoing clients and HourStack keeps everything organised.',
    name: 'Priya M.',
    role: 'Freelance Copywriter',
  },
];

function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="landing">
      {/* ── NAV ── */}
      <header className="landing-nav">
        <div className="landing-nav-inner">
          <div className="landing-logo">
            <span className="landing-logo-icon">⏱</span>
            <span className="landing-logo-text">HourStack</span>
          </div>
          <div className="landing-nav-actions">
            <button className="landing-btn-ghost" onClick={() => navigate('/login')}>
              Log in
            </button>
            <button className="landing-btn-primary" onClick={() => navigate('/register')}>
              Start for free
            </button>
          </div>
        </div>
      </header>

      {/* ── HERO ── */}
      <section className="landing-hero">
        <div className="landing-hero-inner">
          <span className="landing-hero-badge">Built for freelancers</span>
          <h1 className="landing-hero-title">
            Track hours.<br />Get paid faster.
          </h1>
          <p className="landing-hero-sub">
            HourStack is the all-in-one time tracker and invoice generator for freelancers who
            want to spend less time on admin and more time doing great work.
          </p>
          <div className="landing-hero-ctas">
            <button className="landing-btn-primary landing-btn-primary--lg" onClick={() => navigate('/register')}>
              Get started — it's free
            </button>
            <button className="landing-btn-ghost landing-btn-ghost--lg" onClick={() => navigate('/login')}>
              I already have an account →
            </button>
          </div>
          <p className="landing-hero-note">No credit card required · Free plan available forever</p>
        </div>

        {/* Decorative gradient blobs */}
        <div className="landing-hero-blob landing-hero-blob--1" aria-hidden="true" />
        <div className="landing-hero-blob landing-hero-blob--2" aria-hidden="true" />
      </section>

      {/* ── FEATURES ── */}
      <section className="landing-features">
        <div className="landing-section-inner">
          <h2 className="landing-section-title">Everything you need to run your freelance business</h2>
          <p className="landing-section-sub">
            No complexity. No bloat. Just the tools that actually move money into your account.
          </p>
          <div className="landing-features-grid">
            {FEATURES.map((f) => (
              <div className="landing-feature-card" key={f.title}>
                <div className="landing-feature-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="landing-how">
        <div className="landing-section-inner">
          <h2 className="landing-section-title">From first hour to paid invoice in 3 steps</h2>
          <div className="landing-steps">
            <div className="landing-step">
              <div className="landing-step-num">1</div>
              <h3>Create a project</h3>
              <p>Add a project and set your hourly rate. Link it to a client if you have one.</p>
            </div>
            <div className="landing-step-connector" aria-hidden="true">→</div>
            <div className="landing-step">
              <div className="landing-step-num">2</div>
              <h3>Log your time</h3>
              <p>Track sessions as you work. HourStack calculates hours and earnings automatically.</p>
            </div>
            <div className="landing-step-connector" aria-hidden="true">→</div>
            <div className="landing-step">
              <div className="landing-step-num">3</div>
              <h3>Send the invoice</h3>
              <p>Generate a PDF invoice from your logged hours and email it straight to your client.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ── */}
      <section className="landing-testimonials">
        <div className="landing-section-inner">
          <h2 className="landing-section-title">Loved by freelancers</h2>
          <div className="landing-testimonials-grid">
            {TESTIMONIALS.map((t) => (
              <div className="landing-testimonial-card" key={t.name}>
                <p className="landing-testimonial-quote">"{t.quote}"</p>
                <div className="landing-testimonial-author">
                  <strong>{t.name}</strong>
                  <span>{t.role}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── PRICING ── */}
      <section className="landing-pricing">
        <div className="landing-section-inner">
          <h2 className="landing-section-title">Simple, honest pricing</h2>
          <div className="landing-pricing-grid">
            {/* Free */}
            <div className="landing-pricing-card">
              <h3>Free</h3>
              <div className="landing-pricing-price">$0 <span>/ month</span></div>
              <p className="landing-pricing-desc">Perfect for getting started.</p>
              <ul className="landing-pricing-features">
                <li>✓ 3 active projects</li>
                <li>✓ 10 invoices / month</li>
                <li>✓ PDF invoice download</li>
                <li>✓ Time tracking</li>
                <li>✓ Client management</li>
              </ul>
              <button className="landing-btn-outline" onClick={() => navigate('/register')}>
                Get started free
              </button>
            </div>

            {/* Pro */}
            <div className="landing-pricing-card landing-pricing-card--pro">
              <div className="landing-pricing-popular">Most popular</div>
              <h3>⭐ Pro</h3>
              <div className="landing-pricing-price">$12 <span>/ month</span></div>
              <p className="landing-pricing-desc">Everything you need to grow.</p>
              <ul className="landing-pricing-features">
                <li>✓ Unlimited projects</li>
                <li>✓ Unlimited invoices</li>
                <li>✓ PDF invoice download</li>
                <li>✓ Email invoices to clients</li>
                <li>✓ Time tracking</li>
                <li>✓ Priority support</li>
                <li>✓ Early feature access</li>
              </ul>
              <button className="landing-btn-primary" onClick={() => navigate('/register')}>
                Start free, upgrade anytime
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="landing-cta">
        <div className="landing-section-inner landing-cta-inner">
          <h2>Ready to get paid on time?</h2>
          <p>Join freelancers who use HourStack to track, invoice, and grow.</p>
          <button className="landing-btn-primary landing-btn-primary--lg" onClick={() => navigate('/register')}>
            Create your free account →
          </button>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <span className="landing-logo">
            <span className="landing-logo-icon">⏱</span>
            <span className="landing-logo-text">HourStack</span>
          </span>
          <span className="landing-footer-copy">© {new Date().getFullYear()} HourStack. All rights reserved.</span>
        </div>
      </footer>
    </div>
  );
}

export default LandingPage;
