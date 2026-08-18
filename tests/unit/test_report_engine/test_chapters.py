"""Tests for chapter builder functions (Phase B–E: legacy adapter pattern)."""

from unittest.mock import patch

import pytest

from osdagbridge.core.report_engine.facts import (
    CheckStatus,
    DesignCheckData,
    FactMetadata,
    GirderClassification,
    GirderDeflectionCheck,
    GirderDesignData,
    GirderDesignSummary,
    GirderFatigueCheck,
    GirderFlexureCheck,
    GirderInteractionCheck,
    GirderLTBCheck,
    GirderSectionProperties,
    GirderShearCheck,
    GirderBearingStiffenerCheck,
    GirderStiffenerSummary,
    GirderStressCheck,
    InputFacts,
    QuantityValue,
    ReportFacts,
)
from osdagbridge.core.report_engine.document import Chapter, Column, RawLatex, Section, Table, TableGroup


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_facts(**overrides) -> ReportFacts:
    """Return a minimal ReportFacts with raw_input_dict populated."""
    defaults = dict(
        metadata=FactMetadata(
            project_name="Test Bridge",
            project_location="Mumbai",
            designer=" Tester",
            client="Client",
            company="Co",
        ),
        raw_input_dict={"span": 30, "girder_steel_grade": "E350"},
        raw_output_dict={},
        design_checks=[],
    )
    defaults.update(overrides)
    return ReportFacts(**defaults)


# ---------------------------------------------------------------------------
# Chapter 2
# ---------------------------------------------------------------------------

class TestBuildChapter2:
    @patch("osdagbridge.core.reports.chap2.ch2_input_parameters")
    def test_returns_chapter_with_raw_latex(self, mock_fn):
        mock_fn.return_value = (
            r"\chapter{Input Parameters}"
            r"\setlength{\abovecaptionskip}{2pt}"
            r"\begin{table}[H]"
            r"\caption{\textbf{Project Location}}"
            r"\begin{tabular}{...}"
            r"\end{tabular}"
            r"\end{table}"
            r"Hello world"
        )
        facts = _make_facts()

        from osdagbridge.core.report_engine.chapters.ch2_document import build_chapter_2
        ch = build_chapter_2(facts)

        assert isinstance(ch, Chapter)
        assert ch.number == 2
        assert ch.title == "Input Parameters"
        assert len(ch.sections) == 1
        assert isinstance(ch.sections[0].components[0], RawLatex)
        assert "Hello world" in ch.sections[0].components[-1].content
        mock_fn.assert_called_once()

    @patch("osdagbridge.core.reports.chap2.ch2_input_parameters")
    def test_passes_raw_input_dict(self, mock_fn):
        mock_fn.return_value = r"\chapter{Input Parameters}"
        facts = _make_facts(raw_input_dict={"span": 40})

        from osdagbridge.core.report_engine.chapters.ch2_document import build_chapter_2
        build_chapter_2(facts)

        call_args = mock_fn.call_args
        # Second positional arg is input_dict
        assert call_args[0][1] == {"span": 40}

    @patch("osdagbridge.core.reports.chap2.ch2_input_parameters")
    def test_passes_raw_output_dict(self, mock_fn):
        mock_fn.return_value = r"\chapter{Input Parameters}"
        facts = _make_facts(raw_output_dict={"some_key": "val"})

        from osdagbridge.core.report_engine.chapters.ch2_document import build_chapter_2
        build_chapter_2(facts)

        call_args = mock_fn.call_args
        # Third positional arg is output_dict
        assert call_args[0][2] == {"some_key": "val"}


# ---------------------------------------------------------------------------
# Chapter 3 — migrated: uses build_load_facts, returns semantic Tables
# ---------------------------------------------------------------------------

class TestBuildChapter3:
    def test_returns_chapter_with_semantic_tables(self):
        facts = _make_facts()

        from osdagbridge.core.report_engine.chapters.ch3_document import build_chapter_3
        ch = build_chapter_3(facts)

        assert isinstance(ch, Chapter)
        assert ch.number == 3
        assert ch.title == "Loads and Load Combinations"
        assert len(ch.sections) == 1
        assert ch.sections[0].title == ""

    def test_raw_latex_note_present(self):
        facts = _make_facts()

        from osdagbridge.core.report_engine.chapters.ch3_document import build_chapter_3
        ch = build_chapter_3(facts)

        from osdagbridge.core.report_engine.document import RawLatex
        raw_components = [c for c in ch.sections[0].components if isinstance(c, RawLatex)]
        assert any("auto-generated" in r.content for r in raw_components)

    def test_tables_are_table_instances(self):
        facts = _make_facts()

        from osdagbridge.core.report_engine.chapters.ch3_document import build_chapter_3
        ch = build_chapter_3(facts)

        from osdagbridge.core.report_engine.document import Table
        tables = [c for c in ch.sections[0].components if isinstance(c, Table)]
        assert len(tables) == 7
        captions = [t.caption for t in tables]
        assert "Dead Load -- Self Weight" in captions
        assert "Live Loads (LL)" in captions
        assert "Load Combinations" in captions

    def test_dead_load_table_reads_from_facts(self):
        facts = _make_facts()

        from osdagbridge.core.report_engine.chapters.ch3_document import build_chapter_3
        ch = build_chapter_3(facts)

        from osdagbridge.core.report_engine.document import Table
        tables = [c for c in ch.sections[0].components if isinstance(c, Table)]
        dl_table = next(t for t in tables if "Dead Load" in t.caption)
        assert len(dl_table.rows) == 3
        assert dl_table.rows[0][0] == "Steel Self-Weight Applied"
        assert dl_table.rows[1][0] == "Concrete Deck Weight"
        assert dl_table.rows[2][0] == "Self-Weight Factor"

    def test_load_combination_table_has_rows(self):
        facts = _make_facts()

        from osdagbridge.core.report_engine.chapters.ch3_document import build_chapter_3
        ch = build_chapter_3(facts)

        from osdagbridge.core.report_engine.document import Table
        tables = [c for c in ch.sections[0].components if isinstance(c, Table)]
        lc_table = next(t for t in tables if t.caption == "Load Combinations")
        assert len(lc_table.rows) >= 13


# ---------------------------------------------------------------------------
# Chapter 7
# ---------------------------------------------------------------------------

class TestBuildChapter7:
    def test_returns_chapter_with_table(self):
        facts = _make_facts(raw_input_dict={"typical_section.no_of_girders": "4"})
        from osdagbridge.core.report_engine.chapters.ch7_document import build_chapter_7
        from osdagbridge.core.report_engine.document import Table
        
        ch = build_chapter_7(facts)

        assert isinstance(ch, Chapter)
        assert ch.number == 7
        assert "Quantity Summary" in ch.title
        assert isinstance(ch.sections[0].components[0], Table)
        
        table = ch.sections[0].components[0]
        assert len(table.rows) == 9 # 9 rows for items 1-6 including subitems


# ---------------------------------------------------------------------------
# Chapter 5
# ---------------------------------------------------------------------------

class TestBuildChapter5:
    @patch("osdagbridge.core.reports.chap5.ch5_design_checks")
    @patch("osdagbridge.core.reports.report_generator.ReportDataBridge")
    def test_returns_chapter_with_raw_latex(self, MockBridge, mock_fn):
        mock_fn.return_value = r"\chapter{Design Checks}Check content"
        facts = _make_facts(design_checks=["girder_flexure"])

        from osdagbridge.core.report_engine.chapters.ch5_document import build_chapter_5
        ch = build_chapter_5(facts)

        assert isinstance(ch, Chapter)
        assert ch.number == 5
        assert ch.title == "Design Checks"
        assert isinstance(ch.sections[0].components[0], RawLatex)
        assert "Check content" in ch.sections[0].components[0].content
        # Verify bridge was constructed with raw dicts
        MockBridge.assert_called_once()
        call_args = MockBridge.call_args
        assert call_args[0][0] == {}  # output_dict (empty default)
        assert call_args[0][1] == {"span": 30, "girder_steel_grade": "E350"}  # input_dict
        mock_fn.assert_called_once()


# ---------------------------------------------------------------------------
# document_builder wiring
# ---------------------------------------------------------------------------

class TestDocumentBuilder:
    @patch("osdagbridge.core.report_engine.chapters.ch7_document.build_chapter_7")
    @patch("osdagbridge.core.report_engine.chapters.ch5_document.build_chapter_5")
    @patch("osdagbridge.core.report_engine.chapters.ch3_document.build_chapter_3")
    @patch("osdagbridge.core.report_engine.chapters.ch2_document.build_chapter_2")
    def test_always_includes_ch2_and_ch7(self, mock2, mock3, mock5, mock7):
        mock2.return_value = Chapter(number=2, title="Input Parameters")
        mock3.return_value = Chapter(number=3, title="Loads")
        mock5.return_value = Chapter(number=5, title="Design Checks")
        mock7.return_value = Chapter(number=7, title="Material Take-off")

        facts = _make_facts()
        from osdagbridge.core.report_engine.document_builder import build_report_document
        doc = build_report_document(facts, include_sections=[])

        # Ch2 and Ch7 always included even with empty include_sections
        assert len(doc.chapters) == 2
        assert doc.chapters[0].number == 2
        assert doc.chapters[1].number == 7

    @patch("osdagbridge.core.report_engine.chapters.ch7_document.build_chapter_7")
    @patch("osdagbridge.core.report_engine.chapters.ch5_document.build_chapter_5")
    @patch("osdagbridge.core.report_engine.chapters.ch3_document.build_chapter_3")
    @patch("osdagbridge.core.report_engine.chapters.ch2_document.build_chapter_2")
    def test_includes_ch3_when_loads_selected(self, mock2, mock3, mock5, mock7):
        mock2.return_value = Chapter(number=2, title="Input Parameters")
        mock3.return_value = Chapter(number=3, title="Loads")
        mock5.return_value = Chapter(number=5, title="Design Checks")
        mock7.return_value = Chapter(number=7, title="Material Take-off")

        facts = _make_facts()
        from osdagbridge.core.report_engine.document_builder import build_report_document
        doc = build_report_document(facts, include_sections=["loads"])

        chapter_numbers = [ch.number for ch in doc.chapters]
        assert 3 in chapter_numbers

    @patch("osdagbridge.core.report_engine.chapters.ch7_document.build_chapter_7")
    @patch("osdagbridge.core.report_engine.chapters.ch5_document.build_chapter_5")
    @patch("osdagbridge.core.report_engine.chapters.ch3_document.build_chapter_3")
    @patch("osdagbridge.core.report_engine.chapters.ch2_document.build_chapter_2")
    def test_includes_ch5_when_design_checks_selected(self, mock2, mock3, mock5, mock7):
        mock2.return_value = Chapter(number=2, title="Input Parameters")
        mock3.return_value = Chapter(number=3, title="Loads")
        mock5.return_value = Chapter(number=5, title="Design Checks")
        mock7.return_value = Chapter(number=7, title="Material Take-off")

        facts = _make_facts()
        from osdagbridge.core.report_engine.document_builder import build_report_document
        doc = build_report_document(facts, include_sections=["design_checks"])

        chapter_numbers = [ch.number for ch in doc.chapters]
        assert 5 in chapter_numbers

    def test_no_chapters_when_no_raw_input(self):
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="Test",
                project_location="",
                designer="",
                client="",
                company="",
            ),
        )
        from osdagbridge.core.report_engine.document_builder import build_report_document
        doc = build_report_document(facts, include_sections=["loads", "design_checks"])
        assert len(doc.chapters) == 0
