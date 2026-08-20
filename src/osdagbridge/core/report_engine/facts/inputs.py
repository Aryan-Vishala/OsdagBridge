from typing import Dict, Any, Optional
from osdagbridge.core.report_engine.facts import InputFacts, QuantityValue
from osdagbridge.core.report_engine.provenance import ProvenanceTracker, ValueSource


def build_input_facts(
    raw_input_dict: Dict[str, Any],
    tracker: Optional[ProvenanceTracker] = None,
) -> InputFacts:
    """Build InputFacts from the raw production payload.inputs with provenance tracking."""

    def _qv(key: str, unit: str = "") -> QuantityValue | None:
        v = raw_input_dict.get(key)
        if v in (None, ""):
            if tracker:
                tracker.record(
                    fact_name=f"inputs.{key}",
                    source=ValueSource.INPUT_DICT,
                    source_key=key,
                    source_value=None,
                    extracted_value=None,
                    target_unit=unit,
                    transform="missing",
                )
            return None
        try:
            val = float(v)
        except (ValueError, TypeError):
            val = v
        
        if tracker:
            tracker.record(
                fact_name=f"inputs.{key}",
                source=ValueSource.INPUT_DICT,
                source_key=key,
                source_value=v,
                extracted_value=val,
                target_unit=unit,
                transform="none",
            )
        return QuantityValue(value=val, unit=unit)

    # Map basic geometry
    geometry = {}
    if _qv("structure.type"): geometry["structure.type"] = _qv("structure.type")
    if _qv("geometry.span"): geometry["span"] = _qv("geometry.span", "m")
    if _qv("geometry.carriageway_width"): geometry["carriageway_width"] = _qv("geometry.carriageway_width", "m")
    if _qv("geometry.skew_angle"): geometry["skew_angle"] = _qv("geometry.skew_angle", "°")
    if _qv("geometry.include_median"): geometry["include_median"] = _qv("geometry.include_median")
    if _qv("geometry.footpath"): geometry["footpath"] = _qv("geometry.footpath")

    # Map weather and location
    weather = {}
    if _qv("latitude"): weather["latitude"] = _qv("latitude")
    if _qv("longitude"): weather["longitude"] = _qv("longitude")
    if _qv("seismic_zone"): weather["seismic_zone"] = _qv("seismic_zone")
    if _qv("wind_speed"): weather["wind_speed"] = _qv("wind_speed", "m/s")
    if _qv("shade_temp_max"): weather["shade_temp_max"] = _qv("shade_temp_max", "°C")
    if _qv("shade_temp_min"): weather["shade_temp_min"] = _qv("shade_temp_min", "°C")

    # Map material
    material = {}
    if _qv("material.girder"): material["girder"] = _qv("material.girder")
    if _qv("material.cross_bracing"): material["cross_bracing"] = _qv("material.cross_bracing")
    if _qv("material.end_diaphragm"): material["end_diaphragm"] = _qv("material.end_diaphragm")
    if _qv("material.deck"): material["deck"] = _qv("material.deck")

    # Map typical section
    section = {}
    if _qv("typical_section.overall_bridge_width"): section["overall_bridge_width"] = _qv("typical_section.overall_bridge_width", "m")
    if _qv("typical_section.girder_spacing"): section["girder_spacing"] = _qv("typical_section.girder_spacing", "m")
    if _qv("typical_section.deck_overhang"): section["deck_overhang"] = _qv("typical_section.deck_overhang", "m")
    if _qv("typical_section.deck_thickness"): section["deck_thickness"] = _qv("typical_section.deck_thickness", "mm")
    if _qv("typical_section.footpath_width"): section["footpath_width"] = _qv("typical_section.footpath_width", "m")

    return InputFacts(
        geometry=geometry,
        section=section,
        weather=weather,
        material=material,
    )

