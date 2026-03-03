import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { billingAPI } from '../utils/api';
import { useToastStore } from '../store/toastStore';
import './BillingPage.css';

const FREE_FEATURES = [
  '3 active projects',
  '10 invoices / month',
  'Time tracking',
  'PDF invoice download',
  'Client management',
];

const PRO_FEATURES = [
  'Unlimited projects',
  'Unlimited invoices',
  'Time tracking',
  'PDF invoice download',
  'Email invoices to clients',
  'Priority support',
  'Early access to new features',
];

function PlanBadge({ plan }) {
  return (
    <span className={`plan-badge plan-badge--${plan}`}>
      {plan === 'pro' ? '⭐ Pro' : 'Free'}
    </span>
  );
}

function BillingPage() {
  const push = useToastStore((s) => s.push);
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (searchParams.get('success') === '1') {
      push('success', '🎉 Welcome to Pro! Your plan has been activated.');
    } else if (searchParams.get('canceled') === '1') {
      push('info', 'Checkout canceled — no charge was made.');
    }
  }, [searchParams, push]);

  useEffect(() => {
    billingAPI.getStatus()
      .then((res) => setStatus(res.data))
      .catch(() => push('error', 'Failed to load billing status.'))
      .finally(() => setLoading(false));
  }, [push]);

  const handleUpgrade = async () => {
    setActionLoading(true);
    try {
      const res = await billingAPI.createCheckout();
      window.location.href = res.data.url;
    } catch (err) {
      push('error', err?.response?.data?.detail || 'Failed to start checkout.');
      setActionLoading(false);
    }
  };

  const handleManage = async () => {
    setActionLoading(true);
    try {
      const res = await billingAPI.createPortal();
      window.location.href = res.data.url;
    } catch (err) {
      push('error', err?.response?.data?.detail || 'Failed to open billing portal.');
      setActionLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  const isPro = status?.plan === 'pro';
  const billingEnabled = status?.billing_enabled;

  return (
    <div className="billing-page">
      <div className="billing-header">
        <h1>Billing &amp; Plan</h1>
        <p className="billing-sub">Manage your subscription and unlock the full power of HourStack.</p>
      </div>

      {/* Current Plan */}
      <div className="billing-current-plan card">
        <div className="billing-plan-row">
          <div>
            <h2>Current Plan</h2>
            <p className="billing-plan-desc">
              {isPro
                ? 'You are on the Pro plan. Enjoy unlimited everything!'
                : 'You are on the Free plan. Upgrade to unlock all features.'}
            </p>
          </div>
          <PlanBadge plan={status?.plan || 'free'} />
        </div>

        {billingEnabled ? (
          isPro ? (
            <button
              className="btn-secondary"
              onClick={handleManage}
              disabled={actionLoading}
            >
              {actionLoading ? 'Loading…' : 'Manage Subscription'}
            </button>
          ) : (
            <button
              className="btn-upgrade"
              onClick={handleUpgrade}
              disabled={actionLoading}
            >
              {actionLoading ? 'Redirecting…' : '⭐ Upgrade to Pro — $12 / mo'}
            </button>
          )
        ) : (
          <p className="billing-notice">
            💡 <strong>Billing not configured yet.</strong> Set{' '}
            <code>STRIPE_SECRET_KEY</code>, <code>STRIPE_PRO_PRICE_ID</code>, and{' '}
            <code>STRIPE_WEBHOOK_SECRET</code> in your <code>.env</code> to enable payments.
          </p>
        )}
      </div>

      {/* Plan comparison */}
      <div className="billing-plans-grid">
        {/* Free */}
        <div className={`billing-plan-card ${!isPro ? 'billing-plan-card--current' : ''}`}>
          <div className="billing-plan-card-header">
            <h3>Free</h3>
            <div className="billing-price">$0 <span>/ mo</span></div>
            {!isPro && <span className="billing-current-label">Current plan</span>}
          </div>
          <ul className="billing-features">
            {FREE_FEATURES.map((f) => (
              <li key={f}><span className="feature-check">✓</span> {f}</li>
            ))}
          </ul>
        </div>

        {/* Pro */}
        <div className={`billing-plan-card billing-plan-card--pro ${isPro ? 'billing-plan-card--current' : ''}`}>
          <div className="billing-plan-card-header">
            <h3>⭐ Pro</h3>
            <div className="billing-price">$12 <span>/ mo</span></div>
            {isPro
              ? <span className="billing-current-label">Current plan</span>
              : billingEnabled && (
                  <button
                    className="btn-upgrade btn-upgrade--sm"
                    onClick={handleUpgrade}
                    disabled={actionLoading}
                  >
                    Upgrade
                  </button>
                )
            }
          </div>
          <ul className="billing-features">
            {PRO_FEATURES.map((f) => (
              <li key={f}><span className="feature-check feature-check--pro">✓</span> {f}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default BillingPage;
