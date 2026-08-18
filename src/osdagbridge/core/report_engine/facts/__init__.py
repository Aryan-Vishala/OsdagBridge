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
    parameter: str
    value: QuantityValue


@dataclass(frozen=True)
class VehicleLiveLoadFact:
    vehicle_class: str
    impact_factor: Optional[QuantityValue] = None
    braking_load: Optional[QuantityValue] = None
    centrifugal_force: Optional[QuantityValue] = None


@dataclass(frozen=True)
class FootwayLoadFact:
    load_type: str
    intensity: QuantityValue


@dataclass(frozen=True)
class WindLoadFact:
    parameter: str
    value: QuantityValue


@dataclass(frozen=True)
class SeismicLoadFact:
    parameter: str
    value: QuantityValue


@dataclass(frozen=True)
class TemperatureLoadFact:
    parameter: str
    value: QuantityValue


@dataclass(frozen=True)
class LoadCombinationFact:
    combination_id: str
    load_cases: str


@dataclass
class LoadFacts:
    dead_loads: List[DeadLoadFact] = field(default_factory=list)
    vehicle_live_loads: List[VehicleLiveLoadFact] = field(default_factory=list)
    footway_loads: List[FootwayLoadFact] = field(default_factory=list)
    wind_loads: List[WindLoadFact] = field(default_factory=list)
    seismic_loads: List[SeismicLoadFact] = field(default_factory=list)
    temperature_loads: List[TemperatureLoadFact] = field(default_factory=list)
    load_combinations: List[LoadCombinationFact] = field(default_factory=list)


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
