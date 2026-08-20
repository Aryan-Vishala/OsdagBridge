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
    Math,
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

    def render_chapter(self, chapter: Chapter) -> str:
        """Render a single semantic Chapter into a LaTeX string."""
        return self._render_chapter(chapter)

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


    def render_chapter(self, ch: Chapter) -> str:
        """Render a single semantic Chapter AST component into LaTeX."""
        return self._render_chapter(ch)

    def render_document(self, doc: ReportDocument) -> str:
        """Render a full ReportDocument AST into LaTeX."""
        parts = []
        for ch in doc.chapters:
            parts.append(self._render_chapter(ch))
        return "\n\n".join(parts)

    def _render_chapter(self, ch: Chapter) -> str:
        lines = [f"\\chapter{{{ch.title}}}"]
        for section in ch.sections:
            lines.append(self._render_section(section))
        return "\n".join(lines)

    def _render_section(self, sec: Section) -> str:
        cmd = {2: "section", 3: "subsection"}.get(sec.level, "section")
        hints = getattr(sec, "layout", None)
        is_landscape = hints and getattr(hints, "orientation", "portrait") == "landscape"
        lines = []
        if is_landscape:
            lines.append(r"\begin{osdaglandscape}")
        if sec.title:
            lines.append(f"\\{cmd}{{{sec.title}}}")
        for comp in sec.components:
            lines.append(self._render_component(comp, in_landscape=is_landscape))
        if is_landscape:
            lines.append(r"\end{osdaglandscape}")
        return "\n".join(lines)

    def _render_component(self, comp: DocumentComponent, in_landscape: bool = False) -> str:
        from .document import Paragraph
        dispatch = {
            Table: lambda c: self._render_table(c, in_landscape=in_landscape),
            Chart: self._render_chart,
            Figure: self._render_figure,
            Callout: self._render_callout,
            Paragraph: self._render_paragraph,
            RawLatex: self._render_raw_latex,
        }
        renderer = dispatch.get(type(comp))
        if renderer is None:
            raise TypeError(f"Unknown component type: {type(comp).__name__}")
        return renderer(comp)

    # ------------------------------------------------------------------
    # Component renderers
    # ------------------------------------------------------------------

    def _render_paragraph(self, comp: Any) -> str:
        content = self._escape(comp.text) if isinstance(comp.text, (list, tuple)) else self._escape(str(comp.text))
        return f"\n{content}\n"

    def _render_raw_latex(self, comp: RawLatex) -> str:
        if isinstance(comp.content, (list, tuple)):
            parts = []
            for part in comp.content:
                if isinstance(part, Math):
                    parts.append(f"${part.content}$")
                else:
                    parts.append(str(part))
            return "".join(parts)
        return str(comp.content)

    def _render_table(self, table: Table, in_landscape: bool = False) -> str:
        from ..reports.table_utils import make_longtable

        hints = table.layout
        ts = self._theme.table_styles.get(hints.style, self._theme.table_styles["default"])
        
        parts: list[str] = []
        table_landscape = getattr(hints, "orientation", "portrait") == "landscape"
        wrap_landscape = table_landscape and not in_landscape

        if wrap_landscape:
            parts.append(r"\begin{osdaglandscape}")

        if hints.minimum_bottom_clearance_lines > 0:
            parts.append(
                f"\\Needspace{{{hints.minimum_bottom_clearance_lines}\\baselineskip}}"
            )
        elif hints.keep_caption_with_table:
            parts.append(r"\Needspace{4\baselineskip}")

        has_custom_style = (
            ts.font_size != "normalsize"
            or ts.row_height_factor != 1.15
            or ts.column_padding_pt != 6
        )
        if has_custom_style:
            parts.append(r"\begingroup")
            if ts.font_size != "normalsize":
                parts.append(f"\\{ts.font_size}")
            if ts.row_height_factor != 1.15:
                parts.append(f"\\renewcommand{{\\arraystretch}}{{{ts.row_height_factor}}}")
            if ts.column_padding_pt != 6:
                parts.append(f"\\setlength{{\\tabcolsep}}{{{ts.column_padding_pt}pt}}")

        col_spec = self._build_col_spec(table)
        header = self._build_header_row(table)
        body = self._build_body(table, ts)

        pre = r"\hline" if hints.keep_caption_with_table else ""
        
        # Apply caption font weight if bold
        cap_weight = r"\textbf{" if self._theme.typography.caption_font_weight == "bold" else ""
        cap_close = r"}" if cap_weight else ""
        formatted_caption = f"{cap_weight}{table.caption}{cap_close}"
        
        plain_cap = table.caption.replace(r"\textbf{", "").replace("}", "") if r"\textbf{" in table.caption else table.caption
        cont_cap = r"\multicolumn{" + str(max(1, len(table.columns))) + r"}{c}{\textit{" + plain_cap + r" (continued)}} \\"
        rh = cont_cap if hints.repeat_header else False

        parts.append(
            make_longtable(
                col_spec=col_spec,
                num_cols=max(1, len(table.columns)),
                caption=formatted_caption,
                header_rows=[header],
                body=body,
                pre=pre,
                post=r"\hline",
                repeat_header=rh,
            )
        )
        
        if getattr(table, "note", None):
            note_esc = self._escape(table.note)
            parts.append(r"\par\vspace{-2mm}\noindent{\small\textit{Note: " + note_esc + r"}}\par\vspace{1em}")

        if has_custom_style:
            parts.append(r"\endgroup")

        if wrap_landscape:
            parts.append(r"\end{osdaglandscape}")

        if hints.space_after_mm > 0:
            parts.append(f"\\vspace{{{hints.space_after_mm}mm}}")

        return "\n".join(parts)

    def _build_col_spec(self, table: Table) -> str:
        """Derive column specification from table headers and widths."""
        col_types = []
        for col in table.columns:
            if col.width:
                col_types.append(col.width)
            else:
                col_types.append("l")
        return "|" + "|".join(col_types) + "|"

    def _build_header_row(self, table: Table) -> str:
        """Build the header row LaTeX from Table.columns."""
        cells = [r"\textbf{" + self._escape(c.header) + "}" for c in table.columns]
        return " & ".join(cells)

    def _build_body(self, table: Table, ts: TableStyle | None = None) -> str:
        """Dispatch to flat or grouped row builders."""
        if table.groups is not None:
            return self._build_grouped_body(table, ts)
        lines = []
        rows = table.rows or []
        n_cols = len(table.columns)
        for i, row in enumerate(rows):
            # Check if this row is a spanning category subheader (e.g. in Table 5.23)
            if len(row) > 1 and all(c == "" or c is None for c in row[1:]):
                hdr_text = self._escape(row[0])
                lines.append(r"\multicolumn{" + str(n_cols) + r"}{|l|}{\textbf{" + hdr_text + r"}} \\")
            else:
                cells = [self._escape(cell) for cell in row]
                lines.append(" & ".join(cells) + r" \\")
            if i < len(rows) - 1:
                lines.append(r"\noalign{\penalty0}\hline")
        return "\n".join(lines)

    def _build_grouped_body(self, table: Table, ts: TableStyle | None = None) -> str:
        """Build body for grouped tables, handling splittable vs non-splittable with theme rules."""
        if not table.groups:
            return ""
        if ts is None:
            ts = self._theme.table_styles.get(table.layout.style, self._theme.table_styles["default"])

        lines = []
        is_splittable = table.layout.splittable
        n_cols = len(table.columns)
        
        for group_idx, group in enumerate(table.groups):
            n_rows = len(group.rows)
            label_esc = self._escape(group.label)
            for row_idx, row in enumerate(group.rows):
                cells = [self._escape(cell) for cell in row]
                
                if row_idx == 0:
                    if is_splittable:
                        first_cell = label_esc
                    else:
                        first_cell = (
                            r"\multirow{" + str(n_rows) + r"}{*}{\makecell{"
                            + label_esc + r"}}"
                        ) if n_rows > 1 else label_esc
                else:
                    first_cell = ""
                
                cells.insert(0, first_cell)
                lines.append(" & ".join(cells) + r" \\")

                # Inner row separator within the same group
                if row_idx < n_rows - 1:
                    if ts.inner_group_rule == "subtle":
                        lines.append(rf"\noalign{{\penalty0}}\cline{{2-{n_cols}}}")
                    elif ts.inner_group_rule == "full":
                        lines.append(r"\noalign{\penalty0}\hline")
            
            # Group boundary separator
            if group_idx < len(table.groups) - 1:
                if ts.group_boundary_rule == "strong":
                    lines.append(r"\noalign{\penalty0}\hline")
                elif ts.group_boundary_rule == "double":
                    lines.append(r"\noalign{\penalty0}\hline\hline")
                
        return "\n".join(lines)

    def _escape(self, text: Any) -> str:
        """Escape a plain-text value for safe LaTeX embedding.

        This is the renderer's responsibility — chapter builders never
        write LaTeX syntax for table data.
        """
        # Apply visual policy for statuses natively
        if isinstance(text, CheckStatus):
            if text == CheckStatus.FAIL:
                return r"\textcolor{error}{FAIL}"
            if text == CheckStatus.WARN:
                return r"\textcolor{accent}{WARN}"
            if text == CheckStatus.PASS:
                return "PASS"
            return "---"
            
        if isinstance(text, Math):
            return f"${text.content}$"
            
        if isinstance(text, (list, tuple)):
            return "".join(self._escape(part) for part in text if part is not None)
        
        text_str = str(text) if text is not None else ""
        
        # 1. Protect inline math blocks $...$ from being mangled by _tex
        import re
        math_blocks = []
        def _save_math(m):
            idx = len(math_blocks)
            math_blocks.append(m.group(0))
            return f"ZMATH{idx}ZZ"
        text_str = re.sub(r"\$[^$]+\$", _save_math, text_str)

        # 2. Pre-process unicode symbols to protect them from `_tex` and escape to math mode
        unicode_map = {
            "≤": r"$\leq$",
            "≥": r"$\geq$",
            "×": r"$\times$",
            "±": r"$\pm$",
            "°": r"$^\circ$",
            "–": "--",    # en-dash
            "—": "---",   # em-dash
            "−": "-",     # minus sign
            "→": r"$\rightarrow$",
            "·": r"$\cdot$",
            "²": r"$^2$",
            "³": r"$^3$",
            "⁴": r"$^4$",
            "Ø": r"$\emptyset$",
            "α": r"$\alpha$",
            "γ": r"$\gamma$",
            "ε": r"$\epsilon$",
            "λ": r"$\lambda$",
            "ρ": r"$\rho$",
            "σ": r"$\sigma$",
            "τ": r"$\tau$",
            "χ": r"$\chi$",
            "ϕ": r"$\phi$",
            "μ": r"$\mu$"
        }
        
        # Hide characters from _tex using a placeholder
        for uni in unicode_map:
            text_str = text_str.replace(uni, f"ZUNIQ{ord(uni)}ZZ")
            
        from osdagbridge.core.reports.report_utils import _tex
        escaped = _tex(text_str)
        
        # Fix text-mode inequality symbols so they do not render as ¿ in OT1
        escaped = escaped.replace(">", r"$>$").replace("<", r"$<$")

        # Restore unicode math
        for uni, latex_code in unicode_map.items():
            escaped = escaped.replace(f"ZUNIQ{ord(uni)}ZZ", latex_code)

        # Restore preserved inline math blocks
        for idx, math_tex in enumerate(math_blocks):
            escaped = escaped.replace(f"ZMATH{idx}ZZ", math_tex)
            
        return escaped

    def _render_chart(self, chart: Chart) -> str:
        from .chart_generators import generate_chart

        path = generate_chart(chart, self._theme)
        if path:
            path = path.replace("\\", "/")
        hints = chart.layout
        parts = []
        
        if hints.minimum_bottom_clearance_lines > 0:
            parts.append(f"\\Needspace{{{hints.minimum_bottom_clearance_lines}\\baselineskip}}")
            
        cap_weight = r"\textbf{" if self._theme.typography.caption_font_weight == "bold" else ""
        cap_close = r"}" if cap_weight else ""
            
        width_val = chart.width_cm if chart.width_cm is not None else self._theme.charts.get("default", self._theme.charts["default"]).width_cm
        width_str = f"{width_val}cm"

        parts.append(
            r"\begin{figure}[H]"
            + "\n"
            + r"\centering"
            + "\n"
            + r"\includegraphics[width="
            + width_str
            + r"]{"
            + path
            + "}"
            + "\n"
            + r"\caption*{\small "
            + cap_weight + chart.title + cap_close
            + "}"
            + "\n"
            + r"\end{figure}"
        )
        if hints.space_after_mm > 0:
            parts.append(f"\\vspace{{{hints.space_after_mm}mm}}")
            
        return "\n".join(parts)

    def _render_figure(self, figure: Figure) -> str:
        hints = figure.layout
        parts = []
        
        if hints.minimum_bottom_clearance_lines > 0:
            parts.append(f"\\Needspace{{{hints.minimum_bottom_clearance_lines}\\baselineskip}}")
            
        cap_weight = r"\textbf{" if self._theme.typography.caption_font_weight == "bold" else ""
        cap_close = r"}" if cap_weight else ""
            
        if figure.path:
            p = figure.path.replace("\\", "/")
            parts.append(
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
                + cap_weight + figure.caption + cap_close
                + "}"
                + "\n"
                + r"\end{figure}"
            )
        else:
            parts.append(
                r"\noindent\fbox{\parbox{1.0\textwidth}{"
                r"\textit{[ PLACEHOLDER: "
                + figure.caption
                + " ]}}}"
            )
            
        if hints.space_after_mm > 0:
            parts.append(f"\\vspace{{{hints.space_after_mm}mm}}")
            
        return "\n".join(parts)

    def _render_callout(self, callout: Callout) -> str:
        hints = callout.layout
        parts = []
        if hints.minimum_bottom_clearance_lines > 0:
            parts.append(f"\\Needspace{{{hints.minimum_bottom_clearance_lines}\\baselineskip}}")
        if hints.keep_together:
            parts.append(r"\begin{minipage}{\textwidth}")
            
        env_map = {"note": "remark", "warning": "warning", "info": "info"}
        env = env_map.get(callout.callout_type, "remark")
        
        # Render the text content, which can now be a list of semantic elements
        content = self._escape(callout.text) if isinstance(callout.text, (list, tuple)) else str(callout.text)
        
        parts.append(f"\\begin{{{env}}}\n{content}\n\\end{{{env}}}")
        
        if hints.keep_together:
            parts.append(r"\end{minipage}")
        if hints.space_after_mm > 0:
            parts.append(f"\\vspace{{{hints.space_after_mm}mm}}")
            
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Preamble  (auto-generated from the immutable theme)
    # ------------------------------------------------------------------

    def _preamble(self) -> str:
        pg = self._theme.page
        ts = self._theme.table_styles.get("default", self._theme.table_styles["default"])
        cl = self._theme.colors
        
        # Configure footer reserve correctly
        # The footskip is typically the distance from the bottom of the text body to the footer.
        # We ensure bottom margin is the physical margin from the paper edge.
        # includeheadfoot can be omitted if we just set bottom = margin_bottom_mm and footskip = footer_reserve_mm.
        # Actually, bottom=25mm means body ends 25mm above page bottom.
        # If footer_reserve_mm is 15mm, we can set bottom=margin_bottom_mm, footskip=footer_reserve_mm
        
        return (
            r"\documentclass[11pt,a4paper]{report}"
            "\n"
            r"\usepackage["
            f"top={pg.margin_top_mm}mm,"
            f"bottom={pg.margin_bottom_mm}mm,"
            f"left={pg.margin_left_mm}mm,"
            f"right={pg.margin_right_mm}mm,"
            f"footskip={pg.footer_reserve_mm}mm"
            r"]{geometry}"
            "\n"
            r"\usepackage{longtable,booktabs,array,multirow,makecell}"
            "\n"
            r"\usepackage{graphicx,float,caption,xcolor,needspace}"
            "\n"
            r"\newenvironment{remark}{\noindent\textbf{Note: }}{}"
            "\n"
            r"\newenvironment{warning}{\noindent\textbf{\textcolor{orange}{Warning: }}}{}"
            "\n"
            r"\newenvironment{info}{\noindent\textbf{Info: }}{}"
            "\n"
            r"\definecolor{primary}{" + cl.primary + "}"
            "\n"
            r"\definecolor{accent}{" + cl.accent + "}"
            "\n"
            r"\setlength{\tabcolsep}{" + str(ts.column_padding_pt) + "pt}"
            "\n"
            r"\begin{document}"
        )
