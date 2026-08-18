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
        """Run all checks."""
        checks = []
        checks.extend(self._check_data_integrity())
        checks.extend(self._check_document_structure())
        checks.extend(self._check_layout_integrity())
        
        return PreflightReport(checks=checks)

    def _check_data_integrity(self) -> List[PreflightCheck]:
        checks = []
        
        # Check end diaphragm unavailable
        if hasattr(self._facts, "material_facts") and self._facts.material_facts:
            mat = self._facts.material_facts
            if mat.structural_steel and mat.structural_steel.end_diaphragms is None:
                checks.append(PreflightCheck(
                    check_name="End Diaphragm Data",
                    status=PreflightStatus.WARN,
                    message="End diaphragm quantity is unavailable."
                ))
            else:
                checks.append(PreflightCheck(
                    check_name="End Diaphragm Data",
                    status=PreflightStatus.PASS,
                    message="End diaphragm quantity is available."
                ))
                
        # More data integrity checks can go here
        return checks
        
    def _check_document_structure(self) -> List[PreflightCheck]:
        checks = []
        # Basic check to ensure expected chapters are present
        if not self._document.chapters:
            checks.append(PreflightCheck(
                "Document Structure", PreflightStatus.FAIL, "No chapters found in document."
            ))
        else:
            checks.append(PreflightCheck(
                "Document Structure", PreflightStatus.PASS, f"Found {len(self._document.chapters)} chapters."
            ))
        return checks

    def _check_layout_integrity(self) -> List[PreflightCheck]:
        checks = []
        try:
            import fitz  # PyMuPDF
            import os
            if not os.path.exists(self._pdf_path):
                return [PreflightCheck("Footer Collision", PreflightStatus.FAIL, f"PDF file not found: {self._pdf_path}")]
            
            doc = fitz.open(self._pdf_path)
            
            # The theme page height is 297mm (A4)
            # The footer reserve margin is margin_bottom_mm (e.g. 25mm)
            # 1 mm = 2.83465 points
            MM_TO_PT = 2.83465
            page_height_pt = 297 * MM_TO_PT
            margin_bottom_pt = 25 * MM_TO_PT
            footer_reserve_pt = 15 * MM_TO_PT
            
            # Max allowed body Y is where the footer reserve starts
            # If bottom margin is 25mm and footer reserve is 15mm, the body should stop above
            # page_height - margin_bottom_pt.
            max_allowed_body_y = page_height_pt - margin_bottom_pt
            
            collision_found = False
            collision_page = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("blocks")
                
                # Exclude obvious footer text like page numbers
                for b in blocks:
                    x0, y0, x1, y1, text, block_type, block_no = b
                    
                    # block_type 0 is text
                    if block_type != 0:
                        continue
                        
                    # If this block is entirely in the footer zone and looks like a page number, ignore it
                    if y0 >= max_allowed_body_y:
                        text_stripped = text.strip()
                        if text_stripped.isdigit():
                            continue
                    
                    # Any block whose bottom Y goes into the footer zone is a collision
                    if y1 > max_allowed_body_y:
                        collision_found = True
                        collision_page = page_num + 1
                        break
                            
                if collision_found:
                    break
                    
            if collision_found:
                checks.append(PreflightCheck(
                    check_name="Footer Collision",
                    status=PreflightStatus.FAIL,
                    message=f"Body content entered footer reserve on page {collision_page}."
                ))
            else:
                checks.append(PreflightCheck(
                    check_name="Footer Collision",
                    status=PreflightStatus.PASS,
                    message="No body content entered footer reserve."
                ))
            doc.close()
        except ImportError:
            checks.append(PreflightCheck(
                "Footer Collision", PreflightStatus.WARN, "PyMuPDF (fitz) not installed, cannot verify layout."
            ))
        except Exception as e:
            checks.append(PreflightCheck(
                "Footer Collision", PreflightStatus.WARN, f"PDF layout verification failed: {e}"
            ))
            
        return checks
