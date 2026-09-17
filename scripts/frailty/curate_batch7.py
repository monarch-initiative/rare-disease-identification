"""Apply batch 7 of the curated functional-capacity assessments (diseases 751-900).

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
# Batch 7 is dominated by adult-onset and treatable disease, and it produces the
# clearest run yet of entries where CARE DEPENDENCE outranks WORK CAPACITY -
# Kearns-Sayre and SMA type IV both have a dysphagia or transfer need on a
# background of preserved work capability.
C = {}

def capped(stage, wrat, crat, confw=76, confc=76, wlvl="SUBSTANTIAL", clvl="SUBSTANTIAL",
           ctx="STANDARD_OF_CARE_TREATED"):
    return {"work_capacity": (wlvl, ctx, stage, confw, wrat, []),
            "care_dependence": (clvl, ctx, stage, confc, crat, [])}

# --- supporting -------------------------------------------------------------
C["MONDO:0018868"] = capped("ANY",   # metachromatic leukodystrophy (unspecified form)
  "Orphanet rates paid work and professional tasks as severe permanent limitations occurring "
  "very frequently, and a state code list reaches E75.25. This is the form-unspecified MLD "
  "entry; the dataset also carries late infantile (NOT_APPLICABLE for work), juvenile (TOTAL) "
  "and adult (TOTAL). A reviewer should decide whether this parent entry should hold a level at "
  "all, or defer to its subtypes.",
  "Body care and dressing rated severe permanent limitations occurring very frequently, across "
  "the whole MLD spectrum.", 80, 82)

C["MONDO:0008830"] = capped("CONGENITAL",   # aspartylglucosaminuria
  "Orphanet rates paid work and professional tasks as complete permanent limitations occurring "
  "very frequently. Aspartylglucosaminuria causes progressive intellectual disability from "
  "childhood with adult-onset decline, and most affected people are in institutional or "
  "supported care by middle age.",
  "Held at SUBSTANTIAL despite the work rating: Orphanet rates managing one's own health as a "
  "supporting limitation but body care only as LOW severity, so the expert source describes "
  "supervision rather than hands-on personal care until late in the course.", 80, 66)

C["MONDO:0008221"] = capped("ANY",   # prolidase deficiency
  "Orphanet rates paid work and professional tasks as severe permanent limitations occurring "
  "very frequently. Chronic intractable skin ulceration, recurrent infection and splenomegaly "
  "dominate; intellectual disability occurs in a subset.",
  "Held at SUBSTANTIAL: moving around the home is rated severe but TRANSIENT - tracking ulcer "
  "flares rather than a fixed limitation - and body care only moderate. The care need is wound "
  "management, which the schema has no clean way to express.", 78, 66)

C["MONDO:0016241"] = {   # alternating hemiplegia of childhood
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 76,
   "Orphanet rates paid work as a complete permanent limitation occurring frequently, on a "
   "background of recurrent hemiplegic episodes with cumulative developmental impairment. Held "
   "at SUBSTANTIAL because the record is not expert-validated.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 74,
   "Note the temporality: Orphanet rates body care and dressing as severe but TRANSIENT. That "
   "is the disease - hemiplegic attacks lasting hours to days, with recovery between, during "
   "which a child needs complete assistance and outside which they may not. A recurring, "
   "unpredictable total care need is not the same as a continuous one, and the schema records "
   "only the level.", []),
}

C["MONDO:0008965"] = {   # CHARGE syndrome
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 72,
   "Orphanet's expert-validated rows disagree: professional tasks are rated a severe "
   "ACQUISITION DELAY occurring frequently, while paid work is rated very frequent but with "
   "severity UNSPECIFIED. CHARGE combines deafblindness with cranial nerve and structural "
   "anomalies; outcomes range from independent adulthood to profound multiple disability.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 74,
   "Eating and drinking rated severe acquisition delays occurring frequently - feeding "
   "difficulty from cranial nerve involvement is near-universal in infancy and many children "
   "need tube feeding. Recorded as a delay in acquiring the skill rather than loss of it.", []),
}

C["MONDO:0016033"] = {   # Cornelia de Lange syndrome
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 74,
   "Orphanet's own work rows disagree: paid work is rated a complete permanent limitation "
   "occurring very frequently, but professional tasks only occasionally. SSA lists Cornelia de "
   "Lange syndrome as a Compassionate Allowance. The classic phenotype carries severe "
   "intellectual disability; milder variants reach independent adulthood, which is the likely "
   "source of the internal disagreement.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 68,
   "Held below the work axis: Orphanet rates dressing and eating as complete but only "
   "OCCASIONAL, so the expert source does not describe a majority personal-care need despite "
   "the severity when present.", []),
}

# --- care dependence ABOVE work capacity ------------------------------------
# Two clean examples this batch. Both have a swallowing or transfer need on a
# background of largely preserved cognitive and occupational capability.

C["MONDO:0010787"] = {   # Kearns-Sayre syndrome
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 42,
   "Orphanet rates paid work and professional tasks as only MODERATE permanent limitations "
   "despite rating them very frequent, and a state code list reaches H49.81. Kearns-Sayre is "
   "progressive external ophthalmoplegia with pigmentary retinopathy and cardiac conduction "
   "block; ptosis and ophthalmoplegia are visually disabling but not cognitively limiting, and "
   "pacing manages the cardiac risk.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 70,
   "Set deliberately ABOVE the work axis. Orphanet rates eating and drinking as SEVERE permanent "
   "limitations occurring very frequently - bulbar weakness with dysphagia is a defining feature "
   "and a genuine aspiration risk requiring assistance at meals. Someone can hold a job and "
   "still need help eating; this dataset now contains several such diseases and the two axes "
   "being independent is what lets it say so.", []),
}

C["MONDO:0010056"] = {   # spinal muscular atrophy type IV
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 35,
   "Orphanet rates paid work and professional tasks as OCCASIONAL limitations of LOW severity - "
   "below the bar twice over. SMA type IV is the adult-onset form, with onset after 30, normal "
   "life expectancy and preserved ambulation in most patients. Compare SMA type III "
   "(MONDO:0009672, batch 3), rated `None | None | None` and curated MILD; the score ranks both "
   "high because it reads the SMA phenotype without separating types.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 64,
   "Set above the work axis. Orphanet rates transferring oneself as a SEVERE permanent "
   "limitation occurring frequently, while dressing is only moderate - proximal weakness makes "
   "rising from a chair or getting out of a bath hard long before anything else. That is a "
   "specific, real assistance need in someone who otherwise works normally.", []),
}

# --- Orphanet argues the score DOWN ----------------------------------------

C["MONDO:0008633"] = {   # Muckle-Wells syndrome
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 35,
   "Orphanet rates paid work as only a MODERATE limitation, recorded both permanently and "
   "transiently, and records no self-care rows at all. Muckle-Wells is a cryopyrin-associated "
   "periodic syndrome, and IL-1 blockade (anakinra, canakinumab) suppresses the inflammatory "
   "attacks almost completely and prevents the amyloidosis and deafness that drove the "
   "historical burden. This is a textbook case of the phenotype score reading a pre-biologic "
   "natural history.", []),
 "care_dependence": ("UNKNOWN", "UNKNOWN", None, 35,
   "Orphanet records no self-care limitation rows for Muckle-Wells syndrome, and no "
   "functional-outcome cohort was retrieved. On treatment the disease does not produce a "
   "personal-care need; untreated amyloidosis and deafness might. No level is asserted.", []),
}

C["MONDO:0012105"] = {   # granulomatosis with polyangiitis
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 38,
   "Orphanet rates paid work and professional tasks as OCCASIONAL limitations of LOW severity "
   "and explicitly TRANSIENT - below the bar on every axis at once. A state code list reaches "
   "M31.3, which is the dissenting source. Rituximab and cyclophosphamide induce remission in "
   "most patients; the modern course is relapsing-remitting with preserved function between "
   "flares rather than the rapidly fatal disease described before immunosuppression.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 35,
   "Dressing and drinking rated occasional and moderate. End-stage renal disease in a subset "
   "creates a dialysis burden, which is treatment, not personal care.", []),
}

C["MONDO:0010735"] = {   # Kennedy disease (spinal and bulbar muscular atrophy)
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 42,
   "Orphanet rates paid work and professional tasks as MODERATE permanent limitations - "
   "frequent, but explicitly moderate. Kennedy disease is very slowly progressive with a near-"
   "normal life expectancy; onset is typically in the fourth or fifth decade and many affected "
   "men work to retirement. The phenotype score groups it with the motor neurone diseases, "
   "which is where the over-reading comes from.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 40,
   "Dressing and moving around the home rated moderate. Bulbar involvement with dysphagia does "
   "eventually appear and a reviewer may want a late-stage entry, but the expert source does "
   "not describe a standing care need.", []),
}

C["MONDO:0007296"] = {   # spinocerebellar ataxia type 31
 "work_capacity": ("UNKNOWN", "UNKNOWN", None, 40,
   "Orphanet rates paid work and professional tasks as OCCASIONAL with severity UNSPECIFIED - "
   "below the bar on frequency and carrying no severity claim, so the rating cannot establish a "
   "level in either direction. SCA31 is a late-onset pure cerebellar ataxia, typically "
   "presenting after 55, so much of its course falls after working life. No functional-outcome "
   "cohort was retrieved. No level is asserted.", []),
 "care_dependence": ("UNKNOWN", "UNKNOWN", None, 40,
   "Body care and dressing are rated very frequent but with severity UNSPECIFIED, so again no "
   "severity claim is made. A frequency without a severity cannot set a level. No level is "
   "asserted.", []),
}

C["MONDO:0008815"] = {   # argininosuccinic aciduria
 "work_capacity": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 38,
   "Orphanet rates paid work as MODERATE in one row and OCCASIONAL/LOW in another - neither "
   "clears the bar. Argininosuccinic aciduria is the mildest of the classic urea cycle "
   "disorders, newborn-screened in many countries and managed with arginine supplementation "
   "plus nitrogen scavengers. Neonatal-onset disease still causes neurological damage, which is "
   "the part the phenotype score is reading.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 35,
   "Body care and dressing rated occasional and LOW, as acquisition delays. Treated patients "
   "largely manage their own care; the burden is dietary and the risk is hyperammonaemic "
   "crisis.", []),
}

C["MONDO:0010168"] = {   # Usher syndrome type 1
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 70,
   "Orphanet's expert-validated panel rates paid work as a severe permanent limitation "
   "occurring very frequently, and SSA lists Usher syndrome as a Compassionate Allowance. Type "
   "1 is the severe form - profound congenital deafness, absent vestibular function, and "
   "retinitis pigmentosa from childhood. Deafblindness is a real work barrier, though largely "
   "an accommodation and communication-access one; compare Usher type 2 (MONDO:0016484, batch "
   "6), also SUBSTANTIAL on a milder phenotype.", []),
 "care_dependence": ("MILD", "STANDARD_OF_CARE_TREATED", "ANY", 40,
   "Orphanet rates moving around the home and managing one's own health as OCCASIONAL "
   "limitations - below the bar. Even in the severe form the expert source describes "
   "adaptation, orientation training and communication support rather than personal care from "
   "another person. Third batch running in which deafblindness comes out this way.", []),
}

# --- literature -------------------------------------------------------------

SMA1_NAT = lit("PMID:29091557", "Single-Dose Gene-Replacement Therapy for Spinal Muscular Atrophy.",
    "Spinal muscular atrophy type 1 (SMA1) is a progressive, monogenic motor neuron disease with an onset during infancy that results in failure to achieve motor milestones and in death or the need for mechanical ventilation by 2 years of age.",
    "Statement of the untreated natural history of SMA type 1",
    "The untreated course: death or permanent ventilation by age 2.", strength="MODERATE")
SMA1_TX = lit("PMID:29091557", "Single-Dose Gene-Replacement Therapy for Spinal Muscular Atrophy.",
    "Of the 12 patients who had received the high dose, 11 sat unassisted, 9 rolled over, 11 fed orally and could speak, and 2 walked independently.",
    "15 infants with SMA1 given single-dose onasemnogene abeparvovec; 12 at the high dose",
    "After gene therapy, 11 of 12 sat unassisted, fed orally and could speak, and 2 walked - "
    "milestones that essentially never occurred in the untreated disease.",
    direction="DISPUTES")
SMA1_RAT = ("The most dramatic treatment effect in this dataset, and the reason both axes are "
  "VARIABLE rather than TOTAL. Untreated SMA type 1 causes death or permanent ventilation by "
  "age 2 - historical survival 8%. After single-dose gene replacement, all 15 infants were alive "
  "and event-free at 20 months, and 11 of 12 at the high dose sat unassisted, fed orally and "
  "spoke, with 2 walking independently. Whether a child with SMA1 is totally dependent or "
  "acquiring milestones now depends on newborn screening and access to therapy, not on the "
  "disease. Note the other SMA entries: type III (batch 3) and type IV (this batch) both came "
  "out MILD, so the phenotype score's single 'SMA' reading is wrong across the whole family.")
C["MONDO:0009669"] = {
 "work_capacity": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 55, SMA1_RAT,
                   [SMA1_TX, SMA1_NAT]),
 "care_dependence": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 55, SMA1_RAT,
                     [SMA1_TX, SMA1_NAT]),
}

MOCDA = lit("PMID:40132614",
    "Increased Survival in Patients With Molybdenum Cofactor Deficiency Type A Treated With Cyclic Pyranopterin Monophosphate.",
    "At 12 months, in treated patients, 43% could sit unassisted, 44% were ambulatory, and 57% could feed orally.",
    "Treated molybdenum cofactor deficiency type A cohort, 12-month outcomes",
    "Under fosdenopterin, 44% were ambulatory and 57% fed orally at 12 months - outcomes that "
    "do not occur in the untreated disease.", direction="DISPUTES")
C["MONDO:0009643"] = {
 "work_capacity": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 55,
   "Type A is the treatable one, and that is the whole point of separating it. Fosdenopterin "
   "(cyclic pyranopterin monophosphate) replaces the missing intermediate: at 12 months 44% of "
   "treated patients were ambulatory and 57% fed orally. Compare MoCD type B "
   "(MONDO:0009644, batch 3), curated NOT_APPLICABLE on a median age at death of 2.2 years - "
   "no such therapy exists for type B. Two subtypes of the same enzyme deficiency, opposite "
   "prognoses, and the phenotype score sees one disease.",
   [MOCDA]),
 "care_dependence": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 55,
   "Same split. Under treatment 43% sit unassisted and 57% feed orally; untreated neonatal-onset "
   "type A is a rapidly fatal encephalopathy. Recorded as VARIABLE rather than averaged.",
   [MOCDA]),
}

USH1_WORK = lit("PMID:29865098",
    "Health, work, social trust, and financial situation in persons with Usher syndrome type 1.",
    "Sixty-six persons (18-65 y) from the Swedish Usher database received a questionnaire and 47 were included, 23 working and 24 non-working.",
    "47 respondents aged 18-65 from the Swedish Usher database",
    "Roughly half of working-age respondents with Usher type 1 were in work - the second "
    "measured employment figure in this dataset.", strength="MODERATE")
C["MONDO:0010168"]["work_capacity"] = ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 78,
   "Now carried by a measured employment figure rather than an expert rating alone: of 47 "
   "working-age respondents in the Swedish Usher database, 23 were working and 24 were not - "
   "roughly half. That is a serious barrier and squarely SUBSTANTIAL, not TOTAL. Orphanet's "
   "expert-validated panel agrees on severity, and SSA lists the disease. The study's own "
   "conclusion is worth carrying into any policy use: having employment counteracted the health "
   "and financial risks associated with the disability.",
   [USH1_WORK])

RASM = lit("PMID:32679562", "Epilepsy surgery for Rasmussen encephalitis: the UCLA experience.",
    "Following surgery, 68% of the patients could ambulate and 84% could speak regardless of operative intervention.",
    "Rasmussen encephalitis surgical series, UCLA",
    "After hemispherectomy, 68% ambulate and 84% speak - so the operation that stops the "
    "seizures leaves most patients mobile and verbal.", strength="MODERATE")
C["MONDO:0016019"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 70,
   "Rasmussen encephalitis destroys one hemisphere and is treated by disconnecting it, which "
   "necessarily leaves a hemiparesis and a hemianopia. Even so, 68% ambulate and 84% speak "
   "after surgery. The outcome is a fixed, substantial disability rather than a progressive or "
   "total one, which is why this is SUBSTANTIAL. Orphanet holds no record for this disease.",
   [RASM]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PAEDIATRIC", 66,
   "Most patients ambulate and speak after surgery, so this is help with specific tasks - "
   "dressing, fine motor work on the affected side - rather than total dependence. Recorded "
   "as SUBSTANTIAL on that basis.",
   [RASM]),
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
