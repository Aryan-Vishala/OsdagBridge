# =============================================================================
# Chapter 7: Material Take-off & Quantity Summary — document builder.
#
# Phase E: Wraps the legacy ch7_quantities() via RawLatex.
# Future: Migrate individual tables to structured Table components.
# =============================================================================

from ..document import Chapter, RawLatex, Section
from ..facts import ReportFacts


def build_chapter_7(facts: ReportFacts) -> Chapter:
    """Build Chapter 7: Material Take-off & Quantity Summary.

    Delegates to the legacy ``ch7_quantities()`` function which returns a
    complete LaTeX chapter string.  The result is wrapped in a ``Chapter``
    with a single ``RawLatex`` component.
    """
    from osdagbridge.core.reports.chap7 import ch7_quantities

    latex = ch7_quantities(facts.raw_input_dict or {})

    return Chapter(
        number=7,
        title="Material Take-off \\& Quantity Summary",
        sections=[Section(title="", level=2, components=[RawLatex(latex)])],
    )
