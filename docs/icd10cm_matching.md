# How MONDO terms are matched to ICD-10-CM

This is the human-readable companion to `scripts/map_icd10cm/`. It describes what the
matcher actually does, rule by rule, and — separately — the rules that were considered
and **not** implemented, with the reason each one was left out.

The output is `mappings/mondo_icd10cm_exactmatch.sssom.tsv`: one row per list term,
379 exact matches and 2,700 explicit `sssom:NoTermFound` decisions, every row carrying
its reasoning.

**The brief is exact matches only.** A code that is broader, narrower or merely related
to a Mondo term is a rejection, not a weaker row. Everything below serves that: the
rules exist to see past differences in house style, never to close a gap in meaning.

---

## The shape of the problem

Mondo and ICD-10-CM name the same diseases differently, in ways that are systematic
rather than random:

| | Mondo writes | ICD-10-CM writes |
|---|---|---|
| eponyms | `Whipple disease` | `Whipple's disease` |
| word order | `hypercholesterolemia, familial` | `Familial hypercholesterolemia` |
| kind-word | `X disease` | `X disorder` |
| subtype numbering | `type 1` | `type I` |
| spelling | `haematuria` | `hematuria` |

Each of those costs real matches if unhandled. The possessive difference alone hides
Marfan syndrome, Whipple disease, Behçet disease and Ménière disease.

---

## Part 1 — Rules currently implemented

### Stage 0: normalization (applied to both sides, always)

`base_normalize` strips what is never meaning-bearing: accents (`Behçet` → `behcet`),
Unicode dashes and quotes folded to ASCII, bracketed text removed, case folded,
whitespace collapsed. A match that needs only this is still an exact match.

### Stage 1: the ladder

Per Mondo term the matcher walks tiers in order and **stops at the first tier that
produces exactly one ICD-10-CM code**. The query side is the Mondo label plus its
EXACT synonyms; the target side is ICD-10-CM `prefLabel` plus `altLabel`.

| Tier | What it tries | Confidence |
|---|---|---|
| 1 | raw string equality | 1.00 |
| 2 | equality after `base_normalize` | 1.00 × rule |
| 3 | equality after one *surgery* rule (below) | per rule |

Two guards apply throughout, and both are load-bearing:

- **Ambiguity is not a match.** If a tier yields more than one distinct code, nothing
  is emitted and the term goes to human/agentic review. Silently picking one of several
  codes is how a crosswalk stops being trustworthy.
- **Residual rubrics are not matches.** ICD-10-CM files specific diseases as *inclusion
  terms* under catch-all rubrics — "Hereditary coproporphyria" lives under
  `E80.29 Other porphyria`. That is a lexically exact hit on a semantically broader
  class. Any hit whose ICD label contains *other*, *unspecified*, *NEC* or *not
  elsewhere classified* is diverted to review rather than emitted, and adjudicated in
  stage 2 instead. This guard caught **40 would-be matches; review confirmed 38 of them
  as wrong** and replaced the other two with a better, non-residual code (Creutzfeldt-Jakob
  disease to `A81.0` rather than `A81.09 Other Creutzfeldt-Jakob disease`; MPS IV to
  `E76.21` rather than `E76.219 Morquio mucopolysaccharidoses, unspecified`). Without it
  the set would carry a 9% false-positive rate concentrated in exactly the rows a
  clinician would notice first.

### The surgery rules

Each rewrites the query once, then retries. They are applied single-pass, never
chained, so the search stays bounded and reproducible. Rule ids, predicates and
certainties mirror MeDIC's `RULE_PREDICATE` / `RULE_CERTAINTY` tables.

| Rule | Rewrites | Certainty | Real example from this run |
|---|---|---|---|
| `strip_possessive` / `add_possessive` | `X's Y` ↔ `X Y` | 0.97 | fired 16×: `Whipple disease` → `K90.81 Whipple's disease`, also Behçet, Ménière |
| `brit_to_am` / `am_to_brit` | British ↔ American spelling | 0.97 | `haemat`↔`hemat`, `oedema`↔`edema` |
| `comma_drop_type` | `X, type N` → `X type N` | 0.98 | — |
| `hyphen_type` | `type-N` → `type N` | 0.98 | — |
| `cell_hyphen_to_space` / reverse | `T-cell` ↔ `T cell` | 0.97 | — |
| `deficiency_inversion` | `deficiency of X` ↔ `X deficiency` | 0.96 | — |
| `comma_inversion` | `X, congenital` → `congenital X` | 0.95 | fired 3×: `hypercholesterolemia, familial, 1` → `E78.01 Familial hypercholesterolemia` |
| `disease_to_disorder` / reverse | `disease` ↔ `disorder` | 0.95 | — |
| `arabic_to_roman` / reverse | `type 2` ↔ `type ii` | 0.95 | — |
| `syndrome_to_disease` / reverse | `syndrome` ↔ `disease` | 0.88 | fired 3×: `Cushing disease due to pituitary adenoma` → `E24 Cushing's syndrome` |

`comma_inversion` is guarded to a single comma and a tail of at most three words, so
it cannot scramble long descriptive labels. `arabic_to_roman` requires an indicator
word (`type`, `stage`, `grade`, …) before the numeral, so a bare `X` is never read as
the numeral ten — in disease names it is nearly always the chromosome.

### Rules used only to widen the candidate pool

These are implemented, but their hits are **never emitted as exact matches**. MeDIC
scopes them as `broadMatch` or `closeMatch`, and that judgement carries over: they only
propose candidates for stage 2 to adjudicate.

| Rule | Rewrites | MeDIC scope |
|---|---|---|
| `qualifier_strip` | drops a leading clinical qualifier run (`severe congenital X` → `X`) | `skos:broadMatch` |
| `strip_leading_other` | `other X` → `X` | `skos:broadMatch` |
| `fuzzy_edit1_unique` | one edit away, unique hit only | `skos:closeMatch` |

### Stage 2: agentic adjudication

Everything stage 1 could not settle gets a candidate pool from four sources — lexical
ambiguity, the broad-scope rules above, edit-1 neighbours, and IDF-weighted token
retrieval — and an LLM decides concept equivalence, writing a one-sentence reason into
the SSSOM `comment`.

Retrieval has its own trap. ICD-10-CM explodes one concept into laterality and
encounter subcodes (`M08.011`, `M08.012`, …), which swamp a naive top-k: retrieving for
*juvenile idiopathic arthritis* buried `M08 Juvenile arthritis` — the right answer —
beneath its own `M08.0*` siblings. So the matcher retrieves deep, then caps candidates
per 3-character ICD category, always keeping each category's best-scoring code **and**
its most general rubrics.

---

## Part 2 — Rules considered and not implemented

These are proposals, not omissions by oversight. Each is listed with what it would do
and why it was left out. Anyone is welcome to overturn these calls — that is why they
are written down.

### Left out because they would break "exact"

**`combination_split` — splitting `X and Y` into components.**
MeDIC uses this for source literals that name drug combinations. A Mondo label denotes
one disease concept, so splitting it would produce a one-to-many mapping, and no
component is an exact match of the whole term. Deliberately not ported.

**Accepting the nearest parent rubric for numbered subtypes.**
The single biggest lever on coverage. Our list is dominated by terms like
*immunodeficiency 112* or *hearing loss, autosomal recessive 74*, whose only plausible
candidate is the parent rubric (`D83`, `H90`). Accepting those would add several hundred
rows. It was not done because a parent rubric is broader by construction, and pulling
`D83` to represent *CVID 12* pulls every CVID patient. Several reviewers independently
flagged this as the decision point, so it is a policy question rather than a technical
one: **if the project decides subtypes may map up to their parent, this is the switch to
flip**, and it should be flipped explicitly, with the predicate changed to `broadMatch`.

### Left out because they are unsafe without evidence

**Acronym and abbreviation expansion (`JIA` → `juvenile idiopathic arthritis`).**
Mondo already carries most acronyms as EXACT synonyms, which the matcher uses, so the
rule would add little. Generated blindly it is dangerous: three-letter disease acronyms
collide heavily across specialties.

**Stemming or lemmatisation (`tumours`/`tumour`, `-osis`/`-otic`).**
Would catch a handful of plural/adjectival mismatches. Rejected because medical
morphology is treacherous — `-osis` and `-itis` are not interchangeable, and a stemmer
that conflates them produces confident nonsense. The bounded closed-list rules above
buy most of the benefit with none of the risk.

**Edit-distance 2.**
Edit-1 with a unique-hit guard is already only a *candidate* generator, never an
emitter. Widening to edit-2 multiplies the neighbourhood without improving precision,
and in a 97,904-code vocabulary the neighbourhood stops being sparse.

**Definition or description similarity.**
Comparing Mondo `def:` text with ICD inclusion notes would help the hardest cases.
Left out because ICD-10-CM's UMLS2RDF export carries very little usable definition
text, so it would mostly compare a Mondo definition against nothing.

### Left in, but flagged as the weakest thing in the set

**`syndrome_to_disease` / `disease_to_syndrome` (certainty 0.88).**
`X syndrome` and `X disease` are often the same entity, but not reliably — the pairing
is looser than `disease`/`disorder`, which is why it scores 0.88 against 0.95–0.97 for
everything else. It fired 3 times in this run, and is the only rule
whose every firing is arguable. It is not part of MeDIC's rule set; it was added here. **If any implemented rule should be reconsidered first, it is this
one.** One of its hits, `Cushing disease due to pituitary adenoma` → `E24 Cushing's
syndrome`, is arguably wrong on the merits: Cushing *disease* is the pituitary-driven
subset, `E24` is the whole Cushing syndrome category, and `E24.0` is the specific code.

---

## Known limitations

- Coverage is 379 of 3,079 terms (12.3%). That is a property of the list, not of the matcher:
  it is dominated by gene-level and numbered OMIM subtypes that ICD-10-CM does not code.
- Stage 1 is deterministic and reproducible. Stage 2 is not byte-stable across reruns.
- `semapv:CompositeMatching` rows are LLM proposals for human review, not curated
  assertions. Every one carries its reasoning.
- ICD-10-CM here is the 2024ab UMLS2RDF export. Codes added in later revisions are
  absent, so a missing match is not proof that no code exists.
