import { useEffect, useMemo, useState } from 'react';
import { ArrowRight, CheckCircle2, Database, ExternalLink, Loader2, Mail, Radar, ShieldAlert } from 'lucide-react';
import { createWaitlistSignup, getOpportunityId, listOpportunities, queryFromSlug, runScan } from '../api';
import type { Opportunity } from '../api';
import './PublicOpportunityPage.css';

interface PublicOpportunityPageProps {
  slug: string;
  onStartValidation: (query: string) => void;
}

const fallbackOpportunity: Opportunity = {
  title: 'Shopify returns automation',
  rating: 'PIVOT',
  total_score: 6.4,
  evidence_count: 18,
  source_count: 4,
  source: 'Reddit RSS, Hacker News, Product Hunt',
  content_summary:
    'Repeated complaints around manual refunds, return labels, and customer status updates. The opportunity is strongest for DTC stores with enough return volume to feel support pain.',
  key_insight:
    'A narrow returns automation product may work if positioned around support time saved rather than generic ecommerce automation.',
  action_items:
    'Interview 5 Shopify operators, test a fake-door landing page, and validate whether the first workflow is return status automation or label generation.',
  cluster_keywords: ['shopify', 'returns', 'refund', 'automation', 'support'],
  scores: {
    Pain: 7.2,
    'Build Fit': 6.8,
    Stability: 5.9,
    Distribution: 6.5,
    Monetization: 7.1,
  },
};

const formatScore = (value?: number) => (typeof value === 'number' ? value.toFixed(1) : '0.0');

export default function PublicOpportunityPage({ slug, onStartValidation }: PublicOpportunityPageProps) {
  const query = useMemo(() => queryFromSlug(slug) || 'SaaS opportunity', [slug]);
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [email, setEmail] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    listOpportunities(query)
      .then((result) => {
        if (cancelled) return;
        setOpportunity(result.opportunities?.[0] || null);
      })
      .catch(() => {
        if (!cancelled) setOpportunity(null);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [query]);

  const display = opportunity || fallbackOpportunity;
  const scores = Object.entries(display.scores || {});

  const handleMiniScan = async () => {
    setIsScanning(true);
    try {
      const result = await runScan({
        query,
        opportunity_type: 'micro_saas',
        limit: 10,
        quick: true,
        ai_depth: 'none',
      });
      setOpportunity(result.opportunities?.[0] || display);
      setStatus('Mini validation refreshed from live sources.');
    } catch {
      setStatus('Live scan needs the Python backend running. Showing the public sample report for now.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleEmailSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!email) {
      setStatus('Enter an email first.');
      return;
    }
    if (companyName.trim()) {
      setStatus(`Saved interest for ${email}.`);
      return;
    }
    try {
      await createWaitlistSignup({
        email,
        company_name: companyName,
        public_slug: slug,
        query,
        opportunity_id: getOpportunityId(display),
        source: 'public_opportunity_page',
        utm: Object.fromEntries(new URLSearchParams(window.location.search).entries()),
      });
      setStatus(`Saved interest for ${email}.`);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : 'Unable to save interest right now.');
    }
  };

  return (
    <main className="public-page" data-testid="public-opportunity-page">
      <header className="public-nav">
        <a className="public-brand" href="/">
          <span className="brand-mark" aria-hidden="true" />
          GoldIdeas
        </a>
        <button className="public-nav-cta" onClick={() => onStartValidation(query)} data-testid="open-workspace">
          Open workspace
          <ArrowRight size={15} />
        </button>
      </header>

      <article className="public-hero">
        <div className="public-kicker">
          <Radar size={15} />
          Source-backed opportunity report
        </div>
        <h1>{display.title}</h1>
        <p>{display.content_summary}</p>
        <div className="public-actions">
          <button className="public-primary" onClick={handleMiniScan} disabled={isScanning} data-testid="refresh-public-report">
            {isScanning ? <Loader2 size={16} className="spin" /> : <Database size={16} />}
            {isScanning ? 'Scanning...' : 'Refresh live evidence'}
          </button>
          <button className="public-secondary" onClick={() => onStartValidation(query)}>
            Validate a related idea
            <ArrowRight size={16} />
          </button>
        </div>
        {isLoading && <p className="public-status" role="status">Looking for a stored report for this topic...</p>}
        {status && <p className="public-status" role="status">{status}</p>}
      </article>

      <section className="public-metrics" aria-label="Opportunity metrics">
        <div>
          <span>Verdict</span>
          <strong>{display.rating?.includes('GREEN') ? 'GO' : display.rating?.includes('RED') ? 'KILL' : 'PIVOT'}</strong>
        </div>
        <div>
          <span>Score</span>
          <strong>{formatScore(display.total_score)}/10</strong>
        </div>
        <div>
          <span>Evidence</span>
          <strong>{display.evidence_count || 1} signals</strong>
        </div>
        <div>
          <span>Sources</span>
          <strong>{display.source_count || 1}</strong>
        </div>
      </section>

      <section className="public-content-grid">
        <article className="public-panel">
          <h2>Why this may be worth validating</h2>
          <p>{display.key_insight}</p>
          <ul>
            <li><CheckCircle2 size={15} /> Repeated pain language is stronger than a generic idea prompt.</li>
            <li><CheckCircle2 size={15} /> The first product should stay narrow enough for a solo builder.</li>
            <li><CheckCircle2 size={15} /> Pricing should be tested before engineering-heavy automation.</li>
          </ul>
        </article>

        <article className="public-panel">
          <h2>Validation action</h2>
          <p>{display.action_items}</p>
          <div className="keyword-cloud">
            {(display.cluster_keywords || [query]).slice(0, 8).map((keyword) => (
              <span key={keyword}>{keyword}</span>
            ))}
          </div>
        </article>

        <article className="public-panel">
          <h2>Score breakdown</h2>
          <div className="public-score-list">
            {scores.map(([label, score]) => (
              <div key={label}>
                <span>{label}</span>
                <meter min={0} max={10} value={score} />
                <strong>{formatScore(score)}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="public-panel warning">
          <h2><ShieldAlert size={18} /> Open risks</h2>
          <p>
            Treat this as a validation lead, not a build order. Confirm willingness to pay, existing alternatives,
            platform risk, and whether the first workflow can be solved without heavy services work.
          </p>
        </article>
      </section>

      <section className="public-lead-capture">
        <div>
          <h2>Want the full private report?</h2>
          <p>Get notified when the full source-backed report and monitor are ready.</p>
        </div>
        <form onSubmit={handleEmailSubmit} data-testid="public-email-form">
          <Mail size={16} />
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            aria-label="Email address"
          />
          <label className="public-honeypot" aria-hidden="true">
            Company name
            <input
              tabIndex={-1}
              autoComplete="off"
              value={companyName}
              onChange={(event) => setCompanyName(event.target.value)}
            />
          </label>
          <button type="submit">Notify me</button>
        </form>
      </section>

      <footer className="public-footer">
        <a href="/" aria-label="Return to GoldIdeas home">GoldIdeas</a>
        <a href={display.url || '#'} target="_blank" rel="noreferrer">
          Source example
          <ExternalLink size={13} />
        </a>
      </footer>
    </main>
  );
}
