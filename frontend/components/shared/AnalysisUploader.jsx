import React, { useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import { Upload, FileText, Image, CheckCircle, AlertCircle, X, Loader } from 'lucide-react';
import Button from './Button';
import AnalysisDataPreviewModal from './AnalysisDataPreviewModal';

/**
 * AnalysisUploader Component
 * 
 * Allows users to upload soil or water analysis reports (PDF/JPG)
 * and automatically extract data using GPT-4 Vision OCR.
 * 
 * @param {Object} props
 * @param {string} props.type - "soil" or "water"
 * @param {Function} props.onDataExtracted - Callback when data is successfully extracted
 * @param {Function} props.onCancel - Callback when user cancels
 */
function AnalysisUploader({ type, onDataExtracted, onCancel }) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [error, setError] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  const apiEndpoint = type === 'soil' 
    ? '/api/ai/extract-soil-analysis'
    : '/api/ai/extract-water-analysis';

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const validateFile = (file) => {
    const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png'];
    const maxSize = 10 * 1024 * 1024; // 10MB

    if (!validTypes.includes(file.type)) {
      throw new Error('Solo se permiten archivos PDF, JPG o PNG');
    }

    if (file.size > maxSize) {
      throw new Error('El archivo no debe exceder 10MB');
    }
  };

  const uploadFile = async (file) => {
    try {
      validateFile(file);
      setUploading(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(apiEndpoint, {
        method: 'POST',
        body: formData,
        credentials: 'include'
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Error al procesar el archivo');
      }

      if (!result.success) {
        throw new Error(result.error || 'No se pudo extraer información del análisis');
      }

      setExtractedData(result);
      setShowPreview(true); // Show preview modal instead of inline preview
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message);
    } finally {
      setUploading(false);
      setDragActive(false);
    }
  };

  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  }, [type]);

  const handleFileInput = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0]);
    }
  };

  const handleAcceptPreview = (editedData) => {
    onDataExtracted(editedData);
    setShowPreview(false);
    setExtractedData(null);
  };

  const handleCancelPreview = () => {
    setShowPreview(false);
  };

  const handleReset = () => {
    setExtractedData(null);
    setError(null);
    setShowPreview(false);
  };

  return (
    <div>
      {/* Success banner with review button when data is extracted but modal closed */}
      {extractedData && !showPreview && (
        <div style={{
          background: 'var(--success-50)',
          border: '2px solid var(--success-500)',
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-4)',
          marginBottom: 'var(--space-4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 'var(--space-3)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <CheckCircle size={24} color="var(--success-600)" />
            <div>
              <p style={{
                fontSize: 'var(--text-base)',
                fontWeight: 'var(--font-semibold)',
                color: 'var(--success-800)',
                margin: 0
              }}>
                Datos Extraídos Listos
              </p>
              <p style={{
                fontSize: 'var(--text-sm)',
                color: 'var(--success-700)',
                margin: 0
              }}>
                Revisa y acepta los datos para continuar
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <Button
              variant="secondary"
              onClick={handleReset}
            >
              Nuevo Archivo
            </Button>
            <Button
              variant="primary"
              onClick={() => setShowPreview(true)}
            >
              Revisar Datos
            </Button>
          </div>
        </div>
      )}

      {/* Upload Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragActive ? 'var(--primary-500)' : 'var(--gray-300)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-8)',
          textAlign: 'center',
          background: dragActive ? 'var(--primary-50)' : 'var(--color-bg-secondary)',
          transition: 'all var(--transition)',
          cursor: uploading ? 'wait' : 'pointer',
          position: 'relative'
        }}
      >
        <input
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          onChange={handleFileInput}
          disabled={uploading}
          style={{
            position: 'absolute',
            opacity: 0,
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            cursor: 'pointer'
          }}
        />

        {uploading ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 'var(--space-3)'
          }}>
            <Loader size={48} color="var(--primary-500)" className="spin" />
            <p style={{
              fontSize: 'var(--text-base)',
              fontWeight: 'var(--font-semibold)',
              color: 'var(--color-text-primary)',
              margin: 0
            }}>
              Procesando con IA...
            </p>
            <p style={{
              fontSize: 'var(--text-sm)',
              color: 'var(--color-text-secondary)',
              margin: 0
            }}>
              Extrayendo datos del análisis
            </p>
          </div>
        ) : (
          <>
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              gap: 'var(--space-4)',
              marginBottom: 'var(--space-4)'
            }}>
              <FileText size={40} color="var(--primary-500)" />
              <Upload size={40} color="var(--primary-500)" />
              <Image size={40} color="var(--primary-500)" />
            </div>
            
            <h4 style={{
              fontSize: 'var(--text-lg)',
              fontWeight: 'var(--font-bold)',
              color: 'var(--color-text-primary)',
              margin: '0 0 var(--space-2) 0'
            }}>
              Arrastra tu análisis aquí o haz click para seleccionar
            </h4>
            
            <p style={{
              fontSize: 'var(--text-sm)',
              color: 'var(--color-text-secondary)',
              margin: '0 0 var(--space-4) 0'
            }}>
              Formatos: PDF, JPG, PNG • Tamaño máx: 10MB
            </p>

            <div style={{
              background: 'var(--color-bg-primary)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--gray-200)',
              maxWidth: '400px',
              margin: '0 auto'
            }}>
              <p style={{
                fontSize: 'var(--text-xs)',
                color: 'var(--color-text-secondary)',
                margin: 0,
                lineHeight: '1.5'
              }}>
                💡 <strong>Tip:</strong> Para mejores resultados, asegúrate que el análisis sea legible y esté bien iluminado
              </p>
            </div>
          </>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div style={{
          background: 'var(--error-50)',
          border: '1px solid var(--error-300)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          marginTop: 'var(--space-4)',
          display: 'flex',
          alignItems: 'flex-start',
          gap: 'var(--space-3)'
        }}>
          <AlertCircle size={20} color="var(--error-600)" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ flex: 1 }}>
            <p style={{
              fontSize: 'var(--text-sm)',
              fontWeight: 'var(--font-semibold)',
              color: 'var(--error-800)',
              margin: '0 0 var(--space-1) 0'
            }}>
              No se pudo procesar el archivo
            </p>
            <p style={{
              fontSize: 'var(--text-sm)',
              color: 'var(--error-700)',
              margin: 0
            }}>
              {error}
            </p>
          </div>
          <button
            onClick={() => setError(null)}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: 'var(--space-1)'
            }}
          >
            <X size={18} color="var(--error-600)" />
          </button>
        </div>
      )}

      {/* Alternative Option */}
      <div style={{
        textAlign: 'center',
        marginTop: 'var(--space-4)'
      }}>
        <button
          onClick={onCancel}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--color-text-secondary)',
            fontSize: 'var(--text-sm)',
            cursor: 'pointer',
            textDecoration: 'underline',
            padding: 'var(--space-2)'
          }}
        >
          Prefiero ingresar los datos manualmente
        </button>
      </div>

      {/* Preview Modal */}
      {showPreview && extractedData && (
        <AnalysisDataPreviewModal
          extractedData={extractedData.data}
          confidence={extractedData.confidence}
          validationWarnings={extractedData.validation_warnings}
          notes={extractedData.data?.notes}
          onAccept={handleAcceptPreview}
          onCancel={handleCancelPreview}
        />
      )}

      {/* Loading spinner animation */}
      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          .spin {
            animation: spin 1s linear infinite;
          }
        `}
      </style>
    </div>
  );
}

AnalysisUploader.propTypes = {
  type: PropTypes.oneOf(['soil', 'water']).isRequired,
  onDataExtracted: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired
};

export default AnalysisUploader;
