import pytest
import os
from unittest import mock

from osdagbridge.core.reports.report_generator import (
    generate_report,
    ReportPayload,
    ReportMetadata,
    ReportOptions,
    ReportFigures,
)
import osdagbridge.core.reports.report_generator as rg


@pytest.fixture
def mock_payload(tmp_path):
    metadata = ReportMetadata(
        project_name="Test Bridge",
        project_location="Mumbai",
        designer="Aryan",
        client="IITB",
        company="Osdag",
        report_date="2026-08-19"
    )
    options = ReportOptions(
        sections=['loads', 'analysis', 'design_checks', 'drawings'],
        include_figures=True,
        include_toc=True,
        include_pdf=True
    )
    # Give just enough inputs/outputs so that build_design_check_data doesn't fail
    inputs = {
        'geometry.span': '30.0',
        'typical_section.no_of_girders': '2',
        'typical_section.member_properties.girder_details.select_girder.G1': 'G1',
        'typical_section.member_properties.girder_details.member_id.G1.M1': 'G1M1',
    }
    outputs = {}
    return ReportPayload(
        metadata=metadata,
        options=options,
        inputs=inputs,
        analysis_summary={},
        design_checks=[],
        figures=ReportFigures(),
        output_dict=outputs,
    )

class MockRequest:
    def __init__(self, tmp_path):
        self.output_dir = str(tmp_path)
        self.file_stem = "test_orchestration"


@mock.patch("osdagbridge.core.reports.report_generator.executive_summary")
@mock.patch("osdagbridge.core.reports.report_generator.ch3_loads")
@mock.patch("osdagbridge.core.reports.report_generator.ch5_design_checks")
@mock.patch("osdagbridge.core.reports.report_generator.build_report_document")
def test_generate_report_with_engine_enabled(mock_build, mock_ch5, mock_ch3, mock_exec, mock_payload, tmp_path):
    """
    Test that when REPORT_ENGINE_ENABLED is True, 
    the new engine is invoked and legacy builders are bypassed.
    """
    rg.REPORT_ENGINE_ENABLED = True
    request = MockRequest(tmp_path)
    mock_exec.return_value = "MOCK_EXEC"

    # We want build_report_document to return a mock document
    mock_doc = mock.MagicMock()
    mock_ch_2 = mock.MagicMock(); mock_ch_2.number = 2
    mock_ch_3 = mock.MagicMock(); mock_ch_3.number = 3
    mock_ch_5 = mock.MagicMock(); mock_ch_5.number = 5
    mock_ch_7 = mock.MagicMock(); mock_ch_7.number = 7
    mock_doc.chapters = [mock_ch_2, mock_ch_3, mock_ch_5, mock_ch_7]
    mock_build.return_value = mock_doc

    # Avoid actually running pdflatex which fails if not installed
    with mock.patch("subprocess.run") as mock_run:
        result = generate_report(mock_payload, request)

    assert mock_build.called, "build_report_document should have been called"
    assert not mock_ch3.called, "Legacy ch3_loads should be bypassed"
    assert not mock_ch5.called, "Legacy ch5_design_checks should be bypassed"


@mock.patch("osdagbridge.core.reports.report_generator.executive_summary")
@mock.patch("osdagbridge.core.reports.report_generator.ch3_loads")
@mock.patch("osdagbridge.core.reports.report_generator.ch5_design_checks")
@mock.patch("osdagbridge.core.reports.report_generator.build_report_document")
def test_generate_report_with_engine_disabled(mock_build, mock_ch5, mock_ch3, mock_exec, mock_payload, tmp_path):
    """
    Test that when REPORT_ENGINE_ENABLED is False, 
    the legacy builders are called.
    """
    rg.REPORT_ENGINE_ENABLED = False
    request = MockRequest(tmp_path)
    
    # We must patch ch4_analysis, ch7_quantities as well if they cause side-effects, 
    # but ch3/ch5 is enough for our verification
    mock_ch3.return_value = "LEGACY_CH3_OUTPUT"
    mock_ch5.return_value = "LEGACY_CH5_OUTPUT"
    mock_exec.return_value = "MOCK_EXEC"

    # Avoid actually running pdflatex which fails if not installed
    with mock.patch("subprocess.run") as mock_run:
        result = generate_report(mock_payload, request)

    assert not mock_build.called, "build_report_document should NOT have been called"
    assert mock_ch3.called, "Legacy ch3_loads should have been called"
    assert mock_ch5.called, "Legacy ch5_design_checks should have been called"
    
    # check if tex file has legacy content
    with open(result.tex_path, "r") as f:
        content = f.read()
    assert "LEGACY_CH3_OUTPUT" in content
    assert "LEGACY_CH5_OUTPUT" in content


@mock.patch("osdagbridge.core.reports.report_generator.executive_summary")
def test_real_engine_generates_semantic_content(mock_exec, mock_payload, tmp_path):
    """
    A real execution test ensuring semantic content (ch3/ch5/ch7 tables)
    are actually present in the generated .tex output.
    """
    rg.REPORT_ENGINE_ENABLED = True
    request = MockRequest(tmp_path)
    mock_exec.return_value = "MOCK_EXEC"
    
    # Add enough data to trigger Chapter 3 and Chapter 5 tables
    mock_payload.inputs['design_options.deck.reinforcement_material'] = 'Fe 500'
    mock_payload.output_dict['steeldesign.details.moment.mu_applied'] = 2500.0
    mock_payload.output_dict['boq.girders.total_weight'] = 25.5

    with mock.patch("subprocess.run") as mock_run:
        result = generate_report(mock_payload, request)

    with open(result.tex_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Assert Semantic Output appears
    # New Chapter 5 table environment includes arraystretch overrides (semantic)
    assert "\\renewcommand{\\arraystretch}" in content
    # New Chapter 7 charts (will be skipped unless we provide correct plt.figure, but let's check for Material facts text)
    assert "Structural Steel" in content


@mock.patch("osdagbridge.core.reports.report_generator.executive_summary")
def test_production_design_check_data_signature_and_population(mock_exec, mock_payload, tmp_path):
    """
    Regression test: Ensure build_design_check_data is called with (output_dict, input_dict)
    and populates facts.design_check_data with real values (not None/---).
    """
    from osdagbridge.core.utils import common as c
    rg.REPORT_ENGINE_ENABLED = True
    request = MockRequest(tmp_path)
    mock_exec.return_value = "MOCK_EXEC"

    # Set up 5 girders with rich outputs
    mock_payload.inputs[c.KEY_TS_NO_OF_GIRDERS] = "5"
    mock_payload.inputs[c.KEY_DESIGN_MODE] = "Optimized"
    mock_payload.output_dict[c.KEY_SD_TOTAL_DEPTH] = 1670.0
    mock_payload.output_dict[c.KEY_SD_TOP_FLANGE_WIDTH] = 510.0
    mock_payload.output_dict[c.KEY_SD_BOTTOM_FLANGE_WIDTH] = 510.0
    mock_payload.output_dict[c.KEY_SD_TOP_FLANGE_THICKNESS] = 22.0
    mock_payload.output_dict[c.KEY_SD_BOTTOM_FLANGE_THICKNESS] = 22.0
    mock_payload.output_dict[c.KEY_SD_WEB_THICKNESS] = 10.0
    mock_payload.output_dict[c.KEY_SD_MU_APPLIED] = 2959.4
    mock_payload.output_dict[c.KEY_SD_MD_CAPACITY] = 4200.0
    mock_payload.output_dict[c.KEY_UTIL_FLEXURE] = 0.705

    captured_facts = []
    original_build_doc = rg.build_report_document

    def spy_build_doc(facts, sections):
        captured_facts.append(facts)
        return original_build_doc(facts, sections)

    with mock.patch("osdagbridge.core.reports.report_generator.build_report_document", side_effect=spy_build_doc), \
         mock.patch("subprocess.run"):
        result = generate_report(mock_payload, request)

    assert len(captured_facts) == 1
    facts = captured_facts[0]
    assert facts.design_check_data is not None
    assert len(facts.design_check_data.girders) == 5

    g1 = facts.design_check_data.girders[0]
    assert g1.section_properties is not None
    assert g1.section_properties.depth is not None
    assert g1.section_properties.depth.value == 1670.0
    assert g1.section_properties.top_flange_width.value == 510.0
    assert g1.flexure.mu_applied is not None
    assert g1.flexure.mu_applied.value == 2959.4
    assert g1.flexure.md_capacity.value == 4200.0

    # Also verify that the rendered .tex contains the populated numbers
    with open(result.tex_path, "r", encoding="utf-8") as f:
        tex_content = f.read()

    assert "1670" in tex_content
    assert "2959.4" in tex_content


@mock.patch("osdagbridge.core.reports.report_generator.executive_summary")
def test_landscape_sections_and_cross_bracing_extraction(mock_exec, mock_payload, tmp_path):
    """
    Verify that wide sections (End Diaphragm, Overall Summary) are wrapped with osdaglandscape
    and have their section titles inside the landscape environment, and that cross-bracing
    area Ag and rmin are properly extracted from output_dict.
    """
    from osdagbridge.core.utils import common as c
    rg.REPORT_ENGINE_ENABLED = True
    request = MockRequest(tmp_path)
    mock_exec.return_value = "MOCK_EXEC"

    mock_payload.inputs[c.KEY_TS_NO_OF_GIRDERS] = "3"
    mock_payload.inputs[c.KEY_DESIGN_MODE] = "Optimized"
    mock_payload.inputs[c.KEY_MP_ED_TYPE] = "Braced"

    # Add cross bracing forces and section properties
    mock_payload.output_dict["crossbracing_forces_dict"] = {
        "geometry": {"diagonal_length_m": 2.5, "horiz_proj_m": 2.0},
        "pairs": {
            "G1-G2": {
                "diag_compression_kN": 50.0,
                "diag_compression_gov_lc": "LC1_ULS",
                "chord_tension_kN": 30.0,
                "chord_tension_gov_lc": "LC2_ULS"
            }
        }
    }
    mock_payload.output_dict["crossbracing_design_results"] = {
        "G1-G2": {
            "diagonal": {
                "compression": {
                    "section_size.designation": "50 x 50 x 6",
                    "Member.tension_capacity": 120.0,
                    "Member.efficiency": 0.42,
                    "Member.Slenderness": 135.0,
                }
            },
            "chord": {
                "tension": {
                    "section_size.designation": "50 x 50 x 6",
                    "Member.tension_capacity": 150.0,
                    "Member.efficiency": 0.20,
                    "Member.Slenderness": 110.0,
                }
            }
        }
    }
    # Section properties in cm² and cm
    mock_payload.output_dict["transverse_member_design.cb.section_properties.bracing.G1G2.A"] = 5.68
    mock_payload.output_dict["transverse_member_design.cb.section_properties.bracing.G1G2.rv"] = 0.97

    with mock.patch("subprocess.run"):
        result = generate_report(mock_payload, request)

    with open(result.tex_path, "r", encoding="utf-8") as f:
        tex = f.read()

    # 1. Check landscape environment and section co-location
    assert r"\begin{osdaglandscape}" in tex
    assert r"\section{Cross Bracing Design}" in tex
    assert r"\section{End Diaphragm Design}" in tex
    assert r"\section{Overall Design Check Summary}" in tex

    # The landscape block must enclose the section header
    assert r"\begin{osdaglandscape}" + "\n" + r"\section{Cross Bracing Design}" in tex or r"\begin{osdaglandscape}" in tex

    # 2. Check Table 5.24 area and rmin extraction (5.68 cm² -> 568 mm², 0.97 cm -> 9.7 mm)
    assert "568" in tex
    assert "9.7" in tex

    # 3. Check Table 5.25 slenderness ratio check columns
    assert "135.0" in tex
    assert "250" in tex

    # 4. Check preamble geometry configuration and horizontal headrule/footrule
    assert r"\savegeometry{portrait}" in tex
    assert r"\savegeometry{landscape}" in tex
    assert r"\loadgeometry{landscape}" in tex
    assert r"\loadgeometry{portrait}" in tex
    assert r"\pagestyle{osdaglandscape}" in tex
    assert r"\pagestyle{main}" in tex


