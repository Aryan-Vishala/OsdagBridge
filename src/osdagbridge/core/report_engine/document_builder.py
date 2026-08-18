# =============================================================================
# document_builder — Convert ReportFacts into a ReportDocument.
#
# This is the bridge between engineering truth (facts) and the document
# blueprint (ReportDocument).  Each chapter has its own builder function
# imported from the chapters/ sub-package.
# =============================================================================

from __future__ import annotations

from typing import List

from .document import ReportDocument
from .facts import ReportFacts


def build_report_document(
    facts: ReportFacts,
    include_sections: List[str],
) -> ReportDocument:
    """Build a complete :class:`ReportDocument` from engineering facts.

    Parameters
    ----------
    facts:
        All extracted engineering facts.
    include_sections:
        Canonical section keys (e.g. ``["loads", "design_checks"]``).

    Notes
    -----
    Chapters 2 and 7 are always included (matching legacy behaviour).
    Chapters 3 and 5 are conditional on section selection.
    """
    from .chapters.ch2_document import build_chapter_2
    from .chapters.ch3_document import build_chapter_3
    from .chapters.ch5_document import build_chapter_5
    from .chapters.ch7_document import build_chapter_7

    doc = ReportDocument(
        title=facts.metadata.project_name,
        author=facts.metadata.company,
        date=facts.metadata.report_date,
    )

    # Always included (matches legacy report_generator behaviour)
    if facts.raw_input_dict is not None:
        doc.chapters.append(build_chapter_2(facts))

    # Conditional on section selection
    if "loads" in include_sections and facts.raw_input_dict is not None:
        doc.chapters.append(build_chapter_3(facts))
    if "design_checks" in include_sections and facts.raw_input_dict is not None:
        doc.chapters.append(build_chapter_5(facts))

    # Always included (matches legacy report_generator behaviour)
    if facts.raw_input_dict is not None:
        doc.chapters.append(build_chapter_7(facts))

    return doc
