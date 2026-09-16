"""Coverage, lane mix and disputed counts for the frailty curation."""
import collections
from common import load_source, ASSESSMENTS

def main():
    src = load_source()
    diseases = src["diseases"]
    total = len(diseases)

    curated = 0
    status = collections.Counter()
    impair = {s: collections.Counter() for s in ASSESSMENTS}
    lanes = collections.Counter()
    context = collections.Counter()
    strength = collections.Counter()
    with_lit = set()
    n_ev = 0
    lane_pairs = collections.Counter()

    for d in diseases:
        touched = False
        for slot in ASSESSMENTS:
            a = d.get(slot)
            if not isinstance(a, dict):
                continue
            touched = True
            status[a.get("curation_status", "UNREVIEWED")] += 1
            impair[slot][a.get("impairment", "UNKNOWN")] += 1
            context[a.get("care_context", "UNKNOWN")] += 1
            ev = a.get("evidence") or []
            n_ev += len(ev)
            seen = set()
            for e in ev:
                lanes[e.get("lane")] += 1
                strength[e.get("strength")] += 1
                seen.add(e.get("lane"))
                if e.get("lane") == "LITERATURE":
                    with_lit.add(d["mondo_id"])
            lane_pairs[len(seen)] += 1
        if touched:
            curated += 1

    def block(title, counter, denom=None):
        print(f"\n{title}")
        for k, v in counter.most_common():
            pct = f"  ({v / denom:.0%})" if denom else ""
            print(f"  {str(k):<28} {v:>5}{pct}")

    print(f"Diseases in list            : {total}")
    print(f"Diseases with an assessment : {curated}  ({curated / total:.1%})")
    print(f"Assessments written         : {sum(status.values())}")
    print(f"Evidence lines              : {n_ev}")
    if curated:
        print(f"Diseases with a LITERATURE line: {len(with_lit)}  "
              f"({len(with_lit) / curated:.0%} of curated)")

    block("Curation status", status)
    for slot in ASSESSMENTS:
        block(f"Impairment — {slot}", impair[slot])
    block("Care context", context)
    block("Evidence lanes", lanes)
    block("Evidence strength", strength)
    block("Distinct lanes per assessment", lane_pairs)

if __name__ == "__main__":
    main()
