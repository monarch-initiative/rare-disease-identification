"""Step 9: precompute POLICY_LIST evidence, one row per (disease, policy source).

Why this is a build artefact and not something the curation agent works out:
the matching is fiddly and fails silently. State lists enumerate 5-6 character
ICD children (G40811 Lennox-Gastaut with status epilepticus); Mondo maps the
4-character concept (G4081). Exact matching misses it. Parent-only matching
misses it. You need both directions, plus chapter ranges. Getting this wrong
produces a confident, wrong "not listed by any state" - which is exactly the
kind of error a policy artefact cannot afford.

So: compute it once, here, and let the agent do a lookup.
"""
import collections, csv, json, pathlib, re, unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD, SL = ROOT / "build", ROOT / "data/state_lists"
MONDO = pathlib.Path("/Users/matentzn/ws/ont/mondo/mondo.obo")

NEB = set(open(SL / "nebraska_icd10cm.txt").read().split())
NEBX = set(open(SL / "nebraska_chapter_ranges.txt").read().split())
MN = set(open(SL / "minnesota_icd10cm.txt").read().split())
MT = json.load(open(SL / "montana_conditions.json"))

STOP = set("disease diseases disorder disorders syndrome syndromes deficiency type form of the and with due to a an other".split())
def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.lower().replace("'s", "")
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()
def toks(s): return {t for t in norm(s).split() if t not in STOP and len(t) > 3}

def reaches(code, S, X=frozenset()):
    """state list S reaches Mondo's code: exact, chapter range, child, or parent."""
    c = code.replace(".", "").upper()
    if c in S: return "exact"
    if any(c.startswith(p) for p in X): return "chapter_range"
    if any(s.startswith(c) for s in S): return "state_lists_children"
    for k in range(len(c) - 1, 2, -1):
        if c[:k] in S: return "state_lists_parent"
    return None

def load_mondo():
    names = collections.defaultdict(set); icd = collections.defaultdict(set); lbl = {}
    cur = None; obs = False
    for line in open(MONDO, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("id: MONDO:"): cur = line[4:]; obs = False
        elif cur is None: continue
        elif line.startswith("is_obsolete: true"): obs = True
        elif obs: continue
        elif line.startswith("name: "): lbl[cur] = line[6:]; names[cur].add(line[6:])
        elif line.startswith('synonym: "'): names[cur].add(line.split('"')[1])
        elif line.startswith("xref: ICD10CM:"): icd[cur].add(line.split("ICD10CM:")[1].split()[0])
    return names, icd, lbl

def main():
    names, icd, lbl = load_mondo()
    mt_index = []
    for n, cat in MT:
        if "google analytics" in n.lower(): continue
        mt_index.append((n, cat, norm(n), toks(n)))

    rows = []
    for mid, codes in icd.items():
        for state, S, X in (("Nebraska", NEB, NEBX), ("Minnesota", MN, frozenset())):
            for c in sorted(codes):
                how = reaches(c, S, X)
                if how:
                    rows.append(dict(mondo_id=mid, mondo_label=lbl.get(mid, ""), source=state,
                                     match_type=how, matched_value="ICD10CM:" + c,
                                     source_description="", statutory_category=""))
                    break
    # Montana: name-based
    lex = collections.defaultdict(set)
    for mid, ns in names.items():
        for n in ns: lex[norm(n)].add(mid)
    for n, cat, nn, tk in mt_index:
        hit = set(lex.get(nn, ()))
        if not hit and len(tk) >= 1:
            cand = [m for m, nss in names.items() if any(toks(x) == tk for x in nss)]
            hit = set(cand)
        for mid in sorted(hit)[:3]:
            rows.append(dict(mondo_id=mid, mondo_label=lbl.get(mid, ""), source="Montana",
                             match_type="name_match", matched_value=n,
                             source_description=n, statutory_category=cat))

    rows.sort(key=lambda r: (r["mondo_id"], r["source"]))
    with open(BUILD / "policy_evidence.tsv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t"); w.writeheader(); w.writerows(rows)

    per = collections.Counter(r["source"] for r in rows)
    mids = collections.defaultdict(set)
    for r in rows: mids[r["source"]].add(r["mondo_id"])
    print(f"policy evidence rows: {len(rows)}   distinct diseases: {len({r['mondo_id'] for r in rows})}")
    for s in ("Nebraska", "Minnesota", "Montana"):
        print(f"   {s:<10} {per[s]:5d} rows   {len(mids[s]):5d} Mondo classes")
    print(f"   match types: {dict(collections.Counter(r['match_type'] for r in rows))}")
    print("\n   Montana name matches (the lane that reaches diseases with no ICD code):")
    for r in [r for r in rows if r["source"] == "Montana"][:10]:
        print(f"      {r['mondo_label'][:44]:<44} <- {r['matched_value'][:34]}")
    print(f"\n-> build/policy_evidence.tsv")

if __name__ == "__main__":
    main()
