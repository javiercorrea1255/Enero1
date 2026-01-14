"""
Core calculation functions for AgriDose platform.
Implements NOM-021-RECNAT-2000 (Mexico) standards for soil analysis conversions.
"""

def ppm_to_kg_ha(ppm: float, depth_cm: float, bulk_density_g_cm3: float) -> float:
    """
    Convert ppm to kg/ha using NOM-021-RECNAT-2000 formula.
    
    Formula: kg/ha = ppm × 0.1 × depth(cm) × bulk_density(g/cm³)
    
    Args:
        ppm: Concentration in parts per million
        depth_cm: Soil depth in centimeters
        bulk_density_g_cm3: Bulk density in g/cm³
    
    Returns:
        Nutrient content in kg/ha
    """
    return ppm * 0.1 * depth_cm * bulk_density_g_cm3


def elemental_to_p2o5(p_elemental: float) -> float:
    """
    Convert elemental P to P₂O₅.
    
    Args:
        p_elemental: Elemental phosphorus in kg/ha
    
    Returns:
        P₂O₅ in kg/ha
    """
    return p_elemental * 2.29


def elemental_to_k2o(k_elemental: float) -> float:
    """
    Convert elemental K to K₂O.
    
    Args:
        k_elemental: Elemental potassium in kg/ha
    
    Returns:
        K₂O in kg/ha
    """
    return k_elemental * 1.20


def p2o5_to_elemental(p2o5: float) -> float:
    """Convert P₂O₅ to elemental P."""
    return p2o5 / 2.29


def k2o_to_elemental(k2o: float) -> float:
    """Convert K₂O to elemental K."""
    return k2o / 1.20


def calculate_extraction_requirements(
    crop_coef_n: float,
    crop_coef_p2o5: float,
    crop_coef_k2o: float,
    yield_target_t_ha: float
) -> dict:
    """
    Calculate nutrient requirements using extraction/balance method.
    
    Formula: Requirement = extraction_coefficient (kg/t) × yield_target (t/ha)
    
    Args:
        crop_coef_n: N extraction coefficient (kg N per ton of yield)
        crop_coef_p2o5: P₂O₅ extraction coefficient
        crop_coef_k2o: K₂O extraction coefficient
        yield_target_t_ha: Target yield in tons per hectare
    
    Returns:
        Dict with N, P2O5, K2O requirements in kg/ha
    """
    return {
        "N": crop_coef_n * yield_target_t_ha,
        "P2O5": crop_coef_p2o5 * yield_target_t_ha,
        "K2O": crop_coef_k2o * yield_target_t_ha
    }


def calculate_soil_credit(
    soil_n_ppm: float,
    soil_p_ppm: float,
    soil_k_ppm: float,
    depth_cm: float,
    bulk_density_g_cm3: float
) -> dict:
    """
    Calculate nutrient credits from soil analysis.
    
    Args:
        soil_n_ppm: Soil nitrogen in ppm (NO3-N available)
        soil_p_ppm: Soil phosphorus in ppm
        soil_k_ppm: Soil potassium in ppm
        depth_cm: Sampling depth in cm
        bulk_density_g_cm3: Soil bulk density
    
    Returns:
        Dict with N, P2O5, K2O credits in kg/ha
    """
    # Convert all nutrients from ppm to kg/ha using NOM-021 formula
    n_kg_ha = ppm_to_kg_ha(soil_n_ppm, depth_cm, bulk_density_g_cm3)
    p_elemental_kg_ha = ppm_to_kg_ha(soil_p_ppm, depth_cm, bulk_density_g_cm3)
    k_elemental_kg_ha = ppm_to_kg_ha(soil_k_ppm, depth_cm, bulk_density_g_cm3)
    
    return {
        "N": n_kg_ha,
        "P2O5": elemental_to_p2o5(p_elemental_kg_ha),
        "K2O": elemental_to_k2o(k_elemental_kg_ha)
    }


def calculate_build_up(
    current_ppm: float,
    critical_ppm: float,
    depth_cm: float,
    bulk_density_g_cm3: float,
    is_p: bool = True
) -> float:
    """
    Calculate build-up requirement when soil levels are below critical threshold.
    
    Args:
        current_ppm: Current soil nutrient level
        critical_ppm: Critical threshold level
        depth_cm: Soil depth in cm
        bulk_density_g_cm3: Bulk density
        is_p: True for phosphorus (convert to P₂O₅), False for potassium (convert to K₂O)
    
    Returns:
        Build-up requirement in kg/ha (as P₂O₅ or K₂O)
    """
    if current_ppm >= critical_ppm:
        return 0.0
    
    delta_ppm = critical_ppm - current_ppm
    elemental_kg_ha = ppm_to_kg_ha(delta_ppm, depth_cm, bulk_density_g_cm3)
    
    if is_p:
        return elemental_to_p2o5(elemental_kg_ha)
    else:
        return elemental_to_k2o(elemental_kg_ha)


AGRONOMIC_WARNING_THRESHOLDS = {
    'N': 400.0,
    'P2O5': 250.0,
    'K2O': 350.0,
    'Ca': 300.0,
    'Mg': 150.0,
    'S': 100.0
}

def calculate_fertilizer_dose(
    requirement_kg_ha: float,
    soil_credit_kg_ha: float,
    build_up_kg_ha: float,
    efficiency: float,
    nutrient_type: str = None,
    apply_max_limit: bool = False
) -> float:
    """
    Calculate fertilizer dose considering requirements, soil credits, build-up, and efficiency.
    
    Formula: Fertilizer = max(0, (Requirement - SoilCredit + BuildUp) / Efficiency)
    
    Args:
        requirement_kg_ha: Nutrient requirement from crop
        soil_credit_kg_ha: Available nutrient in soil
        build_up_kg_ha: Additional build-up needed
        efficiency: Nutrient use efficiency (0-1)
        nutrient_type: Type of nutrient (unused, kept for API compatibility)
        apply_max_limit: Deprecated - limits are no longer applied silently
    
    Returns:
        Fertilizer dose in kg/ha (no caps applied - use check_agronomic_warnings for alerts)
    """
    if efficiency <= 0:
        efficiency = 0.5
    
    net_requirement = requirement_kg_ha - soil_credit_kg_ha + build_up_kg_ha
    fertilizer = max(0, net_requirement / efficiency)
    
    return fertilizer


def check_agronomic_warnings(fertilizer_kg_ha: dict) -> list:
    """
    Check fertilizer recommendations against agronomic warning thresholds.
    
    Args:
        fertilizer_kg_ha: Dict with nutrient keys ('N', 'P2O5', 'K2O', etc.) and values in kg/ha
    
    Returns:
        List of warning messages for values exceeding thresholds
    """
    warnings = []
    for nutrient, value in fertilizer_kg_ha.items():
        if nutrient in AGRONOMIC_WARNING_THRESHOLDS:
            threshold = AGRONOMIC_WARNING_THRESHOLDS[nutrient]
            if value > threshold:
                warnings.append(
                    f"Recomendación de {nutrient} ({value:.1f} kg/ha) excede el umbral típico "
                    f"({threshold:.0f} kg/ha). Verifique los datos de entrada o consulte un agrónomo."
                )
    return warnings


def suggest_granular_blend(n_kg_ha: float, p2o5_kg_ha: float, k2o_kg_ha: float) -> dict:
    """
    Suggest granular fertilizer blend using DAP, Urea, and MOP.
    
    Strategy:
    1. Cover P₂O₅ with DAP (18-46-0)
    2. Cover K₂O with MOP (0-0-60)
    3. Complete N with Urea (46-0-0)
    
    Args:
        n_kg_ha: Nitrogen requirement (kg/ha)
        p2o5_kg_ha: P₂O₅ requirement (kg/ha)
        k2o_kg_ha: K₂O requirement (kg/ha)
    
    Returns:
        Dict with product names and doses in kg/ha
    """
    blend = {}
    
    dap_n_pct = 18.0
    dap_p2o5_pct = 46.0
    urea_n_pct = 46.0
    mop_k2o_pct = 60.0
    
    dap_kg = (p2o5_kg_ha / dap_p2o5_pct) * 100 if p2o5_kg_ha > 0 else 0
    n_from_dap = (dap_kg * dap_n_pct) / 100
    
    mop_kg = (k2o_kg_ha / mop_k2o_pct) * 100 if k2o_kg_ha > 0 else 0
    
    remaining_n = max(0, n_kg_ha - n_from_dap)
    urea_kg = (remaining_n / urea_n_pct) * 100 if remaining_n > 0 else 0
    
    if dap_kg > 0:
        blend["DAP_18_46_0"] = round(dap_kg, 1)
    if urea_kg > 0:
        blend["Urea_46_0_0"] = round(urea_kg, 1)
    if mop_kg > 0:
        blend["MOP_0_0_60"] = round(mop_kg, 1)
    
    return blend


def calculate_foliar_dose(
    target_concentration_pct: float,
    volume_l_ha: float,
    product_nutrient_pct: float
) -> float:
    """
    Calculate foliar fertilizer product dose.
    
    Formula: Product_dose (L or kg/ha) = (target_% / product_%) × Volume(L/ha)
    
    Args:
        target_concentration_pct: Target nutrient concentration in spray solution (%)
        volume_l_ha: Spray volume (L/ha)
        product_nutrient_pct: Nutrient content in product (%)
    
    Returns:
        Product dose in L or kg per hectare
    """
    if product_nutrient_pct <= 0:
        return 0.0
    
    return (target_concentration_pct / product_nutrient_pct) * volume_l_ha


def calculate_foliar_nutrient_delivery(
    product_dose_l_ha: float,
    product_nutrient_pct: float,
    product_density_kg_l: float = 1.0
) -> float:
    """
    Calculate actual nutrient delivered by foliar application.
    
    Args:
        product_dose_l_ha: Product dose in L/ha
        product_nutrient_pct: Nutrient percentage in product
        product_density_kg_l: Product density (default 1.0 for liquids)
    
    Returns:
        Nutrient delivered in kg/ha
    """
    product_kg_ha = product_dose_l_ha * product_density_kg_l
    return (product_kg_ha * product_nutrient_pct) / 100


def generate_foliar_warnings(
    temp_c: float,
    rh_pct: float,
    water_ph: float,
    product_has_phosphate: bool = False,
    product_has_calcium: bool = False
) -> tuple[list[str], list[str]]:
    """
    Generate safety warnings and compatibility alerts for foliar applications.
    
    Based on FAO guidelines and best practices.
    
    Args:
        temp_c: Air temperature in Celsius
        rh_pct: Relative humidity percentage
        water_ph: Water pH
        product_has_phosphate: Whether product contains phosphate
        product_has_calcium: Whether product contains calcium
    
    Returns:
        Tuple of (warnings list, compatibility list)
    """
    warnings = []
    compatibility = []
    
    if water_ph < 6.0 or water_ph > 6.5:
        warnings.append(
            f"Ajuste el pH del agua a 6.0–6.5 (actual: {water_ph:.1f}). "
            "pH inadecuado reduce efectividad y puede causar fitotoxicidad."
        )
    
    if temp_c > 30:
        warnings.append(
            f"Evite aplicaciones foliares con temperaturas >30°C (actual: {temp_c}°C). "
            "Riesgo alto de quemaduras foliares y evaporación rápida."
        )
    
    if rh_pct < 40:
        warnings.append(
            f"Humedad relativa baja (<40%, actual: {rh_pct}%). "
            "Aplicar temprano en la mañana o al atardecer para mejorar absorción."
        )
    
    if product_has_phosphate and product_has_calcium:
        compatibility.append(
            "INCOMPATIBILIDAD: No mezcle fosfatos con calcio. "
            "Forman precipitados insolubles que obstruyen boquillas."
        )
    
    compatibility.append(
        "Realice prueba de jarra antes de mezclar múltiples productos."
    )
    
    if product_has_phosphate:
        compatibility.append(
            "Evite mezclar productos con fósforo con sulfatos de calcio o magnesio."
        )
    
    return warnings, compatibility
