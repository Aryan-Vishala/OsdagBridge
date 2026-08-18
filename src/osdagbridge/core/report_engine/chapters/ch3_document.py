# =============================================================================
# Chapter 3: Loads and Load Combinations — document builder.
#
# Phase C: Wraps the legacy ch3_loads() via RawLatex.
# Future: Migrate individual tables to structured Table components.
# =============================================================================

from ..document import Chapter, RawLatex, Section
from ..facts import ReportFacts


def build_chapter_3(facts: ReportFacts) -> Chapter:
    """Build Chapter 3: Loads and Load Combinations.

    Delegates to the legacy ``ch3_loads()`` function which returns a
    complete LaTeX chapter string.  The result is wrapped in a ``Chapter``
    with a single ``RawLatex`` component.
    """
    from osdagbridge.core.reports.chap3 import ch3_loads

    latex = ch3_loads(facts.raw_input_dict or {})

    return Chapter(
        number=3,
        title="Loads and Load Combinations",
        sections=[Section(title="", level=2, components=[RawLatex(latex)])],
    )
