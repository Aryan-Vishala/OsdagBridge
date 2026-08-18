"""Tests for report_engine.document — document tree construction."""

from osdagbridge.core.report_engine.document import (
    Callout,
    Chart,
    Chapter,
    Column,
    Figure,
    RawLatex,
    ReportDocument,
    Section,
    Table,
)
from osdagbridge.core.report_engine.layout import LayoutHints


class TestReportDocument:
    def test_defaults(self):
        doc = ReportDocument()
        assert doc.title == "OsdagBridge Design Report"
        assert doc.author == ""
        assert doc.chapters == []

    def test_with_chapters(self):
        ch = Chapter(number=1, title="Introduction")
        doc = ReportDocument(chapters=[ch])
        assert len(doc.chapters) == 1
        assert doc.chapters[0].title == "Introduction"


class TestChapter:
    def test_creation(self):
        ch = Chapter(number=3, title="Loads")
        assert ch.number == 3
        assert ch.title == "Loads"
        assert ch.sections == []

    def test_with_sections(self):
        sec = Section(title="Dead Loads", level=2)
        ch = Chapter(number=3, title="Loads", sections=[sec])
        assert len(ch.sections) == 1


class TestSection:
    def test_creation(self):
        sec = Section(title="Sub heading", level=3)
        assert sec.level == 3
        assert sec.components == []

    def test_with_components(self):
        tbl = Table(
            caption="Test",
            columns=[Column("A"), Column("B")],
            rows=[["1", "2"]],
        )
        sec = Section(title="Data", components=[tbl])
        assert len(sec.components) == 1
        assert isinstance(sec.components[0], Table)


class TestTable:
    def test_creation(self):
        t = Table(
            caption="Caption",
            columns=[Column("H1"), Column("H2")],
            rows=[["a", "b"]],
        )
        assert t.caption == "Caption"
        assert t.label == ""
        assert len(t.columns) == 2
        assert t.rows == [["a", "b"]]

    def test_default_layout(self):
        t = Table(caption="C", columns=[], rows=[])
        assert isinstance(t.layout, LayoutHints)
        assert t.layout.repeat_header is True


class TestChart:
    def test_creation(self):
        c = Chart(
            title="UR Summary",
            chart_type="bar",
            data={"A": 0.8, "B": 0.6},
        )
        assert c.threshold_line is None
        assert c.x_label == ""


class TestFigure:
    def test_with_path(self):
        f = Figure(path="/tmp/img.png", caption="Figure 1")
        assert f.path == "/tmp/img.png"

    def test_without_path(self):
        f = Figure(path=None, caption="Missing")
        assert f.path is None


class TestCallout:
    def test_defaults(self):
        co = Callout(text="Important note")
        assert co.callout_type == "note"


class TestRawLatex:
    def test_passthrough(self):
        raw = RawLatex(r"\chapter{Legacy}")
        assert raw.content == r"\chapter{Legacy}"
