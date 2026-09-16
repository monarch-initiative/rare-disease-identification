"""Emit the next N unreviewed diseases for frailty curation, highest score first.

Selection, in order:
  1. drop anything already curated (curation_status present and not UNREVIEWED)
  2. sort by max(work_score, care_score) descending
  3. take N

Each row carries what the five lanes need, so the curator does not have to go
hunting: Orphanet codes that actually have a cached functional record, ICD-10-CM
codes, and which state lists already reach those codes.
"""
import argparse, csv
from common import (RANKED, ASSERTIONS, FC, CACHE, TMP,
                    ASSESSMENTS, load_source, orpha_codes, icd10cm_codes)


def read_tsv(path, key="mondo_id"):
    with open(path, encoding="utf-8") as fh:
        return {r[key]: r for r in csv.DictReader(fh, delimiter="\t")}


def policy_index():
    """MONDO id -> set of states that reach it, from the authoritative policy table.

    Read the table; do not re-derive it from the raw code lists. See the note in
    skeleton.policy_index - 42% of hits come from Mondo's 4-character code matching
    the state list's 5-6 character children, which exact matching misses.
    """
    tsv = FC / "build/policy_evidence.tsv"
    if not tsv.exists():
        raise SystemExit(f"missing {tsv}\nRebuild: python3 "
                         "functional-capacity/scripts/step9_policy_evidence.py")
    out = {}
    with open(tsv, encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            out.setdefault(r["mondo_id"], set()).add(r["source"])
    return out


def curated(disease):
    """True if a human or agent has already settled both assessments."""
    for slot in ASSESSMENTS:
        a = disease.get(slot)
        if isinstance(a, dict) and a.get("curation_status") not in (None, "UNREVIEWED"):
            return True
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("n", type=int)
    ap.add_argument("-o", "--output", default=str(TMP / "frailty_worklist.tsv"))
    args = ap.parse_args()
    if args.n <= 0:
        ap.error("N must be a positive integer")

    ranked = read_tsv(RANKED)
    asserts = read_tsv(ASSERTIONS)
    policy = policy_index()
    src = load_source()

    rows = []
    for d in src["diseases"]:
        if curated(d):
            continue
        mid = d["mondo_id"]
        r = ranked.get(mid, {})
        a = asserts.get(mid, {})
        work = float(r.get("work_score") or 0)
        care = float(r.get("care_score") or 0)

        orpha = [c for c in orpha_codes(d) if (CACHE / f"ORPHA_{c}.md").exists()]
        icd = icd10cm_codes(d) or ([a["icd10cm"]] if a.get("icd10cm") else [])
        hits = sorted(policy.get(mid, ()))

        rows.append({
            "mondo_id": mid,
            "label": d.get("mondo_label", ""),
            "work_score": f"{work:.2f}",
            "care_score": f"{care:.2f}",
            "max_score": f"{max(work, care):.2f}",
            "n_phenotypes": r.get("n_phenotypes", ""),
            "orpha_cached": ";".join(f"ORPHA:{c}" for c in orpha),
            "icd10cm": ";".join(icd),
            "claims_selectable": a.get("claims_selectable", ""),
            "state_lists": ";".join(hits),
            "top_work_drivers": r.get("top_work_drivers", ""),
            "top_care_drivers": r.get("top_care_drivers", ""),
        })

    rows.sort(key=lambda r: float(r["max_score"]), reverse=True)
    rows = rows[: args.n]

    TMP.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    with_orpha = sum(1 for r in rows if r["orpha_cached"])
    print(f"worklist: {len(rows)} diseases -> {args.output}")
    print(f"  with a cached Orphanet record : {with_orpha}")
    print(f"  with an ICD-10-CM code        : {sum(1 for r in rows if r['icd10cm'])}")
    print(f"  already on a state list       : {sum(1 for r in rows if r['state_lists'])}")


if __name__ == "__main__":
    main()
