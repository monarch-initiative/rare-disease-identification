"""Search PubMed for functional-outcome papers for each worklist disease.

Writes tmp/frailty_triage/<MONDO>.md with title + abstract for the top hits, so
the curator can scan for a quotable employment / ADL / caregiver-burden figure
without fetching every candidate into the reference cache.

Nothing here is evidence. A quote only counts once `just fetch-reference` has
cached it and `just verify-frailty-quotes` has checked it.
"""
import argparse, csv, json, re, time, urllib.parse, urllib.request, pathlib
from common import TMP, load_source

E = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
OUT = TMP / "frailty_triage"

FUNC = ('("activities of daily living" OR employment OR "return to work" OR '
        '"work capacity" OR occupational OR "functional outcome" OR "caregiver burden" '
        'OR caregiver OR disability OR "quality of life" OR "natural history" OR '
        'wheelchair OR "tube feeding" OR institutionalisation OR "life expectancy" '
        'OR ambulation OR "developmental outcome" OR survival)')


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            if attempt == 3:
                return ""
            time.sleep(2 * (attempt + 1))
    return ""


def search(term, retmax=8):
    q = urllib.parse.urlencode({"db": "pubmed", "term": term, "retmax": retmax,
                                "retmode": "json", "sort": "relevance"})
    try:
        return json.loads(get(f"{E}/esearch.fcgi?{q}"))["esearchresult"]["idlist"]
    except Exception:
        return []


def fetch(pmids):
    if not pmids:
        return ""
    q = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids),
                                "retmode": "xml", "rettype": "abstract"})
    return get(f"{E}/efetch.fcgi?{q}")


def parse(xml):
    out = []
    for m in re.finditer(r"<PubmedArticle>(.*?)</PubmedArticle>", xml, re.S):
        a = m.group(1)
        pmid = re.search(r"<PMID[^>]*>(\d+)</PMID>", a)
        title = re.search(r"<ArticleTitle[^>]*>(.*?)</ArticleTitle>", a, re.S)
        year = re.search(r"<Year>(\d{4})</Year>", a)
        abst = " ".join(re.findall(r"<AbstractText[^>]*>(.*?)</AbstractText>", a, re.S))
        clean = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()
        out.append({"pmid": pmid.group(1) if pmid else "",
                    "title": clean(title.group(1) if title else ""),
                    "year": year.group(1) if year else "",
                    "abstract": clean(abst)})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--worklist", default=str(TMP / "frailty_worklist.tsv"))
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=10**6)
    ap.add_argument("--retmax", type=int, default=8)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    syn = {d["mondo_id"]: (d.get("mondo_synonyms") or [])
           for d in load_source()["diseases"]}
    with open(args.worklist, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))[args.start:args.end]

    for i, r in enumerate(rows, args.start + 1):
        dest = OUT / f"{r['mondo_id'].replace(':', '_')}.md"
        if dest.exists():
            print(f"[{i}] cached {r['label'][:60]}")
            continue
        label = r["label"]
        # strip trailing enumerators that hurt recall: "..., 19" / "type 8"
        base = re.sub(r",?\s*(type\s*)?\d+[a-z]?$", "", label, flags=re.I).strip()
        # exact label, then de-enumerated label, then each synonym, then a
        # loose AND-of-words query for hyphen-heavy names that defeat phrase search
        loose = " AND ".join(w for w in re.split(r"[^A-Za-z0-9]+", base)
                             if len(w) > 3)[:300]
        terms = [f'"{label}" AND {FUNC}', f'"{base}" AND {FUNC}']
        terms += [f'"{s}" AND {FUNC}' for s in syn.get(r["mondo_id"], [])[:4]]
        if loose:
            terms.append(f'({loose}) AND {FUNC}')
        arts = []
        seen = set()
        for term in terms:
            for a in parse(fetch(search(term, args.retmax))):
                if a["pmid"] and a["pmid"] not in seen and a["abstract"]:
                    seen.add(a["pmid"])
                    arts.append(a)
            time.sleep(0.4)
            if len(arts) >= args.retmax:
                break
        body = [f"# {label}  ({r['mondo_id']})", "",
                f"work_score={r['work_score']} care_score={r['care_score']} "
                f"orpha={r['orpha_cached'] or '-'} icd={r['icd10cm'] or '-'}", ""]
        if not arts:
            body.append("_No abstracts retrieved._")
        for a in arts:
            body += [f"## PMID:{a['pmid']} ({a['year']})", f"**{a['title']}**", "",
                     a["abstract"], ""]
        dest.write_text("\n".join(body), encoding="utf-8")
        print(f"[{i}] {len(arts):>2} abstracts  {label[:60]}")


if __name__ == "__main__":
    main()
