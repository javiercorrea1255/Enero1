"""
Service for extracting soil and water analysis data from PDF/JPG images using GPT-4 Vision.
Enables users to upload lab reports and auto-fill form fields instead of manual entry.
"""

import os
import base64
import json
import logging
from typing import Dict, Any, Optional, Tuple
from io import BytesIO
try:
    import fitz  # PyMuPDF for PDF handling
except ImportError:
    fitz = None
from PIL import Image

logger = logging.getLogger(__name__)


class AnalysisExtractorService:
    """Service to extract analysis data from PDF/image documents using GPT-4 Vision."""
    
    def __init__(self):
        """Initialize the extractor service with OpenAI client."""
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.openai_api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_api_key)
                logger.info("AnalysisExtractorService initialized with OpenAI")
            except ImportError:
                logger.error("OpenAI library not available")
                self.client = None
        else:
            logger.warning("OPENAI_API_KEY not configured - extraction service disabled")
    
    def _encode_image_to_base64(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def _pdf_to_image(self, pdf_bytes: bytes, page_num: int = 0) -> bytes:
        """
        Convert first page of PDF to PNG image bytes.
        
        Args:
            pdf_bytes: PDF file content as bytes
            page_num: Page number to extract (default: 0 = first page)
        
        Returns:
            PNG image bytes
        """
        if fitz is None:
            raise ValueError("PyMuPDF no está instalado. No se pueden procesar PDFs.")
        
        try:
            # Open PDF from bytes
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Get first page
            page = pdf_document[page_num]
            
            # Render page to image (higher resolution for better OCR)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for clarity
            
            # Convert to PNG bytes
            img_bytes = pix.tobytes("png")
            
            pdf_document.close()
            return img_bytes
            
        except Exception as e:
            logger.error(f"Error converting PDF to image: {e}")
            raise ValueError(f"No se pudo procesar el PDF: {str(e)}")
    
    def _validate_soil_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate extracted soil analysis data for reasonable ranges.
        Comprehensive validation for 35+ parameters from Mexican laboratory reports.
        
        Args:
            data: Extracted soil data dictionary
        
        Returns:
            (is_valid, error_message)
        """
        errors = []
        
        # PRIMARY NUTRIENTS
        if 'soil_n_ppm' in data:
            n = data['soil_n_ppm']
            if n is not None and (n < 0 or n > 150):
                errors.append(f"N inusual: {n} ppm (típico: 0-50)")
        
        if 'soil_p_ppm' in data:
            p = data['soil_p_ppm']
            if p is not None and (p < 0 or p > 200):
                errors.append(f"P inusual: {p} ppm (típico: 0-100)")
        
        if 'soil_k_ppm' in data:
            k = data['soil_k_ppm']
            if k is not None and (k < 0 or k > 1500):
                errors.append(f"K inusual: {k} ppm (típico: 50-800)")
        
        # BASIC PROPERTIES
        if 'ph' in data:
            ph = data['ph']
            if ph is not None and (ph < 3.0 or ph > 10.0):
                errors.append(f"pH fuera de rango: {ph} (debe: 3-10)")
        
        if 'soil_ec_ms_cm' in data:
            ec = data['soil_ec_ms_cm']
            if ec is not None and (ec < 0 or ec > 20):
                errors.append(f"EC inusual: {ec} mS/cm (típico: 0-5)")
        
        if 'organic_matter' in data:
            om = data['organic_matter']
            if om is not None and (om < 0 or om > 20):
                errors.append(f"MO inusual: {om}% (típico: 0-10%)")
        
        if 'cec' in data:
            cec = data['cec']
            if cec is not None and (cec < 0 or cec > 100):
                errors.append(f"CEC inusual: {cec} meq/100g (típico: 5-50)")
        
        if 'sar' in data:
            sar = data['sar']
            if sar is not None and sar > 30:
                errors.append(f"SAR muy alto: {sar} (típico: <15)")
        
        # PHYSICAL PARAMETERS (saturated extract)
        if 'psi' in data:
            psi = data['psi']
            if psi is not None and (psi < 0 or psi > 100):
                errors.append(f"PSI fuera de rango: {psi}% (debe: 0-100%)")
        
        if 'saturation_pct' in data:
            sat = data['saturation_pct']
            if sat is not None and (sat < 0 or sat > 100):
                errors.append(f"Saturación fuera de rango: {sat}% (debe: 0-100%)")
        
        if 'field_capacity' in data:
            fc = data['field_capacity']
            if fc is not None and (fc < 0 or fc > 100):
                errors.append(f"Capacidad de campo fuera de rango: {fc}%")
        
        if 'wilting_point' in data:
            wp = data['wilting_point']
            if wp is not None and (wp < 0 or wp > 100):
                errors.append(f"Punto de marchitez fuera de rango: {wp}%")
        
        # TEXTURE PERCENTAGES
        if 'sand_pct' in data and data['sand_pct'] is not None:
            if data['sand_pct'] < 0 or data['sand_pct'] > 100:
                errors.append(f"Arena % fuera de rango: {data['sand_pct']}")
        
        if 'silt_pct' in data and data['silt_pct'] is not None:
            if data['silt_pct'] < 0 or data['silt_pct'] > 100:
                errors.append(f"Limo % fuera de rango: {data['silt_pct']}")
        
        if 'clay_pct' in data and data['clay_pct'] is not None:
            if data['clay_pct'] < 0 or data['clay_pct'] > 100:
                errors.append(f"Arcilla % fuera de rango: {data['clay_pct']}")
        
        # SECONDARY NUTRIENTS (ppm)
        if 'soil_ca_ppm' in data:
            ca = data['soil_ca_ppm']
            if ca is not None and ca > 10000:
                errors.append(f"Ca muy alto: {ca} ppm (típico: 500-5000)")
        
        if 'soil_mg_ppm' in data:
            mg = data['soil_mg_ppm']
            if mg is not None and mg > 5000:
                errors.append(f"Mg muy alto: {mg} ppm (típico: 100-2000)")
        
        if 'soil_s_ppm' in data:
            s = data['soil_s_ppm']
            if s is not None and s > 500:
                errors.append(f"S muy alto: {s} ppm (típico: 10-100)")
        
        if 'soil_na_ppm' in data:
            na_ppm = data['soil_na_ppm']
            if na_ppm is not None and na_ppm > 2000:
                errors.append(f"Na muy alto: {na_ppm} ppm (típico: <500)")
        
        # MICRONUTRIENTS (ppm)
        if 'soil_fe_ppm' in data:
            fe = data['soil_fe_ppm']
            if fe is not None and (fe < 0 or fe > 200):
                errors.append(f"Fe inusual: {fe} ppm (típico: 5-50)")
        
        if 'soil_zn_ppm' in data:
            zn = data['soil_zn_ppm']
            if zn is not None and (zn < 0 or zn > 50):
                errors.append(f"Zn inusual: {zn} ppm (típico: 1-20)")
        
        if 'soil_cu_ppm' in data:
            cu = data['soil_cu_ppm']
            if cu is not None and (cu < 0 or cu > 30):
                errors.append(f"Cu inusual: {cu} ppm (típico: 0.5-10)")
        
        if 'soil_mn_ppm' in data:
            mn = data['soil_mn_ppm']
            if mn is not None and (mn < 0 or mn > 200):
                errors.append(f"Mn inusual: {mn} ppm (típico: 5-50)")
        
        if 'soil_b_ppm' in data:
            b = data['soil_b_ppm']
            if b is not None and (b < 0 or b > 10):
                errors.append(f"B inusual: {b} ppm (típico: 0.3-3)")
        
        # ANIONS (meq/L - saturated extract)
        if 'soil_no3_meq_l' in data:
            no3 = data['soil_no3_meq_l']
            if no3 is not None and no3 > 30:
                errors.append(f"NO3- muy alto: {no3} meq/L (típico: 1-15)")
        
        if 'soil_so4_meq_l' in data:
            so4 = data['soil_so4_meq_l']
            if so4 is not None and so4 > 30:
                errors.append(f"SO4-2 muy alto: {so4} meq/L (típico: 1-10)")
        
        if 'soil_cl_meq_l' in data:
            cl = data['soil_cl_meq_l']
            if cl is not None and cl > 50:
                errors.append(f"Cl- muy alto: {cl} meq/L (típico: <20)")
        
        if 'soil_hco3_meq_l' in data:
            hco3 = data['soil_hco3_meq_l']
            if hco3 is not None and hco3 > 15:
                errors.append(f"HCO3- muy alto: {hco3} meq/L (típico: 0.5-5)")
        
        if 'soil_co3_meq_l' in data:
            co3 = data['soil_co3_meq_l']
            if co3 is not None and co3 > 5:
                errors.append(f"CO3-2 muy alto: {co3} meq/L (típico: 0)")
        
        # CATIONS (meq/L - saturated extract)
        if 'soil_ca_meq_l' in data:
            ca_meq = data['soil_ca_meq_l']
            if ca_meq is not None and ca_meq > 50:
                errors.append(f"Ca+2 muy alto: {ca_meq} meq/L (típico: 2-20)")
        
        if 'soil_mg_meq_l' in data:
            mg_meq = data['soil_mg_meq_l']
            if mg_meq is not None and mg_meq > 30:
                errors.append(f"Mg+2 muy alto: {mg_meq} meq/L (típico: 1-10)")
        
        if 'soil_k_meq_l' in data:
            k_meq = data['soil_k_meq_l']
            if k_meq is not None and k_meq > 20:
                errors.append(f"K+ muy alto: {k_meq} meq/L (típico: 0.2-5)")
        
        if 'soil_na_meq_l' in data:
            na = data['soil_na_meq_l']
            if na is not None and na > 40:
                errors.append(f"Na+ muy alto: {na} meq/L (típico: <15)")
        
        if errors:
            return False, " | ".join(errors)
        return True, ""
    
    def _validate_water_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate extracted water analysis data for reasonable ranges.
        
        Args:
            data: Extracted water data dictionary
        
        Returns:
            (is_valid, error_message)
        """
        errors = []
        
        # Validate EC - typical range 0-5 dS/m
        if 'source_water_ec' in data:
            ec = data['source_water_ec']
            if ec is not None and (ec < 0 or ec > 10):
                errors.append(f"EC inusual: {ec} dS/m (rango típico: 0-5)")
        
        # Validate pH - must be between 3-10
        if 'current_ph' in data:
            ph = data['current_ph']
            if ph is not None and (ph < 3.0 or ph > 10.0):
                errors.append(f"pH fuera de rango: {ph} (debe estar entre 3-10)")
        
        # Validate Ca - typical range 0-400 ppm
        if 'source_water_ca_ppm' in data:
            ca = data['source_water_ca_ppm']
            if ca is not None and (ca < 0 or ca > 600):
                errors.append(f"Calcio inusual: {ca} ppm (rango típico: 0-400)")
        
        # Validate Mg - typical range 0-200 ppm
        if 'source_water_mg_ppm' in data:
            mg = data['source_water_mg_ppm']
            if mg is not None and (mg < 0 or mg > 300):
                errors.append(f"Magnesio inusual: {mg} ppm (rango típico: 0-200)")
        
        # Validate alkalinity - typical range 0-500 ppm CaCO3
        if 'alkalinity_ppm_caco3' in data:
            alk = data['alkalinity_ppm_caco3']
            if alk is not None and (alk < 0 or alk > 1000):
                errors.append(f"Alcalinidad inusual: {alk} ppm (rango típico: 0-500)")
        
        if errors:
            return False, " | ".join(errors)
        return True, ""
    
    def _round_extracted_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Round extracted numeric values to appropriate precision for form field population.
        
        Rounding rules:
        - Primary nutrients (N, P, K): 1 decimal
        - Secondary nutrients (Ca, Mg, S, Na): 1 decimal
        - Micronutrients (Fe, Zn, Cu, Mn, B): 1 decimal
        - pH: 1 decimal
        - EC: 2 decimals
        - Organic matter: 1 decimal
        - CEC: 1 decimal
        - Percentages (sand, silt, clay, saturation, etc.): 1 decimal
        - Depth: integer (no decimals)
        - Bulk density: 2 decimals
        - meq/L values: 2 decimals
        
        Args:
            data: Extracted data dictionary with numeric values
        
        Returns:
            Dictionary with rounded numeric values
        """
        rounded_data = data.copy()
        
        # Define rounding rules by field name
        one_decimal_fields = [
            'soil_n_ppm', 'soil_p_ppm', 'soil_k_ppm',
            'soil_ca_ppm', 'soil_mg_ppm', 'soil_s_ppm', 'soil_na_ppm',
            'soil_fe_ppm', 'soil_zn_ppm', 'soil_cu_ppm', 'soil_mn_ppm', 'soil_b_ppm',
            'ph', 'organic_matter', 'cec', 'sar', 'psi',
            'sand_pct', 'silt_pct', 'clay_pct',
            'saturation_pct', 'field_capacity', 'wilting_point',
            'current_ph'
        ]
        
        two_decimal_fields = [
            'soil_ec_ms_cm', 'bulk_density_g_cm3',
            'soil_no3_meq_l', 'soil_so4_meq_l', 'soil_cl_meq_l', 
            'soil_hco3_meq_l', 'soil_co3_meq_l',
            'soil_ca_meq_l', 'soil_mg_meq_l', 'soil_k_meq_l', 'soil_na_meq_l',
            'source_water_ec', 'source_water_ca_ppm', 'source_water_mg_ppm',
            'alkalinity_ppm_caco3', 'source_water_tds', 'hardness'
        ]
        
        integer_fields = ['depth_cm']
        
        # Apply rounding
        for field in one_decimal_fields:
            if field in rounded_data and rounded_data[field] is not None:
                try:
                    rounded_data[field] = round(float(rounded_data[field]), 1)
                except (ValueError, TypeError):
                    pass
        
        for field in two_decimal_fields:
            if field in rounded_data and rounded_data[field] is not None:
                try:
                    rounded_data[field] = round(float(rounded_data[field]), 2)
                except (ValueError, TypeError):
                    pass
        
        for field in integer_fields:
            if field in rounded_data and rounded_data[field] is not None:
                try:
                    rounded_data[field] = int(round(float(rounded_data[field])))
                except (ValueError, TypeError):
                    pass
        
        return rounded_data
    
    def extract_soil_analysis(self, file_bytes: bytes, file_type: str) -> Dict[str, Any]:
        """
        Extract soil analysis data from PDF or image using GPT-4 Vision.
        
        Args:
            file_bytes: File content as bytes
            file_type: 'pdf' or 'image'
        
        Returns:
            Dictionary with extracted soil parameters
        
        Raises:
            ValueError: If extraction fails or OpenAI not available
        """
        if not self.client:
            raise ValueError("Servicio de extracción no disponible. Configure OPENAI_API_KEY.")
        
        try:
            # Convert PDF to image if needed
            if file_type.lower() == 'pdf':
                logger.info("Converting PDF to image for OCR")
                image_bytes = self._pdf_to_image(file_bytes)
            else:
                image_bytes = file_bytes
            
            # Encode to base64
            base64_image = self._encode_image_to_base64(image_bytes)
            
            # Prepare comprehensive prompt for GPT-4 Vision (trained on Mexican lab formats)
            prompt = """Analiza este reporte de análisis de suelo PROFESIONAL y extrae TODOS los parámetros disponibles.
Este es típicamente un reporte de laboratorio mexicano (PHYTOMONITOR, AGRILAB, etc.) con análisis completo o extracto saturado.

Si algún dato NO está presente en el reporte, usa null para ese campo.

═══════════════════════════════════════════════════════
PARÁMETROS A EXTRAER (35+ campos):
═══════════════════════════════════════════════════════

📊 PROPIEDADES FÍSICAS BÁSICAS:
- ph: pH del suelo (método potenciométrico)
- soil_ec_ms_cm: Conductividad Eléctrica en mS/cm (electrométrico)
- texture: Textura textual ("arenosa", "franca", "arcillosa", "franco-arenosa", "franco-arcillosa", "franco-limosa")
- organic_matter: Materia Orgánica en % (MO o CO×1.724)
- cec: Capacidad de Intercambio Catiónico en meq/100g o cmol/kg
- sar: Relación de Absorción de Sodio (SAR)
- psi: Porciento de Sodio Intercambiable en %
- saturation_pct: Porcentaje de Saturación en %
- field_capacity: Capacidad de Campo en %
- wilting_point: Punto de Marchitez Permanente en %

📐 TEXTURA DETALLADA (si está desglosado):
- sand_pct: Arena en %
- silt_pct: Limo en %
- clay_pct: Arcilla en %

🌿 NUTRIENTES PRIMARIOS (N-P-K):
- soil_n_ppm: Nitrógeno disponible en ppm o mg/kg (NO3-N, N-Inorgánico, N mineral)
- soil_p_ppm: Fósforo disponible en ppm o mg/kg (Olsen, Bray, Mehlich)  
- soil_k_ppm: Potasio intercambiable en ppm (si está en meq/L, convertir: meq/L × 390 = ppm)

💎 NUTRIENTES SECUNDARIOS (Ca-Mg-S-Na):
- soil_ca_ppm: Calcio en ppm (si está en meq/L, usar: meq/L × 200 = ppm)
- soil_mg_ppm: Magnesio en ppm (si está en meq/L, usar: meq/L × 121 = ppm)
- soil_s_ppm: Azufre en ppm (de SO4-2, si está en meq/L: meq/L × 160 = ppm)
- soil_na_ppm: Sodio en ppm (si está en meq/L, usar: meq/L × 230 = ppm)

🔬 MICRONUTRIENTES (Fe-Zn-Cu-Mn-B):
- soil_fe_ppm: Fierro (Fe) en ppm (método DTPA)
- soil_zn_ppm: Zinc (Zn) en ppm (método DTPA)
- soil_cu_ppm: Cobre (Cu) en ppm (método DTPA)
- soil_mn_ppm: Manganeso (Mn) en ppm (método DTPA)
- soil_b_ppm: Boro (B) en ppm (Azometina-H)

⚡ ANIONES (meq/L para extracto saturado):
- soil_no3_meq_l: Nitratos (NO3-) en meq/L
- soil_so4_meq_l: Sulfatos (SO4-2) en meq/L
- soil_cl_meq_l: Cloruros (Cl-) en meq/L
- soil_hco3_meq_l: Bicarbonatos (HCO3-) en meq/L
- soil_co3_meq_l: Carbonatos (CO3-2) en meq/L

⚡ CATIONES (meq/L para extracto saturado):
- soil_ca_meq_l: Calcio (Ca+2) en meq/L
- soil_mg_meq_l: Magnesio (Mg+2) en meq/L
- soil_k_meq_l: Potasio (K+) en meq/L
- soil_na_meq_l: Sodio (Na+) en meq/L

═══════════════════════════════════════════════════════
INSTRUCCIONES DE CONVERSIÓN:
═══════════════════════════════════════════════════════

1. **Unidades comunes en reportes mexicanos:**
   - ppm = mg/kg (son equivalentes)
   - meq/L para extracto saturado
   - mS/cm para EC (a veces en dS/m, son iguales)
   - µS/cm ÷ 1000 = mS/cm

2. **Conversiones de meq/L a ppm (para extracto saturado):**
   - K+ intercambiable: meq/L × 390 = ppm
   - Ca+2 intercambiable: meq/L × 200 = ppm
   - Mg+2 intercambiable: meq/L × 121 = ppm
   - Na+ intercambiable: meq/L × 230 = ppm
   - S de SO4-2: meq/L × 160 = ppm (azufre elemental)

3. **Para nitrógeno disponible:**
   - Extraer N disponible en ppm o mg/kg como aparece en el reporte
   - Buscar: "N-NO3", "N inorgánico", "N mineral", "N disponible"
   - NO convertir de meq/L - si solo está en meq/L, dejar null y usar soil_no3_meq_l

4. **Prioridad de datos:**
   - Si hay AMBAS formas (ppm Y meq/L), extraer AMBOS valores en sus respectivos campos
   - Campos *_ppm son para valores intercambiables en suelo
   - Campos *_meq_l son para extracto saturado
   - No hacer conversiones complejas - extraer valores como aparecen

5. **Textura:**
   - Usar términos exactos: "arenosa", "franca", "arcillosa", "franco-arenosa", "franco-arcillosa", "franco-limosa"
   - Si solo hay %arena/%limo/%arcilla, determinar la clase textural según USDA

═══════════════════════════════════════════════════════
FORMATO DE RESPUESTA (JSON estricto):
═══════════════════════════════════════════════════════

{
  "ph": number | null,
  "soil_ec_ms_cm": number | null,
  "texture": string | null,
  "organic_matter": number | null,
  "cec": number | null,
  "sar": number | null,
  "psi": number | null,
  "saturation_pct": number | null,
  "field_capacity": number | null,
  "wilting_point": number | null,
  
  "sand_pct": number | null,
  "silt_pct": number | null,
  "clay_pct": number | null,
  
  "soil_n_ppm": number | null,
  "soil_p_ppm": number | null,
  "soil_k_ppm": number | null,
  
  "soil_ca_ppm": number | null,
  "soil_mg_ppm": number | null,
  "soil_s_ppm": number | null,
  "soil_na_ppm": number | null,
  
  "soil_fe_ppm": number | null,
  "soil_zn_ppm": number | null,
  "soil_cu_ppm": number | null,
  "soil_mn_ppm": number | null,
  "soil_b_ppm": number | null,
  
  "soil_no3_meq_l": number | null,
  "soil_so4_meq_l": number | null,
  "soil_cl_meq_l": number | null,
  "soil_hco3_meq_l": number | null,
  "soil_co3_meq_l": number | null,
  
  "soil_ca_meq_l": number | null,
  "soil_mg_meq_l": number | null,
  "soil_k_meq_l": number | null,
  "soil_na_meq_l": number | null,
  
  "confidence": "high" | "medium" | "low",
  "notes": "Breve descripción del tipo de análisis (extracto saturado/suelo estándar) y observaciones"
}

IMPORTANTE: Usa SOLO números sin unidades. Extrae TODO lo que encuentres en el reporte."""
            
            # Call GPT-4 Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",  # GPT-4 with vision capabilities
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"  # High detail for better accuracy
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1  # Low temperature for factual extraction
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            extracted_data = json.loads(content)
            
            # Round extracted values for proper form field population
            extracted_data = self._round_extracted_values(extracted_data)
            
            # Validate extracted data
            is_valid, error_msg = self._validate_soil_data(extracted_data)
            if not is_valid:
                logger.warning(f"Validation warnings: {error_msg}")
                extracted_data['validation_warnings'] = error_msg
            
            logger.info(f"Successfully extracted soil data with confidence: {extracted_data.get('confidence')}")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {e}")
            raise ValueError("No se pudo interpretar la respuesta del análisis. Intente con mejor calidad de imagen.")
        except Exception as e:
            logger.error(f"Error extracting soil analysis: {e}")
            raise ValueError(f"Error al procesar el análisis: {str(e)}")
    
    def extract_water_analysis(self, file_bytes: bytes, file_type: str) -> Dict[str, Any]:
        """
        Extract water analysis data from PDF or image using GPT-4 Vision.
        
        Args:
            file_bytes: File content as bytes
            file_type: 'pdf' or 'image'
        
        Returns:
            Dictionary with extracted water parameters
        
        Raises:
            ValueError: If extraction fails or OpenAI not available
        """
        if not self.client:
            raise ValueError("Servicio de extracción no disponible. Configure OPENAI_API_KEY.")
        
        try:
            # Convert PDF to image if needed
            if file_type.lower() == 'pdf':
                logger.info("Converting PDF to image for OCR")
                image_bytes = self._pdf_to_image(file_bytes)
            else:
                image_bytes = file_bytes
            
            # Encode to base64
            base64_image = self._encode_image_to_base64(image_bytes)
            
            # Prepare prompt for GPT-4 Vision
            prompt = """Analiza este reporte de análisis de agua y extrae los siguientes parámetros. 
Si algún dato no está presente, usa null.

PARÁMETROS A EXTRAER:
- source_water_ec: Conductividad eléctrica (dS/m o mS/cm)
- current_ph: pH del agua
- source_water_ca_ppm: Calcio (ppm o mg/L)
- source_water_mg_ppm: Magnesio (ppm o mg/L)
- alkalinity_ppm_caco3: Alcalinidad como CaCO3 (ppm o mg/L)
- source_water_tds: Sólidos disueltos totales (ppm)
- hardness: Dureza total (ppm CaCO3)

IMPORTANTE:
- Usa SOLO números, sin unidades
- Si EC está en µS/cm, divide entre 1000 para obtener dS/m
- Si TDS está en mg/L, úsalo directamente (equivale a ppm)
- Si la dureza no está como CaCO3, intenta calcularla: Dureza(CaCO3) ≈ 2.5*Ca + 4.1*Mg

Responde en formato JSON estricto:
{
  "source_water_ec": number | null,
  "current_ph": number | null,
  "source_water_ca_ppm": number | null,
  "source_water_mg_ppm": number | null,
  "alkalinity_ppm_caco3": number | null,
  "source_water_tds": number | null,
  "hardness": number | null,
  "confidence": "high" | "medium" | "low",
  "notes": "Observaciones sobre la calidad de extracción"
}"""
            
            # Call GPT-4 Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            import json
            extracted_data = json.loads(content)
            
            # Round extracted values for proper form field population
            extracted_data = self._round_extracted_values(extracted_data)
            
            # Validate extracted data
            is_valid, error_msg = self._validate_water_data(extracted_data)
            if not is_valid:
                logger.warning(f"Validation warnings: {error_msg}")
                extracted_data['validation_warnings'] = error_msg
            
            logger.info(f"Successfully extracted water data with confidence: {extracted_data.get('confidence')}")
            return extracted_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {e}")
            raise ValueError("No se pudo interpretar la respuesta del análisis. Intente con mejor calidad de imagen.")
        except Exception as e:
            logger.error(f"Error extracting water analysis: {e}")
            raise ValueError(f"Error al procesar el análisis: {str(e)}")
