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
    """Generate a high-quality chart as a PNG file and return its path.

    Parameters
    ----------
    chart:
        The chart component to render.
    theme:
        The report theme (provides DPI, dimensions, colors, etc.).
    output_dir:
        Directory for the output file.  A temporary directory is created
        when *None*.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="osdag_charts_")

    safe_title = chart.title.replace(" ", "_").replace("/", "_")
    path = os.path.join(output_dir, f"{safe_title}.png")

    palette = theme.colors
    chart_style = theme.charts.get("default", theme.charts["default"])
    width_cm = chart.width_cm if chart.width_cm is not None else chart_style.width_cm
    height_cm = chart.height_cm if chart.height_cm is not None else chart_style.height_cm

    # Publication-ready styling
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
    plt.rcParams['font.family'] = 'sans-serif'
    
    fig, ax = plt.subplots(
        figsize=(width_cm / 2.54, height_cm / 2.54),
        facecolor=palette.surface
    )
    ax.set_facecolor(palette.surface)

    # Spines styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(palette.muted)
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_color(palette.muted)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.tick_params(colors=palette.secondary, labelsize=9)

    if chart.chart_type == "barh":
        # Horizontal bar chart for Utilization Ratio Summary (Chapter 5)
        keys = list(chart.data.keys())
        vals = [chart.data[k] if chart.data[k] is not None else np.nan for k in keys]
        
        # Reverse to display top-to-bottom
        keys.reverse()
        vals.reverse()

        colors = []
        for v in vals:
            if np.isnan(v):
                colors.append(palette.unavailable)
            elif chart.threshold_line is not None and v > chart.threshold_line:
                colors.append(palette.error)
            else:
                colors.append(palette.success)

        plot_vals = [0.0 if np.isnan(v) else v for v in vals]
        bars = ax.barh(keys, plot_vals, color=colors, height=0.55, zorder=3, edgecolor=palette.surface, linewidth=1.0)
        
        # Add numeric labels and PASS/FAIL
        valid_vals = [v for v in vals if not np.isnan(v)]
        max_val = max(valid_vals + [1.0]) if valid_vals else 1.0
        for idx, (bar, original_val) in enumerate(zip(bars, vals)):
            y_pos = bar.get_y() + bar.get_height() / 2
            if np.isnan(original_val):
                ax.text(
                    0.03, y_pos, "N/A (Not Designed / Optional)",
                    va='center', ha='left', color=palette.unavailable,
                    fontsize=9.5, fontstyle='italic', zorder=5
                )
            else:
                status = "FAIL" if (chart.threshold_line is not None and original_val > chart.threshold_line) else "PASS"
                text = f"{original_val:.2f}  [{status}]"
                color = palette.error if status == "FAIL" else palette.success
                
                # Position text nicely
                x_pos = original_val + (max_val * 0.02)
                ax.text(
                    x_pos, y_pos, text,
                    va='center', ha='left', color=color,
                    fontsize=10.0, fontweight='bold', zorder=5
                )

        # Subtle vertical grid
        ax.xaxis.grid(True, linestyle='--', color=palette.grid, linewidth=0.8, alpha=0.8, zorder=0)
        
        safe_max = max(max_val, chart.threshold_line if chart.threshold_line else 1.0)
        ax.set_xlim(0, safe_max * 1.25)

        if chart.threshold_line is not None:
            ax.axvline(
                x=chart.threshold_line,
                color=palette.threshold,
                linestyle='--',
                linewidth=1.8,
                zorder=4,
                label=f"Code Limit = {chart.threshold_line:.1f}"
            )
            ax.legend(
                loc='lower right',
                frameon=True,
                facecolor=palette.surface,
                edgecolor=palette.grid,
                fontsize=9.0,
                title="Design Threshold",
                title_fontsize=9.0
            )

    else:
        # Vertical bar charts (Chapter 7 Material Quantities & general metrics)
        raw_keys = list(chart.data.keys())
        vals = [chart.data[k] if chart.data[k] is not None else np.nan for k in raw_keys]
        
        # Uniform brand color for all material bars, neutral gray for N/A
        bar_colors = []
        for k, v in zip(raw_keys, vals):
            if np.isnan(v):
                bar_colors.append(palette.unavailable)
            else:
                bar_colors.append(palette.primary)

        bar_width = 0.45 if len(raw_keys) <= 3 else 0.6
        plot_vals = [0.0 if np.isnan(v) else v for v in vals]
        bars = ax.bar(raw_keys, plot_vals, color=bar_colors, width=bar_width, zorder=3, edgecolor=palette.surface, linewidth=1.2)
        
        # Subtle horizontal grid
        ax.yaxis.grid(True, linestyle='--', color=palette.grid, linewidth=0.8, alpha=0.8, zorder=0)

        # Calculate max value for nice y-limit headroom
        valid_vals = [v for v in vals if not np.isnan(v)]
        max_y = max(valid_vals) if valid_vals else 10.0
        ax.set_ylim(0, max_y * 1.25 if max_y > 0 else 1.0)

        # Annotations on top of each bar
        total_sum = sum(valid_vals) if valid_vals else 0.0
        for idx, (bar, original_val) in enumerate(zip(bars, vals)):
            x_pos = bar.get_x() + bar.get_width() / 2
            if np.isnan(original_val):
                ax.text(
                    x_pos, 0.04 * max_y if max_y > 0 else 0.5, "N/A",
                    ha='center', va='bottom', color=palette.unavailable,
                    fontsize=9.5, fontweight='bold', fontstyle='italic', zorder=5
                )
            else:
                val_str = f"{original_val:.2f}"
                pct_str = f" ({original_val/total_sum*100:.1f}%)" if (total_sum > 0 and len(raw_keys) > 1 and "Total" not in chart.title) else ""
                
                label_text = f"{val_str}{pct_str}"
                ax.text(
                    x_pos, original_val + (max_y * 0.02),
                    label_text,
                    ha='center', va='bottom', color=palette.secondary,
                    fontsize=9.5, fontweight='bold', zorder=5
                )

        if chart.threshold_line is not None:
            ax.axhline(
                y=chart.threshold_line,
                color=palette.threshold,
                linestyle='--',
                linewidth=1.8,
                zorder=4,
                label=f"Threshold={chart.threshold_line}",
            )
            ax.legend(loc='upper right', frameon=True, facecolor=palette.surface, edgecolor=palette.grid, fontsize=8.5)

        # Keep labels horizontal if few bars; rotate only if many
        if len(raw_keys) > 3:
            plt.setp(ax.get_xticklabels(), rotation=20, ha="right", fontsize=9)
        else:
            plt.setp(ax.get_xticklabels(), rotation=0, ha="center", fontsize=9.5, fontweight='bold')

    if chart.x_label:
        ax.set_xlabel(chart.x_label, fontsize=9.5, fontweight='bold', color=palette.secondary, labelpad=8)
    if chart.y_label:
        ax.set_ylabel(chart.y_label, fontsize=9.5, fontweight='bold', color=palette.secondary, labelpad=8)

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            plt.tight_layout()
        except Exception:
            pass

    fig.savefig(path, dpi=chart_style.dpi, bbox_inches='tight')
    plt.close(fig)

    return path
