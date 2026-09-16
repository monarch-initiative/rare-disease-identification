"""Step 4: compare our ranking against live state medically-frail code lists.

Two questions:
  1. CODEABILITY - can this disease be selected from claims data at all?
  2. COVERAGE    - if it can, does any state's list actually reach it?
"""
import collections, csv, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD, SL = ROOT / "build", ROOT / "data/state_lists"
MONDO_OBO = pathlib.Path("/Users/matentzn/ws/ont/mondo/mondo.obo")

NEB = set(open(SL / "nebraska_icd10cm.txt").read().split())
NEBX = set(open(SL / "nebraska_chapter_ranges.txt").read().split())
MN = set(open(SL / "minnesota_icd10cm.txt").read().split())

def reaches(code, S, X=frozenset()):
    """A state list reaches a Mondo ICD xref if it lists the code, a parent chapter range,
    or any child of it (states enumerate 5-6 char children of 4 char concepts)."""
    c = code.replace(".", "").upper()
    if c in S or any(c.startswith(p) for p in X): return True
    return any(s.startswith(c) for s in S)

def mondo_icd():
    m2i = collections.defaultdict(set); lbl = {}; rare = set()
    cur = None; obs = False
    for line in open(MONDO_OBO, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("id: MONDO:"): cur = line[4:]; obs = False
        elif cur is None: continue
        elif line.startswith("is_obsolete: true"): obs = True
        elif obs: continue
        elif line.startswith("name: "): lbl[cur] = line[6:]
        elif line.startswith("subset: ") and "rare" in line: rare.add(cur)
        elif line.startswith("xref: ICD10CM:"):
            m2i[cur].add(line.split("ICD10CM:")[1].split()[0].replace(".", "").upper())
    return m2i, lbl, rare

def main():
    m2i, lbl, rare = mondo_icd()
    rc = rare & set(m2i)
    print(f"Mondo classes with an ICD-10-CM xref : {len(m2i)}   (rare subset: {len(rc)})\n")
    neb = {m for m in rc if any(reaches(c, NEB, NEBX) for c in m2i[m])}
    mn  = {m for m in rc if any(reaches(c, MN) for c in m2i[m])}
    print(f"  Nebraska  reaches {len(neb):4d} / {len(rc)} = {len(neb)/len(rc):.0%} of codeable rare disease")
    print(f"  Minnesota reaches {len(mn):4d} / {len(rc)} = {len(mn)/len(rc):.0%}")
    print(f"  both {len(neb&mn)}   either {len(neb|mn)}   NEITHER {len(rc-(neb|mn))} ({len(rc-(neb|mn))/len(rc):.0%})")
    print(f"  the two states agree on {len(MN&NEB)} of MN's {len(MN)} codes = {len(MN&NEB)/len(MN):.0%}\n")

    rows = list(csv.DictReader(open(BUILD / "ranked.tsv"), delimiter="\t"))
    for r in rows:
        codes = m2i.get(r["mondo_id"], set())
        r["icd10cm"] = ",".join(sorted(codes))
        r["claims_selectable"] = "yes" if codes else "no"
        r["in_nebraska"] = "yes" if codes and any(reaches(c, NEB, NEBX) for c in codes) else ("no" if codes else "")
        r["in_minnesota"] = "yes" if codes and any(reaches(c, MN) for c in codes) else ("no" if codes else "")
        r["care_score"] = float(r["care_score"]); r["work_score"] = float(r["work_score"])

    print("OUR RANKING vs THE STATES")
    print(f"  {'top N':<8}{'claims-selectable':>19}{'Nebraska reaches':>19}{'Minnesota reaches':>19}")
    for n in (100, 250, 500, 1000, len(rows)):
        top = sorted(rows, key=lambda r: -r["care_score"])[:n]
        h = [r for r in top if r["claims_selectable"] == "yes"]
        print(f"  {n:<8}{f'{len(h)} ({len(h)/n:.0%})':>19}"
              f"{sum(1 for r in h if r['in_nebraska']=='yes'):>19}"
              f"{sum(1 for r in h if r['in_minnesota']=='yes'):>19}")

    gap = [r for r in sorted(rows, key=lambda r: -r["care_score"])
           if r["claims_selectable"] == "yes" and r["in_nebraska"] == "no" and r["in_minnesota"] == "no"]
    print(f"\nTHE DELTA: {len(gap)} ranked rare diseases that HAVE a billable code and NEITHER state reaches")
    for r in gap[:15]:
        print(f"   {r['care_score']:5.1f}  {r['label'][:52]:<52} ICD10CM:{r['icd10cm'][:22]}")

    with open(BUILD / "state_comparison.tsv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t"); w.writeheader(); w.writerows(rows)
    print(f"\n-> build/state_comparison.tsv")

if __name__ == "__main__":
    main()
