"""Apply batch 5 of the curated functional-capacity assessments (diseases 451-600).

Reads tmp/frailty_skeleton.yaml (deterministic lanes 1/2/5), adds the
LITERATURE and MODEL_JUDGEMENT lanes, sets the impairment level and writes
tmp/frailty_patch.yaml for apply_curation.py.

Every LITERATURE quote below was fetched with `just fetch-reference` and is an
exact substring of the cached abstract; `just verify-frailty-quotes` is the check.
"""
import yaml, pathlib
from common import TMP, ASSESSMENTS

TODAY = "2026-09-16"
CURATOR = "curate-frailty skill (AI agent)"

def lit(ref, title, quote, population, explanation, strength="STRONG",
        direction="SUPPORTS"):
    return {"lane": "LITERATURE", "direction": direction, "strength": strength,
            "reference": ref, "reference_title": title, "quote": quote,
            "population": population, "explanation": explanation,
            "curator_type": "AI_AGENT", "retrieved_on": TODAY}

def model(conf, explanation, direction="SUPPORTS"):
    return {"lane": "MODEL_JUDGEMENT", "direction": direction, "strength": "WEAK",
            "reference": f"RDIDRUN:curate-frailty/{TODAY}",
            "reference_title": "Structured model reading of the disease description",
            "explanation": explanation, "curator_type": "AI_AGENT"}

# ---------------------------------------------------------------- the curation
# Batch 5 continues batch 4's pattern: Orphanet argues levels DOWN more often than
# up. Six of the thirteen Orphanet-covered diseases here carry disputing rows,
# mostly adult-onset or treatable conditions the phenotype score over-reads.
C = {}

def capped(stage, wrat, crat, confw=76, confc=76, wlvl="SUBSTANTIAL", clvl="SUBSTANTIAL",
           ctx="STANDARD_OF_CARE_TREATED"):
    return {"work_capacity": (wlvl, ctx, stage, confw, wrat, []),
            "care_dependence": (clvl, ctx, stage, confc, crat, [])}

# --- supporting -------------------------------------------------------------
C["MONDO:0012116"] = capped("ADULT_ONSET",   # spinocerebellar ataxia type 8
  "Orphanet's expert-validated panel rates paid work and professional tasks as severe permanent "
  "limitations occurring frequently. SCA8 is slowly progressive with a normal lifespan, so the "
  "limitation accumulates across working life rather than arriving at onset.",
  "Body care and dressing rated severe permanent limitations occurring very frequently. Marked "
  "against the established stage; early SCA8 does not create a daily care need.",
  84, 84, "TOTAL", "TOTAL")

C["MONDO:0010674"] = capped("PAEDIATRIC",   # mucopolysaccharidosis type 2 (Hunter)
  "Orphanet rates paid work and professional tasks as complete permanent limitations occurring "
  "very frequently, a state code list reaches E76.1, and SSA lists MPS II as a Compassionate "
  "Allowance - three sources agreeing. Capped at SUBSTANTIAL only because the Orphanet record "
  "is not expert-validated. The severe neuronopathic form would plainly support TOTAL; the "
  "attenuated form would not, which is the stronger reason to hold here.",
  "Body care and dressing rated severe permanent limitations occurring very frequently. "
  "Idursulfase does not cross the blood-brain barrier, so enzyme replacement does not alter the "
  "neurological course in the severe form.", 82, 84)

C["MONDO:0019570"] = capped("PAEDIATRIC",   # Cockayne syndrome type 2
  "Orphanet rates paid work and professional tasks as complete permanent limitations occurring "
  "frequently. Type 2 is the early-onset severe form, with death usually in childhood, so a "
  "reviewer may prefer NOT_APPLICABLE on this axis.",
  "Body care and dressing rated complete permanent limitations, on a course of profound growth "
  "failure and progressive neurological deterioration from infancy.", 78, 84)

C["MONDO:0011925"] = capped("CONGENITAL",   # merosin-deficient congenital muscular dystrophy
  "Orphanet rates paid work as a severe limitation occurring frequently, recorded both as an "
  "acquisition delay and as a permanent limitation, and SSA lists the disease as a Compassionate "
  "Allowance. Most affected children never walk independently.",
  "Body care rated a severe limitation both as acquisition delay and permanently - so the skill "
  "is typically never acquired rather than lost, which is the distinction the temporality field "
  "is carrying here.", 82, 84)

C["MONDO:0008457"] = capped("ADULT_ONSET",   # spinocerebellar ataxia type 6
  "Orphanet rates paid work and professional tasks as severe permanent limitations occurring "
  "frequently. SCA6 is the most purely cerebellar of the common SCAs, with late onset (typically "
  "the fifth decade) and a normal lifespan, so much of its course falls at the end of working "
  "life or after it.",
  "Held at SUBSTANTIAL: Orphanet rates body care as severe and frequent in one row but only "
  "occasional and transient in another, so the expert source does not consistently describe a "
  "standing care need.", 74, 66)

C["MONDO:0800043"] = {   # Stuve-Wiedemann syndrome 1
 "work_capacity": ("UNKNOWN", "UNKNOWN", None, 45,
   "Orphanet holds no paid-work or professional-task rows for this disease, so the expert "
   "database is silent on this axis, and no functional-outcome cohort was retrieved. Most "
   "affected infants die in the first years of life from dysautonomic crises, so a reviewer "
   "may conclude NOT_APPLICABLE - but that is not what the sources say, so no level is "
   "asserted here.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 74,
   "Orphanet rates drinking and eating as severe limitations occurring very frequently, recorded "
   "as acquisition delays - feeding difficulty with swallowing dysfunction is a defining feature "
   "and usually requires tube feeding.", []),
}

C["MONDO:0010691"] = {   # Norrie disease
 "work_capacity": ("UNKNOWN", "UNKNOWN", None, 45,
   "Orphanet holds no paid-work rows for Norrie disease. Congenital blindness with progressive "
   "hearing loss in about a third, and intellectual disability in a minority, gives a very wide "
   "range of working outcomes that no retrieved source quantifies. No level is asserted.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "Orphanet rates moving around within the home as only a MODERATE limitation despite the "
   "blindness being congenital and total - the expert source describes adaptation rather than "
   "dependence. No other self-care row is rated.", []),
}

# --- Orphanet argues the score DOWN ----------------------------------------

C["MONDO:0009258"] = {   # classic galactosemia
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "Orphanet's expert-validated panel rates paid work and professional tasks as MODERATE "
   "permanent limitations - frequent, but explicitly moderate rather than severe. Classic "
   "galactosemia is newborn-screened and treated by galactose restriction from the first days "
   "of life, which prevents the neonatal crisis entirely; the residual burden is a specific "
   "cognitive and speech profile plus primary ovarian insufficiency, not incapacity. Most "
   "affected adults work.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 35,
   "Orphanet rates managing one's own health as a DISPUTING row. The lifelong dietary burden is "
   "real but is self-managed by most affected adults; this is not a personal-care need. The "
   "phenotype score reads the untreated neonatal course, which no screened patient experiences.",
   []),
}

C["MONDO:0001347"] = {   # facioscapulohumeral muscular dystrophy
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 40,
   "Orphanet's expert-validated panel rates paid work and professional tasks as OCCASIONAL "
   "limitations with severity UNSPECIFIED - below the >=30% bar and carrying no severity claim. "
   "FSHD is slowly progressive with a normal lifespan; about 20% eventually use a wheelchair, "
   "so the majority do not. A state code list reaches G71.02, which is the one source pointing "
   "the other way and should be adjudicated by a human.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 38,
   "Dressing and drinking rated occasional - severe when they occur, but affecting a minority. "
   "Shoulder-girdle weakness makes overhead tasks hard well before anything resembling "
   "dependence on another person.", []),
}

C["MONDO:0019600"] = {   # xeroderma pigmentosum
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 58,
   "Orphanet rates paid work as an OCCASIONAL limitation - severe when present, but below the "
   "bar on frequency - while SSA lists xeroderma pigmentosum as a Compassionate Allowance. The "
   "two sources disagree, and the reason is instructive: the barrier in XP is near-total "
   "avoidance of ultraviolet light, which excludes most ordinary workplaces without impairing "
   "capability at all. That is an accommodation problem, not an incapacity one, and the "
   "neurological subtypes are a separate and more severe question.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "Body care and dressing rated occasional. The dominant burden is lifelong photoprotection and "
   "skin-cancer surveillance rather than help with personal care. The XP-neurological subtypes "
   "do develop a care need, and a reviewer should consider splitting them out.", []),
}

C["MONDO:0009614"] = {   # methylmalonic aciduria, cblB type
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 38,
   "Orphanet's expert-validated panel rates paid work as OCCASIONAL with severity UNSPECIFIED, "
   "recorded both permanently and transiently. cblB is a B12-responsive form of methylmalonic "
   "aciduria - hydroxocobalamin plus dietary management prevents the crises that cause the "
   "damage - so it sits at the mild end of the MMA spectrum. Note the contrast with "
   "MONDO:0009612 (mut deficiency), curated VARIABLE in batch 4 on a cohort where 37% died.",
   []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 36,
   "Body care rated occasional with severity unspecified, permanent and transient. Treated cblB "
   "patients largely manage their own care; the risk is acute decompensation, not a standing "
   "care need.", []),
}

C["MONDO:0009623"] = {   # Nijmegen breakage syndrome
 "work_capacity": ("UNKNOWN", "UNKNOWN", None, 45,
   "Orphanet rates paid work and professional tasks as frequent but with severity UNSPECIFIED, "
   "so the rating carries no severity claim and cannot establish a level. The dominant burden "
   "in Nijmegen breakage syndrome is immunodeficiency and a very high malignancy risk rather "
   "than a standing functional limitation, and microcephaly with borderline-to-moderate "
   "intellectual disability varies widely. PubMed returned no quotable employment or "
   "independence measurement. No level is asserted.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 35,
   "Orphanet rates body care as only an occasional limitation of LOW severity, and managing "
   "one's own health as neutral. The care burden is oncological surveillance and infection "
   "management, not daily personal assistance.", []),
}

C["MONDO:0012496"] = {   # Koolen-de Vries syndrome
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 70,
   "Orphanet's own work rows disagree: paid work in a standard environment is rated a severe "
   "permanent limitation occurring very frequently, but professional tasks are rated with "
   "severity UNSPECIFIED. Koolen-de Vries involves mild to moderate intellectual disability "
   "with a characteristically friendly disposition, and supported employment is common - so "
   "SUBSTANTIAL rather than TOTAL, and the disagreement is recorded rather than resolved.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 66,
   "Managing one's own health is rated a supporting limitation while body care is rated with "
   "severity unspecified. The picture is supervision and prompting rather than hands-on "
   "personal care, which is why this stops well below TOTAL.", []),
}

# --- literature: both lines CORROBORATE an Orphanet "argues down" call ------

FSHD_LIT = lit("PMID:16508966", "Facioscapulohumeral muscular dystrophy.",
    "Although FSHD is considered a relatively benign dystrophy by some, as many as 20% of patients eventually become wheelchair-bound.",
    "Review of facioscapulohumeral muscular dystrophy",
    "Eventual wheelchair use in about 20% - so roughly four in five never reach it, which is "
    "what keeps this below the >=30% bar.", strength="MODERATE")
C["MONDO:0001347"]["work_capacity"] = ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 46,
   "Two independent sources now agree on a LOW level. Orphanet's expert-validated panel rates "
   "paid work as an OCCASIONAL limitation with severity unspecified, and the literature puts "
   "eventual wheelchair use at about 20% - below the >=30% bar on both counts. FSHD is slowly "
   "progressive with a normal lifespan. A state code list reaches G71.02, which is the one "
   "source pointing the other way and should be adjudicated by a human.",
   [FSHD_LIT])
C["MONDO:0001347"]["care_dependence"] = ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 42,
   "About 20% eventually become wheelchair-bound, so four in five do not, and Orphanet rates "
   "dressing and drinking as occasional. Shoulder-girdle weakness makes overhead tasks hard "
   "long before anything resembling dependence on another person.",
   [FSHD_LIT])

PNPLA6 = lit("PMID:35069422",
    "Multifaceted and Age-Dependent Phenotypes Associated With Biallelic PNPLA6 Gene Variants: Eight Novel Cases and Review of the Literature.",
    "Progression of cerebellar symptoms was slow in all patients, who retained ambulation even after a mean disease duration of 15 years.",
    "Eight new cases plus literature review of biallelic PNPLA6 variants",
    "Ambulation retained in all patients after a mean 15 years of disease - a direct argument "
    "against a high impairment level.", strength="MODERATE", direction="DISPUTES")
C["MONDO:0008980"] = {
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "All patients retained ambulation after a mean disease duration of 15 years, with slow "
   "cerebellar progression. Boucher-Neuhauser syndrome combines ataxia, hypogonadism and "
   "chorioretinal dystrophy; the visual loss is the more limiting feature for work, and the "
   "ataxia progresses slowly enough that most affected people remain mobile for decades. "
   "Orphanet holds no record for this disease, so the literature carries it alone - one source, "
   "which is itself a reason not to assert more than MILD.",
   [PNPLA6]),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 38,
   "Retained ambulation across all patients after 15 years argues directly against a daily "
   "personal-care need. Chorioretinal dystrophy creates a need for adaptation rather than "
   "assistance from another person.",
   [PNPLA6]),
}

# ------------------------------------------------------------------ assembly
def build():
    skel = yaml.safe_load(pathlib.Path(TMP / "frailty_skeleton.yaml").read_text())
    searched = 0
    for mid, entry in skel.items():
        for slot in ASSESSMENTS:
            a = entry[slot]
            a["assessed_by"] = CURATOR
            a["assessed_on"] = TODAY
            spec = C.get(mid, {}).get(slot)
            if spec:
                imp, ctx, stage, conf, rat, extra = spec[:6]
                status = spec[6] if len(spec) > 6 else "AI_CURATED"
                a["impairment"] = imp
                a["care_context"] = ctx
                if stage:
                    a["life_stage"] = stage
                a["model_confidence"] = conf
                a["rationale"] = rat
                a["curation_status"] = status
                a["evidence"] = list(extra) + a["evidence"]
                a["evidence"].append(model(conf, (
                    "Structured reading of the disease description and phenotype profile, "
                    "consistent with the lanes above. Never sufficient alone.")))
            else:
                searched += 1
                axis = ("sustained competitive employment" if slot == "work_capacity"
                        else "need for daily personal assistance")
                refs = [e["reference"] for e in a["evidence"]]
                cal = sorted({r for r in refs if r.startswith("SSACAL:")})
                icd = sorted({r for r in refs if r.startswith("ICD10CM:")})
                found = []
                if cal:
                    found.append("SSA lists this condition as a Compassionate Allowance "
                                 f"({', '.join(cal)}), a national determination that it "
                                 "precludes substantial gainful activity")
                if icd:
                    found.append("a state medically-frail code list already reaches "
                                 f"{', '.join(icd)}")
                a["impairment"] = "UNKNOWN"
                a["care_context"] = "UNKNOWN"
                a["rationale"] = (
                    f"No usable evidence found for {axis}. Searched: Orphanet's "
                    "functional-consequences dataset (no record, or a record with no "
                    "functional rows); the Nebraska and Minnesota medically-frail ICD-10-CM "
                    "code lists; and PubMed on the disease label, its synonyms and the "
                    "causative gene, combined with employment, activities-of-daily-living, "
                    "caregiver-burden, dependency, institutionalisation and natural-history "
                    "terms. No publication reported a quotable functional measurement. The "
                    "phenotype score ranks this disease highly but is a ranking signal only, "
                    "so no level is asserted."
                    + (" Found, but not enough on its own: " + "; ".join(found) +
                       ". That is a single lane, and the synthesis rules require two "
                       "independent lanes before a level is set." if found else ""))
                a["curation_status"] = "AI_CURATED"
                a["evidence"].append(model(40, (
                    "The phenotype profile suggests substantial impairment, but with no "
                    "expert-database, policy or literature line to corroborate it this lane "
                    "cannot carry an assessment on its own.")))
    out = TMP / "frailty_patch.yaml"
    out.write_text(yaml.safe_dump(skel, sort_keys=False, allow_unicode=True, width=100),
                   encoding="utf-8")
    print(f"patch written: {out}")
    print(f"  assessments with a curated level : {sum(len(v) for v in C.values())}")
    print(f"  assessments recorded UNKNOWN     : {searched}")

if __name__ == "__main__":
    build()
