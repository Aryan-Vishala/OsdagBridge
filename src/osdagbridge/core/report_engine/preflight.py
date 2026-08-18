# =============================================================================
# PDFPreflight — Advisory quality verification.
#
# Phase A: framework skeleton only (run() returns an empty report).
# Phase H: actual checks implemented.
#
# The preflight is always advisory — it never blocks the PDF from being
# returned to the user.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .document import ReportDocument
    from .facts import ReportFacts


class PreflightStatus(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class PreflightCheck:
    check_name: str
    status: PreflightStatus
    message: str = ""


@dataclass
class PreflightReport:
    checks: List[PreflightCheck] = field(default_factory=list)

    @property
    def overall(self) -> PreflightStatus:
        if any(c.status == PreflightStatus.FAIL for c in self.checks):
            return PreflightStatus.FAIL
        if any(c.status == PreflightStatus.WARN for c in self.checks):
            return PreflightStatus.WARN
        return PreflightStatus.PASS

    def summary(self) -> str:
        lines = [
            f"  {c.status.value:5s}  {c.check_name}  {c.message}"
            for c in self.checks
        ]
        return "\n".join(lines)


class PDFPreflight:
    """Advisory quality check against facts and document structure.

    Returns a :class:`PreflightReport` with individual checks.  The PDF is
    always returned regardless of the overall status.
    """

    def __init__(
        self,
        facts: ReportFacts,
        document: ReportDocument,
        pdf_path: str,
    ) -> None:
        self._facts = facts
        self._document = document
        self._pdf_path = pdf_path

    def run(self) -> PreflightReport:
        """Run all checks.  Phase A returns an empty (PASS) report."""
        return PreflightReport(checks=[])
