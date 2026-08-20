"""
Report Content Contract Test Suite
==================================

Enforces semantic structure, table sequences, required calculation rows, and
engineering notes on ReportDocument.

This contract tests the semantic AST directly (in-memory, sub-second execution)
without requiring pdflatex or filesystem side-effects.

Key Invariants Enforced:
1. Chapter 2 structure & required row labels (Traffic Lanes, Stiffeners, Flanges, Bracing).
2. Chapter 5 five-subsection hierarchy (5.1 Girder, 5.2 Deck, 5.3 Cross Bracing, 5.4 End Diaphragm, 5.5 Summary).
3. All intermediate calculation rows in Deck Slab design (Pigeaud flexure, Punching shear geometry, Crack width, Detailing).
4. End Diaphragm slenderness and capacity checks.
5. Correct conditional behavior across multiple bridge configurations (3, 5, 10 girders, with/without stiffeners/deck).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
from unittest.mock import MagicMock

# Mock openseespy if needed
sys.modules.setdefault("openseespy", MagicMock())
sys.modules.setdefault("openseespy.opensees", MagicMock())

from osdagbridge.core.report_engine.document import Chapter, DocumentComponent, Paragraph, ReportDocument, Section, Table
from osdagbridge.core.report_engine.document_builder import build_report_document
from osdagbridge.core.report_engine.facts import (
    CheckStatus,
    FactMetadata,
    GirderDesignData,
    InputFacts,
    QuantityValue,
    ReportFacts,
)
from osdagbridge.core.report_engine.facts.inputs import build_input_facts
from osdagbridge.core.report_engine.facts.loads import build_load_facts
from osdagbridge.core.report_engine.facts.design_checks import build_design_check_data
from osdagbridge.core.report_engine.facts.material_takeoff import build_material_facts
from osdagbridge.core.utils import common as c


# =============================================================================
# Navigational & Inspection Helpers
# =============================================================================

def find_chapter(doc: ReportDocument, number: int) -> Chapter:
    """Find a chapter by its number."""
    for ch in doc.chapters:
        if ch.number == number:
            return ch
    avail = [c.number for c in doc.chapters]
    raise AssertionError(f"Chapter {number} not found in document. Available chapters: {avail}")


def find_section(container: Chapter | Section, title_query: str) -> Section:
    """Find a section whose title contains title_query (case-insensitive)."""
    sections = getattr(container, "sections", [])
    for sec in sections:
        if title_query.lower() in sec.title.lower():
            return sec
    avail = [s.title for s in sections]
    raise AssertionError(f"Section matching '{title_query}' not found. Available sections: {avail}")


def get_all_tables(container: Chapter | Section) -> list[Table]:
    """Recursively gather all Table components from a chapter or section."""
    tables: list[Table] = []
    if isinstance(container, Chapter):
        for sec in container.sections:
            tables.extend(get_all_tables(sec))
    elif isinstance(container, Section):
        for comp in container.components:
            if isinstance(comp, Table):
                tables.append(comp)
    return tables


def find_table(container: Chapter | Section, caption_query: str) -> Table:
    """Find a table whose caption contains caption_query (case-insensitive)."""
    all_tables = get_all_tables(container)
    for tbl in all_tables:
        if caption_query.lower() in tbl.caption.lower():
            return tbl
    avail = [t.caption for t in all_tables]
    raise AssertionError(f"Table matching '{caption_query}' not found. Available tables: {avail}")


def _cell_to_text(cell: Any) -> str:
    """Convert any AST cell (string, Math, QuantityValue, list) to a searchable string."""
    if cell is None:
        return ""
    if isinstance(cell, str):
        return cell
    if isinstance(cell, (list, tuple)):
        return "".join(_cell_to_text(c) for c in cell)
    if hasattr(cell, "latex"):
        return str(cell.latex)
    if hasattr(cell, "value"):
        unit_str = f" {getattr(cell, 'unit', '')}".rstrip()
        return f"{cell.value}{unit_str}"
    return str(cell)


def table_has_row_label(table: Table, label_query: str) -> bool:
    """Check if any row in a flat or grouped table matches label_query."""
    q = label_query.lower()
    if table.rows:
        for row in table.rows:
            row_text = " | ".join(_cell_to_text(c).lower() for c in row)
            if q in row_text:
                return True
    if table.groups:
        for grp in table.groups:
            for row in grp.rows:
                row_text = " | ".join(_cell_to_text(c).lower() for c in row)
                if q in row_text:
                    return True
    return False


def table_contains_field(table: Table, field_name: str) -> bool:
    """Check if a field name appears as a row label, cell content, or column header."""
    q = field_name.lower()
    for col in table.columns:
        if q in _cell_to_text(col.header).lower():
            return True
    return table_has_row_label(table, field_name)


def assert_table_has_rows(table: Table, expected_labels: list[str]):
    """Assert that all expected row labels are present in the table."""
    missing = [lbl for lbl in expected_labels if not table_has_row_label(table, lbl)]
    assert not missing, f"Table '{table.caption}' is missing expected rows: {missing}"


def assert_table_has_fields(table: Table, expected_fields: list[str]):
    """Assert that all expected field names are present in rows or column headers."""
    missing = [f for f in expected_fields if not table_contains_field(table, f)]
    assert not missing, f"Table '{table.caption}' is missing expected fields: {missing}"


# =============================================================================
# Fixture Builders
# =============================================================================

def _build_synthetic_facts(
    n_girders: int = 5,
    has_intermediate_stiffeners: bool = True,
    has_deck: bool = True,
    has_cross_bracing: bool = True,
    has_end_diaphragm: bool = True,
    has_footpath: bool = True,
) -> ReportFacts:
    """Construct a realistic, fully populated ReportFacts fixture for contract testing."""
    girder_ids = [f"G{i}" for i in range(1, n_girders + 1)]
    
    inputs: Dict[str, Any] = {
        "project.name": f"Test Bridge {n_girders}G",
        "project.location": "Meerut, Uttar Pradesh",
        "designer.name": "Contract Tester",
        "client.name": "Osdag Team",
        "company.name": "FOSSEE IIT Bombay",
        "structure.type": "Highway Bridge",
        "geometry.span": "30.0",
        "geometry.carriageway_width": "10.0",
        "geometry.skew_angle": "0.0",
        "geometry.include_median": "No",
        "geometry.footpath": "Single Side" if has_footpath else "None",
        "latitude": "28.9845",
        "longitude": "77.7064",
        "seismic_zone": "IV",
        "wind_speed": "47.0",
        "shade_temp_max": "46.1",
        "shade_temp_min": "-2.5",
        "material.girder": "E 350A",
        "material.cross_bracing": "E 350A",
        "material.end_diaphragm": "E 350A",
        "material.deck": "M40",
        "typical_section.no_of_girders": str(n_girders),
        "typical_section.overall_bridge_width": "12.0",
        "typical_section.girder_spacing": "2.555",
        "typical_section.deck_thickness": "250.0",
        "typical_section.deck_overhang": "0.89",
        "typical_section.lane_details.lane_table_count": "3",
        c.KEY_DESIGN_MODE: "Custom" if has_intermediate_stiffeners else "Optimized",
        c.KEY_DS_STUD_DIAMETER: "19.0",
        c.KEY_DS_TOP_CLEAR_COVER: "50.0",
        c.KEY_DS_BOTTOM_CLEAR_COVER: "50.0",
        c.KEY_DECK_CONCRETE_GRADE_BASIC: "M40",
        c.KEY_DS_REINF_MATERIAL: "Fe 500D",
        "member_properties.cross_bracing_details.bracing_section_designation": "IS 100 x 100 x 10",
        "member_properties.cross_bracing_details.spacing": "15.0",
        "member_properties.end_diaphragm_details.type.G1G2.E1M1": "Cross Bracing",
        "member_properties.end_diaphragm_details.bracing_section_designation": "IS 100 x 100 x 10",
        "design_options_cont.partial_factor.yielding_and_buckling.gamma_m0": "1.10",
        "design_options_cont.partial_factor.ultimate_stress.gamma_m1": "1.25",
        "design_options_cont.partial_factor.concrete_basic.gamma_c_basic": "1.50",
        "design_options_cont.partial_factor.reinforcing_steel.gamma_s": "1.15",
        "design_options_cont.partial_factor.shear_connectors.gamma_v": "1.25",
        "design_options_cont.partial_factor.fatigue_load.gamma_flt": "1.00",
        "design_options_cont.partial_factor.fatigue_strength.gamma_mf": "1.00",
    }

    # Girder details in inputs
    for gid in girder_ids:
        inputs[f"typical_section.member_properties.girder_details.select_girder.{gid}"] = gid
        inputs[f"typical_section.member_properties.girder_details.member_id.{gid}.M1"] = f"{gid}M1"
        inputs[f"typical_section.member_properties.girder_details.web_thickness.{gid}"] = "10.0"
        inputs[f"typical_section.member_properties.girder_details.flange_width_top.{gid}"] = "510.0"
        inputs[f"typical_section.member_properties.girder_details.flange_thickness_top.{gid}"] = "22.0"
        inputs[f"typical_section.member_properties.girder_details.flange_width_bottom.{gid}"] = "510.0"
        inputs[f"typical_section.member_properties.girder_details.flange_thickness_bottom.{gid}"] = "22.0"
        inputs[f"typical_section.member_properties.girder_details.intermediate_stiffener.{gid}"] = "Yes" if has_intermediate_stiffeners else "No"
        inputs[f"typical_section.member_properties.girder_details.bearing_stiffener.{gid}"] = "Yes"
        inputs[f"typical_section.member_properties.girder_details.intermediate_stiffener_spacing.{gid}"] = "2440.0" if has_intermediate_stiffeners else ""
        inputs[f"typical_section.member_properties.girder_details.intermediate_stiffener_thickness.{gid}"] = "10.0" if has_intermediate_stiffeners else ""

    outputs: Dict[str, Any] = {
        c.KEY_SD_TOTAL_DEPTH: 1670.0,
        c.KEY_SD_TOP_FLANGE_WIDTH: 510.0,
        c.KEY_SD_BOTTOM_FLANGE_WIDTH: 510.0,
        c.KEY_SD_TOP_FLANGE_THICKNESS: 22.0,
        c.KEY_SD_BOTTOM_FLANGE_THICKNESS: 22.0,
        c.KEY_SD_WEB_THICKNESS: 10.0,
        c.KEY_SD_SECTION_PROP_AREA: 387.0,
        c.KEY_SD_SECTION_PROP_IZ: 1881960.0,
        c.KEY_SD_SECTION_PROP_ZZ: 22538.4,
        c.KEY_SD_SECTION_PROP_ZUZ: 25100.2,
        c.KEY_SD_EFFECTIVE_SLAB_WIDTH: 2555.0,
        c.KEY_SD_COMPOSITE_IZ: 4378590.0,
        c.KEY_SD_PNA_DEPTH: 259.8,
        c.KEY_SD_FLANGE_SLENDERNESS: 7.2,
        c.KEY_SD_FLANGE_CLASS_LIMIT: 9.4,
        c.KEY_SD_CLASS_FLANGE: "Class 1 (Plastic)",
        c.KEY_SD_WEB_SLENDERNESS: 160.0,
        c.KEY_SD_WEB_CLASS_LIMIT: 200.0,
        c.KEY_SD_CLASS_WEB: "Class 3 (Semi-Compact)",
        c.KEY_SD_SECTION_CLASS: "Class 3 (Semi-Compact)",
        c.KEY_SD_MU_APPLIED: 6540.0,
        c.KEY_SD_MD_CAPACITY: 7986.44,
        c.KEY_UTIL_FLEXURE: 81.89,
        c.KEY_SD_SHEAR_VU: 547.33,
        c.KEY_SD_SHEAR_VCR: 1684.30,
        c.KEY_SD_SHEAR_AV: 16700.0,
        c.KEY_UTIL_SHEAR: 32.50,
        c.KEY_SD_STIFF_METHOD: "post_critical",
        c.KEY_SD_STIFF_INT_THICK: 21.1 if has_intermediate_stiffeners else None,
        c.KEY_SD_STIFF_INT_SPACING: 2440.0 if has_intermediate_stiffeners else None,
        c.KEY_SD_STIFF_END_THICK: 1.7,
        c.KEY_SD_STIFF_END_COUNT: 4,
        c.KEY_SD_STIFF_LONG: "None",
        c.KEY_SD_BS_R: 547.33,
        c.KEY_SD_BS_FCDW_WB: 168430.0,
        c.KEY_SD_BS_FCDW_LC: 652.33,
        c.KEY_SD_BS_FPSD: 3181.82,
        c.KEY_SD_BS_FCD: 2863.64,
        "steeldesign.details.shear.diameter": 19.0,
        "steeldesign.details.shear.height": 100.0,
        "steeldesign.details.shear.yield_strength": 350.0,
        "steeldesign.details.shear.ultimate_strength": 450.0,
        "steeldesign.details.shear.studs_per_section": 3,
        "design_results": {
            "steeldesign.stress.steel": 145.2,
            "steeldesign.stress.steel.allowable": 200.0,
            "steeldesign.uls_per_girder": {
                "fatigue": {
                    gid: {"demand": 65.0, "capacity": 100.0, "ur": 0.65, "status": "PASS"}
                    for gid in girder_ids
                }
            },
            "per_girder": {
                gid: {
                    "checks": [
                        {"check_id": 1, "dcr": 0.8189, "demand": 6540.0, "capacity": 7986.44, "demand_unit": "kN-m", "capacity_unit": "kN-m"},
                        {"check_id": 2, "dcr": 0.3250, "demand": 547.33, "capacity": 1684.30, "demand_unit": "kN", "capacity_unit": "kN"},
                        {"check_id": 5, "dcr": 0.6500, "demand": 4500.0, "capacity": 6900.0, "demand_unit": "kN-m", "capacity_unit": "kN-m"},
                        {"check_id": 13, "dcr": 0.3307, "demand": 12.4, "capacity": 37.5, "demand_unit": "mm", "capacity_unit": "mm"},
                        {"check_id": 11, "dcr": 0.7260, "demand": 145.2, "capacity": 200.0, "demand_unit": "MPa", "capacity_unit": "MPa"},
                        {"check_id": 8, "dcr": 0.6500, "demand": 65.0, "capacity": 100.0, "demand_unit": "MPa", "capacity_unit": "MPa"},
                    ],
                    "per_lc": {
                        "1.5 DL + 1.5 LL": {
                            "checks": [
                                {"id": 1, "dcr": 0.8189},
                                {"id": 2, "dcr": 0.3250},
                                {"id": 5, "dcr": 0.6500},
                                {"id": 13, "dcr": 0.3307},
                                {"id": 11, "dcr": 0.7260},
                                {"id": 8, "dcr": 0.6500},
                            ]
                        }
                    }
                }
                for gid in girder_ids
            },
            c.KEY_SD_SC_Qu_kN: 89.5,
            c.KEY_SD_SC_Qr_kN: 65.0,
            "stud_spacing_provided_mm": 160.0,
            c.KEY_SD_SC_SL1: 250.0,
            c.KEY_SD_SC_SL2: 300.0,
            c.KEY_SD_SC_SR: 200.0,
            "stud_spacing_max_mm": 600.0,
            c.KEY_SD_TS_VL: 350.0,
            c.KEY_SD_TS_VRD: 520.0,
            "transverse_shear_ok": True,
            "Ast_required_cm2_per_m": 4.5,
            c.KEY_SD_SC_D_LIMIT: 44.0,
            c.KEY_SD_SC_EDGE_DIST: 50.0,
            c.KEY_SD_SC_REQ_EDGE_DIST: 38.0,
        },
        "deck_design_results": {
            "rebar_bottom_area": 706.858,
            "rebar_top_area": 526.034,
        },
    }

    for i, gid in enumerate(girder_ids, start=1):
        outputs[f"{c.KEY_SD_DEFL_LIVE}.{gid}"] = 12.4
        outputs[f"{c.KEY_SD_DEFL_TOTAL}.{gid}"] = 37.5

    # Intermediate stiffener check outputs (if custom)
    if has_intermediate_stiffeners:
        outputs[c.KEY_SD_IS_IYS_MIN] = 1500000.0
        outputs[c.KEY_SD_IS_IYS_PROV] = 2200000.0
        outputs[c.KEY_SD_IS_FQ] = 450.0
        outputs[c.KEY_SD_IS_FQD] = 680.0

    # Deck Design Outputs
    if has_deck:
        outputs["deck_report_values"] = {
            c.KEY_DD_SPAN: 2.555,
            c.KEY_DD_FY: 500.0,
            c.KEY_DD_WDL: 5.5,
            c.KEY_DD_WHEEL_LOAD: 100.0,
            c.KEY_DD_TYRE_WIDTH: 0.51,
            c.KEY_DD_IMPACT_FACTOR: 1.15,
            c.KEY_DD_VEHICLE: "70R Wheeled",
            c.KEY_DD_HAS_OVERHANG: True,
            c.KEY_DD_M_DL: 12.5,
            c.KEY_DD_M_LL: 42.0,
            c.KEY_DD_GAMMA_DL: 1.35,
            c.KEY_DD_GAMMA_LL: 1.50,
            c.KEY_DD_M_ULS_SAG: 79.875,
            c.KEY_DD_MU_BOT: 110.5,
            c.KEY_DD_M_ULS_HOG: 65.4,
            c.KEY_DD_MU_TOP: 95.2,
            c.KEY_DD_M_ULS_OH: 28.5,
            c.KEY_DD_MU_OH: 45.0,
            c.KEY_DD_D_BOT: 194.0,
            c.KEY_DD_PUNCH_VED_KN: 150.0,
            c.KEY_DD_TYRE_LENGTH: 300.0,
            c.KEY_DD_PUNCH_C1: 810.0,
            c.KEY_DD_PUNCH_C2: 810.0,
            c.KEY_DD_PUNCH_U1: 4840.0,
            c.KEY_DD_PUNCH_VED: 0.34,
            c.KEY_DD_VRD_C_MPA: 0.555,
            c.KEY_DD_PUNCH_OK: True,
            c.KEY_DD_SHEAR_VED: 83.2072,
            c.KEY_DD_SHEAR_VRDC: 107.582,
            c.KEY_DD_SHEAR_OK: True,
            c.KEY_DD_WK_BOT: 0.22,
            c.KEY_DD_WK_TOP: 0.18,
            c.KEY_DD_WK_LIMIT: 0.3,
            c.KEY_DD_AS_MIN: 302.64,
            c.KEY_DD_DIA_BOT: 12.0,
            c.KEY_DD_SPC_BOT: 160.0,
            c.KEY_DD_AS_BOT: 706.858,
            c.KEY_DD_AS_REQ_BOT: 675.979,
            c.KEY_DD_AS_REQ_TOP: 500.986,
            c.KEY_DD_AS_TOP: 526.034,
            c.KEY_DD_AS_LONG: 376.991,
            c.KEY_DD_SPACING_MAX: 300.0,
            c.KEY_DD_MIN_COVER: 50.0,
            c.KEY_DD_COVER_OK: True,
        }

    # Cross Bracing Outputs
    if has_cross_bracing:
        pairs = {}
        for i in range(1, n_girders):
            pair_lbl = f"G{i}-G{i+1}"
            pairs[pair_lbl] = {
                "diag_compression_kN": 50.0,
                "diag_compression_gov_lc": "1.5 DL + 1.5 WL",
                "chord_tension_kN": 30.0,
                "chord_tension_gov_lc": "1.5 DL + 1.5 WL",
            }
        outputs["crossbracing_forces_dict"] = {
            "geometry": {"diagonal_length_m": 2.5, "horiz_proj_m": 2.0},
            "pairs": pairs,
        }
        cb_results = {}
        for i in range(1, n_girders):
            pair_lbl = f"G{i}-G{i+1}"
            cb_results[pair_lbl] = {
                "diagonal": {
                    "compression": {
                        "section_size.designation": "IS 100 x 100 x 10",
                        "Member.tension_capacity": 280.0,
                        "Member.efficiency": 0.35,
                        "Member.Slenderness": 135.0,
                    }
                },
                "chord": {
                    "tension": {
                        "section_size.designation": "IS 100 x 100 x 10",
                        "Member.tension_capacity": 320.0,
                        "Member.efficiency": 0.20,
                        "Member.Slenderness": 110.0,
                    }
                }
            }
            outputs[f"transverse_member_design.cb.section_properties.bracing.{pair_lbl.replace('-', '')}.A"] = 19.0
            outputs[f"transverse_member_design.cb.section_properties.bracing.{pair_lbl.replace('-', '')}.rv"] = 1.95
            outputs[f"transverse_member_design.cb.section_properties.top_chord.{pair_lbl.replace('-', '')}.A"] = 19.0
            outputs[f"transverse_member_design.cb.section_properties.top_chord.{pair_lbl.replace('-', '')}.rv"] = 1.95
        outputs["crossbracing_design_results"] = cb_results
        outputs["crossbracing_design_results"] = cb_results

    # End Diaphragm Outputs
    if has_end_diaphragm:
        outputs["transverse_member_design.ed.forces"] = {
            "G1-G2": {
                "diag_compression_kN": 65.0,
                "diag_compression_gov_lc": "1.5 DL + 1.5 EQ",
                "chord_tension_kN": 45.0,
                "chord_tension_gov_lc": "1.5 DL + 1.5 EQ",
            }
        }
        outputs["enddiaphragm_design_results"] = {
            "G1-G2": {
                "diagonal": {
                    "compression": {
                        "section_size.designation": "IS 100 x 100 x 10",
                        "Member.tension_capacity": 280.0,
                        "Member.efficiency": 0.45,
                        "Member.Slenderness": 135.0,
                    }
                },
                "chord": {
                    "tension": {
                        "section_size.designation": "IS 100 x 100 x 10",
                        "Member.tension_capacity": 320.0,
                        "Member.efficiency": 0.28,
                        "Member.Slenderness": 110.0,
                    }
                }
            }
        }
        outputs["transverse_member_design.ed.section_properties.bracing.G1G2.A"] = 19.0
        outputs["transverse_member_design.ed.section_properties.bracing.G1G2.rv"] = 19.5

    # Overall Summary
    outputs["summary.max_ur_girder"] = 0.82
    outputs["summary.status_girder"] = "PASS"
    outputs["summary.max_ur_deck"] = 0.77
    outputs["summary.status_deck"] = "PASS"
    outputs["summary.max_ur_cb"] = 0.35
    outputs["summary.status_cb"] = "PASS"
    outputs["summary.max_ur_ed"] = 0.45
    outputs["summary.status_ed"] = "PASS"

    facts = ReportFacts(
        metadata=FactMetadata(
            project_name=inputs["project.name"],
            project_location=inputs["project.location"],
            designer=inputs["designer.name"],
            client=inputs["client.name"],
            company=inputs["company.name"],
            report_date="2026-08-21"
        ),
        inputs=build_input_facts(inputs),
        loads=build_load_facts(inputs),
        design_check_data=build_design_check_data(outputs, inputs),
        materials=build_material_facts(inputs, outputs),
        raw_input_dict=inputs,
        raw_output_dict=outputs,
        design_checks=["girder_flexure", "girder_shear", "deck_slab", "cross_bracing", "end_diaphragm"]
    )
    return facts


@pytest.fixture
def doc_5_girder_full() -> ReportDocument:
    facts = _build_synthetic_facts(n_girders=5, has_intermediate_stiffeners=True, has_deck=True, has_cross_bracing=True, has_end_diaphragm=True)
    return build_report_document(facts, include_sections=["loads", "design_checks"])


@pytest.fixture
def doc_3_girder_no_intermediate() -> ReportDocument:
    facts = _build_synthetic_facts(n_girders=3, has_intermediate_stiffeners=False, has_deck=True, has_cross_bracing=True, has_end_diaphragm=True)
    return build_report_document(facts, include_sections=["loads", "design_checks"])


@pytest.fixture
def doc_10_girder_heavy() -> ReportDocument:
    facts = _build_synthetic_facts(n_girders=10, has_intermediate_stiffeners=True, has_deck=True, has_cross_bracing=True, has_end_diaphragm=True)
    return build_report_document(facts, include_sections=["loads", "design_checks"])


# =============================================================================
# Chapter 2 Content Contract
# =============================================================================

class TestChapter2ContentContract:
    """Verify Chapter 2 hierarchy, table sequences, and required engineering row labels."""

    def test_chapter_2_structure_and_subsections(self, doc_5_girder_full: ReportDocument):
        ch2 = find_chapter(doc_5_girder_full, 2)
        assert ch2.title == "Input Parameters"

        # Introductory section directly under chapter
        assert ch2.sections[0].title == ""
        assert any(isinstance(c, Paragraph) for c in ch2.sections[0].components)
        intro_text = [c.text for c in ch2.sections[0].components if isinstance(c, Paragraph)][0]
        assert "This section documents all inputs" in intro_text

        # Subsections 2.1 and 2.2
        sec_2_1 = find_section(ch2, "Basic Inputs (User-Defined)")
        sec_2_2 = find_section(ch2, "Additional Inputs")
        assert sec_2_1 is not None
        assert sec_2_2 is not None

    def test_chapter_2_basic_inputs_tables(self, doc_5_girder_full: ReportDocument):
        ch2 = find_chapter(doc_5_girder_full, 2)
        sec_2_1 = find_section(ch2, "Basic Inputs (User-Defined)")
        tables = get_all_tables(sec_2_1)
        captions = [t.caption for t in tables]

        expected_tables = [
            "Project Location",
            "Bridge Geometry",
            "Material Selection",
        ]
        assert captions == expected_tables

        # Check required fields in Basic Inputs
        t_loc = find_table(sec_2_1, "Project Location")
        assert_table_has_rows(t_loc, ["Project Location", "Seismic Zone", "Basic Wind Speed"])

        t_geom = find_table(sec_2_1, "Bridge Geometry")
        assert_table_has_rows(t_geom, ["Type of Structure", "Span", "Carriageway Width"])

        t_mat = find_table(sec_2_1, "Material Selection")
        assert_table_has_rows(t_mat, ["Girder Steel Grade", "Cross Bracing Steel Grade", "Concrete Deck Grade"])

    def test_chapter_2_additional_inputs_tables_and_row_labels(self, doc_5_girder_full: ReportDocument):
        ch2 = find_chapter(doc_5_girder_full, 2)
        sec_2_2 = find_section(ch2, "Additional Inputs")
        tables = get_all_tables(sec_2_2)
        captions = [t.caption for t in tables]

        expected_tables = [
            "Typical Section Details",
            "Components Details",
            "Girder General Information",
            "Girder Section Dimensions",
            "Girder Restraint and Stiffener Details",
            "Member Properties: Cross Bracing Details",
            "Member Properties: End Diaphragm Details",
            "Shear Connector Details",
            "Partial Safety Factors",
        ]
        assert captions == expected_tables

        # 1. Typical Section: No. of Traffic Lanes & Girder Spacing
        t_ts = find_table(sec_2_2, "Typical Section Details")
        assert_table_has_fields(t_ts, ["No. of Traffic Lanes", "Overall Bridge Width", "Girder Spacing (m)"])

        # 2. Girder General Information: rows scale with girder count
        t_ggi = find_table(sec_2_2, "Girder General Information")
        assert len(t_ggi.rows) == 5
        assert_table_has_fields(t_ggi, ["Girder", "Member ID", "Design Mode"])

        # 3. Girder Section Dimensions: Depth, Web Thk, Flange Width/Thk
        t_gsd = find_table(sec_2_2, "Girder Section Dimensions")
        assert len(t_gsd.rows) == 5
        assert_table_has_fields(t_gsd, ["Total Depth, D", "Web", "Top Flange", "Bottom Flange"])

        # 4. Girder Restraint & Stiffeners: Bearing Stiffener & Intermediate Stiffeners
        t_grs = find_table(sec_2_2, "Girder Restraint and Stiffener Details")
        assert len(t_grs.rows) == 5
        assert_table_has_fields(t_grs, ["Intermediate Stiffeners", "Bearing Stiffener", "Restraint"])

        # 5. Cross Bracing Details: Section & Spacing
        t_cb = find_table(sec_2_2, "Member Properties: Cross Bracing Details")
        assert_table_has_fields(t_cb, ["Bracing Section", "Spacing"])

        # 6. End Diaphragm Details: Section
        t_ed = find_table(sec_2_2, "Member Properties: End Diaphragm Details")
        assert_table_has_fields(t_ed, ["Bracing Section"])

        # 7. Shear Connector Details
        t_sc = find_table(sec_2_2, "Shear Connector Details")
        assert_table_has_fields(t_sc, ["Stud Diameter", "Stud Height", "Stud", "No. of Studs"])

        # 8. Partial Safety Factors
        t_sf = find_table(sec_2_2, "Partial Safety Factors")
        assert_table_has_fields(t_sf, ["Yielding / Buckling", "Ultimate Stress", "Concrete", "Reinforcement", "Shear Connectors"])


# =============================================================================
# Chapter 5 Content Contract
# =============================================================================

class TestChapter5ContentContract:
    """Verify Chapter 5 hierarchy, calculation rows, notes, and sub-sections."""

    def test_chapter_5_five_subsection_hierarchy(self, doc_5_girder_full: ReportDocument):
        ch5 = find_chapter(doc_5_girder_full, 5)
        assert ch5.title == "Design Checks"

        # Introductory narrative under chapter
        assert ch5.sections[0].title == ""
        assert any(isinstance(c, Paragraph) for c in ch5.sections[0].components)

        sec_titles = [s.title for s in ch5.sections if s.title != ""]
        expected_sections = [
            "Plate Girder Design",
            "Deck Slab Design",
            "Cross Bracing Design",
            "End Diaphragm Design",
            "Overall Design Check Summary",
        ]
        assert sec_titles == expected_sections

    def test_section_5_1_plate_girder_design_tables(self, doc_5_girder_full: ReportDocument):
        ch5 = find_chapter(doc_5_girder_full, 5)
        sec_pg = find_section(ch5, "Plate Girder Design")
        tables = get_all_tables(sec_pg)
        captions = [t.caption for t in tables]

        # Key required girder design check tables
        assert any("Section Properties" in c for c in captions)
        assert any("Section Classification" in c for c in captions)
        assert any("Moment Capacity" in c for c in captions)
        assert any("Shear Capacity" in c for c in captions)
        assert any("Interaction Checks" in c for c in captions)
        assert any("Lateral Torsional Buckling" in c for c in captions)
        assert any("Stiffener Design Summary" in c for c in captions)
        assert any("Intermediate Stiffener Checks" in c for c in captions)
        assert any("End Panel Stiffener Checks" in c for c in captions)
        assert any("Deflection Checks" in c for c in captions)
        assert any("Stress Limitation" in c for c in captions)
        assert any("Fatigue Assessment" in c for c in captions)
        assert any("Shear Connector Capacity" in c for c in captions)
        assert any("Shear Connector Spacing" in c for c in captions)
        assert any("Transverse Shear and Detailing" in c for c in captions)

        # End Panel checks must have all required resistance rows
        t_ep = find_table(sec_pg, "End Panel Stiffener Checks")
        assert_table_has_rows(t_ep, [
            "Web Buckling Resistance",
            "Local Crushing Resistance",
            "Bearing Capacity",
            "Column Buckling Resistance",
        ])

    def test_section_5_2_deck_slab_intermediate_calculation_rows(self, doc_5_girder_full: ReportDocument):
        """Contract test for all restored intermediate calculation rows in Deck Slab design."""
        ch5 = find_chapter(doc_5_girder_full, 5)
        sec_dk = find_section(ch5, "Deck Slab Design")

        # 1. Deck Loading and Geometry (Table 5.17a)
        t_ld = find_table(sec_dk, "Deck Slab --- Loading and Geometry")
        assert_table_has_rows(t_ld, [
            "Effective Span",
            "Deck Thickness",
            "Clear Cover",
            "Concrete Grade",
            "Reinforcement Grade",
            "Dead Load per Unit Area",
            "Wheel Load",
            "Tyre Contact Width",
            "Impact Factor",
            "Governing Live Load Case",
        ])

        # 2. Deck Flexure Check: Interior Panel (Table 5.17b / 5.18)
        t_fx = find_table(sec_dk, "Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)")
        assert_table_has_rows(t_fx, [
            "Transverse BM (DL)",
            "Transverse BM (LL)",
            "Total Design BM",
            "Effective depth",
            "Moment Capacity",
            "Sagging",
        ])

        # 3. Deck Flexure Check: Support / Overhang (Table 5.17c / 5.19)
        t_oh = find_table(sec_dk, "Deck Slab --- Cantilever Overhang Flexure Check")
        assert_table_has_rows(t_oh, [
            "Overhang Length",
            "Dead Load Moment",
            "Live Load Moment",
            "Total Hogging Moment",
            "Moment Capacity (top steel)",
        ])

        # 4. Punching Shear Check (Table 5.17d / 5.20)
        t_pn = find_table(sec_dk, "Deck Slab --- Punching Shear Check")
        assert_table_has_rows(t_pn, [
            "Design Wheel Load",
            "Tyre Contact Area",
            "Loaded Area at mid-depth",
            "Control Perimeter",
            "Punching Shear Stress",
            "Punching Resistance",
            "Punching Shear Check",
        ])

        # 5. Crack Width Check (Table 5.17e / 5.21)
        t_cw = find_table(sec_dk, "Crack Width Check (Deck Slab)")
        assert_table_has_rows(t_cw, [
            "Min. Reinforcement for Crack Control",
            "Provided Reinforcement",
            "Max. Permissible Crack Width",
            "Calculated Crack Width",
            "Crack Width Check",
        ])

        # 6. One-Way Shear Check (Table 5.17f / 5.22)
        t_ow = find_table(sec_dk, "One-Way (Beam) Shear Check (Deck Slab)")
        assert_table_has_rows(t_ow, [
            "Design Shear per unit width",
            "Effective depth",
            "Size factor",
            "Longitudinal reinforcement ratio",
            "Shear resistance",
            "One-Way Shear Check",
        ])

        # 7. Reinforcement Detailing Summary (Table 5.17g / 5.23)
        t_dt = find_table(sec_dk, "Reinforcement Detailing Summary (Deck Slab)")
        assert_table_has_rows(t_dt, [
            "Main Reinforcement — Bottom (Transverse)",
            "Bar Diameter × Spacing",
            "Min. Reinforcement",
            "Max. Bar Spacing",
            "Distribution Reinforcement — Longitudinal",
            "Top Reinforcement (Support / Cantilever Overhang)",
            "Cover and Detailing",
            "Clear Cover",
        ])

    def test_section_5_3_and_5_4_transverse_bracing_contracts(self, doc_5_girder_full: ReportDocument):
        ch5 = find_chapter(doc_5_girder_full, 5)

        # Cross Bracing
        sec_cb = find_section(ch5, "Cross Bracing Design")
        t_cb_prop = find_table(sec_cb, "Cross Bracing --- Connection and Section Properties")
        assert_table_has_rows(t_cb_prop, ["Diagonal", "Chord", "IS 100 x 100 x 10"])

        t_cb_sl = find_table(sec_cb, "Cross Bracing --- Slenderness Ratio Check")
        assert_table_has_rows(t_cb_sl, ["Diagonal", "Chord", "135.0"])

        t_cb_cap = find_table(sec_cb, "Cross Bracing Design --- Capacity Summary")
        assert_table_has_rows(t_cb_cap, ["Diagonal", "Chord", "PASS"])

        # End Diaphragm
        sec_ed = find_section(ch5, "End Diaphragm Design")
        t_ed_prop = find_table(sec_ed, "End Diaphragm --- Connection and Section Properties")
        assert_table_has_rows(t_ed_prop, ["Diagonal", "Chord"])

        t_ed_sl = find_table(sec_ed, "End Diaphragm --- Slenderness Ratio Check")
        assert_table_has_rows(t_ed_sl, ["Diagonal", "Chord", "135.0"])

        t_ed_cap = find_table(sec_ed, "End Diaphragm Design --- Capacity Summary")
        assert_table_has_rows(t_ed_cap, ["Diagonal", "Chord", "PASS"])

    def test_section_5_5_overall_summary_and_notes(self, doc_5_girder_full: ReportDocument):
        ch5 = find_chapter(doc_5_girder_full, 5)
        sec_sum = find_section(ch5, "Overall Design Check Summary")
        t_sum = find_table(sec_sum, "Overall Design Check Summary")
        assert_table_has_rows(t_sum, ["Girder", "Deck", "Cross Bracing", "End Diaphragm"])

        # Ensure engineering notes exist
        sec_dk = find_section(ch5, "Deck Slab Design")
        t_fx = find_table(sec_dk, "Flexure Check: Interior Panel")
        assert t_fx.note is not None and "IRC 112" in t_fx.note

        t_pn = find_table(sec_dk, "Punching Shear Check")
        assert t_pn.note is not None and "Punching shear reinforcement" in t_pn.note

        t_ow = find_table(sec_dk, "One-Way (Beam) Shear Check")
        assert t_ow.note is not None and "IRC 112" in t_ow.note

        t_dt = find_table(sec_dk, "Reinforcement Detailing Summary")
        assert t_dt.note is not None and "IS 456" in t_dt.note


# =============================================================================
# Multi-Configuration Matrix Contracts
# =============================================================================

class TestMultiConfigurationContracts:
    """Verify that contracts hold across different bridge geometries & optional components."""

    def test_3_girder_bridge_without_intermediate_stiffeners(self, doc_3_girder_no_intermediate: ReportDocument):
        """Table 5.8 (Intermediate Stiffeners) must be omitted when not configured, not an empty broken table."""
        ch2 = find_chapter(doc_3_girder_no_intermediate, 2)
        ch5 = find_chapter(doc_3_girder_no_intermediate, 5)

        # 3 Girders in Chapter 2
        sec_2_2 = find_section(ch2, "Additional Inputs")
        t_ggi = find_table(sec_2_2, "Girder General Information")
        assert len(t_ggi.rows) == 3

        # In Chapter 5, Intermediate Stiffener Checks table must not appear when not configured
        sec_pg = find_section(ch5, "Plate Girder Design")
        tables_pg = get_all_tables(sec_pg)
        assert not any("Intermediate Stiffener Checks" in t.caption for t in tables_pg)

        # But End Panel Stiffener Checks MUST exist
        t_ep = find_table(sec_pg, "End Panel Stiffener Checks")
        assert len(t_ep.groups) == 3

    def test_10_girder_heavy_bridge_structure(self, doc_10_girder_heavy: ReportDocument):
        """10 girder bridge must scale all tables without dropped groups or rows."""
        ch2 = find_chapter(doc_10_girder_heavy, 2)
        ch5 = find_chapter(doc_10_girder_heavy, 5)

        sec_2_2 = find_section(ch2, "Additional Inputs")
        t_ggi = find_table(sec_2_2, "Girder General Information")
        assert len(t_ggi.rows) == 10

        sec_pg = find_section(ch5, "Plate Girder Design")
        t_flex = find_table(sec_pg, "Moment Capacity Check")
        assert len(t_flex.groups) == 10
        assert [g.label for g in t_flex.groups] == [f"G{i}" for i in range(1, 11)]

        sec_cb = find_section(ch5, "Cross Bracing Design")
        t_cb_prop = find_table(sec_cb, "Cross Bracing --- Connection and Section Properties")
        assert len(t_cb_prop.rows) == 9 * 2  # 9 pairs * 2 members (diag, chord)

    def test_missing_optional_deck_configuration(self):
        """When deck design was not performed, girder checks still pass and Deck section is omitted cleanly."""
        facts = _build_synthetic_facts(n_girders=5, has_deck=False)
        doc = build_report_document(facts, include_sections=["loads", "design_checks"])

        ch5 = find_chapter(doc, 5)
        sec_titles = [s.title for s in ch5.sections]
        assert "Plate Girder Design" in sec_titles
        assert "Deck Slab Design" not in sec_titles
        assert "Cross Bracing Design" in sec_titles
        assert "Overall Design Check Summary" in sec_titles
