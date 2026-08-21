# OsdagBridge Report Generator — Technical Changes & Architecture Report

**Document Title:** Technical Architecture, Modifications & Visual Engineering Report  
**Project:** OsdagBridge (FOSSEE / Indian Institute of Technology Bombay)  
**Author / Contributor:** Aryan Vishala \quad $|$ \quad **Reviewer / Collaborator:** Nidhikhare12  
**Status:** **FINAL VERIFIED BASELINE**  
**Version / Tag:** `report-engine-production-accepted`  
**GitHub Repository:** [https://github.com/Aryan-Vishala/OsdagBridge.git](https://github.com/Aryan-Vishala/OsdagBridge.git)  

---

## 1. Executive Summary

This report documents the technical architecture, code refactoring, and \LaTeX\ visual rendering enhancements implemented on the **OsdagBridge Report Generator**. 

The legacy reporting subsystem previously assembled PDF reports via procedural string-concatenation scripts (`chap1.py` through `chap8.py`), tightly coupling calculation outputs with raw \LaTeX\ formatting. This approach caused margin overflows on multi-girder bridge configurations ($>5$ girders), footer overlap issues, unformatted math strings, and scattered styling parameters.

The subsystem has been re-architected into a **10-Tier Semantic Report Engine**. The architecture decouples **Engineering Domain Facts**, **Document Abstract Syntax Tree (AST)**, **Centralized Styling (`theme.py`)**, and **LaTeX Rendering (`renderer.py`)**, backed by automated **PDF Preflight Layout Inspection** and a **350-test automated verification suite**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ARCHITECTURE RULE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Engineering meaning belongs in Facts.                                    │
│  • Report structure belongs in Document AST.                                │
│  • Visual policy belongs in Theme/Layout.                                   │
│  • LaTeX generation belongs in Renderer.                                    │
│  • Final PDF geometry belongs in Preflight.                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 10-Tier Semantic Architecture Pipeline

| Tier | Component | Core Responsibility | Why Introduced (Rationale) |
|:---:|---|---|---|
| **1** | **Raw Payload** | Captures solver results, grillage data, and inputs. | Decouples raw solver data structures from document logic. |
| **2** | **Payload Validation** | Fails fast on invalid span $\le 0$, girders $\le 1$, or missing loads. | Prevents silent crashes on malformed models. |
| **3** | **Provenance Tracking** | Records source dictionary keys, raw values, and unit conversions. | Provides end-to-end data lineage; prevents unit errors. |
| **4** | **ReportFacts (Domain Data)** | Immutable, strongly-typed Python domain dataclasses. | Eliminates data mutation; preserves $\text{None} \ne 0.0$. |
| **5** | **Fact Validation** | Asserts positive dimensions, finite demands, non-negative capacity. | Enforces domain invariants before AST building. |
| **6** | **ReportDocument AST** | In-memory AST (`Chapter`, `Section`, `Table`, `TableGroup`, `Chart`). | Completely separates content from \LaTeX\ markup. |
| **7** | **Structural Manifest** | Computes AST fingerprints and asserts structural parity. | Tripwire preventing accidental check omissions. |
| **8** | **ReportTheme** | Single source of truth for page geometry, colors, table styles. | Eliminates scattered styling; instant global updates. |
| **9** | **LatexRenderer** | Emits `longtable` headers, `\cline` rules, and landscape flow. | Emits clean, robust \LaTeX\ without ad-hoc strings. |
| **10** | **PDFPreflight Gate** | PyMuPDF binary scanner checking footer clearance and margins. | Catches physical page overflows post-compilation. |

---

## 3. Scope of Work & Engineering Enhancements

| Category / Requirement | Scope Item | Status | Key Technical Delivery |
|---|---|:---:|---|
| **Core Requirement 1** | Repeated Table Headers | **Completed** | 4-tier `longtable` protocol (`\endfirsthead`, `\endhead` with `(continued)`). |
| **Core Requirement 2** | Layout & Footer Overlap Fixes | **Completed** | Dynamic `\Needspace` clearance buffers + PyMuPDF automated footer check. |
| **Core Requirement 3** | Load & Geometry Refactoring | **Completed** | Separated vehicle live loads, footway, wind, seismic, and thermal tables. |
| **Core Requirement 4** | Utilization Ratio Visualizations | **Completed** | **Figure 5.1** summary chart with $\text{UR}=1.0$ red dashed code threshold line. |
| **Core Requirement 5** | Material Take-off Bar Charts | **Completed** | **Figures 7.1, 7.2, 7.3** for Steel, Concrete, and Rebar with sequential numbering. |
| **Core Requirement 6** | Centralized Theme System | **Completed** | Dedicated `theme.py` acting as single source of truth for all layout/color rules. |
| **Additional Enhancement** | Multi-Girder Scalability | **Enhanced** | Verticalized Table 1 (5 columns), scaling across tested 3, 5, 9, 10-girder models. |
| **Additional Enhancement** | Grouped Table Aesthetics | **Enhanced** | Subtle `\cline{2-N}` inner parameter dividers with full `\hline` group boundaries. |
| **Additional Enhancement** | \LaTeX\ Math AST Protection | **Enhanced** | AST `Math(...)` token isolation eliminating `¿` font artifacts and raw \TeX\ leaks. |
| **Additional Enhancement** | Preflight Safety Tripwires | **Enhanced** | Post-compilation automated physical PDF margin and footer collision detection. |

---

## 4. Authoritative File Modification & Addition Matrix

| File Path | Status | Primary Purpose & Responsibility |
|---|:---:|---|
| `src/osdagbridge/core/report_engine/theme.py` | **NEW** | Centralized styling configuration (`PageGeometry`, `TypographyStyle`, `ColorPalette`, `TableStyle`, `ChartStyle`). |
| `src/osdagbridge/core/report_engine/document.py` | **NEW** | Intermediate AST definitions (`ReportDocument`, `Chapter`, `Section`, `Table`, `TableGroup`, `Column`, `Chart`). |
| `src/osdagbridge/core/report_engine/document_builder.py` | **NEW** | Constructs complete `ReportDocument` AST from typed `ReportFacts`. |
| `src/osdagbridge/core/report_engine/renderer.py` | **NEW** | Production \LaTeX\ rendering engine, math escaping, `longtable` management, and landscape section flow. |
| `src/osdagbridge/core/report_engine/layout.py` | **NEW** | Layout hint definitions, page break triggers, and `\Needspace` clearance buffers. |
| `src/osdagbridge/core/report_engine/chart_generators.py` | **NEW** | Matplotlib chart generation service bound exclusively to `ReportTheme` colors and typography. |
| `src/osdagbridge/core/report_engine/preflight.py` | **NEW** | Automated PyMuPDF (`fitz`) binary PDF inspector for footer clearance and horizontal margin verification. |
| `src/osdagbridge/core/report_engine/manifest.py` | **NEW** | Structural manifest extraction and legacy vs.\ semantic parity verification engine. |
| `src/osdagbridge/core/report_engine/facts/` | **NEW** | Typed domain fact models (`inputs.py`, `loads.py`, `design_checks.py`, `material_takeoff.py`). |
| `src/osdagbridge/core/report_engine/chapters/` | **NEW** | Semantic chapter AST builders (`ch2_document.py`, `ch3_document.py`, `ch5_document.py`, `ch7_document.py`). |
| `src/osdagbridge/core/report_engine/validation.py` | **NEW** | Input payload and domain fact invariant validators. |
| `src/osdagbridge/core/report_engine/provenance.py` | **NEW** | `ProvenanceTracker` recording raw dictionary origins and registered unit transformations. |
| `src/osdagbridge/core/reports/report_generator.py` | **MODIFIED** | Main orchestrator; integrated semantic engine, cleaned running headers, and linked preflight checks. |
| `src/osdagbridge/core/reports/executive_summary.py` | **MODIFIED** | Re-architected Table 1 into a vertical 5-column structure (`Girder | Member ID | Section | Check | UR`). |
| `src/osdagbridge/core/reports/chap6.py` | **MODIFIED** | Constrained Figure 6.1 height to `10.5cm, keepaspectratio` to keep CAD view on opening page. |

---

## 5. Centralized Theme Architecture (`theme.py`)

The centralized formatting configuration module (`theme.py`) serves as the **single source of truth** for all visual properties:

```
ReportTheme (Immutable Single Source of Truth)
├── page: PageGeometry          → A4 dimensions, 20mm margins, 25mm footer reserve
├── typography: TypographyStyle  → 11pt Computer Modern body, 14pt headings, bold captions
├── colors: ColorPalette         → Osdag Brand Green (#91B014), Deep Slate Navy (#1E293B), Neutral Gray (#94A3B8)
├── table_styles: TableStyle     → 6pt padding, inner_group_rule="subtle" (\cline), boundary_rule="strong" (\hline)
└── charts: ChartStyle           → 14.5cm x 5.5cm dimensions, 300 DPI, sans-serif typography
```

---

## 6. Key Technical Changes: Before vs. After Comparison

| Report Element | Legacy Implementation (Before) | Semantic Report Engine (After) |
|---|---|---|
| **Executive Summary Table 1** | Horizontal columns ($G_1 \dots G_{10}$) causing right-margin overflow. | Vertical 5-column table (`Girder | Member | Section | Check | UR`), perfectly scalable. |
| **Multi-Page Tables** | Headers omitted on continuation pages; data disconnected across breaks. | Automatic `\endhead` repeated headers with `(continued)` captions on all pages. |
| **Grouped Girder Tables** | No internal dividing lines between parameter rows, resulting in cluttered blocks. | Subtle `\cline{2-N}` internal rules with full-width `\hline` group boundaries. |
| **Charts & Visualizations** | Default Matplotlib rainbow palette (blue, orange, teal); missing figure numbers. | Unified Osdag Brand Green (`#91B014`), explicit `N/A` badges, and auto figure numbers. |
| **LaTeX Math Formatting** | Raw string escaping exposed unformatted code (`\times`, `\leq`, `\phi`) and `¿` artifacts. | Tokenized math isolation with AST `Math(...)` objects preserving mathematical typography. |
| **Landscape Summary Flow** | Default vertical stretching caused portrait page footers to float mid-page. | Isolated `osdaglandscape` environments with `\raggedbottom` and full-width header rules. |
| **Quality Verification** | Manual visual inspection of compiled PDFs. | Automated PyMuPDF `PDFPreflight` checking bounding boxes for margin/footer collisions. |

---

## 7. Verification & Production Acceptance Suite

### 7.1 Automated Test Locations & Coverage

| Verification Area | Primary Test File Location | Scope Verified | Status |
|---|---|---|:---:|
| **Content Contract** | `tests/contract/test_report_contract.py` | 11 structural contract invariants | **PASS** |
| **Structural Manifest** | `tests/contract/test_structural_manifest.py` | AST manifest tree parity (0 regressions) | **PASS** |
| **Data Provenance** | `tests/contract/test_fact_provenance.py` | Lineage and unit conversion integrity | **PASS** |
| **Validation & Invariants** | `tests/contract/test_payload_facts_validation.py` | Payload/fact domain bounds & finite values | **PASS** |
| **Acceptance Matrix** | `tests/contract/test_acceptance_matrix.py` | Multi-configuration AST document builds | **PASS** |
| **Production PDF Preflight** | `scratch/run_stage8_acceptance.py` | Full `pdflatex` compilation & PyMuPDF layout checks | **PASS** |

### 7.2 Physical Multi-Configuration Acceptance Results

| Configuration Matrix | Girder Count | Physical Page Count | Footer Collision Check | Margin Overflow Check | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| **Configuration A** | 3 Girders | 44 Pages | **PASS** ($y_1 \le 771\text{ pt}$) | **PASS** ($x_1 \le 580\text{ pt}$) | **PASS** |
| **Configuration B** | 5 Girders | 51 Pages | **PASS** ($y_1 \le 771\text{ pt}$) | **PASS** ($x_1 \le 580\text{ pt}$) | **PASS** |
| **Configuration C** | 10 Girders | 69 Pages | **PASS** ($y_1 \le 771\text{ pt}$) | **PASS** ($x_1 \le 580\text{ pt}$) | **PASS** |
| **Configuration D (Partial)** | 4 Girders | 44 Pages | **PASS** ($y_1 \le 771\text{ pt}$) | **PASS** ($x_1 \le 580\text{ pt}$) | **PASS** |
| **10-Girder Submission Report** | 10 Girders | 82 Pages | **PASS** ($y_1 \le 771\text{ pt}$) | **PASS** ($x_1 \le 580\text{ pt}$) | **PASS** |

**Live Automated Test Suite Status:** **350 PASSED, 1 SKIPPED, 0 FAILURES** (Execution time: 11.18s).

---

## 8. Known Limitations & Non-Goals

1. **Solver Boundary:** The Semantic Report Engine formats, models, and validates data produced by OsdagBridge; it does not replace the underlying finite element/grillage analysis solver.
2. **Preflight Scope:** `PDFPreflight` verifies document geometry, structural integrity, and page layout bounds; it is not an independent mathematical re-solver of the structural design calculations.
3. **Compilation Backend:** The engine generates standardized \LaTeX\ and utilizes `pdflatex` as the production compilation backend.
4. **Legacy Compatibility:** The semantic engine is the active production report-generation path (`REPORT_ENGINE_ENABLED = True`); legacy `chap*.py` builders are retained for manifest parity regression testing and fallback.
5. **Optional Components:** Figures and sections remain configuration-dependent based on user UI selections.

---

## 9. Submission Deliverables

```
OsdagBridge_Report_Engine_Submission/
├── Report_Before.pdf            # 10-Girder baseline (81 pages) showing legacy table overflow & formatting issues
├── Report_After.pdf             # 10-Girder production report (82 pages) with vertical Table 1 & brand styling
├── Technical_Changes_Report.pdf # Standalone compiled technical architecture report (3 pages)
└── README.md                    # Submission manifest, repository link & test summary
```

---

## 10. Conclusion

The OsdagBridge Semantic Report Engine has completed the defined production acceptance and regression verification process and is frozen at Git tag **`report-engine-production-accepted`**. The verified system is ready for submission and continued maintenance under the documented architecture.

---
*Report prepared for FOSSEE / Indian Institute of Technology Bombay.*
