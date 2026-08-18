# OsdagBridge Phase 1 Implementation Guide
## Core Infrastructure Setup

**Objective**: Build the foundation components that will support Requirements 2–6  
**Duration**: ~1–2 days of focused development  
**Outcome**: Reusable, validated, well-styled report components

---

## Module 1: Component Models (`components.py`)

**File location**: `src/osdagbridge/core/reports/components.py`

**Install Pydantic first**:
```bash
pip install pydantic>=2.0
```

**Complete implementation**:

```python
"""
Structured component models for OsdagBridge reports.

This module defines Pydantic models that represent report building blocks.
Models are self-validating and serialize to/from JSON/YAML for portability.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class ComponentType(str, Enum):
    """Allowed component types in a report."""
    SECTION = "section"
    TABLE = "table"
    CHART = "chart"
    TEXT = "text"
    IMAGE = "image"
    SPACER = "spacer"


class StyleRef(BaseModel):
    """Reference to a named style in the StyleSheet."""
    name: str = Field(..., description="Style name (e.g., 'table_load', 'chart_summary')")
    override: Optional[Dict[str, Any]] = Field(None, description="Optional local style overrides")
    
    class Config:
        use_enum_values = True


class TableComponent(BaseModel):
    """Structured table representation."""
    type: ComponentType = ComponentType.TABLE
    caption: str = Field(..., description="Table caption (rendered as LaTeX caption)")
    col_spec: str = Field(..., description="LaTeX column specification (e.g., 'p{3cm}|c|r')")
    header_rows: List[str] = Field(..., description="List of header row strings (one per row)")
    body: str = Field(..., description="Rendered table body (rows with & and \\\\ delimiters)")
    style: StyleRef = Field(default_factory=lambda: StyleRef(name="table_default"))
    repeat_header: Optional[str] = Field(None, description="Custom continuation header (optional)")
    auto_width: bool = Field(False, description="Auto-fit column widths")
    
    class Config:
        use_enum_values = True
    
    @validator('col_spec')
    def validate_col_spec(cls, v):
        if not v or not any(c in v for c in 'lcr|p'):
            raise ValueError("col_spec must contain valid LaTeX column descriptors (l, c, r, p, |)")
        return v


class ChartComponent(BaseModel):
    """Chart/visualization component."""
    type: ComponentType = ComponentType.CHART
    title: str = Field(..., description="Chart title")
    chart_type: str = Field(..., description="Chart type: 'bar', 'line', 'pie', etc.")
    data: Dict[str, Union[float, List[float]]] = Field(..., description="Chart data")
    x_label: str = Field(default="", description="X-axis label")
    y_label: str = Field(default="", description="Y-axis label")
    style: StyleRef = Field(default_factory=lambda: StyleRef(name="chart_default"))
    y_reference_line: Optional[float] = Field(None, description="Y-axis reference line (e.g., 1.0 for UR)")
    output_path: Optional[str] = Field(None, description="Temporary path where chart is saved")
    
    class Config:
        use_enum_values = True
    
    @validator('chart_type')
    def validate_chart_type(cls, v):
        allowed = {'bar', 'line', 'pie', 'scatter', 'histogram'}
        if v not in allowed:
            raise ValueError(f"chart_type must be one of {allowed}")
        return v


class ImageComponent(BaseModel):
    """Image/figure component."""
    type: ComponentType = ComponentType.IMAGE
    filepath: str = Field(..., description="Path to image file")
    caption: str = Field(default="", description="Image caption")
    width_cm: float = Field(default=12, description="Image width in cm")
    style: StyleRef = Field(default_factory=lambda: StyleRef(name="image_default"))
    
    class Config:
        use_enum_values = True


class TextComponent(BaseModel):
    """Plain text/paragraph component."""
    type: ComponentType = ComponentType.TEXT
    content: str = Field(..., description="LaTeX text content")
    style: StyleRef = Field(default_factory=lambda: StyleRef(name="text_default"))
    
    class Config:
        use_enum_values = True


class SpacerComponent(BaseModel):
    """Vertical spacing component."""
    type: ComponentType = ComponentType.SPACER
    height_mm: float = Field(default=5, description="Spacing height in mm")
    
    class Config:
        use_enum_values = True


class SectionComponent(BaseModel):
    """Section grouping (heading + nested components)."""
    type: ComponentType = ComponentType.SECTION
    title: str = Field(..., description="Section title")
    level: int = Field(default=1, description="Heading level: 1=chapter, 2=section, 3=subsection")
    components: List[Union[TableComponent, ChartComponent, ImageComponent, TextComponent, 'SectionComponent']] = Field(
        default_factory=list,
        description="Nested components"
    )
    style: StyleRef = Field(default_factory=lambda: StyleRef(name="section_default"))
    
    class Config:
        use_enum_values = True
    
    @validator('level')
    def validate_level(cls, v):
        if v not in {1, 2, 3, 4}:
            raise ValueError("level must be 1-4")
        return v


# Enable forward references for recursive model
SectionComponent.update_forward_refs()


class Chapter(BaseModel):
    """Top-level chapter structure."""
    number: int = Field(..., description="Chapter number")
    title: str = Field(..., description="Chapter title")
    sections: List[SectionComponent] = Field(default_factory=list, description="Chapter sections")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Chapter metadata")
    
    class Config:
        use_enum_values = True


class Report(BaseModel):
    """Complete report structure."""
    title: str = Field(..., description="Report title")
    date: Optional[str] = Field(None, description="Report date")
    author: Optional[str] = Field(None, description="Report author")
    chapters: List[Chapter] = Field(default_factory=list, description="All chapters")
    
    class Config:
        use_enum_values = True
```

**Test this module**:

```python
# tests/unit/test_components.py
import pytest
from osdagbridge.core.reports.components import (
    TableComponent, ChartComponent, SectionComponent, Chapter, StyleRef
)


def test_table_component_valid():
    """Verify table component accepts valid specifications."""
    table = TableComponent(
        caption="Test Table",
        col_spec="p{3cm}|c|r",
        header_rows=["Column 1", "Column 2", "Column 3"],
        body="A & B & C \\\\"
    )
    assert table.caption == "Test Table"
    assert table.type.value == "table"


def test_table_component_invalid_col_spec():
    """Verify table component rejects invalid column specs."""
    with pytest.raises(ValueError, match="col_spec must contain"):
        TableComponent(
            caption="Invalid",
            col_spec="xyz",  # Invalid
            header_rows=["Col1"],
            body="Data"
        )


def test_chart_component_valid():
    """Verify chart component accepts valid types."""
    chart = ChartComponent(
        title="UR Summary",
        chart_type="bar",
        data={"Girders": 0.8, "Deck": 0.6},
        y_reference_line=1.0
    )
    assert chart.y_reference_line == 1.0


def test_chart_component_invalid_type():
    """Verify chart component rejects invalid types."""
    with pytest.raises(ValueError, match="chart_type must be one of"):
        ChartComponent(
            title="Invalid",
            chart_type="invalid_type",
            data={}
        )


def test_section_nesting():
    """Verify sections can be nested."""
    table = TableComponent(
        caption="Nested Table",
        col_spec="l|c|r",
        header_rows=["A", "B"],
        body="1 & 2 \\\\"
    )
    section = SectionComponent(
        title="Test Section",
        components=[table]
    )
    assert len(section.components) == 1
    assert section.components[0].caption == "Nested Table"
```

---

## Module 2: Style System (`style_system.py`)

**File location**: `src/osdagbridge/core/reports/style_system.py`

```python
"""
Centralized style system for OsdagBridge reports.

Single source of truth for all formatting: page geometry, tables, charts, typography, colors.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, Tuple


@dataclass
class PageGeometry:
    """Page layout and margin rules."""
    width_mm: float = 210  # A4
    height_mm: float = 297  # A4
    margin_top_mm: float = 20
    margin_bottom_mm: float = 30  # Increased from 25 to prevent footer overlap (Req 2)
    margin_left_mm: float = 20
    margin_right_mm: float = 20
    footer_height_mm: float = 10
    header_height_mm: float = 10
    
    # Vertical spacing rules (Requirement 2)
    min_orphan_lines: int = 2  # Prevent rows orphaned at page bottom
    keepwithnext_threshold: int = 5  # Lines to keep with next element
    table_spacing_before_mm: float = 6
    table_spacing_after_mm: float = 6


@dataclass
class TableStyle:
    """Table formatting rules."""
    column_padding_pt: float = 6
    row_height_pt: float = 14
    header_bg_color: str = "lightgray"
    header_font_weight: str = "bold"
    font_size_pt: float = 11
    border_width_pt: float = 0.5
    hline_style: str = r"\hline"  # LaTeX command
    
    # Spacing
    inter_row_spacing_pt: float = 2
    inter_cell_spacing_pt: float = 4


@dataclass
class ChartStyle:
    """Chart/visualization formatting rules."""
    width_cm: float = 12
    height_cm: float = 8
    dpi: int = 300
    
    # Font sizes
    title_font_size_pt: int = 14
    label_font_size_pt: int = 11
    tick_font_size_pt: int = 10
    
    # Line/marker styling
    line_width_pt: float = 2.0
    marker_size_pt: float = 8
    
    # Grid and axes
    grid_enabled: bool = True
    grid_style: str = "--"
    grid_alpha: float = 0.3


@dataclass
class TypographyStyle:
    """Font and text styling."""
    main_font: str = "Computer Modern"  # LaTeX font
    main_font_size_pt: float = 11
    
    heading_font: str = "Computer Modern"
    heading_font_size_pt: float = 14
    heading_font_weight: str = "bold"
    
    code_font: str = "Courier"
    code_font_size_pt: float = 9
    
    line_spacing: float = 1.15


@dataclass
class ColorPalette:
    """Osdag color scheme (RGB hex)."""
    primary: str = "#003366"  # Dark blue
    secondary: str = "#666666"  # Gray
    accent: str = "#FF6600"  # Orange
    success: str = "#00AA00"  # Green
    warning: str = "#FFAA00"  # Amber
    error: str = "#DD0000"  # Red
    neutral: str = "#CCCCCC"  # Light gray


class StyleSheet:
    """Central source of truth for all formatting rules."""
    
    def __init__(self):
        """Initialize with default styles."""
        self.page_geometry = PageGeometry()
        
        # Named table styles
        self.table_styles: Dict[str, TableStyle] = {
            "table_default": TableStyle(),
            "table_compact": TableStyle(
                column_padding_pt=4,
                row_height_pt=12,
                font_size_pt=10
            ),
            "table_load": TableStyle(
                column_padding_pt=5,
                row_height_pt=13,
                font_size_pt=10.5
            ),
            "table_detailed": TableStyle(
                column_padding_pt=7,
                row_height_pt=16,
                font_size_pt=11
            ),
        }
        
        # Named chart styles
        self.chart_styles: Dict[str, ChartStyle] = {
            "chart_default": ChartStyle(),
            "chart_summary": ChartStyle(
                width_cm=14,
                height_cm=10,
                title_font_size_pt=16
            ),
            "chart_compact": ChartStyle(
                width_cm=10,
                height_cm=6,
                title_font_size_pt=12
            ),
        }
        
        self.typography = TypographyStyle()
        self.colors = ColorPalette()
    
    def get_table_style(self, name: str) -> TableStyle:
        """Retrieve a table style by name."""
        if name not in self.table_styles:
            raise ValueError(
                f"Unknown table style '{name}'. "
                f"Available: {', '.join(self.table_styles.keys())}"
            )
        return self.table_styles[name]
    
    def get_chart_style(self, name: str) -> ChartStyle:
        """Retrieve a chart style by name."""
        if name not in self.chart_styles:
            raise ValueError(
                f"Unknown chart style '{name}'. "
                f"Available: {', '.join(self.chart_styles.keys())}"
            )
        return self.chart_styles[name]
    
    def add_table_style(self, name: str, style: TableStyle):
        """Register a custom table style."""
        self.table_styles[name] = style
    
    def add_chart_style(self, name: str, style: ChartStyle):
        """Register a custom chart style."""
        self.chart_styles[name] = style
    
    def to_latex_preamble(self) -> str:
        """Generate LaTeX preamble commands from style definitions."""
        geometry = self.page_geometry
        typography = self.typography
        
        preamble = f"""
% Page Geometry
\\usepackage[
    paper=a4paper,
    top={geometry.margin_top_mm}mm,
    bottom={geometry.margin_bottom_mm}mm,
    left={geometry.margin_left_mm}mm,
    right={geometry.margin_right_mm}mm,
    headheight={geometry.header_height_mm}mm,
    footskip={geometry.footer_height_mm}mm
]{{geometry}}

% Typography
\\usepackage{{{typography.main_font.lower()}}}
\\renewcommand{{\\baselinestretch}}{{{typography.line_spacing}}}
\\setlength{{\\parindent}}{{0pt}}
\\setlength{{\\parskip}}{{6pt}}

% Tables
\\usepackage{{longtable}}
\\usepackage{{multirow}}
\\usepackage{{array}}
\\setlength{{\\tabcolsep}}{{{self.table_styles['table_default'].column_padding_pt}pt}}

% Graphics
\\usepackage{{graphicx}}
\\graphicspath{{{{./assets/}}}}

% Colors
\\usepackage{{xcolor}}
\\definecolor{{primary}}{{{self._hex_to_rgb(self.colors.primary)}}}{{rgb}}{{{self._hex_to_rgb_norm(self.colors.primary)}}}
\\definecolor{{error}}{{{self._hex_to_rgb(self.colors.error)}}}{{rgb}}{{{self._hex_to_rgb_norm(self.colors.error)}}}
\\definecolor{{accent}}{{{self._hex_to_rgb(self.colors.accent)}}}{{rgb}}{{{self._hex_to_rgb_norm(self.colors.accent)}}}
"""
        return preamble
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to RGB tuple (0-255 scale)."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def _hex_to_rgb_norm(hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to normalized RGB tuple (0-1 scale)."""
        r, g, b = StyleSheet._hex_to_rgb(hex_color)
        return (r/255, g/255, b/255)
    
    def __repr__(self) -> str:
        return (
            f"<StyleSheet: "
            f"Page {self.page_geometry.width_mm}x{self.page_geometry.height_mm}mm, "
            f"{len(self.table_styles)} table styles, "
            f"{len(self.chart_styles)} chart styles>"
        )
```

**Test this module**:

```python
# tests/unit/test_style_system.py
import pytest
from osdagbridge.core.reports.style_system import StyleSheet, PageGeometry, TableStyle


def test_stylesheet_initialization():
    """Verify StyleSheet initializes with default styles."""
    ss = StyleSheet()
    assert ss.page_geometry.margin_bottom_mm == 30  # Requirement 2 increase
    assert len(ss.table_styles) >= 3
    assert len(ss.chart_styles) >= 2


def test_get_table_style():
    """Verify retrieving named table styles."""
    ss = StyleSheet()
    style = ss.get_table_style("table_load")
    assert style.column_padding_pt == 5
    assert style.row_height_pt == 13


def test_unknown_table_style():
    """Verify error handling for unknown styles."""
    ss = StyleSheet()
    with pytest.raises(ValueError, match="Unknown table style"):
        ss.get_table_style("nonexistent")


def test_add_custom_style():
    """Verify adding custom styles."""
    ss = StyleSheet()
    custom = TableStyle(column_padding_pt=10, row_height_pt=20)
    ss.add_table_style("table_custom", custom)
    assert ss.get_table_style("table_custom").column_padding_pt == 10


def test_latex_preamble_generation():
    """Verify LaTeX preamble contains expected commands."""
    ss = StyleSheet()
    preamble = ss.to_latex_preamble()
    assert "geometry" in preamble
    assert "\\definecolor" in preamble
    assert "longtable" in preamble
```

---

## Module 3: Asset Manager (`asset_pipeline.py`)

**File location**: `src/osdagbridge/core/reports/asset_pipeline.py`

```python
"""
Asset pipeline for managing temporary chart and image files.

Handles generation, registration, and cleanup of visual assets.
"""

import os
import tempfile
import shutil
from typing import Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure


class AssetManager:
    """Centralized manager for temporary visual assets."""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize asset manager.
        
        Args:
            base_dir: Base directory for temp assets. If None, uses system temp.
        """
        if base_dir is None:
            base_dir = tempfile.gettempdir()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.base_dir = os.path.join(base_dir, f"osdag_assets_{timestamp}")
        os.makedirs(self.base_dir, exist_ok=True)
        
        self.assets: Dict[str, str] = {}  # {asset_id: filepath}
        self.logger = None  # Set by caller if needed
    
    def generate_bar_chart(
        self,
        title: str,
        data: Dict[str, float],
        y_label: str = "Value",
        x_label: str = "",
        y_reference: Optional[float] = None,
        style_dict: Optional[Dict] = None,
    ) -> str:
        """
        Generate a bar chart.
        
        Args:
            title: Chart title
            data: Dict of {label: value}
            y_label: Y-axis label
            x_label: X-axis label (optional)
            y_reference: Horizontal reference line (e.g., UR=1.0)
            style_dict: Dictionary with 'width_cm', 'height_cm', 'dpi', 'title_font_size_pt'
        
        Returns:
            Path to generated PNG file
        """
        style = style_dict or {}
        width_cm = style.get('width_cm', 12)
        height_cm = style.get('height_cm', 8)
        dpi = style.get('dpi', 300)
        title_fontsize = style.get('title_font_size_pt', 14)
        
        figsize_inches = (width_cm / 2.54, height_cm / 2.54)
        fig, ax = plt.subplots(figsize=figsize_inches, dpi=dpi)
        
        labels = list(data.keys())
        values = list(data.values())
        
        bars = ax.bar(labels, values, color='steelblue', alpha=0.8, edgecolor='navy', linewidth=1.5)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontsize=10)
        
        # Add reference line if specified (e.g., UR=1.0)
        if y_reference is not None:
            ax.axhline(y=y_reference, color='red', linestyle='--', linewidth=2.5, label=f'Threshold (UR={y_reference})')
            ax.legend(loc='upper right', fontsize=11)
        
        ax.set_title(title, fontsize=title_fontsize, fontweight='bold')
        ax.set_ylabel(y_label, fontsize=12)
        if x_label:
            ax.set_xlabel(x_label, fontsize=12)
        
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # Save to file
        filepath = os.path.join(self.base_dir, self._sanitize_filename(title) + '.png')
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        
        self.assets[title] = filepath
        return filepath
    
    def generate_grouped_bar_chart(
        self,
        title: str,
        data: Dict[str, Dict[str, float]],
        y_label: str = "Value",
        style_dict: Optional[Dict] = None,
    ) -> str:
        """
        Generate a grouped bar chart.
        
        Args:
            title: Chart title
            data: Dict of {group: {category: value}}
            y_label: Y-axis label
            style_dict: Styling options
        
        Returns:
            Path to generated PNG file
        """
        style = style_dict or {}
        width_cm = style.get('width_cm', 14)
        height_cm = style.get('height_cm', 8)
        dpi = style.get('dpi', 300)
        
        figsize_inches = (width_cm / 2.54, height_cm / 2.54)
        fig, ax = plt.subplots(figsize=figsize_inches, dpi=dpi)
        
        categories = list(next(iter(data.values())).keys())
        groups = list(data.keys())
        
        x = range(len(groups))
        width = 0.8 / len(categories)
        
        colors = plt.cm.Set2(range(len(categories)))
        
        for i, category in enumerate(categories):
            values = [data[group].get(category, 0) for group in groups]
            offset = width * (i - len(categories)/2 + 0.5)
            ax.bar([xi + offset for xi in x], values, width, label=category, color=colors[i])
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel(y_label, fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(groups)
        ax.legend()
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        filepath = os.path.join(self.base_dir, self._sanitize_filename(title) + '.png')
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        
        self.assets[title] = filepath
        return filepath
    
    def register_asset(self, asset_id: str, filepath: str):
        """Register a pre-existing asset file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Asset file not found: {filepath}")
        self.assets[asset_id] = filepath
    
    def get_asset_path(self, asset_id: str) -> Optional[str]:
        """Retrieve path of a registered asset."""
        return self.assets.get(asset_id)
    
    def list_assets(self) -> Dict[str, str]:
        """List all registered assets."""
        return dict(self.assets)
    
    def cleanup(self):
        """Remove all temporary assets and directory."""
        if os.path.exists(self.base_dir):
            shutil.rmtree(self.base_dir)
            self.assets.clear()
    
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Convert a title to a valid filename."""
        import re
        # Replace spaces and special chars with underscores
        name = re.sub(r'[^\w\s-]', '', name)
        name = re.sub(r'[-\s]+', '_', name)
        return name.lower()
    
    def __repr__(self) -> str:
        return f"<AssetManager: {len(self.assets)} assets in {self.base_dir}>"
```

---

## Module 4: Report Builder (Minimal Core)

**File location**: `src/osdagbridge/core/reports/report_builder.py`

```python
"""
Report builder: Assembles validated components into LaTeX documents.
"""

from typing import List, Dict, Any
from .components import (
    Chapter, SectionComponent, TableComponent, ChartComponent, 
    ImageComponent, TextComponent, SpacerComponent, ComponentType
)
from .style_system import StyleSheet
from .asset_pipeline import AssetManager
from .table_utils import make_longtable  # Existing function


class ReportBuilder:
    """Assembles validated report components into LaTeX."""
    
    def __init__(self, style_sheet: StyleSheet, asset_manager: Optional[AssetManager] = None):
        self.style_sheet = style_sheet
        self.asset_manager = asset_manager
        self.chapters: List[Chapter] = []
    
    def add_chapter(self, chapter: Chapter):
        """Add a validated chapter."""
        if not isinstance(chapter, Chapter):
            raise TypeError(f"Expected Chapter, got {type(chapter)}")
        self.chapters.append(chapter)
    
    def component_to_latex(self, component: Any) -> str:
        """Serialize a component to LaTeX string."""
        if isinstance(component, TableComponent):
            return self._render_table(component)
        elif isinstance(component, ChartComponent):
            return self._render_chart(component)
        elif isinstance(component, ImageComponent):
            return self._render_image(component)
        elif isinstance(component, TextComponent):
            return self._render_text(component)
        elif isinstance(component, SpacerComponent):
            return self._render_spacer(component)
        elif isinstance(component, SectionComponent):
            return self._render_section(component)
        else:
            raise ValueError(f"Unknown component type: {type(component)}")
    
    def _render_table(self, table: TableComponent) -> str:
        """Render a table component."""
        style = self.style_sheet.get_table_style(table.style.name)
        return make_longtable(
            col_spec=table.col_spec,
            caption=table.caption,
            header_rows=table.header_rows,
            body=table.body,
            repeat_header=table.repeat_header or table.header_rows[0],
        )
    
    def _render_chart(self, chart: ChartComponent) -> str:
        """Render a chart component."""
        if not chart.output_path and self.asset_manager:
            # Generate chart if not already generated
            chart.output_path = self.asset_manager.generate_bar_chart(
                title=chart.title,
                data=chart.data,
                y_label=chart.y_label,
                y_reference=chart.y_reference_line,
            )
        
        if chart.output_path:
            return f"""
\\begin{{figure}}[ht]
\\centering
\\includegraphics[width=12cm]{{{chart.output_path}}}
\\caption{{{chart.title}}}
\\label{{fig:{chart.title.replace(' ', '_')}}}
\\end{{figure}}
"""
        return ""
    
    def _render_image(self, image: ImageComponent) -> str:
        """Render an image component."""
        return f"""
\\begin{{figure}}[ht]
\\centering
\\includegraphics[width={image.width_cm}cm]{{{image.filepath}}}
\\caption{{{image.caption}}}
\\end{{figure}}
"""
    
    def _render_text(self, text: TextComponent) -> str:
        """Render a text component."""
        return f"{text.content}\n\n"
    
    def _render_spacer(self, spacer: SpacerComponent) -> str:
        """Render a vertical spacer."""
        return f"\\vspace{{{spacer.height_mm}mm}}\n"
    
    def _render_section(self, section: SectionComponent) -> str:
        """Render a section and nested components."""
        level_names = {1: "chapter", 2: "section", 3: "subsection", 4: "subsubsection"}
        level_cmd = level_names.get(section.level, "section")
        
        latex = f"\n\\{level_cmd}{{{section.title}}}\n"
        for component in section.components:
            latex += self.component_to_latex(component)
        return latex
    
    def build(self) -> str:
        """Assemble all chapters into complete LaTeX document."""
        latex = self.style_sheet.to_latex_preamble()
        
        latex += """
\\usepackage{needspace}
\\BeforeBeginEnvironment{longtable}{\\Needspace{5\\baselineskip}}
\\begin{document}
"""
        
        for chapter in self.chapters:
            latex += f"\n\\chapter{{{chapter.title}}}\n"
            for section in chapter.sections:
                latex += self._render_section(section)
        
        latex += "\n\\end{document}\n"
        return latex
```

---

## Initial Test & Validation

**Run tests**:

```bash
cd d:\Users\aryan\IITBombay\OsdagBridge
pytest tests/unit/test_components.py -v
pytest tests/unit/test_style_system.py -v
```

---

## Next Steps After Phase 1

1. **Migrate one existing chapter** (e.g., Chapter 3) to use components
2. **Verify PDF output matches original** (visual regression test)
3. **Implement Requirements 2–6** using the new framework

---

**End of Phase 1 Implementation Guide**
