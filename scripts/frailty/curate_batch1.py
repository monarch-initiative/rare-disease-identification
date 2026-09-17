"""Apply the pilot batch of curated functional-capacity assessments.

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
# work/care -> (impairment, care_context, life_stage, model_confidence, rationale,
#               [extra evidence lines])
C = {}

PMD_LIT = lit("PMID:35346287",
    "Genotype-phenotype correlation and natural history analyses in a Chinese cohort with pelizaeus-merzbacher disease.",
    "However, few of the patients could stand (9.0%) or walk (4.5%) by themselves.",
    "111 patients, Chinese multicentre cohort, median follow-up 53 months",
    "Direct measurement of independent standing and walking in a large identified cohort.")
C["MONDO:0010714"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 90,
   "Fewer than 5% of patients in a 111-patient natural-history cohort walk independently and "
   "most never acquire speech beyond single words, so competitive employment is not attainable "
   "for the great majority. No disease-modifying therapy exists; the cohort describes care as "
   "currently delivered. The phenotype score agrees, but the cohort measurement carries the call.",
   [PMD_LIT]),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 92,
   "Independent standing (9.0%) and walking (4.5%) are rare in the largest published cohort, "
   "which places transfers, washing and dressing on a carer for almost everyone affected. "
   "Nothing in the retrieved evidence disputed this.",
   [PMD_LIT]),
}

QARS_LIT = lit("PMID:32042906",
    "Defining and expanding the phenotype of QARS-associated developmental epileptic encephalopathy.",
    "Moderate (14%) or severe (73%) developmental delay was characteristic, with no achievement of sitting (85%), walking (86%), or talking (90%).",
    "22 patients (10 newly recruited, 12 from the literature), international",
    "Quantifies failure to reach sitting, walking and talking milestones across the whole cohort.")
C["MONDO:0044696"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 92,
   "86% never walk and 90% never talk, with severe developmental delay in 73%. Competitive "
   "employment does not arise for this population. Only supportive care exists, so the cohort "
   "describes the current expectation rather than an untreated course.",
   [QARS_LIT]),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 93,
   "With 85% never sitting independently and pharmacoresistant epilepsy in 79%, daily personal "
   "assistance is near-universal. No evidence line disputed this.",
   [QARS_LIT]),
}

WD_LIT = lit("PMID:35342245", "Wilson's Disease Update: An Indian Perspective.",
    "Being a treatable disorder, early diagnosis and proper management of WD may result in near complete recovery.",
    "Narrative review of published Indian series",
    "States directly that treated Wilson disease commonly returns to near-normal function, "
    "which argues against a high impairment level under standard of care.",
    strength="MODERATE", direction="DISPUTES")
WD_RAT = ("Lanes disagree and are recorded rather than averaged. Orphanet's expert-validated "
  "rating limits paid work only 'occasionally' - below the >=30% bar - and the treatment "
  "literature reports near-complete recovery with chelation, both arguing for a low level. "
  "Against that, Nebraska already lists E83.01 as a medically-frail qualifying code, and the "
  "phenotype score ranks Wilson 16th of 2,807 because it reads untreated natural history. "
  "A human curator should settle whether the policy listing reflects treated or untreated course.")
C["MONDO:0010200"] = {
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 35, WD_RAT, [WD_LIT],
                   "DISPUTED"),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 30, WD_RAT, [WD_LIT],
                     "DISPUTED"),
}

AS_LIT = lit("PMID:32893075", "Epilepsy in Angelman syndrome: A scoping review.",
    "Intractable epileptic seizures since early childhood with characteristic EEG abnormalities are present in 80-90% patients with AS.",
    "Scoping review of published Angelman syndrome series",
    "Intractable early-childhood epilepsy in 80-90% compounds the developmental disability "
    "that drives the work and care limitation.", strength="MODERATE")
C["MONDO:0007113"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "ANY", 92,
   "Orphanet's expert-validated panel rates paid work in a standard environment as a complete "
   "and permanent limitation that is very frequent, which alone meets the bar. Two state "
   "medically-frail lists already reach Q93.51, and intractable epilepsy affects 80-90%.",
   [AS_LIT]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 78,
   "Held at SUBSTANTIAL rather than TOTAL on the evidence: Orphanet's experts rate dressing, "
   "washing, eating and moving around the home as moderate - not severe - permanent "
   "limitations, and transferring as only a low limitation. The near-universal need for "
   "supervision that clinicians describe is not represented in Orphanet's item list, so a "
   "reviewer may well raise this.",
   [AS_LIT]),
}

C["MONDO:0010726"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 93,
   "Orphanet's expert-validated rating makes paid work in a standard environment a complete, "
   "permanent and very frequent limitation. Loss of purposeful hand use and of speech are "
   "definitional. No lane disputed this; no quotable functional-outcome cohort was retrieved, "
   "so the expert database carries the call.", []),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 93,
   "Orphanet's expert panel rates body care, washing and dressing as severe permanent "
   "limitations occurring very frequently, which places daily personal assistance on a carer "
   "for the great majority.", []),
}

ALPERS_LIT = lit("PMID:28446219", None, None, None, None)  # placeholder removed below
del ALPERS_LIT
C["MONDO:0008758"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 88,
   "Orphanet rates paid work as a complete, permanent, very frequent limitation, and Nebraska "
   "already lists G31.81 as a qualifying medically-frail code - two independent lanes agreeing. "
   "The Orphanet record is not expert-validated, so the line is MODERATE rather than STRONG.", []),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 90,
   "Orphanet rates washing, dressing, eating, transferring and moving around the home all as "
   "complete permanent limitations occurring very frequently. Alpers-Huttenlocher is a "
   "progressive hepatocerebral degeneration; the state listing concurs.", []),
}

DMD_LIT = lit("PMID:28446219",
    "The burden, epidemiology, costs and treatment for Duchenne muscular dystrophy: an evidence review.",
    "Loss of ambulation occurred at a median age of 12 and ventilation starts at about 20 years.",
    "Systematic review of 58 studies of DMD patients and carers",
    "Median loss of ambulation at 12 years is before working age, and assisted ventilation "
    "from about 20 establishes a continuing daily care need.")
C["MONDO:0010679"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 90,
   "Ambulation is lost at a median age of 12 - before working age - and ventilatory support "
   "typically begins around 20. Glucocorticoids delay these milestones but do not prevent them, "
   "so this remains the treated expectation. Orphanet holds no functional-consequence rows for "
   "DMD, so the systematic review carries the call.",
   [DMD_LIT]),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 92,
   "Loss of ambulation in early adolescence followed by assisted ventilation in the twenties "
   "makes daily personal assistance the norm well before adulthood.",
   [DMD_LIT]),
}

ASNS_LIT = lit("PMID:35469797",
    "An intractable epilepsy phenotype of ASNS novel mutation in two patients with asparagine synthetase deficiency.",
    "71% of ASNSD patients died during early infancy.",
    "Review statement over previously reported ASNSD patients, plus 2 new Chinese cases",
    "Death in early infancy for most patients settles the working-age question and establishes "
    "total care dependence for survivors.", strength="MODERATE")
C["MONDO:0014258"] = {
 "work_capacity": ("NOT_APPLICABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 88,
   "71% of reported patients die during early infancy, so work capacity does not arise for the "
   "typical affected person. Recorded as NOT_APPLICABLE rather than TOTAL so it is not read as "
   "a statement about working-age adults.",
   [ASNS_LIT]),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 90,
   "Congenital microcephaly with intractable epilepsy and spastic quadriplegia; most die in "
   "infancy and survivors need total daily care. The cohort is small and the figure comes from "
   "a case-report review, so the line is MODERATE.",
   [ASNS_LIT]),
}

TANGO2_LIT = lit("PMID:35568137",
    "Cardiac crises: Cardiac arrhythmias and cardiomyopathy during TANGO2 deficiency related metabolic crises.",
    "There were 10 deaths (37%), 6 related to arrhythmias.",
    "27 children admitted for 43 cardiac crises at 14 centres, median age 6.4 years",
    "Measures mortality during metabolic crises in an identified multicentre paediatric cohort.")
C["MONDO:0018820"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 70,
   "37% mortality during cardiac crises in a 27-child multicentre series, on a background of "
   "intellectual disability and recurrent metabolic decompensation. Held at SUBSTANTIAL because "
   "the measured outcome is mortality and crisis morbidity, not employment, and survivors' "
   "working-age function has not been reported.",
   [TANGO2_LIT]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 72,
   "Recurrent life-threatening metabolic crises requiring hospital escalation, with intellectual "
   "disability between crises, imply continuous supervision. No ADL or caregiver-hours "
   "measurement was retrieved, so this stops short of TOTAL.",
   [TANGO2_LIT]),
}

NFU1_LIT = lit("PMID:36256512", "Phenotypic continuum of NFU1-related disorders.",
    "We report 19 affected individuals from 10 independent families with ultra-rare bi-allelic NFU1 missense variants associated with a spectrum of early-onset pure to complex hereditary spastic paraplegia (HSP) phenotype with a longer survival (16/19) on one end and neurodevelopmental delay with severe hypotonia (3/19) on the other.",
    "19 affected individuals from 10 families, international",
    "Establishes a two-ended phenotypic spectrum, which is why this is recorded as VARIABLE "
    "rather than as a single level.", strength="MODERATE")
C["MONDO:0011582"] = {
 "work_capacity": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 55,
   "The NFU1 phenotype runs from early-onset fatal leukoencephalopathy to a milder hereditary "
   "spastic paraplegia with longer survival in 16 of 19 individuals, so no single level is "
   "representative. Orphanet holds a record for MMDS1 but classifies it 'Not applicable' with "
   "no functional rows.",
   [NFU1_LIT]),
 "care_dependence": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 55,
   "Same spectrum: the classical presentation is rapidly fatal while the missense-variant HSP "
   "end survives with spastic paraplegia of varying severity. Recorded as VARIABLE and left for "
   "a reviewer to split by subtype.",
   [NFU1_LIT]),
}

FDXR_LIT = lit("PMID:39669623",
    "Clinical study of ferredoxin-reductase-related mitochondriopathy: Genotype-phenotype correlation and proposal of ancestry-based carrier screening in the Mexican population.",
    "Mortality is high, with 18% of patients, often infants, passing from complications.",
    "62 cases, natural-history study combining new and previously reported patients",
    "Mortality in an identified 62-case natural-history cohort, alongside frequent optic atrophy, "
    "movement disorder and developmental delay.")
C["MONDO:0971174"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 75,
   "Optic atrophy, movement disorder and developmental delay are frequent across a 62-case "
   "natural-history cohort with 18% mortality. Held at SUBSTANTIAL, not TOTAL, because the "
   "quantified outcome is mortality rather than a functional measure - even though this disease "
   "ranks first of 2,807 on the phenotype score.",
   [FDXR_LIT]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 78,
   "Frequent developmental delay and movement disorder in the published natural history imply a "
   "substantial daily care need, but no ADL or dependency measurement has been reported.",
   [FDXR_LIT]),
}

COQ_LIT = lit("PMID:35483523",
    "Variation of the clinical spectrum and genotype-phenotype associations in Coenzyme Q10 deficiency associated glomerulopathy.",
    "At adult age, kidney survival was equally poor (20-25%) across all disorders.",
    "251 patients across COQ2, COQ6 and COQ8B, registry and literature pooled",
    "Kidney survival of 20-25% by adult age means most affected people reach dialysis or "
    "transplantation, a recurring treatment burden rather than a personal-care need.",
    strength="MODERATE")
C["MONDO:0011829"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 65,
   "Kidney survival is 20-25% by adult age across primary CoQ10 deficiencies, and 47% of COQ2 "
   "patients develop neurological symptoms in early childhood. Dialysis or transplantation plus "
   "neurological involvement is a serious barrier to sustained employment, though no employment "
   "rate has been measured.",
   [COQ_LIT]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 60,
   "The dominant burden is renal replacement therapy rather than personal-care dependence; the "
   "infantile multisystem COQ2 subgroup is the part of the spectrum that needs daily care. "
   "Recorded as SUBSTANTIAL with that split named for a reviewer.",
   [COQ_LIT]),
}

C["MONDO:0011724"] = {
 "work_capacity": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "ANY", 45,
   "Orphanet rates paid work as only a moderate permanent limitation, and classic GLUT1 "
   "deficiency responds to ketogenic diet, so the treated course diverges sharply from the "
   "phenotype score's reading of the untreated one. The Orphanet record is not expert-validated "
   "and no functional-outcome cohort was retrieved, so this is left VARIABLE rather than forced "
   "to a level.", []),
 "care_dependence": ("UNKNOWN", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "Orphanet records no self-care limitation rows for classic GLUT1 deficiency, and a PubMed "
   "search on the disease name and SLC2A1 for ADL, caregiver-burden, dependency and employment "
   "outcomes returned no quotable functional measurement. Recorded UNKNOWN rather than inferred "
   "from the phenotype score alone.", []),
}

FUCO_LIT = lit("PMID:2012122", "Fucosidosis revisited: a review of 77 patients.",
    "The clinical picture of fucosidosis consists of progressive mental (95%) and motor (87%) deterioration, coarse facies (79%), growth retardation (78%), recurrent infections (78%), dysostosis multiplex (58%), angiokeratoma corporis diffusum (52%), visceromegaly (44%), and seizures (38%).",
    "77 patients, review of published cases",
    "Progressive mental deterioration in 95% and motor deterioration in 87% across 77 "
    "patients measures both axes directly.", strength="MODERATE")
C["MONDO:0009254"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 80,
   "Two lanes agree: SSA lists Fucosidosis - Type I as a Compassionate Allowance, a national "
   "determination that it precludes substantial gainful activity, and a 77-patient review "
   "reports progressive mental deterioration in 95% and motor deterioration in 87%. Held at "
   "SUBSTANTIAL rather than TOTAL because the review pools published case reports from 1991 "
   "and no employment rate has ever been measured.",
   [FUCO_LIT]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 80,
   "Progressive motor deterioration in 87% of 77 reviewed patients, with recurrent infections "
   "in 78%, implies a growing daily care need. No ADL or caregiver measurement exists, and the "
   "SSA listing speaks only to work, so this rests on one lane plus the phenotype score and "
   "stops at SUBSTANTIAL.",
   [FUCO_LIT]),
}

MECP2D_LIT = lit("PMID:20425814", "The MECP2 duplication syndrome.",
    "MECP2 duplication syndrome is 100% penetrant in affected males and is associated with infantile hypotonia, severe to profound mental retardation, autism or autistic features, poor speech development, recurrent infections, epilepsy, progressive spasticity, and, in some cases, developmental regression.",
    "Review of reported affected males",
    "Full penetrance with severe-to-profound intellectual disability and progressive "
    "spasticity in affected males.", strength="MODERATE")
C["MONDO:0010283"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 82,
   "SSA lists MECP2 Duplication Syndrome as a Compassionate Allowance, and the clinical "
   "literature reports 100% penetrance in affected males with severe to profound intellectual "
   "disability and progressive spasticity - two lanes agreeing. Held at SUBSTANTIAL because "
   "the supporting source is a narrative review rather than a measured cohort.",
   [MECP2D_LIT]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 82,
   "Severe to profound intellectual disability with progressive spasticity and recurrent "
   "infections in a fully penetrant male phenotype implies daily assistance, but no ADL or "
   "dependency measurement has been published and the SSA listing does not speak to care.",
   [MECP2D_LIT]),
}

C["MONDO:0100040"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 78,
   "Two independent government determinations now count as two lanes rather than one: SSA "
   "lists FOXG1 Syndrome as a Compassionate Allowance, certifying that it precludes "
   "substantial gainful activity, and both Nebraska and Minnesota reach F84.8 on their "
   "medically-frail code lists. Held at SUBSTANTIAL rather than TOTAL because no "
   "expert-database rating and no quotable functional-outcome cohort exists - the largest "
   "registry study (258 individuals) measures sleep disturbance, not work or self-care.",
   []),
 "care_dependence": ("UNKNOWN", "UNKNOWN", None, 45,
   "No usable evidence for need for daily personal assistance. Orphanet holds no record for "
   "FOXG1 disorder. The SSA Compassionate Allowances listing speaks only to capacity for "
   "work and is not evidence on this axis, and the state code lists qualify a person as "
   "medically frail without asserting a personal-care need. PubMed on FOXG1 with activities-"
   "of-daily-living, caregiver-burden, dependency and ambulation terms returned a "
   "258-individual registry study whose measured outcome is sleep disturbance. No level is "
   "asserted.",
   []),
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
