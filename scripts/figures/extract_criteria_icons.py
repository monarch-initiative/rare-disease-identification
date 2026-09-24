"""Cut the six criterion glyphs out of the prioritisation-workflow figure.

The workflow figure (Figure X, "Workflow for prioritizing rare diseases for
Phase I data collection") draws the six criteria as a donut, each wedge in its
own colour with a white glyph in the middle of the wedge. This script lifts
each glyph out as a standalone transparent PNG tinted in its wedge colour, so
the website and the upset plot can label sections with the same iconography the
paper uses.

Method: a wedge is a solid block of one exact colour. The glyph is the only
white region *fully enclosed* by that wedge, so a per-wedge hole fill isolates
it -- the donut's central circle escapes through the white gaps between wedges
and is therefore not a hole of any single wedge.

These are stopgap crops of a raster figure. Replace them with the hi-res
originals when those arrive; nothing else needs to change, the filenames are
the contract.
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import click
import numpy as np
import yaml
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rare_disease_identification.criteria import load_criteria  # noqa: E402


def _exact_colour_mask(arr: np.ndarray, rgb: tuple[int, int, int]) -> np.ndarray:
    return np.all(arr[..., :3] == np.array(rgb, dtype=np.uint8), axis=-1)


def _holes(mask: np.ndarray) -> np.ndarray:
    """Pixels not in `mask` that cannot reach the array border without crossing it."""
    h, w = mask.shape
    outside = np.zeros_like(mask)
    q: deque[tuple[int, int]] = deque()

    def push(y: int, x: int) -> None:
        if not mask[y, x] and not outside[y, x]:
            outside[y, x] = True
            q.append((y, x))

    for x in range(w):
        push(0, x)
        push(h - 1, x)
    for y in range(h):
        push(y, 0)
        push(y, w - 1)
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                push(ny, nx)
    return ~mask & ~outside


def _glyph_png(arr: np.ndarray, hole: np.ndarray, rgb: tuple[int, int, int], size: int, pad: int) -> Image.Image:
    ys, xs = np.nonzero(hole)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1

    # Alpha from how white the pixel is, so anti-aliased glyph edges survive the
    # recolour instead of turning into a hard, jagged cut-out.
    sub = arr[y0:y1, x0:x1, :3].astype(np.float32)
    alpha = (sub.min(axis=-1) / 255.0) * hole[y0:y1, x0:x1]

    out = np.zeros((*alpha.shape, 4), dtype=np.uint8)
    out[..., 0], out[..., 1], out[..., 2] = rgb
    out[..., 3] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)

    glyph = Image.fromarray(out, "RGBA")
    # Scale to fill the box rather than thumbnail(), which only ever shrinks: the
    # source glyphs are ~100px and would otherwise sit in a mostly-empty canvas,
    # so every icon would render a third of its intended size on the site.
    box = size - 2 * pad
    scale = box / max(glyph.width, glyph.height)
    glyph = glyph.resize((max(1, round(glyph.width * scale)), max(1, round(glyph.height * scale))),
                         Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(glyph, ((size - glyph.width) // 2, (size - glyph.height) // 2))
    return canvas


@click.command()
@click.option("--figure", required=True, type=click.Path(exists=True, path_type=Path),
              help="Workflow figure PNG (word/media/image4.png inside the manuscript docx).")
@click.option("--criteria", "criteria_path", default="config/prioritisation_criteria.yaml",
              type=click.Path(exists=True, path_type=Path), show_default=True)
@click.option("--output-dir", "-o", default="site/assets/criteria",
              type=click.Path(path_type=Path), show_default=True)
@click.option("--size", default=256, show_default=True, help="Output canvas edge, px.")
@click.option("--pad", default=16, show_default=True, help="Transparent margin inside the canvas, px.")
def main(figure: Path, criteria_path: Path, output_dir: Path, size: int, pad: int) -> None:
    """Write one <criterion id>.png per criterion into OUTPUT_DIR."""
    spec = load_criteria(criteria_path)
    arr = np.array(Image.open(figure).convert("RGBA"))
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = {}
    for crit in spec.criteria:
        rgb = tuple(int(crit.colour.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        mask = _exact_colour_mask(arr, rgb)
        if not mask.any():
            raise click.ClickException(
                f"{crit.id}: no pixel of {crit.colour} in {figure}; the figure was re-rendered "
                "and the wedge colours in the criteria config need updating."
            )
        hole = _holes(mask)
        if not hole.any():
            raise click.ClickException(f"{crit.id}: wedge {crit.colour} enclosed no glyph.")
        path = output_dir / f"{crit.id}.png"
        _glyph_png(arr, hole, rgb, size, pad).save(path)
        manifest[crit.id] = {"file": path.name, "colour": crit.colour, "glyph_px": int(hole.sum())}
        click.echo(f"{crit.id:26s} {crit.colour}  {int(hole.sum()):6d} glyph px -> {path}")

    (output_dir / "manifest.yaml").write_text(
        "# Generated by scripts/figures/extract_criteria_icons.py -- do not edit.\n"
        + yaml.safe_dump(manifest, sort_keys=True)
    )


if __name__ == "__main__":
    main()
