"""Export a flat one-row-per-(disease, drug) indication table from data/drugs.yml.

Output: data/indications_table.tsv

Only includes diseases present in data/drugs.yml (which is already constrained to
the prioritised list via build_drugs). One row per (mondo_id, drug_id) pair from
the `indications` list. All authorities for that pair are collapsed into a single
row using either summary columns or per-authority columns.
"""

from __future__ import annotations

import csv
from collections import OrderedDict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "drugs.yml"
OUT = ROOT / "data" / "indications_table.tsv"

CONFIDENCE_RANK = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0, None: 0, "": 0}
ORDERED_AUTHORITIES = ["FDA", "EMA", "PMDA", "CDSCO", "MOH_RUSSIA"]

SEARCH_FALLBACK_HINTS = (
    "search_api_fulltext",
    "/english/search/search.html",
    "/PmdaSearch/iyakuSearch",
    "Approved-New-Drugs/",
    "grls.rosminzdrav.ru/Default.aspx",
    "/dailymed/search.cfm",
)


def is_direct_link(url: str | None) -> bool:
    if not url:
        return False
    u = url.lower()
    return not any(hint.lower() in u for hint in SEARCH_FALLBACK_HINTS)


def best_url_for_authority(rs_rows: list[dict]) -> str | None:
    """Pick a single representative URL per authority — prefer direct over fallback."""
    direct = [r.get("regulatory_document_url") for r in rs_rows if is_direct_link(r.get("regulatory_document_url"))]
    if direct:
        return direct[0]
    for r in rs_rows:
        if r.get("regulatory_document_url"):
            return r["regulatory_document_url"]
    return None


def max_confidence(values: list[str | None]) -> str:
    best = max((CONFIDENCE_RANK.get(v, 0) for v in values), default=0)
    if best == 0:
        return ""
    for k, v in CONFIDENCE_RANK.items():
        if v == best and k:
            return k
    return ""


def join_unique(values, sep: str = " | ", limit: int | None = None) -> str:
    seen = OrderedDict()
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if not s:
            continue
        seen.setdefault(s, None)
    out = list(seen.keys())
    if limit is not None and len(out) > limit:
        out = out[:limit] + [f"... (+{len(seen) - limit} more)"]
    return sep.join(out)


def main() -> None:
    data = yaml.safe_load(SRC.read_text())
    diseases = data["diseases"]

    rows: list[dict] = []

    for disease in diseases:
        mondo_id = disease.get("disease_id")
        mondo_label = disease.get("disease_label")

        indications = disease.get("indications") or []
        if not indications:
            continue

        research_drug_ids = {r.get("drug_id") for r in (disease.get("research") or []) if r.get("drug_id")}
        contra_drug_ids = {c.get("drug_id") for c in (disease.get("contraindications") or []) if c.get("drug_id")}

        for ind in indications:
            drug_id = ind.get("drug_id")
            drug_label = ind.get("drug_label")
            reg_status = ind.get("regulatory_status") or []
            evidence = ind.get("evidence") or []

            # Group regulatory_status rows by authority
            by_authority: dict[str, list[dict]] = {}
            for rs in reg_status:
                auth = rs.get("authority") or "UNKNOWN"
                by_authority.setdefault(auth, []).append(rs)

            authorities = sorted(by_authority.keys())

            approval_dates = [rs.get("approval_date") for rs in reg_status if rs.get("approval_date")]
            statuses = [rs.get("status") for rs in reg_status if rs.get("status")]
            source_roles = [rs.get("source_role") for rs in reg_status if rs.get("source_role")]

            urls_all = [rs.get("regulatory_document_url") for rs in reg_status if rs.get("regulatory_document_url")]
            direct_urls = [u for u in urls_all if is_direct_link(u)]

            # Evidence aggregation
            ev_snippets = [e.get("snippet") for e in evidence if e.get("snippet")]
            ev_explanations = [e.get("explanation") for e in evidence if e.get("explanation")]
            ev_orig_drug_labels = [e.get("original_drug_label") for e in evidence if e.get("original_drug_label")]
            ev_orig_disease_labels = [e.get("original_disease_label") for e in evidence if e.get("original_disease_label")]
            ev_orig_drug_ids = [e.get("original_drug_id") for e in evidence if e.get("original_drug_id")]
            ev_orig_disease_ids = [e.get("original_disease_id") for e in evidence if e.get("original_disease_id")]
            ev_source_types = [e.get("source_type") for e in evidence if e.get("source_type")]
            ev_jurisdictions = [e.get("jurisdiction") for e in evidence if e.get("jurisdiction")]
            ev_references = [e.get("reference") for e in evidence if e.get("reference")]

            row = {
                "mondo_id": mondo_id,
                "mondo_label": mondo_label,
                "drug_id": drug_id,
                "drug_label": drug_label,
                "authorities": "|".join(authorities),
                "n_authorities": len(authorities),
                "approval_statuses": join_unique(statuses, sep="|"),
                "earliest_approval_date": min(approval_dates) if approval_dates else "",
                "latest_approval_date": max(approval_dates) if approval_dates else "",
                "source_roles": join_unique(source_roles, sep="|"),
                "has_primary_source": "PRIMARY" in source_roles,
                "n_regulatory_status_rows": len(reg_status),
                "n_evidence_rows": len(evidence),
                "has_direct_regulatory_link": bool(direct_urls),
                "n_direct_regulatory_links": len(direct_urls),
                "regulatory_document_urls": join_unique(urls_all, sep=" | "),
                "evidence_references": join_unique(ev_references, sep=" | "),
                "evidence_source_types": join_unique(ev_source_types, sep="|"),
                "evidence_jurisdictions": join_unique(ev_jurisdictions, sep="|"),
                "snippets": join_unique(ev_snippets, sep=" || "),
                "explanations": join_unique(ev_explanations, sep=" || "),
                "original_drug_labels": join_unique(ev_orig_drug_labels, sep=" | "),
                "original_drug_ids": join_unique(ev_orig_drug_ids, sep=" | "),
                "original_disease_labels": join_unique(ev_orig_disease_labels, sep=" | "),
                "original_disease_ids": join_unique(ev_orig_disease_ids, sep=" | "),
                "confidence_overall_max": max_confidence([e.get("confidence") for e in evidence]),
                "confidence_drug_max": max_confidence([e.get("confidence_drug") for e in evidence]),
                "confidence_disease_max": max_confidence([e.get("confidence_disease") for e in evidence]),
                "confidence_association_max": max_confidence([e.get("confidence_association") for e in evidence]),
                "also_in_research": drug_id in research_drug_ids,
                "also_in_contraindications": drug_id in contra_drug_ids,
            }

            # Per-authority columns
            for auth in ORDERED_AUTHORITIES:
                rs_rows = by_authority.get(auth, [])
                if not rs_rows:
                    row[f"{auth.lower()}_status"] = ""
                    row[f"{auth.lower()}_approval_date"] = ""
                    row[f"{auth.lower()}_source_role"] = ""
                    row[f"{auth.lower()}_url"] = ""
                    row[f"{auth.lower()}_url_is_direct"] = ""
                    row[f"{auth.lower()}_n_records"] = 0
                    continue
                dates = [r.get("approval_date") for r in rs_rows if r.get("approval_date")]
                statuses_a = [r.get("status") for r in rs_rows if r.get("status")]
                roles_a = [r.get("source_role") for r in rs_rows if r.get("source_role")]
                best_url = best_url_for_authority(rs_rows)
                row[f"{auth.lower()}_status"] = join_unique(statuses_a, sep="|")
                row[f"{auth.lower()}_approval_date"] = min(dates) if dates else ""
                row[f"{auth.lower()}_source_role"] = join_unique(roles_a, sep="|")
                row[f"{auth.lower()}_url"] = best_url or ""
                row[f"{auth.lower()}_url_is_direct"] = is_direct_link(best_url)
                row[f"{auth.lower()}_n_records"] = len(rs_rows)

            rows.append(row)

    if not rows:
        print("No indication rows produced.")
        return

    # Stable column order
    fieldnames = list(rows[0].keys())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    n_diseases = len({r["mondo_id"] for r in rows})
    n_drugs = len({r["drug_id"] for r in rows})
    print(f"Wrote {len(rows):,} rows ({n_diseases:,} diseases × {n_drugs:,} unique drugs) to {OUT}")
    print(f"Columns: {len(fieldnames)}")
    for fn in fieldnames:
        print(f"  - {fn}")


if __name__ == "__main__":
    main()
