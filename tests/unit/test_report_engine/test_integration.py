"""Integration test: full pipeline ReportFacts → document → LaTeX."""

from unittest.mock import patch

from osdagbridge.core.report_engine.facts import (
    FactMetadata,
    InputFacts,
    MaterialFacts,
    QuantityValue,
    ReportFacts,
    StructuralSteelTakeoff,
)
from osdagbridge.core.report_engine.document_builder import build_report_document
from osdagbridge.core.report_engine.renderer import LatexRenderer
from osdagbridge.core.report_engine.theme import ReportTheme


class TestFullPipeline:
    """End-to-end: ReportFacts → build_report_document → LatexRenderer → LaTeX."""

    @patch("osdagbridge.core.reports.chap7.ch7_quantities")
    @patch("osdagbridge.core.reports.chap5.ch5_design_checks")
    @patch("osdagbridge.core.reports.chap2.ch2_input_parameters")
    def test_all_chapters_produce_latex(
        self, mock_ch2, mock_ch5, mock_ch7
    ):
        mock_ch2.return_value = (
            r"\chapter{Input Parameters}"
            r"\section{Basic Inputs}"
            r"\begin{table}[H]"
            r"\caption{\textbf{Project Location}}"
            r"\begin{tabular}{...}"
            r"\end{tabular}"
            r"\end{table}"
            r"Project location table here."
        )
        mock_ch5.return_value = (
            r"\chapter{Design Checks}"
            r"\section{Plate Girder Design}"
            r"Flexure check table here."
        )
        mock_ch7.return_value = (
            r"\chapter{Material Take-off \& Quantity Summary}"
            r"\section{Bill of Materials}"
            r"BOQ table here."
        )
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="Integration Test Bridge",
                project_location="Mumbai",
                designer="Tester",
                client="Client",
                company="TestCo",
                report_date="2026-01-01",
            ),
            inputs=InputFacts(),
            materials=MaterialFacts(
                structural_steel=StructuralSteelTakeoff(None, None, None, None, None),
                concrete_volume=None,
                reinforcement_steel=None,
                shear_studs=None,
                crash_barrier=None
            ),
            raw_input_dict={"geometry.span": "30"},
            raw_output_dict={},
            design_checks=["girder_flexure"],
        )

        doc = build_report_document(
            facts,
            include_sections=["loads", "design_checks"],
        )

        # Verify document structure
        assert doc.title == "Integration Test Bridge"
        assert doc.author == "TestCo"
        assert doc.date == "2026-01-01"
        assert len(doc.chapters) == 4

        ch_numbers = [ch.number for ch in doc.chapters]
        assert ch_numbers == [2, 3, 5, 7]

        # Verify chapter titles
        assert doc.chapters[0].title == "Input Parameters"
        assert doc.chapters[1].title == "Loads and Load Combinations"
        assert doc.chapters[2].title == "Design Checks"
        assert "Quantity Summary" in doc.chapters[3].title

        # Render to LaTeX
        renderer = LatexRenderer(ReportTheme())
        latex = renderer.render(doc)

        # Verify LaTeX output
        assert r"\chapter{Input Parameters}" in latex
        assert r"\chapter{Loads and Load Combinations}" in latex
        assert r"\chapter{Design Checks}" in latex
        assert r"\chapter{Material Take-off" in latex
        assert "Project Location" in latex
        # Ch3 is migrated: assert actual semantic output
        assert "Dead Load -- Self Weight" in latex
        assert "Vehicle Live Loads" in latex
        assert "Load Combinations" in latex
        assert "Flexure check table here" in latex
        assert "Bill of Materials" in latex

    def test_minimal_pipeline_always_has_ch2_ch7(self):
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="Minimal Bridge",
                project_location="",
                designer="",
                client="",
                company="",
            ),
            raw_input_dict={"geometry.span": "20"},
        )
    
        doc = build_report_document(facts, include_sections=[])
        assert len(doc.chapters) == 2
        assert doc.chapters[0].number == 2
        assert doc.chapters[1].number == 7
    
        renderer = LatexRenderer(ReportTheme())
        latex = renderer.render(doc)
        assert "Project Location" in latex
        assert "Bill of Materials" in latex

    def test_no_raw_input_produces_empty_document(self):
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="Empty",
                project_location="",
                designer="",
                client="",
                company="",
            ),
        )

        doc = build_report_document(facts, include_sections=["loads"])
        assert len(doc.chapters) == 0

        renderer = LatexRenderer(ReportTheme())
        latex = renderer.render(doc)
        assert r"\chapter" not in latex
