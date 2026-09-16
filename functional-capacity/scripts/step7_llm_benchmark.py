"""Step 7: build the blind test set for the LLM benchmark.

Rules of the test:
  - 200 diseases sampled from the 538 with Orphanet expert ratings, stratified so the
    hard cases are represented: neuro / non-neuro x rated-positive / rated-negative.
  - The judge sees ONLY: disease name, Mondo ID, Mondo definition, and the disease's
    recorded symptoms. It never sees the Orphanet rating, the phenotype scores, or the
    rank this pipeline gave it.
  - It answers two yes/no questions with a confidence 0-100.
  - We score it against Orphanet and against the floor set by the phenotype method:
        WORK  AUC 0.797   top-25 correct 64%
        CARE  AUC 0.860   top-25 correct 68%
    and specifically against 0.51 / 0.55 on the non-neuro slice, which is where the
    phenotype method fails.
"""
import collections, csv, json, pathlib, random, sqlite3, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from step2_score import parse_phen, profile, AGG, auc, prec_at

ROOT = pathlib.Path(__file__).resolve().parents[1]; BUILD = ROOT / "build"
MONDO = pathlib.Path("/Users/matentzn/ws/ont/mondo/mondo.obo")
N = 200

def mondo_defs():
    d = {}; cur = None; obs = False
    for line in open(MONDO, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("id: MONDO:"): cur = line[4:]; obs = False
        elif cur is None: continue
        elif line.startswith("is_obsolete: true"): obs = True
        elif obs: continue
        elif line.startswith("def: "): d[cur] = line[6:].split('" [')[0]
    return d

def main():
    con = sqlite3.connect(pathlib.Path.home() / ".data/oaklib/hp.db")
    lbl = dict(con.execute("select subject,value from rdfs_label_statement where subject like 'HP:%'"))
    anc = collections.defaultdict(set)
    for s, o in con.execute("select subject,object from entailed_edge where predicate='rdfs:subClassOf'"
                            " and subject like 'HP:%' and object like 'HP:%'"): anc[s].add(o)
    NEURO = {"HP:0012638", "HP:0000707", "HP:0001249", "HP:0001263", "HP:0012759"}
    defs = mondo_defs()

    val = list(csv.DictReader(open(BUILD / "validation.tsv"), delimiter="\t"))
    for v in val:
        ph = parse_phen(v["phenotypes"]); v["_ph"] = ph
        v["_neuro"] = any(t in NEURO or (anc.get(t, set()) & NEURO) for t in ph)
        p = profile(ph)
        v["_pheno_work"] = AGG["wsum_norm"](p, 0); v["_pheno_care"] = AGG["wsum_norm"](p, 1)

    strata = collections.defaultdict(list)
    for v in val:
        strata[(v["_neuro"], v["care"] == "1", v["work"] == "1")].append(v)
    rng = random.Random(42); pick = []
    per = max(1, N // max(len(strata), 1))
    for k, g in sorted(strata.items(), key=lambda x: str(x[0])):
        rng.shuffle(g); pick += g[:per]
    rest = [v for v in val if v not in pick]; rng.shuffle(rest)
    pick += rest[:max(0, N - len(pick))]
    pick = pick[:N]

    items = []
    for v in pick:
        syms = sorted(((f, lbl.get(t, t)) for t, f in v["_ph"].items()), reverse=True)[:40]
        items.append(dict(mondo_id=v["mondo_id"], label=v["label"],
                          definition=(defs.get(v["mondo_id"], "") or "")[:600],
                          symptoms=[f"{n}{' (common)' if f>=0.5 else ''}" for f, n in syms]))
    json.dump(items, open(BUILD / "llm_input.json", "w"), indent=1)
    key = [dict(mondo_id=v["mondo_id"], label=v["label"], work=int(v["work"]), care=int(v["care"]),
                neuro=v["_neuro"], tier=v["tier"],
                pheno_work=round(v["_pheno_work"], 3), pheno_care=round(v["_pheno_care"], 3)) for v in pick]
    json.dump(key, open(BUILD / "llm_key.json", "w"), indent=1)

    print(f"blind test set: {len(items)} diseases")
    print(f"  Orphanet-rated positive  work {sum(k['work'] for k in key)}  care {sum(k['care'] for k in key)}")
    print(f"  neuro {sum(1 for k in key if k['neuro'])}   non-neuro {sum(1 for k in key if not k['neuro'])}")
    print(f"  tier A labels {sum(1 for k in key if k['tier']=='A')}")
    print("\nFLOOR TO BEAT on this exact subset (phenotype method):")
    for axis in ("work", "care"):
        pr = [(k["pheno_" + axis], k[axis]) for k in key]
        print(f"  {axis:<5} AUC {auc(pr):.3f}   top-25 {prec_at(pr,25):.2f}   base {sum(k[axis] for k in key)/len(key):.2f}")
        for nm, sub in (("neuro", [k for k in key if k["neuro"]]), ("non-neuro", [k for k in key if not k["neuro"]])):
            pr2 = [(k["pheno_" + axis], k[axis]) for k in sub]
            if len(sub) >= 15 and 0 < sum(k[axis] for k in sub) < len(sub):
                print(f"        {nm:<10} n={len(sub):3d}  AUC {auc(pr2):.3f}")
    print(f"\n-> build/llm_input.json (what the judge sees)  build/llm_key.json (held back)")

if __name__ == "__main__":
    main()
