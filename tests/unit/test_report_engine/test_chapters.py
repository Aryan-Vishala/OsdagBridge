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
    def test_returns_chapter_with_semantic_sections(self):
        facts = _make_facts()
        from osdagbridge.core.report_engine.chapters.ch2_document import build_chapter_2
        ch = build_chapter_2(facts)

        assert isinstance(ch, Chapter)
        assert ch.number == 2
        assert ch.title == "Input Parameters"
        assert len(ch.sections) == 3
        assert ch.sections[0].title == ""
        assert ch.sections[1].title == "Basic Inputs (User-Defined)"
        assert ch.sections[2].title == "Additional Inputs"

        sec1_tables = [c.caption for c in ch.sections[1].components if isinstance(c, Table)]
        sec2_tables = [c.caption for c in ch.sections[2].components if isinstance(c, Table)]

        assert sec1_tables == ["Project Location", "Bridge Geometry", "Material Selection"]
        assert sec2_tables == [
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


# ---------------------------------------------------------------------------
# Chapter 3
# ---------------------------------------------------------------------------

class TestBuildChapter3:
    def test_returns_chapter_with_paragraph_and_all_tables(self):
        facts = _make_facts()
        from osdagbridge.core.report_engine.chapters.ch3_document import build_chapter_3
        from osdagbridge.core.report_engine.document import Paragraph
        ch = build_chapter_3(facts)

        assert isinstance(ch, Chapter)
        assert ch.number == 3
        assert ch.title == "Loads and Load Combinations"

        comps = ch.sections[0].components
        assert any(isinstance(c, Paragraph) for c in comps)
        tables = [c.caption for c in comps if isinstance(c, Table)]
        assert len(tables) == 8
        assert "Dead Load -- Self Weight" in tables
        assert "Dead Load for Surfacing (DW)" in tables
        assert "Vehicle Live Loads" in tables
        assert "Footway Load" in tables
        assert "Wind Load (WL) --- per IRC 6" in tables
        assert "Earthquake Load (EL) --- per IRC 6" in tables
        assert "Temperature Load (TL) --- per IRC 6" in tables
        assert "Load Combinations" in tables


# ---------------------------------------------------------------------------
# Chapter 5 Tables
# ---------------------------------------------------------------------------

class TestChapter5Tables:
    def test_build_table_5_17a_formatting(self):
        from osdagbridge.core.report_engine.chapters.ch5_document import _build_table_5_17a
        from osdagbridge.core.report_engine.facts import DeckDesignData, DeckLoadingGeometry, QuantityValue
        from osdagbridge.core.report_engine.document import Math

        # Mock deck design data with numeric/string properties
        dk = DeckDesignData(
            loading=DeckLoadingGeometry(
                effective_span=QuantityValue(10, "m"),
                thickness=QuantityValue(200, "mm"),
                concrete_grade="M35",
                fck=QuantityValue(35, "MPa"),
                fctm=QuantityValue(2.8, "MPa"),
                reinf_grade="Fe500",
                fy=QuantityValue(500, "MPa"),
                dead_load=QuantityValue(50, "kN/m²"),
                vehicle="Class A",
                impact_factor=1.23,
                wheel_load=QuantityValue(114, "kN"),
                tyre_width=QuantityValue(500, "mm"),
            ),
            flexure=None,
            shear=None,
            crack_width=None,
            detailing=None,
        )
        
        table = _build_table_5_17a(dk)
        assert len(table.rows) == 10
        assert table.rows[3][0] == r"Concrete Grade (IRC 112 Cl. 6.4)"
        assert table.rows[3][1][0] == "M35"
        assert isinstance(table.rows[3][1][2], Math)
        assert table.rows[3][1][2].content == r"f_{ck}"

    def test_build_table_5_17b_to_g(self):
        from osdagbridge.core.report_engine.chapters.ch5_document import (
            _build_table_5_17b, _build_table_5_17c, _build_table_5_17d,
            _build_table_5_17e, _build_table_5_17f, _build_table_5_17g
        )
        from osdagbridge.core.report_engine.facts import (
            DeckDesignData, DeckFlexureCheck, DeckShearCheck,
            DeckCrackWidthCheck, DeckDetailingCheck, QuantityValue, CheckStatus
        )
        from osdagbridge.core.report_engine.document import Math

        dk = DeckDesignData(
            flexure=DeckFlexureCheck(
                m_dl_sag=QuantityValue(15, "kN-m/m"),
                m_ll_sag=QuantityValue(25, "kN-m/m"),
                gamma_dl=1.35,
                gamma_ll=1.50,
                demand_sagging=QuantityValue(100, "kN-m/m"),
                d_bot=QuantityValue(194, "mm"),
                capacity_sagging=QuantityValue(120, "kN-m/m"),
                status_sagging=CheckStatus.PASS,
                demand_hogging=QuantityValue(80, "kN-m/m"),
                required_top_steel=QuantityValue(488, "mm²/m"),
                capacity_hogging=QuantityValue(100, "kN-m/m"),
                status_hogging=CheckStatus.PASS,
                has_overhang=True,
                overhang_length=QuantityValue(1.2, "m"),
                m_barrier=QuantityValue(7.5, "kN-m/m"),
                m_dl_oh=QuantityValue(5.25, "kN-m/m"),
                m_ll_oh=QuantityValue(51.3, "kN-m/m"),
                demand_overhang=QuantityValue(40, "kN-m/m"),
                capacity_overhang=QuantityValue(60, "kN-m/m"),
                status_overhang=CheckStatus.PASS
            ),
            shear=DeckShearCheck(
                punching_ved_kn=QuantityValue(150, "kN"),
                tyre_length=QuantityValue(150, "mm"),
                tyre_width=QuantityValue(300, "mm"),
                punching_c1=QuantityValue(400, "mm"),
                punching_c2=QuantityValue(250, "mm"),
                punching_u1=QuantityValue(3738, "mm"),
                punching_ved_mpa=QuantityValue(0.19, "MPa"),
                punching_vrdc_mpa=QuantityValue(0.55, "MPa"),
                punching_ur=0.34,
                punching_status=CheckStatus.PASS,
                oneway_ved=QuantityValue(80, "kN/m"),
                d_bot=QuantityValue(194, "mm"),
                oneway_size_factor_k=2.0,
                oneway_rho_l=0.0033,
                oneway_vrdc=QuantityValue(100, "kN/m"),
                oneway_ur=0.8,
                oneway_status=CheckStatus.PASS,
            ),
            crack_width=DeckCrackWidthCheck(
                as_min=QuantityValue(303, "mm²/m"),
                dia_bot=QuantityValue(12, "mm"),
                spc_bot=QuantityValue(175, "mm"),
                as_bot=QuantityValue(646, "mm²/m"),
                limit=QuantityValue(0.3, "mm"),
                calculated=QuantityValue(0.21, "mm"),
                status=CheckStatus.PASS
            ),
            detailing=DeckDetailingCheck(
                required_bottom=QuantityValue(611, "mm²/m"),
                provided_bottom=QuantityValue(646, "mm²/m"),
                dia_bot=QuantityValue(12, "mm"),
                spc_bot=QuantityValue(175, "mm"),
                as_min=QuantityValue(303, "mm²/m"),
                spc_max=QuantityValue(300, "mm"),
                required_dist=QuantityValue(300, "mm²/m"),
                provided_dist=QuantityValue(377, "mm²/m"),
                required_top=QuantityValue(488, "mm²/m"),
                provided_top=QuantityValue(492, "mm²/m"),
                min_cover=QuantityValue(50, "mm"),
                top_cover=QuantityValue(50, "mm"),
                bot_cover=QuantityValue(50, "mm"),
                status_bottom=CheckStatus.PASS,
                status_dist=CheckStatus.PASS,
                status_top=CheckStatus.PASS,
                status_cover=CheckStatus.PASS
            )
        )
        
        # Test 5.17b - Flexure
        t_b = _build_table_5_17b(dk)
        assert t_b.caption == "Deck Slab --- Flexure Check: Interior Panel (Pigeaud's Method)"
        assert len(t_b.columns) == 5
        assert len(t_b.rows) == 8
        assert t_b.rows[0][0] == "At Midspan (Sagging)"
        assert t_b.rows[5][0] == "At Support (Hogging)"
        
        # Test 5.17c - Overhang
        t_c = _build_table_5_17c(dk)
        assert t_c.caption == "Deck Slab --- Cantilever Overhang Flexure Check"
        assert len(t_c.rows) == 6
        assert t_c.rows[1][0] == "Crash Barrier Load Moment"
        
        # Test 5.17d - Punching shear
        t_d = _build_table_5_17d(dk)
        assert t_d.caption == "Deck Slab --- Punching Shear Check (IRC 112 Cl. 10.4.6)"
        assert len(t_d.rows) == 7
        assert t_d.rows[1][0] == "Tyre Contact Area"
        assert "Control Perimeter" in t_d.rows[3][0][0]
        
        # Test 5.17e - Crack width
        t_e = _build_table_5_17e(dk)
        assert t_e.caption == "Crack Width Check (Deck Slab)"
        assert len(t_e.rows) == 5
        assert "Min. Reinforcement for Crack Control" in t_e.rows[0][0][0]
        assert t_e.rows[1][0] == "Provided Reinforcement (bottom)"
        
        # Test 5.17f - One-way shear
        t_f = _build_table_5_17f(dk)
        assert len(t_f.rows) == 6
        assert "Effective depth" in t_f.rows[1][0][0]
        assert t_f.rows[5][0] == "One-Way Shear Check"
        
        # Test 5.17g - Detailing
        t_g = _build_table_5_17g(dk)
        assert t_g.caption == "Reinforcement Detailing Summary (Deck Slab)"
        assert len(t_g.rows) == 11



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

    def test_load_combinations_note_present(self):
        facts = _make_facts()

        from osdagbridge.core.report_engine.chapters.ch3_document import build_chapter_3
        ch = build_chapter_3(facts)

        from osdagbridge.core.report_engine.document import Table
        tables = [c for c in ch.sections[0].components if isinstance(c, Table)]
        assert any("auto-generated" in (t.note or "") for t in tables)

    def test_tables_are_table_instances(self):
        facts = _make_facts()

        from osdagbridge.core.report_engine.chapters.ch3_document import build_chapter_3
        ch = build_chapter_3(facts)

        from osdagbridge.core.report_engine.document import Table
        tables = [c for c in ch.sections[0].components if isinstance(c, Table)]
        assert len(tables) == 8
        captions = [t.caption for t in tables]
        assert "Dead Load -- Self Weight" in captions
        assert "Vehicle Live Loads" in captions
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

    def test_returns_chapter_with_charts(self):
        facts = _make_facts(raw_input_dict={"typical_section.no_of_girders": "4"})
        from osdagbridge.core.report_engine.chapters.ch7_document import build_chapter_7
        from osdagbridge.core.report_engine.document import Chart
        
        ch = build_chapter_7(facts)
        
        charts = [c for c in ch.sections[0].components if isinstance(c, Chart)]
        assert len(charts) == 3
        
        assert charts[0].title == "Structural Steel Quantities"
        assert "Girders" in charts[0].data
        assert "Cross Bracing" in charts[0].data
        assert "End Diaphragms" in charts[0].data
        
        assert charts[1].title == "Concrete Volume"
        assert "Concrete Deck Slab" in charts[1].data
        
        assert charts[2].title == "Reinforcement Steel"
        assert "Reinforcement Steel" in charts[2].data

    def test_charts_handle_missing_end_diaphragm(self):
        # We need to explicitly manipulate MaterialFacts to set end_diaphragm to None.
        facts = _make_facts()
        from osdagbridge.core.report_engine.chapters.ch7_document import build_chapter_7
        from osdagbridge.core.report_engine.facts.material_takeoff import build_material_facts
        mat_facts = build_material_facts(facts.raw_input_dict or {}, facts.raw_output_dict or {})
        
        # End diaphragm should be None natively because input_dict has no end diaphragm.
        assert mat_facts.structural_steel.end_diaphragms is None
        
        # Override the property
        facts = _make_facts()
        # Set material_facts attribute dynamically
        setattr(facts, "material_facts", mat_facts)
        
        ch = build_chapter_7(facts)
        from osdagbridge.core.report_engine.document import Chart
        charts = [c for c in ch.sections[0].components if isinstance(c, Chart)]
        
        assert charts[0].data["End Diaphragms"] is None

    def test_charts_preserve_genuine_zeros(self):
        facts = _make_facts()
        from osdagbridge.core.report_engine.chapters.ch7_document import build_chapter_7
        from osdagbridge.core.report_engine.facts import MaterialFacts, StructuralSteelTakeoff, TakeoffItem, QuantityValue
        
        # Create a MaterialFacts with a genuine 0.0 quantity
        zero_item = TakeoffItem("Zero Item", None, 0, None, None, QuantityValue(0.0, "MT"), None)
        mat_facts = MaterialFacts(
            structural_steel=StructuralSteelTakeoff(
                zero_item, zero_item, zero_item, zero_item, zero_item
            ),
            concrete_volume=None,
            reinforcement_steel=None,
            shear_studs=None,
            crash_barrier=None
        )
        setattr(facts, "material_facts", mat_facts)
        
        ch = build_chapter_7(facts)
        from osdagbridge.core.report_engine.document import Chart
        charts = [c for c in ch.sections[0].components if isinstance(c, Chart)]
        
        assert charts[0].data["Girders"] == 0.0
        assert charts[0].data["End Diaphragms"] == 0.0
        assert charts[1].data["Concrete Deck Slab"] is None
        assert charts[2].data["Reinforcement Steel"] is None


# ---------------------------------------------------------------------------
# Chapter 5
# ---------------------------------------------------------------------------

class TestBuildChapter5:
    def test_returns_all_five_subsections_with_end_diaphragm_tables(self):
        from osdagbridge.core.report_engine.chapters.ch5_document import build_chapter_5
        from osdagbridge.core.report_engine.facts.design_checks import (
            CrossBracingData, EndDiaphragmData, BracingPanelData, BracingMemberCheck,
            OverallSummaryData, ComponentSummary, SummaryCheckRecord
        )

        dummy_member = BracingMemberCheck(
            demand=QuantityValue(10, "kN"),
            capacity=QuantityValue(40, "kN"),
            ur=0.25,
            status=CheckStatus.PASS,
            governing_lc="1.5 EQ",
            connection_type="Bolted",
            section="40 x 40 x 3",
            gross_area=QuantityValue(237, "mm²"),
            rmin=QuantityValue(8, "mm"),
            effective_length=QuantityValue(2600, "mm"),
            slenderness=135.0,
            slenderness_limit=250.0,
        )
        dummy_panel = BracingPanelData(
            pair_label="G1-G2",
            diagonal_tension=dummy_member,
            diagonal_compression=dummy_member,
            chord_tension=dummy_member,
            chord_compression=dummy_member,
            slenderness_ur=0.54,
            slenderness_status=CheckStatus.PASS,
        )
        ed_data = EndDiaphragmData(diaphragm_type="Cross Bracing", panels=(dummy_panel,), flexural_checks=None)
        cb_data = CrossBracingData(panels=(dummy_panel,))
        comp_summary = ComponentSummary(
            component_name="End Diaphragms",
            records=(SummaryCheckRecord(label="End Diaphragm --- Tension", demand=QuantityValue(10, "kN"), capacity=QuantityValue(40, "kN"), ur=0.25, status=CheckStatus.PASS, governing_lc="1.5 EQ"),),
            max_ur=0.25,
            status=CheckStatus.PASS,
        )
        summary_data = OverallSummaryData(
            girders=comp_summary,
            deck=comp_summary,
            cross_bracing=comp_summary,
            end_diaphragm=comp_summary,
        )
        
        design_data = DesignCheckData(
            girders=(),
            deck=None,
            shear_connectors=None,
            cross_bracing=cb_data,
            end_diaphragm=ed_data,
            summary=summary_data,
        )
        facts = _make_facts(design_check_data=design_data)
        ch = build_chapter_5(facts)

        sec_titles = [s.title for s in ch.sections]
        assert "Cross Bracing Design" in sec_titles
        assert "End Diaphragm Design" in sec_titles
        assert "Overall Design Check Summary" in sec_titles

        # Check End Diaphragm tables
        ed_sec = next(s for s in ch.sections if s.title == "End Diaphragm Design")
        ed_tables = [c.caption for c in ed_sec.components if isinstance(c, Table)]
        assert "End Diaphragm --- Connection and Section Properties" in ed_tables
        assert "End Diaphragm --- Slenderness Ratio Check (IS 800 Cl. 3.8)" in ed_tables
        assert "End Diaphragm Design --- Capacity Summary" in ed_tables

        # Check Overall Summary table
        sum_sec = next(s for s in ch.sections if s.title == "Overall Design Check Summary")
        sum_tables = [c.caption for c in sum_sec.components if isinstance(c, Table)]
        assert "Overall Design Check Summary" in sum_tables

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

# ---------------------------------------------------------------------------
# Chapter 5 Formatting
# ---------------------------------------------------------------------------

class TestCh5Formatting:
    def test_table_5_20b_semantic_status(self):
        """Verify CheckStatus is preserved in structured Table 5.20b rows."""
        from osdagbridge.core.report_engine.chapters.ch5_document import _build_table_5_20b
        from osdagbridge.core.report_engine.facts import CrossBracingData, BracingPanelData, BracingMemberCheck, CheckStatus, QuantityValue

        cb = CrossBracingData(
            panels=[
                BracingPanelData(
                    pair_label="Panel 1",
                    diagonal_tension=None,
                    diagonal_compression=BracingMemberCheck(
                        demand=None, capacity=None, ur=0.82,
                        status=CheckStatus.PASS, governing_lc="ULS",
                        connection_type="Bolted", section="40 x 40 x 3",
                        effective_length=QuantityValue(value=2000, unit="mm"),
                        slenderness=150.0, slenderness_limit=250.0
                    ),
                    chord_tension=None, chord_compression=None,
                    slenderness_ur=0.82,
                    slenderness_status=CheckStatus.PASS,
                ),
            ]
        )
        table = _build_table_5_20b(cb)
        assert len(table.columns) == 7
        assert table.caption == "Cross Bracing --- Slenderness Ratio Check"
        assert table.rows[0] == ["Panel 1", "Diagonal", "C", "2000", "150.0", "250", CheckStatus.PASS]


# ---------------------------------------------------------------------------
# Content Parity & Dynamic Extraction Verification
# ---------------------------------------------------------------------------

class TestContentParity:
    def test_ch2_dynamic_stiffener_and_bracing_extraction(self):
        from osdagbridge.core.report_engine.chapters.ch2_document import (
            _build_girder_restraint_stiffener_table,
            _build_cross_bracing_details_table,
            _build_end_diaphragm_details_table,
        )
        sample_input = {
            "typical_section.no_of_girders": 2,
            "member_properties.girder_details.section_input.torsional_restraint.G1.M1": "Fully Restrained",
            "member_properties.girder_details.section_input.warping_restraint.G1.M1": "Both Flanges Restrained",
            "member_properties.stiffener_details.no_bearing_stiffeners_each_end.G1.M1": "4",
            "member_properties.stiffener_details.bearing_stiffener_spacing.G1.M1": "100",
            "member_properties.stiffener_details.bearing_stiffener_plate_thickness.G1.M1": "10",
            "member_properties.cross_bracing_details.bracing_section_designation.G1G2.B1M1": "IS 100 x 100 x 10",
            "member_properties.cross_bracing_details.spacing.G1G2.B1M1": "15.0",
            "member_properties.end_diaphragm_details.bracing_section_designation.G1G2.E1M1": "IS 90 x 90 x 8",
        }
        facts = ReportFacts(
            metadata=FactMetadata(project_name="T", project_location="", designer="", client="", company=""),
            inputs=InputFacts(),
            raw_input_dict=sample_input,
            raw_output_dict={},
        )
        t_grs = _build_girder_restraint_stiffener_table(facts)
        assert "No.: 4; Spacing: 100 mm; Thickness: 10 mm" in t_grs.rows[0][5]

        t_cbd = _build_cross_bracing_details_table(facts)
        assert t_cbd.rows[0][3] == "IS 100 x 100 x 10"
        assert t_cbd.rows[0][4] == "15.0 m"

        t_edd = _build_end_diaphragm_details_table(facts)
        assert t_edd.rows[0][3] == "IS 90 x 90 x 8"

    def test_deck_facts_dynamic_builder_preserves_engineering_values(self):
        from osdagbridge.core.report_engine.facts.design_checks import build_deck_design_data
        
        sample_input = {
            "typical_section.deck_thickness": 220,
            "deck_slab.top_clear_cover": 50,
            "deck_slab.bottom_clear_cover": 50,
            "material.deck": "M40",
            "material.deck.fck": 40,
            "material.deck.fctm": 3.03,
            "deck_slab.reinf_material": "Fe 500",
        }
        sample_deck_rpt = {
            "span": 2.5,
            "fy": 500,
            "w_dl": 7.42,
            "wheel_load": 114,
            "tyre_width": 0.5,
            "tyre_length": 150,
            "impact_factor": 1.25,
            "vehicle": "IRC Class A",
            "has_overhang": True,
            "m_uls_sag": 72.88,
            "mu_bot": 89.28,
            "m_uls_hog": 66.86,
            "mu_top": 89.28,
            "as_req_top": 723,
            "m_uls_oh": 84.14,
            "mu_oh": 89.28,
            "punch_ved_kn": 142.5,
            "punch_c1": 400,
            "punch_c2": 250,
            "punch_u1": 3738,
            "punch_ved": 0.19,
            "vrd_c_mpa": 0.55,
            "punch_ok": True,
            "shear_ved": 83.9,
            "shear_vrdc": 98.4,
            "shear_ok": True,
            "d_bot": 194,
            "as_bot": 646,
            "dia_bot": 12,
            "spc_bot": 175,
            "as_min": 303,
            "wk_limit": 0.3,
            "wk_bot": 0.21,
            "wk_top": 0.18,
            "wk_oh": 0.24,
            "as_req_bot": 611,
            "spacing_max": 300,
            "as_long": 377,
            "as_top": 492,
            "min_cover": 50,
            "cover_ok": True,
        }
        output_dict = {"deck_report_values": sample_deck_rpt}
        deck_data = build_deck_design_data(output_dict, sample_input)

        assert deck_data.is_designed is True
        assert deck_data.loading.concrete_grade == "M40"
        assert deck_data.loading.fck.value == 40
        assert deck_data.loading.fctm.value == 3.03
        assert deck_data.loading.thickness.value == 220
        assert deck_data.flexure.demand_sagging.value == 72.88
        assert deck_data.shear.punching_u1.value == 3738
        assert deck_data.shear.punching_ved_kn.value == 142.5
        assert deck_data.crack_width.calculated.value == 0.24
        assert deck_data.detailing.provided_bottom.value == 646

