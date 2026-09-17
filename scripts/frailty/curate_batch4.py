"""Apply batch 4 of the curated functional-capacity assessments (diseases 301-450).

Reads tmp/frailty_skeleton.yaml (deterministic lanes 1/2/5), adds the
LITERATURE and MODEL_JUDGEMENT lanes, sets the impairment level and writes
tmp/frailty_patch.yaml for apply_curation.py.

Every LITERATURE quote below was fetched with `just fetch-reference` and is an
exact substring of the cached abstract; `just verify-frailty-quotes` is the check.
"""
import yaml, pathlib
from common import TMP, ASSESSMENTS

TODAY = "2026-09-16"
CURATOR = f"RDIDAGENT:curate-frailty/{TODAY}"

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
# Batch 4 is unusually well covered: 19 of 150 carry Orphanet functional rows, and
# several are diseases with real policy standing (ALS, Huntington). It is also the
# batch where Orphanet most often argues levels DOWN - four treatable or episodic
# diseases are rated "Occasional", below the >=30% bar, despite ranking high.
C = {}

def capped(stage, wrat, crat, confw=76, confc=76, wlvl="SUBSTANTIAL", clvl="SUBSTANTIAL",
           ctx="STANDARD_OF_CARE_TREATED"):
    return {"work_capacity": (wlvl, ctx, stage, confw, wrat, []),
            "care_dependence": (clvl, ctx, stage, confc, crat, [])}

# --- expert-validated, supporting: TOTAL ------------------------------------
C["MONDO:0009697"] = capped("PAEDIATRIC",   # Lafora disease
  "Orphanet's expert-validated panel rates paid work and professional tasks as complete, "
  "permanent limitations occurring very frequently, and SSA lists Lafora disease as a "
  "Compassionate Allowance. Lafora is a progressive myoclonic epilepsy with relentless "
  "cognitive decline and death usually within a decade of onset in adolescence.",
  "Body care and dressing rated complete permanent limitations occurring very frequently, on a "
  "course of progressive dementia, myoclonus and loss of ambulation.",
  90, 91, "TOTAL", "TOTAL")

C["MONDO:0009341"] = capped("CONGENITAL",   # Mowat-Wilson syndrome
  "Orphanet's expert-validated panel rates paid work and professional tasks as complete "
  "permanent limitations occurring very frequently, and SSA lists Mowat-Wilson syndrome as a "
  "Compassionate Allowance. Severe intellectual disability with absent or minimal speech is "
  "definitional.",
  "Body care and managing one's own health rated complete permanent limitations occurring very "
  "frequently.", 89, 89, "TOTAL", "TOTAL")

# --- Huntington: the pre-manifest case the spec calls out -------------------
C["MONDO:0007739"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "PRE_MANIFEST_EXCLUDED", 88,
   "Orphanet's expert-validated panel rates paid work as a complete permanent limitation "
   "occurring frequently; Montana names Huntington's disease directly on its medically-frail "
   "list and a state code list reaches G10. Recorded with life_stage PRE_MANIFEST_EXCLUDED, "
   "which matters more here than anywhere else in the dataset: gene-positive people before "
   "onset have no functional limitation at all, and applying a disease-level expectation to "
   "them would be exactly the misuse this schema exists to prevent. One Orphanet row rates the "
   "same activity with severity Unspecified, which is why a disputing line is recorded.", []),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "PRE_MANIFEST_EXCLUDED", 88,
   "Body care and dressing rated complete permanent limitations occurring frequently. Manifest "
   "Huntington's disease progresses to full dependence; pre-manifest carriers are excluded for "
   "the same reason as on the work axis.", []),
}

# --- policy-heavy, Orphanet not expert-validated ---------------------------
C["MONDO:0004976"] = capped("ADULT_ONSET",   # amyotrophic lateral sclerosis
  "Four sources agree: Orphanet rates paid work as a severe permanent limitation occurring "
  "frequently, Montana names ALS directly on its medically-frail list, a state code list "
  "reaches G12.21, and SSA lists ALS as a Compassionate Allowance. Capped at SUBSTANTIAL only "
  "because the Orphanet record is not expert-validated, so no STRONG line exists - the clinical "
  "picture of progressive paralysis with median survival of 2-4 years plainly supports TOTAL, "
  "and a reviewer should raise it.",
  "Body care and dressing rated severe permanent limitations occurring frequently, on a course "
  "of progressive paralysis ending in ventilator dependence or death. Same evidence-strength "
  "cap; this is among the strongest candidates in the dataset for a reviewer to raise to TOTAL.",
  84, 86)

C["MONDO:0016532"] = capped("PAEDIATRIC",   # Lennox-Gastaut syndrome
  "Orphanet rates paid work and professional tasks as complete permanent limitations occurring "
  "very frequently, and a state code list reaches G40.81. Lennox-Gastaut is a drug-resistant "
  "epileptic encephalopathy with intellectual disability in most affected people.",
  "Body care and managing one's own health rated severe permanent limitations occurring very "
  "frequently, with drop attacks adding a continuous injury-supervision need.", 84, 86)

C["MONDO:0010079"] = capped("CONGENITAL",   # Canavan disease
  "Orphanet rates paid work and professional tasks as complete permanent limitations occurring "
  "very frequently, and SSA lists Canavan disease as a Compassionate Allowance. Canavan is a "
  "leukodystrophy with profound developmental impairment from infancy and death usually in "
  "childhood, so a reviewer may prefer NOT_APPLICABLE on this axis.",
  "Body care and dressing rated complete permanent limitations occurring very frequently.",
  80, 86)

C["MONDO:0010645"] = capped("CONGENITAL",   # oculocerebrorenal (Lowe) syndrome
  "Orphanet rates paid work and professional tasks as complete permanent limitations occurring "
  "very frequently, and SSA lists Lowe syndrome as a Compassionate Allowance. Congenital "
  "cataract, intellectual disability and renal tubulopathy together.",
  "Body care rated severe and, notably, continence rated a severe permanent limitation occurring "
  "very frequently - the renal tubulopathy adds a care need beyond the neurological one.",
  82, 84)

C["MONDO:0009452"] = capped("CONGENITAL",   # Vici syndrome
  "Orphanet rates paid work and professional tasks as severe permanent limitations occurring "
  "very frequently. Vici syndrome combines agenesis of the corpus callosum, cataracts, "
  "immunodeficiency and cardiomyopathy, with most children dying young.",
  "Body care and dressing rated severe permanent limitations occurring very frequently, with "
  "recurrent infection adding a continuous medical-care burden.")

C["MONDO:0009281"] = capped("PAEDIATRIC",   # glutaryl-CoA dehydrogenase deficiency (GA1)
  "Orphanet rates paid work as a complete permanent limitation occurring very frequently. The "
  "important caveat is treatment: GA1 is newborn-screened in many countries, and children "
  "treated before an encephalopathic crisis often avoid the dystonic sequelae entirely. This "
  "rating describes the post-crisis course, so care_context should be read carefully.",
  "Body care and dressing rated complete permanent limitations occurring frequently, reflecting "
  "the severe dystonia that follows a striatal crisis rather than the treated course.", 72, 74)

C["MONDO:0010794"] = capped("ANY",   # NARP syndrome
  "Orphanet rates paid work and professional tasks as severe permanent limitations occurring "
  "frequently. NARP is maternally inherited and heteroplasmy-dependent, so severity varies "
  "widely with mutation load.",
  "Held at SUBSTANTIAL and arguably lower: Orphanet rates dressing and drinking only as moderate "
  "acquisition delays, not severe limitations, so the self-care picture is much milder than the "
  "work picture.", 74, 62)

C["MONDO:0009897"] = {   # adult polyglucosan body disease
 "work_capacity": ("UNKNOWN", "UNKNOWN", None, 45,
   "Orphanet holds no paid-work or professional-task rows for this disease, so the expert "
   "database is silent on this axis, and no functional-outcome cohort was retrieved. No level "
   "is asserted.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 70,
   "Orphanet rates continence as a severe permanent limitation occurring very frequently - "
   "neurogenic bladder is often the presenting feature - while moving around the home is rated "
   "only moderate. The care need is real but partial, which is why this is SUBSTANTIAL.", []),
}

# --- Orphanet argues the score DOWN ----------------------------------------
# Five this batch. Three are treatable (Fabry, Gaucher III, Refsum), two are
# episodic rather than permanent (CADASIL, and Alstrom in part). All rank high
# on a score that reads untreated, steady-state natural history.

C["MONDO:0010526"] = {   # Fabry disease
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 35,
   "Orphanet rates paid work and professional tasks as only OCCASIONAL and TRANSIENT "
   "limitations - below the >=30% bar on frequency, and explicitly not permanent. Fabry "
   "disease is treated with enzyme replacement or chaperone therapy, and the dominant burden "
   "in treated patients is episodic neuropathic pain crises rather than a standing inability "
   "to work. Most affected adults are employed.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 32,
   "Orphanet rates managing one's own health as only an occasional limitation. The late "
   "complications that matter in Fabry - renal failure, stroke, cardiomyopathy - create a "
   "treatment burden and episodic crises rather than a continuing personal-care need.", []),
}

C["MONDO:0009267"] = {   # Gaucher disease type III
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 35,
   "Orphanet's expert-validated panel rates paid work and professional tasks as OCCASIONAL "
   "limitations with severity UNSPECIFIED - below the bar on frequency, and carrying no "
   "severity claim at all. Type III is the chronic neuronopathic form; enzyme replacement "
   "controls the visceral disease well, though it does not cross the blood-brain barrier. "
   "Recorded as MILD rather than NONE because the neurological component does progress.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 32,
   "Body care and dressing rated occasional with severity unspecified. Most people with type "
   "III Gaucher disease on treatment manage their own personal care; horizontal gaze palsy and "
   "ataxia can eventually require help.", []),
}

C["MONDO:0009958"] = {   # adult Refsum disease
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 35,
   "Orphanet's expert-validated panel rates paid work as an OCCASIONAL and TRANSIENT "
   "limitation - below the bar on frequency and explicitly reversible. That matches the "
   "disease: adult Refsum responds to dietary phytanic acid restriction and plasmapheresis, "
   "and acute deteriorations resolve when phytanic acid is brought down. A state code list "
   "reaches G60.1, which is the one source pointing the other way.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 32,
   "Moving around the home and dressing rated occasional and transient. The retinitis "
   "pigmentosa and anosmia are permanent, but the motor deterioration that would create a care "
   "need is the treatable part.", []),
}

C["MONDO:0000914"] = {   # CADASIL
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 55,
   "Orphanet's expert-validated panel rates paid work as an OCCASIONAL limitation, recorded "
   "twice - once permanent, once transient. CADASIL runs in recurrent strokes and migraine with "
   "aura, accumulating to vascular dementia over decades, so at any given moment most affected "
   "people are not limited, while the cumulative trajectory is severe. Recorded as SUBSTANTIAL "
   "as a compromise between those two readings, and a reviewer should split it by stage.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PROGRESSIVE_LATE_STAGE", 58,
   "Body care rated occasional, permanent and transient in separate rows. The care need belongs "
   "to the late dementia stage, not to the decades of recurrent stroke that precede it - hence "
   "the explicit late-stage marker.", []),
}

C["MONDO:0008763"] = {   # Alstrom syndrome
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 62,
   "Orphanet's own rows disagree: paid work in a standard environment is rated a severe "
   "permanent limitation occurring frequently, but performing professional tasks only "
   "occasionally and moderately. SSA lists Alstrom syndrome as a Compassionate Allowance. The "
   "likely reading is that blindness and deafness bar many standard workplaces while the "
   "underlying capability is better preserved - which is an accommodation question, not an "
   "incapacity one.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "Orphanet rates body care as only an occasional, moderate limitation and managing one's own "
   "health as neutral. Despite blindness, deafness and multi-organ disease, the expert source "
   "does not describe a daily personal-care need, and this is set below the work axis "
   "deliberately.", []),
}

# --- sensory and metabolic diseases rated MODERATE throughout ---------------
C["MONDO:0019200"] = {   # retinitis pigmentosa
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "Orphanet rates paid work and professional tasks as MODERATE permanent limitations - "
   "frequent, but explicitly moderate rather than severe. Progressive sight loss is a barrier "
   "that accommodation and assistive technology substantially offset, and many affected people "
   "work throughout life. This is the clearest case in the dataset of the phenotype score "
   "over-reading a sensory impairment as incapacity.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 38,
   "Body care and dressing rated moderate, not severe. Blindness creates a need for adaptation "
   "and occasional assistance, not for daily personal care from another person.", []),
}

C["MONDO:0010543"] = {   # Barth syndrome
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 42,
   "Orphanet rates paid work and professional tasks as MODERATE permanent limitations. Barth "
   "syndrome causes cardiomyopathy, neutropenia and exercise intolerance; survival has improved "
   "markedly with cardiac management, and affected adults commonly work with adjustment for "
   "fatigue. A state code list reaches E78.71.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "Body care and dressing rated moderate. The burden is cardiac monitoring, infection risk and "
   "fatigue rather than dependence on another person for personal care.", []),
}

C["MONDO:0011628"] = {   # propionic acidemia
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 70,
   "Orphanet's expert-validated panel rates paid work as a complete permanent limitation "
   "occurring very frequently, but rates professional tasks with severity UNSPECIFIED, so the "
   "two work rows do not agree. Propionic acidemia is newborn-screened and managed with diet "
   "and carnitine; outcome depends heavily on whether metabolic crises were prevented. Held at "
   "SUBSTANTIAL rather than TOTAL for both reasons.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 72,
   "Managing one's own health rated a very frequent limitation - the lifelong dietary and "
   "emergency-regimen burden is the dominant care need - while eating itself is rated only "
   "moderate. That is a supervision and treatment-management need rather than hands-on "
   "personal care.", []),
}

# --- literature-backed ------------------------------------------------------

MLIII = lit("PMID:29704188", "Mucolipidosis type III, a series of adult patients.",
    "Six patients (46%) needed help with activities of daily living (ADL) or were wheelchair-dependent.",
    "13 adult patients with mucolipidosis type III",
    "A direct ADL measurement in adults - the rarest and most useful kind of line for the care "
    "axis.", strength="MODERATE")
C["MONDO:0018931"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 72,
   "46% of adults in a 13-patient series needed help with activities of daily living or were "
   "wheelchair-dependent. Mucolipidosis III is the attenuated form, with progressive joint "
   "stiffness and skeletal dysplasia rather than the neurodegeneration of type II, so many "
   "affected adults work with accommodation. Held at SUBSTANTIAL; no employment rate exists.",
   [MLIII]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 76,
   "46% of adults needed help with activities of daily living or used a wheelchair - a measured "
   "ADL figure, which clears the >=30% bar for SUBSTANTIAL directly. Held below TOTAL because "
   "the series is small and the figure combines ADL help with wheelchair use.",
   [MLIII]),
}

APBD = lit("PMID:23034915",
    "Adult polyglucosan body disease: Natural History and Key Magnetic Resonance Imaging Findings.",
    "The median age was 51 years for the onset of neurogenic bladder symptoms, 63 years for wheelchair dependence, and 70 years for death.",
    "Natural history cohort of adult polyglucosan body disease",
    "Gives the timeline directly: bladder symptoms at 51, wheelchair at 63, death at 70.")
C["MONDO:0009897"]["work_capacity"] = ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED",
   "ADULT_ONSET", 74,
   "Revised from UNKNOWN once the natural history was retrieved. Median age at wheelchair "
   "dependence is 63 - at or beyond the end of working life in most countries - while "
   "neurogenic bladder starts at a median 51. So the disease does impair late working life, "
   "but much of its course falls after it. Orphanet holds no paid-work rows for this disease, "
   "so the literature carries this axis alone.",
   [APBD])
C["MONDO:0009897"]["care_dependence"] = ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED",
   "PROGRESSIVE_LATE_STAGE", 76,
   "Wheelchair dependence at a median 63 years and death at 70, with neurogenic bladder from 51 "
   "- Orphanet independently rates continence a severe permanent limitation occurring very "
   "frequently. Two sources agreeing. Marked late-stage: the care need arrives in the sixth "
   "decade, not at onset.",
   [APBD])

MMA = lit("PMID:17597648",
    "Long-term outcome in methylmalonic acidurias is influenced by the underlying defect (mut0, mut-, cblA, cblB).",
    "Thirty patients (37%) died, and 26 patients survived with a severe or moderate neurologic handicap (31%), whereas 27 patients (32%) remained neurologically uncompromised.",
    "83 patients with methylmalonic aciduria, long-term outcome by genetic subtype",
    "Splits the cohort three ways - 37% died, 31% survived with neurological handicap, 32% "
    "uncompromised - which is why this is VARIABLE rather than a single level.")
MMA_RAT = ("Recorded as VARIABLE because the outcome genuinely splits three ways and the "
  "evidence says so: of 83 patients, 37% died, 31% survived with severe or moderate "
  "neurological handicap, and 32% remained neurologically uncompromised. The split tracks the "
  "underlying defect - mut0 does worst, cblA best - so a reviewer should consider separating "
  "this entry by subtype rather than assigning one level to all of it.")
C["MONDO:0009612"] = {
 "work_capacity": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 55, MMA_RAT, [MMA]),
 "care_dependence": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 55, MMA_RAT, [MMA]),
}

GAN = lit("PMID:31655922",
    "Giant axonal neuropathy: a multicenter retrospective study with genotypic spectrum expansion.",
    "Proximal motor weakness and bulbar symptoms appeared at a mean age of 12 years (8-14), and patients used a wheelchair at a mean age of 16 years (14-18).",
    "Multicentre retrospective cohort of giant axonal neuropathy",
    "Wheelchair use at a mean age of 16, with bulbar involvement from 12 - both before working "
    "age.")
C["MONDO:0009749"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 84,
   "Wheelchair dependence at a mean age of 16 years, with proximal weakness and bulbar symptoms "
   "from 12, on a course that continues to respiratory failure in early adulthood. Affected "
   "people reach working age already severely disabled.",
   [GAN]),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 85,
   "Wheelchair use from mid-adolescence with bulbar involvement means help with transfers, "
   "feeding and eventually respiratory support becomes the norm well before adulthood.",
   [GAN]),
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
