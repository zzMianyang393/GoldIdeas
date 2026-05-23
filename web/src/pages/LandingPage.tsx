import React, { useState } from 'react';
import { ArrowRight, Globe, Database, Shield, Search, CheckCircle2, GitBranch, Radar } from 'lucide-react';
import type { Language } from '../i18n';
import { useTranslation } from '../i18n';
import './LandingPage.css';

interface LandingPageProps {
  language: Language;
  onLanguageChange: (lang: Language) => void;
  onNavigate: (view: 'dashboard') => void;
  onStartValidation: (query: string) => void;
  isLoggedIn: boolean;
}

const LandingPage: React.FC<LandingPageProps> = ({ language, onLanguageChange, onNavigate, onStartValidation, isLoggedIn }) => {
  const t = useTranslation(language);
  const [query, setQuery] = useState('Shopify returns automation');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onStartValidation(query.trim());
  };

  return (
    <div className="landing-container">
      {/* Background Grid - Minimalist */}
      <div className="grid-bg"></div>

      {/* Header */}
      <header className="landing-header">
        <div className="logo-container">
          <div className="logo-box"></div>
          <span className="logo-text">GoldIdeas</span>
        </div>
        <div className="header-actions">
          <button 
            className="lang-toggle-btn" 
            onClick={() => onLanguageChange(language === 'en' ? 'zh' : 'en')}
          >
            <Globe size={14} />
            <span>{language.toUpperCase()}</span>
          </button>
          
          <div className="auth-buttons">
            {isLoggedIn ? (
              <button className="primary-btn" onClick={() => onNavigate('dashboard')}>
                {t('dashboard')}
                <ArrowRight size={14} />
              </button>
            ) : (
              <>
                <button className="ghost-btn">{t('login')}</button>
                <button className="primary-btn" onClick={() => onStartValidation(query)}>{t('register')}</button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-badge">
          <Radar size={14} />
          <span>{t('heroBadge')}</span>
        </div>
        
        <h1 className="hero-title">
          {t('heroTitle1')}
          <br />
          <span className="text-highlight">{t('heroTitle2')}</span>
        </h1>
        
        <p className="hero-desc">
          {t('heroDesc')}
        </p>

        <form className="hero-validation-form" onSubmit={handleSubmit} data-testid="hero-validation-form">
          <label htmlFor="landing-query">{t('ideaInputLabel')}</label>
          <div className="hero-input-row">
            <Search size={18} />
            <input
              id="landing-query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder={t('ideaInputPlaceholder')}
              data-testid="landing-query"
            />
            <button type="submit" className="cta-primary" data-testid="start-validation">
              {t('getStarted')}
              <ArrowRight size={16} />
            </button>
          </div>
        </form>

        <div className="sample-report">
          <div className="sample-report-header">
            <div>
              <span className="sample-kicker">Sample validation report</span>
              <h3>Shopify returns automation</h3>
            </div>
            <span className="verdict-pill">GO</span>
          </div>
          <div className="sample-grid">
            <div className="sample-cell">
              <span>Evidence</span>
              <strong>18 signals</strong>
              <p>Repeated complaints around manual refunds, return labels, and customer status updates.</p>
            </div>
            <div className="sample-cell">
              <span>Buyer</span>
              <strong>DTC operators</strong>
              <p>Stores doing 200+ monthly orders with support load tied to returns.</p>
            </div>
            <div className="sample-cell">
              <span>Distribution</span>
              <strong>Shopify forums + SEO</strong>
              <p>Search intent exists around return portal alternatives and refund automation.</p>
            </div>
          </div>
          <ul className="report-checks">
            <li><CheckCircle2 size={15} /> Source links attached to every claim</li>
            <li><CheckCircle2 size={15} /> MVP scope and first 20 buyer targets included</li>
            <li><CheckCircle2 size={15} /> GO / PIVOT / KILL decision with risk notes</li>
          </ul>
        </div>
      </section>

      {/* Social Proof */}
      <section className="social-proof">
        <p>{t('trustedBy')}</p>
        <div className="logo-row">
          <div className="fake-logo">Reddit RSS</div>
          <div className="fake-logo">Hacker News</div>
          <div className="fake-logo">Indie Hackers</div>
          <div className="fake-logo">Product Hunt</div>
          <div className="fake-logo">Custom feeds</div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="features-section">
        <div className="feature-grid">
          <div className="feature-card">
            <div className="feature-icon">
              <Database size={20} />
            </div>
            <h3>{t('feat1Title')}</h3>
            <p>{t('feat1Desc')}</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <GitBranch size={20} />
            </div>
            <h3>{t('feat2Title')}</h3>
            <p>{t('feat2Desc')}</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">
              <Shield size={20} />
            </div>
            <h3>{t('feat3Title')}</h3>
            <p>{t('feat3Desc')}</p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="steps-section">
        <h2 className="section-title">{t('stepTitle')}</h2>
        <div className="steps-container">
          <div className="step-item">
            <div className="step-number">01</div>
            <h4>{t('step1Title')}</h4>
            <p>{t('step1Desc')}</p>
          </div>
          <div className="step-line"></div>
          <div className="step-item">
            <div className="step-number">02</div>
            <h4>{t('step2Title')}</h4>
            <p>{t('step2Desc')}</p>
          </div>
          <div className="step-line"></div>
          <div className="step-item">
            <div className="step-number">03</div>
            <h4>{t('step3Title')}</h4>
            <p>{t('step3Desc')}</p>
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="bottom-cta-section">
        <div className="bottom-cta-box">
          <h2>{t('bottomCtaTitle')}</h2>
          <p>{t('bottomCtaDesc')}</p>
          <button className="cta-primary" onClick={() => onStartValidation(query)}>
            {t('getStarted')}
            <ArrowRight size={16} />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-logo">
            <div className="logo-box small"></div>
            <span>GoldIdeas</span>
          </div>
          <div className="footer-links">
            <a href="#">Twitter</a>
            <a href="#">GitHub</a>
            <a href="#">Terms</a>
            <a href="#">Privacy</a>
          </div>
        </div>
        <div className="footer-bottom">
          <p>{t('footerCopyright')}</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
