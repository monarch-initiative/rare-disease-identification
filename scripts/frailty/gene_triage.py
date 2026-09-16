"""Gene-targeted PubMed pass, replacing the loose label query.

The label-based fallback in pubmed_triage.py pulls papers about other diseases
that happen to share an acronym (DEE-19 is GABRA1, but "DEE" retrieves KCNQ2
series). Searching on the causative gene plus a functional-outcome clause keeps
the hits on-disease.
"""
import csv, sys, time, pathlib
from pubmed_triage import search, fetch, parse, FUNC
from common import TMP

OUT = TMP / "frailty_gene_triage"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pairs = [l.split("\t") for l in
             pathlib.Path(TMP / "gene_map.tsv").read_text().strip().splitlines()]
    for mid, gene in pairs:
        dest = OUT / f"{mid.replace(':', '_')}.md"
        if dest.exists():
            print(f"cached {mid} {gene}")
            continue
        arts, seen = [], set()
        for term in (f"{gene} AND {FUNC}",
                     f"{gene} AND (cohort OR series OR \"natural history\" OR outcome)"):
            for a in parse(fetch(search(term, 8))):
                if a["pmid"] not in seen and a["abstract"]:
                    seen.add(a["pmid"])
                    arts.append(a)
            time.sleep(0.4)
        body = [f"# {mid} — {gene}", ""]
        for a in arts:
            body += [f"## PMID:{a['pmid']} ({a['year']})", f"**{a['title']}**", "",
                     a["abstract"], ""]
        dest.write_text("\n".join(body), encoding="utf-8")
        print(f"{len(arts):>2} abstracts  {mid} {gene}")


if __name__ == "__main__":
    main()
