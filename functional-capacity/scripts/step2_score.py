"""Step 2: propagate term scores down HPO, aggregate per disease, rank, evaluate.

Narrative:
  1. A clinician (here: a prototype hand-scoring) rates each HPO term 0-3 on two axes -
     does this finding imply inability to work, and does it imply need for daily care.
  2. Scores propagate DOWN the HPO hierarchy: an unscored term inherits from its most
     specific scored ancestor. So ~370 scored terms cover thousands of annotations.
  3. Each disease's phenotype profile is aggregated into one number per axis,
     weighting each term by how often it occurs in that disease (HPO frequency).
  4. Diseases are RANKED. We take the top N.
  5. We check the ranking against Orphanet's expert functional-consequence annotations,
     which the scoring never saw.
"""
import csv, collections, math, pathlib, sqlite3, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD, DATA = ROOT / "build", ROOT / "data"
HP_DB = pathlib.Path.home() / ".data/oaklib/hp.db"

# ------------------------------------------------ ontology: ancestors + depth proxy
con = sqlite3.connect(HP_DB)
anc = collections.defaultdict(set)
ndesc = collections.Counter()
for s, o in con.execute("select subject,object from entailed_edge where predicate='rdfs:subClassOf'"
                        " and subject like 'HP:%' and object like 'HP:%'"):
    anc[s].add(o); ndesc[o] += 1
label = dict(con.execute("select subject,value from rdfs_label_statement where subject like 'HP:%'"))

# ------------------------------------------------------------------ term scores
scored = {}
for row in csv.DictReader((l for l in open(DATA / "term_scores.tsv") if not l.startswith("#")), delimiter="\t"):
    if row["hp_id"] not in label:
        print(f"  WARN unknown term dropped: {row['hp_id']}", file=sys.stderr); continue
    scored[row["hp_id"]] = (int(row["work"]), int(row["care"]))
print(f"terms scored by hand : {len(scored)}")

_cache = {}
def score_of(t):
    """Explicit score, else inherit from the most specific scored ancestor, else 0."""
    if t in _cache: return _cache[t]
    if t in scored:
        _cache[t] = scored[t] + ("explicit",); return _cache[t]
    cands = [a for a in anc.get(t, ()) if a in scored]
    if cands:
        best = min(cands, key=lambda a: ndesc[a])          # most specific = fewest descendants
        _cache[t] = scored[best] + ("inherited:" + best,)
    else:
        _cache[t] = (0, 0, "unscored")
    return _cache[t]

# --------------------------------------------------------------- aggregators
def profile(phen):
    """phen: {hp_id: frequency}. -> list of (w,c,freq) for terms with any score."""
    out = []
    for t, f in phen.items():
        w, c, _ = score_of(t)
        if w or c: out.append((w, c, f))
    return out

AGG = {}
AGG["max"]    = lambda p, i: max((x[i] * x[2] for x in p), default=0)
AGG["wsum"]   = lambda p, i: sum(x[i] * x[2] for x in p)
AGG["top3"]   = lambda p, i: sum(sorted((x[i] * x[2] for x in p), reverse=True)[:3])
AGG["top5"]   = lambda p, i: sum(sorted((x[i] * x[2] for x in p), reverse=True)[:5])
AGG["wsum_norm"] = lambda p, i: sum(x[i] * x[2] for x in p) / math.sqrt(max(len(p), 1))
AGG["count2"] = lambda p, i: sum(1 for x in p if x[i] >= 2 and x[2] >= 0.30)
AGG["mean_top5_x_n"] = lambda p, i: (sum(sorted((x[i]*x[2] for x in p), reverse=True)[:5])/5.0) * math.log1p(
                                     sum(1 for x in p if x[i] >= 2 and x[2] >= 0.30))

def parse_phen(s):
    d = {}
    for kv in s.split("|"):
        if not kv: continue
        t, v = kv.rsplit(":", 1); d[t] = float(v)
    return d

# ---------------------------------------------------------------- evaluation
def auc(pairs):
    """pairs: [(score, label)] -> rank AUC."""
    pos = [s for s, y in pairs if y]; neg = [s for s, y in pairs if not y]
    if not pos or not neg: return float("nan")
    allv = sorted(s for s, _ in pairs)
    rank = {v: i for i, v in enumerate(sorted(set(allv)))}
    wins = sum(1 for p in pos for n in neg if p > n) + 0.5 * sum(1 for p in pos for n in neg if p == n)
    return wins / (len(pos) * len(neg))

def prec_at(pairs, n):
    top = sorted(pairs, key=lambda x: -x[0])[:n]
    return sum(y for _, y in top) / len(top)

val = list(csv.DictReader(open(BUILD / "validation.tsv"), delimiter="\t"))
print(f"validation diseases  : {len(val)}")
for axis, i, key in (("WORK (cannot sustain employment)", 0, "work"),
                     ("CARE (needs daily assistance)", 1, "care")):
    ys = [int(v[key]) for v in val]
    base = sum(ys) / len(ys)
    print(f"\n=== {axis}   base rate {base:.1%}  ({sum(ys)}/{len(ys)})")
    print(f"{'aggregator':>16} {'AUC':>6} {'P@25':>6} {'P@50':>6} {'P@100':>6} {'lift@50':>8}")
    for name, fn in AGG.items():
        pairs = [(fn(profile(parse_phen(v["phenotypes"])), i), int(v[key])) for v in val]
        print(f"{name:>16} {auc(pairs):6.3f} {prec_at(pairs,25):6.2f} {prec_at(pairs,50):6.2f}"
              f" {prec_at(pairs,100):6.2f} {prec_at(pairs,50)/base:8.1f}x")
    # random baseline for reference
    print(f"{'(random)':>16} {0.5:6.3f} {base:6.2f} {base:6.2f} {base:6.2f} {1.0:8.1f}x")
