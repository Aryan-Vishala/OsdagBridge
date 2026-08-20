"""Test: first real migration — Project Location table.

Verifies that the structured Table component in the new ch2_document builder
produces the same rendered values as the old legacy ch2_input_parameters()
function for the Project Location table.
"""

from osdagbridge.core.report_engine.facts import FactMetadata, ReportFacts
from osdagbridge.core.report_engine.facts.inputs import build_input_facts
from osdagbridge.core.report_engine.chapters.ch2_document import (
    _build_bridge_geometry_table,
    _build_components_details_table,
    _build_material_selection_table,
    _build_project_location_table,
    _build_safety_factors_table,
    _build_shear_connector_table,
    _build_typical_section_table,
)
from osdagbridge.core.report_engine.document import ReportDocument
from osdagbridge.core.report_engine.renderer import LatexRenderer
from osdagbridge.core.report_engine.theme import ReportTheme


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

FACTS = ReportFacts(
    metadata=FactMetadata(
        project_name="Test Bridge",
        project_location="Mumbai, India",
        designer="Tester",
        client="Client",
        company="Co",
    ),
    raw_input_dict={
        "latitude": "19.0760",
        "longitude": "72.8777",
        "seismic_zone": "III",
        "wind_speed": "39",
        "shade_temp_max": "45",
        "shade_temp_min": "10",
    },
)


# ---------------------------------------------------------------------------
# Structured table content tests
# ---------------------------------------------------------------------------

class TestProjectLocationTable:
    """Verify the semantic Table captures all 5 rows correctly."""

    def test_table_has_correct_caption(self):
        table = _build_project_location_table(FACTS)
        assert "Project Location" in table.caption

    def test_table_has_correct_label(self):
        table = _build_project_location_table(FACTS)
        assert table.label == "subsec:project-location"

    def test_table_has_two_columns(self):
        table = _build_project_location_table(FACTS)
        assert len(table.columns) == 2
        assert table.columns[0].header == "Parameter"
        assert table.columns[1].header == "Value"

    def test_row_project_location(self):
        table = _build_project_location_table(FACTS)
        assert table.rows[0] == ["Project Location", "Mumbai, India"]

    def test_row_latitude_longitude(self):
        table = _build_project_location_table(FACTS)
        assert table.rows[1] == ["Latitude / Longitude", "19.0760, 72.8777"]

    def test_row_seismic_zone(self):
        table = _build_project_location_table(FACTS)
        assert table.rows[2] == ["Seismic Zone (IRC 6)", "III"]

    def test_row_wind_speed_with_unit(self):
        table = _build_project_location_table(FACTS)
        assert table.rows[3] == ["Basic Wind Speed (IRC 6)", "39 m/s"]

    def test_row_shade_temps(self):
        table = _build_project_location_table(FACTS)
        assert table.rows[4] == ["Shade Temp. Max / Min (IRC 6)", "45 °C / 10 °C"]

    def test_row_count(self):
        table = _build_project_location_table(FACTS)
        assert len(table.rows) == 5

    def test_no_latex_in_row_data(self):
        """Row data is plain text — no LaTeX commands."""
        table = _build_project_location_table(FACTS)
        for row in table.rows:
            for cell in row:
                assert "\\" not in cell
                assert "&" not in cell


# ---------------------------------------------------------------------------
# Rendered output comparison
# ---------------------------------------------------------------------------

class TestRenderedProjectLocation:
    """Verify the structured table renders correctly in context."""

    def _build_and_render(self, facts):
        from osdagbridge.core.report_engine.chapters.ch2_document import build_chapter_2
        ch = build_chapter_2(facts)
        doc = ReportDocument(title="Test", chapters=[ch])
        renderer = LatexRenderer(ReportTheme())
        return renderer.render(doc)

    def test_project_location_value_in_output(self):
        latex = self._build_and_render(FACTS)
        assert "Mumbai, India" in latex

    def test_row_label_in_output(self):
        latex = self._build_and_render(FACTS)
        # Renderer escapes cell values — "Project Location" appears in the table body
        assert "Project Location & Mumbai, India" in latex

    def test_latitude_longitude_values(self):
        latex = self._build_and_render(FACTS)
        assert "19.0760" in latex
        assert "72.8777" in latex

    def test_wind_speed_with_unit(self):
        latex = self._build_and_render(FACTS)
        assert "39 m/s" in latex

    def test_shade_temps(self):
        latex = self._build_and_render(FACTS)
        assert "45" in latex
        assert "10" in latex

    def test_bridge_geometry_table_rendered(self):
        """The Bridge Geometry table is now a semantic Table component."""
        latex = self._build_and_render(FACTS)
        assert r"\caption{\textbf{Bridge Geometry}}" in latex
        assert "Type of Structure" in latex

    def test_material_selection_table_rendered(self):
        """The Material Selection table is now a semantic Table component."""
        latex = self._build_and_render(FACTS)
        assert r"\caption{\textbf{Material Selection}}" in latex
        assert "Girder Steel Grade (IS 2062)" in latex

    def test_typical_section_table_rendered(self):
        """The Typical Section Details table is now a semantic Table component."""
        latex = self._build_and_render(FACTS)
        assert r"\caption{\textbf{Typical Section Details}}" in latex

    def test_components_details_table_rendered(self):
        """The Components Details table is now a semantic Table component."""
        latex = self._build_and_render(FACTS)
        assert r"\caption{\textbf{Components Details}}" in latex

    def test_shear_connector_table_rendered(self):
        """The Shear Connector Details table is now a semantic Table component."""
        latex = self._build_and_render(FACTS)
        assert r"\caption{\textbf{Shear Connector Details}}" in latex

    def test_safety_factors_table_rendered(self):
        """The Partial Safety Factors table is now a semantic Table component."""
        latex = self._build_and_render(FACTS)
        assert r"\caption{\textbf{Partial Safety Factors}}" in latex

    def test_section_heading_present(self):
        latex = self._build_and_render(FACTS)
        assert r"\section{Basic Inputs (User-Defined)}" in latex

    def test_no_duplicate_chapter_heading(self):
        latex = self._build_and_render(FACTS)
        count = latex.count(r"\chapter{Input Parameters}")
        assert count == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestProjectLocationEdgeCases:
    def test_missing_values_render_as_empty(self):
        """When input_dict keys are absent, rows show empty (not crashes)."""
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="",
                project_location="",
                designer="",
                client="",
                company="",
            ),
            raw_input_dict={},
        )
        table = _build_project_location_table(facts)
        assert table.rows[0] == ["Project Location", ""]
        assert table.rows[1] == ["Latitude / Longitude", ""]

    def test_special_characters_in_data(self):
        """Row data can contain special characters — the renderer escapes them."""
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="",
                project_location="Mumbai & Pune",
                designer="",
                client="",
                company="",
            ),
            raw_input_dict={"seismic_zone": "III & IV"},
        )
        table = _build_project_location_table(facts)
        # Raw data has & — renderer will escape it
        assert "&" in table.rows[0][1]
        assert "&" in table.rows[2][1]

    def test_float_values(self):
        """Numeric values (like lat/lon floats from production payload) are safely converted to string."""
        facts = ReportFacts(
            metadata=FactMetadata(project_name="", project_location="", designer="", client="", company=""),
            raw_input_dict={
                "latitude": 28.9845,
                "longitude": 77.7064,
                "wind_speed": 39.5,
                "shade_temp_max": 45,
                "shade_temp_min": 10.0,
            },
        )
        table = _build_project_location_table(facts)
        assert table.rows[1] == ["Latitude / Longitude", "28.9845, 77.7064"]
        assert table.rows[3] == ["Basic Wind Speed (IRC 6)", "39.5 m/s"]
        assert table.rows[4] == ["Shade Temp. Max / Min (IRC 6)", "45 °C / 10.0 °C"]


# ---------------------------------------------------------------------------
# Bridge Geometry table tests
# ---------------------------------------------------------------------------

BG_FACTS = ReportFacts(
    metadata=FactMetadata(
        project_name="Test Bridge",
        project_location="Mumbai, India",
        designer="Tester",
        client="Client",
        company="Co",
    ),
    raw_input_dict={
        "structure.type": "Composite",
        "geometry.span": "30",
        "geometry.carriageway_width": "7.5",
        "geometry.include_median": "No",
        "geometry.footpath": "Yes",
        "geometry.skew_angle": "10",
    },
)
BG_FACTS.inputs = build_input_facts(BG_FACTS.raw_input_dict)


class TestBridgeGeometryTable:
    """Verify the semantic Bridge Geometry table captures all 6 rows."""

    def test_caption(self):
        t = _build_bridge_geometry_table(BG_FACTS)
        assert t.caption == "Bridge Geometry"

    def test_label(self):
        t = _build_bridge_geometry_table(BG_FACTS)
        assert t.label == "subsec:bridge-geometry"

    def test_two_columns(self):
        t = _build_bridge_geometry_table(BG_FACTS)
        assert len(t.columns) == 2
        assert t.columns[0].header == "Parameter"
        assert t.columns[1].header == "Value"

    def test_row_count(self):
        t = _build_bridge_geometry_table(BG_FACTS)
        assert len(t.rows) == 6

    def test_row_structure_type(self):
        t = _build_bridge_geometry_table(BG_FACTS)
        assert t.rows[0] == ["Type of Structure", "Composite"]

    def test_row_span(self):
        t = _build_bridge_geometry_table(BG_FACTS)
        assert t.rows[1] == ["Span (m)", "30 m"]

    def test_row_carriageway_width(self):
        t = _build_bridge_geometry_table(BG_FACTS)
        assert t.rows[2] == ["Carriageway Width (m)", "7.5 m"]

    def test_row_include_median(self):
        t = _build_bridge_geometry_table(BG_FACTS)
        assert t.rows[3] == ["Include Median", "No"]

    def test_row_footpath(self):
        t = _build_bridge_geometry_table(BG_FACTS)
        assert t.rows[4] == ["Footpath", "Yes"]

    def test_row_skew_angle_with_note(self):
        t = _build_bridge_geometry_table(BG_FACTS)
        assert t.rows[5][0] == "Skew Angle (degrees)"
        assert "10" in t.rows[5][1][0]
        assert "IRC 24" in t.rows[5][1][1]

    def test_no_latex_in_row_data(self):
        """Row data is plain text — no LaTeX commands."""
        t = _build_bridge_geometry_table(BG_FACTS)
        for row in t.rows:
            for cell in row:
                assert "\\" not in cell


class TestBridgeGeometryEdgeCases:
    def test_missing_values_render_as_empty(self):
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="",
                project_location="",
                designer="",
                client="",
                company="",
            ),
            raw_input_dict={},
        )
        t = _build_bridge_geometry_table(facts)
        assert t.rows[0] == ["Type of Structure", ""]
        assert t.rows[1] == ["Span (m)", ""]


# ---------------------------------------------------------------------------
# Material Selection table tests
# ---------------------------------------------------------------------------

MS_FACTS = ReportFacts(
    metadata=FactMetadata(
        project_name="Test Bridge",
        project_location="Mumbai, India",
        designer="Tester",
        client="Client",
        company="Co",
    ),
    raw_input_dict={
        "material.girder": "E250 (Fe 410 W A)",
        "material.cross_bracing": "E250 (Fe 410 W A)",
        "material.end_diaphragm": "E250 (Fe 410 W A)",
        "material.deck": "M30",
    },
)


class TestMaterialSelectionTable:
    """Verify the semantic Material Selection table captures all 4 rows."""

    def test_caption(self):
        t = _build_material_selection_table(MS_FACTS)
        assert t.caption == "Material Selection"

    def test_label(self):
        t = _build_material_selection_table(MS_FACTS)
        assert t.label == "subsec:material"

    def test_row_count(self):
        t = _build_material_selection_table(MS_FACTS)
        assert len(t.rows) == 4

    def test_row_girder(self):
        t = _build_material_selection_table(MS_FACTS)
        assert t.rows[0] == ["Girder Steel Grade (IS 2062)", "E250 (Fe 410 W A)"]

    def test_row_cross_bracing(self):
        t = _build_material_selection_table(MS_FACTS)
        assert t.rows[1] == ["Cross Bracing Steel Grade", "E250 (Fe 410 W A)"]

    def test_row_end_diaphragm(self):
        t = _build_material_selection_table(MS_FACTS)
        assert t.rows[2] == ["End Diaphragm Steel Grade", "E250 (Fe 410 W A)"]

    def test_row_concrete_deck(self):
        t = _build_material_selection_table(MS_FACTS)
        assert t.rows[3] == ["Concrete Deck Grade (IRC 22)", "M30"]

    def test_no_latex_in_row_data(self):
        t = _build_material_selection_table(MS_FACTS)
        for row in t.rows:
            for cell in row:
                assert "\\" not in cell


class TestMaterialSelectionEdgeCases:
    def test_missing_values_render_as_empty(self):
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="",
                project_location="",
                designer="",
                client="",
                company="",
            ),
            raw_input_dict={},
        )
        t = _build_material_selection_table(facts)
        assert t.rows[0] == ["Girder Steel Grade (IS 2062)", ""]


# ---------------------------------------------------------------------------
# Typical Section Details table tests
# ---------------------------------------------------------------------------

TS_FACTS = ReportFacts(
    metadata=FactMetadata(
        project_name="Test Bridge",
        project_location="Mumbai, India",
        designer="Tester",
        client="Client",
        company="Co",
    ),
    raw_input_dict={
        "typical_section.overall_bridge_width": "12.5",
        "typical_section.no_of_girders": "4",
        "typical_section.girder_spacing": "3.5",
        "typical_section.deck_overhang": "1.25",
        "typical_section.deck_thickness": "200",
        "typical_section.footpath_width": "1.5",
        "typical_section.lane_details.lane_table_count": "2",
    },
)
TS_FACTS.inputs = build_input_facts(TS_FACTS.raw_input_dict)


class TestTypicalSectionTable:
    """Verify the semantic Typical Section Details table captures all 7 rows."""

    def test_caption(self):
        t = _build_typical_section_table(TS_FACTS)
        assert t.caption == "Typical Section Details"

    def test_row_count(self):
        t = _build_typical_section_table(TS_FACTS)
        assert len(t.rows) == 7

    def test_row_overall_width(self):
        t = _build_typical_section_table(TS_FACTS)
        assert t.rows[0] == ["Overall Bridge Width (m)", "12.5 m"]

    def test_row_no_of_girders(self):
        t = _build_typical_section_table(TS_FACTS)
        assert t.rows[1] == ["No. of Girders", "4"]

    def test_row_girder_spacing(self):
        t = _build_typical_section_table(TS_FACTS)
        assert t.rows[2] == ["Girder Spacing (m)", "3.5 m"]

    def test_row_deck_overhang(self):
        t = _build_typical_section_table(TS_FACTS)
        assert t.rows[3] == ["Deck Overhang Width (m)", "1.25 m"]

    def test_row_deck_thickness(self):
        t = _build_typical_section_table(TS_FACTS)
        assert t.rows[4] == ["Deck Thickness (mm)", "200 mm"]

    def test_row_footpath_with_code_note(self):
        t = _build_typical_section_table(TS_FACTS)
        assert t.rows[5][0] == "Footpath Width (m)"
        assert "1.5 m" in t.rows[5][1]
        assert "IRC 5 Cl. 104.3.6" in t.rows[5][1]

    def test_row_traffic_lanes_with_code_note(self):
        t = _build_typical_section_table(TS_FACTS)
        assert t.rows[6][0] == "No. of Traffic Lanes"
        assert "2" in t.rows[6][1]
        assert "IRC 5 Cl. 104.3.1" in t.rows[6][1]

    def test_no_latex_in_row_data(self):
        t = _build_typical_section_table(TS_FACTS)
        for row in t.rows:
            for cell in row:
                assert "\\" not in cell


class TestTypicalSectionEdgeCases:
    def test_missing_values_render_as_empty(self):
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="",
                project_location="",
                designer="",
                client="",
                company="",
            ),
            raw_input_dict={},
        )
        t = _build_typical_section_table(facts)
        assert t.rows[0] == ["Overall Bridge Width (m)", ""]
        # No footpath_width → no code note
        assert t.rows[5][1] == ""


# ---------------------------------------------------------------------------
# Components Details table tests
# ---------------------------------------------------------------------------

CD_FACTS = ReportFacts(
    metadata=FactMetadata(
        project_name="Test Bridge",
        project_location="Mumbai, India",
        designer="Tester",
        client="Client",
        company="Co",
    ),
    raw_input_dict={
        "typical_section.crash_barrier.type": "New Jersey",
        "typical_section.crash_barrier.load": "5.0",
        "typical_section.median.type": "Equalining",
        "typical_section.railing.type": "RCC Railing",
        "typical_section.railing.load_value": "2.0",
        "typical_section.wearing_course.material": "Bituminous Concrete",
        "typical_section.wearing_course.thickness": "75",
    },
)


class TestComponentsDetailsTable:
    """Verify the semantic Components Details table captures rows correctly."""

    def test_caption(self):
        t = _build_components_details_table(CD_FACTS)
        assert t.caption == "Components Details"

    def test_row_count_with_median(self):
        """When median type is present, 7 rows total."""
        t = _build_components_details_table(CD_FACTS)
        assert len(t.rows) == 7

    def test_row_crash_barrier_type(self):
        t = _build_components_details_table(CD_FACTS)
        assert t.rows[0] == ["Crash Barrier Type", "New Jersey"]

    def test_row_crash_barrier_load(self):
        t = _build_components_details_table(CD_FACTS)
        assert t.rows[1] == ["Crash Barrier Load (kN/m)", "5.0"]

    def test_row_median_type(self):
        t = _build_components_details_table(CD_FACTS)
        assert t.rows[2] == ["Median Type", "Equalining"]

    def test_row_railing_type(self):
        t = _build_components_details_table(CD_FACTS)
        assert t.rows[3] == ["Railing Type", "RCC Railing"]

    def test_row_railing_load(self):
        t = _build_components_details_table(CD_FACTS)
        assert t.rows[4] == ["Railing Load (kN/m)", "2.0"]

    def test_row_wearing_course_material(self):
        t = _build_components_details_table(CD_FACTS)
        assert t.rows[5] == ["Wearing Course Material", "Bituminous Concrete"]

    def test_row_wearing_course_thickness(self):
        t = _build_components_details_table(CD_FACTS)
        assert t.rows[6] == ["Wearing Course Thickness (mm)", "75 mm"]

    def test_no_median_row_when_absent(self):
        """When median type is not set, 6 rows total (no Median row)."""
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="", project_location="", designer="",
                client="", company="",
            ),
            raw_input_dict={
                "typical_section.crash_barrier.type": "NJ",
                "typical_section.crash_barrier.load": "5.0",
                "typical_section.railing.type": "RCC",
                "typical_section.railing.load_value": "2.0",
                "typical_section.wearing_course.material": "BC",
                "typical_section.wearing_course.thickness": "75",
            },
        )
        t = _build_components_details_table(facts)
        assert len(t.rows) == 6
        # Median row should NOT be present
        assert t.rows[2][0] != "Median Type"

    def test_no_latex_in_row_data(self):
        t = _build_components_details_table(CD_FACTS)
        for row in t.rows:
            for cell in row:
                assert "\\" not in cell


class TestComponentsDetailsEdgeCases:
    def test_missing_values_render_as_empty(self):
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="", project_location="", designer="",
                client="", company="",
            ),
            raw_input_dict={},
        )
        t = _build_components_details_table(facts)
        # No median → 6 rows
        assert len(t.rows) == 6
        assert t.rows[0] == ["Crash Barrier Type", ""]

    def test_unit_conversion(self):
        from osdagbridge.core.report_engine.chapters.ch2_document import _build_girder_section_details_table
        from osdagbridge.core.report_engine.facts import ReportFacts, FactMetadata
    
        # Simulated input dict with raw values in metres.
        input_dict = {
            'typical_section.no_of_girders': '1',
            'member_properties.girder_details.select_girder.G1': 'G1',
            'member_properties.girder_details.member_id.G1.M1': 'G1M1',
        }
    
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="", project_location="", designer="",
                client="", company="",
            ),
            raw_input_dict=input_dict
        )
    
        # My table builder uses raw_output_dict for girder dimensions!
        facts.raw_output_dict = {
            'steeldesign.girders.[0].id': 'G1',
            'steeldesign.girders.[0].section.web_depth': 1670.0,
            'steeldesign.girders.[0].section.web_thickness': 10.0,
            'steeldesign.girders.[0].section.top_flange_width': 510.0,
            'steeldesign.girders.[0].section.top_flange_thickness': 22.0,
            'steeldesign.girders.[0].section.bot_flange_width': 510.0,
            'steeldesign.girders.[0].section.bot_flange_thickness': 22.0,
        }
    
        t = _build_girder_section_details_table(facts)
    
        assert len(t.rows) == 1
        r = t.rows[0]
        assert r[0] == 'G1'
        assert r[1] == '1670 mm'
        assert r[2] == '10 mm'
        assert r[3] == '510 mm, 22 mm'
        assert r[4] == '510 mm, 22 mm'


# ---------------------------------------------------------------------------
# Shear Connector Details table tests
# ---------------------------------------------------------------------------

SC_FACTS = ReportFacts(
    metadata=FactMetadata(
        project_name="Test Bridge",
        project_location="Mumbai, India",
        designer="Tester",
        client="Client",
        company="Co",
    ),
    raw_output_dict={
        "steeldesign.details.shear.diameter": "22",
        "steeldesign.details.shear.height": "100",
        "steeldesign.details.shear.yield_strength": "250",
        "steeldesign.details.shear.ultimate_strength": "410",
        "steeldesign.details.shear.studs_per_section": "3",
    },
)
FACTS.inputs = build_input_facts(FACTS.raw_input_dict)
SC_FACTS.inputs = build_input_facts(SC_FACTS.raw_input_dict or {})


class TestShearConnectorTable:
    """Verify the semantic Shear Connector Details table."""

    def test_caption(self):
        t = _build_shear_connector_table(SC_FACTS)
        assert t.caption == "Shear Connector Details"

    def test_row_count(self):
        t = _build_shear_connector_table(SC_FACTS)
        assert len(t.rows) == 5

    def test_row_diameter(self):
        t = _build_shear_connector_table(SC_FACTS)
        assert t.rows[0] == ["Stud Diameter (mm)", "22 mm"]

    def test_row_height(self):
        t = _build_shear_connector_table(SC_FACTS)
        assert t.rows[1] == ["Stud Height (mm)", "100 mm"]

    def test_row_yield_strength(self):
        t = _build_shear_connector_table(SC_FACTS)
        assert t.rows[2][0][1].content == r"f_y"
        assert t.rows[2][1] == "250 MPa"

    def test_row_ultimate_strength(self):
        t = _build_shear_connector_table(SC_FACTS)
        assert t.rows[3][0][1].content == r"f_u"
        assert t.rows[3][1] == "410 MPa"

    def test_row_studs_per_section(self):
        t = _build_shear_connector_table(SC_FACTS)
        assert t.rows[4] == ["No. of Studs per Section", "3"]

    def test_no_latex_in_row_data(self):
        t = _build_shear_connector_table(SC_FACTS)
        for row in t.rows:
            for cell in row:
                # LaTeX math in parameter names is OK, but no raw \ commands in values
                if row.index(cell) == 1:
                    assert "\\" not in cell


class TestShearConnectorEdgeCases:
    def test_missing_values_render_as_empty(self):
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="", project_location="", designer="",
                client="", company="",
            ),
        )
        t = _build_shear_connector_table(facts)
        assert t.rows[0] == ["Stud Diameter (mm)", ""]


# ---------------------------------------------------------------------------
# Partial Safety Factors table tests
# ---------------------------------------------------------------------------

SF_FACTS = ReportFacts(
    metadata=FactMetadata(
        project_name="Test Bridge",
        project_location="Mumbai, India",
        designer="Tester",
        client="Client",
        company="Co",
    ),
    raw_input_dict={
        "design_options_cont.partial_factor.yielding_and_buckling.gamma_m0": "1.10",
        "design_options_cont.partial_factor.ultimate_stress.gamma_m1": "1.25",
        "design_options_cont.partial_factor.concrete_basic.gamma_c_basic": "1.50",
        "design_options_cont.partial_factor.reinforcing_steel.gamma_s": "1.15",
        "design_options_cont.partial_factor.shear_connectors.gamma_v": "1.25",
        "design_options_cont.partial_factor.fatigue_load.gamma_flt": "1.50",
        "design_options_cont.partial_factor.fatigue_strength.gamma_mf": "1.15",
    },
)
SF_FACTS.inputs = build_input_facts(SF_FACTS.raw_input_dict)


class TestSafetyFactorsTable:
    """Verify the semantic Partial Safety Factors table."""

    def test_caption(self):
        t = _build_safety_factors_table(SF_FACTS)
        assert t.caption == "Partial Safety Factors"

    def test_row_count(self):
        t = _build_safety_factors_table(SF_FACTS)
        assert len(t.rows) == 7

    def test_row_gamma_m0(self):
        t = _build_safety_factors_table(SF_FACTS)
        assert t.rows[0][1] == "1.10"

    def test_row_gamma_m1(self):
        t = _build_safety_factors_table(SF_FACTS)
        assert t.rows[1][0][0].content == r"\gamma_{M1}"
        assert t.rows[1][1] == "1.25"

    def test_row_gamma_c(self):
        t = _build_safety_factors_table(SF_FACTS)
        assert t.rows[2][0][0].content == r"\gamma_C"
        assert t.rows[2][1] == "1.50"

    def test_row_gamma_s(self):
        t = _build_safety_factors_table(SF_FACTS)
        assert t.rows[3][0][0].content == r"\gamma_s"
        assert t.rows[3][1] == "1.15"

    def test_row_gamma_v(self):
        t = _build_safety_factors_table(SF_FACTS)
        assert t.rows[4][0][0].content == r"\gamma_v"
        assert t.rows[4][1] == "1.25"

    def test_row_gamma_flt(self):
        t = _build_safety_factors_table(SF_FACTS)
        assert t.rows[5][0][0].content == r"\gamma_{fft}"
        assert t.rows[5][1] == "1.50"

    def test_row_gamma_mf(self):
        t = _build_safety_factors_table(SF_FACTS)
        assert t.rows[6][0][0].content == r"\gamma_{Mft}"
        assert t.rows[6][1] == "1.15"

    def test_no_latex_in_values(self):
        t = _build_safety_factors_table(SF_FACTS)
        for row in t.rows:
            assert "\\" not in row[1]


class TestSafetyFactorsEdgeCases:
    def test_missing_values_render_as_empty(self):
        facts = ReportFacts(
            metadata=FactMetadata(
                project_name="", project_location="", designer="",
                client="", company="",
            ),
        )
        t = _build_safety_factors_table(facts)
        assert t.rows[0][1] == ""
