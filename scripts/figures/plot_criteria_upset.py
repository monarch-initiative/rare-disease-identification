"""Upset plot of the six prioritisation criteria over the registry.

Reads `criteria.json` (written by `just build-criteria`), so the set membership
plotted here is exactly the membership the website shows and the review document
describes. Nothing about which registry field means which criterion is decided
in this file -- see `config/prioritisation_criteria.yaml`.

Outputs, into --output-dir:

  criteria_upset.png / .svg               all six criteria
  criteria_upset_discriminating.png/.svg  criteria that are neither near-empty nor
                                          near-saturated, i.e. the ones that
                                          actually partition the registry
  criteria_intersections.tsv              every intersection and its size

The upset is drawn directly rather than via the `upsetplot` package: that
package's latest release mutates its style frame with `Series.fillna(inplace=
True)`, which is a silent no-op under pandas 3 and leaves NaN where matplotlib
expects a colour. Drawing it here is about eighty lines and lets the figure carry
the workflow figure's own wedge colours and glyphs.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import click
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402
from matplotlib.offsetbox import AnnotationBbox, OffsetImage  # noqa: E402

DOT_ON = "#3f4e5a"
DOT_OFF = "#dcdad4"
BAR = "#3f4e5a"
SHADE = "#f4f2ec"
MUTED = "#6b6b68"


def load_membership(payload: dict, key: str = "met") -> tuple[pd.DataFrame, list[dict]]:
    """Boolean disease x criterion frame, column order following criterion number.

    `key` picks which evaluation to plot: "met" is the full one, "met_direct"
    re-runs it with proxy signals switched off.
    """
    criteria = sorted(payload["criteria"], key=lambda c: c["number"])
    names = [f"{c['number']}. {c['short_label']}" for c in criteria]
    rows = {
        mondo_id: [c["id"] in set(a[key]) for c in criteria]
        for mondo_id, a in payload["assignments"].items()
    }
    return pd.DataFrame.from_dict(rows, orient="index", columns=names), criteria


def intersections_table(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per observed combination of criteria, largest first."""
    cols = list(frame.columns)
    grouped = frame.groupby(cols, observed=True).size().reset_index(name="n_diseases")
    grouped = grouped.sort_values("n_diseases", ascending=False).reset_index(drop=True)
    total = len(frame)
    grouped["pct"] = (100.0 * grouped["n_diseases"] / total).round(2)
    grouped["n_criteria_met"] = grouped[cols].sum(axis=1)
    grouped["criteria_met"] = [
        " + ".join(c for c in cols if row[c]) or "(none)" for _, row in grouped.iterrows()
    ]
    return grouped


def draw(frame: pd.DataFrame, criteria: list[dict], title: str, subtitle: str,
         icon_dir: Path, max_subsets: int, min_subset_size: int) -> plt.Figure:
    cols = list(frame.columns)
    table = intersections_table(frame)
    if min_subset_size:
        table = table[table["n_diseases"] >= min_subset_size]
    shown = table.head(max_subsets) if max_subsets else table
    hidden = len(table) - len(shown)

    n_rows, n_cols = len(cols), len(shown)
    totals = [int(frame[c].sum()) for c in cols]

    # Three columns: per-criterion totals, a label strip carrying the glyph and
    # name, then the membership matrix. The label strip exists so a criterion's
    # name sits on its own row -- printed above its bar it reads as belonging to
    # the row above, which is exactly the kind of off-by-one a reader cannot
    # detect from the figure alone.
    fig_w = max(10.0, 0.66 * n_cols + 7.4)
    fig_h = 0.62 * n_rows + 5.0
    fig = plt.figure(figsize=(fig_w, fig_h))
    gs = GridSpec(
        2, 3, figure=fig,
        width_ratios=[2.0, 2.3, max(3.0, 0.46 * n_cols)],
        height_ratios=[2.6, 0.46 * n_rows + 0.2],
        wspace=0.04, hspace=0.05,
        left=0.03, right=0.985, top=0.82, bottom=0.08,
    )
    ax_note = fig.add_subplot(gs[0, 0:2])
    ax_note.axis("off")
    ax_bars = fig.add_subplot(gs[0, 2])
    ax_matrix = fig.add_subplot(gs[1, 2], sharex=ax_bars)
    ax_labels = fig.add_subplot(gs[1, 1], sharey=ax_matrix)
    ax_totals = fig.add_subplot(gs[1, 0], sharey=ax_matrix)
    ax_labels.axis("off")

    x = range(n_cols)

    # -- intersection sizes
    ax_bars.bar(x, shown["n_diseases"], width=0.62, color=BAR, linewidth=0)
    top = max(shown["n_diseases"]) if n_cols else 1
    for xi, v in zip(x, shown["n_diseases"]):
        ax_bars.text(xi, v + top * 0.02, f"{v:,}", ha="center", va="bottom",
                     fontsize=8.5, color="#3a3a38")
    ax_bars.set_ylim(0, top * 1.16)
    ax_bars.set_ylabel("Diseases in\nthis combination", fontsize=9.5)
    ax_bars.tick_params(axis="x", which="both", length=0, labelbottom=False)
    ax_bars.tick_params(axis="y", labelsize=8.5)
    for side in ("top", "right", "bottom"):
        ax_bars.spines[side].set_visible(False)
    ax_bars.grid(axis="y", color="#e8e6e0", linewidth=0.8)
    ax_bars.set_axisbelow(True)

    # -- membership matrix
    for row in range(n_rows):
        if row % 2 == 0:
            ax_matrix.axhspan(row - 0.5, row + 0.5, color=SHADE, zorder=0)
    for xi, (_, row) in zip(x, shown.iterrows()):
        on = [r for r in range(n_rows) if row[cols[r]]]
        ax_matrix.scatter([xi] * n_rows, range(n_rows), s=110, color=DOT_OFF, zorder=2)
        if on:
            ax_matrix.plot([xi, xi], [min(on), max(on)], color=DOT_ON, linewidth=2.0, zorder=3)
            ax_matrix.scatter([xi] * len(on), on, s=110, color=DOT_ON, zorder=4)
    ax_matrix.set_ylim(n_rows - 0.5, -0.5)
    ax_matrix.set_xlim(-0.7, n_cols - 0.3)
    ax_matrix.set_yticks(range(n_rows))
    ax_matrix.set_yticklabels([])
    ax_matrix.set_xticks([])
    for side in ("top", "right", "bottom", "left"):
        ax_matrix.spines[side].set_visible(False)
    ax_matrix.tick_params(length=0)

    # -- per-criterion totals, in the wedge colours of the workflow figure. The
    # x axis runs right-to-left so the bars grow away from the matrix.
    ax_totals.barh(range(n_rows), totals, height=0.62,
                   color=[c["colour"] for c in criteria], linewidth=0)
    widest = max(totals) if totals else 1
    for row, value in enumerate(totals):
        ax_totals.text(value + widest * 0.035, row, f"{value:,}", va="center", ha="right",
                       fontsize=8.5, color="#3a3a38")
    ax_totals.set_xlim(widest * 1.22, 0)
    ax_totals.set_xlabel("Diseases meeting\nthe criterion", fontsize=9)
    ax_totals.tick_params(axis="x", labelsize=8)
    ax_totals.tick_params(axis="y", length=0, labelleft=False)
    for side in ("top", "right", "left"):
        ax_totals.spines[side].set_visible(False)
    ax_totals.grid(axis="x", color="#e8e6e0", linewidth=0.8)
    ax_totals.set_axisbelow(True)

    # -- label strip: glyph cut from the same workflow figure, then the name
    ax_labels.set_xlim(0, 1)
    for row, crit in enumerate(criteria):
        path = icon_dir / crit["icon"]
        if icon_dir.is_dir() and path.exists():
            ax_labels.add_artist(
                AnnotationBbox(
                    OffsetImage(mpimg.imread(path), zoom=0.075), (0.06, row),
                    xycoords=("data", "data"), box_alignment=(0.5, 0.5),
                    frameon=False, annotation_clip=False,
                )
            )
        ax_labels.text(0.14, row, f"{crit['number']}. {crit['label']}", va="center",
                       ha="left", fontsize=10, fontweight="bold", color="#2b2b29")
        ax_labels.text(0.14, row + 0.30, textwrap.shorten(crit["tagline"], 44, placeholder="\u2026"),
                       va="center", ha="left", fontsize=7.6, color=MUTED)

    ax_note.text(0.0, 0.46, "How to read this", transform=ax_note.transAxes,
                 ha="left", va="top", fontsize=9.4, fontweight="bold", color="#3a3a38")
    ax_note.text(
        0.0, 0.36,
        "Each column is one combination of criteria. The dots say which criteria\n"
        "that combination contains; the bar above says how many diseases meet\n"
        "exactly that combination and no more. Every disease appears in exactly\n"
        "one column, so the bars sum to the registry. The horizontal bars on the\n"
        "left are the per-criterion totals and do overlap.",
        transform=ax_note.transAxes, ha="left", va="top",
        fontsize=8.6, color=MUTED, linespacing=1.6,
    )

    note = subtitle
    if hidden:
        note += (
            f"\n{hidden} further combination(s) too small to show; "
            "every one of them is in criteria_intersections.tsv."
        )
    fig.text(0.03, 0.975, title, ha="left", va="top",
             fontsize=16, fontweight="bold", color="#1f1f1d")
    fig.text(0.03, 0.935, note, ha="left", va="top",
             fontsize=9, color=MUTED, linespacing=1.55)
    return fig


@click.command()
@click.option("--criteria-json", "-i", default="criteria.json",
              type=click.Path(exists=True, path_type=Path), show_default=True)
@click.option("--icon-dir", default="site/assets/criteria",
              type=click.Path(path_type=Path), show_default=True)
@click.option("--output-dir", "-o", default="docs/figures",
              type=click.Path(path_type=Path), show_default=True)
@click.option("--min-subset-size", default=0, show_default=True,
              help="Drop combinations smaller than this (0 = keep all).")
@click.option("--max-subsets", default=18, show_default=True,
              help="Keep only the N largest combinations (0 = keep all).")
def main(criteria_json: Path, icon_dir: Path, output_dir: Path,
         min_subset_size: int, max_subsets: int) -> None:
    """Render the upset plots and the intersection table."""
    payload = json.loads(criteria_json.read_text())
    output_dir.mkdir(parents=True, exist_ok=True)

    def save(fig: plt.Figure, stem: str) -> None:
        for ext in ("png", "svg"):
            path = output_dir / f"{stem}.{ext}"
            fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
            click.echo(f"wrote {path}")
        plt.close(fig)

    frame, criteria = load_membership(payload, "met")
    total = len(frame)
    subtitle = (
        f"{total:,} prioritised rare diseases, each counted once, in the single combination of criteria it meets.\n"
        f"Criteria version {payload['criteria_version']}, evaluated {payload['generated_on']}. "
        "Which registry field counts as evidence for which criterion: docs/criteria-assignment.md"
    )
    save(draw(frame, criteria, "Prioritisation criteria met, by disease", subtitle,
              icon_dir, max_subsets, min_subset_size), "criteria_upset")

    # Same diseases, same criteria, but every `proxy` signal switched off. The
    # difference between the two figures is the size of the inference the first
    # one rests on -- criterion 6 has no non-proxy signal at all and empties out.
    direct, _ = load_membership(payload, "met_direct")
    sub = (
        "The same diseases and the same criteria, counting only evidence the registry actually records:\n"
        "every signal marked `proxy` in config/prioritisation_criteria.yaml is switched off. The difference\n"
        "between this figure and the previous one is how much of the framework currently rests on inference."
    )
    save(draw(direct, criteria, "Criteria met on recorded evidence alone", sub,
              icon_dir, max_subsets, min_subset_size), "criteria_upset_direct_evidence")

    table = intersections_table(frame)
    path = output_dir / "criteria_intersections.tsv"
    table.to_csv(path, sep="\t", index=False)
    click.echo(f"wrote {path} ({len(table)} combinations)")
    click.echo(table[["criteria_met", "n_criteria_met", "n_diseases", "pct"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
