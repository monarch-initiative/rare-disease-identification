#!/usr/bin/env python3
"""Build the drugs.yml disease-centric drug association report.

Reads MeDIC product YAML files and the priority disease list,
then aggregates drug associations into a disease-centric view
for the rare disease identification project.

Usage:
    python -m rare_disease_identification.build_drugs
    python -m rare_disease_identification.build_drugs --medic-dir ../medic
"""

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


# Map of regulatory jurisdiction to a canonical source description used when
# the MeDIC evidence row only carries `source_type: REGULATORY` and we want to
# label it with a sensible authority name.
JURISDICTION_TO_SOURCE: dict[str, dict[str, str]] = {
    "USA": {
        "name": "FDA DailyMed",
        "description": (
            "Approved indications extracted from FDA DailyMed Structured Product Labels. "
            "Raw label text is downloaded from DailyMed and disease names are normalised "
            "to ontology IDs by the MeDIC pipeline."
        ),
    },
    "EU": {
        "name": "EMA EPAR",
        "description": (
            "Approved indications from European Public Assessment Reports (EPARs) "
            "from the European Medicines Agency."
        ),
    },
    "JAPAN": {
        "name": "PMDA",
        "description": (
            "Approved indications from the Japan Pharmaceuticals and Medical Devices Agency."
        ),
    },
}


def normalize_approval_date(value: str | None) -> str | None:
    """Normalize MeDIC approval dates (often `YYYYMMDD`) to ISO 8601."""
    if not value:
        return None
    s = str(value).strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
    return s


def rewrite_dead_url(url: str) -> str:
    """Rewrite known-dead MEDIC URL patterns to working equivalents.

    MEDIC currently emits a few search URLs that 404 against the live sites.
    Rewrite them in-flight so consumers don't see broken links. This is a
    bandage; the upstream fix lives in MEDIC.

    - EMA  `…/en/search-results?query=…`     → `…/en/medicines?search_api_fulltext=…`
    - Purple Book `purplebooksearch.fda.gov/results?query=…`
                                              → `purplebooksearch.fda.gov/?query=…`
    - PMDA `pmda.go.jp/english/search/search.html?q=…`
                                              → `pmda.go.jp/PmdaSearch/iyakuSearch/`
    """
    if not url:
        return url
    if "ema.europa.eu/en/search-results?query=" in url:
        return url.replace(
            "ema.europa.eu/en/search-results?query=",
            "ema.europa.eu/en/medicines?search_api_fulltext=",
        )
    if "purplebooksearch.fda.gov/results?query=" in url:
        return url.replace(
            "purplebooksearch.fda.gov/results?query=",
            "purplebooksearch.fda.gov/?query=",
        )
    if "pmda.go.jp/english/search/search.html" in url:
        # PMDA's English search page is gone; the closest live equivalent is
        # the Japanese drug search portal. No clean query-string mapping.
        return "https://www.pmda.go.jp/PmdaSearch/iyakuSearch/"
    return url


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


def _strip_empty(d: dict) -> dict:
    """Drop keys whose values are empty strings, None, or empty lists/dicts."""
    return {k: v for k, v in d.items() if v not in (None, "", [], {})}


def build_source(ev: dict, drug_label: str) -> dict:
    """Build a structured `source` object from a MeDIC evidence row.

    The `reference` URL is intentionally not copied into `source.url` —
    the evidence row carries the URL as `reference` already, and the UI
    renders both, which would double the link in the card.
    """
    source_type = ev.get("source_type") or ""
    jurisdiction = ev.get("jurisdiction") or ""

    source: dict = {}
    if source_type == "REGULATORY" and jurisdiction in JURISDICTION_TO_SOURCE:
        info = JURISDICTION_TO_SOURCE[jurisdiction]
        source["name"] = info["name"]
        source["description"] = info["description"]
    elif source_type:
        # LITERATURE / DATABASE / GUIDELINE / POST_MARKET
        source["name"] = source_type.replace("_", " ").title()
    elif jurisdiction:
        source["name"] = jurisdiction
    else:
        source["name"] = "UNKNOWN"

    if source_type:
        source["type"] = source_type
    if jurisdiction:
        source["jurisdiction"] = jurisdiction

    return source


def build_indication_evidence(ev: dict, drug_label: str) -> dict:
    """Convert a MeDIC indication evidence row to our richer evidence shape."""
    confidence = ev.get("confidence") or ""
    item: dict = {
        "source": build_source(ev, drug_label),
        "source_type": ev.get("source_type") or "",
        "source_role": ev.get("source_role") or "",
        "jurisdiction": ev.get("jurisdiction") or "",
        "reference": rewrite_dead_url(ev.get("reference") or ""),
        "source_document_url": ev.get("source_document_url") or "",
        "snippet": ev.get("snippet") or "",
        "explanation": ev.get("explanation") or "",
        "approval_status": ev.get("approval_status") or "",
        "approval_date": normalize_approval_date(ev.get("approval_date")) or "",
        "original_drug_label": ev.get("original_drug_label") or "",
        "original_drug_id": ev.get("original_drug_id") or "",
        "original_disease_label": ev.get("original_disease_label") or "",
        "original_disease_id": ev.get("original_disease_id") or "",
        "setid": ev.get("setid") or "",
        "application_number": ev.get("application_number") or "",
        "bla_number": ev.get("bla_number") or "",
        "confidence": confidence,
        # The site UI reads these three; keep them aligned with the single
        # MeDIC `confidence` value until a richer breakdown is available.
        "confidence_drug": confidence,
        "confidence_disease": confidence,
        "confidence_association": confidence,
    }
    return _strip_empty(item)


def build_research_evidence(ev: dict) -> dict:
    """Convert a MeDIC research evidence row to our evidence shape."""
    curator = ev.get("curator")
    confidence = ev.get("confidence") or ""
    item: dict = {
        "source": {
            "name": (ev.get("source_type") or "").replace("_", " ").title() or "UNKNOWN",
            "type": ev.get("source_type") or "",
        },
        "source_type": ev.get("source_type") or "",
        "reference": rewrite_dead_url(ev.get("reference") or ""),
        "reference_title": ev.get("reference_title") or "",
        "page_or_section": ev.get("page_or_section") or "",
        "snippet": ev.get("snippet") or "",
        "explanation": ev.get("explanation") or "",
        "evidence_source": ev.get("evidence_source") or "",
        "original_drug_label": ev.get("original_drug_label") or "",
        "original_drug_id": ev.get("original_drug_id") or "",
        "original_disease_label": ev.get("original_disease_label") or "",
        "original_disease_id": ev.get("original_disease_id") or "",
        "confidence": confidence,
        "confidence_drug": confidence,
        "confidence_disease": confidence,
        "confidence_association": confidence,
    }
    if isinstance(curator, dict):
        item["curator"] = _strip_empty(dict(curator))
    elif curator:
        item["curator"] = {"name": str(curator)}

    item["source"] = _strip_empty(item["source"])
    return _strip_empty(item)


def build_regulatory_status(rs: dict) -> dict:
    """Convert a MeDIC regulatory_status row to our shape (with normalized date)."""
    return _strip_empty(
        {
            "authority": rs.get("authority") or "",
            "source": rs.get("source") or "",
            "status": rs.get("status") or "",
            "approval_date": normalize_approval_date(rs.get("approval_date")) or "",
            "source_role": rs.get("source_role") or "",
            "regulatory_document_url": rewrite_dead_url(rs.get("regulatory_document_url") or ""),
            "source_document_url": rs.get("source_document_url") or "",
            "setid": rs.get("setid") or "",
            "application_number": rs.get("application_number") or "",
            "bla_number": rs.get("bla_number") or "",
        }
    )


def build_indication_assoc(assoc: dict) -> dict:
    """Build a DrugAssociation dict from a MeDIC indication / contraindication row."""
    drug_id = assoc.get("final_normalized_drug_id") or ""
    drug_label = assoc.get("final_normalized_drug_label") or ""
    rel_type = assoc.get("relationship_type") or "INDICATION"

    evidence = [build_indication_evidence(ev, drug_label) for ev in assoc.get("evidence") or []]
    regulatory_status = [build_regulatory_status(rs) for rs in assoc.get("regulatory_status") or []]

    out: dict = {
        "drug_label": drug_label,
        "drug_id": drug_id,
        "relationship_type": rel_type,
        "indications_text": assoc.get("indications_text") or "",
        "regulatory_status": regulatory_status,
        "evidence": evidence,
    }
    return _strip_empty(out)


def build_research_assoc(assoc: dict) -> dict:
    """Build a DrugAssociation dict from a MeDIC research row."""
    drug_id = assoc.get("drug_id") or ""
    drug_label = assoc.get("drug_label") or ""

    evidence = [build_research_evidence(ev) for ev in assoc.get("evidence") or []]

    curator = assoc.get("curator")
    curator_obj: dict = {}
    if isinstance(curator, dict):
        curator_obj = _strip_empty(dict(curator))
    elif isinstance(curator, str) and curator:
        curator_obj = {"name": curator}

    out: dict = {
        "drug_label": drug_label,
        "drug_id": drug_id,
        "relationship_type": "RESEARCH",
        "curation_status": assoc.get("curation_status") or "",
        "curation_date": assoc.get("curation_date") or "",
        "curator": curator_obj,
        "deep_research_used": assoc.get("deep_research_used"),
        "notes": assoc.get("notes") or "",
        "evidence": evidence,
    }
    # `deep_research_used` is a bool; only drop it when None.
    if out["deep_research_used"] is None:
        out.pop("deep_research_used")
    return _strip_empty(out)


def aggregate_indications(
    path: Path,
    indications: dict[str, list[dict]],
    contraindications: dict[str, list[dict]],
) -> None:
    """Read indication / contraindication associations and split by disease."""
    data = load_yaml(path)
    for assoc in data.get("associations", []):
        disease_id = assoc.get("final_normalized_disease_id") or ""
        if not disease_id:
            continue
        drug_assoc = build_indication_assoc(assoc)
        rel_type = assoc.get("relationship_type") or ""
        if rel_type == "CONTRAINDICATION":
            contraindications[disease_id].append(drug_assoc)
        else:
            indications[disease_id].append(drug_assoc)


def aggregate_research(path: Path, research: dict[str, list[dict]]) -> None:
    """Read research associations and group by disease."""
    data = load_yaml(path)
    for assoc in data.get("associations", []):
        disease_id = assoc.get("disease_id") or ""
        if not disease_id:
            continue
        research[disease_id].append(build_research_assoc(assoc))


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

    priority_diseases = load_priority_diseases(diseases)
    click.echo(f"Loaded {len(priority_diseases)} priority diseases")

    indications: dict[str, list[dict]] = defaultdict(list)
    contraindications: dict[str, list[dict]] = defaultdict(list)
    research: dict[str, list[dict]] = defaultdict(list)

    aggregate_indications(products_dir / "indication_list.yaml", indications, contraindications)
    aggregate_indications(products_dir / "contraindication_list.yaml", indications, contraindications)
    aggregate_research(products_dir / "research_list.yaml", research)

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

        if any(disease_id in store for store in (indications, contraindications, research)):
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
        yaml.dump(
            report,
            f,
            Dumper=NoAliasDumper,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    click.echo(f"Written {len(disease_records)} disease records to {output}")
    click.echo(f"  {diseases_with_data} diseases have at least one association")
    click.echo(f"  {len(disease_records) - diseases_with_data} diseases have no data yet")


if __name__ == "__main__":
    main()
