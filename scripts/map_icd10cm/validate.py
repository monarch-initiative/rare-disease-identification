#!/usr/bin/env python3
"""Validate the assembled MONDO -> ICD-10-CM SSSOM set.

Checks the things that actually go wrong when part of the pipeline is an LLM:
invented codes, codes that were never offered as candidates for that term,
dropped or duplicated subjects, and missing justifications.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import click
import yaml

try:
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader

sys.path.insert(0, str(Path(__file__).parent))
from lexmatch import load_icd10cm  # noqa: E402


@click.command()
@click.option("--sssom", type=click.Path(exists=True, path_type=Path),
              default=Path("mappings/mondo_icd10cm_exactmatch.sssom.tsv"))
@click.option("--diseases", type=click.Path(exists=True, path_type=Path),
              default=Path("src/prioritised-rare-disease-list.yml"))
@click.option("--work-dir", type=click.Path(exists=True, path_type=Path),
              default=Path("tmp/icd10cm"))
@click.option("--icd-ttl", type=click.Path(exists=True, path_type=Path),
              default=Path(Path.home() / "ws/projects/medic/background/ontsrc/icd10cm.owl"))
def main(sssom, diseases, work_dir, icd_ttl):
    """Run every check and exit non-zero on any hard failure."""
    lines = [ln for ln in sssom.read_text().splitlines() if not ln.startswith("#")]
    rows = list(csv.DictReader(lines, delimiter="\t"))

    with open(diseases) as f:
        expected = {d["mondo_id"] for d in yaml.load(f, Loader=_Loader)["diseases"]
                    if d.get("mondo_id")}

    valid_codes = {c for c, _, _, _ in load_icd10cm(icd_ttl)}
    queue = json.loads((work_dir / "review_queue.json").read_text())

    errors, warnings = [], []

    subjects = [r["subject_id"] for r in rows]
    dupes = [s for s, n in Counter(subjects).items() if n > 1]
    if dupes:
        errors.append(f"{len(dupes)} duplicated subject_id rows, e.g. {dupes[:5]}")
    missing = expected - set(subjects)
    if missing:
        errors.append(f"{len(missing)} list terms absent from the set, e.g. {sorted(missing)[:5]}")
    extra = set(subjects) - expected
    if extra:
        errors.append(f"{len(extra)} subjects not on the list, e.g. {sorted(extra)[:5]}")

    bad_code, not_offered, no_comment = [], [], []
    mapped = 0
    for r in rows:
        oid = r["object_id"]
        if oid == "sssom:NoTermFound":
            if not r.get("comment", "").strip():
                no_comment.append(r["subject_id"])
            continue
        mapped += 1
        if not oid.startswith("ICD10CM:"):
            bad_code.append((r["subject_id"], oid))
            continue
        code = oid.split(":", 1)[1]
        if code not in valid_codes:
            bad_code.append((r["subject_id"], oid))
        if r["mapping_justification"] == "semapv:CompositeMatching":
            offered = {c["code"] for c in queue.get(r["subject_id"], {}).get("candidates", [])}
            if offered and code not in offered:
                not_offered.append((r["subject_id"], oid))
            if not r.get("comment", "").strip():
                no_comment.append(r["subject_id"])

    if bad_code:
        errors.append(f"{len(bad_code)} rows reference a code absent from ICD-10-CM: {bad_code[:5]}")
    if not_offered:
        errors.append(f"{len(not_offered)} agentic rows picked a code never offered as a "
                      f"candidate: {not_offered[:5]}")
    if no_comment:
        warnings.append(f"{len(no_comment)} rows have an empty justification comment")

    just = Counter(r["mapping_justification"] for r in rows)
    click.echo(f"Rows: {len(rows)}  (expected {len(expected)})")
    click.echo(f"Mapped: {mapped}   NoTermFound: {len(rows) - mapped}")
    for k, v in just.most_common():
        click.echo(f"  {k:34s} {v}")

    for w in warnings:
        click.echo(f"\nWARN  {w}")
    for e in errors:
        click.echo(f"\nFAIL  {e}", err=True)
    if errors:
        sys.exit(1)
    click.echo("\nAll structural checks passed.")


if __name__ == "__main__":
    main()
