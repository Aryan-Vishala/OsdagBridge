"""
Stage 5: Type Safety, Payload & Facts Validation Engine
======================================================

Provides runtime validation and invariant checking for:
1. Raw engine payloads (inputs/outputs dicts) before fact extraction.
2. Semantic ReportFacts before document/AST generation.

Catches missing required engineering inputs, degenerate dimensions, NaN/Inf values,
inconsistent units, and corrupt analysis outputs before LaTeX compilation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from osdagbridge.core.report_engine.facts import (
    CheckStatus,
    QuantityValue,
    ReportFacts,
)
from osdagbridge.core.report_engine.provenance import (
    ProvenanceTracker,
    ProvenanceValidationIssue,
)
from osdagbridge.core.utils import common as c


@dataclass
class ValidationIssue:
    severity: str  # 'ERROR' | 'WARNING'
    field_name: str
    message: str
    actual_value: Any = None


@dataclass
class ValidationReport:
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "ERROR"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "WARNING"]

    def assert_valid(self):
        """Raise ValueError if there are any ERROR level issues."""
        errs = self.errors
        if errs:
            msg = "\n".join(f"[{e.severity}] {e.field_name}: {e.message}" for e in errs)
            raise ValueError(f"Report payload validation failed with {len(errs)} error(s):\n{msg}")


# =============================================================================
# 1. Payload Validation (Raw Inputs & Outputs)
# =============================================================================

def validate_payload(
    raw_inputs: Dict[str, Any],
    raw_outputs: Optional[Dict[str, Any]] = None,
) -> ValidationReport:
    """Validate raw payload inputs and outputs before facts building."""
    issues: List[ValidationIssue] = []

    # Check Span
    span_val = raw_inputs.get(c.KEY_SPAN)
    if span_val is None or span_val == "":
        issues.append(ValidationIssue("ERROR", "geometry.span", "Bridge span is missing"))
    else:
        try:
            span = float(span_val)
            if span <= 0:
                issues.append(ValidationIssue("ERROR", "geometry.span", f"Bridge span must be positive, got {span}", span))
            elif span > 500:
                issues.append(ValidationIssue("WARNING", "geometry.span", f"Bridge span is unusually large ({span} m)", span))
        except (ValueError, TypeError):
            issues.append(ValidationIssue("ERROR", "geometry.span", f"Invalid span value: {span_val}", span_val))

    # Check Number of Girders
    ng_val = raw_inputs.get(c.KEY_TS_NO_OF_GIRDERS)
    if ng_val is None or ng_val == "":
        issues.append(ValidationIssue("ERROR", "typical_section.no_of_girders", "Number of girders is missing"))
    else:
        try:
            ng = int(ng_val)
            if ng < 1:
                issues.append(ValidationIssue("ERROR", "typical_section.no_of_girders", f"Number of girders must be >= 1, got {ng}", ng))
            elif ng > 50:
                issues.append(ValidationIssue("WARNING", "typical_section.no_of_girders", f"Number of girders is unusually large ({ng})", ng))
        except (ValueError, TypeError):
            issues.append(ValidationIssue("ERROR", "typical_section.no_of_girders", f"Invalid girder count: {ng_val}", ng_val))

    # Check Girder Spacing
    spc_val = raw_inputs.get(c.KEY_TS_GIRDER_SPACING)
    if spc_val is not None and spc_val != "":
        try:
            spc = float(spc_val)
            if spc <= 0:
                issues.append(ValidationIssue("ERROR", "typical_section.girder_spacing", f"Girder spacing must be positive, got {spc}", spc))
        except (ValueError, TypeError):
            issues.append(ValidationIssue("ERROR", "typical_section.girder_spacing", f"Invalid girder spacing: {spc_val}", spc_val))

    # Check Outputs if provided
    if raw_outputs is not None:
        depth = raw_outputs.get(c.KEY_SD_TOTAL_DEPTH)
        if depth is not None:
            try:
                d = float(depth)
                if d <= 0:
                    issues.append(ValidationIssue("ERROR", "output.total_depth", f"Girder depth must be positive, got {d}", d))
            except (ValueError, TypeError):
                issues.append(ValidationIssue("ERROR", "output.total_depth", f"Invalid girder depth: {depth}", depth))

    is_valid = len([i for i in issues if i.severity == "ERROR"]) == 0
    return ValidationReport(is_valid=is_valid, issues=issues)


# =============================================================================
# 2. Semantic Facts Validation (ReportFacts Invariants)
# =============================================================================

def validate_facts(facts: ReportFacts) -> ValidationReport:
    """Validate semantic invariants on ReportFacts before AST document assembly."""
    issues: List[ValidationIssue] = []

    def _check_qv(name: str, qv: Optional[QuantityValue], min_val: Optional[float] = None, allow_zero: bool = True):
        if qv is None or qv.value is None:
            return
        v = qv.value
        if math.isnan(v) or math.isinf(v):
            issues.append(ValidationIssue("ERROR", name, f"Quantity is NaN or Inf ({v})", v))
            return
        if not allow_zero and v == 0.0:
            issues.append(ValidationIssue("ERROR", name, "Quantity cannot be zero", v))
        if min_val is not None and v < min_val:
            issues.append(ValidationIssue("ERROR", name, f"Quantity {v} is less than minimum {min_val}", v))

    # Validate Girder Checks
    if facts.design_check_data and facts.design_check_data.girders:
        for g in facts.design_check_data.girders:
            lbl = g.girder_label
            props = g.section_properties
            _check_qv(f"{lbl}.depth", props.depth, min_val=0.0, allow_zero=False)
            _check_qv(f"{lbl}.top_flange_width", props.top_flange_width, min_val=0.0, allow_zero=False)
            _check_qv(f"{lbl}.bottom_flange_width", props.bottom_flange_width, min_val=0.0, allow_zero=False)
            _check_qv(f"{lbl}.web_thickness", props.web_thickness, min_val=0.0, allow_zero=False)
            _check_qv(f"{lbl}.gross_area", props.gross_area, min_val=0.0, allow_zero=False)

            # Flexure
            _check_qv(f"{lbl}.flexure.mu", g.flexure.mu_applied, min_val=0.0)
            _check_qv(f"{lbl}.flexure.md", g.flexure.md_capacity, min_val=0.0, allow_zero=False)
            if g.flexure.utilization_ratio is not None:
                ur = g.flexure.utilization_ratio
                if math.isnan(ur) or math.isinf(ur) or ur < 0:
                    issues.append(ValidationIssue("ERROR", f"{lbl}.flexure.ur", f"Invalid utilization ratio: {ur}", ur))

            # Shear
            _check_qv(f"{lbl}.shear.vu", g.shear.vu, min_val=0.0)
            _check_qv(f"{lbl}.shear.vcr", g.shear.shear_vcr, min_val=0.0, allow_zero=False)
            if g.shear.utilization_ratio is not None:
                ur = g.shear.utilization_ratio
                if math.isnan(ur) or math.isinf(ur) or ur < 0:
                    issues.append(ValidationIssue("ERROR", f"{lbl}.shear.ur", f"Invalid shear utilization ratio: {ur}", ur))

    # Validate Deck Checks
    if facts.design_check_data and facts.design_check_data.deck and facts.design_check_data.deck.is_designed:
        dk = facts.design_check_data.deck
        _check_qv("deck.loading.effective_span", dk.loading.effective_span, min_val=0.0, allow_zero=False)
        _check_qv("deck.loading.thickness", dk.loading.thickness, min_val=0.0, allow_zero=False)
        _check_qv("deck.flexure.demand_sagging", dk.flexure.demand_sagging, min_val=0.0)
        _check_qv("deck.flexure.capacity_sagging", dk.flexure.capacity_sagging, min_val=0.0, allow_zero=False)
        _check_qv("deck.punching.punching_ved_mpa", dk.shear.punching_ved_mpa, min_val=0.0)
        _check_qv("deck.punching.punching_vrdc_mpa", dk.shear.punching_vrdc_mpa, min_val=0.0, allow_zero=False)
        _check_qv("deck.crack_width.calculated", dk.crack_width.calculated, min_val=0.0)
        _check_qv("deck.crack_width.limit", dk.crack_width.limit, min_val=0.0, allow_zero=False)

    # Validate Material Takeoff
    if facts.materials:
        if facts.materials.structural_steel and facts.materials.structural_steel.girders:
            _check_qv("material_takeoff.girders.total_weight", facts.materials.structural_steel.girders.total_weight, min_val=0.0)
        if facts.materials.concrete_volume:
            _check_qv("material_takeoff.concrete.total_volume", facts.materials.concrete_volume.total_volume, min_val=0.0)

    # Validate Provenance Tracker if attached
    if facts.provenance is not None and isinstance(facts.provenance, ProvenanceTracker):
        p_issues = facts.provenance.validate()
        for pi in p_issues:
            issues.append(ValidationIssue(
                severity=pi.severity,
                field_name=pi.fact_name,
                message=f"Provenance validation error: {pi.message}",
                actual_value=pi.provenance.source_value if pi.provenance else None,
            ))

    is_valid = len([i for i in issues if i.severity == "ERROR"]) == 0
    return ValidationReport(is_valid=is_valid, issues=issues)
