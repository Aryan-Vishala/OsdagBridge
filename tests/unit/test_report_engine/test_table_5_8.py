import pytest
from osdagbridge.core.report_engine.chapters.ch5_document import _build_table_5_8

class MockGirder:
    def __init__(self, label):
        self.girder_label = label
        self.intermediate_stiffener = None

def test_empty_table_5_8_returns_none():
    g = MockGirder("G1")
    t = _build_table_5_8((g,))
    assert t is None

def test_populated_table_5_8_returns_table():
    from osdagbridge.core.report_engine.facts import GirderIntermediateStiffenerCheck, QuantityValue, CheckStatus
    g = MockGirder("G1")
    g.intermediate_stiffener = GirderIntermediateStiffenerCheck(
        iys_min=QuantityValue(100.0, "mm⁴"),
        iys_prov=QuantityValue(150.0, "mm⁴"),
        iys_status=CheckStatus.PASS,
        fq=QuantityValue(50.0, "kN"),
        fqd=QuantityValue(75.0, "kN"),
        fqd_status=CheckStatus.PASS,
    )
    t = _build_table_5_8((g,))
    assert t is not None
    assert t.groups is not None
    assert len(t.groups) == 1
