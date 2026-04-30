import React from 'react';
import { Search, Play, FileText, Clock, Bell, Globe } from 'lucide-react';
import type { Language } from '../i18n';
import './Header.css';

interface HeaderProps {
  activeModule: string;
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const Header: React.FC<HeaderProps> = ({ activeModule, language, setLanguage, t }) => {
  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'zh' : 'en');
  };

  return (
    <header className="header glass-panel animate-fade-in">
      <div className="header-left">
        <h2 className="module-title outfit-font">
          {t(activeModule as any) || activeModule.charAt(0).toUpperCase() + activeModule.slice(1)}
        </h2>
      </div>

      <div className="header-center">
        <div className="search-bar">
          <Search size={16} className="search-icon" />
          <input type="text" placeholder={t('searchPlaceholder')} />
        </div>
      </div>

      <div className="header-right">
        <div className="status-indicator">
          <div className="status-dot green"></div>
          <span className="status-text">{t('engineReady')}</span>
        </div>
        
        <div className="last-run">
          <Clock size={14} />
          <span>{t('lastRun')}</span>
        </div>

        <div className="header-actions">
          <button className="btn-icon" onClick={toggleLanguage} title="Toggle Language">
            <Globe size={18} />
            <span style={{ fontSize: '0.7rem', fontWeight: 600, marginLeft: '4px' }}>
              {language === 'en' ? 'EN' : '中'}
            </span>
          </button>
          <button className="btn-icon">
            <Bell size={18} />
          </button>
          <button className="btn-secondary">
            <FileText size={16} />
            <span>{t('generateReport')}</span>
          </button>
          <button className="btn-primary">
            <Play size={16} fill="currentColor" />
            <span>{t('runScan')}</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
