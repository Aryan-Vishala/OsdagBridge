# OsdagBridge Semantic Report Engine

Production-grade semantic report generation pipeline for bridge structural design calculation reports.

---

## 1. Architectural Overview

The reporting engine transforms raw numerical analysis outputs into rigorous, verified, publication-quality PDF engineering calculation reports via a pure AST pipeline:

```
[Raw Analysis & UI Payload]
             ↓
    [ProvenanceTracker]          ← Records exact key origin, raw values, and unit conversions
             ↓
       [ReportFacts]              ← Frozen typed dataclasses (Inputs, Loads, Checks, Materials)
             ↓
     [validate_facts]            ← Rejects NaN/Inf, degenerate geometries, unit mismatches
             ↓
  [build_report_document]        ← Assembles in-memory Abstract Syntax Tree (AST)
             ↓
     [StructuralManifest]        ← Asserts zero parity regressions vs legacy baseline
             ↓
      [LatexRenderer]            ← Converts AST to production LaTeX with LongTable page breaks
             ↓
      [PDFPreflight]             ← Checks compiled PDF for orphan headers, overflows, blank pages
             ↓
       [Final PDF]
```

---

## 2. Key Modules & Responsibilities

| Module | Location | Purpose |
|---|---|---|
| **Facts** | `src/osdagbridge/core/report_engine/facts/` | Domain dataclasses representing engineering truth (inputs, loads, girder/deck checks, material takeoff). |
| **Provenance** | `src/osdagbridge/core/report_engine/provenance.py` | Lineage tracking for every single value (source key, raw value, unit conversion transform). |
| **Validation** | `src/osdagbridge/core/report_engine/validation.py` | Runtime invariant checks (`validate_payload`, `validate_facts`) that fail fast on degenerate data. |
| **AST Document** | `src/osdagbridge/core/report_engine/document.py` | In-memory structural representation (`ReportDocument`, `Chapter`, `Section`, `Table`, `TableGroup`, `Figure`). |
| **Builder** | `src/osdagbridge/core/report_engine/document_builder.py` | Maps `ReportFacts` into the structured `ReportDocument` AST. |
| **Manifest** | `src/osdagbridge/core/report_engine/manifest.py` | Structural parity extractor and regression tripwire (`ParityReport.assert_no_regressions()`). |
| **Renderer** | `src/osdagbridge/core/report_engine/renderer.py` | LaTeX code emitter handling multi-page tables, landscape sections, group borders, and math. |
| **Preflight** | `src/osdagbridge/core/report_engine/preflight.py` | Post-compilation verification checking page count, geometry, and rendering health. |

---

## 3. Developer Guide: Adding a New Design Check or Table

When introducing a new design check or calculation table to OsdagBridge reports, follow this standard 5-step process:

### Step 1: Define the Typed Fact in `facts/`
Add a frozen dataclass in `src/osdagbridge/core/report_engine/facts/` to hold your check data:
```python
@dataclass(frozen=True)
class BearingCheckData:
    pad_type: str
    horizontal_capacity: Optional[QuantityValue]
    vertical_capacity: Optional[QuantityValue]
    utilization_ratio: Optional[float]
    status: CheckStatus
```

### Step 2: Extract Facts with Provenance in `facts/design_checks.py`
Extract the raw dictionary values and register them with `tracker`:
```python
if tracker:
    tracker.record(
        fact_name="bearing.vertical_capacity",
        source=ValueSource.OUTPUT_DICT,
        source_key="bearing.design.capacity_kn",
        source_value=raw_val,
        extracted_value=float(raw_val),
        target_unit="kN",
        transform="none"
    )
```

### Step 3: Build the Semantic AST Component in `chapters/`
In `src/osdagbridge/core/report_engine/chapters/`, construct a typed `Table` component:
```python
table = Table(
    caption="Bearing Design --- Capacity Checks",
    columns=[
        Column("Parameter", width="6.0cm"),
        Column("Demand", width="3.5cm", alignment="r"),
        Column("Capacity", width="3.5cm", alignment="r"),
        Column("Status", width="2.5cm", alignment="c"),
    ],
    rows=[
        ["Vertical Load", pad_fact.vert_demand, pad_fact.vertical_capacity, pad_fact.status.value],
    ],
    note="Designed according to IRC 83 (Part II).",
)
```

### Step 4: Add Contract Tests in `tests/contract/test_report_contract.py`
Verify that the table appears in the AST with all expected row labels across bridge configurations:
```python
def test_bearing_table_contract(self, doc_5_girder_full: ReportDocument):
    ch5 = find_chapter(doc_5_girder_full, 5)
    tbl = find_table(ch5, "Bearing Design --- Capacity Checks")
    assert_table_has_rows(tbl, ["Vertical Load", "IRC 83"])
```

### Step 5: Update the Structural Manifest in `manifest.py`
If the new table is intentional or configuration-dependent, register it in `KNOWN_INTENTIONAL_TRANSFORMATIONS` or manifest extractors so that parity checks remain green.

---

## 4. Running the Contract & Parity Test Suite

Execute the fast semantic contract test suite ($<1$ second, no LaTeX required):
```bash
pytest tests/contract/ -v
```

Run the entire OsdagBridge test suite:
```bash
pytest tests/ -v
```
