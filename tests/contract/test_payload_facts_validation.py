"""
Stage 5: Type Safety, Payload & Facts Validation Test Suite
==========================================================

Verifies runtime invariants and defensive validation on both raw payloads and
semantic ReportFacts before document building and LaTeX compilation.

Invariants Enforced:
1. Payloads with missing required keys (span, girder count) or invalid numbers fail validation.
2. ReportFacts with degenerate dimensions (depth <= 0, thickness <= 0), NaN, or Inf values fail validation.
3. Provenance tracker errors (such as unit conversion mismatches) automatically fail facts validation.
4. report.assert_valid() raises clear, human-readable exceptions for developer diagnostics.
"""

from __future__ import annotations

import math
import pytest

from osdagbridge.core.report_engine.facts import (
    CheckStatus,
    GirderDesignData,
    GirderFlexureCheck,
    GirderSectionProperties,
    QuantityValue,
    ReportFacts,
)
from osdagbridge.core.report_engine.provenance import (
    ProvenanceTracker,
    ValueSource,
)
from osdagbridge.core.report_engine.validation import (
    ValidationReport,
    validate_facts,
    validate_payload,
)
from tests.contract.test_report_contract import _build_synthetic_facts


class TestPayloadValidation:
    """Test raw payload input/output validation."""

    def test_clean_payload_passes_validation(self):
        """Standard valid inputs and outputs have is_valid == True and 0 errors."""
        facts = _build_synthetic_facts(n_girders=5)
        report = validate_payload(facts.raw_input_dict, facts.raw_output_dict)
        assert report.is_valid
        assert len(report.errors) == 0

    def test_missing_span_fails_validation(self):
        """Payload missing geometry.span triggers an ERROR."""
        facts = _build_synthetic_facts(n_girders=5)
        inputs = dict(facts.raw_input_dict)
        inputs["geometry.span"] = ""

        report = validate_payload(inputs, facts.raw_output_dict)
        assert not report.is_valid
        assert any(e.field_name == "geometry.span" for e in report.errors)

    def test_negative_span_fails_validation(self):
        """Payload with negative span triggers an ERROR."""
        facts = _build_synthetic_facts(n_girders=5)
        inputs = dict(facts.raw_input_dict)
        inputs["geometry.span"] = "-25.0"

        report = validate_payload(inputs, facts.raw_output_dict)
        assert not report.is_valid
        assert any("must be positive" in e.message for e in report.errors)

    def test_invalid_girder_count_fails_validation(self):
        """Payload with 0 or negative girders triggers an ERROR."""
        facts = _build_synthetic_facts(n_girders=5)
        inputs = dict(facts.raw_input_dict)
        inputs["typical_section.no_of_girders"] = "0"

        report = validate_payload(inputs, facts.raw_output_dict)
        assert not report.is_valid
        assert any("typical_section.no_of_girders" in e.field_name for e in report.errors)


class TestFactsValidation:
    """Test semantic ReportFacts invariants validation."""

    def test_clean_facts_pass_validation(self):
        """Clean synthetic facts pass validation with 0 errors."""
        facts = _build_synthetic_facts(n_girders=5)
        report = validate_facts(facts)
        assert report.is_valid
        assert len(report.errors) == 0

    def test_degenerate_girder_dimension_fails(self):
        """Girder with zero or negative depth triggers an ERROR."""
        facts = _build_synthetic_facts(n_girders=3)
        g0 = facts.design_check_data.girders[0]

        # Artificially alter depth to 0.0
        bad_props = GirderSectionProperties(
            girder_label=g0.girder_label,
            depth=QuantityValue(0.0, "mm"),
            top_flange_width=g0.section_properties.top_flange_width,
            bottom_flange_width=g0.section_properties.bottom_flange_width,
            top_flange_thickness=g0.section_properties.top_flange_thickness,
            bottom_flange_thickness=g0.section_properties.bottom_flange_thickness,
            web_thickness=g0.section_properties.web_thickness,
            gross_area=g0.section_properties.gross_area,
            moment_of_inertia=g0.section_properties.moment_of_inertia,
            elastic_section_modulus=g0.section_properties.elastic_section_modulus,
            plastic_section_modulus=g0.section_properties.plastic_section_modulus,
            effective_slab_width=g0.section_properties.effective_slab_width,
            composite_iz=g0.section_properties.composite_iz,
            pna_depth=g0.section_properties.pna_depth,
        )
        bad_girder = GirderDesignData(
            girder_label=g0.girder_label,
            section_properties=bad_props,
            classification=g0.classification,
            flexure=g0.flexure,
            shear=g0.shear,
            interaction=g0.interaction,
            ltb=g0.ltb,
            stiffener_summary=g0.stiffener_summary,
            intermediate_stiffener=g0.intermediate_stiffener,
            bearing_stiffener=g0.bearing_stiffener,
            deflection=g0.deflection,
            stress=g0.stress,
            fatigue=g0.fatigue,
            summary=g0.summary,
        )

        bad_girders = (bad_girder,) + facts.design_check_data.girders[1:]
        from osdagbridge.core.report_engine.facts import DesignCheckData
        new_dchecks = DesignCheckData(
            girders=bad_girders,
            shear_connectors=facts.design_check_data.shear_connectors,
            deck=facts.design_check_data.deck,
            cross_bracing=facts.design_check_data.cross_bracing,
            end_diaphragm=facts.design_check_data.end_diaphragm,
            summary=facts.design_check_data.summary,
        )
        facts.design_check_data = new_dchecks

        report = validate_facts(facts)
        assert not report.is_valid
        assert any("G1.depth" in e.field_name for e in report.errors)

    def test_nan_utilization_ratio_fails(self):
        """NaN or Inf utilization ratio triggers an ERROR."""
        facts = _build_synthetic_facts(n_girders=3)
        g0 = facts.design_check_data.girders[0]

        bad_flexure = GirderFlexureCheck(
            mu_applied=g0.flexure.mu_applied,
            md_capacity=g0.flexure.md_capacity,
            utilization_ratio=float("nan"),
            status=CheckStatus.FAIL,
        )
        bad_girder = GirderDesignData(
            girder_label=g0.girder_label,
            section_properties=g0.section_properties,
            classification=g0.classification,
            flexure=bad_flexure,
            shear=g0.shear,
            interaction=g0.interaction,
            ltb=g0.ltb,
            stiffener_summary=g0.stiffener_summary,
            intermediate_stiffener=g0.intermediate_stiffener,
            bearing_stiffener=g0.bearing_stiffener,
            deflection=g0.deflection,
            stress=g0.stress,
            fatigue=g0.fatigue,
            summary=g0.summary,
        )
        bad_girders = (bad_girder,) + facts.design_check_data.girders[1:]
        from osdagbridge.core.report_engine.facts import DesignCheckData
        new_dchecks = DesignCheckData(
            girders=bad_girders,
            shear_connectors=facts.design_check_data.shear_connectors,
            deck=facts.design_check_data.deck,
            cross_bracing=facts.design_check_data.cross_bracing,
            end_diaphragm=facts.design_check_data.end_diaphragm,
            summary=facts.design_check_data.summary,
        )
        facts.design_check_data = new_dchecks

        report = validate_facts(facts)
        assert not report.is_valid
        assert any("G1.flexure.ur" in e.field_name for e in report.errors)

    def test_provenance_errors_bubble_up_to_facts_validation(self):
        """If an attached ProvenanceTracker has a unit mismatch error, validate_facts must fail."""
        facts = _build_synthetic_facts(n_girders=3)
        tracker = ProvenanceTracker()
        tracker.record(
            fact_name="G1.depth",
            source=ValueSource.OUTPUT_DICT,
            source_key="depth",
            source_value=1.67,  # m
            extracted_value=1.67,  # mm (unscaled error)
            source_unit="m",
            target_unit="mm",
            transform="none",
        )
        facts.provenance = tracker

        report = validate_facts(facts)
        assert not report.is_valid
        assert any("Provenance validation error" in e.message for e in report.errors)

    def test_assert_valid_raises_value_error(self):
        """assert_valid() raises ValueError when errors exist."""
        from osdagbridge.core.report_engine.validation import ValidationIssue
        report = ValidationReport(
            is_valid=False,
            issues=[ValidationIssue("ERROR", "test_field", "Invalid engineering value")]
        )

        with pytest.raises(ValueError, match="Report payload validation failed"):
            report.assert_valid()
