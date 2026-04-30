import React from 'react';
import { Filter, ArrowUpDown } from 'lucide-react';
import { mockOpportunities } from '../mockData';
import './Workspace.css';

interface WorkspaceProps {
  activeModule: string;
  selectedItem: any;
  setSelectedItem: (item: any) => void;
  t: (key: string) => string;
}

const Workspace: React.FC<WorkspaceProps> = ({ activeModule, selectedItem, setSelectedItem, t }) => {

  const renderOpportunities = () => {
    return (
      <div className="opportunities-workspace animate-fade-in">
        <div className="workspace-toolbar">
          <div className="toolbar-left">
            <h3 className="view-title outfit-font">{t('allOpportunities')}</h3>
            <span className="badge">{mockOpportunities.length}</span>
          </div>
          <div className="toolbar-right">
            <button className="btn-filter">
              <Filter size={14} /> {t('filter')}
            </button>
            <button className="btn-filter">
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
            {mockOpportunities.map((opt) => (
              <div 
                key={opt.id} 
                className={`list-row ${selectedItem?.id === opt.id ? 'selected' : ''}`}
                onClick={() => setSelectedItem(opt)}
              >
                <div className="col-rating">
                  <span className={`rating-badge ${opt.rating.includes('GREEN') ? 'green' : opt.rating.includes('YELLOW') ? 'yellow' : 'red'}`}>
                    {opt.rating}
                  </span>
                </div>
                <div className="col-title">
                  <span className="truncate">{opt.title}</span>
                </div>
                <div className="col-score">
                  <div className="score-pill">
                    {opt.total_score.toFixed(1)}
                  </div>
                </div>
                <div className="col-source">
                  <span className="source-tag">{opt.source}</span>
                </div>
                <div className="col-date">
                  <span className="date-text">
                    {new Date(opt.published).toLocaleDateString()}
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

  return (
    <main className="workspace">
      {activeModule === 'opportunities' ? renderOpportunities() : renderPlaceholder()}
    </main>
  );
};

export default Workspace;
