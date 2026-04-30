import { useState } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Workspace from './components/Workspace';
import Inspector from './components/Inspector';
import LandingPage from './pages/LandingPage';
import { useTranslation } from './i18n';
import type { Language } from './i18n';
import './App.css';

function App() {
  const [activeModule, setActiveModule] = useState('opportunities');
  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const [language, setLanguage] = useState<Language>('en');
  const [currentView, setCurrentView] = useState<'home' | 'dashboard'>('home');
  const [isLoggedIn] = useState(false);
  const t = useTranslation(language);

  if (currentView === 'home') {
    return (
      <LandingPage 
        language={language} 
        onLanguageChange={setLanguage} 
        onNavigate={setCurrentView}
        isLoggedIn={isLoggedIn}
      />
    );
  }

  return (
    <div className="app-container">
      <Sidebar 
        activeModule={activeModule} 
        setActiveModule={setActiveModule} 
        t={t}
      />
      <div className="main-content">
        <Header 
          activeModule={activeModule} 
          language={language}
          setLanguage={setLanguage}
          t={t}
        />
        <div className="workspace-container">
          <Workspace 
            activeModule={activeModule} 
            selectedItem={selectedItem}
            setSelectedItem={setSelectedItem} 
            t={t}
          />
          {selectedItem && (
            <Inspector 
              item={selectedItem} 
              activeModule={activeModule}
              onClose={() => setSelectedItem(null)} 
              t={t}
            />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
