import pytest
from unittest.mock import patch
from osdagbridge.core.report_engine.chapters.ch2_document import build_chapter_2
from osdagbridge.core.report_engine.facts import ReportFacts, FactMetadata, InputFacts
from osdagbridge.core.report_engine.document import Chapter

def test_production_ch2_does_not_append_legacy_builder():
    facts = ReportFacts(
        metadata=FactMetadata(project_name="Test", project_location="", designer="", client="", company=""),
        inputs=InputFacts(),
        raw_input_dict={},
        raw_output_dict={}
    )
    
    with patch("osdagbridge.core.reports.chap2.ch2_input_parameters") as mock_legacy:
        ch = build_chapter_2(facts)
        assert isinstance(ch, Chapter)
        assert len(ch.sections) == 3
        mock_legacy.assert_not_called()
