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
    def test_run_returns_populated_report(self):
        facts = _make_facts()
        doc = ReportDocument()
        pf = PDFPreflight(facts, doc, "/tmp/test.pdf")
        report = pf.run()
        assert isinstance(report, PreflightReport)
        
        # It should have a document structure fail because we passed an empty doc
        struct_check = next(c for c in report.checks if c.check_name == "Document Structure")
        assert struct_check.status == PreflightStatus.FAIL

    def test_check_end_diaphragm_unavailable(self):
        facts = _make_facts()
        from osdagbridge.core.report_engine.facts.material_takeoff import build_material_facts
        mat_facts = build_material_facts({}, {})
        setattr(facts, "material_facts", mat_facts)
        
        doc = ReportDocument()
        pf = PDFPreflight(facts, doc, "/tmp/test.pdf")
        report = pf.run()
        diaph_check = next(c for c in report.checks if c.check_name == "End Diaphragm Data")
        assert diaph_check.status == PreflightStatus.WARN

    def test_mock_footer_collision(self, monkeypatch):
        import fitz
        class MockBlock:
            def __init__(self, x0, y0, x1, y1, text, btype):
                self.bbox = (x0, y0, x1, y1, text, btype, 0)
                
        class MockRect:
            width = 595.28
            height = 841.89

        class MockPage:
            def __init__(self, blocks):
                self.blocks = [b.bbox for b in blocks]
                self.rect = MockRect()
            def get_text(self, mode):
                return self.blocks
                
        class MockDoc:
            def __init__(self, pages):
                self.pages = pages
            def __len__(self):
                return len(self.pages)
            def __getitem__(self, idx):
                return self.pages[idx]
            def close(self):
                pass
                
        # page_height = 297 * 2.83465 = 841.89 pt
        # margin_bottom = 25 * 2.83465 = 70.86 pt
        # max_allowed_body_y = 841.89 - 70.86 = 771.02 pt
        
        # Safe body: y1 = 700 (well above 771.02), x1 = 400 (well within width 595.28)
        safe_page = MockPage([MockBlock(50, 600, 400, 700, "Safe text", 0)])
        
        # Footer text: y0 = 800 (starts in footer), is just a number
        footer_page = MockPage([MockBlock(100, 800, 120, 810, " 30 ", 0)])
        
        # Collision: y1 = 780 (crosses into footer)
        collision_page = MockPage([MockBlock(50, 750, 400, 780, "Too long table row", 0)])
        
        # Horizontal overflow: x1 = 580 (crosses right margin 595.28 - 42.5 = 552.78)
        overflow_page = MockPage([MockBlock(50, 200, 580, 250, "Extremely wide table cell extending beyond right margin", 0)])
        
        def mock_open(path):
            if "safe.pdf" in path:
                return MockDoc([safe_page])
            elif "footer.pdf" in path:
                return MockDoc([safe_page, footer_page])
            elif "overflow.pdf" in path:
                return MockDoc([safe_page, overflow_page])
            else:
                return MockDoc([safe_page, collision_page])
                
        monkeypatch.setattr(fitz, "open", mock_open)
        monkeypatch.setattr("os.path.exists", lambda p: True)
        
        facts = _make_facts()
        doc = ReportDocument()
        
        # Test safe
        pf_safe = PDFPreflight(facts, doc, "safe.pdf")
        assert next(c for c in pf_safe.run().checks if c.check_name == "Footer Collision").status == PreflightStatus.PASS
        assert next(c for c in pf_safe.run().checks if c.check_name == "Horizontal Margin Overflow").status == PreflightStatus.PASS
        
        # Test footer ignored
        pf_footer = PDFPreflight(facts, doc, "footer.pdf")
        assert next(c for c in pf_footer.run().checks if c.check_name == "Footer Collision").status == PreflightStatus.PASS
        
        # Test collision
        pf_collision = PDFPreflight(facts, doc, "collision.pdf")
        assert next(c for c in pf_collision.run().checks if c.check_name == "Footer Collision").status == PreflightStatus.FAIL

        # Test horizontal overflow
        pf_overflow = PDFPreflight(facts, doc, "overflow.pdf")
        assert next(c for c in pf_overflow.run().checks if c.check_name == "Horizontal Margin Overflow").status == PreflightStatus.FAIL
