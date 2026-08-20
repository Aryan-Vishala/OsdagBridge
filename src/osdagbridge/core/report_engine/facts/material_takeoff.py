import logging
from typing import Optional, Dict, Any
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_TS_NO_OF_GIRDERS,
    KEY_TS_DECK_THICKNESS,
    KEY_TS_GIRDER_SPACING,
    KEY_SD_SECTION_PROP_AREA,
)
from osdagbridge.core.report_engine.facts import (
    TakeoffItem, StructuralSteelTakeoff, MaterialFacts, QuantityValue
)
from osdagbridge.core.report_engine.provenance import ProvenanceTracker, ValueSource

logger = logging.getLogger("osdagbridge.core.report_engine.facts.material_takeoff")


def _resolve_girder_value(source: dict, base_key: str, i: int = 0):
    candidates = [
        f"{base_key}.G{i + 1}.M1",
        base_key,
        f"{base_key}.G1.M1"
    ]
    for key in candidates:
        if key in source:
            return source[key]
    raise KeyError(base_key)


def build_material_facts(
    inputs: dict,
    outputs: dict,
    tracker: Optional[ProvenanceTracker] = None,
) -> MaterialFacts:
    span_val = inputs.get(KEY_SPAN)
    n_girders_val = inputs.get(KEY_TS_NO_OF_GIRDERS)

    if span_val is None or n_girders_val is None:
        return MaterialFacts(
            structural_steel=StructuralSteelTakeoff(None, None, None, None, None),
            concrete_volume=None,
            reinforcement_steel=None,
            shear_studs=None,
            crash_barrier=None,
        )

    try:
        span = float(span_val)
        n_girders = int(n_girders_val)
    except Exception:
        return MaterialFacts(
            structural_steel=StructuralSteelTakeoff(None, None, None, None, None),
            concrete_volume=None,
            reinforcement_steel=None,
            shear_studs=None,
            crash_barrier=None,
        )

    if span <= 0 or n_girders <= 0:
        return MaterialFacts(
            structural_steel=StructuralSteelTakeoff(None, None, None, None, None),
            concrete_volume=None,
            reinforcement_steel=None,
            shear_studs=None,
            crash_barrier=None,
        )

    # 1. Concrete deck and 2. Reinforcement
    concrete_deck = None
    rebar_deck = None
    overall_width_val = inputs.get("typical_section.overall_bridge_width")
    deck_thickness_val = inputs.get(KEY_TS_DECK_THICKNESS)

    if overall_width_val is not None and deck_thickness_val is not None:
        try:
            overall_width = float(overall_width_val)
            deck_thickness = float(deck_thickness_val) / 1000.0  # mm to m
            if overall_width > 0 and deck_thickness > 0:
                concrete_vol = span * overall_width * deck_thickness
                concrete_deck = TakeoffItem(
                    item_description="Concrete (M40) for Deck Slab",
                    unit_volume=QuantityValue(concrete_vol, "m³"),
                    quantity=1,
                    total_volume=QuantityValue(concrete_vol, "m³"),
                    unit_weight=QuantityValue(concrete_vol * 2.5, "MT"),
                    total_weight=QuantityValue(concrete_vol * 2.5, "MT"),
                    formula_components=(
                        QuantityValue(overall_width, "m"),
                        QuantityValue(deck_thickness, "m"),
                        QuantityValue(span, "m")
                    )
                )

                rebar_wt_kg = concrete_vol * 120.0
                rebar_vol = rebar_wt_kg / 7850.0
                rebar_area = rebar_vol / span if span > 0 else 0.0
                rebar_deck = TakeoffItem(
                    item_description="Reinforcement Steel (Fe 500)",
                    unit_volume=QuantityValue(rebar_vol, "m³"),
                    quantity=1,
                    total_volume=QuantityValue(rebar_vol, "m³"),
                    unit_weight=QuantityValue(rebar_wt_kg / 1000.0, "MT"),
                    total_weight=QuantityValue(rebar_wt_kg / 1000.0, "MT"),
                    formula_components=(
                        QuantityValue(rebar_area, "m²"),
                        QuantityValue(span, "m")
                    )
                )
        except Exception:
            pass

    # 3. Steel Girders
    girder_area = 0.0
    try:
        girder_area = float(_resolve_girder_value(inputs, "member_properties.girder_details.section_properties.area", 0))
    except Exception:
        pass

    if girder_area <= 0:
        try:
            dw = float(_resolve_girder_value(inputs, "member_properties.girder_details.section_input.web_depth", 0))
            tw = float(_resolve_girder_value(inputs, "member_properties.girder_details.section_input.web_thickness", 0))
            bft = float(_resolve_girder_value(inputs, "member_properties.girder_details.section_input.top_flange_width", 0))
            tft = float(_resolve_girder_value(inputs, "member_properties.girder_details.section_input.top_flange_thickness", 0))
            bfb = float(_resolve_girder_value(inputs, "member_properties.girder_details.section_input.bottom_flange_width", 0))
            tfb = float(_resolve_girder_value(inputs, "member_properties.girder_details.section_input.bottom_flange_thickness", 0))
            girder_area = ((dw * tw) + (bft * tft) + (bfb * tfb)) / 1e6
        except Exception:
            pass

    if girder_area <= 0:
        area_cm2 = outputs.get(KEY_SD_SECTION_PROP_AREA) or outputs.get("steeldesign.details.section_properties.area")
        if area_cm2 is not None:
            try:
                girder_area = float(area_cm2) / 10000.0  # cm² to m²
            except Exception:
                pass

    girder_item = None
    if girder_area > 0:
        girder_vol = girder_area * span
        total_girder_mass = 0.0
        for gi in range(n_girders):
            try:
                mass_per_m = float(_resolve_girder_value(inputs, "member_properties.girder_details.section_properties.mass", gi))
                total_girder_mass += mass_per_m * span
            except Exception:
                total_girder_mass += girder_area * span * 7850.0

        girder_total_vol = n_girders * girder_vol
        single_girder_wt = (total_girder_mass / n_girders) / 1000.0
        total_girder_wt = total_girder_mass / 1000.0

        girder_item = TakeoffItem(
            item_description="Structural Steel (IS 2062) for Girders",
            unit_volume=QuantityValue(girder_vol, "m³"),
            quantity=n_girders,
            total_volume=QuantityValue(girder_total_vol, "m³"),
            unit_weight=QuantityValue(single_girder_wt, "MT"),
            total_weight=QuantityValue(total_girder_wt, "MT"),
            formula_components=(
                QuantityValue(girder_area, "m²"),
                QuantityValue(span, "m")
            )
        )

    # 4. Shear Studs
    shear_studs = None
    spacing_mm = 0.0
    studs_per_sec = 0
    stud_d = 0.0
    stud_h_mm = 0.0

    spacing_val = outputs.get("steeldesign.details.shear.longitudinal_spacing")
    studs_val = outputs.get("steeldesign.details.shear.studs_per_section")
    stud_d_val = outputs.get("steeldesign.details.shear.diameter") or inputs.get("design_options.shear_studs.diameter")
    stud_h_val = outputs.get("steeldesign.details.shear.height") or inputs.get("design_options.shear_studs.height")

    if spacing_val is not None and studs_val is not None and stud_d_val is not None and stud_h_val is not None:
        try:
            spacing_mm = float(spacing_val)
            studs_per_sec = int(studs_val)
            stud_d = float(stud_d_val)
            stud_h_mm = float(stud_h_val)
        except Exception:
            pass

    if spacing_mm > 0.0 and studs_per_sec > 0 and stud_d > 0.0 and stud_h_mm > 0.0:
        stud_h = stud_h_mm / 1000.0
        n_sections = int(span * 1000.0 / spacing_mm) + 1
        total_studs = n_girders * studs_per_sec * n_sections
        stud_area = (3.14159 * (stud_d / 1000.0) ** 2) / 4.0
        stud_vol = stud_area * stud_h
        studs_total_vol = total_studs * stud_vol
        single_stud_wt = stud_vol * 7.85
        total_studs_wt = studs_total_vol * 7.85

        shear_studs = TakeoffItem(
            item_description="Shear Stud Connectors",
            unit_volume=QuantityValue(stud_vol, "m³"),
            quantity=total_studs,
            total_volume=QuantityValue(studs_total_vol, "m³"),
            unit_weight=QuantityValue(single_stud_wt, "MT"),
            total_weight=QuantityValue(total_studs_wt, "MT"),
            formula_components=(
                QuantityValue(stud_area, "m²"),
                QuantityValue(stud_h, "m")
            )
        )

    # 5. Cross Bracing
    cb_top, cb_bot, cb_diag = None, None, None
    bracing_area = 0.0
    bracing_len = 0.0
    bracing_area_val = outputs.get("transverse_member_design.cb.section_properties.bracing.G1G2.A")
    cb_forces = outputs.get("crossbracing_forces_dict") or {}
    cb_geom = cb_forces.get("geometry") or {}
    bracing_len_val = cb_geom.get("diagonal_length_m")

    if bracing_area_val is not None and bracing_len_val is not None:
        try:
            bracing_area = float(bracing_area_val) / 10000.0  # cm² to m²
            bracing_len = float(bracing_len_val)
        except Exception:
            pass

    spacing_val = inputs.get(KEY_TS_GIRDER_SPACING)
    spacing = 0.0
    if spacing_val is not None:
        try:
            spacing = float(spacing_val)
        except Exception:
            pass

    if bracing_area > 0.0 and bracing_len > 0.0 and spacing > 0.0:
        cb_spacing_val = cb_geom.get("cb_spacing_m")
        cb_spacing = 0.0
        if cb_spacing_val is not None:
            try:
                cb_spacing = float(cb_spacing_val)
            except Exception:
                pass
                
        if cb_spacing > 0.0:
            n_panels = max(1, round(span / cb_spacing) - 1)
        else:
            n_panels = max(3, int(span / 5.0))

        # Top Chord
        top_chord_qty = (n_girders - 1) * n_panels
        top_chord_vol_single = bracing_area * spacing
        cb_top = TakeoffItem(
            item_description="Cross Bracing - Top Chord",
            unit_volume=QuantityValue(top_chord_vol_single, "m³"),
            quantity=top_chord_qty,
            total_volume=QuantityValue(top_chord_qty * top_chord_vol_single, "m³"),
            unit_weight=QuantityValue(top_chord_vol_single * 7.85, "MT"),
            total_weight=QuantityValue(top_chord_qty * top_chord_vol_single * 7.85, "MT"),
            formula_components=(QuantityValue(bracing_area, "m²"), QuantityValue(spacing, "m"))
        )

        # Bottom Chord
        bot_chord_qty = (n_girders - 1) * n_panels
        bot_chord_vol_single = bracing_area * spacing
        cb_bot = TakeoffItem(
            item_description="Cross Bracing - Bottom Chord",
            unit_volume=QuantityValue(bot_chord_vol_single, "m³"),
            quantity=bot_chord_qty,
            total_volume=QuantityValue(bot_chord_qty * bot_chord_vol_single, "m³"),
            unit_weight=QuantityValue(bot_chord_vol_single * 7.85, "MT"),
            total_weight=QuantityValue(bot_chord_qty * bot_chord_vol_single * 7.85, "MT"),
            formula_components=(QuantityValue(bracing_area, "m²"), QuantityValue(spacing, "m"))
        )

        # Diagonal
        diags_qty = (n_girders - 1) * n_panels * 2
        diag_vol_single = bracing_area * bracing_len
        cb_diag = TakeoffItem(
            item_description="Cross Bracing - Diagonal Chord",
            unit_volume=QuantityValue(diag_vol_single, "m³"),
            quantity=diags_qty,
            total_volume=QuantityValue(diags_qty * diag_vol_single, "m³"),
            unit_weight=QuantityValue(diag_vol_single * 7.85, "MT"),
            total_weight=QuantityValue(diags_qty * diag_vol_single * 7.85, "MT"),
            formula_components=(QuantityValue(bracing_area, "m²"), QuantityValue(bracing_len, "m"))
        )

    # 6. Crash Barrier
    crash_barrier = None
    cb_area = 0.0
    cb_area_val = inputs.get("typical_section.crash_barrier.area")
    
    if cb_area_val is not None:
        try:
            cb_area = float(cb_area_val) / 1e6
        except Exception:
            pass
    
    if cb_area > 0.0:
        cb_vol = cb_area * span
        cb_total_vol = 2 * cb_vol
        crash_barrier = TakeoffItem(
            item_description="Crash Barrier",
            unit_volume=QuantityValue(cb_vol, "m³"),
            quantity=2,
            total_volume=QuantityValue(cb_total_vol, "m³"),
            unit_weight=QuantityValue(cb_vol * 2.5, "MT"),
            total_weight=QuantityValue(cb_total_vol * 2.5, "MT"),
            formula_components=(
                QuantityValue(cb_area, "m²"),
                QuantityValue(span, "m")
            )
        )

    # Note: End Diaphragms intentionally omitted (extracted as None)
    mat_facts = MaterialFacts(
        structural_steel=StructuralSteelTakeoff(
            girders=girder_item,
            cross_bracing_top=cb_top,
            cross_bracing_bot=cb_bot,
            cross_bracing_diag=cb_diag,
            end_diaphragms=None
        ),
        concrete_volume=concrete_deck,
        reinforcement_steel=rebar_deck,
        shear_studs=shear_studs,
        crash_barrier=crash_barrier
    )

    if tracker:
        if girder_item and girder_item.total_weight:
            tracker.record(
                fact_name="material_takeoff.structural_steel.girders_weight",
                source=ValueSource.DERIVED,
                source_key="calculated_girder_weight",
                source_value=girder_item.total_weight.value,
                extracted_value=girder_item.total_weight.value,
                target_unit="MT",
                transform="sum(girder_volume * 7.85)",
            )
        if concrete_deck and concrete_deck.total_volume:
            tracker.record(
                fact_name="material_takeoff.concrete_deck.total_volume",
                source=ValueSource.DERIVED,
                source_key="calculated_deck_volume",
                source_value=concrete_deck.total_volume.value,
                extracted_value=concrete_deck.total_volume.value,
                target_unit="m³",
                transform="deck_area * span",
            )
        if rebar_deck and rebar_deck.total_weight:
            tracker.record(
                fact_name="material_takeoff.reinforcement_steel.total_weight",
                source=ValueSource.DERIVED,
                source_key="calculated_rebar_weight",
                source_value=rebar_deck.total_weight.value,
                extracted_value=rebar_deck.total_weight.value,
                target_unit="MT",
                transform="deck_volume * 160 kg/m³ / 1000",
            )

    return mat_facts
