import React, { useState } from 'react';
import { X, Lock, Zap, TrendingUp, Shield, Check, Sparkles, Crown, Infinity, Calculator, Headphones, GraduationCap } from 'lucide-react';
import api from '../services/api';

const LimitReachedModal = ({ isOpen, onClose, module, closeable = false }) => {
  const [loadingEssential, setLoadingEssential] = useState(false);
  const [loadingPro, setLoadingPro] = useState(false);
  const [loadingPremium, setLoadingPremium] = useState(false);
  const [currency, setCurrency] = useState('mxn');

  const prices = {
    usd: { essential: '$10', pro: '$18', premium: '$30', suffix: 'USD/mes' },
    mxn: { essential: '$200', pro: '$360', premium: '$600', suffix: 'MXN/mes' }
  };

  const handleUpgradeEssential = async () => {
    setLoadingEssential(true);
    try {
      const response = await api.post(`/api/subscription/create-checkout-essential?currency=${currency}`);
      if (response && response.checkout_url) {
        window.location.href = response.checkout_url;
      } else {
        throw new Error('No se recibió URL de checkout');
      }
    } catch (error) {
      console.error('Error creating essential checkout session:', error);
      alert('El Plan Essential estará disponible próximamente. Por favor contáctanos para más información.');
    } finally {
      setLoadingEssential(false);
    }
  };

  const handleUpgradePro = async () => {
    setLoadingPro(true);
    try {
      const response = await api.post(`/api/subscription/create-checkout?currency=${currency}`);
      if (response && response.checkout_url) {
        window.location.href = response.checkout_url;
      } else {
        throw new Error('No se recibió URL de checkout');
      }
    } catch (error) {
      console.error('Error creating pro checkout session:', error);
      alert('Error al iniciar el proceso de pago. Por favor intenta nuevamente.');
    } finally {
      setLoadingPro(false);
    }
  };

  const handleUpgradePremium = async () => {
    setLoadingPremium(true);
    try {
      const response = await api.post(`/api/subscription/create-checkout-premium?currency=${currency}`);
      if (response && response.checkout_url) {
        window.location.href = response.checkout_url;
      } else {
        throw new Error('No se recibió URL de checkout');
      }
    } catch (error) {
      console.error('Error creating premium checkout session:', error);
      alert('El Plan Premium estará disponible próximamente. Por favor contáctanos para más información.');
    } finally {
      setLoadingPremium(false);
    }
  };

  const isLoading = loadingEssential || loadingPro || loadingPremium;

  if (!isOpen) return null;

  const getModuleConfig = (mod) => {
    switch (mod) {
      case 'soil':
        return {
          name: 'SUELO',
          color: { primary: '#22c55e', secondary: '#16a34a', light: '#86efac' }
        };
      case 'hydro_ions':
        return {
          name: 'HIDROPONÍA AVANZADA',
          color: { primary: '#1e40af', secondary: '#1e3a8a', light: '#93c5fd' }
        };
      case 'foliar':
        return {
          name: 'FOLIAR',
          color: { primary: '#f59e0b', secondary: '#d97706', light: '#fcd34d' }
        };
      case 'irrigation':
        return {
          name: 'RIEGO PREMIUM',
          color: { primary: '#0d9488', secondary: '#0f766e', light: '#5eead4' }
        };
      case 'fertiirrigation':
        return {
          name: 'FERTIRRIEGO',
          color: { primary: '#1e40af', secondary: '#1e3a8a', light: '#93c5fd' }
        };
      default:
        return {
          name: 'HIDROPONÍA',
          color: { primary: '#0ea5e9', secondary: '#0284c7', light: '#7dd3fc' }
        };
    }
  };

  const moduleConfig = getModuleConfig(module);
  const moduleName = moduleConfig.name;
  const moduleColor = moduleConfig.color;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      backdropFilter: 'blur(8px)',
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '16px',
      animation: 'fadeIn 0.3s ease-out'
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '24px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        maxWidth: '900px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        animation: 'slideUp 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
        position: 'relative'
      }}>
        {/* Decorative Top Bar */}
        <div style={{
          height: '4px',
          background: 'linear-gradient(90deg, #1e40af 0%, #1d4ed8 33%, #3b82f6 66%, #60a5fa 100%)'
        }} />
        
        {/* Header */}
        <div className="modal-header" style={{
          background: `linear-gradient(135deg, ${moduleColor.primary} 0%, ${moduleColor.secondary} 100%)`,
          padding: '48px 32px',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* Animated Background Circles */}
          <div style={{
            position: 'absolute',
            top: '-100px',
            left: '-100px',
            width: '300px',
            height: '300px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '50%',
            filter: 'blur(60px)',
            animation: 'pulse 3s ease-in-out infinite'
          }} />
          <div style={{
            position: 'absolute',
            bottom: '-150px',
            right: '-150px',
            width: '400px',
            height: '400px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '50%',
            filter: 'blur(80px)',
            animation: 'pulse 4s ease-in-out infinite',
            animationDelay: '1s'
          }} />

          {/* Close Button - Only shown if closeable */}
          {closeable && (
            <button
              onClick={onClose}
              style={{
                position: 'absolute',
                top: '24px',
                right: '24px',
                background: 'rgba(255, 255, 255, 0.2)',
                border: 'none',
                borderRadius: '50%',
                width: '40px',
                height: '40px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s',
                zIndex: 10
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)'}
            >
              <X color="white" size={24} />
            </button>
          )}

          <div style={{ position: 'relative', zIndex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '24px', marginBottom: '24px' }}>
              <div style={{
                width: '96px',
                height: '96px',
                background: 'rgba(255, 255, 255, 0.2)',
                backdropFilter: 'blur(10px)',
                borderRadius: '24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '2px solid rgba(255, 255, 255, 0.4)',
                position: 'relative',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)'
              }}>
                <Crown color="#fde047" size={56} strokeWidth={2.5} />
                <div style={{
                  position: 'absolute',
                  top: '-4px',
                  right: '-4px',
                  width: '16px',
                  height: '16px',
                  background: '#fde047',
                  borderRadius: '50%',
                  animation: 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite'
                }} />
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <h2 style={{
                    fontSize: '48px',
                    fontWeight: '900',
                    color: 'white',
                    margin: 0,
                    textShadow: '0 2px 10px rgba(0, 0, 0, 0.3)',
                    letterSpacing: '-0.5px'
                  }}>
                    Prueba Terminada
                  </h2>
                  <Zap color="#fde047" size={32} strokeWidth={3} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    padding: '6px 16px',
                    background: 'rgba(255, 255, 255, 0.25)',
                    border: '1px solid rgba(255, 255, 255, 0.4)',
                    borderRadius: '20px',
                    fontSize: '13px',
                    fontWeight: '700',
                    color: 'white'
                  }}>
                    {moduleName}
                  </div>
                  <span style={{ color: 'rgba(255, 255, 255, 0.95)', fontSize: '15px', fontWeight: '600' }}>
                    7 días de prueba completados
                  </span>
                </div>
              </div>
            </div>

            <p style={{
              color: 'rgba(255, 255, 255, 0.95)',
              fontSize: '18px',
              lineHeight: '1.7',
              fontWeight: '500',
              maxWidth: '700px',
              margin: 0
            }}>
              Tu periodo de prueba gratuita de <strong style={{ color: '#fde047' }}>7 días</strong> ha finalizado. 
              Elige un plan para continuar usando las <strong style={{ color: '#fde047' }}>calculadoras ilimitadas</strong>.
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="modal-content" style={{
          padding: '48px 32px',
          background: 'linear-gradient(to bottom, #f9fafb 0%, white 100%)'
        }}>
          
          {/* Premium Badge */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            marginTop: '-80px',
            marginBottom: '48px'
          }}>
            <div style={{
              background: 'linear-gradient(135deg, #1e40af 0%, #1e3a8a 50%, #1d4ed8 100%)',
              padding: '24px 40px',
              borderRadius: '20px',
              boxShadow: '0 20px 40px rgba(30, 64, 175, 0.4)',
              border: '4px solid white',
              display: 'flex',
              alignItems: 'center',
              gap: '16px'
            }}>
              <Crown color="#fbbf24" size={36} />
              <div>
                <div style={{ fontSize: '28px', fontWeight: '900', color: 'white', lineHeight: '1.2' }}>
                  Plan Premium
                </div>
                <div style={{ fontSize: '14px', color: '#bfdbfe', fontWeight: '600' }}>
                  Acceso completo e ilimitado
                </div>
              </div>
            </div>
          </div>

          {/* Benefits Title */}
          <div style={{ marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                background: 'linear-gradient(135deg, #1e40af 0%, #1d4ed8 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Zap color="white" size={24} />
              </div>
              <h3 style={{ fontSize: '28px', fontWeight: '800', color: '#111827', margin: 0 }}>
                Beneficios Premium
              </h3>
            </div>
          </div>

          {/* Benefits Grid */}
          <div className="benefits-grid" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '20px',
            marginBottom: '40px'
          }}>
            {/* Benefit 1 */}
            <div style={{
              background: 'white',
              borderRadius: '16px',
              padding: '24px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
              border: '2px solid transparent',
              transition: 'all 0.3s',
              cursor: 'default'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 12px 28px rgba(0, 0, 0, 0.15)';
              e.currentTarget.style.borderColor = '#86efac';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.08)';
              e.currentTarget.style.borderColor = 'transparent';
              e.currentTarget.style.transform = 'translateY(0)';
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                <div style={{
                  width: '56px',
                  height: '56px',
                  background: 'linear-gradient(135deg, #4ade80 0%, #10b981 100%)',
                  borderRadius: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  boxShadow: '0 8px 16px rgba(34, 197, 94, 0.3)',
                  transition: 'transform 0.3s'
                }}>
                  <Infinity color="white" size={28} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: '#111827', marginBottom: '6px' }}>
                    Cálculos Ilimitados
                  </div>
                  <div style={{ fontSize: '15px', color: '#6b7280', lineHeight: '1.6' }}>
                    Realice todos los cálculos que necesite en ambos módulos sin restricciones
                  </div>
                </div>
              </div>
            </div>

            {/* Benefit 2 */}
            <div style={{
              background: 'white',
              borderRadius: '16px',
              padding: '24px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
              border: '2px solid transparent',
              transition: 'all 0.3s',
              cursor: 'default'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 12px 28px rgba(0, 0, 0, 0.15)';
              e.currentTarget.style.borderColor = '#7dd3fc';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.08)';
              e.currentTarget.style.borderColor = 'transparent';
              e.currentTarget.style.transform = 'translateY(0)';
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                <div style={{
                  width: '56px',
                  height: '56px',
                  background: 'linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%)',
                  borderRadius: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  boxShadow: '0 8px 16px rgba(14, 165, 233, 0.3)',
                  transition: 'transform 0.3s'
                }}>
                  <TrendingUp color="white" size={28} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: '#111827', marginBottom: '6px' }}>
                    Reportes Profesionales
                  </div>
                  <div style={{ fontSize: '15px', color: '#6b7280', lineHeight: '1.6' }}>
                    Exporte informes PDF y Excel ilimitados con resultados detallados
                  </div>
                </div>
              </div>
            </div>

            {/* Benefit 3 */}
            <div style={{
              background: 'white',
              borderRadius: '16px',
              padding: '24px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
              border: '2px solid transparent',
              transition: 'all 0.3s',
              cursor: 'default'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 12px 28px rgba(0, 0, 0, 0.15)';
              e.currentTarget.style.borderColor = '#d8b4fe';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.08)';
              e.currentTarget.style.borderColor = 'transparent';
              e.currentTarget.style.transform = 'translateY(0)';
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                <div style={{
                  width: '56px',
                  height: '56px',
                  background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                  borderRadius: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  boxShadow: '0 8px 16px rgba(30, 64, 175, 0.3)',
                  transition: 'transform 0.3s'
                }}>
                  <Sparkles color="white" size={28} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: '#111827', marginBottom: '6px' }}>
                    Modo Profesional
                  </div>
                  <div style={{ fontSize: '15px', color: '#6b7280', lineHeight: '1.6' }}>
                    Acceso completo a calculadora hidropónica con 12 fertilizantes
                  </div>
                </div>
              </div>
            </div>

            {/* Benefit 4 */}
            <div style={{
              background: 'white',
              borderRadius: '16px',
              padding: '24px',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
              border: '2px solid transparent',
              transition: 'all 0.3s',
              cursor: 'default'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 12px 28px rgba(0, 0, 0, 0.15)';
              e.currentTarget.style.borderColor = '#fcd34d';
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.08)';
              e.currentTarget.style.borderColor = 'transparent';
              e.currentTarget.style.transform = 'translateY(0)';
            }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px' }}>
                <div style={{
                  width: '56px',
                  height: '56px',
                  background: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
                  borderRadius: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  boxShadow: '0 8px 16px rgba(245, 158, 11, 0.3)',
                  transition: 'transform 0.3s'
                }}>
                  <Shield color="white" size={28} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '20px', fontWeight: '700', color: '#111827', marginBottom: '6px' }}>
                    Soporte Prioritario
                  </div>
                  <div style={{ fontSize: '15px', color: '#6b7280', lineHeight: '1.6' }}>
                    Atención personalizada y respuesta prioritaria a sus consultas
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Currency Selector */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            marginBottom: '24px'
          }}>
            <div className="currency-selector" style={{
              display: 'flex',
              background: '#f3f4f6',
              borderRadius: '12px',
              padding: '4px',
              gap: '4px'
            }}>
              <button
                className="currency-btn"
                onClick={() => setCurrency('mxn')}
                style={{
                  padding: '10px 24px',
                  borderRadius: '8px',
                  border: 'none',
                  fontWeight: '700',
                  fontSize: '14px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  background: currency === 'mxn' ? 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)' : 'transparent',
                  color: currency === 'mxn' ? 'white' : '#6b7280',
                  boxShadow: currency === 'mxn' ? '0 4px 12px rgba(22, 163, 74, 0.3)' : 'none'
                }}
              >
                Pesos MXN
              </button>
              <button
                className="currency-btn"
                onClick={() => setCurrency('usd')}
                style={{
                  padding: '10px 24px',
                  borderRadius: '8px',
                  border: 'none',
                  fontWeight: '700',
                  fontSize: '14px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  background: currency === 'usd' ? 'linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%)' : 'transparent',
                  color: currency === 'usd' ? 'white' : '#6b7280',
                  boxShadow: currency === 'usd' ? '0 4px 12px rgba(30, 64, 175, 0.3)' : 'none'
                }}
              >
                Dólares USD
              </button>
            </div>
          </div>

          {/* Pricing Cards - Three Options */}
          <div className="pricing-grid" style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            marginBottom: '24px'
          }}>
            {/* Essential Plan Card */}
            <div className="plan-card" style={{
              position: 'relative',
              background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
              borderRadius: '16px',
              padding: '20px',
              paddingTop: '32px',
              boxShadow: '0 4px 12px rgba(37, 99, 235, 0.25)',
              border: '2px solid #2563eb',
              marginTop: '12px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Calculator color="white" size={20} />
                <span style={{ fontSize: '16px', fontWeight: '800', color: 'white' }}>ESSENTIAL</span>
              </div>
              <div style={{ marginBottom: '16px' }}>
                <span className="price-text" style={{ fontSize: '36px', fontWeight: '900', color: 'white' }}>{prices[currency].essential}</span>
                <span style={{ fontSize: '14px', color: 'rgba(255,255,255,0.8)' }}> {prices[currency].suffix}</span>
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 16px 0' }}>
                {['Calculadoras ilimitadas', 'Todos los módulos', 'Actualizaciones incluidas'].map((item, i) => (
                  <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'rgba(255,255,255,0.95)', fontSize: '13px', marginBottom: '6px' }}>
                    <Check size={14} color="white" />
                    {item}
                  </li>
                ))}
              </ul>
              <button
                onClick={handleUpgradeEssential}
                disabled={isLoading}
                style={{
                  width: '100%',
                  background: 'white',
                  color: '#2563eb',
                  fontWeight: '700',
                  fontSize: '14px',
                  padding: '10px',
                  borderRadius: '10px',
                  border: 'none',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  transition: 'all 0.3s',
                  opacity: loadingEssential ? 0.7 : 1
                }}
              >
                {loadingEssential ? (
                  <>
                    <div style={{ width: '16px', height: '16px', border: '2px solid #2563eb', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                    Procesando...
                  </>
                ) : (
                  'Elegir Essential'
                )}
              </button>
            </div>

            {/* Pro Plan Card */}
            <div className="plan-card plan-card-featured" style={{
              position: 'relative',
              background: 'linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%)',
              borderRadius: '16px',
              padding: '20px',
              paddingTop: '32px',
              boxShadow: '0 8px 24px rgba(30, 64, 175, 0.3)',
              border: '3px solid #1e40af',
              marginTop: '12px'
            }}>
              <div style={{
                position: 'absolute',
                top: '-12px',
                left: '50%',
                transform: 'translateX(-50%)',
                padding: '6px 16px',
                background: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
                borderRadius: '20px',
                color: '#1e3a8a',
                fontWeight: '800',
                fontSize: '11px',
                letterSpacing: '0.5px',
                boxShadow: '0 4px 12px rgba(251, 191, 36, 0.4)',
                whiteSpace: 'nowrap',
                zIndex: 10
              }}>
                MÁS POPULAR
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <Zap color="#93c5fd" size={20} />
                <span style={{ fontSize: '16px', fontWeight: '800', color: 'white' }}>PRO</span>
              </div>
              <div style={{ marginBottom: '16px' }}>
                <span className="price-text" style={{ fontSize: '36px', fontWeight: '900', color: 'white' }}>{prices[currency].pro}</span>
                <span style={{ fontSize: '14px', color: '#bfdbfe' }}> {prices[currency].suffix}</span>
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 16px 0' }}>
                {['Todo de Essential', 'Soporte técnico', 'Soporte agronómico (5/mes)'].map((item, i) => (
                  <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#dbeafe', fontSize: '13px', marginBottom: '6px' }}>
                    <Check size={14} color="#93c5fd" />
                    {item}
                  </li>
                ))}
              </ul>
              <button
                onClick={handleUpgradePro}
                disabled={isLoading}
                style={{
                  width: '100%',
                  background: 'white',
                  color: '#1e40af',
                  fontWeight: '700',
                  fontSize: '14px',
                  padding: '10px',
                  borderRadius: '10px',
                  border: 'none',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  transition: 'all 0.3s',
                  opacity: loadingPro ? 0.7 : 1
                }}
              >
                {loadingPro ? (
                  <>
                    <div style={{ width: '16px', height: '16px', border: '2px solid #1e40af', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                    Procesando...
                  </>
                ) : (
                  <>
                    <Zap size={16} />
                    Elegir Pro
                  </>
                )}
              </button>
            </div>

            {/* Premium Plan Card (DESACTIVADO - Próximamente) */}
            <div className="plan-card" style={{
              position: 'relative',
              background: 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
              borderRadius: '16px',
              padding: '20px',
              paddingTop: '32px',
              boxShadow: '0 8px 24px rgba(107, 114, 128, 0.2)',
              border: '2px solid #9ca3af',
              marginTop: '12px',
              opacity: 0.75
            }}>
              <div style={{
                position: 'absolute',
                top: '-12px',
                left: '50%',
                transform: 'translateX(-50%)',
                padding: '6px 16px',
                background: 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)',
                borderRadius: '20px',
                color: 'white',
                fontWeight: '800',
                fontSize: '11px',
                letterSpacing: '0.5px',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                boxShadow: '0 4px 12px rgba(107, 114, 128, 0.4)',
                whiteSpace: 'nowrap',
                zIndex: 10
              }}>
                <GraduationCap size={12} />
                PRÓXIMAMENTE
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <GraduationCap color="#d1d5db" size={20} />
                <span style={{ fontSize: '16px', fontWeight: '800', color: '#d1d5db' }}>PREMIUM</span>
              </div>
              <div style={{ marginBottom: '16px' }}>
                <span className="price-text" style={{ fontSize: '36px', fontWeight: '900', color: '#d1d5db' }}>{prices[currency].premium}</span>
                <span style={{ fontSize: '14px', color: 'rgba(255,255,255,0.5)' }}> {prices[currency].suffix}</span>
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 16px 0' }}>
                {['Todo de Pro', 'Cursos ilimitados', 'Mini-consultoría mensual'].map((item, i) => (
                  <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'rgba(255,255,255,0.6)', fontSize: '13px', marginBottom: '6px' }}>
                    <Check size={14} color="#9ca3af" />
                    {item}
                  </li>
                ))}
              </ul>
              <div
                style={{
                  width: '100%',
                  background: '#9ca3af',
                  color: '#4b5563',
                  fontWeight: '700',
                  fontSize: '14px',
                  padding: '10px',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  cursor: 'not-allowed'
                }}
              >
                <GraduationCap size={16} />
                Próximamente
              </div>
            </div>
          </div>

          {/* Close Button */}
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: '2px solid #d1d5db',
                color: '#6b7280',
                fontWeight: '600',
                fontSize: '14px',
                padding: '12px 32px',
                borderRadius: '10px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#9ca3af';
                e.currentTarget.style.color = '#374151';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#d1d5db';
                e.currentTarget.style.color = '#6b7280';
              }}
            >
              Continuar con Plan Gratuito
            </button>
          </div>

          {/* Security Badge */}
          <div style={{ textAlign: 'center' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              marginBottom: '8px'
            }}>
              <Shield color="#6b7280" size={16} />
              <p style={{
                fontSize: '14px',
                color: '#4b5563',
                fontWeight: '600',
                margin: 0
              }}>
                Pago 100% seguro procesado por Stripe
              </p>
            </div>
            <p style={{
              fontSize: '13px',
              color: '#9ca3af',
              margin: 0
            }}>
              Sin compromisos a largo plazo • Cancele en cualquier momento
            </p>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { 
            opacity: 0;
            transform: translateY(30px) scale(0.95);
          }
          to { 
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        @keyframes pulse {
          0%, 100% { 
            opacity: 0.6;
            transform: scale(1);
          }
          50% { 
            opacity: 0.8;
            transform: scale(1.05);
          }
        }
        @keyframes ping {
          75%, 100% {
            transform: scale(2);
            opacity: 0;
          }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
          .modal-header {
            padding: 32px 20px !important;
          }
          .modal-content {
            padding: 24px 16px !important;
          }
          .benefits-grid {
            gap: 12px !important;
          }
          .benefit-card {
            padding: 16px !important;
          }
          .currency-selector {
            flex-direction: row !important;
          }
          .currency-btn {
            padding: 8px 16px !important;
            font-size: 13px !important;
          }
          .plan-card {
            padding: 16px !important;
          }
          .plan-card .price-text {
            font-size: 28px !important;
          }
          .plan-card-featured {
            transform: none !important;
          }
          .pricing-grid {
            gap: 12px !important;
          }
        }
        
        @media (max-width: 480px) {
          .modal-header {
            padding: 24px 16px !important;
          }
          .modal-header h2 {
            font-size: 22px !important;
          }
          .modal-content {
            padding: 20px 12px !important;
          }
          .benefits-title {
            font-size: 22px !important;
          }
          .benefit-icon {
            width: 44px !important;
            height: 44px !important;
          }
          .benefit-title {
            font-size: 16px !important;
          }
          .currency-btn {
            padding: 8px 12px !important;
            font-size: 12px !important;
          }
          .plan-card {
            padding: 14px !important;
            margin-top: 8px !important;
          }
          .plan-card .price-text {
            font-size: 24px !important;
          }
          .plan-badge {
            font-size: 9px !important;
            padding: 4px 10px !important;
          }
        }
        
        @media (max-width: 360px) {
          .pricing-grid {
            grid-template-columns: 1fr !important;
          }
          .benefits-grid {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>
    </div>
  );
};

export default LimitReachedModal;
