# =============================================================================
# ReportFacts — Engineering truth extracted from UI / analysis.
#
# Rules:
#   - All fact dataclasses are frozen after creation.
#   - QuantityValue is purely value + unit. No display() logic here.
#   - None means "data unavailable". 0.0 means "genuinely zero".
#   - Never use ``or`` to default engineering values.
# =============================================================================

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional



# ---------------------------------------------------------------------------
# Shared primitive
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class QuantityValue:
    """Numeric engineering value with unit.

    ``None`` for value means the datum is unavailable.
    ``0.0`` means the measurement is genuinely zero.

    Rendering (display formatting) is the responsibility of the renderer,
    never of this class.
    """

    value: Optional[float]
    unit: str


# ---------------------------------------------------------------------------
# Root container
# ---------------------------------------------------------------------------

@dataclass
class ReportFacts:
    """Top-level collection of all engineering fact categories."""

    metadata: "FactMetadata"
    loads: Optional["LoadFacts"] = None
    utilization: Optional["UtilizationFacts"] = None
    materials: Optional["MaterialFacts"] = None
    inputs: Optional["InputFacts"] = None
    design_check_data: Optional["DesignCheckData"] = None
    provenance: Optional[Any] = None

    # Migration bridge: raw dicts needed by legacy chapter functions.
    # These will be removed once all chapters are fully migrated.
    raw_input_dict: Optional[Dict] = None
    raw_output_dict: Optional[Dict] = None
    design_checks: Optional[List[str]] = None

    def provenance_report(self) -> str:
        """Format and return the data provenance report."""
        if self.provenance:
            return self.provenance.format_report()
        return "No provenance tracker attached to ReportFacts."


@dataclass
class FactMetadata:
    project_name: str
    project_location: str
    designer: str
    client: str
    company: str
    report_date: str = ""
    reviewer: str = ""
    subtitle: str = ""


# ---------------------------------------------------------------------------
# Load facts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DeadLoadFact:
    steel_density: QuantityValue
    concrete_density: QuantityValue
    self_weight_factor: QuantityValue


@dataclass(frozen=True)
class SurfacingLoadFact:
    wearing_course_material: str
    wearing_course_thickness: QuantityValue
    crash_barrier_load: QuantityValue
    railing_load: QuantityValue


@dataclass(frozen=True)
class VehicleLiveLoadFact:
    vehicle_class: str
    impact_factor: Optional[QuantityValue] = None
    centrifugal_force: Optional[QuantityValue] = None


@dataclass(frozen=True)
class FootwayLoadFact:
    load_type: str
    intensity: QuantityValue


@dataclass(frozen=True)
class LiveLoadFact:
    vehicles: tuple[VehicleLiveLoadFact, ...] = ()
    braking_force: Optional[QuantityValue] = None
    footway_load: Optional[FootwayLoadFact] = None


@dataclass(frozen=True)
class WindLoadFact:
    basic_wind_speed: QuantityValue
    terrain_type: str
    avg_exposed_height: QuantityValue
    hourly_mean_wind_speed: QuantityValue
    hourly_wind_pressure: QuantityValue
    transverse_wind_force: QuantityValue
    longitudinal_wind_force: QuantityValue
    vertical_wind_force: QuantityValue


@dataclass(frozen=True)
class SeismicLoadFact:
    seismic_zone: str
    zone_factor: QuantityValue
    importance_factor: QuantityValue
    soil_type: str
    spectral_coeff: QuantityValue
    horizontal_coeff: QuantityValue
    vertical_coeff: QuantityValue
    horizontal_force_long: Optional[QuantityValue] = None
    horizontal_force_trans: Optional[QuantityValue] = None


@dataclass(frozen=True)
class TemperatureLoadFact:
    max_shade_temp: QuantityValue
    min_shade_temp: QuantityValue
    bridge_temp_min: QuantityValue
    bridge_temp_max: QuantityValue
    temp_rise: QuantityValue
    temp_fall: QuantityValue


@dataclass(frozen=True)
class LoadCombinationFact:
    combination_id: str
    load_cases: tuple[str, ...] = ()
    factors: tuple[tuple[str, Optional[float], Optional[float]], ...] = ()


@dataclass(frozen=True)
class LoadFacts:
    dead_load: DeadLoadFact
    surfacing_load: SurfacingLoadFact
    live_load: LiveLoadFact
    wind_load: WindLoadFact
    seismic_load: SeismicLoadFact
    temperature_load: TemperatureLoadFact
    load_combinations: tuple[LoadCombinationFact, ...] = ()


# ---------------------------------------------------------------------------
# Check status
# ---------------------------------------------------------------------------

class CheckStatus(Enum):
    """Semantic status for design checks. Renderer owns formatting."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    UNAVAILABLE = "unavailable"


# ---------------------------------------------------------------------------
# Design check facts (Chapter 5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GirderSectionProperties:
    """Table 5.1 — girder section properties."""
    girder_label: str
    depth: QuantityValue
    top_flange_width: QuantityValue
    bottom_flange_width: QuantityValue
    top_flange_thickness: QuantityValue
    bottom_flange_thickness: QuantityValue
    web_thickness: QuantityValue
    gross_area: QuantityValue
    moment_of_inertia: QuantityValue
    elastic_section_modulus: QuantityValue
    plastic_section_modulus: QuantityValue
    effective_slab_width: QuantityValue
    composite_iz: QuantityValue
    pna_depth: QuantityValue


@dataclass(frozen=True)
class GirderClassification:
    """Table 5.2 — section classification per IS 800 Table 2."""
    flange_slenderness: Optional[float] = None
    flange_class_limit: Optional[float] = None
    class_flange: str = ""
    web_slenderness: Optional[float] = None
    web_class_limit: Optional[float] = None
    class_web: str = ""
    section_class: str = ""


@dataclass(frozen=True)
class GirderFlexureCheck:
    """Table 5.3 — moment capacity check."""
    mu_applied: Optional[QuantityValue] = None
    md_capacity: Optional[QuantityValue] = None
    utilization_ratio: Optional[float] = None
    status: CheckStatus = CheckStatus.UNAVAILABLE


@dataclass(frozen=True)
class GirderShearCheck:
    """Table 5.4 — shear capacity check."""
    vu: Optional[QuantityValue] = None
    shear_av: Optional[QuantityValue] = None
    panel_cd: Optional[float] = None
    shear_kv: Optional[float] = None
    shear_lambda_w: Optional[float] = None
    shear_tau_b: Optional[QuantityValue] = None
    shear_vcr: Optional[QuantityValue] = None
    utilization_ratio: Optional[float] = None
    status: CheckStatus = CheckStatus.UNAVAILABLE


@dataclass(frozen=True)
class GirderInteractionCheck:
    """Table 5.5 — M-V and M-N interaction."""
    high_shear: str = ""
    mdv: Optional[QuantityValue] = None
    mv_ur: Optional[float] = None
    mv_status: CheckStatus = CheckStatus.UNAVAILABLE
    mn_axial: Optional[float] = None
    mn_moment: Optional[float] = None
    mn_ratio: Optional[float] = None
    mn_status: CheckStatus = CheckStatus.UNAVAILABLE


@dataclass(frozen=True)
class GirderLTBCheck:
    """Table 5.6 — lateral torsional buckling."""
    mcr: Optional[QuantityValue] = None
    ltb_lambda: Optional[float] = None
    ltb_chi: Optional[float] = None
    ltb_mb: Optional[QuantityValue] = None
    utilization_ratio: Optional[float] = None
    status: CheckStatus = CheckStatus.UNAVAILABLE


@dataclass(frozen=True)
class GirderStiffenerSummary:
    """Table 5.7 — stiffener design summary."""
    method: str = ""
    int_thick: Optional[QuantityValue] = None
    int_spacing: Optional[QuantityValue] = None
    end_thick: Optional[QuantityValue] = None
    end_count: Optional[int] = None
    long_stiff: str = ""


@dataclass(frozen=True)
class GirderIntermediateStiffenerCheck:
    """Table 5.8 — IS 800 Cl. 8.7.1.2 (conditional: Custom mode only)."""
    iys_min: Optional[QuantityValue] = None
    iys_prov: Optional[QuantityValue] = None
    iys_status: CheckStatus = CheckStatus.UNAVAILABLE
    fq: Optional[QuantityValue] = None
    fqd: Optional[QuantityValue] = None
    fqd_status: CheckStatus = CheckStatus.UNAVAILABLE


@dataclass(frozen=True)
class GirderBearingStiffenerCheck:
    """Table 5.9 — end panel stiffener checks."""
    wb_req: Optional[QuantityValue] = None
    wb_prov: Optional[QuantityValue] = None
    wb_status: CheckStatus = CheckStatus.UNAVAILABLE
    lc_req: Optional[QuantityValue] = None
    lc_prov: Optional[QuantityValue] = None
    lc_status: CheckStatus = CheckStatus.UNAVAILABLE
    ps_req: Optional[QuantityValue] = None
    ps_prov: Optional[QuantityValue] = None
    ps_status: CheckStatus = CheckStatus.UNAVAILABLE
    cb_req: Optional[QuantityValue] = None
    cb_prov: Optional[QuantityValue] = None
    cb_status: CheckStatus = CheckStatus.UNAVAILABLE


@dataclass(frozen=True)
class GirderDeflectionCheck:
    """Table 5.10 — serviceability deflection."""
    allow_live: Optional[QuantityValue] = None
    allow_total: Optional[QuantityValue] = None
    actual_live: Optional[QuantityValue] = None
    actual_total: Optional[QuantityValue] = None
    live_status: CheckStatus = CheckStatus.UNAVAILABLE
    total_status: CheckStatus = CheckStatus.UNAVAILABLE


@dataclass(frozen=True)
class GirderStressCheck:
    """Table 5.11 — SLS stress limitation."""
    allowable_stress: Optional[QuantityValue] = None
    actual_stress: Optional[QuantityValue] = None
    status: CheckStatus = CheckStatus.UNAVAILABLE


@dataclass(frozen=True)
class GirderFatigueCheck:
    """Table 5.12 — fatigue assessment."""
    stress_range: Optional[QuantityValue] = None
    fatigue_limit: Optional[QuantityValue] = None
    utilization_ratio: Optional[float] = None
    status: CheckStatus = CheckStatus.UNAVAILABLE


@dataclass(frozen=True)
class GirderDesignSummary:
    """Table 5.13 — per-girder DCR summary."""
    governing_lc: str = ""
    controlling_check: str = ""
    demand: Optional[QuantityValue] = None
    capacity: Optional[QuantityValue] = None
    dcr: Optional[float] = None
    status: CheckStatus = CheckStatus.UNAVAILABLE


@dataclass(frozen=True)
class GirderDesignData:
    """Complete design data for one girder (Tables 5.1–5.13)."""
    girder_label: str
    section_properties: GirderSectionProperties
    classification: GirderClassification
    flexure: GirderFlexureCheck
    shear: GirderShearCheck
    interaction: GirderInteractionCheck
    ltb: GirderLTBCheck
    stiffener_summary: GirderStiffenerSummary
    intermediate_stiffener: Optional[GirderIntermediateStiffenerCheck] = None
    bearing_stiffener: GirderBearingStiffenerCheck = field(default_factory=GirderBearingStiffenerCheck)
    deflection: GirderDeflectionCheck = field(default_factory=GirderDeflectionCheck)
    stress: GirderStressCheck = field(default_factory=GirderStressCheck)
    fatigue: GirderFatigueCheck = field(default_factory=GirderFatigueCheck)
    summary: GirderDesignSummary = field(default_factory=GirderDesignSummary)


# ---------------------------------------------------------------------------
# Utilization facts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UtilizationFact:
    component: str
    demand: Optional[QuantityValue] = None
    capacity: Optional[QuantityValue] = None
    utilization_ratio: Optional[float] = None
    governing_case: str = ""
    status: str = ""


@dataclass
class UtilizationFacts:
    items: List[UtilizationFact] = field(default_factory=list)
    threshold: float = 1.0


# ---------------------------------------------------------------------------
# Material facts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MaterialQuantityFact:
    item: str
    volume: QuantityValue
    quantity: QuantityValue
    total_volume: QuantityValue
    weight: QuantityValue
    total_weight: QuantityValue


@dataclass
class MaterialFacts:
    quantities: List[MaterialQuantityFact] = field(default_factory=list)
    # Chart data — raw floats. None = unavailable.
    structural_steel_mt: Dict[str, Optional[float]] = field(default_factory=dict)
    concrete_volume_m3: Optional[float] = None
    reinforcement_mt: Optional[float] = None


# ---------------------------------------------------------------------------
# Input facts
# ---------------------------------------------------------------------------

@dataclass
class InputFacts:
    geometry: Dict[str, QuantityValue] = field(default_factory=dict)
    material: Dict[str, QuantityValue] = field(default_factory=dict)
    section: Dict[str, QuantityValue] = field(default_factory=dict)
    weather: Dict[str, QuantityValue] = field(default_factory=dict)
    design_options: Dict[str, QuantityValue] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Shear Connector Data (Phase 5B.1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ShearConnectorSpacing:
    required: Optional[QuantityValue] = None
    provided: Optional[QuantityValue] = None
    status: CheckStatus = CheckStatus.UNAVAILABLE

@dataclass(frozen=True)
class ShearConnectorData:
    """Tables 5.14-5.16"""
    # 5.14 Capacity
    design_resistance_qu: Optional[QuantityValue] = None
    fatigue_resistance_qr: Optional[QuantityValue] = None
    
    # 5.15 Spacing
    uls_shear: ShearConnectorSpacing = field(default_factory=ShearConnectorSpacing)
    full_composite: ShearConnectorSpacing = field(default_factory=ShearConnectorSpacing)
    sls_fatigue: ShearConnectorSpacing = field(default_factory=ShearConnectorSpacing)
    max_limit: ShearConnectorSpacing = field(default_factory=ShearConnectorSpacing)
    
    # 5.16 Transverse Shear & Detailing
    vl_longitudinal: Optional[QuantityValue] = None
    vrd_capacity: Optional[QuantityValue] = None
    transverse_ur: Optional[float] = None
    transverse_status: CheckStatus = CheckStatus.UNAVAILABLE
    
    min_transverse_reinf_req: Optional[QuantityValue] = None
    min_transverse_reinf_prov: Optional[QuantityValue] = None
    reinf_status: CheckStatus = CheckStatus.UNAVAILABLE
    
    stud_diameter: Optional[QuantityValue] = None
    stud_diameter_limit: Optional[QuantityValue] = None
    diameter_status: CheckStatus = CheckStatus.UNAVAILABLE
    
    edge_dist_prov: Optional[QuantityValue] = None
    edge_dist_req: Optional[QuantityValue] = None
    edge_dist_status: CheckStatus = CheckStatus.UNAVAILABLE


# ---------------------------------------------------------------------------
# Deck Design Data (Phase 5B.2)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DeckLoadingGeometry:
    effective_span: Optional[QuantityValue] = None
    thickness: Optional[QuantityValue] = None
    clear_cover_top: Optional[QuantityValue] = None
    clear_cover_bot: Optional[QuantityValue] = None
    concrete_grade: Optional[str] = None
    fck: Optional[QuantityValue] = None
    fctm: Optional[QuantityValue] = None
    reinf_grade: Optional[str] = None
    fy: Optional[QuantityValue] = None
    dead_load: Optional[QuantityValue] = None
    wheel_load: Optional[QuantityValue] = None
    tyre_width: Optional[QuantityValue] = None
    impact_factor: Optional[float] = None
    vehicle: Optional[str] = None

@dataclass(frozen=True)
class DeckFlexureCheck:
    # Sagging (Interior Panel)
    m_dl_sag: Optional[QuantityValue] = None
    m_ll_sag: Optional[QuantityValue] = None
    gamma_dl: Optional[float] = None
    gamma_ll: Optional[float] = None
    demand_sagging: Optional[QuantityValue] = None
    d_bot: Optional[QuantityValue] = None
    capacity_sagging: Optional[QuantityValue] = None
    status_sagging: CheckStatus = CheckStatus.UNAVAILABLE
    
    # Hogging (Support)
    demand_hogging: Optional[QuantityValue] = None
    required_top_steel: Optional[QuantityValue] = None
    capacity_hogging: Optional[QuantityValue] = None
    status_hogging: CheckStatus = CheckStatus.UNAVAILABLE
    
    # Cantilever Overhang
    has_overhang: bool = False
    overhang_length: Optional[QuantityValue] = None
    m_barrier: Optional[QuantityValue] = None
    m_dl_oh: Optional[QuantityValue] = None
    m_ll_oh: Optional[QuantityValue] = None
    demand_overhang: Optional[QuantityValue] = None
    capacity_overhang: Optional[QuantityValue] = None
    status_overhang: CheckStatus = CheckStatus.UNAVAILABLE

@dataclass(frozen=True)
class DeckShearCheck:
    # Punching Shear (IRC 112 Cl. 10.4.6)
    punching_ved_kn: Optional[QuantityValue] = None
    tyre_length: Optional[QuantityValue] = None
    tyre_width: Optional[QuantityValue] = None
    punching_c1: Optional[QuantityValue] = None
    punching_c2: Optional[QuantityValue] = None
    punching_u1: Optional[QuantityValue] = None
    punching_ved_mpa: Optional[QuantityValue] = None
    punching_vrdc_mpa: Optional[QuantityValue] = None
    punching_ur: Optional[float] = None
    punching_status: CheckStatus = CheckStatus.UNAVAILABLE
    
    # One-Way (Beam) Shear
    oneway_ved: Optional[QuantityValue] = None
    d_bot: Optional[QuantityValue] = None
    oneway_size_factor_k: Optional[float] = None
    oneway_rho_l: Optional[float] = None
    oneway_vrdc: Optional[QuantityValue] = None
    oneway_ur: Optional[float] = None
    oneway_status: CheckStatus = CheckStatus.UNAVAILABLE

@dataclass(frozen=True)
class DeckCrackWidthCheck:
    as_min: Optional[QuantityValue] = None
    dia_bot: Optional[QuantityValue] = None
    spc_bot: Optional[QuantityValue] = None
    as_bot: Optional[QuantityValue] = None
    calculated: Optional[QuantityValue] = None
    limit: Optional[QuantityValue] = None
    status: CheckStatus = CheckStatus.UNAVAILABLE

@dataclass(frozen=True)
class DeckDetailingCheck:
    required_bottom: Optional[QuantityValue] = None
    provided_bottom: Optional[QuantityValue] = None
    dia_bot: Optional[QuantityValue] = None
    spc_bot: Optional[QuantityValue] = None
    as_min: Optional[QuantityValue] = None
    spc_max: Optional[QuantityValue] = None
    
    required_dist: Optional[QuantityValue] = None
    provided_dist: Optional[QuantityValue] = None
    
    required_top: Optional[QuantityValue] = None
    provided_top: Optional[QuantityValue] = None
    
    min_cover: Optional[QuantityValue] = None
    top_cover: Optional[QuantityValue] = None
    bot_cover: Optional[QuantityValue] = None
    
    status_bottom: CheckStatus = CheckStatus.UNAVAILABLE
    status_dist: CheckStatus = CheckStatus.UNAVAILABLE
    status_top: CheckStatus = CheckStatus.UNAVAILABLE
    status_cover: CheckStatus = CheckStatus.UNAVAILABLE

@dataclass(frozen=True)
class DeckDesignData:
    """Tables 5.17a-g"""
    is_designed: bool = False
    loading: DeckLoadingGeometry = field(default_factory=DeckLoadingGeometry)
    flexure: DeckFlexureCheck = field(default_factory=DeckFlexureCheck)
    shear: DeckShearCheck = field(default_factory=DeckShearCheck)
    crack_width: DeckCrackWidthCheck = field(default_factory=DeckCrackWidthCheck)
    detailing: DeckDetailingCheck = field(default_factory=DeckDetailingCheck)


# ---------------------------------------------------------------------------
# Design check data (Chapter 5 — top-level container)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DesignCheckData:
    """Typed view of analysis results for Chapter 5.

    Phase 5A: only ``girders`` is populated.  Other fields will be added
    in Phases 5B (deck, shear connectors) and 5C (bracing, summary).
    """
    girders: tuple[GirderDesignData, ...] = ()
    shear_connectors: Optional[ShearConnectorData] = None
    deck: Optional[DeckDesignData] = None
    cross_bracing: Optional['CrossBracingData'] = None
    end_diaphragm: Optional['EndDiaphragmData'] = None
    summary: Optional['OverallSummaryData'] = None


# ---------------------------------------------------------------------------
# Cross Bracing & End Diaphragm Data (Phase 5C)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BracingMemberCheck:
    """Axial design check for a single member (diagonal or chord)."""
    demand: Optional[QuantityValue]
    capacity: Optional[QuantityValue]
    ur: Optional[float]
    status: CheckStatus
    governing_lc: Optional[str]
    connection_type: Optional[str]
    section: Optional[str]
    gross_area: Optional[QuantityValue] = None
    rmin: Optional[QuantityValue] = None
    effective_length: Optional[QuantityValue] = None
    slenderness: Optional[float] = None
    slenderness_limit: Optional[float] = None

@dataclass(frozen=True)
class BracingPanelData:
    """Design data for a single bracing panel (e.g. between G1-G2)."""
    pair_label: str
    diagonal_tension: Optional[BracingMemberCheck]
    diagonal_compression: Optional[BracingMemberCheck]
    chord_tension: Optional[BracingMemberCheck]
    chord_compression: Optional[BracingMemberCheck]
    slenderness_ur: Optional[float]
    slenderness_status: CheckStatus

@dataclass(frozen=True)
class CrossBracingData:
    panels: tuple[BracingPanelData, ...]

@dataclass(frozen=True)
class EndDiaphragmData:
    diaphragm_type: Optional[str]
    panels: tuple[BracingPanelData, ...]
    flexural_checks: Optional[tuple] = None


# ---------------------------------------------------------------------------
# Overall Summary Data (Phase 5C)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SummaryCheckRecord:
    """A single governing row in Table 5.22."""
    label: str
    demand: Optional[QuantityValue]
    capacity: Optional[QuantityValue]
    ur: Optional[float]
    status: CheckStatus
    governing_lc: Optional[str]
    note: Optional[str] = None

@dataclass(frozen=True)
class ComponentSummary:
    """Aggregates the worst-case checks for a major component."""
    component_name: str
    records: tuple[SummaryCheckRecord, ...]
    max_ur: Optional[float]
    status: CheckStatus

@dataclass(frozen=True)
class OverallSummaryData:
    girders: ComponentSummary
    deck: ComponentSummary
    cross_bracing: Optional[ComponentSummary]
    end_diaphragm: Optional[ComponentSummary]

# ---------------------------------------------------------------------------
# Material Take-off Data (Chapter 7)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TakeoffItem:
    item_description: str
    unit_volume: Optional[QuantityValue]
    quantity: Optional[int]
    total_volume: Optional[QuantityValue]
    unit_weight: Optional[QuantityValue]
    total_weight: Optional[QuantityValue]
    formula_components: Optional[tuple[QuantityValue, ...]] = None

@dataclass(frozen=True)
class StructuralSteelTakeoff:
    girders: Optional[TakeoffItem]
    cross_bracing_top: Optional[TakeoffItem]
    cross_bracing_bot: Optional[TakeoffItem]
    cross_bracing_diag: Optional[TakeoffItem]
    end_diaphragms: Optional[TakeoffItem]

@dataclass(frozen=True)
class MaterialFacts:
    structural_steel: StructuralSteelTakeoff
    concrete_volume: Optional[TakeoffItem]
    reinforcement_steel: Optional[TakeoffItem]
    shear_studs: Optional[TakeoffItem]
    crash_barrier: Optional[TakeoffItem]
