import pytest
from pathlib import Path
from typing import Dict, Any

from osdagbridge.core.reports.report_generator import (
    generate_report,
    ReportPayload,
    ReportMetadata,
    ReportOptions,
    ReportFigures,
)
import osdagbridge.core.reports.report_generator as rg
from unittest import mock

@pytest.fixture(autouse=True)
def mock_subprocess(monkeypatch):
    """Mock the pdflatex call to avoid needing latex installed for tests."""
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        yield mock_run

class DummyRequest:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.file_stem = "osdag_report"

import sys
from unittest.mock import MagicMock
sys.modules['openseespy'] = MagicMock()
sys.modules['openseespy.opensees'] = MagicMock()

def _create_payload(tmp_path, data: Dict[str, Any]) -> ReportPayload:
    metadata = ReportMetadata(
        project_name="Test Bridge",
        project_location="Test",
        designer="Test",
        client="Test",
        company="Test",
        report_date="Test"
    )
    options = ReportOptions(
        sections=['loads', 'analysis', 'design_checks', 'drawings'],
        include_figures=True,
        include_toc=True,
        include_pdf=True
    )
    figures = ReportFigures()
    return ReportPayload(
        metadata=metadata,
        options=options,
        inputs=data,
        analysis_summary={},
        design_checks=[],
        output_dict=data,
        figures=figures,
    )

def test_payload_a_5_girders_full_deck(tmp_path, monkeypatch):
    """Payload A: 5 girders, Cross bracing, Deck present"""
    data = {
        "typical_section.no_of_girders": "5",
        "steeldesign.girders.[0].id": "G1",
        "steeldesign.girders.[1].id": "G2",
        "steeldesign.girders.[2].id": "G3",
        "steeldesign.girders.[3].id": "G4",
        "steeldesign.girders.[4].id": "G5",
        "steeldesign.girders.[0].section.web_depth": 1.5,
        "steeldesign.girders.[1].section.web_depth": 1.5,
        "steeldesign.girders.[2].section.web_depth": 1.5,
        "steeldesign.girders.[3].section.web_depth": 1.5,
        "steeldesign.girders.[4].section.web_depth": 1.5,
        "deck.has_deck": True,
        "cross_bracing.present": True,
        "design.status": "PASS",
        "cross_bracing.ur": 0.85,
        "deck.ur": 0.90
    }
    
    payload = _create_payload(tmp_path, data)
    
    # Force the new engine
    monkeypatch.setattr(rg, "REPORT_ENGINE_ENABLED", True)
    
    out_pdf = generate_report(payload, DummyRequest(str(tmp_path)))
    
    tex_file = tmp_path / "osdag_report.tex"
    assert tex_file.exists()
    latex = tex_file.read_text(encoding="utf-8")
    
    assert r"\endhead" in latex
    assert r"\multicolumn" in latex
    assert r"\hline" in latex

def test_payload_b_3_girders(tmp_path, monkeypatch):
    """Payload B: 3 girders, different span, different vehicles"""
    data = {
        "typical_section.no_of_girders": "3",
        "steeldesign.girders.[0].id": "G1",
        "steeldesign.girders.[1].id": "G2",
        "steeldesign.girders.[2].id": "G3",
        "geometry.span": 25.0,
        "loading.vehicle": "Class AA Tracked",
        "deck.has_deck": True,
        "cross_bracing.present": False,
        "design.status": "FAIL",
    }
    payload = _create_payload(tmp_path, data)
    monkeypatch.setattr(rg, "REPORT_ENGINE_ENABLED", True)
    
    generate_report(payload, DummyRequest(str(tmp_path)))
    tex_file = tmp_path / "osdag_report.tex"
    latex = tex_file.read_text(encoding="utf-8")
    assert r"\endhead" in latex

def test_payload_c_missing_deck_and_diaphragms(tmp_path, monkeypatch):
    """Payload C: deck unavailable, end diaphragm unavailable"""
    data = {
        "typical_section.no_of_girders": "2",
        "steeldesign.girders.[0].id": "G1",
        "steeldesign.girders.[1].id": "G2",
        "deck.has_deck": False,
        "end_diaphragm.present": False,
        "design.status": "PASS",
    }
    payload = _create_payload(tmp_path, data)
    monkeypatch.setattr(rg, "REPORT_ENGINE_ENABLED", True)
    
    generate_report(payload, DummyRequest(str(tmp_path)))
    tex_file = tmp_path / "osdag_report.tex"
    latex = tex_file.read_text(encoding="utf-8")
    # Make sure we didn't crash
    assert r"\begin{document}" in latex

def test_payload_d_different_groups(tmp_path, monkeypatch):
    """Payload D: different number of girders / groups"""
    data = {
        "typical_section.no_of_girders": "7",
        "steeldesign.girders.[0].id": "G1",
        "steeldesign.girders.[1].id": "G2",
        "steeldesign.girders.[2].id": "G3",
        "steeldesign.girders.[3].id": "G4",
        "steeldesign.girders.[4].id": "G5",
        "steeldesign.girders.[5].id": "G6",
        "steeldesign.girders.[6].id": "G7",
        "deck.has_deck": True,
    }
    payload = _create_payload(tmp_path, data)
    monkeypatch.setattr(rg, "REPORT_ENGINE_ENABLED", True)
    
    generate_report(payload, DummyRequest(str(tmp_path)))
    tex_file = tmp_path / "osdag_report.tex"
    latex = tex_file.read_text(encoding="utf-8")
    assert r"\endhead" in latex
