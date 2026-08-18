# =============================================================================
# Legacy adapter — wraps old ch*_load() functions into Chapter objects.
#
# During migration, chapters that haven't been converted yet continue to
# return raw LaTeX strings.  This adapter wraps them so they can be placed
# inside a ReportDocument via RawLatex components.
# =============================================================================

from .document import Chapter, RawLatex, Section


def wrap_legacy_chapter(
    chapter_number: int,
    title: str,
    latex_fn,
    *args,
) -> Chapter:
    """Call an old chapter function and wrap the result in a Chapter."""
    latex = latex_fn(*args)
    return Chapter(
        number=chapter_number,
        title=title,
        sections=[Section(title="", level=2, components=[RawLatex(latex)])],
    )
