"""Apply the six prioritisation criteria to the registry.

Writes two artefacts, both generated, neither hand-editable:

  criteria.json                 per-disease criterion membership plus the
                                criterion definitions, consumed by the website
                                and by scripts/figures/plot_criteria_upset.py
  docs/criteria-assignment.md   the review document -- which registry field was
                                taken as evidence for which criterion, with live
                                counts

Run as `python -m rare_disease_identification.build_criteria`, or `just build-criteria`.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

import click

from .criteria import CriteriaSpec, evaluate_all, load_criteria, load_diseases

TIER_LABELS = {
    "direct": "direct",
    "derived": "derived",
    "proxy": "proxy",
}


def _rule_field(rule: dict) -> str:
    """The registry field a rule reads, for the review document's table."""
    if "field" in rule:
        return rule["field"]
    if rule.get("op") == "value_set_tier_non_empty":
        return f"value_sets.{rule['tier']} ({rule['terminology']})"
    return ""


def _counts(spec: CriteriaSpec, assignments: dict) -> tuple[Counter, Counter, Counter]:
    crit_counts: Counter = Counter()
    direct_counts: Counter = Counter()
    signal_counts: Counter = Counter()
    for a in assignments.values():
        crit_counts.update(a["met"])
        direct_counts.update(a["met_direct"])
        signal_counts.update(a["signals"])
    for c in spec.criteria:
        crit_counts.setdefault(c.id, 0)
        direct_counts.setdefault(c.id, 0)
        for s in c.signals:
            signal_counts.setdefault(s.id, 0)
    return crit_counts, direct_counts, signal_counts


def build_payload(spec: CriteriaSpec, diseases: list[dict]) -> dict:
    assignments = evaluate_all(spec, diseases)
    crit_counts, direct_counts, signal_counts = _counts(spec, assignments)
    total = len(diseases)
    return {
        "generated_on": date.today().isoformat(),
        "criteria_version": spec.version,
        "source_figure": spec.figure,
        "n_diseases": total,
        "criteria": [
            {
                "id": c.id,
                "number": c.number,
                "label": c.label,
                "short_label": c.short_label,
                "tagline": c.tagline,
                "colour": c.colour,
                "icon": c.icon,
                "evidence_status": c.evidence_status,
                "evidence_status_label": spec.evidence_status_labels.get(c.evidence_status, ""),
                "rationale": c.rationale,
                "curation_method": c.curation_method,
                "coverage_note": c.coverage_note,
                "satisfied_when": " ".join(c.satisfied_when.split()),
                "display": list(c.display),
                "n_satisfied": crit_counts[c.id],
                "pct_satisfied": round(100.0 * crit_counts[c.id] / total, 1) if total else 0.0,
                "n_satisfied_direct": direct_counts[c.id],
                "pct_satisfied_direct": round(100.0 * direct_counts[c.id] / total, 1) if total else 0.0,
                "signals": [
                    {
                        "id": s.id,
                        "label": s.label,
                        "tier": s.tier,
                        "subcriterion": s.subcriterion,
                        "description": s.description,
                        "field": _rule_field(s.rule),
                        "n_fired": signal_counts[s.id],
                    }
                    for s in c.signals
                ],
            }
            for c in spec.criteria
        ],
        "assignments": assignments,
    }


def unrendered_fields(spec: CriteriaSpec, diseases: list[dict]) -> list[tuple[str, int]]:
    """Registry fields carrying data that the website renders nowhere.

    The six-criterion card layout only shows a field if some criterion's `display`
    block asks for it, or the header / "everything else" block does. A field added
    to the registry later would otherwise vanish from the site without a sound.
    """
    known = spec.rendered_fields() | {e["field"] for e in spec.not_rendered}
    present: Counter = Counter()
    for d in diseases:
        for key, value in d.items():
            if value not in (None, [], "", {}):
                present[key] += 1
    return sorted(
        ((f, n) for f, n in present.items() if f not in known),
        key=lambda pair: -pair[1],
    )


# ---------------------------------------------------------------- review document


def _wrap(text: str) -> str:
    return " ".join(text.split())


def render_report(spec: CriteriaSpec, payload: dict, source: Path) -> str:
    total = payload["n_diseases"]
    lines: list[str] = []
    add = lines.append

    add("# How registry fields map to the six prioritisation criteria")
    add("")
    add(
        "<!-- GENERATED by `just build-criteria`. Edit "
        "`config/prioritisation_criteria.yaml`, not this file. -->"
    )
    add("")
    add(f"- Criteria version `{payload['criteria_version']}`, rendered {payload['generated_on']}")
    add(f"- Source of the criteria: {_wrap(spec.source_document)}")
    add(f"- Evaluated over `{source}` &mdash; {total:,} diseases")
    add("")
    add("## Why this document exists")
    add("")
    add(_wrap(spec.narrative.get("purpose", "")))
    add("")
    add("## How to read the tables")
    add("")
    add(_wrap(spec.narrative.get("how_to_read", "")))
    add("")
    add("## Read these caveats before the tables")
    add("")
    add(_wrap(spec.narrative.get("caveats", "")))
    add("")

    add("## Summary")
    add("")
    add("| # | Criterion | Evidence | Diseases | % | On recorded evidence only |")
    add("|---|-----------|----------|---------:|--:|-------------------------:|")
    for c in payload["criteria"]:
        add(
            f"| {c['number']} | {c['label']} | {c['evidence_status'].replace('_', ' ')} "
            f"| {c['n_satisfied']:,} | {c['pct_satisfied']}% "
            f"| {c['n_satisfied_direct']:,} ({c['pct_satisfied_direct']}%) |"
        )
    add("")
    add(
        "The last column re-runs each criterion with every `proxy` signal switched "
        "off, i.e. counting only what the registry actually records. The gap "
        "between the two columns is how much of each criterion is inference."
    )
    add("")

    for c in payload["criteria"]:
        add(f"## {c['number']}. {c['label']}")
        add("")
        add(f"*{c['tagline']}*")
        add("")
        add(_wrap(c["rationale"]))
        add("")
        add(f"**How it was curated.** {_wrap(c['curation_method'])}")
        add("")
        add(f"**Satisfied when:** `{c['satisfied_when']}`")
        add("")
        add(
            f"**Result:** {c['n_satisfied']:,} of {total:,} diseases ({c['pct_satisfied']}%); "
            f"{c['n_satisfied_direct']:,} ({c['pct_satisfied_direct']}%) on recorded evidence "
            f"alone, with proxy signals switched off. "
            f"Evidence status: *{c['evidence_status'].replace('_', ' ')}* &mdash; "
            f"{_wrap(c['evidence_status_label']).lower()}."
        )
        add("")
        add("| Signal | Sub | Tier | Registry field | Fires on | What it means |")
        add("|--------|-----|------|----------------|---------:|---------------|")
        for s in c["signals"]:
            sub = s["subcriterion"] or "&mdash;"
            fieldname = f"`{s['field']}`" if s["field"] else "&mdash;"
            add(
                f"| {s['label']} | {sub} | {TIER_LABELS.get(s['tier'], s['tier'])} | {fieldname} "
                f"| {s['n_fired']:,} | {_wrap(s['description'])} |"
            )
        add("")
        add(f"> **Coverage.** {_wrap(c['coverage_note'])}")
        add("")

    add("## Registry fields the website does not show")
    add("")
    add("| Field | Why |")
    add("|-------|-----|")
    for entry in spec.not_rendered:
        add(f"| `{entry['field']}` | {_wrap(entry['reason'])} |")
    add("")
    add(
        "Every other registry field appears somewhere on a disease card: in a "
        "criterion's `display` block, in the card header, or in the "
        "\"Everything else on record\" block. `just build-criteria` warns if that "
        "stops being true."
    )
    add("")

    add("## Registry fields deliberately left out of the criteria")
    add("")
    add("| Field | Why it is not criterion evidence |")
    add("|-------|----------------------------------|")
    for entry in spec.unassigned_fields:
        add(f"| `{entry['field']}` | {_wrap(entry['reason'])} |")
    add("")

    add("## Figures")
    add("")
    add("![Upset plot of the six criteria](figures/criteria_upset.png)")
    add("")
    add(
        "*Every disease counted once, in the single combination of criteria it "
        "meets. Full table: [`figures/criteria_intersections.tsv`]"
        "(figures/criteria_intersections.tsv).*"
    )
    add("")
    add("![The same criteria on recorded evidence alone](figures/criteria_upset_direct_evidence.png)")
    add("")
    add(
        "*The same evaluation with every `proxy` signal switched off. Criterion 5 "
        "empties out entirely, which is the clearest statement of the evidence gap "
        "under it.*"
    )
    add("")
    add("## Reproducing this")
    add("")
    add("```bash")
    add("just build-criteria      # criteria.json + this document")
    add("just upset               # the upset plot over the six criteria")
    add("just criteria-icons      # re-cut the six glyphs from the workflow figure")
    add("```")
    add("")
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI


@click.command()
@click.option("--diseases", "-d", default="prioritised-rare-disease-list.yml",
              type=click.Path(exists=True, path_type=Path), show_default=True,
              help="Merged registry to evaluate.")
@click.option("--criteria", "-c", "criteria_path", default="config/prioritisation_criteria.yaml",
              type=click.Path(exists=True, path_type=Path), show_default=True)
@click.option("--output", "-o", default="criteria.json",
              type=click.Path(path_type=Path), show_default=True)
@click.option("--report", "-r", default="docs/criteria-assignment.md",
              type=click.Path(path_type=Path), show_default=True)
def main(diseases: Path, criteria_path: Path, output: Path, report: Path) -> None:
    """Evaluate the prioritisation criteria and write criteria.json + the review document."""
    spec = load_criteria(criteria_path)
    records = load_diseases(diseases)
    payload = build_payload(spec, records)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=1, sort_keys=False) + "\n")

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(spec, payload, diseases))

    click.echo(f"{payload['n_diseases']:,} diseases evaluated against {len(payload['criteria'])} criteria")
    for c in payload["criteria"]:
        click.echo(f"  {c['number']}. {c['label']:28s} {c['n_satisfied']:5,d}  ({c['pct_satisfied']:4.1f}%)")
    missing = unrendered_fields(spec, records)
    if missing:
        click.echo("")
        click.secho("WARNING: registry fields the website renders nowhere:", fg="yellow")
        for fname, n in missing:
            click.echo(f"    {fname}  ({n:,} diseases)")
        click.echo(
            "  Add each to a criterion's `display` block, to `rendered_outside_criteria`, "
            "or to `not_rendered` in config/prioritisation_criteria.yaml."
        )
    click.echo(f"wrote {output} and {report}")


if __name__ == "__main__":
    main()
