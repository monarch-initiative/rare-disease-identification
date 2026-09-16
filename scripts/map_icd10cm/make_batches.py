#!/usr/bin/env python3
"""Split the stage-1 review queue into batches for stage-2 agentic adjudication."""

from __future__ import annotations

import json
import math
from pathlib import Path

import click


@click.command()
@click.option("--queue", type=click.Path(exists=True, path_type=Path),
              default=Path("tmp/icd10cm/review_queue.json"))
@click.option("--out-dir", type=click.Path(path_type=Path), default=Path("tmp/icd10cm/batches"))
@click.option("--batch-size", default=130, show_default=True)
def main(queue, out_dir, batch_size):
    """Write batch_NNN.json files containing only terms that have candidates."""
    review = json.loads(Path(queue).read_text())
    items = [{"mondo_id": k, **v} for k, v in sorted(review.items()) if v.get("candidates")]
    no_cand = [k for k, v in sorted(review.items()) if not v.get("candidates")]

    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob("batch_*.json"):
        f.unlink()

    n = math.ceil(len(items) / batch_size)
    for i in range(n):
        chunk = items[i * batch_size:(i + 1) * batch_size]
        payload = [
            {"mondo_id": it["mondo_id"], "mondo_label": it["label"],
             "mondo_synonyms": it["synonyms"],
             "candidates": [{"code": c["code"], "icd_label": c["icd_label"]}
                            for c in it["candidates"]]}
            for it in chunk
        ]
        (out_dir / f"batch_{i:03d}.json").write_text(json.dumps(payload, indent=1))

    (out_dir.parent / "no_candidates.json").write_text(json.dumps(no_cand, indent=1))
    click.echo(f"{len(items)} terms to adjudicate in {n} batches of <= {batch_size}")
    click.echo(f"{len(no_cand)} terms have no candidate at all -> sssom:NoTermFound")


if __name__ == "__main__":
    main()
