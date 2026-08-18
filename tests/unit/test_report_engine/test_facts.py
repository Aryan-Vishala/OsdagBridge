"""Tests for report_engine.facts — QuantityValue and all fact dataclasses."""

import pytest

from osdagbridge.core.report_engine.facts import (
    DeadLoadFact,
    FactMetadata,
    FootwayLoadFact,
    LoadCombinationFact,
    LoadFacts,
    MaterialFacts,
    MaterialQuantityFact,
    QuantityValue,
    ReportFacts,
    SeismicLoadFact,
    TemperatureLoadFact,
    UtilizationFact,
    UtilizationFacts,
    VehicleLiveLoadFact,
    WindLoadFact,
)


# ---------------------------------------------------------------------------
# QuantityValue
# ---------------------------------------------------------------------------

class TestQuantityValue:
    def test_creation_with_value_and_unit(self):
        qv = QuantityValue(12.5, "kN")
        assert qv.value == 12.5
        assert qv.unit == "kN"

    def test_none_value_means_unavailable(self):
        qv = QuantityValue(None, "kN")
        assert qv.value is None
        assert qv.unit == "kN"

    def test_zero_is_genuinely_zero(self):
        qv = QuantityValue(0.0, "m")
        assert qv.value == 0.0

    def test_frozen(self):
        qv = QuantityValue(1.0, "MPa")
        with pytest.raises(AttributeError):
            qv.value = 2.0

    def test_empty_unit(self):
        qv = QuantityValue(3.14, "")
        assert qv.unit == ""


# ---------------------------------------------------------------------------
# FactMetadata and ReportFacts
# ---------------------------------------------------------------------------

class TestReportFacts:
    def _make_metadata(self):
        return FactMetadata(
            project_name="Test Bridge",
            project_location="Mumbai",
            designer="Engineer A",
            client="Client X",
            company="Osdag",
        )

    def test_metadata_creation(self):
        m = self._make_metadata()
        assert m.project_name == "Test Bridge"
        assert m.project_location == "Mumbai"

    def test_report_facts_defaults(self):
        facts = ReportFacts(metadata=self._make_metadata())
        assert facts.loads is None
        assert facts.utilization is None
        assert facts.materials is None
        assert facts.inputs is None

    def test_report_facts_with_loads(self):
        lf = LoadFacts(
            dead_loads=[DeadLoadFact("Self-weight", QuantityValue(25.0, "kN/m³"))],
        )
        facts = ReportFacts(metadata=self._make_metadata(), loads=lf)
        assert len(facts.loads.dead_loads) == 1
        assert facts.loads.dead_loads[0].value.value == 25.0


# ---------------------------------------------------------------------------
# Load facts
# ---------------------------------------------------------------------------

class TestLoadFacts:
    def test_dead_load_fact_frozen(self):
        dl = DeadLoadFact("parameter", QuantityValue(1.0, "unit"))
        with pytest.raises(AttributeError):
            dl.parameter = "changed"

    def test_vehicle_live_load_fact_defaults(self):
        v = VehicleLiveLoadFact(vehicle_class="Class 70R")
        assert v.impact_factor is None
        assert v.braking_load is None
        assert v.centrifugal_force is None

    def test_vehicle_live_load_fact_with_values(self):
        v = VehicleLiveLoadFact(
            vehicle_class="Class A",
            impact_factor=QuantityValue(1.207, ""),
            braking_load=QuantityValue(163.04, "kN"),
        )
        assert v.impact_factor.value == 1.207
        assert v.braking_load.unit == "kN"

    def test_footway_load_fact(self):
        f = FootwayLoadFact(load_type="Distributed", intensity=QuantityValue(4.905, "kN/m²"))
        assert f.intensity.value == 4.905

    def test_wind_load_fact(self):
        w = WindLoadFact("Basic Wind Speed", QuantityValue(39.0, "m/s"))
        assert w.value.unit == "m/s"

    def test_seismic_load_fact(self):
        s = SeismicLoadFact("Zone Factor", QuantityValue(0.36, ""))
        assert s.value.value == 0.36

    def test_temperature_load_fact(self):
        t = TemperatureLoadFact("Max Shade Temp", QuantityValue(48.0, "°C"))
        assert t.value.value == 48.0

    def test_load_combination_fact(self):
        lc = LoadCombinationFact("ULS-01", "DL(1.5) + LL(1.5)")
        assert lc.combination_id == "ULS-01"

    def test_load_facts_defaults_to_empty_lists(self):
        lf = LoadFacts()
        assert lf.dead_loads == []
        assert lf.vehicle_live_loads == []
        assert lf.footway_loads == []
        assert lf.wind_loads == []
        assert lf.seismic_loads == []
        assert lf.temperature_loads == []
        assert lf.load_combinations == []


# ---------------------------------------------------------------------------
# Utilization facts
# ---------------------------------------------------------------------------

class TestUtilizationFacts:
    def test_utilization_fact_defaults(self):
        u = UtilizationFact(component="Girder G1")
        assert u.demand is None
        assert u.capacity is None
        assert u.utilization_ratio is None
        assert u.governing_case == ""
        assert u.status == ""

    def test_utilization_fact_with_values(self):
        u = UtilizationFact(
            component="G1 - Flexure",
            demand=QuantityValue(500.0, "kN"),
            capacity=QuantityValue(610.0, "kN"),
            utilization_ratio=0.82,
            governing_case="LC-ULS-3",
            status="PASS",
        )
        assert u.utilization_ratio == 0.82
        assert u.status == "PASS"

    def test_utilization_facts_threshold(self):
        uf = UtilizationFacts(threshold=1.0)
        assert uf.threshold == 1.0
        assert uf.items == []


# ---------------------------------------------------------------------------
# Material facts
# ---------------------------------------------------------------------------

class TestMaterialFacts:
    def test_material_quantity_fact_frozen(self):
        mq = MaterialQuantityFact(
            item="Steel",
            volume=QuantityValue(1.0, ""),
            quantity=QuantityValue(5, ""),
            total_volume=QuantityValue(5.0, ""),
            weight=QuantityValue(2.0, "MT"),
            total_weight=QuantityValue(10.0, "MT"),
        )
        with pytest.raises(AttributeError):
            mq.item = "Changed"

    def test_material_facts_none_vs_zero(self):
        """concrete_volume_m3=None means unavailable; 0.0 means genuinely zero."""
        mf = MaterialFacts(
            concrete_volume_m3=None,
            reinforcement_mt=0.0,
        )
        assert mf.concrete_volume_m3 is None
        assert mf.reinforcement_mt == 0.0

    def test_structural_steel_none_values(self):
        mf = MaterialFacts(
            structural_steel_mt={
                "Girders": 12.5,
                "Bracing": None,
                "Diaphragms": 0.0,
            }
        )
        assert mf.structural_steel_mt["Girders"] == 12.5
        assert mf.structural_steel_mt["Bracing"] is None
        assert mf.structural_steel_mt["Diaphragms"] == 0.0


# ---------------------------------------------------------------------------
# Input facts
# ---------------------------------------------------------------------------

class TestInputFacts:
    def test_defaults_to_empty_dicts(self):
        from osdagbridge.core.report_engine.facts import InputFacts
        inf = InputFacts()
        assert inf.geometry == {}
        assert inf.material == {}
        assert inf.section == {}
        assert inf.weather == {}
        assert inf.design_options == {}

    def test_with_quantity_values(self):
        from osdagbridge.core.report_engine.facts import InputFacts
        inf = InputFacts(
            geometry={"Span": QuantityValue(30.0, "m")},
        )
        assert inf.geometry["Span"].value == 30.0
        assert inf.geometry["Span"].unit == "m"
