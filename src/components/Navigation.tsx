import { useState, useEffect } from 'react';

interface NavigationProps {
  activeSection: string;
  setActiveSection: (section: string) => void;
}

const navItems = [
  { id: 'overview', label: '概述', icon: 'fa-home' },
  { id: 'scenarios', label: '业务场景', icon: 'fa-th-large' },
  { id: 'architecture', label: '系统架构', icon: 'fa-project-diagram' },
  { id: 'modules', label: '核心模块', icon: 'fa-cubes' },
  { id: 'workflow', label: '工作流', icon: 'fa-route' },
  { id: 'context', label: '数据与Memory', icon: 'fa-database' },
  { id: 'techstack', label: '技术栈', icon: 'fa-layer-group' },
  { id: 'security', label: '安全权限', icon: 'fa-shield-alt' },
  { id: 'roadmap', label: '路线图', icon: 'fa-map-signs' },
  { id: 'metrics', label: '指标总结', icon: 'fa-chart-bar' },
];

export default function Navigation({ activeSection, setActiveSection }: NavigationProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (id: string) => {
    setActiveSection(id);
    const element = document.getElementById(id);
    if (element) element.scrollIntoView({ behavior: 'smooth' });
    setMobileMenuOpen(false);
  };

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled ? 'bg-slate-900/95 backdrop-blur-md shadow-lg' : 'bg-transparent'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <i className="fas fa-robot text-white text-sm"></i>
            </div>
            <span className="font-bold text-lg bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Workforce Agent
            </span>
            <span className="hidden sm:inline text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full">v0.2</span>
          </div>

          <div className="hidden xl:flex items-center space-x-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeSection === item.id
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <i className={`fas ${item.icon} mr-1.5 text-xs`}></i>
                {item.label}
              </button>
            ))}
          </div>

          <button
            className="xl:hidden p-2 rounded-lg text-slate-300 hover:bg-slate-700"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <i className={`fas ${mobileMenuOpen ? 'fa-times' : 'fa-bars'}`}></i>
          </button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="xl:hidden bg-slate-900/95 backdrop-blur-md border-t border-slate-700">
          <div className="px-4 py-3 space-y-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => scrollToSection(item.id)}
                className={`block w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  activeSection === item.id
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <i className={`fas ${item.icon} mr-2 text-xs`}></i>
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}
