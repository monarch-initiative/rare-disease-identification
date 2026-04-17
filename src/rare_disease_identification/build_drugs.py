#!/usr/bin/env python3
"""Build the drugs.yml disease-centric drug association report.

Reads MeDIC product YAML files and the priority disease list,
then aggregates drug associations into a disease-centric view
for the rare disease identification project.

This script reads from a MeDIC products directory (configurable)
and the priority disease list extracted by this project.

Usage:
    python -m rare_disease_identification.build_drugs
    python -m rare_disease_identification.build_drugs --medic-dir ../medic
"""

import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import click
import yaml


class NoAliasDumper(yaml.SafeDumper):
    """YAML dumper that writes all values inline (no anchors/aliases)."""

    def ignore_aliases(self, data):
        return True


def load_priority_diseases(yml_path: Path) -> list[tuple[str, str]]:
    """Load (disease_id, disease_label) pairs from the prioritised disease list."""
    with open(yml_path) as f:
        data = yaml.safe_load(f)

    diseases = []
    for d in data.get("diseases", []):
        disease_id = d.get("mondo_id", "")
        disease_label = d.get("mondo_label", "")
        if disease_id:
            diseases.append((disease_id, disease_label))
    return diseases


def load_yaml(path: Path) -> dict:
    """Load a YAML file, returning empty dict if missing or empty."""
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if data else {}


def extract_evidence(record: dict) -> list[dict]:
    """Extract evidence items from a record, preserving only non-empty fields."""
    evidence_items = []
    for ev in record.get("evidence", []):
        item = {}
        for key in (
            "source",
            "reference",
            "reference_title",
            "snippet",
            "support",
            "confidence_drug",
            "confidence_disease",
            "confidence_association",
            "evidence_source",
            "approval_status",
            "max_research_phase",
            "study_status",
            "curator",
        ):
            val = ev.get(key)
            if val is not None and val != "":
                item[key] = val

        # Backward compat: interpreted_text / interpretation -> explanation
        if "explanation" not in item:
            expl = ev.get("interpretation", "") or ev.get("interpreted_text", "")
            if expl:
                item["explanation"] = expl

        # Backward compat: document_text / document_title -> reference_title
        if "reference_title" not in item:
            title = ev.get("document_title", "") or ev.get("document_text", "")
            if title and len(title) < 200:
                item["reference_title"] = title

        # Backward compat: build source object from old flat fields
        if "source" not in item:
            source_obj = {}
            st = ev.get("source_type", "")
            sf = ev.get("source_file", "")
            su = ev.get("source_url", "")
            jur = ev.get("jurisdiction", "")

            assoc_curator = record.get("curator", "")
            if assoc_curator == "cureid":
                source_obj["name"] = "NCATS CURE-ID"
                source_obj["description"] = "Drug repurposing case reports from the NCATS CURE-ID open data platform"
            elif sf and "research" in sf:
                source_obj["name"] = "Deep research"
                source_obj["description"] = f"AI-generated literature review from {sf}"
            elif st:
                source_obj["name"] = st
            else:
                source_obj["name"] = "UNKNOWN"

            if st:
                source_obj["type"] = st
            if jur:
                source_obj["jurisdiction"] = jur
            if sf:
                source_obj["file"] = sf
            if su:
                source_obj["url"] = su
            if source_obj:
                item["source"] = source_obj

        # Backward compat: old single confidence -> all three dimensions
        if "confidence_drug" not in item:
            old_conf = ev.get("confidence", "")
            if old_conf:
                item["confidence_drug"] = old_conf
                item["confidence_disease"] = old_conf
                item["confidence_association"] = old_conf

        if item:
            evidence_items.append(item)
    return evidence_items


def make_drug_assoc(drug_id: str, drug_label: str, evidence: list[dict]) -> dict:
    """Create a DrugAssociation dict."""
    assoc = {"drug_label": drug_label}
    if drug_id:
        assoc["drug_id"] = drug_id
    if evidence:
        assoc["evidence"] = evidence
    return assoc


SOURCE_DESCRIPTIONS = {
    "fda": {
        "source": {
            "name": "FDA DailyMed",
            "description": (
                "Approved indications extracted from FDA DailyMed Structured Product Labels. "
                "Raw label text was downloaded from DailyMed, then disease names were extracted "
                "by an LLM (GPT-4) and grounded to ontology IDs by the MeDIC pipeline."
            ),
            "type": "REGULATORY",
            "jurisdiction": "USA",
        },
        "url_template": "https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query={drug_label}",
        "curator": {"curator_type": "PIPELINE", "name": "MeDIC indication ingest from FDA DailyMed SPL labels"},
    },
    "ema": {
        "source": {
            "name": "EMA EPAR",
            "description": (
                "Approved indications from European Public Assessment Reports (EPARs) "
                "from the European Medicines Agency."
            ),
            "type": "REGULATORY",
            "jurisdiction": "EU",
        },
        "url_template": "https://www.ema.europa.eu/en/search?search_api_fulltext={drug_label}",
        "curator": {"curator_type": "PIPELINE", "name": "MeDIC indication ingest from EMA EPAR"},
    },
    "pmda": {
        "source": {
            "name": "PMDA",
            "description": (
                "Approved indications from the Japan Pharmaceuticals and Medical Devices Agency."
            ),
            "type": "REGULATORY",
            "jurisdiction": "JAPAN",
        },
        "url_template": "https://www.pmda.go.jp/english/search_index.html",
        "curator": {"curator_type": "PIPELINE", "name": "MeDIC indication ingest from PMDA drug labels"},
    },
}


def build_on_label_evidence(assoc: dict) -> list[dict]:
    """Build evidence items from source flags and any existing evidence."""
    evidence = extract_evidence(assoc)
    drug_label = assoc.get("final_normalized_drug_label", "")

    for flag, source_info in SOURCE_DESCRIPTIONS.items():
        if assoc.get(flag):
            indications_text = assoc.get("indications_text", "")
            if indications_text:
                snippet = indications_text
            else:
                drug_id = assoc.get("final_normalized_drug_id", "")
                disease_id = assoc.get("final_normalized_disease_id", "")
                disease_label = assoc.get("final_normalized_disease_label", "")
                rel_type = assoc.get("relationship_type", "INDICATION")
                snippet = (
                    f"Source row: drug={drug_id} ({drug_label}), "
                    f"disease={disease_id} ({disease_label}), "
                    f"relationship={rel_type}, {flag.upper()}=True"
                )

            source_obj = dict(source_info["source"])
            source_obj["url"] = source_info["url_template"].format(drug_label=drug_label.replace(" ", "+"))

            item = {
                "source": source_obj,
                "snippet": snippet,
                "confidence_drug": "HIGH",
                "confidence_disease": "HIGH",
                "confidence_association": "HIGH",
                "curator": source_info["curator"],
            }
            evidence.append(item)

    return evidence


def aggregate_indications(
    path: Path,
    indications: dict[str, list[dict]],
    contraindications: dict[str, list[dict]],
) -> None:
    """Read indication associations and split by disease."""
    data = load_yaml(path)
    for assoc in data.get("associations", []):
        disease_id = assoc.get("final_normalized_disease_id", "")
        if not disease_id:
            continue
        drug_id = assoc.get("final_normalized_drug_id", "")
        drug_label = assoc.get("final_normalized_drug_label", "")
        evidence = build_on_label_evidence(assoc)
        drug_assoc = make_drug_assoc(drug_id, drug_label, evidence)

        rel_type = assoc.get("relationship_type", "")
        if rel_type == "CONTRAINDICATION":
            contraindications[disease_id].append(drug_assoc)
        else:
            indications[disease_id].append(drug_assoc)


def aggregate_research(path: Path, research: dict[str, list[dict]]) -> None:
    """Read research associations and group by disease."""
    data = load_yaml(path)
    for assoc in data.get("associations", []):
        disease_id = assoc.get("disease_id", "")
        if not disease_id:
            continue
        drug_id = assoc.get("drug_id", "")
        drug_label = assoc.get("drug_label", "")
        evidence = extract_evidence(assoc)
        drug_assoc = make_drug_assoc(drug_id, drug_label, evidence)
        research[disease_id].append(drug_assoc)


@click.command()
@click.option(
    "--medic-dir",
    type=click.Path(exists=True, path_type=Path),
    default=Path("../medic"),
    help="Path to the MeDIC project root (contains products/)",
)
@click.option(
    "--diseases",
    type=click.Path(exists=True, path_type=Path),
    default=Path("prioritised-rare-disease-list.yml"),
    help="Path to the prioritised disease list YAML",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("data/drugs.yml"),
    help="Output path for the drugs report",
)
def main(medic_dir: Path, diseases: Path, output: Path):
    """Build the disease-centric drug association report from MeDIC products."""
    products_dir = medic_dir / "products"
    if not products_dir.exists():
        click.echo(f"Error: MeDIC products directory not found: {products_dir}", err=True)
        sys.exit(1)

    # Load priority diseases
    priority_diseases = load_priority_diseases(diseases)
    click.echo(f"Loaded {len(priority_diseases)} priority diseases")

    # Aggregate from MeDIC product files
    indications: dict[str, list[dict]] = defaultdict(list)
    contraindications: dict[str, list[dict]] = defaultdict(list)
    research: dict[str, list[dict]] = defaultdict(list)

    aggregate_indications(products_dir / "indication_list.yaml", indications, contraindications)
    aggregate_indications(products_dir / "contraindication_list.yaml", indications, contraindications)
    aggregate_research(products_dir / "research_list.yaml", research)

    # Build disease records
    disease_records = []
    diseases_with_data = 0
    for disease_id, disease_label in priority_diseases:
        record: dict = {
            "disease_id": disease_id,
            "disease_label": disease_label,
        }
        if disease_id in indications:
            record["indications"] = indications[disease_id]
        if disease_id in contraindications:
            record["contraindications"] = contraindications[disease_id]
        if disease_id in research:
            record["research"] = research[disease_id]

        has_data = any(disease_id in store for store in [indications, contraindications, research])
        if has_data:
            diseases_with_data += 1
        disease_records.append(record)

    report = {
        "id": "mondo-drugs",
        "title": "MeDIC Drug-Disease Association Report",
        "date_created": date.today().isoformat(),
        "diseases": disease_records,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        yaml.dump(report, f, Dumper=NoAliasDumper, default_flow_style=False, sort_keys=False, allow_unicode=True)

    click.echo(f"Written {len(disease_records)} disease records to {output}")
    click.echo(f"  {diseases_with_data} diseases have at least one association")
    click.echo(f"  {len(disease_records) - diseases_with_data} diseases have no data yet")


if __name__ == "__main__":
    main()
