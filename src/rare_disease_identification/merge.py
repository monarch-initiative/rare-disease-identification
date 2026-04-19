"""Merge the source disease list with drug association data."""

from pathlib import Path

import click
import yaml


def load_yaml(path: Path) -> dict:
    """Load a YAML file, returning empty dict if missing or empty."""
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if data else {}


def merge(source_path: Path, drugs_path: Path) -> dict:
    """Merge drug associations into the source disease list.

    Returns a new dict with indications/research/contraindications merged
    per disease by MONDO ID.
    """
    source = load_yaml(source_path)
    drugs = load_yaml(drugs_path)

    # Index drug data by disease ID
    drug_map: dict[str, dict] = {}
    for entry in drugs.get("diseases", []):
        disease_id = entry.get("disease_id")
        if disease_id:
            drug_map[disease_id] = entry

    # Merge into source diseases
    merged_count = 0
    for disease in source.get("diseases", []):
        mondo_id = disease.get("mondo_id")
        if not mondo_id or mondo_id not in drug_map:
            continue
        drug_entry = drug_map[mondo_id]
        for field in ("indications", "contraindications", "research"):
            if field in drug_entry:
                disease[field] = drug_entry[field]
        merged_count += 1

    click.echo(f"Merged drug data for {merged_count} diseases")
    return source


@click.command()
@click.option(
    "--source",
    "-s",
    "source_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the source disease list YAML (without drugs).",
)
@click.option(
    "--drugs",
    "-d",
    "drugs_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the drugs association YAML.",
)
@click.option(
    "--output",
    "-o",
    "output_path",
    required=True,
    type=click.Path(path_type=Path),
    help="Path to write the merged output YAML.",
)
def main(source_path: Path, drugs_path: Path, output_path: Path):
    """Merge the source disease list with drug association data."""
    data = merge(source_path, drugs_path)

    with open(output_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    click.echo(f"Wrote {len(data.get('diseases', []))} diseases to {output_path}")


if __name__ == "__main__":
    main()
