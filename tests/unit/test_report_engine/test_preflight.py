"""Tests for report_engine.preflight — PDFPreflight framework."""

from osdagbridge.core.report_engine.document import ReportDocument
from osdagbridge.core.report_engine.facts import FactMetadata, ReportFacts
from osdagbridge.core.report_engine.preflight import (
    PDFPreflight,
    PreflightCheck,
    PreflightReport,
    PreflightStatus,
)


def _make_facts():
    return ReportFacts(
        metadata=FactMetadata(
            project_name="Test",
            project_location="Mumbai",
            designer="A",
            client="B",
            company="C",
        ),
    )


class TestPreflightStatus:
    def test_values(self):
        assert PreflightStatus.PASS.value == "PASS"
        assert PreflightStatus.WARN.value == "WARN"
        assert PreflightStatus.FAIL.value == "FAIL"


class TestPreflightReport:
    def test_empty_report_is_pass(self):
        report = PreflightReport(checks=[])
        assert report.overall == PreflightStatus.PASS

    def test_all_pass(self):
        report = PreflightReport(checks=[
            PreflightCheck("check1", PreflightStatus.PASS),
            PreflightCheck("check2", PreflightStatus.PASS),
        ])
        assert report.overall == PreflightStatus.PASS

    def test_any_warn_makes_warn(self):
        report = PreflightReport(checks=[
            PreflightCheck("check1", PreflightStatus.PASS),
            PreflightCheck("check2", PreflightStatus.WARN),
        ])
        assert report.overall == PreflightStatus.WARN

    def test_any_fail_makes_fail(self):
        report = PreflightReport(checks=[
            PreflightCheck("check1", PreflightStatus.PASS),
            PreflightCheck("check2", PreflightStatus.FAIL),
        ])
        assert report.overall == PreflightStatus.FAIL

    def test_fail_overrides_warn(self):
        report = PreflightReport(checks=[
            PreflightCheck("check1", PreflightStatus.WARN),
            PreflightCheck("check2", PreflightStatus.FAIL),
        ])
        assert report.overall == PreflightStatus.FAIL

    def test_summary_format(self):
        report = PreflightReport(checks=[
            PreflightCheck("All vehicles", PreflightStatus.PASS),
            PreflightCheck("Footer", PreflightStatus.WARN, "Page 30 close"),
        ])
        summary = report.summary()
        assert "PASS" in summary
        assert "WARN" in summary
        assert "All vehicles" in summary
        assert "Page 30 close" in summary


class TestPDFPreflight:
    def test_run_returns_empty_report(self):
        facts = _make_facts()
        doc = ReportDocument()
        pf = PDFPreflight(facts, doc, "/tmp/test.pdf")
        report = pf.run()
        assert isinstance(report, PreflightReport)
        assert report.overall == PreflightStatus.PASS
        assert report.checks == []
