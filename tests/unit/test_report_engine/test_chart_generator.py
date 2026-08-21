import os
import tempfile
import pytest

from osdagbridge.core.report_engine.chart_generators import generate_chart
from osdagbridge.core.report_engine.document import Chart
from osdagbridge.core.report_engine.theme import ReportTheme


def test_chart_generator_all_present():
    chart = Chart(
        title="Overall Utilization Ratio by Component",
        chart_type="bar",
        data={
            "Steel Plate Girders": 0.82,
            "Concrete Deck Slab": 0.71,
            "Cross Bracing": 0.64,
            "End Diaphragms": 0.93,
        },
        y_label="UR",
        threshold_line=1.0,
    )
    theme = ReportTheme()
    path = generate_chart(chart, theme)
    assert os.path.exists(path)
    os.remove(path)


def test_chart_generator_one_missing():
    chart = Chart(
        title="Overall Utilization Ratio by Component",
        chart_type="bar",
        data={
            "Steel Plate Girders": 0.82,
            "Concrete Deck Slab": 0.71,
            "Cross Bracing": None,
            "End Diaphragms": 0.93,
        },
    )
    assert chart.data["Cross Bracing"] is None
    theme = ReportTheme()
    path = generate_chart(chart, theme)
    assert os.path.exists(path)
    os.remove(path)


def test_chart_generator_multiple_missing():
    chart = Chart(
        title="Overall Utilization Ratio by Component",
        chart_type="bar",
        data={
            "Steel Plate Girders": 0.82,
            "Concrete Deck Slab": 0.71,
            "Cross Bracing": None,
            "End Diaphragms": None,
        },
    )
    assert chart.data["End Diaphragms"] is None
    theme = ReportTheme()
    path = generate_chart(chart, theme)
    assert os.path.exists(path)
    os.remove(path)


def test_chart_generator_zero_ur():
    chart = Chart(
        title="Overall Utilization Ratio by Component",
        chart_type="bar",
        data={
            "Steel Plate Girders": 0.0,
            "Concrete Deck Slab": 0.71,
            "Cross Bracing": 0.64,
            "End Diaphragms": 0.93,
        },
    )
    theme = ReportTheme()
    path = generate_chart(chart, theme)
    assert os.path.exists(path)
    os.remove(path)


def test_chart_generator_exactly_one():
    chart = Chart(
        title="Overall Utilization Ratio by Component",
        chart_type="bar",
        data={
            "Steel Plate Girders": 1.0,
            "Concrete Deck Slab": 1.0,
            "Cross Bracing": 1.0,
            "End Diaphragms": 1.0,
        },
        threshold_line=1.0,
    )
    theme = ReportTheme()
    path = generate_chart(chart, theme)
    assert os.path.exists(path)
    os.remove(path)


def test_chart_generator_greater_than_one():
    chart = Chart(
        title="Overall Utilization Ratio by Component",
        chart_type="bar",
        data={
            "Steel Plate Girders": 1.1,
            "Concrete Deck Slab": 1.5,
            "Cross Bracing": 0.64,
            "End Diaphragms": 0.93,
        },
        threshold_line=1.0,
    )
    theme = ReportTheme()
    path = generate_chart(chart, theme)
    assert os.path.exists(path)
    os.remove(path)


def test_chart_renders_as_numbered_figure_caption():
    from osdagbridge.core.report_engine.renderer import LatexRenderer
    theme = ReportTheme()
    renderer = LatexRenderer(theme)
    
    chart = Chart(
        title="Structural Steel Quantities",
        chart_type="bar",
        data={"Girders": 120.0, "Cross Bracing": 15.0, "End Diaphragms": None},
        y_label="Weight (MT)"
    )
    tex = renderer._render_chart(chart)
    assert r"\caption{\textbf{Structural Steel Quantities}}" in tex
    assert r"\caption*" not in tex  # Must be standard numbered figure caption


def test_ch7_all_three_charts_render_with_captions():
    from osdagbridge.core.report_engine.chapters.ch7_document import _build_charts
    from osdagbridge.core.report_engine.facts import MaterialFacts, StructuralSteelTakeoff, TakeoffItem, QuantityValue
    from osdagbridge.core.report_engine.renderer import LatexRenderer
    
    item = TakeoffItem("Item", None, 1, None, None, QuantityValue(100.0, "MT"), None)
    facts = MaterialFacts(
        structural_steel=StructuralSteelTakeoff(item, item, item, item, None),
        concrete_volume=TakeoffItem("Concrete", None, 1, QuantityValue(50.0, "m3"), None, None, None),
        reinforcement_steel=TakeoffItem("Rebar", None, 1, None, None, QuantityValue(12.0, "MT"), None),
        shear_studs=None,
        crash_barrier=None,
    )
    
    charts = _build_charts(facts)
    assert len(charts) == 3
    
    renderer = LatexRenderer(ReportTheme())
    for chart in charts:
        tex = renderer._render_chart(chart)
        assert r"\begin{figure}[H]" in tex
        assert r"\caption{" in tex
        assert chart.title in tex

