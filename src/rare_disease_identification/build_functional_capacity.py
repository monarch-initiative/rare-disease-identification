"""Derive the computable evidence lines of each functional-capacity assessment.

Same split the value sets use, for the same reason. An assessment's evidence list
mixes two kinds of line:

* **Derived** - EXPERT_DATABASE, FEDERAL_POLICY_LIST, STATE_POLICY_LIST,
  PHENOTYPE_ANCHOR, COMPUTED_SCORE. Each is a pure function of a source file
  (Orphanet's `fc.xml`, the SSA crosswalk, `policy_evidence.tsv`, HPOA, the
  phenotype ranking). Nothing about them is a judgement.
* **Curated** - LITERATURE and MODEL_JUDGEMENT, plus the judgement itself:
  `impairment`, `care_context`, `life_stage`, `rationale`, `curation_status`.
  Which sentence to quote, and what the whole picture means, cannot be computed.

Storing the derived lines in the curated file made them editable by whatever was
writing that file, and an agent that wants a particular answer has an obvious
incentive to adjust the evidence that produced it. Deriving them here removes the
opportunity rather than policing it: a tampered line is simply overwritten on the
next build.

This module **never writes to SOURCE**. `merge.py` joins the two, exactly as it
does for value sets.
"""
from __future__ import annotations

import sys
from pathlib import Path

import click
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/frailty"))

ASSESSMENTS = ("work_capacity", "care_dependence")
DERIVED_LANES = frozenset({
    "EXPERT_DATABASE", "FEDERAL_POLICY_LIST", "STATE_POLICY_LIST",
    "PHENOTYPE_ANCHOR", "COMPUTED_SCORE",
})
CURATED_LANES = frozenset({"LITERATURE", "MODEL_JUDGEMENT"})

# Order the evidence reads in: strongest and most independent first, the
# model's own reading last.
LANE_ORDER = ["EXPERT_DATABASE", "LITERATURE", "FEDERAL_POLICY_LIST",
              "STATE_POLICY_LIST", "PHENOTYPE_ANCHOR", "COMPUTED_SCORE",
              "MODEL_JUDGEMENT"]


def sort_evidence(lines: list[dict]) -> list[dict]:
    return sorted(lines, key=lambda e: LANE_ORDER.index(e["lane"])
                  if e.get("lane") in LANE_ORDER else len(LANE_ORDER))


def derive(source_path: Path) -> dict:
    """Regenerate every derived evidence line, for every curated assessment."""
    import csv

    import skeleton as sk
    from anchors import term_scores, corpus, anchor_evidence
    from common import RANKED, CACHE, orpha_codes

    source = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    cal = sk.cal_index()
    policy = sk.policy_index()
    scores, corp = term_scores(), corpus()
    with open(RANKED, encoding="utf-8") as fh:
        ranked = {r["mondo_id"]: r for r in csv.DictReader(fh, delimiter="\t")}

    out, n_lines = [], 0
    for d in source.get("diseases", []):
        mid = d.get("mondo_id")
        if not mid or not any(isinstance(d.get(s), dict) for s in ASSESSMENTS):
            continue
        codes = [c for c in orpha_codes(d) if (CACHE / f"ORPHA_{c}.md").exists()]
        entry: dict = {"mondo_id": mid}
        for slot in ASSESSMENTS:
            if not isinstance(d.get(slot), dict):
                continue
            ev: list[dict] = []
            for code in codes:
                ev += sk.orpha_evidence(code, slot)
            ev += sk.policy_evidence(policy.get(mid, []))
            ev += sk.cal_evidence(mid, slot, cal)
            # PHENOTYPE_ANCHOR and COMPUTED_SCORE are the same HPOA data seen at
            # two resolutions. Emit the findings when there are any, the score
            # only as a fallback, never both.
            anch = anchor_evidence(mid, slot, scores, corp)
            if anch:
                ev += anch
            elif mid in ranked:
                ev += sk.score_evidence(ranked[mid], slot)
            entry[slot] = ev
            n_lines += len(ev)
        out.append(entry)

    click.echo(f"Derived {n_lines} evidence lines for {len(out)} diseases")
    return {"diseases": out}


def refuse_if_source_carries_derived(source_path: Path) -> None:
    """SOURCE must not hand-carry a derived lane. Mirrors build_value_sets."""
    source = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    offenders = []
    for d in source.get("diseases", []):
        for slot in ASSESSMENTS:
            a = d.get(slot)
            if not isinstance(a, dict):
                continue
            for e in a.get("evidence") or []:
                if e.get("lane") in DERIVED_LANES:
                    offenders.append(f"{d['mondo_id']}.{slot}: {e['lane']}")
    if offenders:
        raise SystemExit(
            f"{source_path} carries {len(offenders)} derived evidence lines, which this "
            f"build regenerates.\nFirst few: {offenders[:3]}\n"
            "Run `just strip-derived-evidence` once to remove them; merge re-attaches them.")


@click.command()
@click.option("--source", "-s", "source_path", required=True,
              type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", "output_path", required=True,
              type=click.Path(path_type=Path))
@click.option("--check-source/--no-check-source", default=True,
              help="Refuse to run if SOURCE hand-carries a derived lane.")
def main(source_path: Path, output_path: Path, check_source: bool) -> None:
    """Derive functional-capacity evidence -> data/functional_capacity.yml."""
    if check_source:
        refuse_if_source_carries_derived(source_path)
    data = derive(source_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        yaml.dump(data, fh, default_flow_style=False, allow_unicode=True,
                  sort_keys=False, width=100)
    click.echo(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
