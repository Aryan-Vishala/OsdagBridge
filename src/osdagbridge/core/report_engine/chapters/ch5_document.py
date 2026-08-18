# =============================================================================
# Chapter 5: Design Checks — document builder.
#
# Phase D: Wraps the legacy ch5_design_checks() via RawLatex.
# Future: Migrate individual tables to structured Table components.
# =============================================================================

from ..document import Chapter, RawLatex, Section
from ..facts import ReportFacts


def build_chapter_5(facts: ReportFacts) -> Chapter:
    """Build Chapter 5: Design Checks.

    Delegates to the legacy ``ch5_design_checks()`` function which returns a
    complete LaTeX chapter string.  The result is wrapped in a ``Chapter``
    with a single ``RawLatex`` component.

    Requires a ``ReportDataBridge`` instance, which is constructed from the
    raw dicts stored on ``facts``.
    """
    from osdagbridge.core.reports.chap5 import ch5_design_checks
    from osdagbridge.core.reports.report_generator import ReportDataBridge

    input_dict = facts.raw_input_dict or {}
    output_dict = facts.raw_output_dict or {}

    bridge = ReportDataBridge(output_dict, input_dict, _PayloadProxy(facts))

    latex = ch5_design_checks(facts.design_checks or [], bridge)

    return Chapter(
        number=5,
        title="Design Checks",
        sections=[Section(title="", level=2, components=[RawLatex(latex)])],
    )


class _PayloadProxy:
    """Minimal proxy satisfying the ``ReportPayload`` interface accessed by
    ``ReportDataBridge`` — only ``design_checks`` is read."""

    def __init__(self, facts: ReportFacts):
        self.design_checks = facts.design_checks or []
