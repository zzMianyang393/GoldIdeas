import React, { useEffect, useState } from 'react';
import { X, ExternalLink, Activity, FileText, Target, Link2, Loader2, Quote, Maximize2, Minimize2 } from 'lucide-react';
import { createAiReport, getOpportunityId, listOpportunitySignals, slugifyOpportunity } from '../api';
import type { AiReport, Opportunity, Signal } from '../api';
import './Inspector.css';

interface InspectorProps {
  item: Opportunity;
  activeModule: string;
  onClose: () => void;
  t: (key: string) => string;
}

const ratingClass = (rating = '') => {
  if (rating.includes('GREEN')) return 'green';
  if (rating.includes('YELLOW')) return 'yellow';
  return 'red';
};

type Redline = NonNullable<Opportunity['redlines']>[number];

const redlineText = (redline: Redline) => {
  if (typeof redline === 'string') return redline;
  return [redline.name, redline.reason].filter(Boolean).join(': ');
};

const Inspector: React.FC<InspectorProps> = ({ item, activeModule, onClose, t }) => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [report, setReport] = useState<AiReport | null>(null);
  const [isLoadingSignals, setIsLoadingSignals] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [error, setError] = useState('');
  const opportunityId = getOpportunityId(item);
  const publicPath = `/opportunities/${slugifyOpportunity(item.title || opportunityId || 'opportunity')}`;

  useEffect(() => {
    if (activeModule !== 'opportunities' || !opportunityId) return;
    let cancelled = false;
    setIsLoadingSignals(true);
    setError('');
    setSignals([]);
    setReport(null);
    listOpportunitySignals(opportunityId)
      .then((result) => {
        if (!cancelled) setSignals(result.signals || []);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Unable to load evidence');
      })
      .finally(() => {
        if (!cancelled) setIsLoadingSignals(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeModule, opportunityId]);

  const handleGenerateReport = async () => {
    if (!opportunityId) return;
    setIsGeneratingReport(true);
    setError('');
    try {
      const result = await createAiReport(opportunityId);
      setReport(result.report);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to generate report');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  if (activeModule !== 'opportunities') {
    return (
      <aside className="inspector glass-panel animate-fade-in">
        <div className="inspector-header">
          <h3 className="outfit-font">{t('detail')}</h3>
          <button className="btn-close" onClick={onClose} aria-label="Close detail panel">
            <X size={18} />
          </button>
        </div>
        <div className="inspector-content">
          <p className="placeholder-text">{t('detailPlaceholder')}</p>
        </div>
      </aside>
    );
  }

  return (
    <aside className={`inspector glass-panel animate-fade-in ${isExpanded ? 'expanded' : ''}`}>
      <div className="inspector-header">
        <div className="inspector-header-top">
          <h3 className="outfit-font">{t('optDetail')}</h3>
          <div className="inspector-tools">
            <button
              className="btn-close"
              onClick={() => setIsExpanded((value) => !value)}
              aria-label={isExpanded ? 'Collapse detail panel' : 'Expand detail panel'}
              title={isExpanded ? 'Collapse detail panel' : 'Expand detail panel'}
            >
              {isExpanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
            </button>
            <button className="btn-close" onClick={onClose} aria-label="Close opportunity detail">
              <X size={18} />
            </button>
          </div>
        </div>
      </div>

      <div className="inspector-content">
        <div className="inspector-section">
          <div className="meta-tags">
            <span className={`rating-badge ${ratingClass(item.rating)}`}>
              {item.rating || 'UNRATED'}
            </span>
            <span className="source-tag">{item.source || item.source_group || 'source'}</span>
            {item.evidence_count ? <span className="source-tag">{item.evidence_count} evidence</span> : null}
            {item.source_count ? <span className="source-tag">{item.source_count} sources</span> : null}
          </div>
          
          <h2 className="item-title outfit-font">{item.title}</h2>
          
          <div className="actions-row">
            <a className="btn-outline" href={item.url || item.comments_url || '#'} target="_blank" rel="noreferrer">
              <ExternalLink size={14} /> {t('openOriginal')}
            </a>
            <a className="btn-outline" href={publicPath} target="_blank" rel="noreferrer">
              <ExternalLink size={14} /> Public page
            </a>
            <button className="btn-primary-small" onClick={handleGenerateReport} disabled={isGeneratingReport} data-testid="generate-report">
              {isGeneratingReport ? <Loader2 size={14} className="spin" /> : <FileText size={14} />}
              {isGeneratingReport ? 'Generating...' : t('generateReport')}
            </button>
          </div>
          {error && <p className="inspector-error">{error}</p>}
        </div>

        <div className="inspector-section">
          <h4 className="section-title outfit-font"><Activity size={14} /> {t('aiSummary')}</h4>
          <p className="summary-text">{item.content_summary}</p>
          {item.cluster_keywords?.length ? (
            <div className="keyword-row">
              {item.cluster_keywords.slice(0, 8).map((keyword) => (
                <span key={keyword}>{keyword}</span>
              ))}
            </div>
          ) : null}
          <div className="insight-box">
            <span className="insight-label">{t('keyInsight')}:</span>
            {item.key_insight}
          </div>
          <div className="action-box">
            <span className="action-label">{t('actionItems')}:</span>
            {item.action_items}
          </div>
        </div>

        <div className="inspector-section">
          <h4 className="section-title outfit-font"><Target size={14} /> {t('fiveDimScore')} ({(item.total_score || 0).toFixed(1)})</h4>
          <div className="score-bars">
            {Object.entries(item.scores || {}).map(([label, score]) => (
              <div className="score-row" key={label}>
                <div className="score-label">{label}</div>
                <div className="score-bar-container">
                  <div 
                    className="score-bar-fill" 
                    style={{ 
                      width: `${(score / 10) * 100}%`,
                      backgroundColor: score >= 8 ? 'var(--accent-green)' : score >= 5 ? 'var(--accent-yellow)' : 'var(--accent-red)'
                    }}
                  />
                </div>
                <div className="score-value">{score.toFixed(1)}</div>
                {item.score_reasons?.[label] && <p className="score-reason">{item.score_reasons[label]}</p>}
              </div>
            ))}
          </div>
        </div>

        {item.redlines && item.redlines.length > 0 && (
          <div className="inspector-section">
            <h4 className="section-title text-red outfit-font">{t('redlineTriggered')}</h4>
            <ul className="redline-list">
              {item.redlines.map((redline, i: number) => (
                <li key={i}>{redlineText(redline)}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="inspector-section">
          <h4 className="section-title outfit-font"><Link2 size={14} /> Evidence</h4>
          {isLoadingSignals && (
            <div className="mini-loading"><Loader2 size={14} className="spin" /> Loading evidence...</div>
          )}
          {!isLoadingSignals && signals.length === 0 && (
            <p className="muted-text">No linked source evidence found yet. Run a scan first.</p>
          )}
          <div className="evidence-list">
            {signals.slice(0, 12).map((signal) => (
              <article className="evidence-card" key={signal.id}>
                <div className="evidence-meta">
                  <span>{signal.source || signal.source_group}</span>
                  {signal.published_at && <span>{new Date(signal.published_at).toLocaleDateString()}</span>}
                </div>
                <h5>{signal.title}</h5>
                {signal.content && (
                  <p>
                    <Quote size={12} />
                    {signal.content}
                  </p>
                )}
                <div className="evidence-actions">
                  {signal.url && <a href={signal.url} target="_blank" rel="noreferrer">Open evidence</a>}
                  {signal.comments_url && signal.comments_url !== signal.url && (
                    <a href={signal.comments_url} target="_blank" rel="noreferrer">Open discussion</a>
                  )}
                </div>
              </article>
            ))}
          </div>
        </div>

        {report && (
          <div className="inspector-section">
            <h4 className="section-title outfit-font"><FileText size={14} /> Feasibility Report</h4>
            <div className="report-box">
              <div className="report-meta">
                <span>{report.provider || 'local'}</span>
                {report.cache_hit && <span>cache hit</span>}
              </div>
              {typeof report.report_json?.executive_summary === 'object' && report.report_json.executive_summary !== null && (
                <div className="report-verdict">
                  <span>{String((report.report_json.executive_summary as Record<string, unknown>).verdict || 'REPORT')}</span>
                  <p>{String((report.report_json.executive_summary as Record<string, unknown>).decision_reason || '')}</p>
                </div>
              )}
              <pre>{report.report_markdown || JSON.stringify(report.report_json, null, 2)}</pre>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Inspector;
