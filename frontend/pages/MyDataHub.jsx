import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Droplets, Mountain, DollarSign, Database, FileText, Calendar } from 'lucide-react';
import useIsMobile from '../hooks/useIsMobile';
import '../styles/data-modules.css';

import MyWaterAnalysesContent from '../components/mydata/MyWaterAnalysesContent';
import MySoilAnalysesContent from '../components/mydata/MySoilAnalysesContent';
import FertilizerPricesContent from '../components/mydata/FertilizerPricesContent';
import MyReportsContent from '../components/mydata/MyReportsContent';
import MyCalendarContent from '../components/mydata/MyCalendarContent';

const TABS = [
  { id: 'calendar', label: 'Calendario', mobileLabel: 'Calendario', icon: Calendar },
  { id: 'water', label: 'Análisis de Agua', mobileLabel: 'Agua', icon: Droplets },
  { id: 'soil', label: 'Análisis de Suelo', mobileLabel: 'Suelo', icon: Mountain },
  { id: 'prices', label: 'Precios Fertilizantes', mobileLabel: 'Precios', icon: DollarSign },
  { id: 'reports', label: 'Mis Informes', mobileLabel: 'Informes', icon: FileText },
];

export default function MyDataHub() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') || 'calendar';
  const [activeTab, setActiveTab] = useState(initialTab);
  const isMobile = useIsMobile(768);

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab && TABS.some(t => t.id === tab)) {
      setActiveTab(tab);
    }
  }, [searchParams]);

  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setSearchParams({ tab: tabId });
  };

  return (
    <div className="dm-container" style={{ minHeight: '100vh' }}>
      <div className="dm-header">
        <div className="dm-header-content">
          <div className="dm-header-title">
            <div className="dm-header-icon">
              <Database size={24} color="white" />
            </div>
            <div>
              <h1>Mis Datos</h1>
              <p>Gestiona tus análisis y configuraciones para usar en las calculadoras</p>
            </div>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: isMobile ? '16px 12px' : '24px' }}>
        <div className="dm-card" style={{ overflow: 'hidden' }}>
          <div className="dm-tabs">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => handleTabChange(tab.id)}
                  className={`dm-tab ${isActive ? 'dm-tab-active' : ''}`}
                >
                  <Icon size={isMobile ? 16 : 18} />
                  <span>{isMobile ? tab.mobileLabel : tab.label}</span>
                </button>
              );
            })}
          </div>

          <div className="dm-tab-content">
            {activeTab === 'calendar' && <MyCalendarContent />}
            {activeTab === 'water' && <MyWaterAnalysesContent />}
            {activeTab === 'soil' && <MySoilAnalysesContent />}
            {activeTab === 'prices' && <FertilizerPricesContent />}
            {activeTab === 'reports' && <MyReportsContent />}
          </div>
        </div>

        <div className="dm-info-box" style={{ marginTop: '16px' }}>
          <div className="dm-info-box-icon">
            <Database size={isMobile ? 16 : 20} />
          </div>
          <div>
            <h4>Datos compartidos</h4>
            <p>Los análisis y precios que configures aquí estarán disponibles en las calculadoras de Hidroponía y FertiRiego.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
