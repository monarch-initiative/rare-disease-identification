#!/usr/bin/env python3
"""Update mondo_category_* fields via Mondo ontology ancestor traversal.

For each disease in the prioritised disease list, finds ancestors that are
direct children of the specified MONDO category root nodes and updates the
corresponding fields. Existing values are always overwritten in the output.

Category roots:
    mondo_category_body_system    <- MONDO:7770006
    mondo_category_developmental  <- MONDO:7770007
    mondo_category_etiologic      <- MONDO:7770008
    mondo_category_genetic        <- MONDO:7770009
    mondo_category_extrinsic      <- MONDO:7770010
    mondo_category_molecular      <- MONDO:7770011

Usage:
    python -m rare_disease_identification.update_mondo_categories
    python -m rare_disease_identification.update_mondo_categories \\
        --input src/prioritised-rare-disease-list.yml --output out.yml \\
        --summary summary.yml
"""

from collections import Counter
from pathlib import Path
from functools import cache

import click
import yaml
from oaklib import get_adapter
from oaklib.datamodels.vocabulary import IS_A


CATEGORY_ROOTS = {
    "MONDO:7770006": "mondo_category_body_system",
    "MONDO:7770007": "mondo_category_developmental",
    "MONDO:7770008": "mondo_category_etiologic",
    "MONDO:7770009": "mondo_category_genetic",
    "MONDO:7770010": "mondo_category_extrinsic",
    "MONDO:7770011": "mondo_category_molecular",
}


class NoAliasDumper(yaml.SafeDumper):
    """YAML dumper that writes all values inline (no anchors/aliases)."""

    def ignore_aliases(self, data):
        return True


@click.command()
@click.option(
    "--input",
    "-i",
    "input_path",
    type=click.Path(exists=True, path_type=Path),
    default=Path("src/prioritised-rare-disease-list.yml"),
    help="Input disease list YAML",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path (defaults to --input for in-place update)",
)
@click.option(
    "--summary",
    "-s",
    "summary_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Optional path to write a YAML summary of category counts",
)
def main(input_path: Path, output_path: Path, summary_path: Path):
    """Update MONDO category fields from ontology ancestor traversal."""
    if output_path is None:
        output_path = input_path

    with open(input_path) as f:
        data = yaml.safe_load(f)

    diseases = data.get("diseases", [])
    click.echo(f"Loaded {len(diseases)} diseases from {input_path}")

    click.echo("Initialising Mondo OAK adapter")
    adapter = get_adapter("simpleobo:mondo.obo")

    @cache
    def direct_parents(term_id: str) -> frozenset:
        return frozenset(
            obj for _pred, obj in adapter.outgoing_relationships(term_id, predicates=[IS_A])
        )

    @cache
    def direct_children(term_id: str) -> frozenset:
        return frozenset(
            obj for _pred, obj in adapter.incoming_relationships(term_id, predicates=[IS_A])
        )

    @cache
    def term_label(term_id: str) -> str | None:
        return adapter.label(term_id)

    updated: dict[str, int] = {f: 0 for f in CATEGORY_ROOTS.values()}
    cleared: dict[str, int] = {f: 0 for f in CATEGORY_ROOTS.values()}
    category_counts: dict[str, Counter] = {f: Counter() for f in CATEGORY_ROOTS.values()}
    no_category: dict[str, int] = {f: 0 for f in CATEGORY_ROOTS.values()}

    category_children = {root_id: direct_children(root_id) for root_id in CATEGORY_ROOTS.keys()}

    for i, disease in enumerate(diseases):
        mondo_id = disease.get("mondo_id", "")
        if not mondo_id:
            continue

        if (i + 1) % 100 == 0:
            click.echo(f"  {i + 1}/{len(diseases)} diseases processed...")

        try:
            ancestors = set(
                anc
                for anc in adapter.ancestors(mondo_id, predicates=[IS_A], reflexive=False)
                if anc.startswith("MONDO:")
            )
        except Exception as e:
            click.echo(f"  Warning: could not get ancestors for {mondo_id}: {e}", err=True)
            continue

        for root_id, field in CATEGORY_ROOTS.items():
            matching = category_children[root_id].intersection(ancestors)
            if matching:
                terms = [{"id": t, "label": term_label(t) or ""} for t in matching]
                for t in matching:
                    category_counts[field][t] += 1
                if set(matching) != set(t["id"] for t in disease.get(field, [])):
                    updated[field] += 1
                disease[field] = terms
            else:
                if field in disease:
                    del disease[field]
                    cleared[field] += 1
                no_category[field] += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(data, f, Dumper=NoAliasDumper, default_flow_style=False, sort_keys=False, allow_unicode=True)

    click.echo(f"Written to {output_path}")
    for field in CATEGORY_ROOTS.values():
        click.echo(f"  {field}: {updated[field]} updated, {cleared[field]} cleared")

    if summary_path is not None:
        summary = {}
        for field in CATEGORY_ROOTS.values():
            sorted_terms = sorted(category_counts[field].items(), key=lambda x: (-x[1], x[0]))
            summary[field] = {
                "counts": [
                    {k: v for k, v in {"id": term_id, "label": term_label(term_id) or None, "count": count}.items() if v is not None}
                    for term_id, count in sorted_terms
                ],
                "no_category": no_category[field],
            }
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, "w") as f:
            yaml.dump(summary, f, Dumper=NoAliasDumper, default_flow_style=False, sort_keys=False, allow_unicode=True)
        click.echo(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
