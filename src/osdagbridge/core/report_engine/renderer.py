# =============================================================================
# LatexRenderer — Translates a ReportDocument into a LaTeX string.
#
# All formatting logic lives here.  Chapters never touch LaTeX directly
# (except via RawLatex escape hatches during migration).
# =============================================================================

from __future__ import annotations

from typing import Optional

from .document import (
    Callout,
    Chart,
    Chapter,
    Column,
    DocumentComponent,
    Figure,
    RawLatex,
    ReportDocument,
    Section,
    Table,
    TableGroup,
)
from .facts import CheckStatus, QuantityValue
from .theme import ReportTheme


class LatexRenderer:
    """Render a :class:`ReportDocument` into a complete LaTeX string."""

    def __init__(self, theme: ReportTheme) -> None:
        self._theme = theme

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render(self, document: ReportDocument) -> str:
        """Return a full LaTeX document body (preamble … \\end{document})."""
        parts = [self._preamble()]
        for chapter in document.chapters:
            parts.append(self._render_chapter(chapter))
        parts.append(r"\end{document}")
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Formatting helpers  (renderer owns all presentation)
    # ------------------------------------------------------------------

    def fmt_quantity(self, qv: Optional[QuantityValue], fallback: str = "N/A") -> str:
        """Format a QuantityValue for LaTeX output.

        ``None`` → *fallback*.  ``QuantityValue(None, unit)`` → *fallback*.
        ``QuantityValue(0.0, "kN")`` → ``"0.0 kN"`` (zero is valid).
        """
        if qv is None:
            return fallback
        if qv.value is None:
            return fallback
        if qv.unit:
            return f"{qv.value} {qv.unit}"
        return str(qv.value)

    def fmt_float(self, v: Optional[float], fallback: str = "N/A") -> str:
        """Format an optional float.  ``None`` → *fallback*."""
        if v is None:
            return fallback
        return str(v)

    def fmt_status(self, status: CheckStatus) -> str:
        """Format a CheckStatus for LaTeX output."""
        _map = {
            CheckStatus.PASS: "PASS",
            CheckStatus.WARN: r"\textcolor{orange}{WARN}",
            CheckStatus.FAIL: r"\textcolor{red}{FAIL}",
            CheckStatus.UNAVAILABLE: "---",
        }
        return _map.get(status, "---")

    # ------------------------------------------------------------------
    # Document tree
    # ------------------------------------------------------------------

    def _render_chapter(self, ch: Chapter) -> str:
        lines = [f"\\chapter{{{ch.title}}}"]
        for section in ch.sections:
            lines.append(self._render_section(section))
        return "\n".join(lines)

    def _render_section(self, sec: Section) -> str:
        cmd = {2: "section", 3: "subsection"}.get(sec.level, "section")
        lines = [f"\\{cmd}{{{sec.title}}}"]
        for comp in sec.components:
            lines.append(self._render_component(comp))
        return "\n".join(lines)

    def _render_component(self, comp: DocumentComponent) -> str:
        dispatch = {
            Table: self._render_table,
            Chart: self._render_chart,
            Figure: self._render_figure,
            Callout: self._render_callout,
            RawLatex: lambda c: c.content,
        }
        renderer = dispatch.get(type(comp))
        if renderer is None:
            raise TypeError(f"Unknown component type: {type(comp).__name__}")
        return renderer(comp)

    # ------------------------------------------------------------------
    # Component renderers
    # ------------------------------------------------------------------

    def _render_table(self, table: Table) -> str:
        from ..reports.table_utils import make_longtable

        hints = table.layout
        parts: list[str] = []

        if hints.minimum_bottom_clearance_lines > 0:
            parts.append(
                f"\\Needspace{{{hints.minimum_bottom_clearance_lines}\\baselineskip}}"
            )

        if hints.keep_together:
            parts.append(r"\begin{minipage}[t]{\textwidth}")

        # Build column spec from columns
        col_spec = self._build_col_spec(table)

        # Build header row from columns
        header = self._build_header_row(table)

        # Build body from semantic rows or groups
        body = self._build_body(table)

        pre = r"\hline" if hints.keep_caption_with_table else ""
        parts.append(
            make_longtable(
                col_spec=col_spec,
                caption=table.caption,
                header_rows=[header],
                body=body,
                pre=pre,
                post=r"\hline",
            )
        )

        if hints.keep_together:
            parts.append(r"\end{minipage}")

        if hints.space_after_mm > 0:
            parts.append(f"\\vspace{{{hints.space_after_mm}mm}}")

        return "\n".join(parts)

    def _build_col_spec(self, table: Table) -> str:
        """Build a LaTeX column spec string from Table.columns."""
        if table.columns:
            # Use explicit widths if provided, otherwise default to left-aligned
            specs = []
            for col in table.columns:
                if col.width:
                    specs.append(col.width)
                else:
                    specs.append("l")
            return "|" + "|".join(specs) + "|"
        return "l"

    def _build_header_row(self, table: Table) -> str:
        """Build the header row LaTeX from Table.columns."""
        cells = [r"\textbf{" + self._escape(c.header) + "}" for c in table.columns]
        return " & ".join(cells)

    def _build_body(self, table: Table) -> str:
        """Build the table body LaTeX from Table.rows or Table.groups."""
        if table.groups:
            return self._build_grouped_body(table)
        lines = []
        for row in (table.rows or []):
            cells = [self._escape(cell) for cell in row]
            lines.append(" & ".join(cells) + r" \\")
        return "\n".join(lines)

    def _build_grouped_body(self, table: Table) -> str:
        """Build body with \\multirow for TableGroup labels.

        For each group, the group label spans all rows in the first column.
        Subsequent rows have an empty first cell (the \\multirow covers them).
        """
        if not table.groups:
            return ""
        lines = []
        for group_idx, group in enumerate(table.groups):
            n_rows = len(group.rows)
            label_esc = self._escape(group.label)
            for row_idx, row in enumerate(group.rows):
                cells = [self._escape(cell) for cell in row]
                if row_idx == 0 and n_rows > 1:
                    first_cell = (
                        r"\multirow{" + str(n_rows) + r"}{*}{\makecell{"
                        + label_esc + r"}}"
                    )
                elif row_idx == 0:
                    first_cell = label_esc
                else:
                    first_cell = ""
                
                cells.insert(0, first_cell)
                lines.append(" & ".join(cells) + r" \\[6pt]")
                if row_idx < n_rows - 1:
                    lines.append(r"\cline{2-" + str(len(table.columns)) + "}")
            lines.append(r"\hline")
        return "\n".join(lines)

    def _escape(self, text: str) -> str:
        """Escape a plain-text value for safe LaTeX embedding.

        This is the renderer's responsibility — chapter builders never
        write LaTeX syntax for table data.
        """
        from osdagbridge.core.reports.report_utils import _tex
        return _tex(text)

    def _render_chart(self, chart: Chart) -> str:
        from .chart_generators import generate_chart

        path = generate_chart(chart, self._theme)
        return (
            r"\begin{figure}[H]"
            + "\n"
            + r"\centering"
            + "\n"
            + r"\includegraphics[width="
            + str(self._theme.chart.width_cm)
            + r"cm]{"
            + path
            + "}"
            + "\n"
            + r"\caption*{\small "
            + chart.title
            + "}"
            + "\n"
            + r"\end{figure}"
        )

    def _render_figure(self, figure: Figure) -> str:
        if figure.path:
            p = figure.path.replace("\\", "/")
            return (
                r"\begin{figure}[H]"
                + "\n"
                + r"\centering"
                + "\n"
                + r"\includegraphics[width="
                + figure.width
                + "]{"
                + p
                + "}"
                + "\n"
                + r"\caption*{\small "
                + figure.caption
                + "}"
                + "\n"
                + r"\end{figure}"
            )
        # Placeholder when no image is available.
        return (
            r"\noindent\fbox{\parbox{0.97\textwidth}{"
            r"\textit{[ PLACEHOLDER: "
            + figure.caption
            + " ]}}}"
        )

    def _render_callout(self, callout: Callout) -> str:
        env_map = {"note": "remark", "warning": "warning", "info": "info"}
        env = env_map.get(callout.callout_type, "remark")
        return f"\\begin{{{env}}}\n{callout.text}\n\\end{{{env}}}"

    # ------------------------------------------------------------------
    # Preamble  (auto-generated from the immutable theme)
    # ------------------------------------------------------------------

    def _preamble(self) -> str:
        pg = self._theme.page
        ts = self._theme.table_styles.get("default", self._theme.table_styles["default"])
        cl = self._theme.colors
        return (
            r"\documentclass[11pt,a4paper]{report}"
            "\n"
            r"\usepackage["
            f"top={pg.margin_top_mm}mm,"
            f"bottom={pg.margin_bottom_mm}mm,"
            f"left={pg.margin_left_mm}mm,"
            f"right={pg.margin_right_mm}mm"
            r"]{geometry}"
            "\n"
            r"\usepackage{longtable,booktabs,array}"
            "\n"
            r"\usepackage{graphicx}"
            "\n"
            r"\usepackage{float}"
            "\n"
            r"\usepackage{needspace}"
            "\n"
            r"\usepackage{xcolor}"
            "\n"
            r"\definecolor{primary}{" + cl.primary + "}"
            "\n"
            r"\definecolor{accent}{" + cl.accent + "}"
            "\n"
            r"\setlength{\tabcolsep}{" + str(ts.column_padding_pt) + "pt}"
            "\n"
        )
