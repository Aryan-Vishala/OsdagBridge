import pytest
from osdagbridge.core.report_engine.document import Table, TableGroup, Column, LayoutHints
from osdagbridge.core.report_engine.renderer import LatexRenderer
from osdagbridge.core.report_engine.theme import ReportTheme

def test_split_table_repeats_header():
    t = Table(caption="Test", columns=[Column("A"), Column("B")], rows=[["1", "2"]])
    r = LatexRenderer(ReportTheme())
    latex = r._render_component(t)
    assert r"\endhead" in latex
    assert r"\multicolumn{2}{c}{\textit{Test (continued)}} \\" in latex

def test_split_group_has_no_multirow():
    t = Table(caption="Test", columns=[Column("A"), Column("B")], groups=[TableGroup(label="G1", rows=[["X", "Y"], ["Z", "W"]])])
    r = LatexRenderer(ReportTheme())
    latex = r._render_component(t)
    assert r"\multirow" not in latex
    assert "G1 & X & Y" in latex
    assert " & Z & W" in latex

def test_final_bottom_border_only_at_table_end():
    t = Table(caption="Test", columns=[Column("A"), Column("B")], rows=[["1", "2"]])
    r = LatexRenderer(ReportTheme())
    latex = r._render_component(t)
    assert r"\hline" in latex
    assert r"\endlastfoot" in latex
    assert r"\endfoot" in latex
