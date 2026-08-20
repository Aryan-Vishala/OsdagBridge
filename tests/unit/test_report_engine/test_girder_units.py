import pytest
from osdagbridge.core.report_engine.chapters.ch2_document import _build_girder_section_details_table
from osdagbridge.core.report_engine.facts import ReportFacts, FactMetadata

def test_girder_dimension_units_are_mm():
    facts = ReportFacts(
        metadata=FactMetadata(project_name="Test", project_location="", designer="", client="", company=""),
        inputs=None,
        raw_input_dict={},
        raw_output_dict={
            "steeldesign.girders.[0].id": "G1",
            "steeldesign.girders.[0].section.web_depth": 1.67,
            "steeldesign.girders.[0].section.web_thickness": 0.01,
            "steeldesign.girders.[0].section.top_flange_width": 0.51,
            "steeldesign.girders.[0].section.top_flange_thickness": 0.022,
            "steeldesign.girders.[0].section.bot_flange_width": 0.51,
            "steeldesign.girders.[0].section.bot_flange_thickness": 0.022,
        }
    )
    table = _build_girder_section_details_table(facts)
    assert len(table.rows) == 1
    row = table.rows[0]
    
    assert "G1" in row[0]
    assert "1670 mm" in row[1]
    assert "10 mm" in row[2]
    assert "510 mm, 22 mm" in row[3]
    assert "510 mm, 22 mm" in row[4]
