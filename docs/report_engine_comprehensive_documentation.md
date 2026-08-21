# OsdagBridge Semantic Report Engine — Comprehensive Architectural & Implementation Reference

**Document Version:** 2.0.0 (Production Accepted Baseline)  
**Date:** August 21, 2026  
**System Baseline:** `report-engine-production-accepted`  
**Target Repository:** OsdagBridge (`src/osdagbridge/core/report_engine/`)  

---

## Table of Contents

1. [Executive Summary & Background](#1-executive-summary--background)
2. [Complete 10-Tier Architectural Pipeline](#2-complete-10-tier-architectural-pipeline)
3. [Core Data Models & Invariant Safety](#3-core-data-models--invariant-safety)
4. [Chapter-by-Chapter Architectural Breakdown](#4-chapter-by-chapter-architectural-breakdown)
   - [Executive Summary (Summary & Table 1)](#41-executive-summary)
   - [Chapter 1: Project Information](#42-chapter-1-project-information)
   - [Chapter 2: Input Parameters & Geometry](#43-chapter-2-input-parameters--geometry)
   - [Chapter 3: Loads & Combinations](#44-chapter-3-loads--combinations)
   - [Chapter 4: Analysis Results](#45-chapter-4-analysis-results)
   - [Chapter 5: Design Checks (30+ Verification Checks)](#46-chapter-5-design-checks)
   - [Chapter 6: Drawings & CAD Visualizations](#47-chapter-6-drawings--visualizations)
   - [Chapter 7: Material Take-off & Quantity Summary](#48-chapter-7-material-take-off)
   - [Chapter 8: Standards, Assumptions & Limitations](#49-chapter-8-standards-assumptions--limitations)
5. [Visual System & Theme Architecture (ReportTheme)](#5-visual-system--theme-architecture-reporttheme)
   - [Centralized Color Hierarchy & Monochromatic Aesthetics](#51-centralized-color-hierarchy)
   - [Table Group Row Rules (`TableStyle`)](#52-table-group-row-rules)
   - [Unified Chart Palette & Automatic Figure Numbering](#53-unified-chart-palette--figure-numbering)
6. [Advanced LaTeX Rendering & Layout Engineering](#6-advanced-latex-rendering--layout-engineering)
   - [Semantic Math Escaping & AST Formula Protection](#61-semantic-math-escaping)
   - [Dynamic Geometry & Multi-Page `longtable` Handling](#62-dynamic-geometry--longtable-handling)
   - [Landscape Flow Isolation (`osdaglandscape`)](#63-landscape-flow-isolation)
7. [Quality Assurance, Preflight & Verification Infrastructure](#7-quality-assurance-preflight--verification-infrastructure)
   - [Preflight Binary Analysis (`PDFPreflight`)](#71-preflight-binary-analysis)
   - [Structural Manifest Parity System (`manifest.py`)](#72-structural-manifest-parity-system)
   - [Multi-Configuration Production Acceptance Suite](#73-multi-configuration-production-acceptance-suite)
8. [Comprehensive Log of Bugs Resolved & Refinements Made](#8-comprehensive-log-of-bugs-resolved--refinements-made)
9. [Developer Extension Guide](#9-developer-extension-guide)

---

## 1. Executive Summary & Background

### 1.1 The Legacy Challenge
Historically, the OsdagBridge PDF report was assembled through monolithic procedural string-concatenation scripts (`chap1.py` through `chap8.py`). While functional for the initial 5-girder prototype, this approach suffered from fundamental structural deficiencies:
1. **Tight Coupling to LaTeX Code:** Engineering logic was intertwined with raw LaTeX formatting commands, making styling changes dangerous and error-prone.
2. **Brittle Girder Scaling:** Tables assumed static girder counts (3 to 5 girders). When scaled to 9, 10, or 20 girders, wide horizontal tables overflowed off the page margins and collided with headers/footers.
3. **Data Mutation & Provenance Loss:** Empty or missing values were silently coerced to `0.0`, violating the fundamental engineering invariant that `None ≠ 0.0` (an unavailable design check or optional diaphragm is *not* a member with zero capacity).
4. **Formatting Inconsistencies:** Floating-point numbers displayed excessive raw precision or scientific notation (`1.881958e+06`), inequality signs rendered as upside-down question marks (`¿`) in standard TeX OT1 encodings, and raw LaTeX math syntax was exposed as unformatted text.
5. **Aesthetic Disconnect:** Visual elements such as Matplotlib bar charts used arbitrary rainbow color cycles that did not reflect Osdag's corporate design language.

### 1.2 The Semantic Engine Solution
The **OsdagBridge Semantic Report Engine** completely replaces raw string manipulation with an immutable, type-safe, intermediate Abstract Syntax Tree (AST) pipeline. Engineering facts are extracted once into typed dataclasses, validated against structural invariants, represented as abstract document components (`Chapter`, `Section`, `Table`, `TableGroup`, `Chart`, `Figure`), and compiled into clean LaTeX via a centralized `ReportTheme`.

```
========================================================================================
                          OSDAGBRIDGE REPORT ENGINE ARCHITECTURE
========================================================================================
  [1] Raw Payload (UI / Analysis / Optimization Outputs)
         ↓
  [2] Payload Validation (validate_payload: structural preconditions)
         ↓
  [3] Provenance Tracking (ProvenanceTracker: tracks key origin & conversions)
         ↓
  [4] Fact Extraction (ReportFacts: immutable, strongly-typed domain models)
         ↓
  [5] Fact Validation (validate_facts: domain bounds & engineering invariants)
         ↓
  [6] Semantic AST Assembly (ReportDocument: Chapter, Section, Table, Chart)
         ↓
  [7] Contract & Manifest Verification (Structural Manifest AST comparison)
         ↓
  [8] Theme & Layout Application (ReportTheme: colors, typography, TableStyle)
         ↓
  [9] LaTeX Compilation (LatexRenderer → pdflatex)
         ↓
 [10] Automated PDF Preflight (PDFPreflight: footer clearance, horizontal margins)
========================================================================================
```

---

## 2. Complete 10-Tier Architectural Pipeline

### Tier 1: Raw Input Payload
Receives unstructured UI inputs, optimization outputs, grillage analysis dictionaries, and design check results from the Osdag core solver.

### Tier 2: Payload Validation (`validate_payload`)
Performs early fast-failing validation before any report generation begins:
- Checks that span length $L > 0$, carriageway width $W > 0$, and girder count $N \ge 2$.
- Validates the presence of mandatory limit-state load combinations.
- Ensures metadata fields (Project Name, Designer) are cleanly typed.

### Tier 3: Provenance Tracking (`ProvenanceTracker`)
Every engineering fact extracted into the engine records its exact origin:
- Raw source dictionary key (e.g., `typical_section.no_of_girders`).
- Original unformatted value.
- Unit transformation applied (e.g., $\text{mm} \to \text{m}$, $\text{N} \to \text{kN}$, $\text{N/mm}^2 \to \text{MPa}$).
- Enables complete traceability from the final PDF page back to the exact Python variable.

### Tier 4: Typed Report Facts (`ReportFacts`)
Immutable, strongly typed Python dataclasses representing the domain truth:
- `InputFacts`: Geometric dimensions, material grades, environmental/seismic zones.
- `LoadFacts`: Dead loads, live loads, wind, seismic, thermal, and load combinations.
- `DesignCheckFacts`: Moment, shear, buckling, fatigue, deflection, stiffeners, and deck checks.
- `MaterialFacts`: Structural steel, concrete volume, rebar, studs, and barriers.

### Tier 5: Fact Invariant Validation (`validate_facts`)
Asserts domain rules across the extracted facts:
- Dimensions must be strictly positive ($D > 0$, $t_w > 0$, $b_f > 0$).
- Demand and capacity values must be finite non-negative numbers.
- Utilization ratios ($\text{UR} = \text{Demand} / \text{Capacity}$) must be mathematical invariants.
- Preserves explicit `None` representation for unavailable or optional components.

### Tier 6: Semantic AST Document (`ReportDocument`)
Builds an in-memory structural representation of the document hierarchy:
- `ReportDocument` $\to$ `Chapter` $\to$ `Section` $\to$ `DocumentComponent`.
- Pure abstract components: `Table`, `TableGroup`, `Column`, `Chart`, `Figure`, `Callout`, `Paragraph`.
- Completely decoupled from target output syntax (contains no LaTeX commands).

### Tier 7: Structural Manifest Engine (`manifest.py`)
Extracts a structural fingerprint (`ReportManifest`) of the AST:
- Captures chapter numbers, section headings, table captions, column headers, and row parameter labels.
- Compares semantic output against reference baselines to ensure zero silent omissions.

### Tier 8: Theme & Layout Binding (`ReportTheme`)
A single, immutable formatting source that provides:
- Page geometry (A4 dimensions, margins, footer reserves).
- Centralized color palette (Osdag Brand Green `#91B014`, Deep Slate `#1E293B`, Neutral Gray `#94A3B8`).
- Table styling policies (`TableStyle` with subtle internal rules and strong group boundaries).
- Chart dimensions, DPI, and typography parameters.

### Tier 9: LaTeX Renderer (`LatexRenderer`)
Transforms the semantic AST into production-grade LaTeX:
- Translates `TableGroup` into multi-row structures with clean `\cline{2-N}` rules.
- Manages multi-page `longtable` environments with repeated headers (`\endhead`).
- Isolates wide tables inside landscape environments (`\begin{osdaglandscape}`).
- Generates publication-ready Matplotlib chart graphics and embeds them via `\begin{figure}[H]`.

### Tier 10: PDF Preflight Safety Gate (`PDFPreflight`)
Automated post-compilation inspection using PyMuPDF (`fitz`):
- Checks every rendered page for **Footer Collision** (ensuring text does not invade the 25mm bottom reserve).
- Checks every rendered page for **Horizontal Margin Overflow** (ensuring table columns remain strictly within the 170mm printable width).
- Returns structured status (`PASS` / `WARN` / `FAIL`).

---

## 3. Core Data Models & Invariant Safety

### 3.1 Typed Values (`QuantityValue` & `CheckStatus`)

```python
@dataclass(frozen=True)
class QuantityValue:
    """Represents an engineering quantity with explicit physical unit."""
    value: float
    unit: str

    def __str__(self) -> str:
        return f"{self.value:g} {self.unit}"

class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    UNAVAILABLE = "N/A"
```

### 3.2 Semantic Document AST Components

```python
@dataclass
class Column:
    """Defines a table column with header text, width, and alignment."""
    header: str
    width: str = "L{3.0cm}"
    align: str = "l"

@dataclass
class TableGroup:
    """Represents a grouped entity (e.g. Girder G1) spanning multiple sub-rows."""
    label: str
    rows: List[List[Any]]
    splittable: bool = False

@dataclass
class Table:
    """A semantic table with captions, columns, and rows/groups."""
    caption: str
    columns: List[Column]
    rows: Optional[List[List[Any]]] = None
    groups: Optional[List[TableGroup]] = None
    layout: LayoutHints = field(default_factory=LayoutHints)
    label: str = ""
    note: str = ""

@dataclass
class Chart:
    """A semantic visualization component."""
    title: str
    chart_type: str  # "bar", "barh"
    data: Dict[str, Optional[float]]
    x_label: str = ""
    y_label: str = ""
    threshold_line: Optional[float] = None
    width_cm: Optional[float] = None
    height_cm: Optional[float] = None
    layout: LayoutHints = field(default_factory=LayoutHints)
```

---

## 4. Chapter-by-Chapter Architectural Breakdown

### 4.1 Executive Summary
- **Table 1 Architecture Transformation:**
  - *Legacy Issue:* Originally formatted horizontally across columns ($G_1, G_2, \dots, G_n$), which broke the page margins whenever girder count $> 5$.
  - *New Semantic Architecture:* Converted into a clean 5-column vertical table:
    $$\text{Girder } (G_i) \;\vert\; \text{Member ID} \;\vert\; \text{Section Designation} \;\vert\; \text{Governing Check} \;\vert\; \text{Utilization Ratio}$$
  - Fits comfortably within portrait margins for any girder count ($N = 3, 5, 9, 10, 20+$) and automatically splits across pages if needed.
- **Units & Accuracy:** Added explicit units (`m` for Girder Spacing, `mm` for Deck Thickness) and robust fallback resolution (`G{i}M1`).

### 4.2 Chapter 1: Project Information
- Extracts metadata fields (`project_name`, `project_location`, `designer`, `reviewer`, `client`).
- Maps all applicable Indian Road Congress (IRC) and Indian Standards (IS) design specifications (IRC 5, IRC 6, IRC 22, IRC 24, IRC 112, IS 800, IS 2062).

### 4.3 Chapter 2: Input Parameters & Geometry
- **Table 2.1 – 2.5 (Basic & Component Inputs):** Project location coordinates, seismic zone IV, basic wind speed ($47\text{ m/s}$), and design temperatures.
- **Table 2.2 (Skew Angle Limit Formatting):** Fixed raw string escaping so $0^\circ$ is formatted with code limits:
  $$0^\circ \; (\text{IRC 24 Cl. 504.8 limit: } \pm 15^\circ)$$
- **Table 2.4 (Traffic Lanes Heuristic):** Dynamically calculates estimated traffic lanes from carriageway width ($W / 3.5\text{m}$) when unpopulated by the solver.
- **Table 2.7 & 2.8 (Girder Geometry & Stiffener Preferences):** 6-column portrait table with automated cell wrapping (`p{2.6cm}`), ensuring longitudinal and bearing stiffener parameters do not exceed margins.
- **Table 2.9 & 2.10 (Cross Bracing & End Diaphragms):** Member IDs, bracing configurations (X-bracing, K-bracing), section sizes ($\text{IS } 100 \times 100 \times 10$), and spacing.

### 4.4 Chapter 3: Loads & Combinations
- **Table 3.1 – 3.7 (Individual Loads):** Self-weight, surfacing ($50\text{ mm}$ concrete), vehicle live loads (Class A, Class 70R), footway loading ($4.905\text{ kN/m}^2$), wind pressure ($940.6\text{ N/m}^2$), seismic coefficient ($A_h = 0.336$), and thermal loads.
- **Table 3.8 (Load Combinations):** Full tabulation of Ultimate Limit State (ULS-01 to ULS-08) and Serviceability Limit State (SLS-01 to SLS-07) partial safety factor equations.

### 4.5 Chapter 4: Analysis Results
- **Table 4.1 (Maximum Demands):** Bending moments, shear forces, and support reactions per load combination.
- **Grillage Diagrams:** Embedded 3D Bending Moment Envelope ($M_z$), Shear Force Envelope ($V_y$), and Vertical Deflection ($D_y$) grillage plots generated by `OSPGrillage`.

### 4.6 Chapter 5: Design Checks (30+ Structural Checks)
- **Elimination of Scientific Notation:** Replaced raw float formatting with formatted integer representations ($1,881,960\text{ cm}^4$ instead of `1.881958e+06`).
- **LaTeX Math Escaping:** Replaced plain-text expressions with AST `Math(...)` objects in Table 5.18 (*Cantilever Overhang Flexure*) and Table 5.19 (*Punching Shear*), eliminating raw TeX code spills like `\times`, `\leq`, `\mu_r`, `\min`, `\phi`, `A_g`, `r_{min}`.
- **Multi-Row Girder Grouping:** Implemented `TableGroup` across Tables 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12.
- **Wide Landscape Summary:** Tables 5.25, 5.26, 5.27, 5.28, 5.29, 5.30 are rendered in isolated `osdaglandscape` environments with 12 distinct metric columns.
- **Figure 5.1 (Utilization Ratio Chart):** Unified horizontal bar chart with Osdag Brand Green bars, clear code limit dashed line at $\text{UR} = 1.0$, and bold status text tags (`[PASS]` / `[FAIL]`).

### 4.7 Chapter 6: Drawings & CAD Visualizations
- **CAD Views Embedded:** 3D Superstructure Overview, Typical Cross-Section, Top Plan View, Plate Girder Details, and Cross Bracing/End Diaphragm connection layouts.
- **Figure 6.1 Sizing Constraint:** Restricted Figure 6.1 height to `10.5cm, keepaspectratio` so Section 6.1 heading and the 3D superstructure render together on the opening page without page-spill.
- **Pinned Footers:** Fixed landscape-to-portrait geometry resets so Chapter 6 footers remain pinned at the exact bottom margin.

### 4.8 Chapter 7: Material Take-off & Quantity Summary
- **Table 7.1 (Bill of Materials):** Comprehensive takeoff covering Structural Steel (Girders, Cross Bracing Top/Bottom/Diagonal, End Diaphragms), Concrete (M40 Deck), Rebar (Fe 500), Shear Studs, and Crash Barriers.
- **Formula Reconstruction AST (`_fmt_formula`):** Formats volume calculation expressions ($0.03870\text{ m}^2 \times 30.00\text{ m} = 1.16100\text{ m}^3$) cleanly without raw LaTeX artifacts.
- **Material Figures (Figures 7.1, 7.2, 7.3):**
  - **Figure 7.1:** Structural Steel Quantities (Girders: $45.57\text{ MT}$, Cross Bracing: $3.62\text{ MT}$, End Diaphragms: `N/A`).
  - **Figure 7.2:** Concrete Volume (Deck Slab: $90.00\text{ m}^3$).
  - **Figure 7.3:** Reinforcement Steel Quantity (Rebar: $10.80\text{ MT}$).

### 4.9 Chapter 8: Standards, Assumptions & Limitations
- Tabulates all design standards (IRC 5, 6, 22, 24, 112, SP 114; IS 800, 456, 1786, 1893, 2062).
- Details analysis assumptions (simply supported grillage, composite action, modular ratios, thickness reduction factor $\mu_r$).
- Explicitly documents software scope and version limitations (substructure, bearings, and splices designed in separate modules).

---

## 5. Visual System & Theme Architecture (ReportTheme)

### 5.1 Centralized Color Hierarchy
The reporting visual system is controlled entirely by `ColorPalette` in `theme.py`:

```python
@dataclass(frozen=True)
class ColorPalette:
    primary: str = "#91B014"        # Osdag Brand Green (Rules, Highlights, Bar Charts)
    primary_dark: str = "#5C720D"   # Deep Forest Accent
    secondary: str = "#1E293B"      # Deep Slate / Navy (Text, Table Borders)
    steel: str = "#91B014"          # Structural Steel Primary
    concrete: str = "#91B014"       # Concrete Volume Primary
    rebar: str = "#91B014"          # Reinforcement Steel Primary
    accent: str = "#0284C7"         # Technical Blue Accent
    error: str = "#DC2626"          # Code Failure Red (FAIL / Threshold)
    success: str = "#16A34A"        # Code Pass Green (PASS)
    warning: str = "#D97706"        # Code Warning Amber (WARN)
    muted: str = "#94A3B8"          # Neutral Slate Gray (N/A / Grid)
    grid: str = "#E2E8F0"           # Subtle Grid Line
    surface: str = "#FFFFFF"        # Chart Surface Background
```

### 5.2 Table Group Row Rules
To eliminate visual clutter while maintaining clear structural distinction, `TableStyle` defines two distinct rule policies:
1. `inner_group_rule = "subtle"`: Emits `\cline{2-N}` between parameter rows within the same girder group. Column 1 ($G_i$) remains unified in a clean multi-row cell without horizontal division.
2. `group_boundary_rule = "strong"`: Emits a full-width `\hline` across all columns between girder groups ($G_1 \to G_2 \to G_3$).

```
┌────┬────────────────────────────────────┬──────────────┐
│ G1 │ Depth, D (mm)                      │ 1670         │
│    ├────────────────────────────────────┼──────────────┤  ← \cline{2-3} (subtle inner rule)
│    │ Top Flange Width, bf (mm)          │ 510          │
│    ├────────────────────────────────────┼──────────────┤  ← \cline{2-3} (subtle inner rule)
│    │ Moment of Inertia, Iz (cm4)        │ 1,881,960    │
├────┴────────────────────────────────────┴──────────────┤  ← \hline (strong group boundary)
│ G2 │ Depth, D (mm)                      │ 1670         │
│    ├────────────────────────────────────┼──────────────┤  ← \cline{2-3} (subtle inner rule)
│    │ Top Flange Width, bf (mm)          │ 510          │
└────┴────────────────────────────────────┴──────────────┘
```

### 5.3 Unified Chart Palette & Automatic Figure Numbering
- **Uniform Brand Green:** All valid data bars across all charts (Figures 5.1, 7.1, 7.2, 7.3) render in the single official Osdag Brand Green (`#91B014`).
- **Semantic N/A Handling:** When a component is `None` (e.g. End Diaphragms in Fig 7.1), the bar is not drawn, and an explicit `"N/A"` text badge is placed in neutral slate gray (`#94A3B8`).
- **No Duplicate Image Titles:** Chart images contain no internal title strings. The LaTeX `\caption{\textbf{...}}` command provides the single, numbered figure caption.

---

## 6. Advanced LaTeX Rendering & Layout Engineering

### 6.1 Semantic Math Escaping
The renderer's `_escape()` method isolates inline math blocks ($ \dots $) before escaping special TeX characters:
1. Replaces inline math `$ ... $` with unique temporary tokens (`ZMATH{i}ZZ`).
2. Replaces unicode characters ($\ge, \le, \tau, \sigma, \Delta, \phi, \mu$) with placeholder tokens (`ZUNIQ{code}ZZ`).
3. Escapes standard text special characters (`&`, `%`, `_`, `#`, `{`, `}`).
4. Converts text inequality symbols (`>` and `<`) to math mode (`$>$`, `$<$`) to prevent TeX OT1 `¿` and `!` font substitution artifacts.
5. Restores LaTeX math definitions and preserved math blocks.

### 6.2 Multi-Page `longtable` Repeating Headers
Every multi-page table emits standard `longtable` header and footer regions:
- `\endfirsthead`: Emitted after the initial table header on Page 1.
- `\endhead`: Emitted after the repeated header on subsequent pages, appending `(continued)` to the table caption.
- `\endfoot`: Emitted for interim page bottom borders.
- `\endlastfoot`: Emitted for the final closing table border.

### 6.3 Landscape Flow Isolation (`osdaglandscape`)
Wide multi-column tables are enclosed in `\begin{osdaglandscape} ... \end{osdaglandscape}`:
- Issues explicit `\clearpage` before and after rotation to prevent portrait/landscape content mixing.
- Configures `\pagestyle{osdagfancy}` with `\setlength{\headwidth}{\textwidth}` so header rules and page numbers span the full 297mm landscape page.
- Employs `\raggedbottom` to prevent TeX vertical box stretching, keeping footers firmly anchored to the bottom margin.

---

## 7. Quality Assurance, Preflight & Verification Infrastructure

### 7.1 Preflight Binary Analysis (`PDFPreflight`)
`PDFPreflight` inspects the compiled PDF binary using PyMuPDF (`fitz`):
1. **Footer Collision Check:**
   - Scans text bounding boxes on every page.
   - Asserts that no body content enters the bottom 25mm footer reserve ($y_1 \le 771\text{ pt}$).
2. **Horizontal Margin Overflow Check:**
   - Evaluates text block horizontal boundaries ($x_1 \le \text{PageWidth} - 15\text{mm}$).
   - Detects over-wide tables or cell overflows before human review.
3. **Data Integrity Check:**
   - Validates that unavailable components produce advisory warnings rather than silent calculation crashes.

### 7.2 Structural Manifest Parity System (`manifest.py`)
- Extracts an AST structural manifest (`ReportManifest`) from the in-memory document.
- Parses legacy report output into a parallel structural manifest.
- Executes automated diff checks (`assert_manifest_parity`) verifying 100% parameter, check, and table parity.

### 7.3 Multi-Configuration Production Acceptance Suite
Every release is certified against the 4 canonical bridge configurations:

```
========================================================================================
STAGE 8 PRODUCTION ACCEPTANCE RESULTS
========================================================================================
  Config A (3 Girders)     | Pages: 44 | Footer Collision: PASS | Margin Overflow: PASS
  Config B (5 Girders)     | Pages: 51 | Footer Collision: PASS | Margin Overflow: PASS
  Config C (10 Girders)    | Pages: 69 | Footer Collision: PASS | Margin Overflow: PASS
  Config D (Partial Data)  | Pages: 44 | Footer Collision: PASS | Margin Overflow: PASS
========================================================================================
  Automated Test Suite     | 350 PASSED, 1 SKIPPED, 0 FAILURES (13.02s)
========================================================================================
```

---

## 8. Comprehensive Log of Bugs Resolved & Refinements Made

| Issue / Defect | Root Cause in Legacy Pipeline | Semantic Engine Resolution |
|---|---|---|
| **Table 1 Margin Overflow on 9+ Girders** | Horizontal column layout ($G_1 \dots G_n$) exceeded A4 page width. | Re-architected Table 1 into a 5-column vertical table ($G_i$ per row). |
| **Scientific Notation in Section Properties** | Unformatted Python float string conversion (`1.881958e+06`). | Implemented `_fmt_qv()` with comma-separated integer formatting ($1,881,960$). |
| **Raw LaTeX Code Spills in Tables 5.18/5.19** | String math was escaped by text cleaner, exposing `\times`, `\leq`, `\phi`. | Wrapped formulas in AST `Math(...)` objects with protected math preservation. |
| **Upside-Down Question Mark (`¿`) in Checks** | Text-mode `>` and `<` evaluated in TeX OT1 font encoding. | Automatically transformed text inequality operators to `$>$` and `$<$`. |
| **Floating/High Footers on Landscape Pages** | Default TeX vertical justification (`\flushbottom`) stretched page content. | Added `\raggedbottom` and explicit `\setlength{\headwidth}{\textwidth}`. |
| **Figure 6.1 Spilling to Next Page** | Unconstrained 3D CAD image height pushed heading across page break. | Constrained Figure 6.1 height to `10.5cm, keepaspectratio`. |
| **Rainbow Bar Graph Colors** | Unset Matplotlib default color cycle in standalone plotting functions. | Unified all material and UR bar charts to official Osdag Green (`#91B014`). |
| **`None` Coercion to `0.0` in Charts** | Missing End Diaphragm data plotted as a zero-height bar. | Added explicit `"N/A"` neutral badge; no zero-height bar drawn. |
| **Missing Sequential Figure Numbers** | Unstarred `\caption*{...}` prevented LaTeX figure counter incrementation. | Replaced with standard `\caption{\textbf{...}}` producing Figures 5.1, 7.1, 7.2, 7.3. |
| **Table Visual Clutter in Girder Groups** | Missing horizontal rules between internal rows of grouped tables. | Added `\cline{2-N}` inner rules with full-width `\hline` group boundaries. |

---

## 9. Developer Extension Guide

To add a new engineering check or table to OsdagBridge, follow this strict protocol:

```
[1] Define Fact Dataclass
    └─ src/osdagbridge/core/report_engine/facts/my_check.py
       └─ Define @dataclass(frozen=True) class MyCheckFacts

[2] Register Provenance & Extraction
    └─ src/osdagbridge/core/report_engine/facts/design_checks.py
       └─ tracker.record("my_output_key", raw_val, unit="kN")

[3] Add Fact Validation Invariant
    └─ src/osdagbridge/core/report_engine/validation.py
       └─ Assert MyCheckFacts.demand >= 0 and capacity > 0

[4] Construct Semantic Component
    └─ src/osdagbridge/core/report_engine/chapters/ch5_document.py
       └─ Return Table(caption="...", columns=[...], groups=[...])

[5] Assert Contract & Manifest Parity
    └─ tests/contract/test_report_contract.py
       └─ Verify AST component existence and structural integrity

[6] Execute Full Verification
    └─ pytest tests/ -v
    └─ python scratch/run_stage8_acceptance.py
```

---

*End of Comprehensive Architectural & Implementation Reference.*
