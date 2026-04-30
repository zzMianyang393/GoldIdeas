import React from 'react';
import { ArrowRight, Globe, Database, Activity, Shield, Terminal, ArrowUpRight } from 'lucide-react';
import type { Language } from '../i18n';
import { useTranslation } from '../i18n';
import './LandingPage.css';

interface LandingPageProps {
  language: Language;
  onLanguageChange: (lang: Language) => void;
  onNavigate: (view: 'dashboard') => void;
  isLoggedIn: boolean;
}

const LandingPage: React.FC<LandingPageProps> = ({ language, onLanguageChange, onNavigate, isLoggedIn }) => {
  const t = useTranslation(language);

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
                <button className="primary-btn" onClick={() => onNavigate('dashboard')}>{t('register')}</button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-badge">
          <Terminal size={14} />
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

        <div className="hero-cta">
          <button className="cta-primary" onClick={() => onNavigate('dashboard')}>
            {t('getStarted')}
            <ArrowRight size={16} />
          </button>
          <button className="cta-secondary">
            {t('viewDemo')}
            <ArrowUpRight size={16} />
          </button>
        </div>

        {/* Dashboard Preview Mockup */}
        <div className="dashboard-mockup">
          <div className="mockup-header">
            <div className="mockup-dots">
              <span></span><span></span><span></span>
            </div>
            <div className="mockup-url">app.goldideas.io/workspace</div>
          </div>
          <div className="mockup-body">
            <div className="mockup-sidebar"></div>
            <div className="mockup-content">
              <div className="mockup-row skeleton"></div>
              <div className="mockup-row skeleton-light"></div>
              <div className="mockup-row skeleton-light"></div>
              <div className="mockup-row skeleton-light"></div>
            </div>
            <div className="mockup-inspector">
              <div className="mockup-circle"></div>
              <div className="mockup-line"></div>
              <div className="mockup-line short"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="social-proof">
        <p>{t('trustedBy')}</p>
        <div className="logo-row">
          <div className="fake-logo">HackerNews</div>
          <div className="fake-logo">IndieHackers</div>
          <div className="fake-logo">Reddit</div>
          <div className="fake-logo">ProductHunt</div>
          <div className="fake-logo">V2EX</div>
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
              <Activity size={20} />
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
          <button className="cta-primary" onClick={() => onNavigate('dashboard')}>
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
