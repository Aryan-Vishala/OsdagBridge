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
from typing import List, Optional, Dict


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

    # Migration bridge: raw dicts needed by legacy chapter functions.
    # These will be removed once all chapters are fully migrated.
    raw_input_dict: Optional[Dict] = None
    raw_output_dict: Optional[Dict] = None
    design_checks: Optional[List[str]] = None


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
