"""Step 5: one assertion per disease, four states, never silence.

Precedence:
  1. Orphanet expert functional data, where it exists          -> EXPERT_*
  2. else the HPO negative guardrail (zero strong anchors)     -> PREDICTED_UNLIKELY  (NPV .94/.97)
  3. else the phenotype ranking                                -> PREDICTED_CANDIDATE / PREDICTED_LOWER
  4. else nothing to go on                                     -> NOT_ASSESSED
Every row carries the evidence and the rule that fired.
"""
import collections, csv, math, pathlib, sqlite3, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from step1_corpus import mondo_index, orphanet_labels, hpoa
from step2_score import scored, score_of, profile, parse_phen, AGG
from step4_policy import mondo_icd, reaches, NEB, NEBX, MN

ROOT = pathlib.Path(__file__).resolve().parents[1]; BUILD = ROOT / "build"
TOP_N = 500            # how deep the candidate band goes
AGGF = AGG["wsum_norm"]

con = sqlite3.connect(pathlib.Path.home() / ".data/oaklib/hp.db")
desc = collections.defaultdict(set)
for s, o in con.execute("select subject,object from entailed_edge where predicate='rdfs:subClassOf'"
                        " and subject like 'HP:%' and object like 'HP:%'"):
    desc[o].add(s)
ANCHOR = {i: set() for i in (0, 1)}
for t, (w, c) in scored.items():
    for i, v in ((0, w), (1, c)):
        if v >= 2: ANCHOR[i] |= desc.get(t, set()) | {t}

def main():
    idx, _ = mondo_index(); labels = orphanet_labels(); ann = hpoa()
    m2i, _, rare = mondo_icd()

    listed = []
    for line in open(ROOT.parent / "prioritised-rare-disease-list.yml", encoding="utf-8"):
        s = line.strip()
        if s.startswith("- mondo_id:") or s.startswith("mondo_id:"):
            listed.append(s.split()[-1])
    scope = dict.fromkeys(listed)
    for code in labels:
        for m, v in idx.items():
            if code in v["xrefs"]: scope.setdefault(m); break
    scope = [m for m in scope if m in idx]

    out = []
    for mid in scope:
        xr = idx[mid]["xrefs"]
        phen = {}
        for x in xr:
            for t, f in ann.get(x, {}).items():
                phen[t] = max(phen.get(t, 0) or 0, f if f is not None else 0.5)
        lab = next((labels[x] for x in xr if x in labels), None)
        p = profile(phen)
        ws, cs = AGGF(p, 0), AGGF(p, 1)
        hi = {t for t, f in phen.items() if f >= 0.30}
        anch = {i: len(hi & ANCHOR[i]) for i in (0, 1)}
        codes = m2i.get(mid, set())
        row = dict(mondo_id=mid, label=idx[mid]["label"],
                   rare="yes" if mid in rare else "no",
                   work_score=round(ws, 2), care_score=round(cs, 2),
                   n_phenotypes=len(phen), n_work_anchors=anch[0], n_care_anchors=anch[1],
                   icd10cm=",".join(sorted(codes)),
                   claims_selectable="yes" if codes else "no",
                   in_nebraska="yes" if codes and any(reaches(c, NEB, NEBX) for c in codes) else ("no" if codes else ""),
                   in_minnesota="yes" if codes and any(reaches(c, MN) for c in codes) else ("no" if codes else ""))
        for i, axis in ((0, "work"), (1, "care")):
            if lab and lab["scope"] == "Activity limitation/participation restriction":
                st = "EXPERT_POSITIVE" if lab[axis] else "EXPERT_NEGATIVE"
                ev, rule = f"Orphanet functional consequences, tier {lab['tier']}", "orphanet_direct"
            elif lab and lab["scope"] == "No functional disability":
                st, ev, rule = "EXPERT_NEGATIVE", "Orphanet: no functional disability", "orphanet_direct"
            elif lab:
                st, ev, rule = "EXPERT_NOT_APPLICABLE", "Orphanet: not applicable", "orphanet_direct"
            elif not phen:
                st, ev, rule = "NOT_ASSESSED", "no HPO annotations", "no_evidence"
            elif anch[i] == 0:
                st, ev, rule = "PREDICTED_UNLIKELY", f"no high-frequency anchor finding (NPV {'0.94' if i==0 else '0.97'})", "hpo_guardrail"
            else:
                st, ev, rule = "PENDING_RANK", f"{anch[i]} anchor findings", "phenotype_ranking"
            row[axis + "_status"] = st; row[axis + "_evidence"] = ev; row[axis + "_rule"] = rule
            row[axis + "_tier"] = (lab["tier"] if lab else ("C" if st.startswith("PREDICTED") else ""))
        out.append(row)

    for i, axis in ((0, "work"), (1, "care")):
        pend = sorted([r for r in out if r[axis + "_status"] == "PENDING_RANK"],
                      key=lambda r: -r[axis + "_score"])
        for n, r in enumerate(pend):
            r[axis + "_status"] = "PREDICTED_CANDIDATE" if n < TOP_N else "PREDICTED_LOWER"
            r[axis + "_rank"] = n + 1
    for r in out:
        for axis in ("work", "care"): r.setdefault(axis + "_rank", "")

    with open(BUILD / "assertions.tsv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]), delimiter="\t"); w.writeheader(); w.writerows(out)

    print(f"ASSERTIONS: {len(out)} Mondo classes  (prioritised list + every Orphanet-covered class)\n")
    for axis in ("care", "work"):
        c = collections.Counter(r[axis + "_status"] for r in out)
        print(f"  {axis.upper():<5}", " | ".join(f"{k} {v}" for k, v in c.most_common()))
    print()
    ct = collections.Counter(r["claims_selectable"] for r in out)
    print(f"  claims-selectable: yes {ct['yes']}  no {ct['no']} ({ct['no']/len(out):.0%})")
    exp = [r for r in out if r["care_status"].startswith("EXPERT") and r["care_status"] != "EXPERT_NOT_APPLICABLE"]
    print(f"  expert-evidenced (either direction): {len(exp)}   of which tier A: {sum(1 for r in exp if r['care_tier']=='A')}")
    print(f"\n-> build/assertions.tsv")

if __name__ == "__main__":
    main()
