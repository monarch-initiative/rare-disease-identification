"""Apply batch 3 of the curated functional-capacity assessments (diseases 151-300).

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
# Batch 3 leans on Orphanet, which reaches 18 of these 150. Where the record is
# expert-validated the line is STRONG and can set TOTAL alone; where it is not,
# the level is capped at SUBSTANTIAL by evidence strength, not by the clinical
# picture - and the rationale says so, so a reviewer can raise it deliberately.
C = {}

def orph(work, care, stage, confw, confc, wrat, crat, wlvl="TOTAL", clvl="TOTAL",
         ctx="STANDARD_OF_CARE_TREATED"):
    return {"work_capacity": (wlvl, ctx, stage, confw, wrat, []),
            "care_dependence": (clvl, ctx, stage, confc, crat, [])}

# --- expert-validated: STRONG, can carry TOTAL ------------------------------
C["MONDO:0007182"] = orph(None, None, "ADULT_ONSET", 86, 85,
  "Orphanet's expert-validated panel rates paid work and professional tasks as severe, "
  "permanent limitations occurring very frequently. Machado-Joseph disease is progressive "
  "and adult-onset, so the limitation accumulates across working life.",
  "Orphanet's experts rate body care and dressing as severe permanent limitations occurring "
  "very frequently, placing daily personal assistance on a carer as the disease advances.")

C["MONDO:0008119"] = orph(None, None, "ADULT_ONSET", 85, 85,
  "Orphanet's expert-validated panel rates professional tasks as a complete permanent "
  "limitation and paid work as severe, both occurring frequently. SCA1 is progressive, so "
  "this describes the established rather than the earliest stage.",
  "Body care and dressing are rated severe permanent limitations occurring very frequently. "
  "Recorded against the progressed stage; early SCA1 does not create a daily care need.")

C["MONDO:0009591"] = orph(None, None, "PAEDIATRIC", 90, 90,
  "Orphanet's expert-validated panel rates paid work and professional tasks as complete, "
  "permanent limitations occurring very frequently. Juvenile metachromatic leukodystrophy is "
  "a progressive demyelinating disease with loss of acquired skills; SSA also lists it as a "
  "Compassionate Allowance.",
  "Body care and dressing are rated severe permanent limitations occurring very frequently, "
  "on a course of progressive motor and cognitive regression.")

C["MONDO:0008678"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "ANY", 84,
   "Orphanet's expert-validated panel rates paid work as a severe permanent limitation "
   "occurring very frequently, and professional tasks as severe and frequent. Minnesota also "
   "reaches the code. Williams syndrome pairs relative verbal strength with marked visuospatial "
   "and executive difficulty, so supported rather than competitive employment is typical.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 72,
   "Held below TOTAL on the evidence: Orphanet rates managing one's own health as severe and "
   "very frequent, but body care only as a moderate acquisition delay. Many adults manage "
   "personal care with supervision rather than hands-on assistance.", []),
}

C["MONDO:0008300"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "ANY", 84,
   "Orphanet's expert-validated panel rates paid work in a standard environment as a severe "
   "permanent limitation occurring very frequently. Montana names Prader-Willi syndrome "
   "directly on its medically-frail list, and two state code lists reach Q87.11 - three "
   "independent government determinations alongside the expert rating.", []),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "ANY", 86,
   "Orphanet rates eating and drinking as severe limitations occurring very frequently. The "
   "care need in Prader-Willi is distinctive: hyperphagia requires continuous supervision of "
   "food access rather than help with the mechanics of eating, and that supervision is "
   "lifelong and unremitting.", []),
}

# --- not expert-validated: MODERATE, capped at SUBSTANTIAL ------------------
def capped(stage, wrat, crat, confw=76, confc=76, ctx="STANDARD_OF_CARE_TREATED"):
    return {"work_capacity": ("SUBSTANTIAL", ctx, stage, confw, wrat, []),
            "care_dependence": ("SUBSTANTIAL", ctx, stage, confc, crat, [])}

C["MONDO:0008840"] = capped("PAEDIATRIC",
  "Orphanet rates paid work as a complete permanent limitation occurring very frequently, and "
  "SSA lists ataxia telangiectasia as a Compassionate Allowance - two independent sources "
  "agreeing. Capped at SUBSTANTIAL only because the Orphanet record is not expert-validated, "
  "so no STRONG line exists; the clinical picture would support TOTAL.",
  "Body care and dressing are rated severe permanent limitations occurring very frequently, on "
  "a course of progressive cerebellar degeneration with loss of ambulation in childhood. Same "
  "evidence-strength cap.", 80, 80)

C["MONDO:0010651"] = capped("CONGENITAL",
  "Orphanet rates paid work and professional tasks as severe permanent limitations occurring "
  "very frequently, and SSA lists Menkes disease as a Compassionate Allowance. Menkes is "
  "usually fatal in early childhood, so work capacity rarely arises in practice - a reviewer "
  "may prefer NOT_APPLICABLE.",
  "Severe permanent limitations in body care and dressing, very frequent, on a course of "
  "progressive neurodegeneration from infancy.", 74, 80)

C["MONDO:0010568"] = capped("CONGENITAL",
  "Orphanet rates paid work and professional tasks as severe permanent limitations occurring "
  "very frequently, and SSA lists Aicardi syndrome as a Compassionate Allowance. Capped by "
  "evidence strength: the Orphanet record is not expert-validated.",
  "Body care and dressing rated severe, permanent and very frequent, on a background of "
  "infantile spasms and severe developmental impairment.", 80, 82)

C["MONDO:0019876"] = capped("CONGENITAL",
  "Orphanet rates paid work and professional tasks as severe permanent limitations occurring "
  "very frequently. This is the only substantive source - no policy list reaches the disease "
  "and no functional-outcome cohort was retrieved - so the level rests on one source and stops "
  "at SUBSTANTIAL.",
  "Body care and dressing rated severe, permanent and very frequent, on a background of "
  "significant intellectual disability and hypotonia.")

C["MONDO:0019569"] = capped("PAEDIATRIC",
  "Orphanet rates paid work and professional tasks as complete permanent limitations occurring "
  "frequently. Cockayne syndrome type 1 is a progressive multisystem degeneration with a "
  "shortened lifespan, so working age is often not reached.",
  "Body care and dressing rated complete permanent limitations, frequent, on a course of "
  "progressive neurological and sensory deterioration.", 78, 80)

C["MONDO:0012198"] = capped("CONGENITAL",
  "Orphanet rates paid work as a complete permanent limitation occurring very frequently and "
  "professional tasks as severe. PCWH combines peripheral demyelinating neuropathy, central "
  "dysmyelination, Waardenburg syndrome and Hirschsprung disease.",
  "Held at SUBSTANTIAL: managing one's own health is rated a frequent limitation but body care "
  "only as moderate, so the picture is assistance and supervision rather than total dependence.",
  78, 70)

C["MONDO:0010035"] = capped("CONGENITAL",
  "Three sources agree: Orphanet rates paid work and professional tasks as severe permanent "
  "limitations occurring very frequently, two state lists reach E78.72, and SSA lists "
  "Smith-Lemli-Opitz syndrome as a Compassionate Allowance. Capped at SUBSTANTIAL only because "
  "the Orphanet record is not expert-validated.",
  "Body care and dressing rated severe, permanent and very frequent, on a background of "
  "intellectual disability, feeding difficulty and characteristic malformations.", 82, 82)

C["MONDO:0010519"] = capped("CONGENITAL",
  "Orphanet rates paid work as a complete permanent limitation and professional tasks as "
  "severe, both very frequent. ATR-X causes severe intellectual disability with profound "
  "speech impairment, so competitive employment does not realistically arise.",
  "Body care is rated a severe permanent limitation, frequent, with an additional very frequent "
  "acquisition delay - so both failure to acquire the skill and ongoing limitation.")

C["MONDO:0009092"] = capped("ADULT_ONSET",
  "Orphanet rates paid work and professional tasks as complete permanent limitations occurring "
  "very frequently. Nasu-Hakola disease causes early-onset dementia with bone cysts, typically "
  "presenting in the third decade and ending working life.",
  "Body care and drinking rated complete permanent limitations, very frequent, on a course of "
  "presenile dementia progressing to total dependence.", 80, 82)

C["MONDO:0009260"] = {
 "work_capacity": ("NOT_APPLICABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 80,
   "Orphanet holds no paid-work or professional-task rows for this disease, and infantile GM1 "
   "gangliosidosis is usually fatal in early childhood, so work capacity does not arise for the "
   "typical affected person. Recorded as NOT_APPLICABLE rather than TOTAL so it is not read as "
   "a statement about working-age adults.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 84,
   "Orphanet rates body care and dressing as complete permanent limitations occurring very "
   "frequently, on a course of rapid neurodegeneration from infancy. Capped at SUBSTANTIAL "
   "only because the record is not expert-validated; the clinical picture is total dependence "
   "and a reviewer should consider raising it.", []),
}

# --- Orphanet argues the score DOWN -----------------------------------------
# The three most informative rows in this batch. All are treatable, all rank
# high on a score that reads untreated natural history, and Orphanet's raters
# put the actual limitation at or below the >=30% bar.

C["MONDO:0009672"] = {   # spinal muscular atrophy type III (Kugelberg-Welander)
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 30,
   "Orphanet's rater records paid work in a standard environment and professional tasks as "
   "'None | None | None' - no limitation at all - and does the same for self-care items, "
   "while rating only peripheral activities such as administrative procedures as occasional "
   "and low. SMA type III is the ambulatory form, and disease-modifying therapy has improved "
   "motor outcomes further. The phenotype score ranks it in the top 300 because it reads the "
   "SMA phenotype without distinguishing type III from types I and II. The score is wrong here.",
   []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 28,
   "Orphanet records body care and dressing as 'None | None | None'. Most people with SMA III "
   "walk independently into adulthood and do not need daily personal assistance, though some "
   "lose ambulation later. Recorded as MILD rather than NONE because the record is not "
   "expert-validated and later loss of ambulation does occur.", []),
}

C["MONDO:0008919"] = {   # systemic primary carnitine deficiency
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 30,
   "Orphanet rates paid work as only an occasional limitation of LOW severity - below the "
   ">=30% bar on frequency and below it again on severity. Systemic primary carnitine "
   "deficiency responds to lifelong L-carnitine supplementation, and treated patients are "
   "typically asymptomatic. Nebraska reaches E71.41 on its code list, which is the one source "
   "pointing the other way; a reviewer should decide whether that listing reflects the treated "
   "or the untreated course.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 28,
   "Orphanet rates dressing and drinking as occasional limitations of moderate severity, below "
   "the bar on frequency. The danger in this disease is acute metabolic decompensation and "
   "cardiomyopathy if supplementation lapses, not a continuing personal-care need.", []),
}

C["MONDO:0008948"] = {   # cerebrotendinous xanthomatosis
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 60,
   "Orphanet's own rows disagree with each other: paid work in a standard environment is rated "
   "a severe permanent limitation occurring very frequently, but performing professional tasks "
   "only occasionally. SSA lists cerebrotendinous xanthomatosis as a Compassionate Allowance. "
   "Against that, the disease responds to chenodeoxycholic acid, and early treatment prevents "
   "the progressive neurological decline that drives the limitation - so the untreated course "
   "overstates the expectation for a diagnosed, treated patient.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 40,
   "Orphanet rates continence and body care as occasional limitations of moderate or "
   "unspecified severity - below the >=30% bar - so the expert source does not support a daily "
   "care need. Untreated late-stage disease does produce one, which is why this is MILD rather "
   "than NONE.", []),
}

# --- literature-backed ------------------------------------------------------

ARSACS = lit("PMID:33307884",
    "Wheelchair mobility, motor performance and participation of adult wheelchair users with ARSACS: a cross-sectional study.",
    "Although approximately 45% of adults with Autosomal Recessive Spastic Ataxia of Charlevoix-Saguenay (ARSACS) are permanent wheelchair users, this sub population has been less studied.",
    "Adults with ARSACS; figure stated as the premise of a wheelchair-user study",
    "Permanent wheelchair use in about 45% of adults. Recorded as MODERATE because the "
    "figure is the study's background premise rather than its own measurement.",
    strength="MODERATE")
C["MONDO:0010041"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 74,
   "About 45% of adults are permanent wheelchair users, on a course of progressive spastic "
   "ataxia with neuropathy beginning in early childhood. Held at SUBSTANTIAL: wheelchair use "
   "is not itself inability to work, and no employment rate has been measured for ARSACS.",
   [ARSACS]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 70,
   "Permanent wheelchair use in about 45% of adults implies help with transfers for a "
   "substantial proportion, but wheelchair use and personal-care dependence are not the same "
   "thing and no ADL measurement exists.",
   [ARSACS]),
}

MOCD = lit("PMID:35192225", "Molybdenum cofactor deficiency: A natural history.",
    "One-year survival rates were 77.4% (overall), 71.8% (neonatal onset MoCD-A), and 76.9% (neonatal onset MoCD-B); median ages at death were 2.4, 2.4, and 2.2 years, respectively.",
    "Natural history cohort of molybdenum cofactor deficiency, reported by subtype",
    "Reports survival for MoCD-B specifically: median age at death 2.2 years.")
C["MONDO:0009644"] = {
 "work_capacity": ("NOT_APPLICABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 85,
   "Median age at death in neonatal-onset MoCD-B is 2.2 years, so work capacity does not "
   "arise for the typical affected person. Recorded as NOT_APPLICABLE rather than TOTAL so it "
   "is not read as a statement about working-age adults. Note that fosdenopterin treats "
   "MoCD-A, not type B, so the natural history stands for this subtype.",
   [MOCD]),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 88,
   "Neonatal seizures, profound developmental impairment and death at a median 2.2 years. "
   "Survivors need total daily care throughout.",
   [MOCD]),
}

MENKES = lit("PMID:38969962", "Phenotypic and mutational spectrum of 17 Chinese patients with Menkes Disease.",
    "Out of 13 patients with follow-up (median: 24 months), 7 patients (53.8%) died with median survival of 40 months (range: 21-48 months), 3 patients (23.1%) show severe motor development delay and 2 (15.4%) have refractory epilepsy, only the mild MD patient shows improved cerebellar ataxia.",
    "13 Chinese patients with Menkes disease followed a median 24 months",
    "Mortality of 53.8% with median survival 40 months, and severe motor delay in most "
    "survivors.", strength="MODERATE")
C["MONDO:0010651"]["work_capacity"] = ("NOT_APPLICABLE", "STANDARD_OF_CARE_TREATED",
   "CONGENITAL", 84,
   "Revised from the Orphanet-only reading: 53.8% of 13 followed patients died at a median "
   "survival of 40 months, so classical Menkes disease rarely reaches working age at all. "
   "Recorded as NOT_APPLICABLE rather than TOTAL. Orphanet does rate paid work as a severe "
   "permanent limitation, and SSA lists the disease, but neither speaks to a population that "
   "mostly does not survive childhood.",
   [MENKES])
C["MONDO:0010651"]["care_dependence"] = ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 86,
   "Severe motor developmental delay in most survivors, with refractory epilepsy in a further "
   "15%, alongside Orphanet's severe permanent ratings for body care and dressing. Total "
   "daily care for the whole surviving population.",
   [MENKES])

GM3 = lit("PMID:30691927",
    "Recessive GM3 synthase deficiency: Natural history, biochemistry, and therapeutic frontier.",
    "Development stagnated early in life; only 13 (26%) patients sat independently (median age 30 months), three (6%) learned to crawl, and none achieved reciprocal communication.",
    "50 patients with GM3 synthase deficiency, natural history study",
    "Only 26% ever sit independently, 6% crawl, and none achieve reciprocal communication.")
C["MONDO:0018274"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 92,
   "No patient in the natural-history cohort achieved reciprocal communication and only 26% "
   "ever sat independently. Competitive employment does not arise. Recorded as TOTAL rather "
   "than NOT_APPLICABLE because survival into adulthood does occur.",
   [GM3]),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 93,
   "Only 26% sit independently and 6% crawl, so transfers, feeding and all personal care fall "
   "to a carer for essentially the whole population.",
   [GM3]),
}

SSADH = lit("PMID:39919676",
    "The neuropsychological profile of SSADH deficiency, a neurotransmitter disorder of GABA metabolism.",
    "The neuropsychological profile of the study's 65 enrollees [54 % females, median (interquartile range) age 9.6 (5.4-14.7)] consisted almost universally of intellectual disability, delays in adaptive skills, and deficits in expressive more than receptive language.",
    "65 enrollees, median age 9.6 years",
    "Near-universal intellectual disability with delays in adaptive skills across 65 patients.")
C["MONDO:0010083"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 76,
   "Intellectual disability and adaptive-skill delay in almost all of 65 enrollees. Held at "
   "SUBSTANTIAL rather than TOTAL because the cohort is paediatric (median age 9.6 years) and "
   "reports a neuropsychological profile rather than an employment or independence outcome; "
   "SSADH deficiency has a wide severity range including mildly affected adults.",
   [SSADH]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 74,
   "Near-universal delays in adaptive skills imply help with daily tasks, but the study "
   "measures neuropsychological profile, not personal-care dependence, and the phenotype "
   "spans mild to severe.",
   [SSADH]),
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
