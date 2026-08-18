"""Tests for report_engine.facts — QuantityValue and all fact dataclasses."""

import pytest

from osdagbridge.core.report_engine.facts import (
    CheckStatus,
    DeadLoadFact,
    DesignCheckData,
    FactMetadata,
    FootwayLoadFact,
    GirderFlexureCheck,
    LiveLoadFact,
    LoadCombinationFact,
    LoadFacts,
    MaterialFacts,
    MaterialQuantityFact,
    QuantityValue,
    ReportFacts,
    SeismicLoadFact,
    StructuralSteelTakeoff,
    SurfacingLoadFact,
    TakeoffItem,
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
            dead_load=DeadLoadFact(
                steel_density=QuantityValue(78.5, "kN/m³"),
                concrete_density=QuantityValue(25.0, "kN/m³"),
                self_weight_factor=QuantityValue(1.0, ""),
            ),
            surfacing_load=SurfacingLoadFact(
                wearing_course_material="Bituminous Concrete",
                wearing_course_thickness=QuantityValue(75, "mm"),
                crash_barrier_load=QuantityValue(5.0, "kN/m"),
                railing_load=QuantityValue(2.0, "kN/m"),
            ),
            live_load=LiveLoadFact(vehicles=()),
            wind_load=WindLoadFact(
                basic_wind_speed=QuantityValue(39.0, "m/s"),
                terrain_type="Plain Terrain",
                avg_exposed_height=QuantityValue(10.0, "m"),
                hourly_mean_wind_speed=QuantityValue(36.5, "m/s"),
                hourly_wind_pressure=QuantityValue(835.0, "N/m²"),
                transverse_wind_force=QuantityValue(100.0, "kN"),
                longitudinal_wind_force=QuantityValue(50.0, "kN"),
                vertical_wind_force=QuantityValue(30.0, "kN"),
            ),
            seismic_load=SeismicLoadFact(
                seismic_zone="Zone IV",
                zone_factor=QuantityValue(0.36, ""),
                importance_factor=QuantityValue(1.5, ""),
                soil_type="Type II – Medium Soil",
                spectral_coeff=QuantityValue(2.5, ""),
                horizontal_coeff=QuantityValue(0.36, ""),
                vertical_coeff=QuantityValue(0.24, ""),
            ),
            temperature_load=TemperatureLoadFact(
                max_shade_temp=QuantityValue(48.0, "°C"),
                min_shade_temp=QuantityValue(10.0, "°C"),
                bridge_temp_min=QuantityValue(14.6, "°C"),
                bridge_temp_max=QuantityValue(43.4, "°C"),
                temp_rise=QuantityValue(14.4, "°C"),
                temp_fall=QuantityValue(14.4, "°C"),
            ),
        )
        facts = ReportFacts(metadata=self._make_metadata(), loads=lf)
        assert facts.loads.dead_load.steel_density.value == 78.5


# ---------------------------------------------------------------------------
# Load facts
# ---------------------------------------------------------------------------

class TestLoadFacts:
    def test_dead_load_fact_frozen(self):
        dl = DeadLoadFact(
            steel_density=QuantityValue(78.5, "kN/m³"),
            concrete_density=QuantityValue(25.0, "kN/m³"),
            self_weight_factor=QuantityValue(1.0, ""),
        )
        with pytest.raises(AttributeError):
            dl.steel_density = QuantityValue(0, "")

    def test_vehicle_live_load_fact_defaults(self):
        v = VehicleLiveLoadFact(vehicle_class="Class 70R")
        assert v.impact_factor is None
        assert v.centrifugal_force is None

    def test_vehicle_live_load_fact_with_values(self):
        v = VehicleLiveLoadFact(
            vehicle_class="Class A",
            impact_factor=QuantityValue(1.207, ""),
        )
        assert v.impact_factor.value == 1.207

    def test_footway_load_fact(self):
        f = FootwayLoadFact(load_type="IRC 6 Cl. 206.1", intensity=QuantityValue(4.905, "kN/m²"))
        assert f.intensity.value == 4.905

    def test_wind_load_fact(self):
        w = WindLoadFact(
            basic_wind_speed=QuantityValue(39.0, "m/s"),
            terrain_type="Plain Terrain",
            avg_exposed_height=QuantityValue(10.0, "m"),
            hourly_mean_wind_speed=QuantityValue(36.5, "m/s"),
            hourly_wind_pressure=QuantityValue(835.0, "N/m²"),
            transverse_wind_force=QuantityValue(100.0, "kN"),
            longitudinal_wind_force=QuantityValue(50.0, "kN"),
            vertical_wind_force=QuantityValue(30.0, "kN"),
        )
        assert w.basic_wind_speed.unit == "m/s"

    def test_seismic_load_fact(self):
        s = SeismicLoadFact(
            seismic_zone="Zone IV",
            zone_factor=QuantityValue(0.36, ""),
            importance_factor=QuantityValue(1.5, ""),
            soil_type="Type II – Medium Soil",
            spectral_coeff=QuantityValue(2.5, ""),
            horizontal_coeff=QuantityValue(0.36, ""),
            vertical_coeff=QuantityValue(0.24, ""),
        )
        assert s.zone_factor.value == 0.36

    def test_temperature_load_fact(self):
        t = TemperatureLoadFact(
            max_shade_temp=QuantityValue(48.0, "°C"),
            min_shade_temp=QuantityValue(10.0, "°C"),
            bridge_temp_min=QuantityValue(14.6, "°C"),
            bridge_temp_max=QuantityValue(43.4, "°C"),
            temp_rise=QuantityValue(14.4, "°C"),
            temp_fall=QuantityValue(14.4, "°C"),
        )
        assert t.max_shade_temp.value == 48.0

    def test_load_combination_fact(self):
        lc = LoadCombinationFact(
            combination_id="ULS-01",
            load_cases=("DL", "LL"),
            factors=(("DL", 1.5, None), ("LL", 1.5, None)),
        )
        assert lc.combination_id == "ULS-01"

    def test_load_facts_is_frozen(self):
        lf = LoadFacts(
            dead_load=DeadLoadFact(
                steel_density=QuantityValue(78.5, "kN/m³"),
                concrete_density=QuantityValue(25.0, "kN/m³"),
                self_weight_factor=QuantityValue(1.0, ""),
            ),
            surfacing_load=SurfacingLoadFact(
                wearing_course_material="",
                wearing_course_thickness=QuantityValue(None, "mm"),
                crash_barrier_load=QuantityValue(None, "kN/m"),
                railing_load=QuantityValue(None, "kN/m"),
            ),
            live_load=LiveLoadFact(vehicles=()),
            wind_load=WindLoadFact(
                basic_wind_speed=QuantityValue(None, "m/s"),
                terrain_type="",
                avg_exposed_height=QuantityValue(None, "m"),
                hourly_mean_wind_speed=QuantityValue(None, "m/s"),
                hourly_wind_pressure=QuantityValue(None, "N/m²"),
                transverse_wind_force=QuantityValue(None, "kN"),
                longitudinal_wind_force=QuantityValue(None, "kN"),
                vertical_wind_force=QuantityValue(None, "kN"),
            ),
            seismic_load=SeismicLoadFact(
                seismic_zone="",
                zone_factor=QuantityValue(None, ""),
                importance_factor=QuantityValue(None, ""),
                soil_type="",
                spectral_coeff=QuantityValue(None, ""),
                horizontal_coeff=QuantityValue(None, ""),
                vertical_coeff=QuantityValue(None, ""),
            ),
            temperature_load=TemperatureLoadFact(
                max_shade_temp=QuantityValue(None, "°C"),
                min_shade_temp=QuantityValue(None, "°C"),
                bridge_temp_min=QuantityValue(None, "°C"),
                bridge_temp_max=QuantityValue(None, "°C"),
                temp_rise=QuantityValue(None, "°C"),
                temp_fall=QuantityValue(None, "°C"),
            ),
        )
        with pytest.raises(AttributeError):
            lf.load_combinations = ()


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
        """concrete_volume=None means unavailable"""
        mf = MaterialFacts(
            structural_steel=StructuralSteelTakeoff(None, None, None, None, None),
            concrete_volume=None,
            reinforcement_steel=None,
            shear_studs=None,
            crash_barrier=None
        )
        assert mf.concrete_volume is None

    def test_structural_steel_none_values(self):
        mf = MaterialFacts(
            structural_steel=StructuralSteelTakeoff(
                TakeoffItem("Girders", None, 1, None, None, None), 
                None, None, None, None
            ),
            concrete_volume=None,
            reinforcement_steel=None,
            shear_studs=None,
            crash_barrier=None
        )
        assert mf.structural_steel.girders is not None
        assert mf.structural_steel.cross_bracing_top is None


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
