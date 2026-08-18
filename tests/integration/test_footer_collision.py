import os
import subprocess
import shutil
import pytest

from osdagbridge.core.report_engine.document import ReportDocument, Chapter, Section, RawLatex, Table, Column, LayoutHints
from osdagbridge.core.report_engine.facts import ReportFacts, FactMetadata
from osdagbridge.core.report_engine.renderer import LatexRenderer
from osdagbridge.core.report_engine.theme import ReportTheme
from osdagbridge.core.report_engine.preflight import PDFPreflight, PreflightStatus

@pytest.mark.skipif(shutil.which("pdflatex") is None, reason="pdflatex not installed")
def test_real_pdf_footer_collision(tmp_path):
    # This integration test generates a real PDF and runs the actual PyMuPDF collision detection.
    
    doc = ReportDocument()
    ch = Chapter(1, "Test Chapter")
    
    # We add enough text to push the table near the bottom of the page
    filler_lines = "This is a filler line to push content down. " * 300
    ch.sections.append(Section("Filler", 2, [RawLatex(filler_lines)]))
    
    # A table that spans pages
    rows = [[f"Item {i}", str(i * 10)] for i in range(50)]
    t = Table(
        caption="Long Table",
        columns=[Column("Name"), Column("Value")],
        rows=rows,
        layout=LayoutHints(minimum_bottom_clearance_lines=0) # Let it naturally collide if geometry is bad
    )
    ch.sections.append(Section("Table Section", 2, [t]))
    doc.chapters.append(ch)
    
    facts = ReportFacts(metadata=FactMetadata("A", "B", "C", "D", "E"))
    
    theme = ReportTheme()
    latex = LatexRenderer(theme).render(doc)
    
    tex_path = tmp_path / "test_footer_reserve.tex"
    pdf_path = tmp_path / "test_footer_reserve.pdf"
    
    tex_path.write_text(latex, encoding="utf-8")
    
    cmd = ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(tmp_path), str(tex_path)]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert result.returncode == 0
    
    pf = PDFPreflight(facts, doc, str(pdf_path))
    report = pf.run()
    
    col_check = next(c for c in report.checks if c.check_name == "Footer Collision")
    assert col_check.status == PreflightStatus.PASS
