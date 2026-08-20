"""
Stage 7: Multi-Configuration Acceptance Matrix Test Suite
=========================================================

End-to-end production acceptance matrix verifying that the complete reporting
pipeline operates with zero regressions across materially different bridge geometries
and engineering configurations.

Configurations Matrix:
- Configuration A: 3 Girders, No Intermediate Stiffeners, No Footway.
- Configuration B: 5 Girders, Custom Intermediate Stiffeners, Footway, Full Deck.
- Configuration C: 10 Girders Heavy Bridge, 9 Bracing Panels, Multi-Page Scaling.
- Configuration D: Partial Data / Optional Engineering Sections Unavailable.

Full Pipeline Verified per Configuration:
  Raw Payload
      ↓
  validate_payload
      ↓
  ReportFacts (with ProvenanceTracker)
      ↓
  validate_facts
      ↓
  ReportDocument AST (build_report_document)
      ↓
  Report Content Contract (TOC, AST inspection, row assertions)
      ↓
  Structural Manifest Parity (compare_manifests & assert_no_regressions)
      ↓
  LatexRenderer (Theme + LayoutHints + LongTable headers)
      ↓
  Preflight & Compilation Sanity Check
"""

from __future__ import annotations

import pytest
from typing import Any, Dict

from osdagbridge.core.report_engine import (
    LatexRenderer,
    ParityStatus,
    PDFPreflight,
    PreflightStatus,
    ProvenanceTracker,
    ReportFacts,
    ReportTheme,
    build_report_document,
    compare_manifests,
    extract_legacy_manifest_from_payload,
    extract_semantic_manifest,
    validate_facts,
    validate_payload,
)
from osdagbridge.core.report_engine.document import Chapter, ReportDocument, Section, Table
from osdagbridge.core.report_engine.facts.design_checks import build_design_check_data
from osdagbridge.core.report_engine.facts.inputs import build_input_facts
from osdagbridge.core.report_engine.facts.loads import build_load_facts
from osdagbridge.core.report_engine.facts.material_takeoff import build_material_facts
from tests.contract.test_report_contract import (
    _build_synthetic_facts,
    assert_table_has_fields,
    assert_table_has_rows,
    find_chapter,
    find_section,
    find_table,
    get_all_tables,
)


def _run_full_pipeline_for_configuration(
    n_girders: int,
    has_intermediate_stiffeners: bool = True,
    has_deck: bool = True,
    has_cross_bracing: bool = True,
    has_end_diaphragm: bool = True,
    has_footpath: bool = True,
) -> tuple[ReportFacts, ReportDocument, str, Any]:
    """Execute the complete end-to-end report engine pipeline for a given configuration."""
    base_facts = _build_synthetic_facts(
        n_girders=n_girders,
        has_intermediate_stiffeners=has_intermediate_stiffeners,
        has_deck=has_deck,
        has_cross_bracing=has_cross_bracing,
        has_end_diaphragm=has_end_diaphragm,
        has_footpath=has_footpath,
    )
    raw_in = base_facts.raw_input_dict or {}
    raw_out = base_facts.raw_output_dict or {}

    # 1. Payload Validation
    payload_report = validate_payload(raw_in, raw_out)
    payload_report.assert_valid()

    # 2. Build Facts with Provenance
    tracker = ProvenanceTracker()
    inputs = build_input_facts(raw_in, tracker=tracker)
    loads = build_load_facts(raw_in, tracker=tracker)
    dchecks = build_design_check_data(raw_out, raw_in, tracker=tracker)
    materials = build_material_facts(raw_in, raw_out, tracker=tracker)

    facts = ReportFacts(
        metadata=base_facts.metadata,
        inputs=inputs,
        loads=loads,
        design_check_data=dchecks,
        materials=materials,
        provenance=tracker,
        raw_input_dict=raw_in,
        raw_output_dict=raw_out,
        design_checks=base_facts.design_checks,
    )

    # 3. Facts Invariant Validation
    facts_report = validate_facts(facts)
    facts_report.assert_valid()

    # 4. AST Document Assembly
    doc = build_report_document(facts, include_sections=["loads", "analysis", "design_checks", "drawings", "quantities"])

    # 5. Structural Manifest Parity Verification
    legacy_payload = {"inputs": raw_in, "output_dict": raw_out, "design_checks": base_facts.design_checks}
    legacy_manifest = extract_legacy_manifest_from_payload(legacy_payload)
    semantic_manifest = extract_semantic_manifest(doc)
    parity_report = compare_manifests(legacy_manifest, semantic_manifest)
    parity_report.assert_no_regressions()

    # 6. LaTeX Rendering
    theme = ReportTheme()
    renderer = LatexRenderer(theme)
    latex_output = renderer.render_document(doc)

    # 7. Basic Preflight / LaTeX Sanity
    preflight = PDFPreflight(facts=facts, document=doc, pdf_path="test_acceptance.pdf")
    preflight_report = preflight.run()
    assert preflight_report.overall != PreflightStatus.FAIL

    return facts, doc, latex_output, parity_report


class TestAcceptanceConfigurationA:
    """Configuration A: 3 Girders, No Intermediate Stiffeners, No Footway."""

    def test_pipeline_configuration_a(self):
        facts, doc, latex, parity = _run_full_pipeline_for_configuration(
            n_girders=3,
            has_intermediate_stiffeners=False,
            has_deck=True,
            has_footpath=False,
        )

        # Content Contract: 3 girders
        ch2 = find_chapter(doc, 2)
        sec_2_2 = find_section(ch2, "Additional Inputs")
        t_ggi = find_table(sec_2_2, "Girder General Information")
        assert len(t_ggi.rows) == 3

        # Chapter 5: Intermediate stiffeners omitted cleanly, End panel has 3 groups
        ch5 = find_chapter(doc, 5)
        sec_pg = find_section(ch5, "Plate Girder Design")
        tables_pg = get_all_tables(sec_pg)
        assert not any("Intermediate Stiffener Checks" in t.caption for t in tables_pg)

        t_ep = find_table(sec_pg, "End Panel Stiffener Checks")
        assert len(t_ep.groups) == 3

        # Cross bracing: 2 pairs (G1-G2, G2-G3)
        sec_cb = find_section(ch5, "Cross Bracing Design")
        t_cb = find_table(sec_cb, "Cross Bracing --- Connection and Section Properties")
        assert len(t_cb.rows) == 2 * 2  # 2 pairs * 2 members

        # Parity: Clean with 0 regressions
        assert parity.is_clean
        assert parity.total_regressions == 0

        # Renderer: Clean LaTeX with longtable headers
        assert r"\begin{longtable}" in latex
        assert r"\endhead" in latex
        assert r"\endfirsthead" in latex


class TestAcceptanceConfigurationB:
    """Configuration B: 5 Girders Standard Production (Custom Stiffeners, Footway, Full Deck)."""

    def test_pipeline_configuration_b(self):
        facts, doc, latex, parity = _run_full_pipeline_for_configuration(
            n_girders=5,
            has_intermediate_stiffeners=True,
            has_deck=True,
            has_footpath=True,
        )

        # Chapter 2: 5 Girders
        ch2 = find_chapter(doc, 2)
        t_ggi = find_table(find_section(ch2, "Additional Inputs"), "Girder General Information")
        assert len(t_ggi.rows) == 5

        # Chapter 3: Vehicle + Footway intentional split
        ch3 = find_chapter(doc, 3)
        t_veh = find_table(ch3, "Vehicle Live Loads")
        t_fw = find_table(ch3, "Footway Load")
        assert t_veh is not None and t_fw is not None

        # Chapter 5: 5 subsections, Intermediate stiffeners present
        ch5 = find_chapter(doc, 5)
        sec_titles = [s.title for s in ch5.sections]
        assert "Plate Girder Design" in sec_titles
        assert "Deck Slab Design" in sec_titles
        assert "Cross Bracing Design" in sec_titles
        assert "End Diaphragm Design" in sec_titles
        assert "Overall Design Check Summary" in sec_titles

        sec_pg = find_section(ch5, "Plate Girder Design")
        t_is = find_table(sec_pg, "Intermediate Stiffener Checks")
        assert len(t_is.groups) == 5

        # Deck intermediate tables all present
        sec_dk = find_section(ch5, "Deck Slab Design")
        assert find_table(sec_dk, "Deck Slab --- Loading and Geometry") is not None
        assert find_table(sec_dk, "Deck Slab --- Flexure Check: Interior Panel") is not None
        assert find_table(sec_dk, "Deck Slab --- Cantilever Overhang Flexure Check") is not None
        assert find_table(sec_dk, "Deck Slab --- Punching Shear Check") is not None
        assert find_table(sec_dk, "Crack Width Check (Deck Slab)") is not None
        assert find_table(sec_dk, "One-Way (Beam) Shear Check (Deck Slab)") is not None
        assert find_table(sec_dk, "Reinforcement Detailing Summary (Deck Slab)") is not None

        # Cross bracing: 4 pairs
        sec_cb = find_section(ch5, "Cross Bracing Design")
        t_cb = find_table(sec_cb, "Cross Bracing --- Connection and Section Properties")
        assert len(t_cb.rows) == 4 * 2

        # Overall summary: Detailed check rows
        t_sum = find_table(find_section(ch5, "Overall Design Check Summary"), "Overall Design Check Summary")
        assert len(t_sum.rows) >= 4

        # Material Takeoff: Non-empty structural steel & concrete
        ch7 = find_chapter(doc, 7)
        t_takeoff = find_table(ch7, "Bill of Materials")
        assert len(t_takeoff.rows) >= 3

        # Parity: Clean with 0 regressions
        assert parity.is_clean
        assert parity.total_regressions == 0


class TestAcceptanceConfigurationC:
    """Configuration C: 10 Girders Heavy Bridge (9 Bracing Panels, Multi-Page Scaling)."""

    def test_pipeline_configuration_c(self):
        facts, doc, latex, parity = _run_full_pipeline_for_configuration(
            n_girders=10,
            has_intermediate_stiffeners=True,
            has_deck=True,
            has_footpath=True,
        )

        # 10 Girders across Chapter 2 and Chapter 5
        ch2 = find_chapter(doc, 2)
        t_ggi = find_table(find_section(ch2, "Additional Inputs"), "Girder General Information")
        assert len(t_ggi.rows) == 10

        ch5 = find_chapter(doc, 5)
        sec_pg = find_section(ch5, "Plate Girder Design")
        t_flex = find_table(sec_pg, "Moment Capacity Check")
        assert len(t_flex.groups) == 10
        assert [g.label for g in t_flex.groups] == [f"G{i}" for i in range(1, 11)]

        # 9 Cross bracing pairs
        sec_cb = find_section(ch5, "Cross Bracing Design")
        t_cb = find_table(sec_cb, "Cross Bracing --- Connection and Section Properties")
        assert len(t_cb.rows) == 9 * 2

        # Parity: Clean
        assert parity.is_clean
        assert parity.total_regressions == 0


class TestAcceptanceConfigurationD:
    """Configuration D: Partial Data / Optional Engineering Sections Unavailable."""

    def test_pipeline_configuration_d(self):
        facts, doc, latex, parity = _run_full_pipeline_for_configuration(
            n_girders=4,
            has_intermediate_stiffeners=False,
            has_deck=False,
            has_end_diaphragm=False,
            has_footpath=False,
        )

        # Chapter 5: Deck section omitted cleanly
        ch5 = find_chapter(doc, 5)
        sec_titles = [s.title for s in ch5.sections]
        assert "Plate Girder Design" in sec_titles
        assert not any("Deck Slab" in t for t in sec_titles)

        # Intermediate Stiffeners omitted cleanly
        sec_pg = find_section(ch5, "Plate Girder Design")
        tables_pg = get_all_tables(sec_pg)
        assert not any("Intermediate Stiffener Checks" in t.caption for t in tables_pg)

        # Parity: 0 regressions
        assert parity.is_clean
        assert parity.total_regressions == 0


class TestProductionReportGeneratorAcceptance:
    """End-to-end acceptance testing through generate_report() API."""

    @pytest.fixture(autouse=True)
    def mock_subprocess(self):
        from unittest import mock
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            yield mock_run

    @pytest.mark.parametrize("n_girders,has_stiffeners,has_deck", [
        (3, False, True),
        (5, True, True),
        (10, True, True),
        (4, False, False),
    ])
    def test_full_generate_report_orchestrator(self, tmp_path, monkeypatch, n_girders, has_stiffeners, has_deck):
        from osdagbridge.core.reports.report_generator import (
            generate_report,
            ReportPayload,
            ReportMetadata,
            ReportOptions,
            ReportFigures,
        )
        import osdagbridge.core.reports.report_generator as rg

        facts = _build_synthetic_facts(
            n_girders=n_girders,
            has_intermediate_stiffeners=has_stiffeners,
            has_deck=has_deck,
        )

        metadata = ReportMetadata(
            project_name=f"Acceptance Bridge {n_girders}G",
            project_location="Test City, India",
            designer="Acceptance Engineer",
            client="NHAI / Ministry of Road Transport",
            company="OsdagBridge Production",
            report_date="August 2026",
        )
        options = ReportOptions(
            sections=["loads", "analysis", "design_checks", "drawings", "quantities"],
            include_figures=True,
            include_toc=True,
            include_pdf=True,
        )
        payload = ReportPayload(
            metadata=metadata,
            options=options,
            inputs=facts.raw_input_dict or {},
            analysis_summary={},
            design_checks=facts.design_checks,
            output_dict=facts.raw_output_dict or {},
            figures=ReportFigures(),
        )

        class DummyRequest:
            def __init__(self, output_dir):
                self.output_dir = output_dir
                self.file_stem = f"acceptance_bridge_{n_girders}g"

        monkeypatch.setattr(rg, "REPORT_ENGINE_ENABLED", True)
        generate_report(payload, DummyRequest(str(tmp_path)))

        tex_file = tmp_path / f"acceptance_bridge_{n_girders}g.tex"
        assert tex_file.exists()
        latex = tex_file.read_text(encoding="utf-8")

        # Core sanity assertions on produced LaTeX
        assert r"\begin{document}" in latex
        assert r"\begin{longtable}" in latex
        assert r"\endhead" in latex
        assert r"\end{document}" in latex
        assert f"acceptance_bridge_{n_girders}g" in str(tex_file)

