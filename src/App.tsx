import { useState } from 'react';
import Navigation from './components/Navigation';
import HeroSection from './components/HeroSection';
import ScenariosSection from './components/ScenariosSection';
import ArchitectureSection from './components/ArchitectureSection';
import ModulesSection from './components/ModulesSection';
import WorkflowSection from './components/WorkflowSection';
import ContextSection from './components/ContextSection';
import TechStackSection from './components/TechStack';
import SecuritySection from './components/SecuritySection';
import RoadmapSection from './components/RoadmapSection';
import MetricsSection from './components/MetricsSection';

export default function App() {
  const [activeSection, setActiveSection] = useState('overview');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <Navigation activeSection={activeSection} setActiveSection={setActiveSection} />
      <HeroSection />
      <ScenariosSection />
      <ArchitectureSection />
      <ModulesSection />
      <WorkflowSection />
      <ContextSection />
      <TechStackSection />
      <SecuritySection />
      <RoadmapSection />
      <MetricsSection />
      <footer className="py-8 text-center text-slate-400 border-t border-slate-700">
        <p className="text-sm font-medium">Workforce Operations Agent v0.2 合并完整版</p>
        <p className="text-xs mt-1 text-slate-500">智能员工服务与人力运营 Agent 建设方案</p>
      </footer>
    </div>
  );
}
