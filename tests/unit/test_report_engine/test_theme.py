"""Tests for report_engine.theme — ReportTheme and sub-dataclasses."""

import pytest

from osdagbridge.core.report_engine.theme import (
    ChartStyle,
    ColorPalette,
    PageGeometry,
    ReportTheme,
    TableStyle,
    TypographyStyle,
)


class TestPageGeometry:
    def test_defaults(self):
        pg = PageGeometry()
        assert pg.width_mm == 210
        assert pg.height_mm == 297
        assert pg.margin_bottom_mm == 25

    def test_frozen(self):
        pg = PageGeometry()
        with pytest.raises(AttributeError):
            pg.margin_bottom_mm = 30


class TestTableStyle:
    def test_defaults(self):
        ts = TableStyle()
        assert ts.column_padding_pt == 6
        assert ts.row_height_factor == 1.15
        assert ts.inner_group_rule == "subtle"
        assert ts.group_boundary_rule == "strong"

    def test_frozen(self):
        ts = TableStyle()
        with pytest.raises(AttributeError):
            ts.column_padding_pt = 10


class TestChartStyle:
    def test_defaults(self):
        cs = ChartStyle()
        assert cs.dpi == 300
        assert cs.width_cm == 12


class TestColorPalette:
    def test_defaults(self):
        cp = ColorPalette()
        assert cp.primary == "#91B014"
        assert cp.secondary == "#1E293B"
        assert cp.accent == "#0284C7"
        assert cp.steel == "#2563EB"
        assert cp.concrete == "#0D9488"
        assert cp.rebar == "#D97706"


class TestReportTheme:
    def test_defaults(self):
        theme = ReportTheme()
        assert isinstance(theme.page, PageGeometry)
        assert "default" in theme.table_styles
        assert isinstance(theme.charts["default"], ChartStyle)
        assert isinstance(theme.typography, TypographyStyle)
        assert isinstance(theme.colors, ColorPalette)

    def test_frozen(self):
        theme = ReportTheme()
        with pytest.raises(AttributeError):
            theme.page = PageGeometry(margin_bottom_mm=30)

    def test_table_style_lookup(self):
        theme = ReportTheme()
        assert theme.table_styles["default"].column_padding_pt == 6
        assert theme.table_styles["compact"].column_padding_pt == 4
        assert theme.table_styles["load"].column_padding_pt == 5

    def test_custom_theme(self):
        theme = ReportTheme(
            page=PageGeometry(margin_bottom_mm=30),
            table_styles={
                "default": TableStyle(column_padding_pt=8),
            },
        )
        assert theme.page.margin_bottom_mm == 30
        assert theme.table_styles["default"].column_padding_pt == 8
