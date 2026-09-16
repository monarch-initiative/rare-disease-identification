"""Reference-validation machinery vendored from `dismech-1`.

`linkml-reference-validator` is the authority on whether a quote matches its
source, but out of the box it has three gaps this project hits directly:

* it crashes the whole run on a transient NCBI read error,
* its "Total checks: N" counts *issues found*, not checks performed, so a clean
  run is indistinguishable from one that verified nothing,
* it strips square-bracketed spans from the quote but not from the cached text,
  so a verbatim quote spanning an abbreviation definition fails as if the
  curator had paraphrased it.

dismech solved all three. The modules here are copied from
`~/ws/projects/dismech-1/src/dismech/` with the package path rewritten; the
comments explaining *why* each patch exists are theirs and are kept verbatim.
Re-sync rather than re-invent when that repo moves on.
"""
