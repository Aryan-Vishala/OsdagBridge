# OsdagBridge Report Generator Refactoring

## Project
OsdagBridge — LaTeX/PyLaTeX Report Generator Refactoring & Enhancements

---

## Submission Deliverables

### 1. Original Report
[`Report_Before.pdf`](Report_Before.pdf)  
The original 10-girder OsdagBridge report generated before the report-engine refactoring, illustrating legacy table overflow and layout issues.

### 2. Enhanced Report
[`Report_After.pdf`](Report_After.pdf)  
The final production report generated using the refactored semantic report engine with vertical Table 1, repeated headers, and unified styling.

### 3. Technical Changes Report
[`Technical_Changes_Report.pdf`](Technical_Changes_Report.pdf)  
Detailed technical report explaining:
- Python and LaTeX/PyLaTeX modifications
- Files changed and created under the report generator
- Centralized formatting/theme architecture (`theme.py`)
- Architectural and styling rationale
- Visual enhancements and polish

---

## Scope of Work Completed

1. **Repeated headers across multi-page tables**: 4-tier `longtable` protocol with `\endhead` and `(continued)` captions.
2. **Footer/layout and vertical-spacing improvements**: Dynamic `\Needspace` clearance buffers and PyMuPDF PDF preflight verification.
3. **Load and geometry table refactoring**: Separated vehicle live loads, footway, wind, seismic, and thermal tables with units.
4. **Utilization-ratio visualization**: Figure 5.1 summary chart with red dashed $\text{UR}=1.0$ code threshold line.
5. **Material quantity visualizations**: Figures 7.1–7.3 for Steel, Concrete, and Rebar with sequential numbering.
6. **Centralized formatting and styling system**: Dedicated `theme.py` acting as single source of truth.

---

## Additional Improvements

- Semantic report-document architecture (10-tier pipeline)
- Strongly-typed immutable engineering facts
- Data provenance and unit-conversion tracking
- Input payload and domain fact validation
- Structural regression manifest parity verification
- Multi-configuration acceptance testing (3, 5, 10-girder and partial models)
- PDF preflight layout verification
- Improved mathematical notation and AST Math token isolation
- Subtle `\cline{2-N}` grouped-table separators
- Automatic figure numbering and Osdag Brand Green visualizations

---

## Verification

- **Automated Test Suite**: **350 passed, 1 skipped, 0 failures** (Execution time: ~12s).
- **Physical Acceptance**: Physically verified across 3-, 5-, and 10-girder configurations and a partial-data model (0 footer collisions, 0 margin overflows).

---

## GitHub Repository Information

- **Repository:** [https://github.com/Aryan-Vishala/OsdagBridge](https://github.com/Aryan-Vishala/OsdagBridge)
- **Final Branch:** `report-generator-refactor`
- **Final Release Tag:** `report-engine-production-accepted`
- **Collaborator:** `Nidhikhare12`
