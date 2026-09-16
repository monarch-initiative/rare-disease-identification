#!/usr/bin/env python3
"""Look up POLICY_LIST evidence for one or more MONDO ids.

    python3 scripts/policy_lookup.py MONDO:0016532 MONDO:0010726
    python3 scripts/policy_lookup.py --yaml MONDO:0016532     # ready to paste

Prints nothing but a NOT LISTED line when there is no hit. That is the correct
output, and it is NOT evidence against the disease - see the note it prints.
"""
import csv, pathlib, sys, collections
TSV = pathlib.Path(__file__).resolve().parents[1] / "build/policy_evidence.tsv"
SRC = {"Nebraska": "Nebraska Medicaid Medically Frail Exemption Conditions Index",
       "Minnesota": "Minnesota DHS Appendix A, medically frail definition (PL 119-21 s71119)",
       "Montana": "Montana DPHHS medically frail conditions"}

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_yaml = "--yaml" in sys.argv
    if not args: sys.exit("usage: policy_lookup.py [--yaml] MONDO:NNNNNNN ...")
    rows = collections.defaultdict(list)
    for r in csv.DictReader(open(TSV), delimiter="\t"): rows[r["mondo_id"]].append(r)
    for mid in args:
        hits = rows.get(mid, [])
        if not hits:
            print(f"# {mid}: NOT LISTED by Nebraska, Minnesota or Montana.")
            print("# This is NOT a DISPUTES line. Most rare diseases carry no ICD-10-CM code,")
            print("# so absence from a code-based list carries no information. Omit the lane.")
            continue
        if not as_yaml:
            for h in hits:
                print(f"{mid}  {h['source']:<10} {h['match_type']:<22} {h['matched_value']}")
            continue
        for h in hits:
            cat = f"\n  source_statement: \"statutory category: {h['statutory_category']}\"" if h["statutory_category"] else ""
            print(f"""- lane: POLICY_LIST
  direction: SUPPORTS
  strength: MODERATE
  reference: {h['matched_value']}
  reference_title: {SRC[h['source']]}{cat}
  explanation: >-
    {h['source']} treats this disease as qualifying for the medically-frail exemption
    (match: {h['match_type']}).
  curator_type: PIPELINE""")

if __name__ == "__main__":
    main()
