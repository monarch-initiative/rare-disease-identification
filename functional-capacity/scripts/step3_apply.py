"""Step 3: robustness checks, then apply the ranking to the full prioritised list."""
import csv, collections, pathlib, sqlite3, sys, json
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from step2_score import (score_of, profile, parse_phen, auc, prec_at, AGG, label, BUILD, DATA)

PRIMARY = "wsum_norm"   # count-normalised: beats count-only baseline in every annotation-depth stratum

val = list(csv.DictReader(open(BUILD / "validation.tsv"), delimiter="\t"))
def sc(v, i): return AGG[PRIMARY](profile(parse_phen(v["phenotypes"])), i)

print("=" * 78)
print("ROBUSTNESS CHECKS  (aggregator = %s)" % PRIMARY)
print("=" * 78)

NEURO = {"HP:0012638", "HP:0000707", "HP:0001249", "HP:0001263", "HP:0012759"}
import sqlite3, pathlib as pl
con = sqlite3.connect(pl.Path.home() / ".data/oaklib/hp.db")
anc = collections.defaultdict(set)
for s, o in con.execute("select subject,object from entailed_edge where predicate='rdfs:subClassOf'"
                        " and subject like 'HP:%' and object like 'HP:%'"):
    anc[s].add(o)
def is_neuro(v):
    return any(t in NEURO or (anc.get(t, set()) & NEURO) for t in parse_phen(v["phenotypes"]))

for axis, i, key in (("WORK", 0, "work"), ("CARE", 1, "care")):
    print(f"\n--- {axis}")
    for name, sub in (("all validation diseases", val),
                      ("TIER A only (expert-validated labels)", [v for v in val if v["tier"] == "A"]),
                      ("neuro-annotated only (is it just 'finds neuro'?)", [v for v in val if is_neuro(v)]),
                      ("NON-neuro only", [v for v in val if not is_neuro(v)])):
        if len(sub) < 25: 
            print(f"  {name:<50} n={len(sub):4d}  (too small)"); continue
        pairs = [(sc(v, i), int(v[key])) for v in sub]
        base = sum(y for _, y in pairs) / len(pairs)
        print(f"  {name:<50} n={len(sub):4d}  base={base:.0%}  AUC={auc(pairs):.3f}"
              f"  P@25={prec_at(pairs,25):.2f}  lift={prec_at(pairs,25)/base if base else 0:.1f}x")

# ---------------------------------------------------------------- apply to corpus
rows = list(csv.DictReader(open(BUILD / "corpus.tsv"), delimiter="\t"))
rows = [r for r in rows if int(r["n_phenotypes"]) > 0]
out = []
for r in rows:
    phen = parse_phen(r["phenotypes"]); p = profile(phen)
    def drivers(axis):
        d = sorted(((score_of(t)[axis] * f, t) for t, f in phen.items()), reverse=True)
        return "; ".join(f"{label.get(t,t)}" for v, t in d[:4] if v > 0)
    top_w, top_c = drivers(0), drivers(1)
    out.append(dict(mondo_id=r["mondo_id"], label=r["label"],
                    work_score=round(AGG[PRIMARY](p, 0), 2), care_score=round(AGG[PRIMARY](p, 1), 2),
                    n_phenotypes=r["n_phenotypes"], n_scored=len(p),
                    gold_work=r["gold_work"], gold_care=r["gold_care"], gold_tier=r["gold_tier"],
                    top_work_drivers=top_w, top_care_drivers=top_c))

for key, nm in (("work_score", "WORK"), ("care_score", "CARE")):
    out.sort(key=lambda r: -r[key])
    for rank, r in enumerate(out, 1): r[nm.lower() + "_rank"] = rank
out.sort(key=lambda r: -r["work_score"])

with open(BUILD / "ranked.tsv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]), delimiter="\t"); w.writeheader(); w.writerows(out)
json.dump(out, open(BUILD / "ranked.json", "w"), indent=0)

print("\n" + "=" * 78)
print(f"APPLIED TO PRIORITISED LIST: {len(out)} diseases ranked")
print("=" * 78)
for key, nm in (("work_score", "TOP 20 - likely unable to sustain employment"),
                ("care_score", "TOP 20 - likely needs daily personal care")):
    print(f"\n{nm}")
    for r in sorted(out, key=lambda r: -r[key])[:20]:
        g = {"1": "gold+", "0": "gold-", "": "  -  "}[r["gold_work" if key == "work_score" else "gold_care"]]
        print(f"  {r[key]:6.1f} {g}  {r['label'][:58]:<58} {r['mondo_id']}")
