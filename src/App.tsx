import { useState } from 'react';
import HeroSection from './components/HeroSection';
import ArchitectureSection from './components/ArchitectureSection';
import CoreModules from './components/CoreModules';
import AgenticWorkflow from './components/AgenticWorkflow';
import TechStack from './components/TechStack';
import DataFlow from './components/DataFlow';
import SecuritySection from './components/SecuritySection';
import RoadmapSection from './components/RoadmapSection';
import Navigation from './components/Navigation';

export default function App() {
  const [activeSection, setActiveSection] = useState('overview');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <Navigation activeSection={activeSection} setActiveSection={setActiveSection} />
      <HeroSection />
      <ArchitectureSection />
      <CoreModules />
      <AgenticWorkflow />
      <TechStack />
      <DataFlow />
      <SecuritySection />
      <RoadmapSection />
      <footer className="py-8 text-center text-slate-400 border-t border-slate-700">
        <p>Workforce Operations Agent - Technical Architecture Proposal</p>
        <p className="text-sm mt-2">© 2026 Enterprise AI Solutions</p>
      </footer>
    </div>
  );
}
