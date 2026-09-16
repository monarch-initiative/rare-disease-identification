"""Fetch references into references_cache via linkml-reference-validator.

Thin wrapper so the curation workflow has one command and one cache, and so a
cache file is never hand-written -- the rule the evidence discipline turns on.
"""
import subprocess, sys
from common import ROOT, CACHE

def main(refs):
    if not refs:
        sys.exit("usage: fetch_reference.py PMID:12345678 [PMID:... ...]")
    cmd = ["uv", "run", "linkml-reference-validator", "lookup", *refs,
           "--config", str(ROOT / "config/frailty_refval.yaml"),
           "--cache-dir", str(CACHE)]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    for ref in refs:
        p = CACHE / (ref.replace(":", "_") + ".md")
        print(f"{'OK  ' if p.exists() else 'MISS'} {ref} -> {p.name}")
    if r.returncode != 0:
        sys.stderr.write("\n".join(l for l in r.stderr.splitlines()
                                   if "fontTools" not in l)[-2000:])
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
