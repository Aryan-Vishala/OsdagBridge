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
)
from osdagbridge.core.report_engine.facts import QuantityValue
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
        assert r"\caption{Test Table}" in tex
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

    def test_keep_together(self):
        t = Table(
            caption="Together",
            columns=[Column("H")],
            rows=[["row"]],
            layout=LayoutHints(keep_together=True),
        )
        tex = self.renderer._render_table(t)
        assert r"\begin{minipage}[t]{\textwidth}" in tex
        assert r"\end{minipage}" in tex

    def test_no_needspace_when_zero(self):
        t = Table(
            caption="Small",
            columns=[Column("H")],
            rows=[["row"]],
            layout=LayoutHints(minimum_bottom_clearance_lines=0),
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

    def test_col_spec_from_column_widths(self):
        t = Table(
            caption="Test",
            columns=[
                Column("Name", width="5cm"),
                Column("Value"),
            ],
            rows=[],
        )
        tex = self.renderer._render_table(t)
        assert r"|L{5cm}|" in tex
        assert "l" in tex


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


class TestUnknownComponent:
    def setup_method(self):
        self.renderer = LatexRenderer(ReportTheme())

    def test_raises_type_error(self):
        with pytest.raises(TypeError):
            self.renderer._render_component("not a component")


# Need pytest for the error test
import pytest
