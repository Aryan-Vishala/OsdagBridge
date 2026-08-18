# =============================================================================
# ReportDocument — The document blueprint.
#
# Represents *what* the report should show.  No LaTeX.  No formatting.
# Chapters compose these building blocks; the renderer turns them into LaTeX.
# =============================================================================

from dataclasses import dataclass, field
from typing import List, Optional, Union

from .layout import LayoutHints

# Union of all renderable component types.
DocumentComponent = Union["Table", "Chart", "Figure", "Callout", "RawLatex"]


@dataclass(frozen=True)
class Column:
    """Describes a single column in a Table."""

    header: str
    width: str = ""


@dataclass
class Table:
    """A longtable with caption, semantic columns, and data rows.

    ``columns`` defines the header row.  ``rows`` contains plain-text cell
    values — no LaTeX syntax.  The renderer is responsible for escaping and
    formatting.
    """

    caption: str
    columns: List[Column]
    rows: List[List[str]]
    layout: LayoutHints = field(default_factory=LayoutHints)
    label: str = ""


@dataclass
class Chart:
    """A chart / visualisation component.

    ``data`` is a plain dict for now.  The eventual target is structured
    semantic data (e.g. ``UtilizationFacts``) so that chapters pass facts
    directly rather than pre-aggregating into dicts.
    """

    title: str
    chart_type: str  # "bar", "grouped_bar"
    data: dict
    x_label: str = ""
    y_label: str = ""
    threshold_line: Optional[float] = None
    layout: LayoutHints = field(default_factory=LayoutHints)


@dataclass
class Figure:
    """An embedded image (CAD view, grillage plot, etc.)."""

    path: Optional[str]
    caption: str
    width: str = r"0.9\textwidth"
    layout: LayoutHints = field(default_factory=LayoutHints)


@dataclass
class Callout:
    """A note, warning, or info box."""

    text: str
    callout_type: str = "note"  # "note", "warning", "info"
    layout: LayoutHints = field(default_factory=LayoutHints)


@dataclass
class RawLatex:
    """Legacy escape hatch — raw LaTeX passed through unchanged.

    Used only during migration of chapters that haven't been converted to
    structured components yet.  Not the target architecture.
    """

    content: str


@dataclass
class Section:
    r"""A section within a chapter (level 2 = ``\section``, 3 = ``\subsection``)."""

    title: str
    level: int = 2
    components: List[DocumentComponent] = field(default_factory=list)


@dataclass
class Chapter:
    """A top-level chapter of the report."""

    number: int
    title: str
    sections: List[Section] = field(default_factory=list)


@dataclass
class ReportDocument:
    """Root container for the entire report blueprint."""

    title: str = "OsdagBridge Design Report"
    author: str = ""
    date: str = ""
    chapters: List[Chapter] = field(default_factory=list)
