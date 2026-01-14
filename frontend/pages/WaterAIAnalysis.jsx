import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import WaterAIWizard from '../components/wizards/WaterAIWizard';
import PageHeader from '../components/shared/PageHeader';
import { Droplet, ArrowLeft } from 'lucide-react';
import './WaterAIAnalysis.css';

function WaterAIAnalysis() {
  const navigate = useNavigate();
  const [showSuccessMessage, setShowSuccessMessage] = useState(false);

  const handleComplete = (report) => {
    setShowSuccessMessage(true);
    
    setTimeout(() => {
      navigate('/app/water-ai-reports');
    }, 3000);
  };

  return (
    <div className="water-ai-analysis-page">
      <PageHeader
        title="HidroponIA Vision"
        subtitle="Análisis inteligente de agua para hidroponía"
        icon={Droplet}
      />

      {showSuccessMessage && (
        <div className="success-banner">
          <div className="success-content">
            <div className="success-icon">✓</div>
            <div>
              <h3>¡Análisis Completado!</h3>
              <p>Redirigiendo a tus reportes...</p>
            </div>
          </div>
        </div>
      )}

      <WaterAIWizard onComplete={handleComplete} />

      <div className="back-action">
        <button onClick={() => navigate('/app/dashboard')} className="back-btn">
          <ArrowLeft />
          Volver al Dashboard
        </button>
      </div>
    </div>
  );
}

export default WaterAIAnalysis;
