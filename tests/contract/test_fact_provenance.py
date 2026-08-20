"""
Stage 4: Data Provenance & Fact Tracing Test Suite
==================================================

Verifies the origin, transformation, and unit conversion traceability of every
engineering fact used across the report engine.

Invariants Enforced:
1. Every critical engineering value (girder dimensions, capacities, deck values,
   bracing properties, material takeoff) records its exact source dictionary, source key,
   raw value, extracted value, and unit conversion transformation.
2. The ProvenanceTracker validates unit transformations (e.g. m -> mm, cm² -> mm², N -> kN)
   and detects unexpected scaling errors.
3. Developer / debug provenance reports are accessible directly via ReportFacts.provenance_report().
"""

from __future__ import annotations

import pytest

from osdagbridge.core.report_engine.facts import (
    FactMetadata,
    ReportFacts,
)
from osdagbridge.core.report_engine.facts.inputs import build_input_facts
from osdagbridge.core.report_engine.facts.loads import build_load_facts
from osdagbridge.core.report_engine.facts.material_takeoff import build_material_facts
from osdagbridge.core.report_engine.facts.design_checks import build_design_check_data
from osdagbridge.core.report_engine.provenance import (
    FactProvenance,
    ProvenanceTracker,
    ProvenanceValidationIssue,
    ValueSource,
)
from tests.contract.test_report_contract import _build_synthetic_facts


def _create_tracked_facts(n_girders=5, has_intermediate_stiffeners=True, has_deck=True) -> ReportFacts:
    base_facts = _build_synthetic_facts(
        n_girders=n_girders,
        has_intermediate_stiffeners=has_intermediate_stiffeners,
        has_deck=has_deck,
    )
    tracker = ProvenanceTracker()
    in_dict = base_facts.raw_input_dict or {}
    out_dict = base_facts.raw_output_dict or {}

    inputs = build_input_facts(in_dict, tracker=tracker)
    loads = build_load_facts(in_dict, tracker=tracker)
    dchecks = build_design_check_data(out_dict, in_dict, tracker=tracker)
    materials = build_material_facts(in_dict, out_dict, tracker=tracker)

    return ReportFacts(
        metadata=base_facts.metadata,
        inputs=inputs,
        loads=loads,
        design_check_data=dchecks,
        materials=materials,
        provenance=tracker,
        raw_input_dict=in_dict,
        raw_output_dict=out_dict,
        design_checks=base_facts.design_checks,
    )


class TestDataProvenance:
    """Test provenance capture, unit conversion verification, and reporting."""

    def test_girder_provenance_tracking(self):
        """Verify girder section properties and capacities are tracked with provenance."""
        facts = _create_tracked_facts(n_girders=5)
        tracker = facts.provenance
        assert tracker is not None

        # Check G1 properties
        p_depth = tracker.get("G1.depth")
        assert p_depth is not None
        assert p_depth.source == ValueSource.OUTPUT_DICT
        assert p_depth.target_unit == "mm"
        assert p_depth.extracted_value == 1670.0

        p_tf_w = tracker.get("G1.top_flange_width")
        assert p_tf_w is not None
        assert p_tf_w.extracted_value == 510.0

        # Check flexure & shear capacities
        p_md = tracker.get("G1.flexure.moment_capacity")
        assert p_md is not None
        assert p_md.target_unit == "kN-m"
        assert p_md.extracted_value == 7986.44

        p_vd = tracker.get("G1.shear.shear_capacity")
        assert p_vd is not None
        assert p_vd.target_unit == "kN"
        assert p_vd.extracted_value == 1684.30

    def test_deck_provenance_tracking(self):
        """Verify deck slab calculations and intermediate parameters are tracked."""
        facts = _create_tracked_facts(n_girders=5, has_deck=True)
        tracker = facts.provenance
        assert tracker is not None

        p_thk = tracker.get("deck.thickness")
        assert p_thk is not None
        assert p_thk.source == ValueSource.INPUT_DICT
        assert p_thk.extracted_value == 250.0
        assert p_thk.target_unit == "mm"

        p_punch = tracker.get("deck.punching.punch_vrdc_mpa")
        assert p_punch is not None
        assert p_punch.extracted_value == 0.555
        assert p_punch.target_unit == "MPa"

        p_sag = tracker.get("deck.flexure.interior_moment_sag")
        assert p_sag is not None
        assert p_sag.extracted_value == 79.875
        assert p_sag.target_unit == "kN-m/m"

    def test_cross_bracing_unit_conversion_provenance(self):
        """Verify cross bracing area (cm² -> mm²) and rmin (cm -> mm) conversion tracking."""
        facts = _create_tracked_facts(n_girders=5)
        tracker = facts.provenance
        assert tracker is not None

        p_area = tracker.get("cross_bracing.G1-G2.diagonal.compression.gross_area")
        assert p_area is not None
        assert p_area.source_unit == "cm²"
        assert p_area.target_unit == "mm²"
        assert p_area.is_converted
        assert "x 100" in (p_area.transform or "")
        assert p_area.extracted_value == 1900.0  # 19.0 cm² -> 1900.0 mm²

        p_rmin = tracker.get("cross_bracing.G1-G2.diagonal.compression.rmin")
        assert p_rmin is not None
        assert p_rmin.source_unit == "cm"
        assert p_rmin.target_unit == "mm"
        assert p_rmin.is_converted
        assert "x 10" in (p_rmin.transform or "")
        assert p_rmin.extracted_value == 19.5  # 1.95 cm -> 19.5 mm

    def test_material_takeoff_provenance(self):
        """Verify material takeoff quantities record their derivation lineage."""
        facts = _create_tracked_facts(n_girders=5)
        tracker = facts.provenance
        assert tracker is not None

        p_steel = tracker.get("material_takeoff.structural_steel.girders_weight")
        assert p_steel is not None
        assert p_steel.source == ValueSource.DERIVED
        assert p_steel.target_unit == "MT"

        p_conc = tracker.get("material_takeoff.concrete_deck.total_volume")
        assert p_conc is not None
        assert p_conc.source == ValueSource.DERIVED
        assert p_conc.target_unit == "m³"

    def test_provenance_validation_clean_on_standard_payload(self):
        """Standard payload must have zero provenance validation issues."""
        facts = _create_tracked_facts(n_girders=5)
        tracker = facts.provenance
        assert tracker is not None

        issues = tracker.validate()
        assert len(issues) == 0, f"Expected 0 issues, found: {issues}"

    def test_provenance_validation_detects_unit_mismatch_tripwire(self):
        """Tripwire test: A faulty unit conversion (e.g. 1.67 m -> 1.67 mm) must fail validation."""
        tracker = ProvenanceTracker()
        tracker.record(
            fact_name="faulty_girder.depth",
            source=ValueSource.OUTPUT_DICT,
            source_key="section_design.total_depth",
            source_value=1.67,  # in meters
            extracted_value=1.67,  # in mm (forgot * 1000!)
            source_unit="m",
            target_unit="mm",
            transform="none",
        )

        issues = tracker.validate()
        assert len(issues) == 1
        assert issues[0].severity == "ERROR"
        assert "Unit mismatch" in issues[0].message
        assert "1.67 m converted to 1.67 mm" in issues[0].message

    def test_provenance_report_generation(self):
        """Verify provenance report formats cleanly as a debug lineage summary."""
        facts = _create_tracked_facts(n_girders=5)
        report_str = facts.provenance_report()
        assert "DATA PROVENANCE REPORT" in report_str
        assert "G1.depth" in report_str
        assert "1670.0 mm" in report_str
        assert "deck.punching.punch_vrdc_mpa" in report_str
        assert "0.555 MPa" in report_str
        assert "Tracked Fact Values:" in report_str
        print("\n" + report_str[:600] + "\n...")
