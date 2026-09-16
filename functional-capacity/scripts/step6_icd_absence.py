"""Step 6: which high-scoring diseases have no ICD-10-CM representation at all?

A disease counts as FINDABLE IN ICD-10-CM if either
  (a) Mondo carries an ICD10CM xref for it, or
  (b) some ICD-10-CM term label matches one of its Mondo names (exact after
      normalisation, or all distinctive tokens present).
Everything else is NOT IN ICD-10-CM: there is no code a clinic could put on a claim.
"""
import collections, csv, pathlib, re, sqlite3, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]; BUILD = ROOT / "build"
MONDO = pathlib.Path("/Users/matentzn/ws/ont/mondo/mondo.obo")

STOP = set("disease diseases disorder disorders syndrome syndromes deficiency type form of the and with due to a an".split())
def norm(s):
    s = s.lower()
    s = re.sub(r"'s\b", "", s)                 # Rett's -> Rett
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()
def toks(s):
    return {t for t in norm(s).split() if t not in STOP and len(t) > 2}

def load_mondo():
    names = collections.defaultdict(set); icd = collections.defaultdict(set)
    cur = None; obs = False
    for line in open(MONDO, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("id: MONDO:"): cur = line[4:]; obs = False
        elif cur is None: continue
        elif line.startswith("is_obsolete: true"): obs = True
        elif obs: continue
        elif line.startswith("name: "): names[cur].add(line[6:])
        elif line.startswith('synonym: "'): names[cur].add(line.split('"')[1])
        elif line.startswith("xref: ICD10CM:"): icd[cur].add(line.split("ICD10CM:")[1].split()[0])
    return names, icd

def load_icd():
    con = sqlite3.connect(pathlib.Path.home() / ".data/oaklib/icd10cm.db")
    exact = {}; tokidx = collections.defaultdict(set)
    for s, v in con.execute("select subject,value from statements where predicate='rdfs:label'"):
        if not s.startswith("ICD10CM:") or "-" in s.split(":")[1]: continue
        v = re.sub(r"\s*\([A-Z]\d{2}.*?\)\s*$", "", v)
        n = norm(v); exact.setdefault(n, s)
        for t in toks(v): tokidx[t].add((s, frozenset(toks(v))))
    return exact, tokidx

def main():
    names, m_icd = load_mondo()
    exact, tokidx = load_icd()
    rows = list(csv.DictReader(open(BUILD / "assertions.tsv"), delimiter="\t"))
    out = []
    for r in rows:
        mid = r["mondo_id"]
        if m_icd.get(mid):
            r["in_icd10cm"] = "mapped"; r["icd_match"] = ",".join(sorted(m_icd[mid])); out.append(r); continue
        hit = None
        for nm in names.get(mid, ()):
            n = norm(nm)
            if n in exact: hit = f"{exact[n]} (label match)"; break
            tk = toks(nm)
            if len(tk) >= 1:
                cands = set.intersection(*[tokidx.get(t, set()) for t in tk]) if all(t in tokidx for t in tk) else set()
                if cands: hit = f"{sorted(cands)[0][0]} (token match)"; break
        r["in_icd10cm"] = "lexical" if hit else "ABSENT"
        r["icd_match"] = hit or ""
        out.append(r)
    with open(BUILD / "icd_absence.tsv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]), delimiter="\t"); w.writeheader(); w.writerows(out)
    c = collections.Counter(r["in_icd10cm"] for r in out)
    print(f"{len(out)} Mondo classes assessed")
    print(f"  mapped to an ICD-10-CM code by Mondo : {c['mapped']}")
    print(f"  findable in ICD-10-CM by name        : {c['lexical']}")
    print(f"  NOT IN ICD-10-CM AT ALL              : {c['ABSENT']}  ({c['ABSENT']/len(out):.0%})")
    for axis in ("care", "work"):
        print(f"\n--- {axis.upper()}: of diseases we flag (expert-positive or top-500 candidate)")
        fl = [r for r in out if r[axis + "_status"] in ("EXPERT_POSITIVE", "PREDICTED_CANDIDATE")]
        ab = [r for r in fl if r["in_icd10cm"] == "ABSENT"]
        print(f"    flagged {len(fl)}   of which NOT IN ICD-10-CM: {len(ab)} ({len(ab)/len(fl):.0%})")
        for r in sorted(ab, key=lambda r: -float(r[axis + "_score"]))[:12]:
            print(f"      {r['label'][:60]:<60} {r['mondo_id']}")
    print("\nsanity check — these SHOULD be found in ICD-10-CM:")
    want = ["Rett syndrome", "Dravet syndrome", "Angelman syndrome", "Lesch-Nyhan syndrome",
            "cystic fibrosis", "Prader-Willi syndrome", "Huntington disease", "Down syndrome",
            "Duchenne muscular dystrophy", "Marfan syndrome", "tuberous sclerosis",
            "Lennox-Gastaut syndrome", "phenylketonuria", "achondroplasia", "Turner syndrome",
            "Wilson disease", "sickle cell disease", "Gaucher disease", "Fabry disease",
            "spinal muscular atrophy", "Friedreich ataxia", "neurofibromatosis type 1"]
    byl = {r["label"]: r for r in out}
    for w in want:
        r = byl.get(w)
        print(f"   {w:<26} {r['in_icd10cm'] if r else 'not in corpus':<10} {r['icd_match'][:40] if r else ''}")

if __name__ == "__main__":
    main()
