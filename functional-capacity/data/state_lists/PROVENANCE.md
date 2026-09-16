# State medically-frail code lists

Code sets extracted from the primary state documents. The documents themselves are public state
publications and are not redistributed here; these extracted code sets are what the pipeline reads.

| File | Source document | Codes |
|---|---|---|
| `nebraska_icd10cm.txt` | *Nebraska Medicaid Work Requirements — Medically Frail Exemption Conditions Index*, 295 pp, ICD-10-CM by chapter | 4,806 |
| `nebraska_chapter_ranges.txt` | the same, `.x` chapter-range entries | 5 |
| `minnesota_icd10cm.txt` | Minnesota DHS *Appendix A — Medically frail definition per Public Law 119-21 §71119*, 73 diagnosis groups | 6,281 |
| (Montana — not coded) | Montana DPHHS FAQ, ~50 plain-language conditions each mapped to one of the five statutory categories | — |

## Minnesota's inclusion criteria — adopted as our operational definition

> Specific Clinical High-Risk Medical Frailty Diagnosis Codes … included if they were deemed:
> **likely to result in ongoing medical care needs OR impairment that limits likelihood of
> employment, number of hours worked if employed**, extent of community participation, or other
> aspects of economic self-sufficiency; AND **likely to last 6 months or longer**; AND are **not
> easily curable with treatment**.

Methodology attributed by Minnesota to a memo by Ari Ne'eman, Adrianna McIntyre, Daniel L.
Smithers and Benjamin D. Sommers, 27 February 2026.

That sentence contains both of our axes (care dependence, work capacity) plus a duration gate and
a treatment-status gate. We adopt it rather than proposing our own, so the definition is never the
thing under argument.

## Montana screens on function, not only diagnosis

Montana's list includes *bed confinement; need for assistance*, *dependence on ventilator,
wheelchair, oxygen, other devices*, *gait and mobility issues*, *history of falling* — ICF-shaped
functional concepts already in a live state screen.
