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
