# OsdagBridge Report Generation — Architectural Transformation
## From Ad-Hoc to Structured Component Framework

**Date:** 2026-08-17  
**Phase:** Pre-Implementation Strategic Planning  
**Scope:** Requirements 2–6 + Structural Improvements

---

## Executive Summary

The current report generation architecture (post-Requirement 1) is **procedural and linear**: chapter generators produce LaTeX strings that `report_generator.py` assembles and compiles.

This works well for incremental fixes, but it creates **friction for future enhancements**:

- **Problem 1**: No schema/contract. Each chapter can produce any LaTeX; there's no guarantee about structure.
- **Problem 2**: Formatting is scattered. Colors, fonts, spacing are hardcoded in multiple places.
- **Problem 3**: Assets (charts, images) are handled ad-hoc. Chart generation, embedding, and cleanup are duplicated.
- **Problem 4**: Reusability is limited. Similar tables/sections require manual duplication.
- **Problem 5**: Validation happens at compile time (via pdflatex), not at generation time.

**Proposal**: Introduce a **Component-Based Report Framework** that treats reports as structured assemblies of reusable, validated, styled components.

---

## Vision: Report as Structured Data

Instead of:
```
chapter_generator() → LaTeX string → report_generator.py → pdflatex
```

Introduce:
```
report_spec.yaml (or Python) 
    ↓
ReportBuilder (validates, assembles)
    ↓
Component objects (table, chart, section)
    ↓
Style system (queries formatting rules)
    ↓
LaTeX serialization (generates strings)
    ↓
report_generator.py (final assembly)
    ↓
pdflatex
```

**Key insight**: Separate the *what* (report structure, data, components) from the *how* (LaTeX rendering, styling, pagination).

---

## Phase 1: Core Infrastructure (Foundation for Req 2–6)

### 1.1 Pydantic-Based Component Model

**File**: `src/osdagbridge/core/reports/components.py`

Define structured types that represent report building blocks:

```python
from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum

class ComponentType(str, Enum):
    SECTION = "section"
    TABLE = "table"
    CHART = "chart"
    TEXT = "text"
    IMAGE = "image"
    SPACER = "spacer"

class StyleRef(BaseModel):
    """Reference to a named style (resolved from style system)."""
    name: str
    override: Optional[Dict[str, str]] = None  # Optional local override

class TableComponent(BaseModel):
    """Structured table representation."""
    type: ComponentType = ComponentType.TABLE
    caption: str
    col_spec: str
    header_rows: List[str]
    body: str  # Still opaque; caller supplies rendered rows
    style: StyleRef = StyleRef(name="table_default")
    repeat_header: Optional[str] = None
    auto_width: bool = False

class ChartComponent(BaseModel):
    """Chart/visualization component."""
    type: ComponentType = ComponentType.CHART
    title: str
    chart_type: str  # "bar", "line", "pie"
    data: Dict[str, List[float]]
    x_label: str
    y_label: str
    style: StyleRef = StyleRef(name="chart_default")
    y_reference_line: Optional[float] = None  # e.g., 1.0 for UR threshold
    output_path: Optional[str] = None  # Where to save temp image

class SectionComponent(BaseModel):
    """Section grouping (heading + content)."""
    type: ComponentType = ComponentType.SECTION
    title: str
    level: int = 1  # 1 = chapter, 2 = section, 3 = subsection
    components: List['ComponentType'] = []  # Nested components
    style: StyleRef = StyleRef(name="section_default")

class Chapter(BaseModel):
    """Top-level chapter structure."""
    number: int
    title: str
    sections: List[SectionComponent]
    metadata: Dict[str, str] = {}
```

**Benefits**:
- Type safety (Pydantic validates at object creation time).
- Self-documenting (code is the specification).
- Easy to serialize/deserialize (YAML, JSON).
- Enables validation *before* LaTeX generation.

### 1.2 Style System (Centralized)

**File**: `src/osdagbridge/core/reports/style_system.py`

```python
from dataclasses import dataclass
from typing import Dict, Optional
import json

@dataclass
class PageGeometry:
    """Page layout rules."""
    width_mm: float = 210
    height_mm: float = 297
    margin_top_mm: float = 20
    margin_bottom_mm: float = 25
    margin_left_mm: float = 20
    margin_right_mm: float = 20
    footer_height_mm: float = 10

@dataclass
class TableStyle:
    """Table formatting rules."""
    column_padding_pt: float = 6
    row_height_pt: float = 14
    header_bg_color: str = "lightgray"
    font_size_pt: float = 11
    border_width_pt: float = 0.5
    hline_style: str = r"\hline"

@dataclass
class ChartStyle:
    """Chart/visualization rules."""
    width_cm: float = 12
    height_cm: float = 8
    dpi: int = 300
    title_font_size: int = 12
    label_font_size: int = 10
    line_width: float = 2.0

@dataclass
class TypographyStyle:
    """Font and text styling."""
    main_font: str = "Computer Modern"
    main_font_size_pt: float = 11
    heading_font_size_pt: float = 14
    code_font_size_pt: float = 9

@dataclass
class ColorPalette:
    """Osdag color scheme."""
    primary: str = "#003366"  # Dark blue
    accent: str = "#FF6600"   # Orange
    success: str = "#00AA00"  # Green
    warning: str = "#FFAA00"  # Amber
    error: str = "#DD0000"    # Red
    neutral: str = "#999999"  # Gray

class StyleSheet:
    """Central source of truth for all formatting."""
    
    def __init__(self):
        self.page_geometry = PageGeometry()
        self.table_styles = {
            "table_default": TableStyle(),
            "table_compact": TableStyle(column_padding_pt=4, row_height_pt=12),
            "table_load": TableStyle(column_padding_pt=5, row_height_pt=13),
        }
        self.chart_styles = {
            "chart_default": ChartStyle(),
            "chart_summary": ChartStyle(width_cm=14, height_cm=10),
        }
        self.typography = TypographyStyle()
        self.colors = ColorPalette()
    
    def get_table_style(self, name: str) -> TableStyle:
        """Retrieve a table style by name."""
        if name not in self.table_styles:
            raise ValueError(f"Unknown table style: {name}")
        return self.table_styles[name]
    
    def get_chart_style(self, name: str) -> ChartStyle:
        """Retrieve a chart style by name."""
        if name not in self.chart_styles:
            raise ValueError(f"Unknown chart style: {name}")
        return self.chart_styles[name]
    
    def to_latex_preamble(self) -> str:
        """Generate LaTeX preamble from style definitions."""
        # Convert all style rules into corresponding LaTeX commands
        preamble = f"""
\\usepackage[
    top={self.page_geometry.margin_top_mm}mm,
    bottom={self.page_geometry.margin_bottom_mm}mm,
    left={self.page_geometry.margin_left_mm}mm,
    right={self.page_geometry.margin_right_mm}mm
]{{geometry}}

\\definecolor{{primary}}{{{self.colors.primary}}}
\\definecolor{{accent}}{{{self.colors.accent}}}
\\definecolor{{error}}{{{self.colors.error}}}

\\setlength{{\\tabcolsep}}{{{self.table_styles['table_default'].column_padding_pt}pt}}
"""
        return preamble
```

**Benefits**:
- All formatting in one place.
- Programmatic access to style attributes.
- Easy to generate LaTeX preamble from style definitions.
- One change updates entire document.

### 1.3 Report Builder

**File**: `src/osdagbridge/core/reports/report_builder.py`

```python
from typing import List, Dict, Any
from .components import Chapter, ComponentType
from .style_system import StyleSheet
from .table_utils import make_longtable

class ReportBuilder:
    """Assembles validated components into a report."""
    
    def __init__(self, payload: Dict[str, Any], style_sheet: StyleSheet):
        self.payload = payload
        self.style_sheet = style_sheet
        self.chapters: List[Chapter] = []
        self.asset_registry: Dict[str, str] = {}  # {asset_id: filepath}
    
    def register_asset(self, asset_id: str, filepath: str):
        """Register a temporary asset (chart, image)."""
        self.asset_registry[asset_id] = filepath
    
    def add_chapter(self, chapter: Chapter):
        """Add a validated chapter."""
        # Validation: ensure chapter structure is valid
        if not isinstance(chapter, Chapter):
            raise TypeError(f"Expected Chapter, got {type(chapter)}")
        self.chapters.append(chapter)
    
    def component_to_latex(self, component: Any) -> str:
        """Serialize a component to LaTeX string."""
        if isinstance(component, TableComponent):
            return self._render_table(component)
        elif isinstance(component, ChartComponent):
            return self._render_chart(component)
        elif isinstance(component, SectionComponent):
            return self._render_section(component)
        else:
            raise ValueError(f"Unknown component type: {type(component)}")
    
    def _render_table(self, table: TableComponent) -> str:
        """Render a table component using table_utils helper."""
        style = self.style_sheet.get_table_style(table.style.name)
        return make_longtable(
            col_spec=table.col_spec,
            caption=table.caption,
            header_rows=table.header_rows,
            body=table.body,
            repeat_header=table.repeat_header,
        )
    
    def _render_chart(self, chart: ChartComponent) -> str:
        """Render a chart component to LaTeX includegraphics."""
        # Chart generation happens here; asset is registered
        chart_path = self._generate_chart(chart)
        self.register_asset(chart.title, chart_path)
        return f"""
\\begin{{figure}}[ht]
\\centering
\\includegraphics[width=12cm]{{{chart_path}}}
\\caption{{{chart.title}}}
\\end{{figure}}
"""
    
    def _generate_chart(self, chart: ChartComponent) -> str:
        """Generate actual chart file. Can use matplotlib, plotly, etc."""
        # Implementation details: matplotlib → PNG/PDF
        pass
    
    def _render_section(self, section: SectionComponent) -> str:
        """Render a section and its nested components."""
        level_cmd = {1: "chapter", 2: "section", 3: "subsection"}.get(section.level)
        latex = f"\n\\{level_cmd}{{{section.title}}}\n"
        for component in section.components:
            latex += self.component_to_latex(component)
        return latex
    
    def build(self) -> str:
        """Assemble all chapters into a complete LaTeX document."""
        all_latex = self.style_sheet.to_latex_preamble()
        for chapter in self.chapters:
            for section in chapter.sections:
                all_latex += self._render_section(section)
        return all_latex
    
    def cleanup_assets(self):
        """Clean up temporary chart/image files after compilation."""
        import os
        for asset_id, filepath in self.asset_registry.items():
            if os.path.exists(filepath):
                os.remove(filepath)
```

**Benefits**:
- Central control point for report assembly.
- Asset lifecycle management (registration → cleanup).
- Consistent component serialization.
- Easy to add validation hooks.

### 1.4 Asset Pipeline

**File**: `src/osdagbridge/core/reports/asset_pipeline.py`

```python
import os
import tempfile
from typing import Dict, List
import matplotlib.pyplot as plt
from datetime import datetime

class AssetManager:
    """Handles temporary asset (chart, image) generation and cleanup."""
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = tempfile.gettempdir()
        self.base_dir = os.path.join(base_dir, f"osdag_assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        os.makedirs(self.base_dir, exist_ok=True)
        self.assets: Dict[str, str] = {}
    
    def generate_chart(self, title: str, chart_type: str, data: Dict, **kwargs) -> str:
        """Generate a chart and return its path."""
        filepath = os.path.join(self.base_dir, f"{title.replace(' ', '_')}.png")
        
        fig, ax = plt.subplots(figsize=kwargs.get('figsize', (12, 8)))
        
        if chart_type == "bar":
            x = list(data.keys())
            y = list(data.values())
            ax.bar(x, y, color=kwargs.get('color', 'steelblue'))
        elif chart_type == "line":
            ax.plot(data.keys(), data.values())
        
        ax.set_title(title, fontsize=kwargs.get('title_fontsize', 12))
        ax.set_xlabel(kwargs.get('x_label', ''))
        ax.set_ylabel(kwargs.get('y_label', ''))
        
        # Add reference line if specified (e.g., UR=1.0)
        if 'y_reference' in kwargs:
            ax.axhline(y=kwargs['y_reference'], color='r', linestyle='--', linewidth=2, label='UR=1.0')
            ax.legend()
        
        plt.tight_layout()
        fig.savefig(filepath, dpi=kwargs.get('dpi', 300))
        plt.close(fig)
        
        self.assets[title] = filepath
        return filepath
    
    def cleanup(self):
        """Remove all temporary assets."""
        import shutil
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
    
    def get_asset_path(self, title: str) -> str:
        """Retrieve path of a generated asset."""
        return self.assets.get(title)
```

**Benefits**:
- Centralized chart/image generation.
- Automatic temp directory management.
- Easy cleanup after report compilation.

---

## Phase 2: Applying Framework to Requirements 2–6

### 2.1 Requirement 2: Layout & Footer Overlap Fixes

**Implementation via Style System**:

```python
# In style_system.py
class PageGeometry:
    margin_bottom_mm: float = 30  # Increase from 25 to prevent overlap
    keepwithnext_threshold: int = 5  # Minimum lines to keep with next

class TableStyle:
    row_height_pt: float = 14
    orphan_lines: int = 2  # Prevent orphaned rows
```

**Validation in ReportBuilder**:
- Check row heights + page margins don't exceed page bounds.
- Flag tables with orphaned rows before compilation.

**Result**: Vertical spacing is now parameterized and easily adjustable globally.

### 2.2 Requirement 3: Load & Geometry Table Refactoring

**Using Component Model**:

```python
# Chapter 3 generator
from components import TableComponent, Chapter, SectionComponent, StyleRef

def generate_chapter_3(payload: Dict) -> Chapter:
    sections = []
    
    # Dead Load table
    dead_load_table = TableComponent(
        caption="Table 3.1: Dead Load (Self-Weight)",
        col_spec="p{3cm}p{2cm}p{2cm}p{2cm}",
        header_rows=["Component", "Unit", "Value", "Remark"],
        body=render_dead_load_body(payload),
        style=StyleRef(name="table_load")
    )
    
    # Live Load table (separate)
    live_load_table = TableComponent(
        caption="Table 3.3: Vehicle Live Loads",
        col_spec="p{2.5cm}p{2cm}p{2cm}p{2cm}p{2cm}",
        header_rows=["Vehicle Class", "Impact Factor", "Braking Load", "Centrifugal", "Unit"],
        body=render_live_load_body(payload),  # From UI selection
        style=StyleRef(name="table_load"),
        repeat_header=render_live_load_header()
    )
    
    # Footpath Live Loads (separate table)
    footpath_table = TableComponent(
        caption="Table 3.4: Footpath Live Loads",
        col_spec="p{3cm}p{2cm}p{2cm}",
        header_rows=["Load Type", "Unit", "Value"],
        body=render_footpath_body(payload),  # Formatted from UI
        style=StyleRef(name="table_load")
    )
    
    sections.append(SectionComponent(
        title="Dead Loads",
        level=2,
        components=[dead_load_table]
    ))
    
    sections.append(SectionComponent(
        title="Live Loads",
        level=2,
        components=[live_load_table, footpath_table]
    ))
    
    return Chapter(number=3, title="Loads", sections=sections)
```

**Benefits**:
- Clear separation of vehicle vs. footpath loads.
- Reusable component structure.
- Easy to add new load tables without modifying core logic.

### 2.3 Requirement 4: Utilization Ratio Charts

**Using Chart Component**:

```python
from components import ChartComponent, StyleRef
from asset_pipeline import AssetManager

def generate_ur_summary(payload: Dict, asset_mgr: AssetManager) -> ChartComponent:
    """Generate UR summary chart."""
    
    ur_data = {
        "Steel Plate Girders": payload['utilization_ratio']['girders'],
        "Concrete Deck Slab": payload['utilization_ratio']['deck'],
        "Cross Bracing": payload['utilization_ratio']['bracing'],
        "End Diaphragms": payload['utilization_ratio']['diaphragms'],
    }
    
    chart = ChartComponent(
        title="Utilization Ratio Summary",
        chart_type="bar",
        data=ur_data,
        x_label="Structural Element",
        y_label="UR (Demand/Capacity)",
        style=StyleRef(name="chart_summary"),
        y_reference_line=1.0  # Red dashed line at UR=1.0
    )
    
    # Asset manager generates the actual chart
    chart_path = asset_mgr.generate_chart(
        title=chart.title,
        chart_type=chart.chart_type,
        data=ur_data,
        y_reference=1.0,
        title_fontsize=14
    )
    
    chart.output_path = chart_path
    return chart
```

**Result**: Charts are structured, validated, and managed consistently.

### 2.4 Requirement 5: Material Quantity Charts

**Same pattern**: `MaterialQuantityComponent` → `asset_mgr.generate_chart()` → embedded in Chapter 7.

### 2.5 Requirement 6: Centralized Formatting

**Already addressed by Phase 1**:
- `StyleSheet` is the single source of truth.
- All chapters import and query from it.
- One change affects entire document.

---

## Phase 3: Configuration as Code (Optional but Powerful)

**File**: `src/osdagbridge/core/reports/report_spec.yaml`

```yaml
document:
  title: "OsdagBridge Design Report"
  author: "Osdag Team"
  date_format: "%Y-%m-%d"

style:
  page_geometry:
    margin_top_mm: 20
    margin_bottom_mm: 30  # Increased for footer
    margin_left_mm: 20
    margin_right_mm: 20
  
  table_styles:
    table_load:
      column_padding_pt: 5
      row_height_pt: 13
    table_compact:
      column_padding_pt: 4
      row_height_pt: 12
  
  colors:
    primary: "#003366"
    error: "#DD0000"

chapters:
  - number: 3
    title: "Loads"
    sections:
      - title: "Dead Loads"
        components:
          - type: "table"
            id: "dead_load"
            style: "table_load"
      - title: "Live Loads"
        components:
          - type: "table"
            id: "vehicle_loads"
            style: "table_load"
          - type: "table"
            id: "footpath_loads"
            style: "table_load"
  
  - number: 5
    title: "Design Checks"
    sections:
      - title: "Utilization Ratios"
        components:
          - type: "chart"
            id: "ur_summary"
            chart_type: "bar"
            y_reference: 1.0
            style: "chart_summary"
```

**Benefits**:
- Non-programmers can understand report structure.
- Easy to reorder/add sections without code changes.
- Spec is documentation.

---

## Phase 4: Implementation Roadmap

### Step 1: Create Core Infrastructure
1. `components.py` (Pydantic models)
2. `style_system.py` (StyleSheet class)
3. `report_builder.py` (ReportBuilder class)
4. `asset_pipeline.py` (AssetManager class)

**Time estimate**: 1–2 days  
**Validation**: Unit tests for each module

### Step 2: Migrate Existing Chapters
1. Refactor `chap3.py` to use `TableComponent`
2. Refactor `chap5.py` to use `TableComponent` + `ChartComponent`
3. Update `table_utils.make_longtable()` to accept `StyleRef`

**Time estimate**: 2–3 days  
**Validation**: Compare generated PDFs before/after; ensure no regressions

### Step 3: Implement Requirements 2–6
1. **Req 2**: Adjust `PageGeometry` in `StyleSheet`
2. **Req 3**: Add `footpath_load_table` as separate component in chap3
3. **Req 4**: Implement `generate_ur_summary()` chart
4. **Req 5**: Implement material quantity charts
5. **Req 6**: Leverage `StyleSheet` (already done in Phase 1)

**Time estimate**: 3–5 days  
**Validation**: Visual inspection of generated PDFs

### Step 4: Polish & Documentation
1. Create `report_spec.yaml` template
2. Write developer guide (how to add new chapters)
3. Add comprehensive docstrings

**Time estimate**: 1–2 days

---

## Why This Approach is Better

| Aspect | Current | Proposed |
|--------|---------|----------|
| **Formatting consistency** | Scattered, hardcoded | Centralized, queryable |
| **Validation** | Only at compile time | At object creation time |
| **Reusability** | Manual duplication | Component library |
| **Asset management** | Ad-hoc | Centralized pipeline |
| **Adding new chapter** | Copy-paste existing code | Implement component interface |
| **Changing global layout** | Find and edit multiple files | Adjust `StyleSheet` |
| **Testing** | Only full-PDF regression | Component unit tests |
| **Documentation** | Implicit in code | Component specs are documentation |

---

## Structural Insight: "Report as Data"

The key insight is to **separate the report definition from its rendering**:

```
Report Definition (Pydantic models)
    ↓
Validation & Transformation
    ↓
Rendering (LaTeX, PDF, HTML, etc.)
```

This enables:
- **Multiple outputs**: Same report spec → LaTeX, HTML, Markdown
- **Validation before rendering**: Catch errors early
- **Easy testing**: Test component logic separately from LaTeX
- **Future extensibility**: Add new component types without touching core

---

## Immediate Next Steps

1. **Review this roadmap** with your team.
2. **Decide**: Full Phase 1–4, or staged implementation?
3. **Create a Git branch** for Phase 1 infrastructure.
4. **Start with** `components.py` (smallest, self-contained module).

---

## Questions to Consider

1. **Pydantic vs. dataclasses**? (Pydantic is more powerful but heavier)
2. **YAML spec file or pure Python**? (Both supported in proposed architecture)
3. **How versioned should StyleSheet be**? (Git-track + documentation)
4. **Should chapter generators be auto-discovered** from a registry?

---

**End of Architectural Roadmap**
