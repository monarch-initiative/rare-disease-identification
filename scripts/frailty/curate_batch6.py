"""Apply batch 6 of the curated functional-capacity assessments (diseases 601-750).

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
# Batch 6 introduces a temporality pattern the earlier batches did not contain:
# RELAPSING-REMITTING autoimmune disease, where Orphanet rates the limitation
# COMPLETE but TRANSIENT. Dermatomyositis, polymyositis and Landau-Kleffner all
# take this shape. It is a third distinct mechanism for arguing a level down,
# alongside treated-metabolic disease and episodic vascular disease.
C = {}

def capped(stage, wrat, crat, confw=76, confc=76, wlvl="SUBSTANTIAL", clvl="SUBSTANTIAL",
           ctx="STANDARD_OF_CARE_TREATED"):
    return {"work_capacity": (wlvl, ctx, stage, confw, wrat, []),
            "care_dependence": (clvl, ctx, stage, confc, crat, [])}

# --- expert-validated, supporting: TOTAL ------------------------------------
C["MONDO:0018937"] = capped("PAEDIATRIC",   # mucopolysaccharidosis type 3 (Sanfilippo)
  "Orphanet's expert-validated panel rates paid work as a complete, permanent limitation "
  "occurring very frequently. Sanfilippo syndrome causes progressive dementia from early "
  "childhood with loss of acquired skills; enzyme replacement does not cross the blood-brain "
  "barrier, so the neurological course is unaltered by current treatment.",
  "Body care and dressing rated severe permanent limitations occurring very frequently, on a "
  "course of relentless cognitive and motor regression.", 91, 92, "TOTAL", "TOTAL")

C["MONDO:0016621"] = capped("PAEDIATRIC",   # juvenile Huntington disease
  "Orphanet's expert-validated panel rates paid work and professional tasks as complete "
  "permanent limitations occurring very frequently. Note the deliberate contrast with adult "
  "Huntington disease (MONDO:0007739, batch 4): the juvenile form is Westphal-variant, rigid "
  "rather than choreic, faster, and manifests in childhood - so it carries no pre-manifest "
  "exclusion, because affected children are symptomatic before working age.",
  "Body care and dressing rated complete permanent limitations occurring frequently, with "
  "progression to full dependence over a decade or less.", 90, 90, "TOTAL", "TOTAL")

C["MONDO:0017730"] = capped("ADULT_ONSET",   # metachromatic leukodystrophy, adult form
  "Orphanet's expert-validated panel rates paid work and professional tasks as severe permanent "
  "limitations occurring very frequently. The adult form typically presents with psychiatric or "
  "behavioural change and cognitive decline in the third or fourth decade - squarely within "
  "working life. Contrast the juvenile form (MONDO:0009591, batch 3), rated complete.",
  "Body care and dressing rated severe permanent limitations occurring very frequently, on a "
  "course of progressive demyelination ending in total dependence.", 86, 87, "TOTAL", "TOTAL")

C["MONDO:0011652"] = capped("CONGENITAL",   # Phelan-McDermid syndrome
  "Orphanet's expert-validated panel rates paid work as a complete permanent limitation "
  "occurring very frequently, and SSA lists Phelan-McDermid syndrome as a Compassionate "
  "Allowance. Absent or severely delayed speech with moderate to profound intellectual "
  "disability is near-universal.",
  "Managing one's own health and body care rated severe permanent limitations occurring "
  "frequently to very frequently.", 88, 87, "TOTAL", "TOTAL")

C["MONDO:0008365"] = capped("CONGENITAL",   # recombinant 8 syndrome
  "Orphanet rates paid work and professional tasks as severe permanent limitations occurring "
  "very frequently. Recombinant 8 syndrome combines intellectual disability with congenital "
  "heart disease and a characteristic facial appearance.",
  "Body care and dressing rated severe permanent limitations occurring very frequently.")

C["MONDO:0010590"] = capped("CONGENITAL",   # FG syndrome 1
  "Orphanet rates paid work and professional tasks as severe permanent limitations occurring "
  "very frequently, on a background of intellectual disability with hypotonia and constipation.",
  "Held at SUBSTANTIAL: moving around the home is rated a severe acquisition delay, but body "
  "care only as moderate - so the picture is delayed independence rather than permanent "
  "hands-on care.", 78, 68)

C["MONDO:0016002"] = capped("ANY",   # Ehlers-Danlos, kyphoscoliotic type 1
  "Orphanet rates paid work and professional tasks as severe permanent limitations occurring "
  "frequently. The kyphoscoliotic type is among the more severe EDS forms, with congenital "
  "muscle hypotonia, progressive scoliosis and vascular fragility.",
  "Dressing rated a severe permanent limitation occurring very frequently, and continence "
  "rated severe and frequent - the autonomic and connective-tissue involvement adds a care need "
  "beyond the musculoskeletal one.", 78, 78)

C["MONDO:0009613"] = capped("CONGENITAL",   # methylmalonic aciduria, cblA type
  "Orphanet rates professional tasks as a complete limitation, recorded both permanently "
  "(frequent) and transiently (very frequent). Worth reading alongside the other two "
  "methylmalonic acidurias in this dataset: cblB (MONDO:0009614, batch 5) came out MILD as a "
  "B12-responsive form, and mut deficiency (MONDO:0009612, batch 4) came out VARIABLE on a "
  "cohort where 37% died. cblA is B12-responsive too but sits higher here on Orphanet's "
  "reading; the three entries together show how much subtype granularity the score cannot see.",
  "Dressing rated a severe permanent limitation and drinking a severe acquisition delay, both "
  "frequent. The lifelong dietary and emergency-regimen burden dominates.", 70, 72)

# --- relapsing-remitting: COMPLETE but TRANSIENT ----------------------------
# A new shape. Orphanet rates the limitation as complete during a flare and
# explicitly transient between them. Severity alone would read TOTAL; temporality
# says otherwise, and for these diseases temporality is the whole clinical story.

C["MONDO:0016367"] = {   # dermatomyositis
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 62,
   "Orphanet rates paid work as a COMPLETE but TRANSIENT limitation occurring frequently. That "
   "temporality is the whole point: dermatomyositis relapses and remits, and corticosteroids "
   "with steroid-sparing agents induce remission in most patients. During a flare the limitation "
   "is total; between flares many people work normally. SUBSTANTIAL captures the recurring "
   "interruption without asserting a standing incapacity. A state code list reaches M33.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "Orphanet rates eating and drinking as only OCCASIONAL and transient limitations - "
   "dysphagia occurs in a minority and responds to treatment. Set well below the work axis "
   "deliberately: this disease interrupts work far more than it creates a personal-care need.",
   []),
}

C["MONDO:0019127"] = {   # polymyositis
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 62,
   "Same shape as dermatomyositis: Orphanet rates paid work as COMPLETE but TRANSIENT, "
   "frequent. Proximal weakness responds to immunosuppression in most patients, so the "
   "limitation is episodic rather than fixed. A state code list reaches M33.2.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 40,
   "Eating and drinking rated occasional and transient. The care need arrives only in "
   "treatment-refractory disease with established dysphagia, which is a minority.", []),
}

C["MONDO:0009509"] = {   # Landau-Kleffner syndrome
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 58,
   "Orphanet rates paid work and professional tasks as COMPLETE but TRANSIENT limitations "
   "occurring very frequently. Landau-Kleffner is an acquired epileptic aphasia of childhood; "
   "seizures and the EEG abnormality usually remit by adolescence, but language recovery is "
   "incomplete in many. So the disease-stage limitation is total and the adult outcome is "
   "variable - which is why this is SUBSTANTIAL and not TOTAL. Orphanet records no self-care "
   "rows at all, which fits: the deficit is linguistic, not motor.", []),
 "care_dependence": ("UNKNOWN", "UNKNOWN", None, 40,
   "Orphanet holds no self-care rows for Landau-Kleffner syndrome, and no functional-outcome "
   "cohort was retrieved. The deficit is language regression rather than motor or self-care "
   "impairment, so a care-dependence claim would not follow from the phenotype anyway. No "
   "level is asserted.", []),
}

# --- Orphanet argues the score DOWN ----------------------------------------

C["MONDO:0016239"] = {   # cystinosis
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 42,
   "Orphanet's expert-validated panel records paid work twice and neither row clears the bar: "
   "complete but only OCCASIONAL, and frequent but only MODERATE. Cystinosis is treated with "
   "cysteamine from diagnosis, which delays renal failure and preserves growth; treated patients "
   "commonly reach adulthood, receive transplants and work. The phenotype score reads the "
   "untreated course, in which children died in the first decade.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "Managing one's own health is rated as a disputing row. The burden in cystinosis is an "
   "exacting medication schedule plus renal replacement - a treatment burden carried by the "
   "patient, not personal care delivered by someone else.", []),
}

C["MONDO:0010703"] = {   # ornithine carbamoyltransferase deficiency
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "Orphanet rates paid work and professional tasks as only MODERATE permanent limitations, and "
   "body care and dressing as occasional. SSA lists OTC deficiency as a Compassionate Allowance, "
   "which is the dissenting source. The split makes sense: neonatal-onset OTC deficiency in boys "
   "is catastrophic, while late-onset and heterozygous female disease is managed with diet and "
   "nitrogen scavengers and is compatible with normal work. A reviewer should consider splitting "
   "this entry by onset.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 38,
   "Body care and dressing rated occasional and moderate. The risk is acute hyperammonaemic "
   "crisis, which is an emergency-response and dietary-supervision need rather than a daily "
   "personal-care one.", []),
}

C["MONDO:0010788"] = {   # Leber hereditary optic neuropathy
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 40,
   "Orphanet's expert-validated panel rates paid work and professional tasks as MODERATE "
   "permanent limitations despite the sight loss being bilateral, subacute and usually severe. "
   "This is the same shape as retinitis pigmentosa in batch 4: the expert source treats visual "
   "impairment as an accommodation problem rather than an incapacity. Spontaneous partial "
   "recovery also occurs, particularly with the m.14484T>C variant.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 35,
   "Orphanet records managing one's own health as a disputing row and no other self-care "
   "limitation. LHON affects vision alone - there is no motor or cognitive component to create "
   "a personal-care need.", []),
}

C["MONDO:0016484"] = {   # Usher syndrome type 2
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 66,
   "Orphanet's expert-validated panel rates paid work and professional tasks as severe "
   "permanent limitations occurring frequently. Type 2 is the moderate form - congenital "
   "hearing loss with later-onset retinitis pigmentosa and no vestibular dysfunction - so "
   "most affected people have full mobility and use hearing aids successfully. Dual sensory "
   "loss is a genuine work barrier, but again largely an accommodation one.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 38,
   "Orphanet records managing one's own health as a disputing row and moving around the home as "
   "only moderate. Deafblindness creates a profound communication and orientation need without "
   "necessarily creating a personal-care one, and the schema currently cannot express that "
   "distinction.", []),
}

C["MONDO:0005100"] = {   # systemic sclerosis
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 68,
   "Orphanet rates paid work as a severe limitation occurring frequently, recorded both "
   "permanently and transiently, and a state code list reaches M34. Systemic sclerosis is "
   "heterogeneous - limited cutaneous disease is compatible with work for decades, while "
   "diffuse disease with interstitial lung involvement or renal crisis is not.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 42,
   "Orphanet rates moving around the home as only an occasional, moderate limitation, recorded "
   "permanently and transiently. Hand contractures and Raynaud phenomenon impair fine tasks "
   "long before mobility or personal care are affected.", []),
}

C["MONDO:0100339"] = {   # Friedreich ataxia
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 70,
   "The two axes disagree in an unusual direction here. Orphanet rates paid work and "
   "professional tasks with severity UNSPECIFIED - carrying no severity claim - while rating "
   "body care and dressing as severe and very frequent. A state code list reaches G11.11 and "
   "SSA lists Friedreich ataxia as a Compassionate Allowance. Held at SUBSTANTIAL because the "
   "work rows cannot establish a level on their own, even though the policy sources and the "
   "care ratings both point higher.", []),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "ANY", 80,
   "Body care and dressing rated severe permanent limitations occurring very frequently. Most "
   "people with Friedreich ataxia lose ambulation within 10-15 years of onset, typically in "
   "their twenties, and cardiomyopathy and diabetes add to the burden. This is one of the few "
   "entries where care dependence is rated above work capacity, and the evidence supports it.",
   []),
}

# --- literature -------------------------------------------------------------

EDMD = lit("PMID:24839233",
    "Professional activity of Emery-Dreifuss muscular dystrophy patients in Poland.",
    "54% of the study participants were employed, and 90% of them had job position corresponding to their education.",
    "Emery-Dreifuss muscular dystrophy patients surveyed in Poland",
    "A measured EMPLOYMENT RATE - the top-preference evidence type for this axis and the only "
    "one in the dataset so far. 54% employed, and of those, 90% in work matching their education.")
C["MONDO:0100531"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 78,
   "The rarest kind of evidence this pipeline can find: an actual employment rate. 54% of "
   "surveyed patients were employed, and 90% of those held positions matching their education - "
   "so employment is reduced relative to the general population but far from precluded, and the "
   "work people do is skilled. Only 23% of the employed were in sheltered workplaces. This is a "
   "clear SUBSTANTIAL: a serious barrier, not an incapacity. Orphanet holds no functional rows "
   "for this disease, so the literature carries it alone.",
   [EDMD]),
 "care_dependence": ("UNKNOWN", "UNKNOWN", None, 45,
   "The employment survey does not measure personal care, Orphanet holds no record, and no ADL "
   "or dependency figure was retrieved. Emery-Dreifuss causes early contractures and cardiac "
   "conduction disease; the cardiac risk is the dominant clinical concern and is not a "
   "personal-care need. No level is asserted.", []),
}

FRDA = lit("PMID:31938785", "Predictors of loss of ambulation in Friedreich's ataxia.",
    "Early onset FRDA patients (<15y of age) typically become fully wheelchair dependent at a median of 11.5y (25th, 75th percentiles 8.6y, 16.2y) after the onset of first symptoms.",
    "Friedreich ataxia cohort, stratified by age at onset",
    "Median 11.5 years from onset to full wheelchair dependence in early-onset disease - so "
    "someone with onset at 10 is wheelchair-dependent by their early twenties.")
C["MONDO:0100339"]["care_dependence"] = ("TOTAL", "STANDARD_OF_CARE_TREATED", "ANY", 86,
   "Two sources agree. Orphanet rates body care and dressing as severe permanent limitations "
   "occurring very frequently, and the literature puts full wheelchair dependence at a median "
   "11.5 years from onset in early-onset disease - so a person with onset at 10 is "
   "wheelchair-dependent by their early twenties. Cardiomyopathy and diabetes add further "
   "burden. This remains one of the few entries where care dependence is rated above work "
   "capacity, and the added literature line strengthens rather than changes that.",
   [FRDA])

MLD_LI = lit("PMID:31036045",
    "Insights into the natural history of metachromatic leukodystrophy from interviews with caregivers.",
    "The most common initial symptoms in this group related to problems with gross motor function (12/16 patients); 11 patients never learned to walk independently.",
    "16 late-infantile metachromatic leukodystrophy cases, caregiver interviews",
    "11 of 16 never walked independently - failure to acquire the skill rather than loss of it.")
C["MONDO:0017729"] = {
 "work_capacity": ("NOT_APPLICABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 86,
   "11 of 16 children in the late-infantile group never learned to walk independently, on a "
   "course of rapid regression with death usually in early childhood. Work capacity does not "
   "arise; recorded as NOT_APPLICABLE rather than TOTAL so it is not read as a statement about "
   "working-age adults. Note the contrast with the juvenile form (MONDO:0009591, batch 3) and "
   "the adult form (MONDO:0017730, this batch), both curated TOTAL - the three MLD entries "
   "differ by onset, and the phenotype score cannot see that.",
   [MLD_LI]),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 90,
   "Most affected children never walk independently and regress rapidly from an already limited "
   "baseline, so feeding, transfers and all personal care fall to a carer from early childhood.",
   [MLD_LI]),
}

KMT2B = lit("PMID:31768667", "Update on KMT2B-Related Dystonia.",
    "Sustained response to deep brain stimulation (DBS), including restoration of independent ambulation, is seen in 93% (27/29) of patients.",
    "29 patients with KMT2B-related dystonia treated with deep brain stimulation",
    "Deep brain stimulation restores independent ambulation in 93% - a treatment effect large "
    "enough that an untreated-course assessment would misstate the current expectation.",
    direction="DISPUTES")
C["MONDO:0015003"] = {
 "work_capacity": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 55,
   "Recorded as VARIABLE because treatment splits the outcome sharply. Untreated KMT2B-related "
   "dystonia is a progressive generalised dystonia beginning in childhood with loss of "
   "ambulation and speech. With deep brain stimulation, 93% of 29 patients show a sustained "
   "response including restoration of independent ambulation. Whether a given person is "
   "severely limited depends on whether they were diagnosed and implanted - which is a "
   "healthcare-access question, not a disease-severity one.",
   [KMT2B]),
 "care_dependence": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 55,
   "Same split. Restoration of independent ambulation in 93% of implanted patients removes the "
   "transfer and mobility care need that the untreated course creates. Recorded as VARIABLE "
   "rather than averaged.",
   [KMT2B]),
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
