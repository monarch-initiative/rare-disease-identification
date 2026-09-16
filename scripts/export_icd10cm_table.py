#!/usr/bin/env python3
"""Export a MONDO -> ICD-10-CM mapping table for the prioritised rare disease list.

Output: data/icd10cm_table.tsv

One row per (disease, ICD-10-CM code) pair, plus an explicit row for every disease
that has no mapping at all, so absence is stated rather than inferred from a gap.

Mappings come from Mondo's per-predicate SSSOM releases, all six of them, because
the ask is recall-first:

    exactmatch, broadmatch, narrowmatch, closematch, relatedmatch, hasdbxref

`--rollup` additionally walks up the Mondo `is_a` hierarchy for diseases with no
direct mapping and emits their nearest mapped ancestor's code, flagged as
`ancestor` in `mapping_scope` with the ancestor named in `via_mondo_id`. Those rows
are deliberately lossy: pulling the ancestor's code pulls a cohort far broader than
the disease. Keep them separable, never merge them into the direct rows.

Usage:
    python scripts/export_icd10cm_table.py
    python scripts/export_icd10cm_table.py --rollup --mondo-obo tmp/mondo.obo
"""

from __future__ import annotations

import csv
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

import click
import yaml

try:
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader

PURL = "http://purl.obolibrary.org/obo/mondo/mappings/mondo_{pred}_icd10cm.sssom.tsv"

# Ordered strongest-first; a disease's rows are emitted in this order.
PREDICATES = [
    "exactmatch",
    "closematch",
    "narrowmatch",
    "broadmatch",
    "relatedmatch",
    "hasdbxref",
]

COLUMNS = [
    "mondo_id",
    "mondo_label",
    "icd10cm_code",
    "icd10cm_label",
    "predicate",
    "mapping_scope",
    "via_mondo_id",
    "via_mondo_label",
    "prioritization_category",
]


def fetch_sssom(pred: str, cache_dir: Path) -> list[dict]:
    """Download (and cache) one Mondo SSSOM mapping file."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"mondo_{pred}_icd10cm.sssom.tsv"
    if not path.exists():
        url = PURL.format(pred=pred)
        click.echo(f"  fetching {url}")
        urllib.request.urlretrieve(url, path)
    with open(path) as f:
        lines = [line for line in f if not line.startswith("#")]
    return list(csv.DictReader(lines, delimiter="\t"))


def load_parents(mondo_obo: Path) -> dict[str, set[str]]:
    """Parse `is_a` edges out of mondo.obo, skipping obsolete terms."""
    parents: dict[str, set[str]] = defaultdict(set)
    current = None
    obsolete = False
    with open(mondo_obo) as f:
        for line in f:
            line = line.rstrip("\n")
            if line == "[Term]":
                current, obsolete = None, False
            elif line.startswith("id: MONDO:"):
                current = line[4:].strip()
            elif line.startswith("is_obsolete: true"):
                obsolete = True
            elif line.startswith("is_a: ") and current and not obsolete:
                parents[current].add(line[6:].split("!")[0].strip())
    return parents


def nearest_mapped_ancestors(term: str, parents: dict[str, set[str]], mapped: set[str]) -> list[str]:
    """Breadth-first walk upwards, returning the closest mapped ancestors."""
    seen = set()
    frontier = set(parents.get(term, ()))
    while frontier:
        hits = sorted(frontier & mapped)
        if hits:
            return hits
        seen |= frontier
        frontier = {p for t in frontier for p in parents.get(t, ())} - seen
    return []


@click.command()
@click.option("--diseases", type=click.Path(exists=True, path_type=Path),
              default=Path("prioritised-rare-disease-list.yml"),
              help="Prioritised disease list YAML.")
@click.option("--output", "-o", type=click.Path(path_type=Path),
              default=Path("data/icd10cm_table.tsv"), help="Output TSV path.")
@click.option("--cache-dir", type=click.Path(path_type=Path), default=Path("tmp/sssom"),
              help="Where to cache the downloaded SSSOM files.")
@click.option("--rollup/--no-rollup", default=False,
              help="Also emit nearest mapped ancestor codes for unmapped diseases.")
@click.option("--mondo-obo", type=click.Path(path_type=Path), default=Path("tmp/mondo.obo"),
              help="mondo.obo, required by --rollup.")
def main(diseases: Path, output: Path, cache_dir: Path, rollup: bool, mondo_obo: Path):
    """Build the MONDO -> ICD-10-CM table for the prioritised list."""
    with open(diseases) as f:
        data = yaml.load(f, Loader=_Loader)
    entries = [d for d in data.get("diseases", []) if d.get("mondo_id")]
    labels = {d["mondo_id"]: d.get("mondo_label", "") for d in entries}
    category = {d["mondo_id"]: d.get("prioritization_category", "") for d in entries}
    click.echo(f"Loaded {len(entries)} diseases from {diseases}")

    click.echo("Loading Mondo ICD-10-CM mappings:")
    by_disease: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    all_mapped: set[str] = set()
    for pred in PREDICATES:
        rows = fetch_sssom(pred, cache_dir)
        for row in rows:
            subject = row.get("subject_id")
            if not subject:
                continue
            all_mapped.add(subject)
            # Ancestors are usually outside the prioritised list, so take their
            # labels from SSSOM rather than leaving via_mondo_label blank.
            if subject not in labels and row.get("subject_label"):
                labels[subject] = row["subject_label"]
            by_disease[subject].append(
                (pred, row.get("object_id", ""), row.get("object_label", ""))
            )
        hit = sum(1 for d in entries if any(p == pred for p, _, _ in by_disease.get(d["mondo_id"], [])))
        click.echo(f"  {pred:13s} {len(rows):6d} mappings, {hit:4d} on the list")

    parents: dict[str, set[str]] = {}
    if rollup:
        if not mondo_obo.exists():
            click.echo(f"Error: --rollup needs {mondo_obo}; run `just fetch-mondo`", err=True)
            sys.exit(1)
        click.echo(f"Loading hierarchy from {mondo_obo}")
        parents = load_parents(mondo_obo)

    out_rows: list[dict] = []
    n_direct = n_rolled = n_none = 0
    for d in entries:
        mondo_id = d["mondo_id"]
        base = {
            "mondo_id": mondo_id,
            "mondo_label": labels.get(mondo_id, ""),
            "prioritization_category": category.get(mondo_id, ""),
            "via_mondo_id": "",
            "via_mondo_label": "",
        }
        direct = by_disease.get(mondo_id) or []
        if direct:
            n_direct += 1
            order = {p: i for i, p in enumerate(PREDICATES)}
            for pred, code, code_label in sorted(direct, key=lambda t: (order[t[0]], t[1])):
                out_rows.append({**base, "icd10cm_code": code, "icd10cm_label": code_label,
                                 "predicate": pred, "mapping_scope": "direct"})
            continue

        ancestors = nearest_mapped_ancestors(mondo_id, parents, all_mapped) if rollup else []
        if ancestors:
            n_rolled += 1
            for anc in ancestors:
                for pred, code, code_label in by_disease.get(anc, []):
                    out_rows.append({**base, "icd10cm_code": code, "icd10cm_label": code_label,
                                     "predicate": pred, "mapping_scope": "ancestor",
                                     "via_mondo_id": anc, "via_mondo_label": labels.get(anc, "")})
            continue

        n_none += 1
        out_rows.append({**base, "icd10cm_code": "", "icd10cm_label": "",
                         "predicate": "none", "mapping_scope": "none"})

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out_rows)

    click.echo(f"\nWritten {len(out_rows)} rows to {output}")
    click.echo(f"  {n_direct} diseases with a direct ICD-10-CM mapping")
    if rollup:
        click.echo(f"  {n_rolled} diseases mapped only via an ancestor (mapping_scope=ancestor)")
    click.echo(f"  {n_none} diseases with no mapping at all (predicate=none)")


if __name__ == "__main__":
    main()
