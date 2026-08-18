# OsdagBridge Requirements 2–6 Implementation Mapping
## How the Component Framework Enables Each Requirement

**Purpose**: Show the direct connection between the new architecture and your specific requirements  
**Audience**: Development team executing Requirements 2–6

---

## Requirement 2: Layout, Footer Overlap & Vertical Spacing

**Original Problem**: Page 30 exhibits text/tables bleeding into footer margin

### Solution via Component Framework

**Before (Ad-hoc approach)**:
```python
# In chap5.py — scattered page-break rules
def generate_table_with_keepwithnext(data):
    latex = "\\needspace{5\\baselineskip}\n"
    latex += "\\keepwithnext\n"
    latex += "\\begin{longtable}{...}"
    # ... magic numbers scattered throughout
```

**After (Centralized approach)**:

1. **Edit `style_system.py`**:

```python
@dataclass
class PageGeometry:
    margin_bottom_mm: float = 30  # Was 25, increased for Req 2
    min_orphan_lines: int = 2  # Prevent row orphans
    keepwithnext_threshold: int = 5  # Lines to keep together
```

2. **Edit `report_builder.py`**:

```python
def _render_table(self, table: TableComponent) -> str:
    """Render table with pagination guardrails."""
    style = self.style_sheet.get_table_style(table.style.name)
    geometry = self.style_sheet.page_geometry
    
    # Add keepwithnext protection
    latex = f"\\Needspace{{{geometry.keepwithnext_threshold}\\baselineskip}}\n"
    
    # Render table
    latex += make_longtable(
        col_spec=table.col_spec,
        caption=table.caption,
        header_rows=table.header_rows,
        body=table.body,
    )
    
    # Add spacing after
    latex += f"\\vspace{{{geometry.table_spacing_after_mm}mm}}\n"
    
    return latex
```

3. **Update all chapter generators**:

```python
# chap5.py — now uses TableComponent
def generate_chapter_5(payload: Dict) -> Chapter:
    # No hardcoded keepwithnext; uses StyleSheet
    reinforcement_table = TableComponent(
        caption="Table 5.1: Reinforcement Details",
        col_spec="p{2cm}|c|r",
        header_rows=["Bar Size", "Quantity", "Unit"],
        body=render_reinforcement_body(payload),
        style=StyleRef(name="table_load")
    )
    return Chapter(number=5, title="Design Details", sections=[...])
```

**Result**: 
- One margin change (in `PageGeometry`) fixes footer overlap globally
- No individual chapter files need editing
- Before/after PDF margins are controlled from `StyleSheet`

---

## Requirement 3: Load & Geometry Table Refactoring

**Original Problem**: Live Loads (LL) and Footway Load merged or improperly formatted

### Solution via Component Framework

**Before (Hand-built tables)**:
```python
# chap3.py — single large table with mixed data
def generate_live_loads_table(payload):
    rows = []
    # Vehicle loads
    for vehicle in payload['vehicles']:
        rows.append(f"{vehicle['name']} & {vehicle['impact']} & {vehicle['braking']} \\\\")
    # Footway loads (same table!)
    rows.append(f"Footway & {payload['footway']['load']} \\\\")
    return "\\begin{longtable}...".join(rows)
```

**After (Separated components)**:

1. **Update `components.py`** to allow nested sections (already done)

2. **Refactor `chap3.py`**:

```python
def generate_chapter_3(payload: Dict) -> Chapter:
    """Migrated to component-based structure."""
    
    sections = []
    
    # ========== DEAD LOADS ==========
    dead_load_table = TableComponent(
        caption="Table 3.1: Dead Load (Self-Weight)",
        col_spec="p{3.5cm}|c|c|c",
        header_rows=["Component", "Unit", "Value", "Remarks"],
        body=render_dead_load_body(payload),
        style=StyleRef(name="table_load")
    )
    
    sections.append(SectionComponent(
        title="Dead Loads",
        level=2,
        components=[dead_load_table]
    ))
    
    # ========== LIVE LOADS - VEHICLE ==========
    # NEW: Get vehicle list from UI payload
    vehicle_selection = payload.get('vehicle_details', [])
    
    vehicle_load_table = TableComponent(
        caption="Table 3.3: Vehicle Live Loads",
        col_spec="p{2.5cm}|c|c|c|c",
        header_rows=[
            "Vehicle Class",
            "Impact Factor",
            "Braking Load (kN)",
            "Centrifugal (kN)",
            "Unit"
        ],
        body=render_vehicle_live_loads_body(vehicle_selection),
        style=StyleRef(name="table_load"),
        repeat_header="Vehicle Class & Impact Factor & Braking Load (kN) & Centrifugal (kN) & Unit"
    )
    
    sections.append(SectionComponent(
        title="Live Loads — Vehicles",
        level=2,
        components=[vehicle_load_table]
    ))
    
    # ========== LIVE LOADS - FOOTWAY (SEPARATE) ==========
    footway_load_table = TableComponent(
        caption="Table 3.4: Footway Live Loads",
        col_spec="p{3cm}|c|c",
        header_rows=["Load Type", "Intensity (kN/m²)", "Unit"],
        body=render_footway_live_loads_body(payload),
        style=StyleRef(name="table_load")
    )
    
    sections.append(SectionComponent(
        title="Live Loads — Footway",
        level=2,
        components=[footway_load_table]
    ))
    
    # ========== WIND LOADS ==========
    wind_load_table = TableComponent(
        caption="Table 3.5: Wind Load",
        col_spec="p{3cm}|c|c",
        header_rows=["Parameter", "Value", "Unit"],
        body=render_wind_load_body(payload),
        style=StyleRef(name="table_load")
    )
    
    sections.append(SectionComponent(
        title="Wind Loads",
        level=2,
        components=[wind_load_table]
    ))
    
    # ... (continue for other loads)
    
    return Chapter(number=3, title="Loads and Load Cases", sections=sections)


def render_vehicle_live_loads_body(vehicles: List[Dict]) -> str:
    """Render vehicle live load rows from UI-selected vehicles."""
    rows = []
    for vehicle in vehicles:
        # vehicle schema: {name, impact_factor, braking_load, centrifugal_load, unit}
        rows.append(
            f"{vehicle['name']} & "
            f"{vehicle['impact_factor']:.2f} & "
            f"{vehicle['braking_load']:.1f} & "
            f"{vehicle['centrifugal_load']:.1f} & "
            f"{vehicle['unit']} \\\\"
        )
    return "\n".join(rows)


def render_footway_live_loads_body(payload: Dict) -> str:
    """Render footway load rows."""
    footway_load = payload.get('footway_load_intensity', 4.0)  # Default 4 kN/m²
    rows = [
        f"Distributed Load & {footway_load:.1f} & kN/m$^2$ \\\\",
        f"Concentrated Load & 1.0 & kN \\\\",
    ]
    return "\n".join(rows)
```

**Result**:
- Vehicle and footway loads are now **separate, clearly labeled tables**
- Each table has its own caption and header repetition
- Vehicle selection comes **directly from UI payload**
- Easy to add new vehicle types; table structure stays the same

---

## Requirement 4: Utilization Ratio (UR) Summary Charts

**Original Problem**: No programmatic chart generation; manual embedding

### Solution via Component Framework

**Implementation**:

1. **Create chart generation helper** in a new file:

```python
# src/osdagbridge/core/reports/chart_generators.py

def generate_ur_summary_chart(
    payload: Dict,
    asset_manager: AssetManager,
    style_sheet: StyleSheet
) -> ChartComponent:
    """
    Generate Utilization Ratio (UR) summary bar chart.
    
    Args:
        payload: Design output dictionary
        asset_manager: Asset manager for file handling
        style_sheet: Global styles
    
    Returns:
        ChartComponent ready to embed in report
    """
    # Extract UR values from payload
    ur_data = {
        "Steel Plate Girders": payload['design_output']['ur_girders'],
        "Concrete Deck Slab": payload['design_output']['ur_deck'],
        "Cross Bracing": payload['design_output']['ur_bracing'],
        "End Diaphragms": payload['design_output']['ur_diaphragms'],
    }
    
    # Generate physical chart file
    chart_style = style_sheet.get_chart_style("chart_summary")
    chart_path = asset_manager.generate_bar_chart(
        title="Utilization Ratio Summary",
        data=ur_data,
        y_label="UR (Demand/Capacity)",
        x_label="Structural Element",
        y_reference=1.0,  # Red dashed line at UR=1.0
        style_dict={
            'width_cm': chart_style.width_cm,
            'height_cm': chart_style.height_cm,
            'dpi': chart_style.dpi,
            'title_font_size_pt': chart_style.title_font_size_pt,
        }
    )
    
    # Return component
    return ChartComponent(
        title="Utilization Ratio Summary",
        chart_type="bar",
        data=ur_data,
        x_label="Structural Element",
        y_label="UR (Demand/Capacity)",
        y_reference_line=1.0,
        output_path=chart_path,
        style=StyleRef(name="chart_summary")
    )
```

2. **Embed in Chapter 5 (Design Checks)**:

```python
# chap5.py — updated to use components

from .chart_generators import generate_ur_summary_chart

def generate_chapter_5(payload: Dict, asset_manager: AssetManager, style_sheet: StyleSheet) -> Chapter:
    """Chapter 5: Design Checks with UR visualization."""
    
    sections = []
    
    # Section 5.1: Design Summary
    ur_chart = generate_ur_summary_chart(payload, asset_manager, style_sheet)
    
    summary_section = SectionComponent(
        title="Overall Design Check Summary",
        level=2,
        components=[
            TextComponent(content="The following chart summarizes the utilization ratios for all primary structural elements."),
            ur_chart,
            TextComponent(content="Elements with UR > 1.0 do not meet design requirements and require revision.")
        ]
    )
    
    sections.append(summary_section)
    
    # Section 5.2: Detailed Checks...
    
    return Chapter(number=5, title="Design Checks", sections=sections)
```

3. **Chart is automatically**:
   - Generated with consistent styling (from `StyleSheet`)
   - Saved to temp directory (managed by `AssetManager`)
   - Embedded in LaTeX via `ReportBuilder._render_chart()`
   - Cleaned up after PDF compilation

**Result**:
- UR chart generated automatically
- Red dashed threshold line at UR=1.0 automatically added
- Styling consistent with rest of document
- Temp files auto-cleaned

---

## Requirement 5: Material Quantity Bar Charts

**Implementation** (same pattern as Req 4):

```python
# In chart_generators.py

def generate_material_summary_chart(
    payload: Dict,
    asset_manager: AssetManager,
    style_sheet: StyleSheet
) -> ChartComponent:
    """Generate material quantity summary chart."""
    
    material_data = {
        "Steel Girders (MT)": payload['material_takeoff']['steel_girders'],
        "Steel Bracing (MT)": payload['material_takeoff']['steel_bracing'],
        "Steel Diaphragms (MT)": payload['material_takeoff']['steel_diaphragms'],
        "Concrete Deck (m³)": payload['material_takeoff']['concrete_deck'],
        "Reinforcement (MT)": payload['material_takeoff']['reinforcement'],
    }
    
    chart_path = asset_manager.generate_bar_chart(
        title="Material Quantity Summary",
        data=material_data,
        y_label="Quantity (MT / m³)",
        style_dict={
            'width_cm': 14,
            'height_cm': 8,
            'dpi': 300,
        }
    )
    
    return ChartComponent(
        title="Material Quantity Summary",
        chart_type="bar",
        data=material_data,
        y_label="Quantity (MT / m³)",
        output_path=chart_path,
        style=StyleRef(name="chart_summary")
    )
```

**Embed in Chapter 7**:

```python
# chap7.py

def generate_chapter_7(payload: Dict, asset_manager: AssetManager, style_sheet: StyleSheet) -> Chapter:
    """Chapter 7: Material Take-off & Quantity Summary."""
    
    material_chart = generate_material_summary_chart(payload, asset_manager, style_sheet)
    
    sections = [
        SectionComponent(
            title="Material Summary",
            level=2,
            components=[material_chart]
        ),
        # ... detail tables follow
    ]
    
    return Chapter(number=7, title="Material Take-off", sections=sections)
```

---

## Requirement 6: Centralized Formatting & Style System

**Already Implemented in Phase 1!**

The `StyleSheet` class is your single source of truth. Every chapter imports and uses it:

```python
# All chapters use the same pattern:
from osdagbridge.core.reports.style_system import StyleSheet

def generate_chapter_X(payload, asset_manager):
    style_sheet = StyleSheet()  # Global instance
    
    table = TableComponent(
        caption="...",
        col_spec="...",
        # ...
        style=StyleRef(name="table_load")  # References StyleSheet
    )
```

**Example: Change all table padding globally**:

```python
# In style_system.py — one change, entire document updated
@dataclass
class TableStyle:
    column_padding_pt: float = 7  # Was 6 → increased
    row_height_pt: float = 14
    # ... rest unchanged
```

**Result**: All tables now have 7pt padding. No chapter file edits needed.

---

## Summary: Requirements 2–6 via Component Framework

| Requirement | Before | After | Enabled By |
|-------------|--------|-------|-----------|
| **Req 2: Footer Overlap** | Scattered `\keepwithnext` in chapters | Centralized in `PageGeometry` | `StyleSheet` |
| **Req 3: Load Tables** | Mixed vehicle+footway; hardcoded | Separate `TableComponent` instances; vehicle selection from UI | Component model |
| **Req 4: UR Charts** | Manual embedding; inconsistent styling | Auto-generated `ChartComponent`; consistent styling | `AssetManager` + `StyleSheet` |
| **Req 5: Material Charts** | Ad-hoc script | Same pattern as Req 4 | Component library |
| **Req 6: Formatting** | Scattered across chapters | Single `StyleSheet` instance | `StyleSheet` class |

---

## Integration Checklist

### Step 1: Implement Phase 1 infrastructure
- [ ] `components.py` created and tested
- [ ] `style_system.py` created and tested
- [ ] `asset_pipeline.py` created and tested
- [ ] `report_builder.py` created and tested

### Step 2: Migrate one chapter
- [ ] Refactor `chap3.py` to use `TableComponent`
- [ ] Generate PDF and verify visual match
- [ ] Commit to git (checkpoint)

### Step 3: Implement Requirements 2–6
- [ ] Adjust `PageGeometry` for Req 2
- [ ] Refactor `chap3.py` live loads for Req 3 (separate tables)
- [ ] Implement `chart_generators.py` (Req 4 & 5)
- [ ] Verify `StyleSheet` usage (Req 6)

### Step 4: Migrate remaining chapters
- [ ] Apply component pattern to all chapters
- [ ] Full regression test
- [ ] Production release

---

## Example: Before/After Code Diff

**Before (Ad-hoc)**:
```python
# chap3.py (150 lines of mixed concerns)
def generate_chapter_3_loads(payload):
    latex = "\\chapter{Loads}\n"
    latex += "\\section{Dead Loads}\n"
    # Hardcoded table
    latex += "\\begin{longtable}{p{3cm}|c|r}\n"
    latex += "\\caption{Dead Load}\\\\\n"
    # ... rows ...
    latex += "\\end{longtable}\n"
    
    # Vehicle and footway loads mixed
    latex += "\\section{Live Loads}\n"
    latex += "\\begin{longtable}{...}\n"  # Vehicle data
    # ... vehicle rows ...
    # ... footway rows ... (same table!)
    latex += "\\end{longtable}\n"
    
    # Hardcoded styling scattered throughout
    return latex
```

**After (Component-based)**:
```python
# chap3.py (80 lines, cleaner separation)
from components import TableComponent, Chapter, SectionComponent, StyleRef

def generate_chapter_3(payload, asset_manager):
    sections = []
    
    # Dead loads
    dead_load = TableComponent(
        caption="Table 3.1: Dead Load",
        col_spec="p{3cm}|c|r",
        header_rows=["Component", "Unit", "Value"],
        body=render_dead_load_body(payload),
        style=StyleRef(name="table_load")
    )
    sections.append(SectionComponent(title="Dead Loads", level=2, components=[dead_load]))
    
    # Vehicle live loads
    vehicle_loads = TableComponent(
        caption="Table 3.3: Vehicle Live Loads",
        col_spec="p{2.5cm}|c|c|c|c",
        header_rows=["Vehicle", "Impact", "Braking", "Centrifugal", "Unit"],
        body=render_vehicle_loads(payload.get('vehicles')),
        style=StyleRef(name="table_load")
    )
    sections.append(SectionComponent(title="Live Loads — Vehicles", level=2, components=[vehicle_loads]))
    
    # Footway live loads (separate!)
    footway_loads = TableComponent(
        caption="Table 3.4: Footway Live Loads",
        col_spec="p{3cm}|c|c",
        header_rows=["Load Type", "Intensity", "Unit"],
        body=render_footway_loads(payload),
        style=StyleRef(name="table_load")
    )
    sections.append(SectionComponent(title="Live Loads — Footway", level=2, components=[footway_loads]))
    
    return Chapter(number=3, title="Loads", sections=sections)
```

**Benefits**:
- Code is self-documenting (table structure visible at a glance)
- Styling is parameterized (not hardcoded)
- Tables are reusable components (can be moved, reordered, duplicated)
- Validation happens at object creation, not at compile time
- Easy to test (components are Pydantic models; serialize to JSON for test fixtures)

---

**End of Requirements Mapping**
