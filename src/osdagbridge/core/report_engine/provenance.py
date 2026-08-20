"""
Data Provenance & Fact Tracing Engine
=====================================

Provides comprehensive tracking, validation, and reporting of the exact data lineage
for every engineering value presented in the semantic report system.

Architecture (Stage 4):
  Raw Analysis / Input Payload
             ↓
     ProvenanceTracker
             ↓
  ReportFacts (Typed Facts + Provenance Records)
             ↓
  Provenance Validation & Tracing
             ↓
  ReportDocument AST → LatexRenderer → PDF

Classes & Models:
- ValueSource: Enum for origin source (input_dict, output_dict, derived, code_default, fallback).
- FactProvenance: Immutable typed record tracking the origin key, raw source value, target unit,
  and mathematical transformation.
- ProvenanceValidationIssue: Verification failure (missing key, unexpected unit conversion, invalid scaling).
- ProvenanceTracker: Central registry capturing all provenance events, validating unit conversions,
  and rendering debug lineage reports.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union


class ValueSource(str, Enum):
    INPUT_DICT = "input_dict"
    OUTPUT_DICT = "output_dict"
    DERIVED = "derived"
    CODE_DEFAULT = "code_default"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class FactProvenance:
    """Typed record tracking the exact origin, transformation, and unit conversion of an engineering fact."""
    fact_name: str
    source: ValueSource
    source_key: str
    source_value: Any
    extracted_value: Any
    source_unit: Optional[str] = None
    target_unit: Optional[str] = None
    transform: Optional[str] = None
    notes: Optional[str] = None

    @property
    def is_converted(self) -> bool:
        return (
            self.source_unit is not None
            and self.target_unit is not None
            and self.source_unit.lower() != self.target_unit.lower()
        )


@dataclass
class ProvenanceValidationIssue:
    fact_name: str
    severity: str  # "ERROR", "WARNING"
    message: str
    provenance: Optional[FactProvenance] = None


class ProvenanceTracker:
    """Registry capturing fact extractions, conversions, and provenance traces."""

    def __init__(self):
        self._records: Dict[str, FactProvenance] = {}
        self._issues: List[ProvenanceValidationIssue] = []

    def record(
        self,
        fact_name: str,
        source: Union[ValueSource, str],
        source_key: str,
        source_value: Any,
        extracted_value: Any,
        source_unit: Optional[str] = None,
        target_unit: Optional[str] = None,
        transform: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> FactProvenance:
        if isinstance(source, str):
            try:
                source = ValueSource(source)
            except ValueError:
                source = ValueSource.DERIVED
        prov = FactProvenance(
            fact_name=fact_name,
            source=source,
            source_key=source_key,
            source_value=source_value,
            extracted_value=extracted_value,
            source_unit=source_unit,
            target_unit=target_unit,
            transform=transform,
            notes=notes,
        )
        self._records[fact_name] = prov
        return prov

    def get(self, fact_name: str) -> Optional[FactProvenance]:
        return self._records.get(fact_name)

    @property
    def all_records(self) -> Dict[str, FactProvenance]:
        return dict(self._records)

    @property
    def issues(self) -> List[ProvenanceValidationIssue]:
        return list(self._issues)

    def extract(
        self,
        fact_name: str,
        data_dict: Optional[Dict[str, Any]],
        key: str,
        target_unit: str,
        expected_source_unit: Optional[str] = None,
        transform_fn: Optional[Callable[[Any], Any]] = None,
        transform_description: Optional[str] = None,
        default: Any = None,
        source_type: ValueSource = ValueSource.OUTPUT_DICT,
        notes: Optional[str] = None,
    ) -> Any:
        """Extract a value from a dictionary while recording its complete provenance trace."""
        if data_dict is None or key not in data_dict:
            self.record(
                fact_name=fact_name,
                source=ValueSource.FALLBACK if default is not None else source_type,
                source_key=key,
                source_value=None,
                extracted_value=default,
                source_unit=expected_source_unit,
                target_unit=target_unit,
                transform="fallback_default" if default is not None else "missing_key",
                notes=notes,
            )
            return default

        raw_val = data_dict[key]
        if raw_val is None or raw_val == "":
            self.record(
                fact_name=fact_name,
                source=source_type,
                source_key=key,
                source_value=raw_val,
                extracted_value=default,
                source_unit=expected_source_unit,
                target_unit=target_unit,
                transform="none",
                notes=notes,
            )
            return default

        try:
            if transform_fn is not None:
                final_val = transform_fn(raw_val)
            else:
                try:
                    final_val = float(raw_val)
                except (ValueError, TypeError):
                    final_val = raw_val
        except Exception as e:
            self._issues.append(ProvenanceValidationIssue(
                fact_name=fact_name,
                severity="ERROR",
                message=f"Failed to transform value '{raw_val}' for key '{key}': {e}",
            ))
            final_val = default

        # Determine transform description
        if transform_description:
            t_desc = transform_description
        elif expected_source_unit and target_unit and expected_source_unit.lower() != target_unit.lower():
            t_desc = f"{expected_source_unit} -> {target_unit}"
        else:
            t_desc = "none"

        self.record(
            fact_name=fact_name,
            source=source_type,
            source_key=key,
            source_value=raw_val,
            extracted_value=final_val,
            source_unit=expected_source_unit or target_unit,
            target_unit=target_unit,
            transform=t_desc,
            notes=notes,
        )
        return final_val

    def validate(self) -> List[ProvenanceValidationIssue]:
        """Validate all recorded provenance records against domain sanity rules."""
        issues = list(self._issues)
        for name, p in self._records.items():
            # Check unit transformation consistency
            if p.source_unit and p.target_unit and p.source_value is not None and p.extracted_value is not None:
                s_u = p.source_unit.lower().replace(" ", "")
                t_u = p.target_unit.lower().replace(" ", "")
                try:
                    s_f = float(p.source_value)
                    e_f = float(p.extracted_value)
                except (ValueError, TypeError):
                    continue

                if s_u == "m" and t_u == "mm":
                    # Value should scale by 1000
                    if s_f > 0 and abs(e_f - s_f * 1000.0) / (s_f * 1000.0) > 0.01:
                        issues.append(ProvenanceValidationIssue(
                            fact_name=name,
                            severity="ERROR",
                            message=f"Unit mismatch: source {s_f} m converted to {e_f} mm (expected {s_f * 1000.0} mm)",
                            provenance=p,
                        ))
                elif s_u == "mm" and t_u == "m":
                    # Value should scale by 0.001
                    if s_f > 0 and abs(e_f - s_f / 1000.0) / (s_f / 1000.0) > 0.01:
                        issues.append(ProvenanceValidationIssue(
                            fact_name=name,
                            severity="ERROR",
                            message=f"Unit mismatch: source {s_f} mm converted to {e_f} m (expected {s_f / 1000.0} m)",
                            provenance=p,
                        ))
                elif s_u in ("cm^2", "cm2") and t_u in ("mm^2", "mm2"):
                    # Value should scale by 100
                    if s_f > 0 and abs(e_f - s_f * 100.0) / (s_f * 100.0) > 0.01:
                        issues.append(ProvenanceValidationIssue(
                            fact_name=name,
                            severity="ERROR",
                            message=f"Unit mismatch: source {s_f} cm² converted to {e_f} mm² (expected {s_f * 100.0} mm²)",
                            provenance=p,
                        ))
                elif s_u == "n" and t_u == "kn":
                    # Value should scale by 0.001
                    if s_f > 0 and abs(e_f - s_f / 1000.0) / (s_f / 1000.0) > 0.01:
                        issues.append(ProvenanceValidationIssue(
                            fact_name=name,
                            severity="ERROR",
                            message=f"Unit mismatch: source {s_f} N converted to {e_f} kN (expected {s_f / 1000.0} kN)",
                            provenance=p,
                        ))
        return issues

    def format_report(self) -> str:
        """Format human-readable provenance report."""
        lines = [
            "DATA PROVENANCE REPORT",
            "------------------------------------",
            "",
        ]
        for name, p in sorted(self._records.items()):
            val_str = f"{p.extracted_value} {p.target_unit or ''}".rstrip()
            src_val_str = f"{p.source_value} {p.source_unit or ''}".rstrip()
            lines.append(f"{name}")
            lines.append(f"  {val_str}")
            lines.append(f"  <- {p.source.value}[\"{p.source_key}\"] ({src_val_str})")
            if p.transform and p.transform != "none":
                lines.append(f"  <- transform: {p.transform}")
            else:
                lines.append("  <- transform: none")
            lines.append("")

        issues = self.validate()
        lines.extend([
            "SUMMARY:",
            f"  Tracked Fact Values: {len(self._records)}",
            f"  Conversions Tracked: {sum(1 for p in self._records.values() if p.is_converted)}",
            f"  Validation Issues:   {len(issues)}",
        ])
        if issues:
            lines.append("")
            lines.append("ISSUES DETECTED:")
            for iss in issues:
                lines.append(f"  [{iss.severity}] {iss.fact_name}: {iss.message}")

        return "\n".join(lines)
