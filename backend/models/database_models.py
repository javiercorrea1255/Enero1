"""
SQLAlchemy database models for AgriDose-Directoalcampo.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class ModuleType(str, enum.Enum):
    """Module type enum for projects.
    
    Note: HYDROPONICS is legacy value for backward compatibility with existing data.
    Use HYDRO for new records (basic hydroponics) and HYDRO_IONS for ion-based hydroponics.
    """
    SOIL = "soil"
    HYDROPONICS = "hydroponics"  # LEGACY: for backward compatibility with existing records
    HYDRO = "hydro"  # Canonical identifier for basic hydroponics module
    HYDRO_IONS = "hydro_ions"  # Canonical identifier for ion-based hydroponics (Meq/L)
    
    @classmethod
    def normalize(cls, module_str: str) -> 'ModuleType':
        """Normalize module identifier to enum member.
        
        Maps legacy 'hydroponics' to HYDRO for new code,
        while accepting HYDRO_IONS directly.
        """
        if not module_str:
            return cls.SOIL
        
        module_lower = module_str.lower().strip()
        
        if module_lower == "soil":
            return cls.SOIL
        elif module_lower in ("hydro", "hydroponics"):
            # Map both to HYDRO (legacy hydroponics → new canonical)
            return cls.HYDRO
        elif module_lower == "hydro_ions":
            return cls.HYDRO_IONS
        else:
            raise ValueError(f"Unknown module type: {module_str}")


class User(Base):
    """User model for authentication and profile."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Name fields (separated for better database structure)
    # nullable=True for backwards compatibility with existing users
    nombres = Column(String, nullable=True)
    apellido_paterno = Column(String, nullable=True)
    apellido_materno = Column(String, nullable=True)
    full_name = Column(String, nullable=True)  # Computed field for backwards compatibility
    
    role = Column(String, default="productor")  # productor, tecnico, admin
    organization = Column(String, nullable=True)
    
    # Contact fields
    phone = Column(String, nullable=True)
    has_whatsapp = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    phone_verified_at = Column(DateTime(timezone=True), nullable=True)
    phone_verification_attempts = Column(Integer, default=0)
    phone_verification_locked_until = Column(DateTime(timezone=True), nullable=True)  # Anti-fraud lockout
    
    position = Column(String, nullable=True)
    
    # Location fields
    country = Column(String, nullable=False, default="México")
    state = Column(String, nullable=True)  # Estado/Province
    municipality = Column(String, nullable=True)  # Municipio (for México)
    city = Column(String, nullable=True)  # Ciudad/City (for non-México countries or additional detail)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Subscription fields
    subscription_status = Column(String, default="free")  # free, active, past_due, canceled
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    plan_type = Column(String, default="free")  # free, professional
    project_limit = Column(Integer, default=3)  # 3 for free, 9999 for professional
    projects_used = Column(Integer, default=0)
    subscription_ends_at = Column(DateTime(timezone=True), nullable=True)
    subscription_start_date = Column(DateTime(timezone=True), nullable=True)  # When Pro subscription started (for 30-day cycle reset)
    
    # Module usage limits (deprecated - now using trial days instead)
    soil_uses_count = Column(Integer, default=0)  # Counter for SOIL module (NOM-021 + ROI combined)
    hydro_uses_count = Column(Integer, default=0)  # Counter for HYDROPONICS module (basic + pro combined)
    
    # 7-day free trial system
    trial_start_date = Column(DateTime(timezone=True), nullable=True)  # When user started their 7-day trial
    
    # Session tracking for anti-sharing
    last_login_ip = Column(String, nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_device_fingerprint = Column(String, nullable=True)
    known_device_fingerprints = Column(JSON, nullable=True)  # List of known fingerprints
    
    # Grower Expert role - assigned by admin, grants Premium access + self-service profile management
    is_grower_expert = Column(Boolean, default=False)
    grower_expert_assigned_at = Column(DateTime(timezone=True), nullable=True)
    grower_expert_assigned_by = Column(Integer, nullable=True)  # Admin user_id who assigned the role
    
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    grower_profile = relationship("Grower", back_populates="user", uselist=False)


class PasswordResetToken(Base):
    """Password reset token model for secure password recovery."""
    __tablename__ = "password_reset_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="password_reset_tokens")


class Project(Base):
    """Project/Farm model - represents a farm or production unit."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    total_area_ha = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    geometry = Column(JSON, nullable=True)  # GeoJSON polygon for georeferenced boundary
    module_type = Column(Enum(ModuleType, values_callable=lambda x: [e.value for e in x]), default=ModuleType.SOIL, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    owner = relationship("User", back_populates="projects")
    plots = relationship("Plot", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="project", cascade="all, delete-orphan")


class Plot(Base):
    """Plot/Field model - represents individual plots within a project."""
    __tablename__ = "plots"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    area_ha = Column(Float, nullable=False)
    soil_texture = Column(String, nullable=True)
    irrigation_type = Column(String, nullable=True)  # riego, temporal, goteo, aspersion
    gps_coordinates = Column(JSON, nullable=True)  # {"lat": x, "lng": y}
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    project = relationship("Project", back_populates="plots")
    soil_analyses = relationship("SoilAnalysis", back_populates="plot", cascade="all, delete-orphan")
    foliar_analyses = relationship("FoliarAnalysis", back_populates="plot", cascade="all, delete-orphan")
    fertilization_programs = relationship("FertilizationProgram", back_populates="plot", cascade="all, delete-orphan")


class SoilAnalysis(Base):
    """Soil analysis records."""
    __tablename__ = "soil_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    plot_id = Column(Integer, ForeignKey("plots.id"), nullable=False)
    analysis_date = Column(DateTime(timezone=True), nullable=False)
    laboratory = Column(String, nullable=True)
    
    # Nutrient levels
    n_kg_ha = Column(Float, nullable=True)
    p_ppm = Column(Float, nullable=True)
    k_ppm = Column(Float, nullable=True)
    
    # Physical properties
    ph = Column(Float, nullable=True)
    organic_matter_pct = Column(Float, nullable=True)
    texture = Column(String, nullable=True)
    bulk_density_g_cm3 = Column(Float, default=1.3)
    depth_cm = Column(Float, default=20.0)
    
    # Salinity
    ec_dS_m = Column(Float, nullable=True)
    
    # Additional nutrients
    ca_ppm = Column(Float, nullable=True)
    mg_ppm = Column(Float, nullable=True)
    s_ppm = Column(Float, nullable=True)
    zn_ppm = Column(Float, nullable=True)
    fe_ppm = Column(Float, nullable=True)
    mn_ppm = Column(Float, nullable=True)
    cu_ppm = Column(Float, nullable=True)
    b_ppm = Column(Float, nullable=True)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    plot = relationship("Plot", back_populates="soil_analyses")


class FoliarAnalysis(Base):
    """Foliar analysis records."""
    __tablename__ = "foliar_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    plot_id = Column(Integer, ForeignKey("plots.id"), nullable=False)
    analysis_date = Column(DateTime(timezone=True), nullable=False)
    phenological_stage = Column(String, nullable=False)
    laboratory = Column(String, nullable=True)
    
    # Macronutrients (%)
    n_pct = Column(Float, nullable=True)
    p_pct = Column(Float, nullable=True)
    k_pct = Column(Float, nullable=True)
    ca_pct = Column(Float, nullable=True)
    mg_pct = Column(Float, nullable=True)
    s_pct = Column(Float, nullable=True)
    
    # Micronutrients (ppm)
    zn_ppm = Column(Float, nullable=True)
    fe_ppm = Column(Float, nullable=True)
    mn_ppm = Column(Float, nullable=True)
    cu_ppm = Column(Float, nullable=True)
    b_ppm = Column(Float, nullable=True)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    plot = relationship("Plot", back_populates="foliar_analyses")


class FertilizationProgram(Base):
    """Fertilization program/calculation records."""
    __tablename__ = "fertilization_programs"
    
    id = Column(Integer, primary_key=True, index=True)
    plot_id = Column(Integer, ForeignKey("plots.id"), nullable=False)
    crop_slug = Column(String, nullable=False)
    crop_variety = Column(String, nullable=True)
    planting_date = Column(DateTime(timezone=True), nullable=True)
    harvest_date = Column(DateTime(timezone=True), nullable=True)
    yield_target_t_ha = Column(Float, nullable=False)
    actual_yield_t_ha = Column(Float, nullable=True)
    
    # Calculation method and parameters
    calculation_method = Column(String, nullable=False)  # extraccion_balance, suficiencia_critico, dris, etc
    calculation_inputs = Column(JSON, nullable=False)  # All input parameters
    calculation_results = Column(JSON, nullable=False)  # Complete results
    
    # Soil analysis reference
    soil_analysis_id = Column(Integer, ForeignKey("soil_analyses.id"), nullable=True)
    
    # Status
    status = Column(String, default="planificado")  # planificado, en_ejecucion, completado
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    plot = relationship("Plot", back_populates="fertilization_programs")
    applications = relationship("FertilizerApplication", back_populates="program", cascade="all, delete-orphan")


class FertilizerApplication(Base):
    """Individual fertilizer application records."""
    __tablename__ = "fertilizer_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("fertilization_programs.id"), nullable=False)
    application_date = Column(DateTime(timezone=True), nullable=True)
    planned_date = Column(DateTime(timezone=True), nullable=True)
    phenological_stage = Column(String, nullable=True)
    
    application_type = Column(String, nullable=False)  # soil, foliar
    
    # Products and doses
    products = Column(JSON, nullable=False)  # [{"name": "Urea", "dose_kg_ha": 200, "n_content": 46}]
    
    # Nutrients applied
    n_applied_kg_ha = Column(Float, nullable=True)
    p2o5_applied_kg_ha = Column(Float, nullable=True)
    k2o_applied_kg_ha = Column(Float, nullable=True)
    
    # Application details
    method = Column(String, nullable=True)  # broadcast, banding, fertigation, foliar
    volume_l_ha = Column(Float, nullable=True)  # For foliar/fertigation
    
    completed = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    program = relationship("FertilizationProgram", back_populates="applications")


class CropVariety(Base):
    """Extended crop varieties database."""
    __tablename__ = "crop_varieties"
    
    id = Column(Integer, primary_key=True, index=True)
    crop_slug = Column(String, nullable=False, index=True)
    variety_name = Column(String, nullable=False)
    variety_code = Column(String, nullable=True)
    
    # Extraction coefficients (can vary by variety)
    n_per_t = Column(Float, nullable=False)
    p2o5_per_t = Column(Float, nullable=False)
    k2o_per_t = Column(Float, nullable=False)
    
    # Growth cycle
    days_to_harvest = Column(Integer, nullable=True)
    
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FertilizerProduct(Base):
    """Fertilizer product catalog with complete specifications."""
    __tablename__ = "fertilizer_products"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic information
    name = Column(String, nullable=False, unique=True, index=True)
    slug = Column(String, nullable=False, unique=True, index=True)
    category = Column(String, nullable=False, index=True)
    subcategory = Column(String, nullable=True)
    
    # Nutrient composition (%)
    n_pct = Column(Float, default=0.0)
    p2o5_pct = Column(Float, default=0.0)
    k2o_pct = Column(Float, default=0.0)
    s_pct = Column(Float, default=0.0)
    ca_pct = Column(Float, default=0.0)
    mg_pct = Column(Float, default=0.0)
    
    # Micronutrients (% or ppm as JSON)
    micronutrients = Column(JSON, nullable=True)
    
    # Chemical form and nitrogen distribution
    chemical_form = Column(String, nullable=True)
    n_ammoniacal_pct = Column(Float, default=0.0)
    n_nitric_pct = Column(Float, default=0.0)
    n_ureic_pct = Column(Float, default=0.0)
    
    # Physical state
    physical_state = Column(String, nullable=False)
    density_g_ml = Column(Float, nullable=True)
    
    # Solubility and chemistry
    solubility_g_l = Column(Float, nullable=True)
    ph_solution_1pct = Column(Float, nullable=True)
    ec_typical_dS_m = Column(Float, nullable=True)
    salt_index = Column(Float, nullable=True)
    chloride_content_pct = Column(Float, default=0.0)
    
    # Acidity/basicity
    caco3_equivalent_kg_per_100kg = Column(Float, default=0.0)
    
    # Urea specific
    biuret_pct = Column(Float, default=0.0)
    
    # Pricing module alias (maps to user_fertilizer_prices.fertilizer_id)
    pricing_alias = Column(String, nullable=True, index=True)
    
    # Application systems
    for_soil = Column(Boolean, default=True)
    for_fertigation = Column(Boolean, default=False)
    for_foliar = Column(Boolean, default=False)
    
    # Foliar application limits
    max_foliar_dose_g_l = Column(Float, nullable=True)
    max_foliar_dose_l_ha = Column(Float, nullable=True)
    safe_interval_days = Column(Integer, nullable=True)
    
    # Compatibility and restrictions
    compatibility_notes = Column(Text, nullable=True)
    incompatible_with = Column(JSON, nullable=True)
    sensitive_crops = Column(JSON, nullable=True)
    
    # Economic
    cost_per_unit = Column(Float, nullable=True)
    unit = Column(String, default="kg")
    
    # Regulatory
    restricted = Column(Boolean, default=False)
    hazard_phrases = Column(JSON, nullable=True)
    
    # Additional properties
    prnt_pct = Column(Float, nullable=True)
    particle_size_mm = Column(Float, nullable=True)
    shelf_life_months = Column(Integer, nullable=True)
    storage_conditions = Column(Text, nullable=True)
    
    # Recommendations
    recommended_stages = Column(JSON, nullable=True)
    efficiency_factor = Column(Float, default=1.0)
    
    # Metadata
    manufacturer = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    technical_sheet_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Report(Base):
    """Report model - stores generated PDF reports for projects."""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    report_type = Column(String, nullable=False)  # 'project_complete', 'soil_analysis', 'fertilization_plan', etc.
    file_path = Column(String, nullable=False)  # Relative path to PDF file
    file_size_bytes = Column(Integer, nullable=True)
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    report_metadata = Column(JSON, nullable=True)  # Additional report metadata (crop, area, calculations, etc.)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    project = relationship("Project", back_populates="reports")


class Grower(Base):
    """Grower/Advisor model - represents agricultural advisors available for consultations."""
    __tablename__ = "growers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    specialty = Column(String, nullable=False)
    experience_years = Column(Integer, default=0)
    bio = Column(Text, nullable=True)
    certifications = Column(JSON, nullable=True)
    languages = Column(JSON, nullable=True)
    research_lines = Column(JSON, nullable=True)
    location = Column(String, nullable=True)
    rating = Column(Float, default=5.0)
    total_consultations = Column(Integer, default=0)
    price_usd = Column(Float, default=30.0)
    price_mxn = Column(Float, default=600.0)
    is_active = Column(Boolean, default=True)
    is_self_registered = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="grower_profile")
    availabilities = relationship("GrowerAvailability", back_populates="grower", cascade="all, delete-orphan")
    appointments = relationship("AdvisoryAppointment", back_populates="grower")
    messages = relationship("GrowerMessage", back_populates="grower", cascade="all, delete-orphan")


class GrowerAvailability(Base):
    """Grower availability slots for scheduling appointments."""
    __tablename__ = "grower_availabilities"
    
    id = Column(Integer, primary_key=True, index=True)
    grower_id = Column(Integer, ForeignKey("growers.id", ondelete="CASCADE"), nullable=False)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="available")  # available, reserved, blocked
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    grower = relationship("Grower", back_populates="availabilities")
    appointment = relationship("AdvisoryAppointment", back_populates="availability", uselist=False)


class AdvisoryAppointment(Base):
    """Advisory appointment model - represents booked consultations."""
    __tablename__ = "advisory_appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    grower_id = Column(Integer, ForeignKey("growers.id", ondelete="SET NULL"), nullable=True)
    availability_id = Column(Integer, ForeignKey("grower_availabilities.id", ondelete="SET NULL"), nullable=True, unique=True)
    
    status = Column(String(30), default="pending")  # pending, awaiting_payment, paid, confirmed, completed, canceled, no_show
    price_usd = Column(Float, default=30.0)
    
    stripe_payment_intent_id = Column(String, nullable=True)
    stripe_checkout_session_id = Column(String, nullable=True)
    
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, default=60)
    
    meeting_url = Column(String, nullable=True)
    meeting_notes = Column(Text, nullable=True)
    user_notes = Column(Text, nullable=True)
    
    booked_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    
    meeting_password = Column(String, nullable=True)
    reminder_sent = Column(Boolean, default=False)
    
    user = relationship("User")
    grower = relationship("Grower", back_populates="appointments")
    availability = relationship("GrowerAvailability", back_populates="appointment")


class WaterAnalysis(Base):
    """Saved water analyses for reuse in hydroponic calculations."""
    __tablename__ = "water_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    source_type = Column(String(50), default="otro")  # pozo, municipal, rio, lluvia, otro
    saved_units = Column(String(10), default="meq")  # meq, ppm, mmol - unit used when saving
    
    # Anions (meq/L)
    anion_no3 = Column(Float, default=0.0)
    anion_h2po4 = Column(Float, default=0.0)
    anion_so42 = Column(Float, default=0.0)
    anion_hco3 = Column(Float, default=0.0)
    anion_cl = Column(Float, default=0.0)
    
    # Cations (meq/L)
    cation_nh4 = Column(Float, default=0.0)
    cation_k = Column(Float, default=0.0)
    cation_ca = Column(Float, default=0.0)
    cation_mg = Column(Float, default=0.0)
    cation_na = Column(Float, default=0.0)
    
    # Micronutrients (ppm)
    micro_fe = Column(Float, default=0.0)
    micro_mn = Column(Float, default=0.0)
    micro_zn = Column(Float, default=0.0)
    micro_cu = Column(Float, default=0.0)
    micro_b = Column(Float, default=0.0)
    micro_mo = Column(Float, default=0.0)
    
    # Additional properties
    ec = Column(Float, default=0.0)  # mS/cm
    ph = Column(Float, nullable=True)
    source_description = Column(String(255), nullable=True)  # e.g., "Pozo profundo", "Agua municipal"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User")


class UserSession(Base):
    """Active user sessions for anti-sharing enforcement (max 2 sessions per user)."""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    session_token = Column(String, unique=True, index=True, nullable=False)
    device_fingerprint = Column(String, nullable=True, index=True)
    device_name = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_reason = Column(String, nullable=True)
    
    user = relationship("User", back_populates="sessions")


class GrowerMessage(Base):
    """Messages between users and growers, only allowed for paid appointments."""
    __tablename__ = "grower_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    grower_id = Column(Integer, ForeignKey("growers.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("advisory_appointments.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sender_type = Column(String(10), nullable=False)  # 'user' or 'grower'
    message = Column(Text, nullable=True)  # Text message (optional if file is attached)
    is_read = Column(Boolean, default=False)
    
    # File attachment fields
    file_url = Column(String(500), nullable=True)  # URL to file in Object Storage
    file_name = Column(String(255), nullable=True)  # Original file name
    file_type = Column(String(50), nullable=True)  # 'image', 'document', 'pdf'
    file_size = Column(Integer, nullable=True)  # File size in bytes
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    grower = relationship("Grower", back_populates="messages")
    user = relationship("User")
    appointment = relationship("AdvisoryAppointment")


class Parcel(Base):
    """User-defined georeferenced parcels for soil analysis and irrigation calculations."""
    __tablename__ = "parcels"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    geometry_type = Column(String(50), nullable=False)  # Polygon, Rectangle
    geometry_coordinates = Column(JSON, nullable=False)  # GeoJSON coordinates
    
    area_hectares = Column(Float, nullable=True)
    center_lat = Column(Float, nullable=True)
    center_lon = Column(Float, nullable=True)
    
    crop_type = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    municipality = Column(String(100), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="parcels")
    irrigation_analyses = relationship("IrrigationAnalysis", back_populates="parcel", cascade="all, delete-orphan")


class IrrigationAnalysis(Base):
    """Saved irrigation analysis records for historical tracking and comparison."""
    __tablename__ = "irrigation_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parcel_id = Column(Integer, ForeignKey("parcels.id", ondelete="CASCADE"), nullable=True, index=True)
    
    name = Column(String(200), nullable=True)
    
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    crop_type = Column(String(100), nullable=False)
    irrigation_efficiency = Column(Float, nullable=False)
    
    geometry_geojson = Column(JSON, nullable=False)
    area_hectares = Column(Float, nullable=True)
    center_lat = Column(Float, nullable=True)
    center_lon = Column(Float, nullable=True)
    
    net_irrigation_mm = Column(Float, nullable=True)
    gross_irrigation_mm = Column(Float, nullable=True)
    etc_total_mm = Column(Float, nullable=True)
    etc_daily_mm = Column(Float, nullable=True)
    precipitation_total_mm = Column(Float, nullable=True)
    precipitation_effective_mm = Column(Float, nullable=True)
    
    ndvi_mean = Column(Float, nullable=True)
    kc_mean = Column(Float, nullable=True)
    
    water_cost_estimate = Column(Float, nullable=True)
    water_saved_m3 = Column(Float, nullable=True)
    money_saved = Column(Float, nullable=True)
    
    full_result = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="irrigation_analyses")
    parcel = relationship("Parcel", back_populates="irrigation_analyses")


class IrrigationAlert(Base):
    """Irrigation alerts configuration and history."""
    __tablename__ = "irrigation_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parcel_id = Column(Integer, ForeignKey("parcels.id", ondelete="CASCADE"), nullable=True, index=True)
    
    alert_type = Column(String(50), nullable=False)
    threshold_mm = Column(Float, nullable=True)
    threshold_etc_daily = Column(Float, nullable=True)
    
    is_active = Column(Boolean, default=True)
    notify_whatsapp = Column(Boolean, default=True)
    whatsapp_phone = Column(String(20), nullable=True)
    
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="irrigation_alerts")
    parcel = relationship("Parcel", backref="irrigation_alerts")


# ==================== FERTIIRRIGATION MODULE (Independent) ====================

class MySoilAnalysis(Base):
    """Saved soil analyses for fertirrigation calculations (independent module)."""
    __tablename__ = "my_soil_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    laboratory = Column(String(100), nullable=True)
    analysis_date = Column(DateTime(timezone=True), nullable=True)
    
    # Physical properties
    texture = Column(String(50), nullable=True)  # arena, franco, arcilla, etc.
    bulk_density = Column(Float, default=1.3)  # g/cm3
    depth_cm = Column(Float, default=30.0)  # cm
    
    # pH and EC
    ph = Column(Float, nullable=True)
    ec_ds_m = Column(Float, nullable=True)  # dS/m
    
    # Organic matter
    organic_matter_pct = Column(Float, nullable=True)  # %
    
    # Macronutrients
    n_total_pct = Column(Float, nullable=True)  # % Nitrogen total
    n_no3_ppm = Column(Float, nullable=True)  # ppm Nitrate-N
    n_nh4_ppm = Column(Float, nullable=True)  # ppm Ammonium-N
    p_ppm = Column(Float, nullable=True)  # ppm Phosphorus (Olsen/Bray)
    k_ppm = Column(Float, nullable=True)  # ppm Potassium
    
    # Secondary macronutrients
    ca_ppm = Column(Float, nullable=True)  # ppm Calcium
    mg_ppm = Column(Float, nullable=True)  # ppm Magnesium
    s_ppm = Column(Float, nullable=True)  # ppm Sulfur
    na_ppm = Column(Float, nullable=True)  # ppm Sodium
    
    # Cation Exchange Capacity
    cic_cmol_kg = Column(Float, nullable=True)  # cmol(+)/kg or meq/100g
    
    # Exchangeable bases (cmol/kg or meq/100g)
    ca_exch = Column(Float, nullable=True)
    mg_exch = Column(Float, nullable=True)
    k_exch = Column(Float, nullable=True)
    na_exch = Column(Float, nullable=True)
    
    # Micronutrients (ppm)
    fe_ppm = Column(Float, nullable=True)
    mn_ppm = Column(Float, nullable=True)
    zn_ppm = Column(Float, nullable=True)
    cu_ppm = Column(Float, nullable=True)
    b_ppm = Column(Float, nullable=True)
    
    # Carbonates
    caco3_pct = Column(Float, nullable=True)  # % Calcium carbonate
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="my_soil_analyses")


class FertiIrrigationCalculation(Base):
    """Saved fertiirrigation calculations (independent module)."""
    __tablename__ = "fertiirrigation_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    
    # References to analyses
    soil_analysis_id = Column(Integer, ForeignKey("my_soil_analyses.id", ondelete="SET NULL"), nullable=True)
    water_analysis_id = Column(Integer, ForeignKey("water_analyses.id", ondelete="SET NULL"), nullable=True)
    
    # Crop information
    crop_name = Column(String(100), nullable=False)
    crop_variety = Column(String(100), nullable=True)
    growth_stage = Column(String(50), nullable=True)
    
    # Irrigation parameters
    irrigation_system = Column(String(50), nullable=True)  # goteo, aspersion, gravedad
    irrigation_frequency_days = Column(Float, nullable=True)
    irrigation_volume_m3_ha = Column(Float, nullable=True)
    area_ha = Column(Float, nullable=True)
    
    # Target yields
    yield_target_ton_ha = Column(Float, nullable=True)
    
    # Calculation results (stored as JSON)
    input_data = Column(JSON, nullable=True)  # Complete input snapshot
    results = Column(JSON, nullable=True)  # Calculation results
    fertilizer_program = Column(JSON, nullable=True)  # Fertilization program by application
    warnings = Column(JSON, nullable=True)  # Warnings and recommendations
    
    # Summary metrics
    total_n_kg_ha = Column(Float, nullable=True)
    total_p2o5_kg_ha = Column(Float, nullable=True)
    total_k2o_kg_ha = Column(Float, nullable=True)
    total_cost_estimate = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="fertiirrigation_calculations")
    soil_analysis = relationship("MySoilAnalysis", backref="fertiirrigation_calculations")
    water_analysis = relationship("WaterAnalysis", backref="fertiirrigation_calculations")


class UserExtractionCurve(Base):
    """User-defined custom extraction curves for fertirrigation calculations."""
    __tablename__ = "user_extraction_curves"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    scientific_name = Column(String(150), nullable=True)
    description = Column(Text, nullable=True)
    
    cycle_days_min = Column(Integer, nullable=True)
    cycle_days_max = Column(Integer, nullable=True)
    yield_reference_ton_ha = Column(Float, nullable=True)
    
    total_n_kg_ha = Column(Float, nullable=True)
    total_p2o5_kg_ha = Column(Float, nullable=True)
    total_k2o_kg_ha = Column(Float, nullable=True)
    total_ca_kg_ha = Column(Float, nullable=True)
    total_mg_kg_ha = Column(Float, nullable=True)
    total_s_kg_ha = Column(Float, nullable=True)
    
    stages = Column(JSON, nullable=False, default=list)
    sensitivity_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", backref="user_extraction_curves")


class AgronomicQueryStatus(str, enum.Enum):
    """Status enum for agronomic support queries."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ANSWERED = "answered"
    CLOSED = "closed"


class AgronomicQuery(Base):
    """Agronomic support queries for Pro plan users (5/month limit)."""
    __tablename__ = "agronomic_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    subject = Column(String(200), nullable=False)
    question = Column(Text, nullable=False)
    crop = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    attachments = Column(JSON, nullable=True, default=list)
    
    status = Column(String(20), default="pending")
    
    response = Column(Text, nullable=True)
    responded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    assigned_grower_id = Column(Integer, ForeignKey("growers.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", foreign_keys=[user_id], backref="agronomic_queries")
    responder = relationship("User", foreign_keys=[responded_by])
    assigned_grower = relationship("Grower", foreign_keys=[assigned_grower_id])


class BlogPostStatus(str, enum.Enum):
    """Status enum for blog posts."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class BlogCategory(Base):
    """Blog categories for organizing articles."""
    __tablename__ = "blog_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    meta_title = Column(String(70), nullable=True)
    meta_description = Column(String(160), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    posts = relationship("BlogPost", back_populates="category")


class BlogTag(Base):
    """Blog tags for keyword organization."""
    __tablename__ = "blog_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    slug = Column(String(60), nullable=False, unique=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class BlogPostTag(Base):
    """Association table for blog posts and tags."""
    __tablename__ = "blog_post_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"), nullable=False)
    tag_id = Column(Integer, ForeignKey("blog_tags.id", ondelete="CASCADE"), nullable=False)


class BlogPost(Base):
    """Blog posts for SEO content marketing."""
    __tablename__ = "blog_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    title = Column(String(200), nullable=False)
    slug = Column(String(220), nullable=False, unique=True, index=True)
    excerpt = Column(String(300), nullable=True)
    content = Column(Text, nullable=False)
    
    featured_image = Column(String(500), nullable=True)
    featured_image_alt = Column(String(200), nullable=True)
    
    meta_title = Column(String(70), nullable=True)
    meta_description = Column(String(160), nullable=True)
    keywords = Column(String(300), nullable=True)
    canonical_url = Column(String(500), nullable=True)
    
    category_id = Column(Integer, ForeignKey("blog_categories.id", ondelete="SET NULL"), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(String(20), default="draft")
    
    views_count = Column(Integer, default=0)
    reading_time_minutes = Column(Integer, default=5)
    
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    category = relationship("BlogCategory", back_populates="posts")
    author = relationship("User", backref="blog_posts")
    tags = relationship("BlogTag", secondary="blog_post_tags", backref="posts")
