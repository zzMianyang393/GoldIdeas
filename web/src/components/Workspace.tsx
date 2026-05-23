import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, ArrowUpDown, Check, Copy, Download, ExternalLink, Filter, Globe2, Loader2, Mail, Play, Search, Sparkles } from 'lucide-react';
import { getAppConfig, getOpportunityId, getWaitlistStats, listOpportunities, listPublicOpportunities, listWaitlistSignups, runScan } from '../api';
import type { Opportunity, PublicOpportunity, WaitlistSignup, WaitlistStats } from '../api';
import './Workspace.css';

interface WorkspaceProps {
  activeModule: string;
  selectedItem: Opportunity | null;
  setSelectedItem: (item: Opportunity | null) => void;
  initialQuery: string;
  t: (key: string) => string;
}

const OPPORTUNITY_TYPES = [
  { value: 'micro_saas', label: 'Micro SaaS' },
  { value: 'developer_tools', label: 'Developer Tools' },
  { value: 'ecommerce_tools', label: 'E-commerce Tools' },
];

const ratingClass = (rating = '') => {
  if (rating.includes('GREEN')) return 'green';
  if (rating.includes('YELLOW')) return 'yellow';
  return 'red';
};

const formatDate = (value?: string) => {
  if (!value) return 'New';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'New';
  return date.toLocaleDateString();
};

const Workspace: React.FC<WorkspaceProps> = ({ activeModule, selectedItem, setSelectedItem, initialQuery, t }) => {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [query, setQuery] = useState(initialQuery);
  const [opportunityType, setOpportunityType] = useState('micro_saas');
  const [includeKeywords, setIncludeKeywords] = useState('');
  const [excludeKeywords, setExcludeKeywords] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState('');
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [waitlist, setWaitlist] = useState<WaitlistSignup[]>([]);
  const [waitlistStats, setWaitlistStats] = useState<WaitlistStats | null>(null);
  const [isLoadingWaitlist, setIsLoadingWaitlist] = useState(false);
  const [waitlistError, setWaitlistError] = useState('');
  const [publicPages, setPublicPages] = useState<PublicOpportunity[]>([]);
  const [publicBaseUrl, setPublicBaseUrl] = useState('');
  const [isLoadingPublicPages, setIsLoadingPublicPages] = useState(false);
  const [publicPagesError, setPublicPagesError] = useState('');
  const [copiedSlug, setCopiedSlug] = useState('');

  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  useEffect(() => {
    if (activeModule !== 'opportunities') return;
    let cancelled = false;
    setIsLoading(true);
    setError('');
    listOpportunities()
      .then((result) => {
        if (cancelled) return;
        setOpportunities(result.opportunities || []);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Unable to load opportunities');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeModule]);

  useEffect(() => {
    if (activeModule !== 'leads') return;
    let cancelled = false;
    setIsLoadingWaitlist(true);
    setWaitlistError('');
    Promise.all([listWaitlistSignups(), getWaitlistStats()])
      .then(([listResult, statsResult]) => {
        if (cancelled) return;
        setWaitlist(listResult.waitlist || []);
        setWaitlistStats(statsResult.stats || null);
      })
      .catch((err) => {
        if (!cancelled) setWaitlistError(err instanceof Error ? err.message : 'Unable to load leads');
      })
      .finally(() => {
        if (!cancelled) setIsLoadingWaitlist(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeModule]);

  useEffect(() => {
    if (activeModule !== 'publicPages') return;
    let cancelled = false;
    setIsLoadingPublicPages(true);
    setPublicPagesError('');
    Promise.all([listPublicOpportunities(), getAppConfig()])
      .then(([feed, config]) => {
        if (cancelled) return;
        setPublicPages(feed.opportunities || []);
        setPublicBaseUrl(config.public_base_url || window.location.origin);
      })
      .catch((err) => {
        if (!cancelled) setPublicPagesError(err instanceof Error ? err.message : 'Unable to load public pages');
      })
      .finally(() => {
        if (!cancelled) setIsLoadingPublicPages(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeModule]);

  const visibleOpportunities = useMemo(() => opportunities, [opportunities]);
  const selectedOpportunityId = selectedItem ? getOpportunityId(selectedItem) : '';

  const parseKeywordList = (value: string) =>
    value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

  const downloadWaitlistCsv = () => {
    window.location.href = '/api/waitlist.csv?limit=500';
  };

  const copyPublicUrl = async (page: PublicOpportunity) => {
    const url = page.url || `${publicBaseUrl || window.location.origin}${page.path || `/opportunities/${page.slug}`}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopiedSlug(page.slug);
      window.setTimeout(() => setCopiedSlug(''), 1600);
    } catch {
      window.prompt('Copy public URL', url);
    }
  };

  const handleScan = async (event?: React.FormEvent) => {
    event?.preventDefault();
    setIsScanning(true);
    setError('');
    setSelectedItem(null);
    try {
      const result = await runScan({
        query: query.trim() || undefined,
        opportunity_type: opportunityType,
        limit: 12,
        quick: true,
        include_keywords: parseKeywordList(includeKeywords),
        exclude_keywords: parseKeywordList(excludeKeywords),
        ai_depth: 'none',
      });
      setOpportunities(result.opportunities || []);
      setCounts(result.counts || {});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setIsScanning(false);
    }
  };

  const renderOpportunities = () => {
    return (
      <div className="opportunities-workspace animate-fade-in">
        <form className="scan-panel" onSubmit={handleScan} data-testid="scan-form">
          <div className="scan-copy">
            <span className="eyebrow"><Sparkles size={14} /> Validation search</span>
            <h3 className="scan-title outfit-font">Find source-backed SaaS opportunities</h3>
            <p>Enter a market, workflow, product category, or competitor complaint. GoldIdeas will scan live sources and score the evidence.</p>
          </div>
          <div className="scan-controls">
            <label className="scan-field scan-field-main">
              <span>Idea or market</span>
              <div className="input-with-icon">
                <Search size={15} />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="e.g. Shopify returns automation"
                  data-testid="scan-query"
                />
              </div>
            </label>
            <label className="scan-field">
              <span>Opportunity type</span>
              <select
                value={opportunityType}
                onChange={(event) => setOpportunityType(event.target.value)}
                data-testid="opportunity-type"
              >
                {OPPORTUNITY_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </label>
            <label className="scan-field">
              <span>Include</span>
              <input
                value={includeKeywords}
                onChange={(event) => setIncludeKeywords(event.target.value)}
                placeholder="returns, refund"
              />
            </label>
            <label className="scan-field">
              <span>Exclude</span>
              <input
                value={excludeKeywords}
                onChange={(event) => setExcludeKeywords(event.target.value)}
                placeholder="jobs, hiring"
              />
            </label>
            <button className="btn-scan" type="submit" disabled={isScanning} data-testid="run-scan">
              {isScanning ? <Loader2 size={16} className="spin" /> : <Play size={16} fill="currentColor" />}
              {isScanning ? 'Scanning...' : t('runScan')}
            </button>
          </div>
        </form>

        <div className="workspace-toolbar">
          <div className="toolbar-left">
            <h3 className="view-title outfit-font">{t('allOpportunities')}</h3>
            <span className="badge">{visibleOpportunities.length}</span>
            {Object.keys(counts).length > 0 && (
              <span className="counts-text">
                {counts.green || 0} green / {counts.yellow || 0} yellow / {counts.red || 0} red
              </span>
            )}
          </div>
          <div className="toolbar-right">
            <button className="btn-filter" type="button">
              <Filter size={14} /> {t('filter')}
            </button>
            <button className="btn-filter" type="button">
              <ArrowUpDown size={14} /> {t('sort')}
            </button>
          </div>
        </div>

        <div className="list-container glass-panel">
          <div className="list-header">
            <div className="col-rating">{t('colRating')}</div>
            <div className="col-title">{t('colTitle')}</div>
            <div className="col-score">{t('colScore')}</div>
            <div className="col-source">{t('colSource')}</div>
            <div className="col-date">{t('colDate')}</div>
          </div>
          
          <div className="list-body">
            {error && (
              <div className="state-row error-state">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}
            {(isLoading || isScanning) && !error && (
              <div className="state-row">
                <Loader2 size={18} className="spin" />
                <span>{isScanning ? 'Scanning live sources...' : 'Loading stored opportunities...'}</span>
              </div>
            )}
            {!isLoading && !isScanning && !error && visibleOpportunities.length === 0 && (
              <div className="empty-state">
                <h4>No opportunities yet</h4>
                <p>Run a validation search to create your first source-backed opportunity list.</p>
              </div>
            )}
            {visibleOpportunities.map((opt) => (
              <div 
                key={getOpportunityId(opt) || opt.title}
                className={`list-row ${selectedOpportunityId === getOpportunityId(opt) ? 'selected' : ''}`}
                onClick={() => setSelectedItem(opt)}
                data-testid="opportunity-row"
              >
                <div className="col-rating">
                  <span className={`rating-badge ${ratingClass(opt.rating)}`}>
                    {opt.rating || 'UNRATED'}
                  </span>
                </div>
                <div className="col-title">
                  <span className="truncate">{opt.title}</span>
                  <span className="row-summary">
                    {opt.evidence_count ? `${opt.evidence_count} evidence signals` : 'Single evidence signal'}
                    {opt.source_count ? ` across ${opt.source_count} sources` : ''}
                    {opt.cluster_keywords?.length ? ` - ${opt.cluster_keywords.slice(0, 4).join(', ')}` : ''}
                  </span>
                </div>
                <div className="col-score">
                  <div className="score-pill">
                    {(opt.total_score || 0).toFixed(1)}
                  </div>
                </div>
                <div className="col-source">
                  <span className="source-tag">{opt.source || opt.source_group || 'source'}</span>
                </div>
                <div className="col-date">
                  <span className="date-text">
                    {formatDate(opt.last_seen_at || opt.published)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderPlaceholder = () => (
    <div className="placeholder-workspace animate-fade-in">
      <div className="placeholder-content glass-panel">
        <h2 className="outfit-font">{t(activeModule as any) || activeModule} {t('placeholderTitle')}</h2>
        <p>{t('placeholderDesc')}</p>
      </div>
    </div>
  );

  const renderLeads = () => (
    <div className="leads-workspace animate-fade-in">
      <div className="leads-header">
        <div>
          <span className="eyebrow"><Mail size={14} /> Public page leads</span>
          <h3 className="scan-title outfit-font">Waitlist and report requests</h3>
          <p>Emails captured from public opportunity pages, with the query and slug that produced the lead.</p>
        </div>
        <div className="leads-actions">
          <span className="badge">{waitlist.length}</span>
          <button className="btn-filter" type="button" onClick={downloadWaitlistCsv} disabled={waitlist.length === 0}>
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      <div className="lead-stats">
        <div className="lead-stat glass-panel">
          <span>Total leads</span>
          <strong>{waitlistStats?.total ?? waitlist.length}</strong>
        </div>
        <div className="lead-stat glass-panel">
          <span>Pages with leads</span>
          <strong>{waitlistStats?.public_page_count ?? 0}</strong>
        </div>
        <div className="lead-stat glass-panel">
          <span>Top page</span>
          <strong>{waitlistStats?.by_slug?.[0]?.slug || '-'}</strong>
        </div>
        <div className="lead-stat glass-panel">
          <span>Top source</span>
          <strong>{waitlistStats?.by_source?.[0]?.source || '-'}</strong>
        </div>
      </div>

      <div className="leads-table glass-panel">
        <div className="leads-row leads-row-head">
          <div>Email</div>
          <div>Query</div>
          <div>Public page</div>
          <div>Source</div>
          <div>Created</div>
        </div>
        {isLoadingWaitlist && (
          <div className="state-row">
            <Loader2 size={18} className="spin" />
            <span>Loading leads...</span>
          </div>
        )}
        {waitlistError && (
          <div className="state-row error-state">
            <AlertCircle size={18} />
            <span>{waitlistError}</span>
          </div>
        )}
        {!isLoadingWaitlist && !waitlistError && waitlist.length === 0 && (
          <div className="empty-state">
            <h4>No leads yet</h4>
            <p>Publish or share an opportunity page, then capture email interest from the public report form.</p>
          </div>
        )}
        {waitlist.map((lead) => (
          <div className="leads-row" key={lead.id}>
            <div>
              <strong>{lead.email}</strong>
              {lead.utm && Object.keys(lead.utm).length > 0 && (
                <span className="lead-meta">UTM: {Object.entries(lead.utm).map(([key, value]) => `${key}=${value}`).join(', ')}</span>
              )}
            </div>
            <div>{lead.query || '-'}</div>
            <div>
              {lead.public_slug ? (
                <a href={`/opportunities/${lead.public_slug}`} target="_blank" rel="noreferrer">{lead.public_slug}</a>
              ) : '-'}
            </div>
            <div>{lead.source || '-'}</div>
            <div>{formatDate(lead.created_at)}</div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderPublicPages = () => (
    <div className="public-workspace animate-fade-in">
      <div className="leads-header">
        <div>
          <span className="eyebrow"><Globe2 size={14} /> Search and agent entry points</span>
          <h3 className="scan-title outfit-font">Public opportunity pages</h3>
          <p>Indexable pages and machine-readable feeds for acquisition through search, directories, partner links, and AI agents.</p>
        </div>
        <div className="leads-actions">
          <a className="btn-filter" href="/sitemap.xml" target="_blank" rel="noreferrer">
            <ExternalLink size={14} /> Sitemap
          </a>
          <a className="btn-filter" href="/public-opportunities.json" target="_blank" rel="noreferrer">
            <ExternalLink size={14} /> Feed
          </a>
          <a className="btn-filter" href="/opportunities.xml" target="_blank" rel="noreferrer">
            <ExternalLink size={14} /> RSS
          </a>
          <a className="btn-filter" href="/llms.txt" target="_blank" rel="noreferrer">
            <ExternalLink size={14} /> llms.txt
          </a>
        </div>
      </div>

      <div className="public-config glass-panel">
        <div>
          <span>Public base URL</span>
          <strong>{publicBaseUrl || window.location.origin}</strong>
        </div>
        <p>Set GOLDIDEAS_PUBLIC_BASE_URL in production so sitemap and feeds use the real domain.</p>
      </div>

      <div className="public-table glass-panel">
        <div className="public-row public-row-head">
          <div>Page</div>
          <div>Evidence</div>
          <div>Leads</div>
          <div>Rating</div>
          <div>Last seen</div>
          <div>Actions</div>
        </div>
        {isLoadingPublicPages && (
          <div className="state-row">
            <Loader2 size={18} className="spin" />
            <span>Loading public pages...</span>
          </div>
        )}
        {publicPagesError && (
          <div className="state-row error-state">
            <AlertCircle size={18} />
            <span>{publicPagesError}</span>
          </div>
        )}
        {!isLoadingPublicPages && !publicPagesError && publicPages.length === 0 && (
          <div className="empty-state">
            <h4>No public pages yet</h4>
            <p>Run a validation search first. Each stored opportunity becomes a public page candidate.</p>
          </div>
        )}
        {publicPages.map((page) => (
          <div className="public-row" key={page.id || page.slug}>
            <div>
              <strong>{page.title || page.slug}</strong>
              <span className="lead-meta">{page.summary || page.url}</span>
            </div>
            <div>{page.evidence_count || 1} signals / {page.source_count || 1} sources</div>
            <div><span className="lead-count">{page.lead_count || 0}</span></div>
            <div>
              <span className={`rating-badge ${ratingClass(page.rating)}`}>{page.rating || 'UNRATED'}</span>
            </div>
            <div>{formatDate(page.last_seen_at)}</div>
            <div className="public-actions-cell">
              <button className="icon-link" type="button" onClick={() => copyPublicUrl(page)} aria-label={`Copy ${page.title || page.slug}`}>
                {copiedSlug === page.slug ? <Check size={16} /> : <Copy size={16} />}
              </button>
              <a className="icon-link" href={page.path || `/opportunities/${page.slug}`} target="_blank" rel="noreferrer" aria-label={`Open ${page.title || page.slug}`}>
                <ExternalLink size={16} />
              </a>
              <a className="icon-link text-link" href={page.markdown_path || `/opportunities/${page.slug}.md`} target="_blank" rel="noreferrer" aria-label={`Open Markdown for ${page.title || page.slug}`}>
                MD
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <main className="workspace">
      {activeModule === 'opportunities'
        ? renderOpportunities()
        : activeModule === 'publicPages'
          ? renderPublicPages()
          : activeModule === 'leads'
            ? renderLeads()
            : renderPlaceholder()}
    </main>
  );
};

export default Workspace;
