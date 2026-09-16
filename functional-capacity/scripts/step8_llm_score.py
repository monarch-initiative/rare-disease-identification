"""Step 8: score the blind LLM ratings against the Orphanet key and the phenotype floor."""
import glob, json, math, pathlib, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from step2_score import auc, prec_at
BUILD = pathlib.Path(__file__).resolve().parents[1] / "build"

def kappa(a, b):
    n = len(a); po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1 = sum(a) / n; pb1 = sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")

def main():
    key = {k["mondo_id"]: k for k in json.load(open(BUILD / "llm_key.json"))}
    pred = {}
    for f in sorted(glob.glob(str(BUILD / "batches/out_*.json"))):
        for r in json.load(open(f)): pred[r["mondo_id"]] = r
    both = [m for m in key if m in pred]
    print(f"rated {len(pred)} / {len(key)} in the blind set; scoring {len(both)}\n")
    if len(both) < len(key):
        print(f"  WARNING: {len(key)-len(both)} unrated, excluded from scoring\n")

    rows = []
    for axis in ("work", "care"):
        base = sum(key[m][axis] for m in both) / len(both)
        conf = [(pred[m][axis + "_conf"], key[m][axis]) for m in both]
        hard = [pred[m][axis + "_yes"] for m in both]; truth = [key[m][axis] for m in both]
        ph = [(key[m]["pheno_" + axis], key[m][axis]) for m in both]
        tp = sum(1 for h, t in zip(hard, truth) if h and t); fp = sum(1 for h, t in zip(hard, truth) if h and not t)
        fn = sum(1 for h, t in zip(hard, truth) if not h and t); tn = sum(1 for h, t in zip(hard, truth) if not h and not t)
        print(f"=== {axis.upper()}   base rate {base:.0%}  ({sum(truth)}/{len(truth)})")
        print(f"  {'':<22}{'AUC':>8}{'top-25':>9}{'top-50':>9}")
        print(f"  {'phenotype method':<22}{auc(ph):8.3f}{prec_at(ph,25):9.2f}{prec_at(ph,50):9.2f}   <- floor to beat")
        print(f"  {'LLM (confidence)':<22}{auc(conf):8.3f}{prec_at(conf,25):9.2f}{prec_at(conf,50):9.2f}")
        comb = [(0.5*(key[m]["pheno_"+axis]/max(1e-9,max(key[x]["pheno_"+axis] for x in both)))
                 + 0.5*(pred[m][axis+"_conf"]/100), key[m][axis]) for m in both]
        print(f"  {'both combined':<22}{auc(comb):8.3f}{prec_at(comb,25):9.2f}{prec_at(comb,50):9.2f}")
        print(f"  LLM yes/no vs experts: sens {tp/(tp+fn) if tp+fn else 0:.2f}  spec {tn/(tn+fp) if tn+fp else 0:.2f}"
              f"  precision {tp/(tp+fp) if tp+fp else 0:.2f}  kappa {kappa(hard,truth):.3f}")
        for nm, sub in (("neuro", [m for m in both if key[m]["neuro"]]),
                        ("NON-NEURO", [m for m in both if not key[m]["neuro"]]),
                        ("tier A labels", [m for m in both if key[m]["tier"] == "A"])):
            t2 = [key[m][axis] for m in sub]
            if len(sub) < 12 or not 0 < sum(t2) < len(sub): continue
            c2 = [(pred[m][axis + "_conf"], key[m][axis]) for m in sub]
            p2 = [(key[m]["pheno_" + axis], key[m][axis]) for m in sub]
            star = "  <-- the failure case" if nm == "NON-NEURO" else ""
            print(f"      {nm:<16} n={len(sub):3d}  base {sum(t2)/len(sub):.0%}   phenotype AUC {auc(p2):.3f}   LLM AUC {auc(c2):.3f}{star}")
        print()
        rows.append((axis, auc(ph), auc(conf), auc(comb)))
    print("VERDICT")
    for axis, a_ph, a_llm, a_c in rows:
        best = max((a_ph, "phenotype"), (a_llm, "LLM"), (a_c, "combined"))
        print(f"  {axis:<5} best = {best[1]} (AUC {best[0]:.3f});  LLM {'beats' if a_llm > a_ph else 'does not beat'} the phenotype floor")

if __name__ == "__main__":
    main()
