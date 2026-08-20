"""Tests for report_engine.renderer — LatexRenderer formatting and rendering."""

from osdagbridge.core.report_engine.document import (
    Callout,
    Chapter,
    Column,
    Figure,
    RawLatex,
    ReportDocument,
    Section,
    Table,
    TableGroup,
)
from osdagbridge.core.report_engine.facts import CheckStatus, QuantityValue
from osdagbridge.core.report_engine.layout import LayoutHints
from osdagbridge.core.report_engine.renderer import LatexRenderer
from osdagbridge.core.report_engine.theme import ReportTheme


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

class TestFmtQuantity:
    def setup_method(self):
        self.renderer = LatexRenderer(ReportTheme())

    def test_normal_value(self):
        qv = QuantityValue(12.5, "kN")
        assert self.renderer.fmt_quantity(qv) == "12.5 kN"

    def test_none_quantity(self):
        assert self.renderer.fmt_quantity(None) == "N/A"

    def test_none_value(self):
        qv = QuantityValue(None, "kN")
        assert self.renderer.fmt_quantity(qv) == "N/A"

    def test_zero_is_valid(self):
        qv = QuantityValue(0.0, "m")
        assert self.renderer.fmt_quantity(qv) == "0.0 m"

    def test_zero_no_unit(self):
        qv = QuantityValue(0.0, "")
        assert self.renderer.fmt_quantity(qv) == "0.0"

    def test_custom_fallback(self):
        assert self.renderer.fmt_quantity(None, fallback="--") == "--"

    def test_negative_value(self):
        qv = QuantityValue(-3.5, "°C")
        assert self.renderer.fmt_quantity(qv) == "-3.5 °C"


class TestFmtFloat:
    def setup_method(self):
        self.renderer = LatexRenderer(ReportTheme())

    def test_normal(self):
        assert self.renderer.fmt_float(0.82) == "0.82"

    def test_none(self):
        assert self.renderer.fmt_float(None) == "N/A"

    def test_zero(self):
        assert self.renderer.fmt_float(0.0) == "0.0"

    def test_custom_fallback(self):
        assert self.renderer.fmt_float(None, fallback="missing") == "missing"


# ---------------------------------------------------------------------------
# Document rendering
# ---------------------------------------------------------------------------

class TestRenderDocument:
    def setup_method(self):
        self.renderer = LatexRenderer(ReportTheme())

    def test_empty_document(self):
        doc = ReportDocument(title="Empty")
        tex = self.renderer.render(doc)
        assert r"\documentclass" in tex
        assert r"\end{document}" in tex

    def test_document_with_chapter(self):
        ch = Chapter(
            number=1,
            title="Introduction",
            sections=[
                Section(
                    title="Background",
                    level=2,
                    components=[RawLatex(r"Some legacy content.")],
                ),
            ],
        )
        doc = ReportDocument(chapters=[ch])
        tex = self.renderer.render(doc)
        assert r"\chapter{Introduction}" in tex
        assert r"\section{Background}" in tex
        assert r"Some legacy content." in tex


class TestRenderTable:
    def setup_method(self):
        self.renderer = LatexRenderer(ReportTheme())

    def test_basic_table(self):
        t = Table(
            caption="Test Table",
            columns=[Column("A"), Column("B")],
            rows=[["1", "2"]],
        )
        tex = self.renderer._render_table(t)
        assert r"\begin{longtable}" in tex
        assert r"\caption{\textbf{Test Table}}" in tex
        assert r"\endfirsthead" in tex
        assert r"\endhead" in tex
        assert r"\textbf{A}" in tex
        assert r"\textbf{B}" in tex
        assert "1 & 2 \\\\" in tex

    def test_needspace_from_layout_hint(self):
        t = Table(
            caption="Big Table",
            columns=[Column("H")],
            rows=[["row"]],
            layout=LayoutHints(minimum_bottom_clearance_lines=5),
        )
        tex = self.renderer._render_table(t)
        assert r"\Needspace{5\baselineskip}" in tex

    def test_keep_together_ignored_for_table(self):
        t = Table(
            caption="Together",
            columns=[Column("H")],
            rows=[["row"]],
            layout=LayoutHints(keep_together=True),
        )
        tex = self.renderer._render_table(t)
        assert r"\begin{minipage}" not in tex  # Tables should not use minipage anymore

    def test_no_needspace_when_zero(self):
        t = Table(
            caption="Small",
            columns=[Column("H")],
            rows=[["row"]],
            layout=LayoutHints(minimum_bottom_clearance_lines=0, keep_caption_with_table=False),
        )
        tex = self.renderer._render_table(t)
        assert r"\Needspace" not in tex

    def test_special_chars_escaped_in_body(self):
        """LaTeX special characters in cell values are escaped by the renderer."""
        t = Table(
            caption="Test",
            columns=[Column("X")],
            rows=[["A & B"]],
        )
        tex = self.renderer._render_table(t)
        assert r"A \& B" in tex

    def test_unicode_escaping(self):
        """Mathematical and typographical Unicode symbols are mapped to LaTeX commands."""
        t = Table(
            caption="Test",
            columns=[Column("X")],
            rows=[["≤ ≥ × ± ° – — − → · ² ³ ⁴ Ø α γ ε λ ρ σ τ χ"]],
        )
        tex = self.renderer._render_table(t)
        assert r"$\leq$ $\geq$ $\times$ $\pm$ $^\circ$ -- --- - $\rightarrow$ $\cdot$ $^2$ $^3$ $^4$ $\emptyset$ $\alpha$ $\gamma$ $\epsilon$ $\lambda$ $\rho$ $\sigma$ $\tau$ $\chi$" in tex

    def test_math_component_and_mixed_content(self):
        """Mixed semantic content (Math, CheckStatus, Text) are rendered securely."""
        from osdagbridge.core.report_engine.document import Math
        t = Table(
            caption="Mixed Content",
            columns=[Column("X"), Column("Y")],
            rows=[
                [["Top Flange Width, ", Math("b_f"), " (mm)"], "150"],
                [["UR=", "0.95", CheckStatus.PASS], "OK"],
            ],
        )
        tex = self.renderer._render_table(t)
        # Math should be rendered with $ but NOT escaped (e.g. _ not converted to \_)
        assert r"Top Flange Width, $b_f$ (mm)" in tex
        assert r"UR=0.95PASS" in tex


    def test_col_spec_from_column_widths(self):
        t = Table(
            caption="Test",
            columns=[
                Column("Name", width="L{5cm}"),
                Column("Value"),
            ],
            rows=[],
        )
        tex = self.renderer._render_table(t)
        assert r"|L{5cm}|" in tex
        assert "l" in tex


class TestRenderTableGroup:
    def setup_method(self):
        self.renderer = LatexRenderer(ReportTheme())

    def test_single_row_group(self):
        """Single-row group: label displayed directly (no multirow needed)."""
        t = Table(
            caption="Test",
            columns=[Column(""), Column("Param"), Column("Value")],
            groups=[
                TableGroup(label="G1", rows=[["Depth", "1500"]]),
            ],
        )
        tex = self.renderer._render_table(t)
        assert "G1" in tex
        assert "Depth" in tex
        assert "1500" in tex

    def test_multirow_for_multi_row_group(self):
        """Multi-row group: \\multirow spans all rows in the group when non-splittable."""
        t = Table(
            caption="Test",
            columns=[Column(""), Column("Param"), Column("Value")],
            layout=LayoutHints(splittable=False),
            groups=[
                TableGroup(label="G1", rows=[
                    ["Depth", "1500"],
                    ["Width", "400"],
                    ["Thickness", "25"],
                ]),
            ],
        )
        tex = self.renderer._render_table(t)
        assert r"\multirow{3}" in tex
        
    def test_no_multirow_for_splittable_group(self):
        """Multi-row group: no \\multirow when splittable."""
        t = Table(
            caption="Test",
            columns=[Column(""), Column("Param"), Column("Value")],
            layout=LayoutHints(splittable=True),
            groups=[
                TableGroup(label="G1", rows=[
                    ["Depth", "1500"],
                    ["Width", "400"],
                    ["Thickness", "25"],
                ]),
            ],
        )
        tex = self.renderer._render_table(t)
        assert r"\multirow{3}" not in tex
        assert r"G1 & Depth" in tex
        assert "G1" in tex
        assert "Depth" in tex
        assert "Width" in tex
        assert "Thickness" in tex

    def test_multiple_girder_groups(self):
        """Multiple groups: each gets its own \\multirow block."""
        t = Table(
            caption="Test",
            columns=[Column(""), Column("Param"), Column("Value")],
            layout=LayoutHints(splittable=False),
            groups=[
                TableGroup(label="G1", rows=[["Depth", "1500"], ["Width", "400"]]),
                TableGroup(label="G2", rows=[["Depth", "1600"], ["Width", "420"]]),
            ],
        )
        tex = self.renderer._render_table(t)
        assert r"\multirow{2}" in tex
        assert tex.count(r"\multirow{2}") == 2
        assert "G1" in tex
        assert "G2" in tex
        assert "1500" in tex
        assert "1600" in tex

    def test_cline_between_rows(self):
        """No inner \\cline within a group (cleaner visual grouping)."""
        t = Table(
            caption="Test",
            columns=[Column(""), Column("Param"), Column("Value")],
            groups=[
                TableGroup(label="G1", rows=[["A", "1"], ["B", "2"]]),
            ],
        )
        tex = self.renderer._render_table(t)
        assert r"\cline{2-3}" not in tex

    def test_hline_between_groups(self):
        """\\hline separates groups."""
        t = Table(
            caption="Test",
            columns=[Column(""), Column("Param"), Column("Value")],
            groups=[
                TableGroup(label="G1", rows=[["A", "1"]]),
                TableGroup(label="G2", rows=[["B", "2"]]),
            ],
        )
        tex = self.renderer._render_table(t)
        assert tex.count(r"\hline") >= 3  # header + between groups + footer

    def test_repeated_header_after_page_break(self):
        """Grouped tables include \\endhead for page-break headers."""
        t = Table(
            caption="Test",
            columns=[Column(""), Column("Param"), Column("Value")],
            groups=[
                TableGroup(label="G1", rows=[["A", "1"]]),
            ],
        )
        tex = self.renderer._render_table(t)
        assert r"\endfirsthead" in tex
        assert r"\endhead" in tex

    def test_no_groups_falls_back_to_flat_rows(self):
        """Table with groups=None uses flat rows."""
        t = Table(
            caption="Flat",
            columns=[Column("A"), Column("B")],
            rows=[["1", "2"]],
        )
        tex = self.renderer._render_table(t)
        assert r"\multirow" not in tex
        assert "1 & 2" in tex

    def test_empty_groups(self):
        """Empty groups list produces no body rows."""
        t = Table(
            caption="Empty",
            columns=[Column(""), Column("X")],
            groups=[],
        )
        tex = self.renderer._render_table(t)
        assert r"\begin{longtable}" in tex
        assert r"\end{longtable}" in tex

    def test_special_chars_escaped_in_groups(self):
        """LaTeX special characters in group rows are escaped."""
        t = Table(
            caption="Test",
            columns=[Column(""), Column("X")],
            groups=[
                TableGroup(label="G1", rows=[["A & B", "C%D"]]),
            ],
        )
        tex = self.renderer._render_table(t)
        assert r"A \& B" in tex
        assert r"C\%D" in tex



class TestRenderFigure:
    def setup_method(self):
        self.renderer = LatexRenderer(ReportTheme())

    def test_with_path(self):
        f = Figure(path="/tmp/test.png", caption="Test Figure")
        tex = self.renderer._render_figure(f)
        assert r"\includegraphics" in tex
        assert "/tmp/test.png" in tex

    def test_without_path_shows_placeholder(self):
        f = Figure(path=None, caption="Missing Figure")
        tex = self.renderer._render_figure(f)
        assert "PLACEHOLDER" in tex
        assert "Missing Figure" in tex


class TestRenderCallout:
    def setup_method(self):
        self.renderer = LatexRenderer(ReportTheme())

    def test_note(self):
        co = Callout(text="Important", callout_type="note")
        tex = self.renderer._render_callout(co)
        assert r"\begin{remark}" in tex
        assert "Important" in tex

    def test_warning(self):
        co = Callout(text="Caution", callout_type="warning")
        tex = self.renderer._render_callout(co)
        assert r"\begin{warning}" in tex


class TestRenderRawLatex:
    def setup_method(self):
        self.renderer = LatexRenderer(ReportTheme())

    def test_passthrough(self):
        raw = RawLatex(r"\chapter{Legacy}")
        tex = self.renderer._render_component(raw)
        assert tex == r"\chapter{Legacy}"


class TestLandscapeSectionFlow:
    def setup_method(self):
        self.renderer = LatexRenderer(ReportTheme())

    def test_landscape_section_structure(self):
        cols = [Column("Check", "L{6cm}"), Column("Status", "C{3cm}")]
        sec = Section(
            title="Overall Summary",
            level=2,
            layout=LayoutHints(orientation="landscape"),
            components=[
                Table(
                    caption="Summary Table",
                    columns=cols,
                    rows=[["Moment", "PASS"], ["Shear", "PASS"]],
                )
            ],
        )
        tex = self.renderer._render_section(sec)
        assert r"\begin{osdaglandscape}" in tex
        assert r"\section{Overall Summary}" in tex
        assert r"\begin{longtable}" in tex
        assert r"\end{longtable}" in tex
        assert r"\end{osdaglandscape}" in tex
        assert r"\begin{minipage}" not in tex
        assert r"\begin{samepage}" not in tex

    def test_landscape_multipage_longtable_repeat_header(self):
        cols = [Column("Item", "L{8cm}"), Column("Value", "C{4cm}")]
        sec = Section(
            title="Large Design Table",
            level=2,
            layout=LayoutHints(orientation="landscape"),
            components=[
                Table(
                    caption="Extended Checks",
                    columns=cols,
                    rows=[[f"Check {i}", "PASS"] for i in range(35)],
                    layout=LayoutHints(splittable=True, repeat_header=True),
                )
            ],
        )
        tex = self.renderer._render_section(sec)
        assert r"\begin{osdaglandscape}" in tex
        assert r"\caption{\textbf{Extended Checks}}" in tex
        assert r"\textit{Extended Checks (continued)}" in tex
        assert r"\end{osdaglandscape}" in tex


# Need pytest for the error test
import pytest
