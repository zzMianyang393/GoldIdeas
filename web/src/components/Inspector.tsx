import React from 'react';
import { X, ExternalLink, Activity, FileText, Target } from 'lucide-react';
import './Inspector.css';

interface InspectorProps {
  item: any;
  activeModule: string;
  onClose: () => void;
  t: (key: string) => string;
}

const Inspector: React.FC<InspectorProps> = ({ item, activeModule, onClose, t }) => {
  if (activeModule !== 'opportunities') {
    return (
      <aside className="inspector glass-panel animate-fade-in">
        <div className="inspector-header">
          <h3 className="outfit-font">{t('detail')}</h3>
          <button className="btn-close" onClick={onClose}>
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
    <aside className="inspector glass-panel animate-fade-in">
      <div className="inspector-header">
        <div className="inspector-header-top">
          <h3 className="outfit-font">{t('optDetail')}</h3>
          <button className="btn-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
      </div>

      <div className="inspector-content">
        <div className="inspector-section">
          <div className="meta-tags">
            <span className={`rating-badge ${item.rating.includes('GREEN') ? 'green' : item.rating.includes('YELLOW') ? 'yellow' : 'red'}`}>
              {item.rating}
            </span>
            <span className="source-tag">{item.source}</span>
          </div>
          
          <h2 className="item-title outfit-font">{item.title}</h2>
          
          <div className="actions-row">
            <button className="btn-outline">
              <ExternalLink size={14} /> {t('openOriginal')}
            </button>
            <button className="btn-primary-small">
              <FileText size={14} /> {t('generateReport')}
            </button>
          </div>
        </div>

        <div className="inspector-section">
          <h4 className="section-title outfit-font"><Activity size={14} /> {t('aiSummary')}</h4>
          <p className="summary-text">{item.content_summary}</p>
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
          <h4 className="section-title outfit-font"><Target size={14} /> {t('fiveDimScore')} ({item.total_score.toFixed(1)})</h4>
          <div className="score-bars">
            {Object.entries(item.scores).map(([label, score]: [string, any]) => (
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
              </div>
            ))}
          </div>
        </div>

        {item.redlines && item.redlines.length > 0 && (
          <div className="inspector-section">
            <h4 className="section-title text-red outfit-font">{t('redlineTriggered')}</h4>
            <ul className="redline-list">
              {item.redlines.map((redline: string, i: number) => (
                <li key={i}>{redline}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Inspector;
