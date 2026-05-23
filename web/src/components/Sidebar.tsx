import React from 'react';
import { 
  Activity, 
  Lightbulb, 
  FileText, 
  Database, 
  PlaySquare, 
  Settings,
  Hexagon,
  Users,
  Globe2
} from 'lucide-react';
import './Sidebar.css';

interface SidebarProps {
  activeModule: string;
  setActiveModule: (module: string) => void;
  t: (key: string) => string;
}

const Sidebar: React.FC<SidebarProps> = ({ activeModule, setActiveModule, t }) => {
  const modules = [
    { id: 'signals', label: t('signals'), icon: Activity },
    { id: 'opportunities', label: t('opportunities'), icon: Lightbulb },
    { id: 'reports', label: t('reports'), icon: FileText },
    { id: 'publicPages', label: t('publicPages'), icon: Globe2 },
    { id: 'leads', label: t('leads'), icon: Users },
    { id: 'sources', label: t('sources'), icon: Database },
    { id: 'runs', label: t('runs'), icon: PlaySquare },
  ];

  return (
    <div className="sidebar glass-panel">
      <div className="sidebar-header">
        <div className="logo-container">
          <Hexagon className="logo-icon" size={28} />
          <span className="logo-text outfit-font">GoldIdeas</span>
        </div>
        <div className="logo-badge">V4.1</div>
      </div>
      
      <div className="sidebar-nav">
        <div className="nav-section-title">{t('workspace')}</div>
        <nav>
          {modules.map((mod) => {
            const Icon = mod.icon;
            const isActive = activeModule === mod.id;
            return (
              <button
                key={mod.id}
                className={`nav-item ${isActive ? 'active' : ''}`}
                onClick={() => setActiveModule(mod.id)}
              >
                <Icon size={18} className="nav-icon" />
                <span>{mod.label}</span>
                {isActive && <div className="active-indicator" />}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="sidebar-footer">
        <button
          className={`nav-item ${activeModule === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveModule('settings')}
        >
          <Settings size={18} className="nav-icon" />
          <span>{t('settings')}</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
