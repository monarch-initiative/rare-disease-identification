#!/usr/bin/env python3
"""Assemble the reviewable MONDO -> ICD-10-CM exact-match SSSOM set.

Merges three provenance tiers, strongest first, one row per Mondo term:

  1. `semapv:ManualMappingCuration` — Mondo's own asserted `skos:exactMatch` to
     ICD-10-CM, taken from the Mondo SSSOM release. Curated upstream, trusted as-is.
  2. `semapv:LexicalMatching`       — stage-1 deterministic ladder (raw / normalized /
     exact-preserving surgery), with the rule chain in `subject_preprocessing`.
  3. `semapv:CompositeMatching`     — stage-2 agentic adjudication: lexical retrieval
     proposed candidates, an LLM decided concept equivalence. `comment` carries the
     reviewer's one-sentence reason, which is the point of the file being reviewable.

Terms with no exact match are still emitted, as `sssom:NoTermFound`, so absence is
stated rather than inferred from a missing row. That is a deliberate choice: a
consumer pulling cohorts needs to tell "no code exists" from "we did not look".
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

import click
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from lexmatch import load_icd10cm  # noqa: E402

try:
    from yaml import CSafeLoader as _Loader
except ImportError:  # pragma: no cover
    from yaml import SafeLoader as _Loader

COLUMNS = [
    "subject_id", "subject_label", "predicate_id", "object_id", "object_label",
    "mapping_justification", "mapping_tool", "confidence",
    "subject_preprocessing", "match_string", "object_match_field",
    "subject_type", "object_type", "comment",
]

CURIE_MAP = {
    "ICD10CM": "http://purl.bioontology.org/ontology/ICD10CM/",
    "MONDO": "http://purl.obolibrary.org/obo/MONDO_",
    "infores": "https://w3id.org/information-resource-registry/",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "semapv": "https://w3id.org/semapv/vocab/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "sssom": "https://w3id.org/sssom/",
}

NO_TERM = "sssom:NoTermFound"


def load_mondo_asserted(path: Path, wanted: set[str]) -> dict[str, dict]:
    if not path.exists():
        return {}
    lines = [line for line in path.read_text().splitlines() if not line.startswith("#")]
    out = {}
    for row in csv.DictReader(lines, delimiter="\t"):
        sid = row.get("subject_id")
        if sid in wanted and row.get("object_id"):
            out[sid] = row
    return out


@click.command()
@click.option("--diseases", type=click.Path(exists=True, path_type=Path),
              default=Path("src/prioritised-rare-disease-list.yml"))
@click.option("--work-dir", type=click.Path(exists=True, path_type=Path),
              default=Path("tmp/icd10cm"))
@click.option("--mondo-sssom", type=click.Path(path_type=Path),
              default=Path("tmp/sssom/mondo_exactmatch_icd10cm.sssom.tsv"))
@click.option("--output", "-o", type=click.Path(path_type=Path),
              default=Path("mappings/mondo_icd10cm_exactmatch.sssom.tsv"))
@click.option("--icd-ttl", type=click.Path(exists=True, path_type=Path),
              default=Path(Path.home() / "ws/projects/medic/background/ontsrc/icd10cm.owl"))
@click.option("--model", default="claude-opus-5", show_default=True,
              help="Model that performed stage-2 adjudication, recorded as mapping_tool.")
def main(diseases, work_dir, mondo_sssom, output, icd_ttl, model):
    """Merge stage-1 and stage-2 outputs into one SSSOM file."""
    with open(diseases) as f:
        data = yaml.load(f, Loader=_Loader)
    entries = [d for d in data.get("diseases", []) if d.get("mondo_id")]
    wanted = {d["mondo_id"] for d in entries}

    lexical = json.loads((work_dir / "lexical_matches.json").read_text())
    queue = json.loads((work_dir / "review_queue.json").read_text())
    asserted = load_mondo_asserted(mondo_sssom, wanted)

    valid_codes = {c for c, _, _, _ in load_icd10cm(icd_ttl)}

    decisions: dict[str, dict] = {}
    dec_dir = work_dir / "decisions"
    missing_batches = []
    for batch in sorted((work_dir / "batches").glob("batch_*.json")):
        out_file = dec_dir / batch.name
        if not out_file.exists():
            missing_batches.append(batch.name)
            continue
        try:
            for d in json.loads(out_file.read_text()):
                if d.get("mondo_id"):
                    decisions[d["mondo_id"]] = d
        except json.JSONDecodeError as exc:
            missing_batches.append(f"{batch.name} (unparseable: {exc})")

    # Terms whose only lexical hit was a residual rubric ("Other porphyria") are
    # adjudicated separately; those decisions override nothing, they just join the pool.
    residual = work_dir / "decisions_residual.json"
    if residual.exists():
        for d in json.loads(residual.read_text()):
            if d.get("mondo_id"):
                decisions[d["mondo_id"]] = d

    rows, stats = [], {"mondo": 0, "lexical": 0, "agentic": 0, "none": 0,
                       "invalid_mondo": 0}
    for d in sorted(entries, key=lambda e: e["mondo_id"]):
        mid = d["mondo_id"]
        label = (lexical.get(mid, {}).get("label")
                 or queue.get(mid, {}).get("label")
                 or d.get("mondo_label", ""))
        base = {"subject_id": mid, "subject_label": label,
                "subject_type": "owl class", "object_type": "owl class"}

        if mid in asserted:
            a = asserted[mid]
            code = a["object_id"].split(":", 1)[1] if ":" in a["object_id"] else ""
            # Mondo's exact-match release carries a handful of object_ids that are not
            # ICD-10-CM codes at all: chapter ranges (E00-E90) and ICD-11-style codes
            # (QA0.0142). Passing those on would hand a consumer something unpullable,
            # so record the assertion in the comment and emit NoTermFound.
            if code in valid_codes:
                rows.append({**base, "predicate_id": "skos:exactMatch",
                             "object_id": a["object_id"],
                             "object_label": a.get("object_label", ""),
                             "mapping_justification": "semapv:ManualMappingCuration",
                             "mapping_tool": "mondo", "confidence": "1.0",
                             "comment": "Asserted by Mondo's own ICD-10-CM exact-match release."})
                stats["mondo"] += 1
            else:
                rows.append({**base, "predicate_id": "skos:exactMatch",
                             "object_id": NO_TERM, "object_label": "",
                             "mapping_justification": "semapv:ManualMappingCuration",
                             "mapping_tool": "mondo", "confidence": "0.0",
                             "comment": f"Mondo asserts {a['object_id']}, which is not a code "
                                        f"in the ICD-10-CM 2024ab release (chapter range or "
                                        f"non-ICD-10-CM identifier); dropped as unusable."})
                stats["invalid_mondo"] += 1
            continue

        if mid in lexical:
            m = lexical[mid]
            rows.append({**base, "predicate_id": "skos:exactMatch",
                         "object_id": f"ICD10CM:{m['code']}", "object_label": m["object_label"],
                         "mapping_justification": "semapv:LexicalMatching",
                         "mapping_tool": "rdi-lexmatch", "confidence": f"{m['confidence']:.4f}",
                         "subject_preprocessing": "|".join(m["preprocessing"]),
                         "match_string": m["match_string"],
                         "object_match_field": ("rdfs:label" if m["field"] == "label"
                                                else "oio:hasExactSynonym"),
                         "comment": f"Lexical tier {m['tier']} on the Mondo {m['query_kind']}."})
            stats["lexical"] += 1
            continue

        dec = decisions.get(mid)
        if dec and dec.get("exact") and dec.get("code"):
            code = str(dec["code"]).replace("ICD10CM:", "")
            cand = {c["code"]: c for c in queue.get(mid, {}).get("candidates", [])}
            rows.append({**base, "predicate_id": "skos:exactMatch",
                         "object_id": f"ICD10CM:{code}",
                         "object_label": cand.get(code, {}).get("icd_label", ""),
                         "mapping_justification": "semapv:CompositeMatching",
                         "mapping_tool": model,
                         "confidence": f"{float(dec.get('confidence', 0.8)):.4f}",
                         "subject_preprocessing": "agentic_review",
                         "comment": dec.get("justification", "")})
            stats["agentic"] += 1
            continue

        comment = (dec.get("justification") if dec
                   else "No ICD-10-CM candidate retrieved for this term.")
        rows.append({**base, "predicate_id": "skos:exactMatch", "object_id": NO_TERM,
                     "object_label": "",
                     "mapping_justification": ("semapv:CompositeMatching" if dec
                                               else "semapv:LexicalMatching"),
                     "mapping_tool": model if dec else "rdi-lexmatch",
                     "confidence": "0.0", "comment": comment})
        stats["none"] += 1

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="") as f:
        f.write("# curie_map:\n")
        for k, v in sorted(CURIE_MAP.items()):
            f.write(f"#   {k}: {v}\n")
        f.write("# license: https://creativecommons.org/publicdomain/zero/1.0/\n")
        f.write("# mapping_set_id: https://w3id.org/monarch-initiative/"
                "rare-disease-identification/mappings/mondo_icd10cm_exactmatch\n")
        f.write(f"# mapping_set_version: {date.today().isoformat()}\n")
        f.write("# mapping_set_title: Prioritised rare disease list, MONDO to ICD-10-CM "
                "exact matches\n")
        f.write("# subject_source: infores:mondo\n")
        f.write("# object_source: infores:icd10cm\n")
        f.write("# comment: Exact matches only. Rows with object_id sssom:NoTermFound record "
                "a searched-and-not-found decision, not an absence of effort. "
                "semapv:CompositeMatching rows were adjudicated by an LLM over "
                "lexically retrieved candidates and carry the reason in `comment`; "
                "they are proposals for human review, not curated assertions.\n")
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t", extrasaction="ignore",
                           restval="")
        w.writeheader()
        w.writerows(rows)

    total_mapped = stats["mondo"] + stats["lexical"] + stats["agentic"]
    click.echo(f"Written {len(rows)} rows to {output}")
    click.echo(f"  mondo-asserted (ManualMappingCuration) : {stats['mondo']}")
    click.echo(f"  lexical        (LexicalMatching)       : {stats['lexical']}")
    click.echo(f"  agentic        (CompositeMatching)     : {stats['agentic']}")
    click.echo(f"  NoTermFound                            : {stats['none'] + stats['invalid_mondo']}")
    if stats["invalid_mondo"]:
        click.echo(f"    of which Mondo asserted an invalid code: {stats['invalid_mondo']}")
    click.echo(f"  ---> {total_mapped} of {len(rows)} terms have an exact ICD-10-CM match "
               f"({100 * total_mapped / max(len(rows), 1):.1f}%)")
    if missing_batches:
        click.echo(f"\nWARNING: {len(missing_batches)} review batches missing/unparseable: "
                   f"{', '.join(missing_batches)}", err=True)


if __name__ == "__main__":
    main()
