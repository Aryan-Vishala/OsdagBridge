"""
Stage 3: Legacy vs Semantic Structural Manifest Test Suite
==========================================================

Verifies structural parity, intentional transformations, and configuration-dependent
behavior between the Legacy report generator and the Semantic Report Engine.

Invariants Enforced:
1. Every piece of engineering information present in the legacy report must either be:
   - PRESERVED in the semantic report
   - Explicitly catalogued as an INTENTIONAL_TRANSFORMATION (e.g. Table 3.3 live load split)
   - CONFIGURATION_DEPENDENT based on bridge inputs
2. Zero unexpected MISSING_REGRESSION elements across 3, 5, and 10 girder bridge configurations.
3. Automated regression tripwires that immediately fail if any engineering check or table is dropped.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from osdagbridge.core.report_engine.document import Chapter, ReportDocument, Section, Table
from osdagbridge.core.report_engine.document_builder import build_report_document
from osdagbridge.core.report_engine.manifest import (
    ParityStatus,
    ParityReport,
    ReportManifest,
    extract_legacy_manifest_from_payload,
    extract_semantic_manifest,
    compare_manifests,
)
from tests.contract.test_report_contract import _build_synthetic_facts


class DummyPayload:
    def __init__(self, facts):
        self.inputs = facts.raw_input_dict or {}
        self.output_dict = facts.raw_output_dict or {}
        self.design_checks = facts.design_checks or []
        self.metadata = facts.metadata


@pytest.fixture
def facts_5_girder():
    return _build_synthetic_facts(n_girders=5, has_intermediate_stiffeners=True, has_deck=True)


@pytest.fixture
def facts_3_girder():
    return _build_synthetic_facts(n_girders=3, has_intermediate_stiffeners=False, has_deck=True)


@pytest.fixture
def facts_10_girder():
    return _build_synthetic_facts(n_girders=10, has_intermediate_stiffeners=True, has_deck=True)


class TestStructuralManifest:
    """Test manifest extraction, parity comparison, and regression detection."""

    def test_semantic_manifest_extraction(self, facts_5_girder):
        """Verify semantic document AST is accurately converted to a ReportManifest."""
        doc = build_report_document(facts_5_girder, include_sections=["loads", "design_checks"])
        man = extract_semantic_manifest(doc)

        assert len(man.chapters) == 4
        ch2 = man.get_chapter(2)
        assert ch2 is not None
        assert ch2.title == "Input Parameters"

        # Check section names
        sec_titles = [s.title for s in ch2.sections]
        assert "Basic Inputs (User-Defined)" in sec_titles
        assert "Additional Inputs" in sec_titles

        # Check Chapter 5 tables
        ch5 = man.get_chapter(5)
        assert ch5 is not None
        all_ch5_tables = list(ch5.tables)
        for s in ch5.sections:
            all_ch5_tables.extend(s.tables)

        captions = [t.caption for t in all_ch5_tables]
        assert any("Moment Capacity Check" in c for c in captions)
        assert any("Shear Capacity Check" in c for c in captions)
        assert any("Punching Shear Check" in c for c in captions)
        assert any("Reinforcement Detailing Summary" in c for c in captions)

    def test_legacy_manifest_extraction(self, facts_5_girder):
        """Verify legacy LaTeX generation is cleanly parsed into a ReportManifest."""
        payload = DummyPayload(facts_5_girder)
        legacy_man = extract_legacy_manifest_from_payload(payload)

        assert len(legacy_man.chapters) == 4
        ch2 = legacy_man.get_chapter(2)
        assert ch2 is not None
        assert ch2.title == "Input Parameters"

        ch5 = legacy_man.get_chapter(5)
        assert ch5 is not None
        assert ch5.title == "Design Checks"

    def test_5_girder_full_parity_comparison(self, facts_5_girder):
        """Compare 5-girder legacy and semantic reports for full parity without regressions."""
        payload = DummyPayload(facts_5_girder)
        legacy_man = extract_legacy_manifest_from_payload(payload)

        doc = build_report_document(facts_5_girder, include_sections=["loads", "design_checks"])
        semantic_man = extract_semantic_manifest(doc)

        report = compare_manifests(legacy_man, semantic_man)
        formatted = report.format_report()
        print("\n" + formatted)

        # Assert zero regressions
        report.assert_no_regressions()
        assert report.is_clean
        assert report.total_preserved > 0
        assert report.total_intentional > 0

        # Assert specific intentional transformations were identified
        ch3_parity = [cp for cp in report.chapter_parities if cp.chapter_number == 3][0]
        assert any("split" in item.name.lower() for item in ch3_parity.items)

        ch5_parity = [cp for cp in report.chapter_parities if cp.chapter_number == 5][0]
        assert any("intermediate stiffener" in item.name.lower() for item in ch5_parity.items)

    def test_3_girder_no_intermediate_stiffeners_parity(self, facts_3_girder):
        """Verify parity on a 3-girder bridge without intermediate stiffeners."""
        payload = DummyPayload(facts_3_girder)
        legacy_man = extract_legacy_manifest_from_payload(payload)

        doc = build_report_document(facts_3_girder, include_sections=["loads", "design_checks"])
        semantic_man = extract_semantic_manifest(doc)

        report = compare_manifests(legacy_man, semantic_man)
        report.assert_no_regressions()
        assert report.is_clean

    def test_10_girder_heavy_bridge_parity(self, facts_10_girder):
        """Verify parity on a 10-girder heavy bridge."""
        payload = DummyPayload(facts_10_girder)
        legacy_man = extract_legacy_manifest_from_payload(payload)

        doc = build_report_document(facts_10_girder, include_sections=["loads", "design_checks"])
        semantic_man = extract_semantic_manifest(doc)

        report = compare_manifests(legacy_man, semantic_man)
        report.assert_no_regressions()
        assert report.is_clean

    def test_regression_detection_tripwire(self, facts_5_girder):
        """Tripwire test: Artificially removing a table must trigger an immediate assertion error."""
        payload = DummyPayload(facts_5_girder)
        legacy_man = extract_legacy_manifest_from_payload(payload)

        doc = build_report_document(facts_5_girder, include_sections=["loads", "design_checks"])
        # Artificially remove Chapter 5 Section 5.1
        ch5 = [c for c in doc.chapters if c.number == 5][0]
        ch5.sections = [s for s in ch5.sections if "Plate Girder" not in s.title]

        semantic_man = extract_semantic_manifest(doc)
        report = compare_manifests(legacy_man, semantic_man)

        assert not report.is_clean
        assert report.total_regressions > 0
        with pytest.raises(AssertionError, match="Structural Manifest Parity Failed"):
            report.assert_no_regressions()
