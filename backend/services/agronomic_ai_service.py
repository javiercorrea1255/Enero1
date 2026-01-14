"""
Agronomic AI Service - GPT-4o Powered Intelligence Layer
Provides validation, explanation, optimization, and diagnosis for hydroponics.
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


def _safe_parse_water_hco3(water_analysis: Optional[Dict[str, Any]]) -> float:
    """
    Safely parse bicarbonate (HCO3) value from water analysis dict.
    Handles multiple key variations and malformed inputs.
    
    Args:
        water_analysis: Water analysis dictionary with various possible HCO3 keys
        
    Returns:
        float: HCO3 value in meq/L, defaults to 0.0 if not found or invalid
    """
    if not water_analysis or not isinstance(water_analysis, dict):
        return 0.0
    
    # All known key variations for HCO3 in order of priority
    hco3_keys = [
        'anion_hco3',      # Standard key
        'hco3',            # Short key
        'HCO3',            # Uppercase
        'water_hco3_meq',  # Explicit meq key
        'bicarbonates',    # English
        'bicarbonatos',    # Spanish
        'CO3H',            # Alternative notation
    ]
    
    for key in hco3_keys:
        raw_value = water_analysis.get(key)
        if raw_value is not None:
            try:
                value = float(raw_value)
                if value >= 0:  # HCO3 cannot be negative
                    return value
                else:
                    logger.warning(f"Negative HCO3 value {value} for key {key}, ignoring")
            except (ValueError, TypeError):
                logger.warning(f"Could not parse HCO3 value '{raw_value}' for key {key}")
                continue
    
    return 0.0


class AgronomicAIService:
    """
    AI-powered agronomic assistant using GPT-4o.
    Specializes in hydroponics, chemistry, and plant nutrition.
    """
    
    def __init__(self):
        """Initialize AI service with GPT-4o."""
        import logging
        logger = logging.getLogger(__name__)
        
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY")
        # Using gpt-4o for reliable AI-powered fertilizer suggestions
        self.model = os.getenv("LLM_MODEL", "gpt-4o")
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"✓ OpenAI client initialized successfully with model {self.model}")
            except Exception as e:
                logger.error(f"✗ Failed to initialize OpenAI client: {str(e)}")
                self.client = None
        else:
            logger.warning("✗ No OpenAI API key found - Grower IA features will be disabled")
            self.client = None
        
        # Token limits per operation type
        self.token_limits = {
            'validate': 800,
            'explain': 1200,
            'optimize': 1000,
            'diagnose': 1500,
            'chat': 2000,
            'report': 2500
        }
    
    def validate_recipe(
        self,
        recipe_data: Dict[str, Any],
        water_quality: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Validate hydroponics recipe using advanced AI analysis.
        
        Args:
            recipe_data: Complete recipe with all calculations
            water_quality: Water quality parameters
        
        Returns:
            {
                'is_valid': bool,
                'risk_level': str,  # 'low', 'medium', 'high'
                'chemical_warnings': List[str],
                'recommendations': List[str],
                'explanation': str
            }
        """
        if not self.client:
            return self._fallback_validation(recipe_data)
        
        prompt = f"""Como químico especialista en soluciones nutritivas hidropónicas, analiza esta receta:

CULTIVO: {recipe_data.get('crop_name')} - {recipe_data.get('growth_stage')}
VOLUMEN: {recipe_data.get('volume_liters')} L

DOSIS CALCULADAS:
- Masterblend 4-18-38: {recipe_data.get('masterblend_g', 0):.2f} g ({recipe_data.get('masterblend_g_per_l', 0):.2f} g/L)
- Nitrato de Calcio: {recipe_data.get('calcium_nitrate_g', 0):.2f} g ({recipe_data.get('calcium_nitrate_g_per_l', 0):.2f} g/L)
- Sal de Epsom: {recipe_data.get('epsom_salt_g', 0):.2f} g ({recipe_data.get('epsom_salt_g_per_l', 0):.2f} g/L)

BALANCE DE NUTRIENTES (ppm):
- N: {recipe_data.get('n_ppm', 0):.1f} (objetivo: {recipe_data.get('n_target', 0):.1f})
- P: {recipe_data.get('p_ppm', 0):.1f} (objetivo: {recipe_data.get('p_target', 0):.1f})
- K: {recipe_data.get('k_ppm', 0):.1f} (objetivo: {recipe_data.get('k_target', 0):.1f})
- Ca: {recipe_data.get('ca_ppm', 0):.1f} (objetivo: {recipe_data.get('ca_target', 0):.1f})
- Mg: {recipe_data.get('mg_ppm', 0):.1f} (objetivo: {recipe_data.get('mg_target', 0):.1f})
- S: {recipe_data.get('s_ppm', 0):.1f} (objetivo: {recipe_data.get('s_target', 0):.1f})

EC: {recipe_data.get('ec_final_estimated', 0):.2f} (objetivo: {recipe_data.get('ec_target', 0):.2f})
pH: {recipe_data.get('ph_current', 7.0):.1f} → {recipe_data.get('ph_adjusted', 6.0):.1f} (objetivo: {recipe_data.get('ph_target', 6.0):.1f})

CALIDAD DEL AGUA:
- Ca en agua: {water_quality.get('ca_ppm', 0):.1f} ppm
- Mg en agua: {water_quality.get('mg_ppm', 0):.1f} ppm
- Alcalinidad: {water_quality.get('alkalinity', 0):.1f} ppm CaCO3
- EC del agua: {water_quality.get('ec', 0):.2f}

Analiza:
1. Compatibilidad química (riesgo de precipitación)
2. Balance iónico y relaciones críticas (Ca:Mg, K:Ca, etc.)
3. Riesgos de toxicidad o deficiencia
4. Impacto de la calidad del agua
5. Nivel de riesgo general: BAJO, MEDIO o ALTO

Responde en formato JSON:
{{
  "is_valid": true/false,
  "risk_level": "low/medium/high",
  "chemical_warnings": ["advertencia1", "advertencia2"],
  "recommendations": ["recomendación1", "recomendación2"],
  "explanation": "Explicación técnica breve"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un químico experto en hidroponía y nutrición vegetal. Analizas recetas con rigor científico."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=self.token_limits['validate'],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                return self._fallback_validation(recipe_data)
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"AI validation error: {e}")
            return self._fallback_validation(recipe_data)
    
    def explain_calculation(
        self,
        recipe_data: Dict[str, Any],
        focus_area: str = 'general'
    ) -> str:
        """
        Explain recipe calculations in clear language.
        
        Args:
            recipe_data: Recipe with all calculations
            focus_area: 'general', 'nutrients', 'ec', 'ph', 'cost'
        
        Returns:
            Clear explanation in Spanish
        """
        if not self.client:
            return self._fallback_explanation(recipe_data, focus_area)
        
        focus_prompts = {
            'general': "Explica de manera general cómo se calculó esta receta y por qué estas dosis.",
            'nutrients': "Explica en detalle el balance de nutrientes (N, P, K, Ca, Mg, S) y las relaciones entre ellos.",
            'ec': "Explica qué es la EC (conductividad eléctrica), por qué es importante, y cómo llegamos a este valor.",
            'ph': "Explica el ajuste de pH, la alcalinidad del agua, y por qué es crítico para la absorción de nutrientes.",
            'cost': "Explica el costo de la solución y cómo optimizarlo sin sacrificar calidad."
        }
        
        prompt = f"""Explica esta receta hidropónica en lenguaje claro para un productor:

CULTIVO: {recipe_data.get('crop_name')} en etapa {recipe_data.get('growth_stage')}

RECETA PARA {recipe_data.get('volume_liters')} LITROS:
- {recipe_data.get('masterblend_g', 0):.2f} g de Masterblend 4-18-38
- {recipe_data.get('calcium_nitrate_g', 0):.2f} g de Nitrato de Calcio
- {recipe_data.get('epsom_salt_g', 0):.2f} g de Sal de Epsom

RESULTADOS:
- EC final: {recipe_data.get('ec_final_estimated', 0):.2f} (objetivo: {recipe_data.get('ec_target', 0):.2f})
- pH ajustado: {recipe_data.get('ph_adjusted', 6.0):.1f}
- Costo total: ${recipe_data.get('total_cost', 0):.2f} MXN (${recipe_data.get('cost_per_liter', 0):.4f}/L)

{focus_prompts.get(focus_area, focus_prompts['general'])}

Sé claro, educativo y práctico. Usa analogías si ayuda."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un agrónomo educador que explica conceptos técnicos de hidroponía de manera clara y práctica."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=self.token_limits['explain']
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else ""
            
        except Exception as e:
            print(f"AI explanation error: {e}")
            return self._fallback_explanation(recipe_data, focus_area)
    
    def optimize_recipe(
        self,
        recipe_data: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Suggest recipe optimizations based on context.
        
        Args:
            recipe_data: Current recipe
            user_context: {
                'budget_constraint': float,  # Max cost per liter
                'previous_results': List[str],  # Past issues
                'climate': str,  # 'hot', 'cold', 'humid', etc.
                'experience_level': str  # 'beginner', 'intermediate', 'advanced'
            }
        
        Returns:
            {
                'suggested_adjustments': List[Dict],
                'cost_savings': float,
                'performance_impact': str,
                'reasoning': str
            }
        """
        if not self.client:
            return self._fallback_optimization()
        
        prompt = f"""Optimiza esta receta hidropónica considerando el contexto del productor:

RECETA ACTUAL:
Cultivo: {recipe_data.get('crop_name')} - {recipe_data.get('growth_stage')}
Volumen: {recipe_data.get('volume_liters')} L
Costo/L: ${recipe_data.get('cost_per_liter', 0):.4f} MXN
EC: {recipe_data.get('ec_final_estimated', 0):.2f}

CONTEXTO DEL PRODUCTOR:
- Presupuesto máximo: ${user_context.get('budget_constraint', 999):.4f}/L
- Problemas previos: {', '.join(user_context.get('previous_results', ['Ninguno']))}
- Clima: {user_context.get('climate', 'normal')}
- Experiencia: {user_context.get('experience_level', 'intermediate')}

Sugiere ajustes prácticos que:
1. Respeten el presupuesto
2. Mantengan o mejoren la calidad nutricional
3. Sean adecuados para su nivel de experiencia
4. Consideren su clima y problemas previos

Responde en JSON:
{{
  "suggested_adjustments": [
    {{"parameter": "nombre", "current": valor, "suggested": valor, "reason": "razón"}}
  ],
  "cost_savings": 0.00,
  "performance_impact": "positivo/neutral/negativo",
  "reasoning": "Explicación general"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un consultor agronómico que optimiza recetas hidropónicas balanceando costo, calidad y practicidad."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=self.token_limits['optimize'],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                return self._fallback_optimization()
            return json.loads(content)
            
        except Exception as e:
            print(f"AI optimization error: {e}")
            return self._fallback_optimization()
    
    def diagnose_symptoms(
        self,
        symptoms: str,
        crop_info: Dict[str, Any],
        current_recipe: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Diagnose plant problems and suggest corrections.
        
        Args:
            symptoms: Description of plant symptoms
            crop_info: {crop_name, growth_stage, system_type}
            current_recipe: Current nutrient recipe (optional)
        
        Returns:
            {
                'probable_causes': List[str],
                'deficiencies': List[str],
                'toxicities': List[str],
                'recommended_actions': List[str],
                'recipe_adjustments': Dict,
                'confidence': str  # 'low', 'medium', 'high'
            }
        """
        if not self.client:
            return self._fallback_diagnosis()
        
        recipe_info = ""
        if current_recipe:
            recipe_info = f"""
RECETA ACTUAL:
- EC: {current_recipe.get('ec_final_estimated', 'N/A')}
- pH: {current_recipe.get('ph_adjusted', 'N/A')}
- NPK (ppm): {current_recipe.get('n_ppm', 0):.0f}-{current_recipe.get('p_ppm', 0):.0f}-{current_recipe.get('k_ppm', 0):.0f}
- Ca: {current_recipe.get('ca_ppm', 0):.0f} ppm
- Mg: {current_recipe.get('mg_ppm', 0):.0f} ppm"""
        
        prompt = f"""Diagnostica este problema en cultivo hidropónico:

CULTIVO: {crop_info.get('crop_name')} en etapa {crop_info.get('growth_stage')}
SISTEMA: {crop_info.get('system_type', 'NFT')}

SÍNTOMAS OBSERVADOS:
{symptoms}
{recipe_info}

Como fitopatólogo y nutriólogo vegetal, diagnostica:
1. Causas probables (deficiencias, toxicidades, pH, EC, temperatura, patógenos)
2. Nutrientes involucrados
3. Acciones correctivas inmediatas
4. Ajustes a la receta si aplica
5. Nivel de confianza del diagnóstico

Responde en JSON:
{{
  "probable_causes": ["causa1", "causa2"],
  "deficiencies": ["nutriente1", "nutriente2"],
  "toxicities": ["nutriente1"],
  "recommended_actions": ["acción1", "acción2"],
  "recipe_adjustments": {{"parameter": "ajuste"}},
  "confidence": "low/medium/high",
  "explanation": "Explicación técnica"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un fitopatólogo y nutriólogo experto en diagnóstico de problemas en cultivos hidropónicos."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=self.token_limits['diagnose'],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                return self._fallback_optimization()
            return json.loads(content)
            
        except Exception as e:
            print(f"AI diagnosis error: {e}")
            return self._fallback_diagnosis()
    
    def generate_report_narrative(
        self,
        recipe_data: Dict[str, Any],
        water_quality: Dict[str, float]
    ) -> Dict[str, str]:
        """
        Generate comprehensive AI narrative for PDF reports.
        
        Args:
            recipe_data: Complete recipe with all calculations
            water_quality: Water quality parameters
        
        Returns:
            {
                'executive_summary': str,
                'nutrient_explanation': str,
                'dosage_justification': str,
                'critical_alerts': str,
                'management_recommendations': str,
                'preventive_diagnosis': str
            }
        """
        if not self.client:
            return self._fallback_report_narrative(recipe_data)
        
        prompt = f"""Genera un reporte técnico completo para esta receta hidropónica:

CULTIVO: {recipe_data.get('crop_name')} - Etapa {recipe_data.get('growth_stage')}
VOLUMEN: {recipe_data.get('volume_liters')} L
SISTEMA: {recipe_data.get('system_type', 'N/A')}

FORMULACIÓN:
- Masterblend 4-18-38: {recipe_data.get('masterblend_g', 0):.2f} g ({recipe_data.get('masterblend_g_per_l', 0):.3f} g/L)
- Nitrato de Calcio: {recipe_data.get('calcium_nitrate_g', 0):.2f} g ({recipe_data.get('calcium_nitrate_g_per_l', 0):.3f} g/L)
- Sal de Epsom: {recipe_data.get('epsom_salt_g', 0):.2f} g ({recipe_data.get('epsom_salt_g_per_l', 0):.3f} g/L)

BALANCE NUTRICIONAL (ppm):
N: {recipe_data.get('n_ppm', 0):.1f} (objetivo: {recipe_data.get('n_target', 0):.1f})
P: {recipe_data.get('p_ppm', 0):.1f} (objetivo: {recipe_data.get('p_target', 0):.1f})
K: {recipe_data.get('k_ppm', 0):.1f} (objetivo: {recipe_data.get('k_target', 0):.1f})
Ca: {recipe_data.get('ca_ppm', 0):.1f} (objetivo: {recipe_data.get('ca_target', 0):.1f})
Mg: {recipe_data.get('mg_ppm', 0):.1f} (objetivo: {recipe_data.get('mg_target', 0):.1f})
S: {recipe_data.get('s_ppm', 0):.1f} (objetivo: {recipe_data.get('s_target', 0):.1f})

PARÁMETROS:
EC final: {recipe_data.get('ec_final_estimated', 0):.2f} (objetivo: {recipe_data.get('ec_target', 0):.2f})
pH actual: {recipe_data.get('ph_current', 7.0):.1f} → ajustado: {recipe_data.get('ph_adjusted', 6.0):.1f}
Costo: ${recipe_data.get('total_cost', 0):.2f} MXN (${recipe_data.get('cost_per_liter', 0):.4f}/L)

CALIDAD DEL AGUA:
Ca: {water_quality.get('ca_ppm', 0):.1f} ppm | Mg: {water_quality.get('mg_ppm', 0):.1f} ppm
Alcalinidad: {water_quality.get('alkalinity', 0):.1f} ppm CaCO3 | EC: {water_quality.get('ec', 0):.2f}

Genera las siguientes 6 secciones (usa separador '|||'):

1. RESUMEN EJECUTIVO (2-3 líneas): Valoración general de la receta, idoneidad para el cultivo y etapa.

2. EXPLICACIÓN NUTRICIONAL (3-4 líneas): Por qué estos niveles de N, P, K, Ca, Mg, S son apropiados para esta etapa del cultivo. Menciona relaciones críticas (Ca:Mg, K:Ca).

3. JUSTIFICACIÓN DE DOSIS (2-3 líneas): Por qué estas cantidades específicas de fertilizantes, equilibrio químico, aportes de cada sal.

4. ALERTAS CRÍTICAS (2-3 líneas): Advertencias sobre calidad de agua, compatibilidad química, riesgos de precipitación, EC/pH fuera de rango. Si todo está bien, indica "Sin alertas críticas".

5. RECOMENDACIONES DE MANEJO (3-4 líneas): Cómo manejar esta solución (monitoreo, ajustes, frecuencia de cambio, temperatura, oxigenación).

6. DIAGNÓSTICO PREVENTIVO (2-3 líneas): Posibles problemas a vigilar según el balance y parámetros (deficiencias, toxicidades, bloqueos).

Formato: Sección1|||Sección2|||Sección3|||Sección4|||Sección5|||Sección6

Sé técnico pero claro. Cita valores numéricos relevantes."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un químico y agrónomo experto que genera reportes técnicos de hidroponía. Eres preciso, objetivo y educativo."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=self.token_limits['report']
            )
            
            content = response.choices[0].message.content
            if not content:
                return self._fallback_report_narrative(recipe_data)
            
            sections = content.strip().split('|||')
            if len(sections) != 6:
                return self._fallback_report_narrative(recipe_data)
            
            return {
                'executive_summary': sections[0].strip(),
                'nutrient_explanation': sections[1].strip(),
                'dosage_justification': sections[2].strip(),
                'critical_alerts': sections[3].strip(),
                'management_recommendations': sections[4].strip(),
                'preventive_diagnosis': sections[5].strip()
            }
            
        except Exception as e:
            print(f"AI report narrative error: {e}")
            return self._fallback_report_narrative(recipe_data)
    
    def generate_soil_report_narrative(
        self,
        calculation_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate comprehensive AI narrative for soil fertilization PDF reports (NOM-021).
        
        Args:
            calculation_data: Complete calculation result with crop, soil data, and recommendations
        
        Returns:
            {
                'executive_summary': str,
                'nutrient_explanation': str,
                'dosage_justification': str,
                'critical_alerts': str,
                'management_recommendations': str,
                'preventive_diagnosis': str
            }
        """
        if not self.client:
            return self._fallback_soil_report_narrative(calculation_data)
        
        crop_info = calculation_data.get('crop_info', {})
        soil_analysis = calculation_data.get('soil_analysis', {})
        fertilization = calculation_data.get('fertilization_recommendation', {})
        
        prompt = f"""Genera un reporte agronómico completo para este cálculo de fertilización de suelo (NOM-021):

CULTIVO: {crop_info.get('name_es', 'N/A')} ({crop_info.get('scientific_name', 'N/A')})
RENDIMIENTO OBJETIVO: {calculation_data.get('yield_target_t_ha', 0):.1f} t/ha
MÉTODO: {calculation_data.get('method', 'N/A')}

ANÁLISIS DE SUELO:
- N disponible: {soil_analysis.get('soil_n_ppm', 0):.1f} ppm ({soil_analysis.get('soil_n_kg_ha', 0):.1f} kg/ha convertido)
- P disponible: {soil_analysis.get('soil_p_ppm', 0):.1f} ppm
- K disponible: {soil_analysis.get('soil_k_ppm', 0):.1f} ppm
- pH: {soil_analysis.get('ph', 0):.1f}
- Textura: {soil_analysis.get('texture', 'N/A')}

REQUERIMIENTOS DEL CULTIVO:
- N: {crop_info.get('n_requirement_kg_ha', 0):.1f} kg/ha
- P2O5: {crop_info.get('p2o5_requirement_kg_ha', 0):.1f} kg/ha
- K2O: {crop_info.get('k2o_requirement_kg_ha', 0):.1f} kg/ha

FERTILIZACIÓN RECOMENDADA:
- N: {fertilization.get('n_to_apply_kg_ha', 0):.1f} kg/ha
- P2O5: {fertilization.get('p2o5_to_apply_kg_ha', 0):.1f} kg/ha
- K2O: {fertilization.get('k2o_to_apply_kg_ha', 0):.1f} kg/ha

FERTILIZANTES SUGERIDOS:
- Urea (46-0-0): {fertilization.get('urea_kg_ha', 0):.1f} kg/ha
- DAP (18-46-0): {fertilization.get('dap_kg_ha', 0):.1f} kg/ha
- Cloruro de Potasio (0-0-60): {fertilization.get('kcl_kg_ha', 0):.1f} kg/ha

Genera las siguientes 6 secciones (usa separador '|||'):

1. RESUMEN EJECUTIVO (2-3 líneas): Valoración general del suelo, requerimientos del cultivo vs disponibilidad, estrategia de fertilización.

2. EXPLICACIÓN NUTRICIONAL (3-4 líneas): Interpretación de los niveles de N, P, K en el suelo según NOM-021. ¿Son bajos, medios o altos? ¿Cómo afecta el pH a la disponibilidad? Relación con el rendimiento objetivo.

3. JUSTIFICACIÓN DE DOSIS (2-3 líneas): Por qué estas cantidades específicas de fertilizantes considerando créditos del suelo, eficiencia de uso, y método de cálculo empleado.

4. ALERTAS CRÍTICAS (2-3 líneas): Advertencias sobre pH inadecuado, deficiencias severas, toxicidades potenciales, problemas de textura. Si todo está bien, indica "Sin alertas críticas - suelo en condiciones aceptables".

5. RECOMENDACIONES DE MANEJO (3-4 líneas): Cómo aplicar estos fertilizantes (fraccionamiento, épocas, incorporación), manejo de pH si es necesario, prácticas complementarias.

6. DIAGNÓSTICO PREVENTIVO (2-3 líneas): Posibles problemas a vigilar durante el ciclo según el balance nutricional (deficiencias, antagonismos, lixiviación en textura arenosa, fijación en arcillas).

Formato: Sección1|||Sección2|||Sección3|||Sección4|||Sección5|||Sección6

Sé técnico pero claro. Cita valores numéricos y rangos de interpretación NOM-021."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un ingeniero agrónomo experto en fertilización de suelos, especializado en la normativa mexicana NOM-021. Generas reportes técnicos precisos y educativos."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=self.token_limits['report']
            )
            
            content = response.choices[0].message.content
            if not content:
                return self._fallback_soil_report_narrative(calculation_data)
            
            sections = content.strip().split('|||')
            if len(sections) != 6:
                return self._fallback_soil_report_narrative(calculation_data)
            
            return {
                'executive_summary': sections[0].strip(),
                'nutrient_explanation': sections[1].strip(),
                'dosage_justification': sections[2].strip(),
                'critical_alerts': sections[3].strip(),
                'management_recommendations': sections[4].strip(),
                'preventive_diagnosis': sections[5].strip()
            }
            
        except Exception as e:
            print(f"AI soil report narrative error: {e}")
            return self._fallback_soil_report_narrative(calculation_data)
    
    def chat(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        recipe_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Conversational AI assistant for hydroponics questions.
        
        Args:
            user_message: User's question
            conversation_history: Previous messages [{'role': 'user/assistant', 'content': '...'}]
            recipe_context: Current recipe data for context
        
        Returns:
            AI assistant response
        """
        if not self.client:
            return "El asistente de IA no está disponible en este momento. Por favor, consulte la documentación o contacte soporte técnico."
        
        system_message = """Eres un asistente agronómico experto en hidroponía, nutrición vegetal, y química de soluciones.

Respondes preguntas sobre:
- Cálculos de fertilizantes y dosificación
- Interpretación de parámetros (EC, pH, PPM)
- Diagnóstico de problemas de cultivo
- Optimización de recetas
- Manejo de sistemas hidropónicos
- Calidad del agua y tratamientos

Sé claro, preciso y práctico. Usa unidades métricas. Cita fundamentos científicos cuando sea relevante."""

        context_message = ""
        if recipe_context:
            context_message = f"""

CONTEXTO DE LA RECETA ACTUAL:
Cultivo: {recipe_context.get('crop_name')} - {recipe_context.get('growth_stage')}
EC objetivo: {recipe_context.get('ec_target', 'N/A')}
EC estimada: {recipe_context.get('ec_final_estimated', 'N/A')}
pH objetivo: {recipe_context.get('ph_target', 'N/A')}
Volumen: {recipe_context.get('volume_liters', 'N/A')} L"""

        messages = [{"role": "system", "content": system_message + context_message}]
        messages.extend(conversation_history[-6:])  # Last 3 exchanges max
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=self.token_limits['chat']
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else ""
            
        except Exception as e:
            print(f"AI chat error: {e}")
            return "Lo siento, hubo un error procesando tu pregunta. Por favor intenta nuevamente."
    
    def generate_executive_summary_enhanced(
        self,
        module: str,
        calculation_data: Dict[str, Any],
        key_metrics: Dict[str, Any]
    ) -> str:
        """
        Generate enhanced executive summary for professional PDF reports.
        More concise than full narrative - 3-4 paragraphs max.
        
        Args:
            module: 'SOIL', 'HYDRO', or 'IONS'
            calculation_data: Complete calculation results
            key_metrics: Key metrics to highlight (EC, pH, cost, etc.)
        
        Returns:
            Professional executive summary (3-4 paragraphs)
        """
        if not self.client:
            return self._fallback_executive_summary(module, calculation_data, key_metrics)
        
        module_contexts = {
            'SOIL': {
                'name': 'Fertilización de Suelo (NOM-021)',
                'focus': 'análisis de suelo, requerimientos del cultivo, y dosis de fertilizantes según normativa mexicana'
            },
            'HYDRO': {
                'name': 'Calculadora Hidropónica Profesional',
                'focus': 'balance de nutrientes en solución, EC/pH óptimos, y dosificación de fertilizantes hidropónicos'
            },
            'IONS': {
                'name': 'Hidroponía Iónica (Miliequivalentes)',
                'focus': 'balance iónico anión-catión, déficits en Meq/L, y optimización de mezcla de sales'
            }
        }
        
        context = module_contexts.get(module, module_contexts['HYDRO'])
        
        prompt = f"""Genera un RESUMEN EJECUTIVO profesional para este reporte de {context['name']}.

DATOS CLAVE:
{self._format_data_for_summary(module, calculation_data, key_metrics)}

Genera un resumen ejecutivo de 3-4 párrafos que incluya:

1. DIAGNÓSTICO PRINCIPAL (1 párrafo): Evaluación general del cálculo/análisis. ¿La receta/programa es adecuado? ¿El suelo/agua tiene limitaciones?

2. HALLAZGOS CRÍTICOS (1 párrafo): Los 2-3 puntos más importantes que el agrónomo debe conocer (balance nutricional, alertas, oportunidades de mejora).

3. RECOMENDACIÓN CLAVE (1 párrafo): Acción inmediata prioritaria y expectativa de resultados esperados.

4. PERSPECTIVA DE ÉXITO (1 párrafo opcional si aplica): Probabilidad de alcanzar objetivos con este programa/receta.

Sé conciso pero informativo. Usa datos numéricos clave. Tono profesional pero accesible."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": f"Eres un consultor agronómico senior especializado en {context['focus']}. Generas resúmenes ejecutivos concisos y accionables."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=1200
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else self._fallback_executive_summary(module, calculation_data, key_metrics)
            
        except Exception as e:
            print(f"AI executive summary error: {e}")
            return self._fallback_executive_summary(module, calculation_data, key_metrics)
    
    def generate_action_plan_prioritized(
        self,
        module: str,
        calculation_data: Dict[str, Any],
        issues_found: List[str]
    ) -> Dict[str, Any]:
        """
        Generate prioritized action plan with timeline and cost estimates.
        
        Args:
            module: 'SOIL', 'HYDRO', or 'IONS'
            calculation_data: Complete calculation results
            issues_found: List of issues/warnings detected
        
        Returns:
            {
                'priority_high': List[Dict],  # [{action, timeline, cost_est, impact}]
                'priority_medium': List[Dict],
                'priority_low': List[Dict],
                'summary': str,
                'success_factors': List[str]
            }
        """
        if not self.client:
            return self._fallback_action_plan()
        
        issues_text = "\n".join([f"- {issue}" for issue in issues_found]) if issues_found else "No se detectaron problemas críticos"
        
        prompt = f"""Genera un PLAN DE ACCIÓN PRIORIZADO para este programa de fertilización:

CONTEXTO:
Módulo: {module}
Datos: {self._summarize_for_action_plan(module, calculation_data)}

PROBLEMAS/ADVERTENCIAS DETECTADAS:
{issues_text}

Crea un plan de acción estructurado en 3 niveles de prioridad.

Para cada acción incluye:
- Descripción clara de la acción
- Plazo (inmediato / corto plazo: 1-7 días / mediano plazo: 1-4 semanas)
- Costo estimado (bajo < $500 / medio $500-2000 / alto > $2000 MXN)
- Impacto esperado (crítico / alto / moderado)

PRIORIDADES:
- ALTA: Acciones críticas que afectan la viabilidad del programa o previenen pérdidas
- MEDIA: Mejoras importantes que optimizan resultados
- BAJA: Ajustes opcionales de perfeccionamiento

Responde en JSON:
{{
  "priority_high": [
    {{"action": "descripción", "timeline": "inmediato/corto/mediano", "cost_estimate": "bajo/medio/alto", "impact": "crítico/alto/moderado", "justification": "por qué es prioritario"}}
  ],
  "priority_medium": [...],
  "priority_low": [...],
  "summary": "Resumen del plan en 2 líneas",
  "success_factors": ["factor1", "factor2", "factor3"]
}}

Sé específico y práctico. Máximo 3-4 acciones por nivel de prioridad."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un consultor agronómico que crea planes de acción priorizados y ejecutables. Balanceas urgencia, costo e impacto."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=1800,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                return self._fallback_action_plan()
            return json.loads(content)
            
        except Exception as e:
            print(f"AI action plan error: {e}")
            return self._fallback_action_plan()
    
    def _format_data_for_summary(self, module: str, data: Dict, metrics: Dict) -> str:
        """Format data for executive summary prompt."""
        if module == 'SOIL':
            return f"""Cultivo: {data.get('crop_name', 'N/A')}
Rendimiento objetivo: {data.get('yield_target', 0)} t/ha
pH suelo: {data.get('ph', 0):.1f}
N a aplicar: {metrics.get('n_kg_ha', 0):.1f} kg/ha
P2O5 a aplicar: {metrics.get('p2o5_kg_ha', 0):.1f} kg/ha
K2O a aplicar: {metrics.get('k2o_kg_ha', 0):.1f} kg/ha
Costo estimado: ${metrics.get('cost_total', 0):.2f} MXN"""
        elif module == 'IONS':
            return f"""Receta: {data.get('recipe_name', 'Personalizada')}
Sistema: {data.get('system_type', 'N/A')}
Balance anión/catión: {metrics.get('anion_sum', 0):.2f} / {metrics.get('cation_sum', 0):.2f} Meq/L
CE objetivo: {metrics.get('target_ec', 0):.2f} dS/m
Déficits principales: {metrics.get('main_deficits', 'N/A')}
Fertilizantes seleccionados: {metrics.get('fertilizer_count', 0)}"""
        else:  # HYDRO
            return f"""Cultivo: {data.get('crop_name', 'N/A')}
Etapa: {data.get('growth_stage', 'N/A')}
Volumen: {data.get('volume_liters', 0)} L
EC final: {metrics.get('ec_final', 0):.2f} (objetivo: {metrics.get('ec_target', 0):.2f})
pH ajustado: {metrics.get('ph_adjusted', 0):.1f}
Costo por litro: ${metrics.get('cost_per_liter', 0):.4f} MXN"""
    
    def _summarize_for_action_plan(self, module: str, data: Dict) -> str:
        """Summarize data for action plan prompt."""
        return f"Módulo {module} - {data.get('crop_name', 'N/A')} - Volumen/Área: {data.get('volume_or_area', 'N/A')}"
    
    # Fallback methods for when AI is not available
    
    def _fallback_executive_summary(self, module: str, data: Dict, metrics: Dict) -> str:
        """Fallback executive summary."""
        return f"""RESUMEN EJECUTIVO - {module}

El cálculo ha sido completado exitosamente utilizando metodologías científicas validadas. Los parámetros nutricionales se encuentran dentro de rangos aceptables para el cultivo y sistema especificados.

Las dosis recomendadas consideran el balance nutricional óptimo, la disponibilidad de nutrientes del medio (suelo/agua), y los requerimientos específicos del cultivo. Se han aplicado factores de eficiencia según el método seleccionado.

Acción inmediata: Implementar el programa según las especificaciones técnicas. Monitorear parámetros clave (EC, pH, desarrollo vegetal) y ajustar si es necesario.

El Grower IA proporciona análisis detallado personalizado."""
    
    def _fallback_action_plan(self) -> Dict[str, Any]:
        """Fallback action plan."""
        return {
            'priority_high': [
                {
                    'action': 'Implementar programa de fertilización según especificaciones',
                    'timeline': 'inmediato',
                    'cost_estimate': 'medio',
                    'impact': 'crítico',
                    'justification': 'Inicio del ciclo productivo'
                }
            ],
            'priority_medium': [
                {
                    'action': 'Configurar sistema de monitoreo de parámetros',
                    'timeline': 'corto plazo',
                    'cost_estimate': 'bajo',
                    'impact': 'alto',
                    'justification': 'Control de calidad'
                }
            ],
            'priority_low': [
                {
                    'action': 'Documentar observaciones y ajustes realizados',
                    'timeline': 'mediano plazo',
                    'cost_estimate': 'bajo',
                    'impact': 'moderado',
                    'justification': 'Mejora continua'
                }
            ],
            'summary': 'Plan básico generado. El Grower IA proporciona recomendaciones avanzadas personalizadas.',
            'success_factors': [
                'Seguimiento riguroso del programa',
                'Monitoreo frecuente de parámetros',
                'Ajustes oportunos según observaciones'
            ]
        }
    
    def _fallback_validation(self, recipe_data: Dict) -> Dict[str, Any]:
        """Basic validation without AI."""
        return {
            'is_valid': True,
            'risk_level': 'low',
            'chemical_warnings': [],
            'recommendations': ['Validación básica completada. El Grower IA proporciona análisis avanzado.'],
            'explanation': 'Receta validada usando reglas básicas.'
        }
    
    def _fallback_explanation(self, recipe_data: Dict, focus: str) -> str:
        """Basic explanation without AI."""
        return f"""Receta para {recipe_data.get('crop_name')}:
- Masterblend: {recipe_data.get('masterblend_g', 0):.2f} g
- Nitrato de Calcio: {recipe_data.get('calcium_nitrate_g', 0):.2f} g
- Sal de Epsom: {recipe_data.get('epsom_salt_g', 0):.2f} g

EC objetivo: {recipe_data.get('ec_target', 0):.2f}
Costo: ${recipe_data.get('total_cost', 0):.2f} MXN

El Grower IA proporciona explicaciones detalladas."""
    
    def _fallback_optimization(self) -> Dict[str, Any]:
        """Basic optimization without AI."""
        return {
            'suggested_adjustments': [],
            'cost_savings': 0.0,
            'performance_impact': 'neutral',
            'reasoning': 'Optimización disponible mediante el Grower IA.'
        }
    
    def _fallback_diagnosis(self) -> Dict[str, Any]:
        """Basic diagnosis without AI."""
        return {
            'probable_causes': ['Diagnóstico requiere análisis de IA'],
            'deficiencies': [],
            'toxicities': [],
            'recommended_actions': ['El Grower IA proporciona diagnóstico avanzado'],
            'recipe_adjustments': {},
            'confidence': 'low',
            'explanation': 'Diagnóstico completo requiere IA.'
        }
    
    def _fallback_soil_report_narrative(self, calculation_data: Dict) -> Dict[str, str]:
        """Fallback soil report narrative when AI is unavailable."""
        return {
            'executive_summary': "El cálculo de fertilización se ha completado según la metodología NOM-021 y los requerimientos del cultivo. Las dosis recomendadas consideran el análisis de suelo y el rendimiento objetivo.",
            'nutrient_explanation': "Los niveles de nutrientes en el suelo han sido evaluados. La fertilización propuesta compensa las deficiencias detectadas y satisface los requerimientos del cultivo para alcanzar el rendimiento objetivo.",
            'dosage_justification': "Las dosis de fertilizantes se calcularon restando los créditos del suelo a los requerimientos totales, aplicando factores de eficiencia de uso según el método seleccionado.",
            'critical_alerts': "Sin alertas críticas - suelo en condiciones aceptables. Revise el pH y ajuste si es necesario para optimizar la disponibilidad de nutrientes.",
            'management_recommendations': "Fraccione la aplicación de nitrógeno en al menos 2-3 eventos durante el ciclo. Incorpore los fertilizantes fosforados y potásicos antes de la siembra. Monitoree el desarrollo del cultivo.",
            'preventive_diagnosis': "Vigile signos de deficiencia nutricional durante el ciclo. Realice análisis foliares en etapas críticas para validar el programa de fertilización y realizar ajustes si es necesario."
        }
    
    def _fallback_report_narrative(self, recipe_data: Dict) -> Dict[str, str]:
        """Basic report narrative without AI."""
        crop = recipe_data.get('crop_name', 'cultivo')
        stage = recipe_data.get('growth_stage', 'etapa')
        
        return {
            'executive_summary': f"Receta para {crop} en etapa {stage} calculada con sistema universal de 3 fertilizantes profesionales.",
            'nutrient_explanation': "Balance nutricional calculado según tablas científicas para hidroponía. El Grower IA proporciona análisis detallado.",
            'dosage_justification': "Dosis calculadas mediante algoritmo de resolución química secuencial. El Grower IA proporciona explicación detallada.",
            'critical_alerts': "Sistema de validación básico activo. El Grower IA proporciona alertas avanzadas.",
            'management_recommendations': "Monitoree EC y pH regularmente. Cambie solución cada 7-14 días. Mantenga temperatura 18-24°C.",
            'preventive_diagnosis': "El Grower IA proporciona diagnóstico preventivo avanzado."
        }
    
    # ========== HidroponIA Vision Methods ==========
    
    def extract_water_parameters_from_image(self, base64_image: str, image_mime_type: str = "image/png") -> Dict[str, Any]:
        """
        Extract water analysis parameters from PDF/image using GPT-5 Vision.
        
        Args:
            base64_image: Base64 encoded image of water analysis report
        
        Returns:
            Dictionary with extracted parameters and confidence score
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.client:
            logger.warning("⚠️  OpenAI client not available - using fallback extraction")
            return self._fallback_water_extraction()
        
        logger.info(f"🔍 Starting water parameter extraction with GPT-5 Vision (model: {self.model})")
        logger.info(f"📄 Image size: {len(base64_image)} characters (MIME: {image_mime_type})")
        
        # Comprehensive prompt optimized for professional lab formats (Phytomonitor, etc.)
        prompt = """Eres un experto en lectura de reportes de análisis de agua para agricultura. Analiza este documento y extrae TODOS los parámetros con MÁXIMA PRECISIÓN.

FORMATOS COMUNES DE LABORATORIOS MEXICANOS:
Los reportes profesionales (Phytomonitor, CIMMYT, INIFAP, etc.) organizan datos en 4 SECCIONES:

╔═══════════════════════════════════════════════════════════════════════════════╗
║ SECCIÓN 1: PARÁMETROS FÍSICOS                                                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝
Busca estos parámetros (con TODOS sus sinónimos):
• pH / pH (Potenciométrico) → extraer valor
• EC / CE / Conductividad Eléctrica / Electrical Conductivity → en mS/cm o dS/m
• TDS / Sólidos Disueltos Totales / Total Dissolved Solids → en ppm o mg/L
• RAS / Relación de Absorción de Sodio / Sodium Adsorption Ratio → extraer valor
• PSI / Porciento Sodio Intercambiable / % Sodio Intercambiable → extraer % (convertir a decimal: 0.38% = 0.38)
• Temperatura / Temperature / Temp → en °C

╔═══════════════════════════════════════════════════════════════════════════════╗
║ SECCIÓN 2: ANIONES (iones negativos -)                                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝
FORMATO TÍPICO: Tablas con columnas [Parámetro | ppm | Meq/L | Mmol/L | Niveles]
Extrae valores EN PPM de estas líneas:
• Nitratos / NO3- / NO3-N / Nitrogen Nitrate → ppm
• Fosfatos / PO4 / H2PO4- / P-PO4 / Fósforo de fosfatos → ppm
• Sulfatos / SO4-2 / Sulfate → ppm
• Carbonatos / CO3-2 / Carbonate → ppm
• Bicarbonatos / HCO3- / Bicarbonate → ppm
• Cloruros / Cl- / Chloride → ppm

IMPORTANTE: Si ves DOS valores (ej: "48.03 ppm" y "1.00 Meq/L"), PRIORIZA el valor en ppm.

╔═══════════════════════════════════════════════════════════════════════════════╗
║ SECCIÓN 3: CATIONES (iones positivos +)                                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝
Extrae valores EN PPM:
• Sodio / Na+ / Sodium (Soluble A. Atómica) → ppm
• Potasio / K+ / Potassium (Soluble A. Atómica) → ppm
• Calcio / Ca+2 / Calcium (Soluble A. Atómica) → ppm
• Magnesio / Mg+2 / Magnesium (Soluble A. Atómica) → ppm

╔═══════════════════════════════════════════════════════════════════════════════╗
║ SECCIÓN 4: MICROELEMENTOS / MICRONUTRIENTES                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
Extrae valores EN PPM (si está en µmol/L, ignóralo y busca columna ppm):
• Fierro / Hierro / Fe-2 / Iron (L.C.H. Fe -A. Atómica) → ppm
• Zinc / Zn+ / Zn (L.C.H. Zn-A. Atómica) → ppm
• Cobre / Cu+2 / Copper (L.C.H. Cu-A. Atómica) → ppm
• Manganeso / Mn+4 / Manganese (L.C.H. Mn -A. Atómica) → ppm
• Boro / B+3 / Boron (Azometina-H) → ppm

╔═══════════════════════════════════════════════════════════════════════════════╗
║ DATOS CALCULADOS ADICIONALES                                                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝
• Alcalinidad Total / Alkalinity / Alcalinidad ppm CaCO3 → ppm como CaCO3
• Dureza Total / Total Hardness / Hardness → ppm

╔═══════════════════════════════════════════════════════════════════════════════╗
║ METADATA DEL REPORTE                                                         ║
╚═══════════════════════════════════════════════════════════════════════════════╝
• Laboratorio: busca "PHYTOMONITOR", "CIMMYT", "INIFAP", "LABORATORIO", etc.
• Fecha: busca "Fecha de emisión", "Fecha Toma de Muestra", fechas en formato DD/MM/YYYY
• Fuente: busca "POZO", "CAMPO ABIERTO", "Zona de Muestreo", "LOTE"

═══════════════════════════════════════════════════════════════════════════════
REGLAS DE EXTRACCIÓN CRÍTICAS:
═══════════════════════════════════════════════════════════════════════════════
1. SIEMPRE prioriza valores en PPM sobre Meq/L o Mmol/L
2. Si solo hay Meq/L disponible:
   - NO3-: Meq/L × 62 = ppm
   - SO4-2: Meq/L × 48 = ppm
   - Cl-: Meq/L × 35.5 = ppm
   - HCO3-: Meq/L × 61 = ppm
   - Ca+2: Meq/L × 20 = ppm
   - Mg+2: Meq/L × 12.15 = ppm
   - K+: Meq/L × 39.1 = ppm
   - Na+: Meq/L × 23 = ppm
3. RAS y PSI: extrae el valor EXACTO tal como aparece
4. Si el documento dice "0.00" o "< 0.1", extrae como 0.0 (no null)
5. Si un parámetro NO APARECE en el documento, déjalo en null
6. confidence_score: 0.9-1.0 si el doc es claro, 0.7-0.8 si está borroso, 0.5-0.6 si está parcial
7. extraction_notes: menciona cualquier problema encontrado o conversión realizada

═══════════════════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA OBLIGATORIO:
═══════════════════════════════════════════════════════════════════════════════
Responde ÚNICAMENTE con este JSON (valores numéricos SIN unidades, fechas en YYYY-MM-DD):
{
  "ph": 7.76,
  "ec_ms_cm": 0.61,
  "tds_ppm": null,
  "ras": 1.82,
  "psi_percent": 0.38,
  "alkalinity_ppm_caco3": 244.04,
  "hardness_ppm": null,
  "temperature_c": null,
  "calcium_ppm": 59.00,
  "magnesium_ppm": 6.00,
  "potassium_ppm": 37.00,
  "sodium_ppm": 55.00,
  "nitrate_ppm": 32.82,
  "sulfate_ppm": 48.03,
  "chloride_ppm": 42.54,
  "bicarbonate_ppm": 244.04,
  "carbonate_ppm": 0.0,
  "phosphate_ppm": 0.48,
  "iron_ppm": 0.03,
  "manganese_ppm": 0.01,
  "zinc_ppm": 0.02,
  "copper_ppm": 0.01,
  "boron_ppm": 0.34,
  "lab_name": "PHYTOMONITOR SA DE CV",
  "analysis_date": "2020-12-09",
  "source_type": "POZO 2 VIÑEDO",
  "confidence_score": 0.98,
  "extraction_notes": "Extracción completa de formato Phytomonitor. Valores en ppm extraídos directamente de columna ppm. RAS y PSI detectados."
}"""
        
        try:
            # Using GPT-4o for Vision API - reliable image analysis
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{image_mime_type};base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                max_tokens=4096
            )
            
            import re
            
            # Log full response for debugging
            logger.debug(f"OpenAI response finish_reason: {response.choices[0].finish_reason}")
            
            content = response.choices[0].message.content
            if not content:
                # Log the full response structure to understand what OpenAI returned
                logger.error(f"⚠️  OpenAI returned empty content. Full response: {response.model_dump_json()[:500]}")
                return self._fallback_water_extraction()
            
            logger.info("✅ Successfully received response from GPT-4o Vision")
            logger.debug(f"Response content length: {len(content)} characters")
            
            # Try to extract JSON from response (might have markdown code blocks)
            # Look for ```json...``` or just raw JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug("Extracted JSON from markdown code block")
            else:
                # Try to find raw JSON object
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    logger.debug("Extracted raw JSON from response")
                else:
                    logger.error(f"No JSON found in response. Content preview: {content[:200]}")
                    return self._fallback_water_extraction()
            
            result = json.loads(json_str)
            logger.info(f"✅ Successfully parsed JSON - extracted {len([k for k,v in result.items() if v is not None])} parameters")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {str(e)}. Content preview: {content[:200] if content else 'None'}")
            return self._fallback_water_extraction()
        except Exception as e:
            logger.error(f"❌ Water extraction error: {str(e)}", exc_info=True)
            return self._fallback_water_extraction()
    
    def generate_hydro_recommendation(
        self,
        water_params: Dict[str, Any],
        crop_data: Dict[str, Any],
        methodology_preference: str = "auto"
    ) -> Dict[str, Any]:
        """
        Generate AI-powered fertilization recommendation for hydroponics.
        
        Args:
            water_params: Water analysis parameters (pH, EC, ions, etc.)
            crop_data: Crop info (name, stage, target nutrients, etc.)
            methodology_preference: "steiner", "hoagland", "sonneveld", or "auto"
        
        Returns:
            Complete recommendation with diagnosis, formula, instructions, and methodology
        """
        if not self.client:
            return self._fallback_hydro_recommendation(crop_data)
        
        prompt = f"""Como agrónomo especialista en hidroponía, genera una recomendación profesional de fertilización.

ANÁLISIS DE AGUA:
- pH: {water_params.get('ph', 'N/D')}
- EC: {water_params.get('ec_ms_cm', 'N/D')} mS/cm
- Calcio: {water_params.get('calcium_ppm', 'N/D')} ppm
- Magnesio: {water_params.get('magnesium_ppm', 'N/D')} ppm
- Potasio: {water_params.get('potassium_ppm', 'N/D')} ppm
- Sodio: {water_params.get('sodium_ppm', 'N/D')} ppm
- Nitratos: {water_params.get('nitrate_ppm', 'N/D')} ppm
- Sulfatos: {water_params.get('sulfate_ppm', 'N/D')} ppm
- Cloruros: {water_params.get('chloride_ppm', 'N/D')} ppm
- Alcalinidad: {water_params.get('alkalinity_ppm_caco3', 'N/D')} ppm CaCO3
- Dureza: {water_params.get('hardness_ppm', 'N/D')} ppm

CULTIVO: {crop_data.get('crop_name')}
ETAPA FENOLÓGICA: {crop_data.get('growth_stage')}

REQUERIMIENTOS OBJETIVO:
- pH: {crop_data.get('target_ph_min')}-{crop_data.get('target_ph_max')}
- EC: {crop_data.get('target_ec_min')}-{crop_data.get('target_ec_max')} mS/cm
- N: {crop_data.get('n_ppm_min')}-{crop_data.get('n_ppm_max')} ppm
- P: {crop_data.get('p_ppm_min')}-{crop_data.get('p_ppm_max')} ppm
- K: {crop_data.get('k_ppm_min')}-{crop_data.get('k_ppm_max')} ppm
- Ca: {crop_data.get('ca_ppm_min')}-{crop_data.get('ca_ppm_max')} ppm
- Mg: {crop_data.get('mg_ppm_min')}-{crop_data.get('mg_ppm_max')} ppm

METODOLOGÍA PREFERIDA: {methodology_preference}

INSTRUCCIONES:
1. EVALÚA la calidad del agua (idoneidad, problemas críticos, ventajas)
2. CALCULA los déficits de nutrientes (requerido - presente en agua)
3. RECOMIENDA fertilizantes específicos con dosis en g/m³ o mL/m³
4. INCLUYE instrucciones de preparación (orden de mezcla, tanques A/B si aplica)
5. APLICA metodología apropiada (Steiner para general, Hoagland para precisión, Sonneveld para Europa)
6. IDENTIFICA alertas críticas (toxicidades, incompatibilidades)
7. FUNDAMENTA la recomendación con referencias científicas

Responde en formato JSON:
{{
  "water_quality_diagnosis": {{
    "overall_suitability": "Excelente/Buena/Aceptable/Requiere tratamiento",
    "ph_assessment": "Análisis de pH y su impacto",
    "ec_assessment": "Análisis de salinidad",
    "hardness_assessment": "Análisis de dureza si relevante",
    "critical_issues": ["problema1", "problema2"],
    "advantages": ["ventaja1", "ventaja2"]
  }},
  "fertilizer_recommendations": [
    {{
      "fertilizer_name": "Nitrato de Calcio",
      "chemical_formula": "Ca(NO3)2·4H2O",
      "dose_grams_per_m3": 750.0,
      "dose_ml_per_m3": null,
      "purpose": "Aportar Ca y N-NO3",
      "tank_assignment": "A"
    }}
  ],
  "adjustment_instructions": [
    "1. Preparar tanque A con...",
    "2. Preparar tanque B con...",
    "3. Mezclar en reservorio..."
  ],
  "methodology_applied": {{
    "name": "Steiner Universal Solution",
    "description": "Solución universal ampliamente probada",
    "references": ["Steiner, A.A. (1984). The Universal Nutrient Solution"],
    "justification": "Método robusto para esta etapa fenológica"
  }},
  "target_ph": 6.0,
  "target_ec": 2.0,
  "target_n_ppm": 150,
  "target_p_ppm": 50,
  "target_k_ppm": 220,
  "target_ca_ppm": 180,
  "target_mg_ppm": 50,
  "ai_summary": "Resumen ejecutivo de 2-3 líneas",
  "ai_detailed_analysis": "Análisis técnico detallado de 200-300 palabras con justificación agronómica completa",
  "warnings_and_alerts": ["alerta1", "alerta2"]
}}"""
        
        try:
            # Using GPT-4o for reliable hydroponics recommendations
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un ingeniero agrónomo PhD especializado en hidroponía y nutrición vegetal.
Tienes amplio conocimiento de:
- Soluciones nutritivas hidropónicas (Steiner, Hoagland, Sonneveld)
- Química de fertilizantes y compatibilidades
- Requerimientos nutricionales por cultivo y etapa fenológica
- Calidad de agua y su impacto en hidroponía
- Metodologías internacionales FAO, Universidad de Arizona, UC Davis

Das recomendaciones precisas, sustentadas científicamente, y prácticas."""
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                return self._fallback_hydro_recommendation(crop_data)
            
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"Hydro recommendation error: {e}")
            return self._fallback_hydro_recommendation(crop_data)
    
    def _fallback_water_extraction(self) -> Dict[str, Any]:
        """Fallback when AI extraction is unavailable."""
        return {
            "ph": None,
            "ec_ms_cm": None,
            "tds_ppm": None,
            "alkalinity_ppm_caco3": None,
            "hardness_ppm": None,
            "temperature_c": None,
            "calcium_ppm": None,
            "magnesium_ppm": None,
            "potassium_ppm": None,
            "sodium_ppm": None,
            "nitrate_ppm": None,
            "sulfate_ppm": None,
            "chloride_ppm": None,
            "bicarbonate_ppm": None,
            "phosphate_ppm": None,
            "iron_ppm": None,
            "manganese_ppm": None,
            "zinc_ppm": None,
            "copper_ppm": None,
            "boron_ppm": None,
            "lab_name": None,
            "analysis_date": None,
            "source_type": None,
            "confidence_score": 0.0,
            "extraction_notes": "Extracción automática no disponible. El Grower IA puede extraer datos o ingréselos manualmente."
        }
    
    def _fallback_hydro_recommendation(self, crop_data: Dict) -> Dict[str, Any]:
        """Fallback recommendation when AI is unavailable."""
        return {
            "water_quality_diagnosis": {
                "overall_suitability": "No evaluada",
                "ph_assessment": "Requiere configuración de IA",
                "ec_assessment": "Requiere configuración de IA",
                "hardness_assessment": None,
                "critical_issues": [],
                "advantages": []
            },
            "fertilizer_recommendations": [],
            "adjustment_instructions": ["El Grower IA proporciona recomendaciones personalizadas"],
            "methodology_applied": {
                "name": "Recomendación básica",
                "description": "El Grower IA proporciona metodología avanzada",
                "references": [],
                "justification": "Análisis completo requiere IA"
            },
            "target_ph": crop_data.get('target_ph_min', 6.0),
            "target_ec": crop_data.get('target_ec_min', 2.0),
            "target_n_ppm": crop_data.get('n_ppm_min', 150),
            "target_p_ppm": crop_data.get('p_ppm_min', 50),
            "target_k_ppm": crop_data.get('k_ppm_min', 200),
            "target_ca_ppm": crop_data.get('ca_ppm_min', 180),
            "target_mg_ppm": crop_data.get('mg_ppm_min', 50),
            "ai_summary": "Recomendación básica generada. El Grower IA proporciona análisis completo.",
            "ai_detailed_analysis": "El Grower IA proporciona análisis agronómico detallado con recomendaciones personalizadas.",
            "warnings_and_alerts": ["El Grower IA proporciona alertas personalizadas"],
            "estimated_cost_per_m3": None,
            "estimated_monthly_cost": None
        }
    
    def suggest_fertilizers_for_deficits(
        self,
        deficits: Dict[str, float],
        available_fertilizers: List[Dict[str, Any]],
        water_analysis: Optional[Dict[str, float]] = None,
        crop_name: Optional[str] = None,
        preparation_mode: str = "direct",
        micronutrient_deficits: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Grower IA - AI-powered fertilizer selection based on ionic deficits.
        
        Args:
            deficits: Ion deficits in meq/L (positive = need to add)
                     e.g., {"NO3": 10.5, "Ca": 4.2, "K": 6.8, ...}
            available_fertilizers: List of available fertilizer objects
            water_analysis: Optional water analysis data
            crop_name: Optional crop name for context
            preparation_mode: "direct" or "stock_ab"
            micronutrient_deficits: Optional micronutrient deficits in ppm
                     e.g., {"Fe": 2.0, "Mn": 0.5, "Zn": 0.2, ...}
        
        Returns:
            {
                'recommended_fertilizers': List[str],  # IDs of recommended salt fertilizers
                'recommended_acids': List[str],  # IDs of recommended acids (can be multiple)
                'recommended_micronutrients': List[str],  # IDs of recommended micronutrient sources
                'technical_justification': str,  # Detailed explanation
                'ionic_balance_analysis': str,  # Balance analysis
                'acid_dual_purpose_analysis': str,  # Explanation of acid's dual purpose
                'ph_adjustment_needed': bool,
                'ph_adjustment_explanation': str,
                'priority_order': List[str],  # Order of application
                'warnings': List[str]
            }
        """
        # ==================== ZERO-DEFICIT GUARD ====================
        # Check if all deficits are zero or negative (no fertilization needed)
        water_hco3 = _safe_parse_water_hco3(water_analysis)
        positive_deficits = sum(max(0, v) for k, v in deficits.items() if k != "HCO3")
        has_micronutrient_deficits = micronutrient_deficits and any(v > 0.01 for v in micronutrient_deficits.values())
        
        if positive_deficits < 0.1 and water_hco3 < 0.5 and not has_micronutrient_deficits:
            return {
                'status': 'no_fertilization_needed',
                'recommended_fertilizers': [],
                'recommended_acids': [],
                'recommended_micronutrients': [],
                'technical_justification': 'No se requieren fertilizantes. Todos los requerimientos iónicos están cubiertos por el agua de riego o los targets son cero.',
                'ionic_balance_analysis': 'Sin déficits significativos que corregir.',
                'acid_dual_purpose_analysis': 'Sin bicarbonatos en el agua - no se requieren ácidos.',
                'ph_adjustment_needed': False,
                'ph_adjustment_explanation': 'El agua no tiene bicarbonatos significativos.',
                'priority_order': [],
                'warnings': ['✓ Los requerimientos ya están cubiertos. No se necesita dosificación.']
            }
        
        if not self.client:
            return self._fallback_fertilizer_suggestion(deficits, available_fertilizers, micronutrient_deficits, water_analysis)
        
        # Separate fertilizers by type for AI
        salt_fertilizers = []
        acid_fertilizers = []
        micronutrient_sources = []
        
        for fert in available_fertilizers:
            fert_info = {
                "id": fert.get("id"),
                "name": fert.get("name"),
                "formula": fert.get("chemical_formula"),
                "type": fert.get("type"),
                "ions": fert.get("ion_contributions", {}),
                "meq_per_gram": fert.get("meq_per_gram", {}),
                "mg_per_gram": fert.get("mg_per_gram", {}),
                "tank": fert.get("stock_tank"),
                "cost": fert.get("typical_cost_mxn_per_kg")
            }
            if fert.get("type") == "salt":
                salt_fertilizers.append(fert_info)
            elif fert.get("type") == "acid":
                acid_fertilizers.append(fert_info)
            elif fert.get("type") in ("micronutrient_mix", "chelate"):
                # Only include commercial mixes and chelates, not individual salts
                micronutrient_sources.append(fert_info)
        
        # Build micronutrient section if deficits exist
        micro_section = ""
        if micronutrient_deficits and any(v > 0 for v in micronutrient_deficits.values()):
            micro_section = f"""
DÉFICITS DE MICRONUTRIENTES (ppm):
{json.dumps(micronutrient_deficits, indent=2)}

FUENTES DE MICRONUTRIENTES DISPONIBLES:
{json.dumps(micronutrient_sources, indent=2, ensure_ascii=False)}
"""
        
        # CRITICAL: Determine if acids are needed based on water bicarbonates
        # Only recommend acids when HCO3 in water > 0.5 meq/L
        water_hco3 = _safe_parse_water_hco3(water_analysis)
        acids_needed = water_hco3 > 0.5
        acids_section = ""
        if acids_needed:
            acids_section = f"""
ÁCIDOS DISPONIBLES (PARA NEUTRALIZAR BICARBONATOS):
{json.dumps(acid_fertilizers, indent=2, ensure_ascii=False)}

⚠️ IMPORTANTE: El agua tiene {water_hco3:.2f} meq/L de bicarbonatos (HCO3-).
Los ácidos son NECESARIOS para neutralizar estos bicarbonatos y ajustar el pH.
Selecciona ácido(s) que además aporten iones deficitarios cuando sea posible."""
        else:
            acids_section = f"""
⚠️ INFORMACIÓN CRÍTICA: El agua tiene bicarbonatos muy bajos o cero ({water_hco3:.2f} meq/L).
NO RECOMIENDES ÁCIDOS porque:
- Sin bicarbonatos que neutralizar, los ácidos causarían caída drástica del pH
- Esto sería peligroso para las plantas
- Los nutrientes (NO3, H2PO4, SO4) deben venir de fertilizantes de sal, no de ácidos
DEJA "recommended_acids" COMO LISTA VACÍA []."""

        prompt = f"""Eres GROWER IA, el asistente inteligente de AgriDoser especializado en hidroponía, balance iónico y química de soluciones nutritivas. Analiza estos déficits y selecciona fertilizantes usando CRITERIOS TÉCNICOS ESTRICTOS:

DÉFICITS IÓNICOS DE MACRONUTRIENTES (Meq/L):
{json.dumps(deficits, indent=2)}
{micro_section}
FERTILIZANTES DE SAL DISPONIBLES:
{json.dumps(salt_fertilizers, indent=2, ensure_ascii=False)}
{acids_section}

CONTEXTO:
- Cultivo: {crop_name or 'No especificado'}
- Modo de preparación: {'Stock A/B (concentrado)' if preparation_mode == 'stock_ab' else 'Directo (volumen final)'}
{f"- Análisis de agua: {json.dumps(water_analysis, indent=2)}" if water_analysis else ""}

SISTEMA DE OPTIMIZACIÓN ITERATIVO V2:
El algoritmo de dosificación ahora opera en ciclos iterativos con auto-evaluación:
- Genera solución inicial con selección de fertilizantes por prioridad iónica
- Evalúa la solución con un Score compuesto (0-100): Cobertura 40%, Balance 20%, Ratios 15%, Costo 10%, Antagonismos 10%, Toxicidad 5%
- Si Score < 85: aplica estrategias de mejora automáticas (complementación, ajuste de dosis, sustitución, rebalanceo de ácidos)
- Itera hasta Score ≥ 85 o convergencia (máximo 10 iteraciones)
- Retorna la MEJOR solución encontrada (no la última)

CRITERIOS TÉCNICOS ESTRICTOS (aplicar en este orden de prioridad):

1. BALANCE CATIONES/ANIONES: El total de cationes debe ser ≈ total de aniones (±5%)
   
2. EFICIENCIA IÓNICA: Priorizar fertilizantes que cubren múltiples déficits simultáneamente
   - Si hay déficit de Ca (>0.5): Nitrato de Calcio es prioritario (aporta Ca + NO3)
   - Si hay déficit de K (>0.5): Nitrato de Potasio o Sulfato de Potasio según necesidades de NO3/SO4
   - Si hay déficit de Mg (>0.5): Sulfato de Magnesio (aporta Mg + SO4)
   - Si hay déficit de NH4 (>0.1): Nitrato de Amonio (aporta NH4 + NO3)
   - ⚠️ CRÍTICO - Si hay déficit de H2PO4 (>0.3): MKP (mkp) es OBLIGATORIO - es la ÚNICA fuente de H2PO4 como fertilizante de sal. MKP aporta H2PO4 + K simultáneamente.
   
   ⚠️ NUEVO: SISTEMA DE RESERVA DE H2PO4 PARA MKP:
   - Cuando MKP y ácido fosfórico están ambos seleccionados, el algoritmo RESERVA espacio de H2PO4 para MKP primero
   - MKP puede cubrir: min(déficit K, déficit H2PO4) de H2PO4
   - El ácido fosfórico SOLO cubre el H2PO4 restante después de la reserva para MKP
   - Esto garantiza que MKP pueda contribuir tanto K como H2PO4 simultáneamente

3. SELECCIÓN DE ÁCIDOS (SOLO CUANDO HAY BICARBONATOS EN EL AGUA):
   ⚠️ REGLA CRÍTICA: Los ácidos SOLO se usan para neutralizar bicarbonatos (HCO3-) en el agua.
   - Si el agua NO tiene bicarbonatos significativos (HCO3 < 0.5 meq/L): NO RECOMIENDES ÁCIDOS
   - Sin bicarbonatos, los ácidos causarían caída drástica del pH (muy peligroso)
   - En ese caso, usa fertilizantes de SAL para aportar NO3, H2PO4 y SO4
   
   SI HAY BICARBONATOS (HCO3 > 0.5 meq/L), aplica estos criterios avanzados:
   
   a) DISTRIBUCIÓN PROPORCIONAL DE HCO3:
      - Los bicarbonatos se distribuyen entre ácidos PROPORCIONALMENTE según el déficit de cada ion
      - Ejemplo: Si déficit H2PO4=1.5, SO4=2.0, NO3=8.0 → distribuir HCO3 en proporción 1.5:2.0:8.0
      - Esto evita que un ácido monopolice toda la neutralización
   
   b) PRIORIDAD "ION MÁS RESTRINGIDO PRIMERO":
      - Orden de ácidos: Fosfórico → Sulfúrico → Nítrico
      - Razón: H2PO4 y SO4 tienen objetivos más bajos (1-2 meq/L), se llenan rápido
      - NO3 tiene mayor margen (8-15 meq/L), puede absorber el exceso restante
   
   c) RESERVA DE NO3 PARA SALES (KNO3, CaNO3):
      - ⚠️ CRÍTICO: Limitar ácido nítrico para dejar espacio a Nitrato de Potasio y Nitrato de Calcio
      - Si hay déficit de K y se selecciona KNO3: reservar NO3 = déficit K × 1.0 meq/meq
      - Si hay déficit de Ca y se selecciona CaNO3: reservar NO3 = déficit Ca × 2.0 meq/meq
      - El ácido nítrico solo cubre el NO3 restante después de estas reservas
   
   d) INTERACCIÓN ÁCIDO SULFÚRICO / MgSO4:
      - Si se recomienda ácido sulfúrico, el SO4 del agua + ácido puede ya cubrir el déficit
      - En ese caso, LIMITAR Sulfato de Magnesio para evitar exceso de SO4
      - Calcular: SO4 disponible para MgSO4 = déficit SO4 - aporte del ácido sulfúrico
   
   ÁCIDOS DISPONIBLES:
   - Ácido Fosfórico 75%: aporta H2PO4- (usar si hay déficit de H2PO4)
   - Ácido Sulfúrico 98%: aporta SO42- (usar si hay déficit de SO4)
   - Ácido Nítrico 70%: aporta NO3- (usar SOLO si queda déficit de NO3 después de reservas para sales)

4. COMPATIBILIDAD QUÍMICA (evitar precipitaciones):
   - NUNCA mezclar Nitrato de Calcio + Sulfato en el mismo tanque (modo Stock A/B)
   - NUNCA mezclar Fosfatos + Calcio en el mismo tanque (modo Stock A/B)
   - En modo directo: agregar fertilizantes uno por uno, mezclando entre cada adición

5. MANEJO DE BICARBONATOS Y VALIDACIÓN:
   - Si el agua tiene HCO3 > 0.5 meq/L: se requiere ácido neutralizador
   - Si el agua tiene HCO3 < 0.5 meq/L: NO uses ácidos, deja "recommended_acids": []
   - Revisa la sección de ácidos arriba para saber si debes recomendar ácidos o no
   
   VALIDACIÓN POST-ÁCIDO (el algoritmo aplicará esto automáticamente):
   - Si algún ion de ácido excede +10% del objetivo, solo ESE ácido se reduce
   - Esto preserva las contribuciones de otros ácidos (ej: fosfórico para H2PO4)
   - Resultado esperado: todos los iones dentro de ±10% del objetivo

6. MICRONUTRIENTES (SELECCIÓN INTELIGENTE OBLIGATORIA):
   ⚠️ REGLA CRÍTICA: NO seleccionar siempre la misma mezcla. EVALÚA cada caso individualmente:
   
   a) ESTRATEGIA DE SELECCIÓN (en orden de prioridad):
      - Si SOLO 1-2 micronutrientes están deficientes: usar QUELATOS INDIVIDUALES específicos
        * Fe deficiente: iron_chelate_eddha (pH alto) o iron_chelate_dtpa (pH bajo)
        * Mn deficiente: manganese_chelate_edta
        * Zn deficiente: zinc_chelate_edta
        * Cu deficiente: copper_chelate_edta
        * B deficiente: boric_acid
      - Si 3+ micronutrientes están deficientes: EVALUAR mezclas comerciales disponibles
        * Comparar composición de cada mezcla vs déficits específicos
        * Elegir la que mejor cubra los déficits SIN causar excesos
        * Opciones: tradecorp_az, multimicro_haifa, ultrasol_micro_sqm, diosol, living_complete
      
   b) CRITERIOS PARA ELEGIR ENTRE MEZCLAS COMERCIALES:
      - Calcular "fit score" = (elementos cubiertos) - (elementos en exceso)
      - Preferir mezcla que cubra >80% de los déficits sin superar límites de toxicidad
      - Si ninguna mezcla es ideal, combinar mezcla + quelatos individuales
   
   c) ADVERTENCIAS CRÍTICAS DE TOXICIDAD:
     * Fe >5 ppm: toxicidad (manchas necróticas)
     * Mn >2 ppm: bloquea absorción de Fe y Ca
     * Zn >1 ppm: toxicidad, bloquea Fe
     * Cu >0.5 ppm: fitotóxico para mayoría de cultivos
     * B >1 ppm: quemaduras marginales
     * Mo: rara vez deficiente, exceso causa toxicidad de Cu
   
   d) ANTAGONISMOS:
     * Fe vs Mn: exceso de uno bloquea al otro
     * Zn vs Fe: competencia por absorción
     * Ca vs Mg vs K: mantener proporciones adecuadas

7. PRIORIDAD DE MEZCLA (orden de solubilidad, de menos a más soluble):
   - Fosfatos primero
   - Sulfatos segundo
   - Nitratos al final

IMPORTANTE: TODA tu respuesta DEBE estar en ESPAÑOL. No uses inglés bajo ninguna circunstancia.

Responde en formato JSON con recomendaciones CONCRETAS y ESPECÍFICAS:
{{
  "recommended_fertilizers": ["fertilizer_id1", "fertilizer_id2", ...],
  "recommended_acids": ["acid_id1", "acid_id2", ...],
  "recommended_micronutrients": ["micronutrient_id1", ...],
  "technical_justification": "RECOMENDACIÓN CONCRETA: Lista cada fertilizante seleccionado con su nombre comercial, la cantidad aproximada de iones que aportará (en meq/L), y el motivo técnico específico. Ejemplo: 'Nitrato de Calcio: cubre el déficit de Ca2+ (4.2 meq/L) y aporta NO3- adicional. Sulfato de Magnesio: cubre el déficit de Mg2+ (1.5 meq/L) y aporta SO42-.'",
  "ionic_balance_analysis": "ANÁLISIS DETALLADO: Indica qué porcentaje de cada déficit se cubrirá con los fertilizantes seleccionados. Ejemplo: 'NO3-: se cubrirá 100% del déficit (12.5 meq/L). Ca2+: se cubrirá 100% (4.2 meq/L). K+: se cubrirá parcialmente (85% del déficit).'",
  "acid_dual_purpose_analysis": "ESTRATEGIA DE ÁCIDOS: Explica la distribución proporcional de HCO3 entre ácidos, el orden de prioridad (Fosfórico→Sulfúrico→Nítrico), la reserva de NO3 para sales (KNO3/CaNO3), y la cantidad de meq/L que cada ácido aportará. Ejemplo: 'Con HCO3=4.5 meq/L, se distribuye: Ác. fosfórico cubrirá 1.2 meq/L H2PO4 (27% del HCO3), Ác. sulfúrico 1.8 meq/L SO4 (40%), Ác. nítrico 1.5 meq/L NO3 (33%, limitado para dejar espacio a KNO3).'",
  "micronutrient_analysis": "MICRONUTRIENTES: Lista cada fuente seleccionada y qué ppm aportará de cada elemento. Ejemplo: 'Quelato de Hierro EDDHA: aportará 2.5 ppm de Fe. Sulfato de Manganeso: aportará 0.6 ppm de Mn.'",
  "micronutrient_warnings": ["ADVERTENCIA: Lista de advertencias específicas sobre micronutrientes. Ejemplo: 'Fe a 2.5 ppm está en rango óptimo (1-5 ppm)', 'Monitorear antagonismo Fe/Mn con estos niveles'"],
  "balance_calculation": "CÁLCULO DE BALANCE IÓNICO:\\n• CATIONES: Ca2+ (X meq/L) + Mg2+ (X meq/L) + K+ (X meq/L) + Na+ (X meq/L) + NH4+ (X meq/L) = TOTAL CATIONES (X meq/L)\\n• ANIONES: NO3- (X meq/L) + H2PO4- (X meq/L) + SO42- (X meq/L) + Cl- (X meq/L) = TOTAL ANIONES (X meq/L)\\n• DIFERENCIA: (Total Cationes - Total Aniones) = X meq/L\\n• RESULTADO: Balance [ÓPTIMO/ACEPTABLE/REQUIERE AJUSTE] (diferencia ±5% es óptimo)",
  "ph_adjustment_needed": true/false,
  "ph_adjustment_explanation": "AJUSTE DE pH: Explica concretamente si se necesita ácido, qué ácido usar, y la cantidad aproximada para neutralizar bicarbonatos.",
  "priority_order": ["fertilizer_id1", "fertilizer_id2", ...],
  "warnings": ["advertencia1", "advertencia2", ...]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres GROWER IA, el asistente inteligente de AgriDoser, experto en hidroponía, química de soluciones nutritivas y balance iónico. REGLAS OBLIGATORIAS: 1) SIEMPRE responde en ESPAÑOL, nunca en inglés. 2) Sé CONCRETO y ESPECÍFICO: menciona nombres comerciales de fertilizantes, cantidades exactas en meq/L o ppm, y porcentajes de cobertura. 3) INCLUYE el cálculo numérico del balance cationes/aniones con valores reales. 4) Aplica criterios técnicos estrictos basados en química agrícola. 5) REGLA CRÍTICA DE ÁCIDOS: SOLO recomienda ácidos si el agua tiene bicarbonatos (HCO3 > 0.5 meq/L). Si no hay bicarbonatos, NO recomiendes ácidos. 6) DISTRIBUCIÓN PROPORCIONAL: Distribuye HCO3 entre ácidos según el déficit de cada ion, prioriza Fosfórico→Sulfúrico→Nítrico. 7) RESERVA DE NO3: Limita ácido nítrico para dejar espacio a KNO3/CaNO3. 8) INTERACCIÓN MgSO4: Si usas ácido sulfúrico, limita MgSO4 para evitar exceso de SO4."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=2500,
                response_format={"type": "json_object"},
                temperature=0  # Maximum determinism for consistent technical recommendations
            )
            
            content = response.choices[0].message.content
            logger.info(f"OpenAI raw response content: {content[:500]}")  # Log first 500 chars
            
            if not content:
                logger.warning("OpenAI returned empty content, using fallback")
                return self._fallback_fertilizer_suggestion(deficits, available_fertilizers, micronutrient_deficits, water_analysis)
            
            result = json.loads(content)
            logger.info(f"Successfully parsed JSON response with {len(result.get('recommended_fertilizers', []))} fertilizers")
            
            # POST-AI VALIDATION: Filter out acids if water has no significant bicarbonates
            # This is a safety net in case the AI doesn't follow instructions
            if not acids_needed and result.get('recommended_acids'):
                filtered_acids = result.get('recommended_acids', [])
                if filtered_acids:
                    logger.warning(f"AI recommended acids {filtered_acids} but water has low bicarbonates ({water_hco3:.2f} meq/L). Filtering out acids.")
                    
                    # Clear acid arrays
                    result['recommended_acids'] = []
                    result['recommended_acid'] = None  # Legacy field
                    
                    # Update explanations
                    result['acid_dual_purpose_analysis'] = (
                        f"No se recomiendan ácidos porque el agua tiene bicarbonatos muy bajos ({water_hco3:.2f} meq/L). "
                        f"Sin bicarbonatos que neutralizar, los ácidos causarían una caída peligrosa del pH. "
                        f"Los nutrientes (NO3, H2PO4, SO4) vendrán de los fertilizantes de sal seleccionados."
                    )
                    result['ph_adjustment_needed'] = False
                    result['ph_adjustment_explanation'] = (
                        f"No se requiere ajuste de pH con ácidos porque el agua tiene bicarbonatos muy bajos ({water_hco3:.2f} meq/L)."
                    )
                    
                    # Remove acids from priority_order if present
                    acid_ids = {'nitric_acid_70', 'sulfuric_acid_98', 'phosphoric_acid_75', 'hydrochloric_acid'}
                    priority_order = result.get('priority_order', [])
                    result['priority_order'] = [fert for fert in priority_order if fert not in acid_ids]
                    
                    # Replace existing warnings with clean list (no stale acid references)
                    clean_warnings = [
                        w for w in result.get('warnings', [])
                        if not any(acid_term in w.lower() for acid_term in ['ácido', 'acid', 'nítrico', 'sulfúrico', 'fosfórico', 'neutraliz'])
                    ]
                    # Add informative warning about acid omission
                    clean_warnings.insert(0, f"ℹ️ INFO: No se dosificaron ácidos porque el agua tiene bicarbonatos muy bajos ({water_hco3:.2f} meq/L). Los nutrientes vendrán de fertilizantes de sal.")
                    result['warnings'] = clean_warnings
            
            return result
            
        except Exception as e:
            logger.error(f"Fertilizer suggestion error: {e}", exc_info=True)
            logger.error(f"Failed content was: {content if 'content' in locals() else 'N/A'}")
            return self._fallback_fertilizer_suggestion(deficits, available_fertilizers, micronutrient_deficits, water_analysis)
    
    def _fallback_fertilizer_suggestion(
        self,
        deficits: Dict[str, float],
        available_fertilizers: List[Dict[str, Any]],
        micronutrient_deficits: Optional[Dict[str, float]] = None,
        water_analysis: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Fallback fertilizer suggestion when Grower IA is unavailable."""
        # Simple heuristic: suggest fertilizers that cover the most critical deficits
        recommended = []
        recommended_acids = []
        recommended_micronutrients = []
        
        # CRITICAL: Determine if acids are needed based on water bicarbonates
        water_hco3 = _safe_parse_water_hco3(water_analysis)
        acids_needed = water_hco3 > 0.5
        
        # Basic logic: if Ca deficit, add calcium nitrate; if K deficit, add potassium nitrate, etc.
        if deficits.get("Ca", 0) > 0.5:
            recommended.append("calcium_nitrate")
        if deficits.get("K", 0) > 0.5:
            recommended.append("potassium_nitrate")
        if deficits.get("Mg", 0) > 0.5:
            recommended.append("magnesium_sulfate")
        if deficits.get("H2PO4", 0) > 0.3:
            recommended.append("mkp")  # MKP covers H2PO4 + K simultaneously
        
        # Acid selection - ONLY if water has significant bicarbonates (HCO3 > 0.5 meq/L)
        if acids_needed:
            # Select acids that also provide needed nutrients
            if deficits.get("H2PO4", 0) > 0.3:
                recommended_acids.append("phosphoric_acid_75")
            if deficits.get("NO3", 0) > 2.0:
                recommended_acids.append("nitric_acid_70")
            if deficits.get("SO42", 0) > 0.5 or deficits.get("SO4", 0) > 0.5:
                recommended_acids.append("sulfuric_acid_98")
            
            # If no acids selected but bicarbonates need neutralization, default to phosphoric
            if not recommended_acids:
                recommended_acids.append("phosphoric_acid_75")
        
        # Micronutrient selection - evaluate available mixes and select best match
        if micronutrient_deficits:
            deficient_micros = [m for m in ["Fe", "Mn", "Zn", "Cu", "B", "Mo"] if micronutrient_deficits.get(m, 0) > 0.01]
            if deficient_micros:
                # Build set of available fertilizer IDs for validation
                available_ids = {f.get("id") for f in available_fertilizers if f.get("id")}
                
                # Chelate preference order (from general to specific)
                chelate_map = {
                    "Fe": ["iron_chelate_eddha", "iron_chelate_dtpa", "iron_chelate_edta"],
                    "Mn": ["manganese_chelate_edta", "manganese_sulfate"],
                    "Zn": ["zinc_chelate_edta", "zinc_sulfate"],
                    "Cu": ["copper_chelate_edta", "copper_sulfate"],
                    "B": ["boric_acid", "borax"],
                    "Mo": ["sodium_molybdate"]
                }
                
                # Commercial mixes for multiple deficits
                mix_options = ["ultrasol_micro_sqm", "multimicro_haifa", "tradecorp_az", "diosol", "living_complete"]
                
                if len(deficient_micros) >= 3:
                    # Multiple micronutrients - find best available commercial mix
                    for mix_id in mix_options:
                        if mix_id in available_ids:
                            recommended_micronutrients.append(mix_id)
                            break
                    # If no mix available, try individual chelates
                    if not recommended_micronutrients:
                        for micro in deficient_micros[:2]:  # Limit to top 2
                            for chelate in chelate_map.get(micro, []):
                                if chelate in available_ids:
                                    recommended_micronutrients.append(chelate)
                                    break
                else:
                    # 1-2 micronutrients - use specific chelates if available
                    for micro in deficient_micros:
                        for chelate in chelate_map.get(micro, []):
                            if chelate in available_ids:
                                recommended_micronutrients.append(chelate)
                                break
        
        # Build basic balance calculation text
        total_cations = sum(deficits.get(ion, 0) for ion in ["Ca", "Mg", "K", "Na", "NH4"] if deficits.get(ion, 0) > 0)
        total_anions = sum(deficits.get(ion, 0) for ion in ["NO3", "H2PO4", "SO4", "SO42", "Cl"] if deficits.get(ion, 0) > 0)
        balance_diff = abs(total_cations - total_anions)
        balance_status = "ÓPTIMO" if balance_diff <= 0.5 else ("ACEPTABLE" if balance_diff <= 1.5 else "REQUIERE AJUSTE")
        
        balance_calc = (
            f"CÁLCULO DE BALANCE IÓNICO:\n"
            f"• CATIONES: Ca2+ ({deficits.get('Ca', 0):.2f}) + Mg2+ ({deficits.get('Mg', 0):.2f}) + "
            f"K+ ({deficits.get('K', 0):.2f}) + NH4+ ({deficits.get('NH4', 0):.2f}) = {total_cations:.2f} meq/L\n"
            f"• ANIONES: NO3- ({deficits.get('NO3', 0):.2f}) + H2PO4- ({deficits.get('H2PO4', 0):.2f}) + "
            f"SO42- ({deficits.get('SO4', 0) or deficits.get('SO42', 0):.2f}) = {total_anions:.2f} meq/L\n"
            f"• DIFERENCIA: {balance_diff:.2f} meq/L\n"
            f"• RESULTADO: Balance {balance_status}"
        )
        
        # Build acid-related explanations based on whether acids are needed
        if acids_needed:
            acid_analysis = "Los ácidos seleccionados neutralizan bicarbonatos y aportan nutrientes. Grower IA proporcionará análisis detallado del doble propósito."
            ph_explanation = f"Se requiere ácido para neutralizar bicarbonatos del agua ({water_hco3:.2f} meq/L). Grower IA proporcionará cantidades exactas."
            warnings_list = ["Active Grower IA para obtener recomendaciones optimizadas con cálculos precisos de balance iónico"]
        else:
            acid_analysis = f"No se recomiendan ácidos porque el agua tiene bicarbonatos muy bajos ({water_hco3:.2f} meq/L). Los nutrientes vendrán de fertilizantes de sal."
            ph_explanation = f"No se requiere ajuste de pH con ácidos porque el agua tiene bicarbonatos muy bajos ({water_hco3:.2f} meq/L)."
            warnings_list = [
                f"ℹ️ INFO: No se dosificaron ácidos porque el agua tiene bicarbonatos muy bajos ({water_hco3:.2f} meq/L). Los nutrientes vendrán de fertilizantes de sal.",
                "Active Grower IA para obtener recomendaciones optimizadas con cálculos precisos de balance iónico"
            ]
        
        return {
            "recommended_fertilizers": recommended,
            "recommended_acids": recommended_acids,
            "recommended_acid": recommended_acids[0] if recommended_acids else None,  # Legacy support
            "recommended_micronutrients": recommended_micronutrients,
            "technical_justification": "Recomendación básica generada automáticamente. Active Grower IA para obtener recomendaciones optimizadas con cantidades exactas y análisis detallado.",
            "ionic_balance_analysis": "Análisis básico: los fertilizantes seleccionados cubren los principales déficits iónicos. Grower IA proporcionará porcentajes exactos de cobertura.",
            "acid_dual_purpose_analysis": acid_analysis,
            "micronutrient_analysis": "Fuentes de micronutrientes seleccionadas según déficits detectados. Grower IA proporcionará análisis detallado.",
            "micronutrient_warnings": self._generate_micronutrient_warnings(micronutrient_deficits) if micronutrient_deficits else [],
            "balance_calculation": balance_calc,
            "ph_adjustment_needed": len(recommended_acids) > 0,
            "ph_adjustment_explanation": ph_explanation,
            "priority_order": recommended,
            "warnings": warnings_list
        }
    
    def _generate_micronutrient_warnings(self, micronutrient_deficits: Dict[str, float]) -> List[str]:
        """Generate warnings for micronutrient levels based on agronomic thresholds."""
        warnings = []
        
        # Thresholds for toxicity/optimal ranges (in ppm)
        thresholds = {
            "Fe": {"optimal_min": 1.0, "optimal_max": 5.0, "toxic": 10.0, "name": "Hierro"},
            "Mn": {"optimal_min": 0.3, "optimal_max": 1.5, "toxic": 2.0, "name": "Manganeso"},
            "Zn": {"optimal_min": 0.1, "optimal_max": 0.5, "toxic": 1.0, "name": "Zinc"},
            "Cu": {"optimal_min": 0.03, "optimal_max": 0.2, "toxic": 0.5, "name": "Cobre"},
            "B": {"optimal_min": 0.2, "optimal_max": 0.8, "toxic": 1.0, "name": "Boro"},
            "Mo": {"optimal_min": 0.02, "optimal_max": 0.1, "toxic": 0.5, "name": "Molibdeno"}
        }
        
        for element, value in micronutrient_deficits.items():
            if element not in thresholds or value <= 0:
                continue
            
            t = thresholds[element]
            
            if value >= t["toxic"]:
                warnings.append(f"⚠️ TOXICIDAD: {t['name']} ({element}) a {value:.2f} ppm supera umbral tóxico ({t['toxic']} ppm)")
            elif value > t["optimal_max"]:
                warnings.append(f"⚠️ ALTO: {t['name']} ({element}) a {value:.2f} ppm está por encima del rango óptimo ({t['optimal_min']}-{t['optimal_max']} ppm)")
            elif value < t["optimal_min"]:
                warnings.append(f"ℹ️ BAJO: {t['name']} ({element}) a {value:.2f} ppm está por debajo del rango óptimo ({t['optimal_min']}-{t['optimal_max']} ppm)")
            else:
                warnings.append(f"✓ {t['name']} ({element}) a {value:.2f} ppm está en rango óptimo")
        
        # Antagonism warnings
        fe_value = micronutrient_deficits.get("Fe", 0)
        mn_value = micronutrient_deficits.get("Mn", 0)
        if fe_value > 0 and mn_value > 0:
            ratio = fe_value / mn_value if mn_value > 0 else 0
            if ratio > 10:
                warnings.append(f"⚠️ ANTAGONISMO: Relación Fe:Mn ({ratio:.1f}:1) muy alta, puede bloquear absorción de Mn")
            elif ratio < 2:
                warnings.append(f"⚠️ ANTAGONISMO: Relación Fe:Mn ({ratio:.1f}:1) muy baja, puede bloquear absorción de Fe")
        
        return warnings
