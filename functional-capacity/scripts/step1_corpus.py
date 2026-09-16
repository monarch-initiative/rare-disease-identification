"""Step 1: build the corpus.

Scope   : the 3,079 curated diseases in prioritised-rare-disease-list.yml
Answer  : Orphanet functional-consequences labels, where they exist
Features: HPO annotations (phenotype.hpoa), frequency-qualified

Writes build/corpus.tsv (one row per disease) and build/terms_to_score.tsv.
"""
import collections, csv, re, sys, xml.etree.ElementTree as ET, pathlib, sqlite3, pickle

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
MONDO_OBO = pathlib.Path("/Users/matentzn/ws/ont/mondo/mondo.obo")
HP_DB = pathlib.Path.home() / ".data/oaklib/hp.db"
LIST = ROOT.parent / "prioritised-rare-disease-list.yml"

# ---------------------------------------------------------------- Mondo xrefs
def mondo_index():
    """MONDO id -> {'label':..,'xrefs':set(OMIM:/ORPHA:)}, plus parent edges."""
    idx, parents = {}, collections.defaultdict(set)
    cur = None; obs = False
    for line in open(MONDO_OBO, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("id: MONDO:"):
            cur = line[4:]; obs = False; idx[cur] = {"label": "", "xrefs": set()}
        elif cur is None:
            continue
        elif line.startswith("is_obsolete: true"):
            obs = True; idx.pop(cur, None)
        elif obs:
            continue
        elif line.startswith("name: "):
            idx[cur]["label"] = line[6:]
        elif line.startswith("is_a: MONDO:"):
            parents[cur].add(line.split()[1])
        elif line.startswith("xref: "):
            x = line[6:].split()[0]
            if x.startswith("Orphanet:"):
                idx[cur]["xrefs"].add("ORPHA:" + x.split(":")[1])
            elif x.startswith("OMIM:") and not x.startswith("OMIMPS"):
                idx[cur]["xrefs"].add(x)
    return idx, parents

# ---------------------------------------------- Orphanet functional labels
WORK = {"Engaging in paid work in a standard environment", "Performing professional tasks"}
CARE = {"Washing oneself", "Dressing/undressing", "Eating", "Drinking", "Transferring oneself",
        "Regulating urination", "Regulating defecation",
        "Caring for body parts (skin, teeth, nails, hair, genitals)",
        "Managing one's health (diet, medications, prevention, needs, assistance, monitoring)",
        "Moving around within the home"}
FREQ_OK = {"Very frequent", "Frequent"}
SEV_HI = {"Severe", "Complete"}

def orphanet_labels():
    """ORPHA:code -> dict(work=0/1, care=0/1, scope=..., tier=A/B, source=...)"""
    out = {}
    for d in ET.parse(BUILD / "fc.xml").getroot().iter("DisorderDisabilityRelevance"):
        code = "ORPHA:" + d.find("Disorder").findtext("OrphaCode")
        scope = d.find("DisabilityCategory").findtext("Name")
        status = d.find("StatusDisability").findtext("Name")
        src = (d.findtext("SourceOfValidation") or "").strip()
        w = c = 0
        for a in d.iter("DisabilityDisorderAssociation"):
            if a.findtext("Type") != "Disability":
                continue
            item = a.find("Disability").findtext("Name")
            strict = (a.find("FrequenceDisability").findtext("Name") in FREQ_OK
                      and a.find("SeverityDisability").findtext("Name") in SEV_HI
                      and a.find("TemporalityDisability").findtext("Name") == "Permanent limitation")
            if strict and item in WORK: w += 1
            if strict and item in CARE: c += 1
        out[code] = dict(work=1 if w else 0, care=1 if c >= 3 else 0, scope=scope,
                         tier="A" if (status == "Validated" and "[Expert]" in src) else "B",
                         source=src[:120], annotated=(d.findtext("AnnotationDate") or "")[:10])
    return out

# ------------------------------------------------------------------- HPOA
FREQ_TERM = {"HP:0040280": 1.0, "HP:0040281": 0.90, "HP:0040282": 0.55,
             "HP:0040283": 0.17, "HP:0040284": 0.02, "HP:0040285": 0.0}

def parse_freq(f):
    f = (f or "").strip()
    if not f: return None                       # unstated
    if f.startswith("HP:"): return FREQ_TERM.get(f)
    if "/" in f:
        try:
            a, b = f.split("/"); b = int(b)
            return int(a) / b if b else None
        except ValueError: return None
    if f.endswith("%"):
        try: return float(f[:-1]) / 100
        except ValueError: return None
    return None

def hpoa():
    ann = collections.defaultdict(dict)
    for line in open(BUILD / "hpoa.tsv", encoding="utf-8"):
        if line.startswith("#") or line.startswith("database_id"): continue
        p = line.rstrip("\n").split("\t")
        if len(p) < 11 or p[10] != "P": continue
        f = parse_freq(p[7])
        prev = ann[p[0]].get(p[3])
        ann[p[0]][p[3]] = f if prev is None else max(prev, f if f is not None else 0)
    return ann

# ------------------------------------------------------------------ main
def main():
    idx, parents = mondo_index()
    labels = orphanet_labels()
    ann = hpoa()

    listed = []
    for line in open(LIST, encoding="utf-8"):
        m = re.match(r"-?\s*mondo_id:\s*(MONDO:\d+)", line.strip())
        if m: listed.append(m.group(1))
    listed = list(dict.fromkeys(listed))

    rows, termcount = [], collections.Counter()
    for mid in listed:
        info = idx.get(mid)
        if not info: continue
        xr = info["xrefs"]
        phen = {}
        for x in xr:
            for t, f in ann.get(x, {}).items():
                phen[t] = max(phen.get(t, 0) or 0, f if f is not None else 0.5)
        lab = next((labels[x] for x in xr if x in labels), None)
        for t in phen: termcount[t] += 1
        rows.append(dict(mondo_id=mid, label=info["label"], n_phenotypes=len(phen),
                         xrefs="|".join(sorted(xr)) or "",
                         gold_scope=lab["scope"] if lab else "",
                         gold_work=lab["work"] if lab else "",
                         gold_care=lab["care"] if lab else "",
                         gold_tier=lab["tier"] if lab else "",
                         phenotypes="|".join(f"{t}:{v:.2f}" for t, v in sorted(phen.items()))))

    with open(BUILD / "corpus.tsv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader(); w.writerows(rows)

    # validation cohort = every FC-labelled disease in scope, not just those on the list
    val = []
    for code, lab in labels.items():
        if lab["scope"] != "Activity limitation/participation restriction": continue
        mids = [m for m, v in idx.items() if code in v["xrefs"]]
        if not mids: continue
        mid = mids[0]
        phen = {}
        for x in idx[mid]["xrefs"]:
            for t, f in ann.get(x, {}).items():
                phen[t] = max(phen.get(t, 0) or 0, f if f is not None else 0.5)
        if not phen: continue
        for t in phen: termcount[t] += 1
        val.append(dict(mondo_id=mid, orpha=code, label=idx[mid]["label"], work=lab["work"],
                        care=lab["care"], tier=lab["tier"], n_phenotypes=len(phen),
                        phenotypes="|".join(f"{t}:{v:.2f}" for t, v in sorted(phen.items()))))
    with open(BUILD / "validation.tsv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(val[0]), delimiter="\t")
        w.writeheader(); w.writerows(val)

    con = sqlite3.connect(HP_DB)
    lbl = dict(con.execute("select subject,value from rdfs_label_statement where subject like 'HP:%'"))
    with open(BUILD / "terms_to_score.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t"); w.writerow(["hp_id", "label", "n_diseases"])
        for t, n in termcount.most_common():
            w.writerow([t, lbl.get(t, "?"), n])

    print(f"prioritised list MONDO ids            : {len(listed)}")
    print(f"  ...resolved in current Mondo        : {len(rows)}")
    print(f"  ...with >=1 HPO phenotype           : {sum(1 for r in rows if r['n_phenotypes'])}")
    print(f"  ...with Orphanet functional label   : {sum(1 for r in rows if r['gold_scope'])}")
    print(f"validation cohort (in-scope, w/ HPO)  : {len(val)}"
          f"  work+ {sum(v['work'] for v in val)}  care+ {sum(v['care'] for v in val)}"
          f"  tierA {sum(1 for v in val if v['tier']=='A')}")
    print(f"distinct HP terms to score            : {len(termcount)}")
    for k in (200, 400, 600, 900):
        cov = sum(c for _, c in termcount.most_common(k)) / sum(termcount.values())
        print(f"  top {k:4d} terms cover {cov:.0%} of annotations")

if __name__ == "__main__":
    main()
