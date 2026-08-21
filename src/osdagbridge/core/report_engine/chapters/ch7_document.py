from __future__ import annotations

from osdagbridge.core.report_engine.document import (
    Chapter, Column, Chart, Paragraph, RawLatex, Section, Table
)
from osdagbridge.core.report_engine.facts import (
    MaterialFacts, TakeoffItem, QuantityValue, ReportFacts
)


def _fmt_qv(qv: QuantityValue | None, prec: int = 2) -> str:
    """Format a QuantityValue explicitly without units (units are in header)."""
    if qv is None:
        return "---"
    return f"{qv.value:.{prec}f}"


def _fmt_formula(components: tuple[QuantityValue, ...] | None, unit_volume: QuantityValue | None) -> str:
    """Reconstructs a formula string from semantic components."""
    if not components:
        return "N.A."
    
    parts = []
    for comp in components:
        unit_str = comp.unit.replace("²", "^2").replace("³", "^3")
        if comp.unit == "m²":
            parts.append(f"{comp.value:.5f} {unit_str}")
        elif comp.unit == "m":
            parts.append(f"{comp.value:.2f} {unit_str}")
        elif comp.unit == "mm":
            parts.append(f"{comp.value:.2f} {unit_str}")
        elif comp.unit == "No.":
            parts.append(f"{int(comp.value)}")
        else:
            parts.append(f"{comp.value:.2f} {unit_str}")
    
    if not parts:
        return "N.A."

    formula_str = " x ".join(parts)
    if unit_volume is not None:
        unit_vol_str = unit_volume.unit.replace("²", "^2").replace("³", "^3")
        formula_str += f" = {unit_volume.value:.5f} {unit_vol_str}"
        
    return formula_str


def _build_row(sn: str, item: TakeoffItem | None, label_fallback: str) -> list[str]:
    if item is None:
        return [
            sn,
            label_fallback,
            "---",
            "---",
            "---",
            "---",
            "---"
        ]
        
    formula_str = _fmt_formula(item.formula_components, item.unit_volume)
    
    unit_wt_prec = 2
    tot_wt_prec = 2
    if "Cross Bracing" in item.item_description:
        unit_wt_prec = 4
    elif "Stud" in item.item_description:
        unit_wt_prec = 6
        tot_wt_prec = 3
    
    return [
        sn,
        item.item_description,
        formula_str if formula_str != "N.A." else "---",
        str(item.quantity) if item.quantity is not None else "---",
        _fmt_qv(item.total_volume),
        _fmt_qv(item.unit_weight, prec=unit_wt_prec),
        _fmt_qv(item.total_weight, prec=tot_wt_prec)
    ]


def _build_table_7_1(facts: MaterialFacts) -> Table:
    """Builds Table 7.1 (Bill of Materials)"""
    columns = [
        Column("S.N.", width="C{1.0cm}"),
        Column("Item Description", width="L{3.8cm}"),
        Column("Volume", width="C{2.6cm}"),
        Column("Quantity", width="C{1.8cm}"),
        Column("Total Volume", width="C{1.8cm}"),
        Column("Weight (MT)", width="C{1.8cm}"),
        Column("Total Weight (MT)", width="C{1.8cm}"),
    ]
    
    rows = [
        _build_row("1", facts.structural_steel.girders if facts.structural_steel else None, "Structural Steel (IS 2062) for Girders"),
        _build_row("2(a)", facts.structural_steel.cross_bracing_top if facts.structural_steel else None, "Cross Bracing - Top Chord"),
        _build_row("2(b)", facts.structural_steel.cross_bracing_bot if facts.structural_steel else None, "Cross Bracing - Bottom Chord"),
        _build_row("2(c)", facts.structural_steel.cross_bracing_diag if facts.structural_steel else None, "Cross Bracing - Diagonal Chord"),
        _build_row("2(d)", facts.structural_steel.end_diaphragms if facts.structural_steel else None, "End Diaphragm"),
        _build_row("3", facts.concrete_volume, "Concrete (M40) for Deck Slab"),
        _build_row("4", facts.reinforcement_steel, "Reinforcement Steel (Fe 500)"),
        _build_row("5", facts.shear_studs, "Shear Stud Connectors"),
        _build_row("6", facts.crash_barrier, "Crash Barrier")
    ]
    
    return Table(
        caption="Bill of Materials (Steel, Concrete, and Reinforcement Quantities)",
        columns=columns,
        rows=rows,
        label="tab:bill_of_materials"
    )


def _build_charts(facts: MaterialFacts) -> list[Chart]:
    """Builds the 3 material charts with professional aesthetics."""
    charts = []

    # 1. Structural Steel Quantities (MT)
    steel = facts.structural_steel
    girders_wt = steel.girders.total_weight.value if steel and steel.girders and steel.girders.total_weight else None
    
    cb_wts = [
        getattr(getattr(steel, attr), "total_weight").value if getattr(steel, attr) and getattr(getattr(steel, attr), "total_weight") else None
        for attr in ["cross_bracing_top", "cross_bracing_bot", "cross_bracing_diag"]
    ] if steel else [None]
    if all(w is None for w in cb_wts):
        cb_wt = None
    else:
        cb_wt = sum(w for w in cb_wts if w is not None)

    ed_wt = steel.end_diaphragms.total_weight.value if steel and steel.end_diaphragms and steel.end_diaphragms.total_weight else None

    chart_steel = Chart(
        title="Structural Steel Quantities",
        chart_type="bar",
        data={
            "Girders": girders_wt,
            "Cross Bracing": cb_wt,
            "End Diaphragms": ed_wt
        },
        y_label="Weight (MT)",
        width_cm=14.5,
        height_cm=5.5,
    )
    charts.append(chart_steel)

    # 2. Concrete Volume (m³)
    concrete_vol = facts.concrete_volume.total_volume.value if facts.concrete_volume and facts.concrete_volume.total_volume else None
    chart_concrete = Chart(
        title="Concrete Volume",
        chart_type="bar",
        data={
            "Concrete Deck Slab": concrete_vol
        },
        y_label="Volume (m³)",
        width_cm=14.5,
        height_cm=5.5,
    )
    charts.append(chart_concrete)

    # 3. Reinforcement Steel Quantity (MT)
    rebar_wt = facts.reinforcement_steel.total_weight.value if facts.reinforcement_steel and facts.reinforcement_steel.total_weight else None
    chart_rebar = Chart(
        title="Reinforcement Steel Quantity",
        chart_type="bar",
        data={
            "Reinforcement Steel": rebar_wt
        },
        y_label="Weight (MT)",
        width_cm=14.5,
        height_cm=5.5,
    )
    charts.append(chart_rebar)

    return charts


def build_chapter_7(facts: ReportFacts) -> Chapter:
    """Build Chapter 7: Material Take-off & Quantity Summary."""
    if hasattr(facts, "material_facts") and facts.material_facts:
        mat_facts = facts.material_facts
    else:
        from osdagbridge.core.report_engine.facts.material_takeoff import build_material_facts
        mat_facts = build_material_facts(facts.raw_input_dict or {}, facts.raw_output_dict or {})

    components = [
        _build_table_7_1(mat_facts),
        Paragraph("The charts below summarize the distribution of structural steel components and key construction material quantities required for the bridge superstructure."),
        *_build_charts(mat_facts)
    ]
    
    return Chapter(
        number=7,
        title="Material Take-off \\& Quantity Summary",
        sections=[Section(title="", level=2, components=components)],
    )
