# Mapping curation rules — chemical pack

Domain pack for chemical structures, substances and roles: ChEBI, PubChem, ChEMBL, DrugBank,
UNII/FDA SRS, RxNorm, CAS, InChI-based resources, DRON.

Load alongside the core registry (`curation-rules.md`), which supplies the `EV`, `SC`, `PR`,
`ST` and `RJ` families. This pack supplies `CX`.

**Namespace:** `maprule:` → `https://w3id.org/mapping-rules/`

Chemical resources disagree about **what counts as the same substance**. The disagreements
are sharper and more mechanical than in disease terminologies — two resources can differ on
whether a salt is the same thing as its free base while agreeing on everything else — and
they are usually invisible in the label. `Diclofenac` and `Diclofenac sodium` look like a
naming variant and are not. Cite the `CX` rule alongside the `EV` rule that produced the
match, so the conflation is on the record.

---

## Family CX — Conceptual model conflation (chemical)

| ID | Title | Meaning |
|---|---|---|
| `CX-001` | salt or ester vs free acid/base | Subject and object differ only by a counter-ion or ester group (`diclofenac sodium` vs `diclofenac`). The *active moiety* is shared; the substances are not identical. Conflate only when the use case is about the moiety — typical for drug-indication data, wrong for formulation or dosing data. Declare it; do not assert `exactMatch` silently. |
| `CX-002` | hydrate, solvate or anhydrous form | Differ only by associated solvent (`morphine sulfate pentahydrate` vs `morphine sulfate`). Same treatment as CX-001, and the same warning for anything dose-related. |
| `CX-003` | racemate vs enantiomer | One side specifies stereochemistry, the other does not, or specifies the opposite (`levocetirizine` vs `cetirizine`; `(S)-ibuprofen` vs `ibuprofen`). **Rejection ground by default** — enantiomers can differ in activity and in toxicity. Conflate only with an explicit, stated reason. |
| `CX-004` | unspecified stereochemistry | Neither side pins the stereocentre and the resources disagree about whether the parent term is the racemate or the stereochemistry-agnostic class. Record the ambiguity; prefer `skos:closeMatch`. |
| `CX-005` | tautomers | The two forms interconvert (keto/enol, amide/imidic acid). Usually the same substance in practice; conflate, but say so, because structure-derived identifiers (InChI, SMILES) may disagree. |
| `CX-006` | conjugate acid/base pair | Neutral species vs its ion (`acetic acid` vs `acetate`). ChEBI models these as distinct entities linked by `is_conjugate_base_of`. **Not an exactMatch** — use the relation, or `closeMatch` with CX-006 declared. |
| `CX-007` | isotopologue or isotopically labelled | Differ only in isotopic composition (`deuterated` forms, `carbon-14` tracers). Distinct substances; conflate only for use cases indifferent to labelling. |
| `CX-008` | structure vs role | ChEBI runs two hierarchies: what a thing *is* (structure) and what it *does* (role — `anti-inflammatory agent`, `EC 3.4.21.* inhibitor`). A structural term and a role term are never the same entity even when a label suggests it. **Rejection ground.** |
| `CX-009` | class vs individual compound | One side is a structural class (`steroid`, `penicillin`), the other a specific compound. This is a scope difference, not a conflation — see `SC-006`. Listed here because chemical class labels read like compound names. |
| `CX-010` | mixture or combination product vs single substance | Object names a formulated combination (`amoxicillin/clavulanate`) where the subject is one component. **Rejection ground**; if the set needs components, split the mapping and say so (`SC-004` applies too). |
| `CX-011` | substance vs product/brand | One side is a marketed product or brand (`Advil`, an NDC, an RxNorm SCD), the other a chemical substance. Different primary categories. **Rejection ground** unless the set explicitly maps products to actives. |
| `CX-012` | polymer or macromolecule vs repeat unit | Object denotes a polymer, subject its monomer, or vice versa. **Rejection ground.** |
| `CX-013` | mineral/nutrient element vs compound | `iron` the element vs `ferrous sulfate` the administered compound. Common in supplement and nutrition data. **Rejection ground** unless declared. |

---

## Notes for reviewers

**Structural identifiers are evidence, and better evidence than labels.** Where both sides
carry InChIKey, SMILES or CAS, compare them — that is a `EV-009`-strength check available at
`EV-001` cost, and it is the main way this domain is *easier* than disease mapping. Note that
an InChIKey's first block encodes the skeleton, so a matching first block with a differing
second block is exactly the CX-001/CX-003 situation.

**Beware label-only matching on drug names.** International non-proprietary names vary
systematically across regions (`paracetamol`/`acetaminophen`, `-in`/`-ine` endings,
`ph`/`f` spellings). Those are naming variants and belong in `EV-004`, not here. What belongs
here is anything that changes the substance.

**Precedent worth knowing.** MeDIC's lexical grounder already strips salts and esters to
reach the active moiety and deliberately scopes the result `skos:closeMatch` rather than
`skos:exactMatch`. That is `CX-001` applied correctly — it just had no rule ID to cite.
