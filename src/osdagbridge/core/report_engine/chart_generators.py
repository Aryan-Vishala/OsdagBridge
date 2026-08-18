# =============================================================================
# Chart generators — matplotlib helpers for report charts.
#
# These are *implementation services* of the renderer, not core architectural
# concepts.  The renderer calls generate_chart(); it never owns engineering
# logic.
# =============================================================================

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .document import Chart
    from .theme import ReportTheme


def generate_chart(
    chart: Chart,
    theme: ReportTheme,
    output_dir: str | None = None,
) -> str:
    """Generate a chart as a PNG file and return its path.

    Parameters
    ----------
    chart:
        The chart component to render.
    theme:
        The report theme (provides DPI, dimensions, etc.).
    output_dir:
        Directory for the output file.  A temporary directory is created
        when *None*.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="osdag_charts_")

    safe_title = chart.title.replace(" ", "_").replace("/", "_")
    path = os.path.join(output_dir, f"{safe_title}.png")

    fig, ax = plt.subplots(
        figsize=(theme.chart.width_cm / 2.54, theme.chart.height_cm / 2.54),
    )

    if chart.chart_type == "bar":
        ax.bar(chart.data.keys(), chart.data.values(), color="steelblue")
    elif chart.chart_type == "grouped_bar":
        # Grouped bar — for now, single-series fallback.
        ax.bar(chart.data.keys(), chart.data.values(), color="steelblue")

    if chart.threshold_line is not None:
        ax.axhline(
            y=chart.threshold_line,
            color="r",
            linestyle="--",
            linewidth=2,
            label=f"Threshold={chart.threshold_line}",
        )
        ax.legend()

    ax.set_title(chart.title, fontsize=theme.chart.title_font_size)
    if chart.x_label:
        ax.set_xlabel(chart.x_label)
    if chart.y_label:
        ax.set_ylabel(chart.y_label)

    plt.tight_layout()
    fig.savefig(path, dpi=theme.chart.dpi)
    plt.close(fig)

    return path
