import pytest
from osdagbridge.core.report_engine.facts.material_takeoff import build_material_facts
from osdagbridge.core.report_engine.facts import QuantityValue

def test_build_material_facts_empty():
    facts = build_material_facts({}, {})
    assert facts.structural_steel.girders is None
    assert facts.structural_steel.cross_bracing_top is None
    assert facts.structural_steel.cross_bracing_bot is None
    assert facts.structural_steel.cross_bracing_diag is None
    assert facts.structural_steel.end_diaphragms is None
    assert facts.concrete_volume is None
    assert facts.reinforcement_steel is None
    assert facts.shear_studs is None
    assert facts.crash_barrier is None

def test_build_material_facts_girders():
    inputs = {
        "geometry.span": "30",
        "typical_section.no_of_girders": "4",
        "member_properties.girder_details.section_properties.area": "0.12",
        "member_properties.girder_details.section_properties.mass": "900.0"
    }
    facts = build_material_facts(inputs, {})
    girders = facts.structural_steel.girders
    assert girders is not None
    assert girders.item_description == "Structural Steel (IS 2062) for Girders"
    assert girders.quantity == 4
    
    # 0.12 * 30 = 3.6
    assert girders.unit_volume.value == pytest.approx(3.6)
    assert girders.total_volume.value == pytest.approx(14.4)
    
    # 900.0 * 30 = 27000 kg per girder = 27.0 MT per girder
    # Total for 4 girders = 108.0 MT
    assert girders.unit_weight.value == pytest.approx(27.0)
    assert girders.total_weight.value == pytest.approx(108.0)
