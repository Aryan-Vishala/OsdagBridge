# =============================================================================
# LayoutHints — Semantic pagination and spacing directives.
#
# These are *semantic*, not mechanical.  The renderer translates each hint
# into the appropriate LaTeX construct.  Chapters never emit raw LaTeX for
# spacing or pagination — they declare hints only.
# =============================================================================

from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutHints:
    """Semantic pagination / spacing hints attached to every document component."""

    keep_with_next: bool = False
    keep_together: bool = False
    keep_caption_with_table: bool = True
    minimum_bottom_clearance_lines: int = 3
    splittable: bool = True
    repeat_header: bool = True
    space_after_mm: float = 4.0
