"""Render the criteria config as a self-contained, shareable HTML report.

Same source as everything else: `config/prioritisation_criteria.yaml` supplies the
criteria, their prose and their rules; `criteria.json` supplies the counts. The
glyphs and the upset figures are embedded as data URIs, so the file can be mailed,
attached or published without carrying a folder of assets behind it.

Run as `python -m rare_disease_identification.build_criteria_report`, or
`just criteria-report`.
"""

from __future__ import annotations

import base64
import html
import io
import json
import re
from pathlib import Path

import click

from .criteria import load_criteria

TIER_NOTE = {
    "direct": "the registry field was recorded in order to say this",
    "derived": "computed from structured registry data",
    "proxy": "the field says something adjacent; this reads across a gap",
}


def _lighten(hex_colour: str, amount: float) -> str:
    """Mix a colour toward white. Criterion 2's navy is invisible on a dark ground."""
    r, g, b = (int(hex_colour.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    mix = lambda c: round(c + (255 - c) * amount)  # noqa: E731
    return f"#{mix(r):02x}{mix(g):02x}{mix(b):02x}"


def _data_uri(path: Path, max_px: int | None = None) -> str:
    raw = path.read_bytes()
    if max_px:
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(raw))
            if max(img.size) > max_px:
                img.thumbnail((max_px, max_px), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                raw = buf.getvalue()
        except ImportError:
            pass
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


def e(text: str) -> str:
    return html.escape(str(text or ""))


def rich(text: str) -> str:
    """Escape, then honour the light markdown the config's prose is written in.

    The coverage notes and caveats name fields as `backticked` code and stress
    terms with *asterisks*; rendered literally those marks read as typos.
    """
    out = e(text)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", out)
    return out


CSS = """
:root {
  --bg: #f4f2ec;
  --surface: #ffffff;
  --surface-sunk: #eeebe2;
  --ink: #1f2a33;
  --muted: #5d6970;
  --rule: #ddd8cb;
  --rule-strong: #c7c0ae;
  --caution: #a8651a;
  --caution-bg: #fdf6e8;
  --caution-rule: #dfba78;
  --code-bg: #f0ede4;
}
:root:not([data-theme="light"]) {
  color-scheme: light dark;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #171b1f;
    --surface: #1f252a;
    --surface-sunk: #262d33;
    --ink: #e8e5dc;
    --muted: #9ba5ac;
    --rule: #333b42;
    --rule-strong: #4a545c;
    --caution: #e9b968;
    --caution-bg: #2b2418;
    --caution-rule: #6b5526;
    --code-bg: #262d33;
  }
}
:root[data-theme="dark"] {
  --bg: #171b1f;
  --surface: #1f252a;
  --surface-sunk: #262d33;
  --ink: #e8e5dc;
  --muted: #9ba5ac;
  --rule: #333b42;
  --rule-strong: #4a545c;
  --caution: #e9b968;
  --caution-bg: #2b2418;
  --caution-rule: #6b5526;
  --code-bg: #262d33;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: "Source Sans 3", ui-sans-serif, system-ui, sans-serif;
  font-size: 16px;
  line-height: 1.6;
}

.wrap {
  max-width: 1080px;
  margin: 0 auto;
  padding-block: 2.5rem 4rem;
  padding-left: 1.25rem;
  padding-right: 1.25rem;
}

h1, h2, h3 {
  font-family: "Oswald", "Arial Narrow", ui-sans-serif, sans-serif;
  font-weight: 500;
  text-wrap: balance;
  margin: 0;
}
h1 { font-size: clamp(2rem, 5vw, 2.9rem); line-height: 1.08; letter-spacing: 0.004em; }
h2 { font-size: 1.5rem; line-height: 1.2; }
h3 { font-size: 1.15rem; line-height: 1.25; }
p { margin: 0; }
a { color: inherit; text-underline-offset: 2px; text-decoration-color: var(--rule-strong); }
a:hover { text-decoration-color: currentColor; }
:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }

/* ---- masthead ---- */
.masthead { display: grid; gap: 0.9rem; padding-bottom: 1.6rem; border-bottom: 2px solid var(--ink); }
.eyebrow {
  font-family: "Oswald", sans-serif;
  font-size: 0.82rem;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  color: var(--muted);
}
.lede { max-width: 66ch; color: var(--muted); font-size: 1.06rem; }
.meta { display: flex; flex-wrap: wrap; gap: 0.4rem 1.4rem; font-size: 0.84rem; color: var(--muted); }
.meta strong { color: var(--ink); font-weight: 600; }

/* ---- criterion index ---- */
.index { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.9rem; margin-top: 1.8rem; }
.index-card {
  --tone: var(--c);
  display: grid;
  grid-template-columns: 40px 1fr;
  gap: 0.2rem 0.85rem;
  align-items: center;
  padding: 0.85rem 0.95rem;
  background: var(--surface);
  border: 1px solid var(--rule);
  border-left: 4px solid var(--tone);
  text-decoration: none;
}
.index-card img { grid-row: span 2; width: 34px; height: 34px; }
.index-name { font-family: "Oswald", sans-serif; font-size: 1.02rem; display: flex; gap: 0.45rem; align-items: baseline; }
.index-num { color: var(--tone); font-size: 1.3rem; font-weight: 600; }
.index-card:hover { border-color: var(--tone); }

/* The single most reviewable fact, drawn rather than tabulated: solid is what the
   registry records, translucent is how much further inference carries it. */
.rail { position: relative; height: 7px; background: var(--rule); margin-top: 0.15rem; }
.rail span { position: absolute; inset-block: 0; left: 0; background: var(--tone); }
.rail .all { opacity: 0.35; }
.rail-note { font-size: 0.76rem; color: var(--muted); font-variant-numeric: tabular-nums; }

.legend {
  display: flex; flex-wrap: wrap; gap: 0.5rem 1.2rem;
  margin-top: 0.9rem; font-size: 0.8rem; color: var(--muted);
}
.legend i { display: inline-block; width: 22px; height: 7px; background: var(--ink); vertical-align: middle; margin-right: 0.4rem; }
.legend i.faint { opacity: 0.35; }

/* ---- generic blocks ---- */
section { margin-top: 3rem; }
.prose { max-width: 68ch; display: grid; gap: 0.8rem; margin-top: 0.8rem; }

.caveats {
  margin-top: 1.8rem;
  background: var(--caution-bg);
  border: 1px solid var(--caution-rule);
  border-left: 4px solid var(--caution);
  padding: 1rem 1.2rem;
}
.caveats h2 { color: var(--caution); font-size: 1.2rem; }
.caveats p { margin-top: 0.5rem; max-width: 74ch; }

code, .expr {
  font-family: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  font-size: 0.85em;
  background: var(--code-bg);
  padding: 0.08em 0.35em;
  border-radius: 2px;
}
.expr { display: block; padding: 0.6rem 0.8rem; font-size: 0.85rem; line-height: 1.5; overflow-x: auto; }

/* ---- tables ---- */
.scroll { overflow-x: auto; margin-top: 1rem; }
table { border-collapse: collapse; width: 100%; font-size: 0.87rem; }
th, td { text-align: left; padding: 0.5rem 0.7rem; border-bottom: 1px solid var(--rule); vertical-align: top; }
th {
  font-family: "Oswald", sans-serif; font-weight: 400;
  font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--muted); border-bottom: 1px solid var(--rule-strong); white-space: nowrap;
}
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
tbody tr:last-child td { border-bottom: none; }

.tier {
  display: inline-block; font-size: 0.7rem; letter-spacing: 0.04em; text-transform: uppercase;
  padding: 0.05rem 0.4rem; border: 1px solid var(--rule-strong); color: var(--muted); white-space: nowrap;
}
.tier.direct { border-color: var(--tone); color: var(--tone); }
.tier.derived { border-style: dashed; border-color: var(--tone); color: var(--tone); }
.tier.proxy { border-style: dotted; }

/* ---- criterion sections ---- */
.criterion { --tone: var(--c); margin-top: 3.2rem; scroll-margin-top: 1rem; }
.crit-head { display: grid; grid-template-columns: 48px 1fr auto; gap: 0.2rem 1rem; align-items: center; }
.crit-head img { grid-row: span 2; width: 44px; height: 44px; }
.crit-title { font-family: "Oswald", sans-serif; font-size: 1.55rem; display: flex; gap: 0.55rem; align-items: baseline; }
.crit-num { color: var(--tone); font-size: 2rem; font-weight: 600; line-height: 1; }
.crit-tagline { grid-column: 2; color: var(--muted); font-size: 0.92rem; }
.crit-score { grid-row: span 2; text-align: right; font-variant-numeric: tabular-nums; }
.crit-score b { font-family: "Oswald", sans-serif; font-size: 1.7rem; font-weight: 500; color: var(--tone); display: block; line-height: 1; }
.crit-score span { font-size: 0.78rem; color: var(--muted); }
.crit-rule { height: 3px; background: var(--tone); margin-top: 0.8rem; }

.status {
  display: inline-block; margin-top: 0.9rem; font-size: 0.78rem; color: var(--muted);
}
.status b { color: var(--ink); font-weight: 600; }

/* The coverage note is where the weakness of each assignment is stated, so it gets
   weight instead of being filed away as a grey aside. */
.coverage {
  margin-top: 1.2rem;
  border-left: 4px solid var(--tone);
  background: var(--surface);
  border-top: 1px solid var(--rule);
  border-right: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
  padding: 0.9rem 1.1rem;
  max-width: 74ch;
}
.coverage h3 { font-size: 0.82rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--tone); }
.coverage p { margin-top: 0.4rem; }

figure { margin: 1.4rem 0 0; }
figure img { width: 100%; max-width: 100%; height: auto; border: 1px solid var(--rule); background: #fff; }
figcaption { margin-top: 0.5rem; font-size: 0.82rem; color: var(--muted); max-width: 74ch; }

footer { margin-top: 3.5rem; padding-top: 1.2rem; border-top: 1px solid var(--rule); font-size: 0.82rem; color: var(--muted); }

@media (max-width: 560px) {
  .crit-head { grid-template-columns: 36px 1fr; }
  .crit-head img { width: 34px; height: 34px; }
  .crit-score { grid-row: auto; grid-column: 1 / -1; text-align: left; margin-top: 0.4rem; }
  .crit-score b { display: inline; font-size: 1.3rem; }
}
"""


def render(spec, payload: dict, icon_dir: Path, figure_dir: Path, fragment: bool = False) -> str:
    """Build the report.

    `fragment` drops the document wrapper and emits title, font link, style and
    content only. That is the shape the Artifact publisher wants, since it supplies
    its own doctype, head and body; the standalone file keeps the wrapper so it can
    be opened from disk.
    """
    total = payload["n_diseases"]
    by_id = {c["id"]: c for c in payload["criteria"]}
    icons = {c.id: _data_uri(icon_dir / c.icon, max_px=96) for c in spec.criteria
             if (icon_dir / c.icon).exists()}

    tones = "\n".join(
        f'  .c-{c.number} {{ --c: {c.colour}; }}\n'
        f'  @media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .c-{c.number} '
        f'{{ --c: {_lighten(c.colour, 0.38)}; }} }}\n'
        f'  :root[data-theme="dark"] .c-{c.number} {{ --c: {_lighten(c.colour, 0.38)}; }}'
        for c in spec.criteria
    )

    out: list[str] = []
    add = out.append

    if not fragment:
        add('<!doctype html><html lang="en"><head><meta charset="utf-8">')
        add('<meta name="viewport" content="width=device-width, initial-scale=1">')
    add("<title>Six Criteria, Read Off the Registry</title>")
    add('<link rel="preconnect" href="https://fonts.googleapis.com">')
    add('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    add('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        'family=Oswald:wght@400;500;600&family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&display=swap">')
    add(f"<style>{CSS}\n{tones}\n</style>")
    if not fragment:
        add("</head><body>")
    add('<div class="wrap">')

    # ---- masthead
    add('<header class="masthead">')
    add('<p class="eyebrow">Rare disease prioritisation &middot; criteria assignment</p>')
    add("<h1>Six criteria, read off the registry</h1>")
    add(f'<p class="lede">The manuscript prioritises rare diseases on six criteria. The registry was '
        f'not built around them. This is the mapping between the two, field by field, with the places '
        f'it is weakest written down rather than smoothed over.</p>')
    add('<div class="meta">')
    add(f"<span><strong>{total:,}</strong> diseases</span>")
    add(f"<span><strong>{len(spec.criteria)}</strong> criteria</span>")
    add(f"<span><strong>{sum(len(c.signals) for c in spec.criteria)}</strong> signals</span>")
    add(f"<span>Criteria version <strong>{e(payload['criteria_version'])}</strong></span>")
    add(f"<span>Evaluated <strong>{e(payload['generated_on'])}</strong></span>")
    add("</div></header>")

    # ---- index
    add('<div class="index">')
    for c in spec.criteria:
        d = by_id[c.id]
        icon = f'<img src="{icons[c.id]}" alt="">' if c.id in icons else ""
        add(f'<a class="index-card c-{c.number}" href="#{e(c.id)}">{icon}'
            f'<div><div class="index-name"><span class="index-num">{c.number}</span>{e(c.label)}</div>'
            f'<div class="rail"><span class="all" style="width:{d["pct_satisfied"]}%"></span>'
            f'<span style="width:{d["pct_satisfied_direct"]}%"></span></div>'
            f'<div class="rail-note">{d["n_satisfied"]:,} met &middot; '
            f'{d["n_satisfied_direct"]:,} on recorded evidence</div></div></a>')
    add("</div>")
    add('<p class="legend"><span><i></i>Met on evidence the registry records</span>'
        '<span><i class="faint"></i>Met only once inferred signals are allowed</span></p>')

    # ---- caveats
    add('<div class="caveats"><h2>Push back on these first</h2>')
    add(f"<p>{rich(spec.narrative.get('caveats', ''))}</p></div>")

    # ---- how to read
    add("<section><h2>How to read this</h2><div class=\"prose\">")
    add(f"<p>{rich(spec.narrative.get('purpose', ''))}</p>")
    add(f"<p>{rich(spec.narrative.get('how_to_read', ''))}</p>")
    add("</div></section>")

    # ---- per criterion
    for c in spec.criteria:
        d = by_id[c.id]
        icon = f'<img src="{icons[c.id]}" alt="">' if c.id in icons else ""
        add(f'<section class="criterion c-{c.number}" id="{e(c.id)}">')
        add(f'<div class="crit-head">{icon}'
            f'<div class="crit-title"><span class="crit-num">{c.number}</span>{e(c.label)}</div>'
            f'<div class="crit-score"><b>{d["pct_satisfied"]}%</b>'
            f'<span>{d["n_satisfied"]:,} of {total:,}</span></div>'
            f'<p class="crit-tagline">{e(c.tagline)}</p></div>')
        add('<div class="crit-rule"></div>')
        add(f'<div class="prose"><p>{rich(c.rationale)}</p>'
            f'<p><b>How it was curated.</b> {rich(c.curation_method)}</p></div>')
        add(f'<p class="status">Evidence: <b>{e(c.evidence_status.replace("_", " "))}</b> &mdash; '
            f'{e(spec.evidence_status_labels.get(c.evidence_status, "").lower())}. '
            f'On recorded evidence alone, with every inferred signal switched off: '
            f'<b>{d["n_satisfied_direct"]:,}</b> ({d["pct_satisfied_direct"]}%).</p>')
        add(f'<code class="expr">satisfied_when: {e(d["satisfied_when"])}</code>')

        add('<div class="scroll"><table><thead><tr>'
            '<th>Signal</th><th>Sub</th><th>Evidence</th><th>Registry field</th>'
            '<th class="num">Fires on</th><th>What it means</th>'
            "</tr></thead><tbody>")
        for s, sd in zip(c.signals, d["signals"]):
            sub = e(s.subcriterion) if s.subcriterion else "&mdash;"
            fieldname = f"<code>{e(sd['field'])}</code>" if sd["field"] else "&mdash;"
            add(f"<tr><td>{e(s.label)}</td><td>{sub}</td>"
                f'<td><span class="tier {e(s.tier)}" title="{e(TIER_NOTE.get(s.tier, ""))}">{e(s.tier)}</span></td>'
                f'<td>{fieldname}</td><td class="num">{sd["n_fired"]:,}</td>'
                f"<td>{rich(s.description)}</td></tr>")
        add("</tbody></table></div>")

        add(f'<div class="coverage"><h3>Where this is weak</h3><p>{rich(c.coverage_note)}</p></div>')
        add("</section>")

    # ---- figures
    add("<section><h2>Every combination, counted once</h2>")
    for stem, caption in (
        ("criteria_upset",
         "Each column is one combination of criteria. The dots say which criteria it contains; "
         "the bar says how many diseases meet exactly that combination and no more. Every disease "
         "appears in exactly one column."),
        ("criteria_upset_direct_evidence",
         "The same diseases and the same criteria, with every inferred signal switched off. "
         "Criterion 5 empties out completely: nothing in the registry records it."),
    ):
        path = figure_dir / f"{stem}.png"
        if path.exists():
            add(f'<figure><img src="{_data_uri(path)}" alt="{e(caption)}">'
                f"<figcaption>{e(caption)}</figcaption></figure>")
    add("</section>")

    # ---- omissions
    if spec.not_rendered:
        add("<section><h2>Shown nowhere on the site</h2>")
        add('<div class="scroll"><table><thead><tr><th>Field</th><th>Why</th></tr></thead><tbody>')
        for entry in spec.not_rendered:
            add(f'<tr><td><code>{e(entry["field"])}</code></td><td>{rich(entry["reason"])}</td></tr>')
        add("</tbody></table></div></section>")

    if spec.unassigned_fields:
        add("<section><h2>Counted as evidence for nothing</h2>")
        add('<div class="prose"><p>These registry fields carry data and are displayed, but no '
            "criterion reads them. Each exclusion is a decision, not an oversight.</p></div>")
        add('<div class="scroll"><table><thead><tr><th>Field</th>'
            "<th>Why it is not criterion evidence</th></tr></thead><tbody>")
        for entry in spec.unassigned_fields:
            add(f'<tr><td><code>{e(entry["field"])}</code></td><td>{rich(entry["reason"])}</td></tr>')
        add("</tbody></table></div></section>")

    add(f'<footer><p>Generated from <code>config/prioritisation_criteria.yaml</code> and '
        f"<code>criteria.json</code>. Source of the criteria: {e(spec.source_document)} "
        f"Regenerate with <code>just criteria-report</code>.</p></footer>")
    add("</div>" if fragment else "</div></body></html>")
    return "\n".join(out)


@click.command()
@click.option("--criteria", "-c", "criteria_path", default="config/prioritisation_criteria.yaml",
              type=click.Path(exists=True, path_type=Path), show_default=True)
@click.option("--criteria-json", "-i", default="criteria.json",
              type=click.Path(exists=True, path_type=Path), show_default=True)
@click.option("--icon-dir", default="site/assets/criteria",
              type=click.Path(path_type=Path), show_default=True)
@click.option("--figure-dir", default="docs/figures",
              type=click.Path(path_type=Path), show_default=True)
@click.option("--output", "-o", default="docs/criteria-report.html",
              type=click.Path(path_type=Path), show_default=True)
@click.option("--fragment", is_flag=True,
              help="Omit the document wrapper, for publishers that supply their own.")
def main(criteria_path: Path, criteria_json: Path, icon_dir: Path,
         figure_dir: Path, output: Path, fragment: bool) -> None:
    """Write a self-contained HTML report of the six prioritisation criteria."""
    spec = load_criteria(criteria_path)
    payload = json.loads(criteria_json.read_text())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(spec, payload, icon_dir, figure_dir, fragment=fragment))
    click.echo(f"wrote {output} ({output.stat().st_size / 1024:.0f} KB, self-contained)")


if __name__ == "__main__":
    main()
