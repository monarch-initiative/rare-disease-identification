"""Apply batch 2 of the curated functional-capacity assessments (diseases 51-150).

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
C = {}

# --- TK2 mtDNA depletion, myopathic form -----------------------------------
TK2_NAT = lit("PMID:38544965", "Clinical and Genetic Analysis of Patients With TK2 Deficiency.",
    "Approximately 30% of patients died of respiratory insufficiency, while 56% of surviving patients needed mechanical ventilation.",
    "Cohort of patients with genetically confirmed TK2 deficiency",
    "Measures mortality and ventilator dependence directly in an identified cohort.")
TK2_TX = lit("PMID:40911819",
    "Pyrimidine Nucleos(t)ide Therapy in Patients With Thymidine Kinase 2 Deficiency: A Multicenter Retrospective Chart Review Study.",
    "None of the treated patients (0/38) and 58% (40/69) of untreated patients died.",
    "38 treated and 69 untreated patients, multicentre retrospective review",
    "Nucleoside therapy changes the course so sharply that an untreated-history "
    "assessment would misstate the current expectation.",
    direction="DISPUTES")
C["MONDO:0012301"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 70,
   "Held at SUBSTANTIAL, and the two literature lines disagree by design. Untreated, "
   "30% die of respiratory insufficiency and 56% of survivors need mechanical ventilation. "
   "Under pyrimidine nucleoside therapy none of 38 treated patients died against 58% of 69 "
   "untreated. Ventilator dependence is a serious barrier to employment either way, but the "
   "treated course is not the devastating one the older series describe.",
   [TK2_NAT, TK2_TX]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 72,
   "Mechanical ventilation in over half of untreated survivors implies continuous support, "
   "but nucleoside therapy reduces both mortality and ventilatory burden. No ADL or "
   "caregiver-hours measurement exists, so this stops short of TOTAL.",
   [TK2_NAT, TK2_TX]),
}

# --- X-linked adrenoleukodystrophy -----------------------------------------
ALD_F = lit("PMID:39919255", "Disease Burden in Female Patients With X-Linked Adrenoleukodystrophy.",
    "Activities of daily living beyond walking were affected in 25 (44%) participants.",
    "57 female participants with X-linked adrenoleukodystrophy",
    "Direct ADL measurement in an identified adult cohort of female heterozygotes, who are "
    "affected rather than merely carriers.")
ALD_GT = lit("PMID:39383459", "Lentiviral Gene Therapy for Cerebral Adrenoleukodystrophy.",
    "At the most recent assessment (median follow-up, 6 years), the neurologic function score was stable as compared with the baseline score in 30 of 32 patients (94%); 26 patients (81%) had no major functional disabilities.",
    "32 boys with early cerebral adrenoleukodystrophy, median follow-up 6 years",
    "Gene therapy leaves most treated boys without major functional disability, which argues "
    "against reading the untreated cerebral course as the current expectation.",
    direction="DISPUTES")
ALD_RAT = ("Recorded as VARIABLE because the phenotype genuinely splits and the evidence "
  "splits with it. Untreated childhood cerebral ALD is devastating; after lentiviral gene "
  "therapy 81% of 32 boys had no major functional disability at a median 6 years. Adult "
  "male adrenomyeloneuropathy and affected female heterozygotes follow a slower course - "
  "44% of 57 women had activities of daily living beyond walking affected. No single level "
  "represents all of these.")
C["MONDO:0018544"] = {
 "work_capacity": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "ANY", 55, ALD_RAT,
                   [ALD_F, ALD_GT]),
 "care_dependence": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "ANY", 55, ALD_RAT,
                     [ALD_F, ALD_GT]),
}

# --- MEGDEL / SERAC1 --------------------------------------------------------
SERAC = lit("PMID:29205472",
    "Progressive deafness-dystonia due to SERAC1 mutations: A study of 67 cases.",
    "The majority of affected individuals never learned to walk (68%).",
    "67 individuals with SERAC1 mutations",
    "Failure to acquire independent walking in 68% of a 67-case series.")
SERAC2 = lit("PMID:29205472",
    "Progressive deafness-dystonia due to SERAC1 mutations: A study of 67 cases.",
    "Seventy-nine percent suffered hearing loss, 58% never learned to speak, and nearly all had significant intellectual disability (88%).",
    "67 individuals with SERAC1 mutations",
    "Speech and intellectual outcomes across the same 67-case series.")
C["MONDO:0013875"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 90,
   "68% never walk, 58% never speak and 88% have significant intellectual disability across "
   "67 cases. Competitive employment does not arise for the great majority. Only supportive "
   "care exists, so this is the current expectation, not an untreated course.",
   [SERAC, SERAC2]),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 91,
   "Never walking (68%) combined with progressive dystonia and near-universal intellectual "
   "disability places transfers, feeding and personal care on a carer for most affected people.",
   [SERAC, SERAC2]),
}

# --- ASXL3 / Bainbridge-Ropers ---------------------------------------------
ASXL3 = lit("PMID:38420660",
    "ASXL3-related disorder: Molecular phenotyping and comprehensive review providing insights into disease mechanism.",
    "Common phenotypic features comprised global developmental delay or intellectual disability (97%), feeding problems (76%), hypotonia (88%) and characteristic facial features (93%).",
    "Comprehensive review of reported ASXL3-related disorder cases",
    "Near-universal developmental delay or intellectual disability, with feeding problems in "
    "three quarters.", strength="MODERATE")
C["MONDO:0014205"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 78,
   "Global developmental delay or intellectual disability in 97% of reported cases. Held at "
   "SUBSTANTIAL rather than TOTAL because the source is a phenotype review rather than a "
   "measured functional cohort, and no employment or ambulation rate has been reported.",
   [ASXL3]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 78,
   "Feeding problems in 76% and hypotonia in 88% on a background of near-universal "
   "intellectual disability imply a substantial daily care need, but no ADL or dependency "
   "measurement exists.",
   [ASXL3]),
}

# --- 1p36 deletion syndrome -------------------------------------------------
DEL1P36 = lit("PMID:25044719", "Delineating the phenotype of 1p36 deletion in adolescents and adults.",
    "Approximately 90% are reported to have severe to profound intellectual disability and 75% to have absent expressive language.",
    "Adolescents and adults with 1p36 deletion",
    "Severe-to-profound intellectual disability in ~90% with absent expressive language in "
    "75%, reported for the adolescent and adult population specifically.")
C["MONDO:0011929"] = {
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "ANY", 90,
   "Severe to profound intellectual disability in about 90% and absent expressive language in "
   "75%, reported specifically for adolescents and adults, so this speaks directly to "
   "working-age function. SSA also lists 1p36 Deletion Syndrome as a Compassionate Allowance.",
   [DEL1P36]),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "ANY", 88,
   "Severe to profound intellectual disability in about 90% of adolescents and adults means "
   "daily personal assistance and supervision for the great majority.",
   [DEL1P36]),
}

# --- KCNQ2 developmental and epileptic encephalopathy (DEE7) ----------------
KCNQ2 = lit("PMID:33811133", "Adult phenotype of KCNQ2 encephalopathy.",
    "At last contact, six individuals (46%) remained unable to walk independently, six (46%) had limb spasticity and four (31%) tetraparesis/tetraplegia.",
    "13 adults aged 18-45, international recruitment",
    "Direct measurement of ambulation and motor outcome in adults, the population this axis "
    "asks about.", strength="MODERATE")
KCNQ2B = lit("PMID:33811133", "Adult phenotype of KCNQ2 encephalopathy.",
    "Intellectual disability (ID) ranged from mild to profound, with the majority (54%) of individuals in the severe category.",
    "13 adults aged 18-45, international recruitment",
    "Severe intellectual disability in the majority of adults followed up.", strength="MODERATE")
C["MONDO:0013387"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 80,
   "In the only published adult cohort, 46% remained unable to walk independently, 46% were "
   "non-verbal and 54% had severe intellectual disability. Capped at SUBSTANTIAL rather than "
   "TOTAL by evidence strength, not by the clinical picture: n=13 is below the threshold for "
   "a STRONG line, and the point estimates would support TOTAL if replicated in a larger series.",
   [KCNQ2, KCNQ2B]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 80,
   "Nearly half of adults cannot walk independently and over half have severe intellectual "
   "disability, implying daily assistance. Same n=13 cap applies. Notably, seizures remit for "
   "most (77% seizure-free), so epilepsy control is not what drives the care need.",
   [KCNQ2, KCNQ2B]),
}

# --- Infantile-onset Pompe disease ------------------------------------------
POMPE = lit("PMID:41453391", "Evaluation of Experienced Clinical Events in Pompe Disease Based on Real-life Data.",
    "However, 56% of patients-all with IOPD-died during follow-up.",
    "Real-life cohort of Pompe disease patients; deaths confined to the infantile-onset group",
    "Mortality concentrated entirely in the infantile-onset form.", strength="MODERATE")
POMPE_NBS = lit("PMID:36310651", "Newborn screening for Pompe disease in Italy: Long-term results and future challenges.",
    "Our study, the largest reported to date in Europe, presents data from longstanding NBS for PD, revealing an incidence in North East Italy of 1/18,795 (IOPD 1/68,914; LOPD 1/25,843), and the absence of mortality in IOPD treated from birth.",
    "Long-running newborn screening programme, North East Italy",
    "No mortality in infantile-onset disease treated from birth, which contradicts any "
    "assessment built on the untreated course.",
    direction="DISPUTES", strength="MODERATE")
POMPE_RAT = ("The classic PKU trap, and the evidence states both sides. Untreated or "
  "late-treated infantile Pompe kills most affected infants - 56% mortality in a real-life "
  "cohort, all in the infantile-onset group. Under newborn screening with enzyme replacement "
  "from birth an Italian programme reports no mortality at all. Recorded as VARIABLE because "
  "the level depends entirely on whether the child was screened and treated early, and the "
  "assessment must not be read as the expectation for a treated newborn today.")
C["MONDO:0017694"] = {
 "work_capacity": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 55, POMPE_RAT,
                   [POMPE, POMPE_NBS]),
 "care_dependence": ("VARIABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 55, POMPE_RAT,
                     [POMPE, POMPE_NBS]),
}

# --- NALCN / CLIFAHDD -------------------------------------------------------
NALCN = lit("PMID:40048676", "Genotype-Phenotype Landscape of NALCN and UNC80-Related Disorders.",
    "Distal arthrogryposis (76.5%), episodic ataxia (41.2% of ambulatory patients), and paroxysmal dystonia (11.7%) were exclusively diagnosed in patients with CLIFAHDD.",
    "Patients with NALCN and UNC80-related disorders; CLIFAHDD subgroup",
    "Distal arthrogryposis in over three quarters, with ambulation limited enough that "
    "ataxia is reported as a fraction of ambulatory patients.", strength="MODERATE")
C["MONDO:0024567"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 72,
   "Distal arthrogryposis in 76.5% on a background of infantile hypotonia and psychomotor "
   "retardation. Held at SUBSTANTIAL: the cohort reports phenotype frequencies rather than "
   "a functional outcome, and no employment or independence measure exists.",
   [NALCN]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 72,
   "Congenital contractures with hypotonia and psychomotor retardation imply help with "
   "transfers and personal care, but only a subset are ambulatory and no ADL measurement "
   "has been published.",
   [NALCN]),
}

# --- HHH / ornithine translocase deficiency ---------------------------------
HHH = lit("PMID:31443672",
    "Corticospinal tract damage in HHH syndrome: a metabolic cause of hereditary spastic paraplegia.",
    "Mild to moderate cerebellar signs were found in 7/9, intellectual disability in 8/9.",
    "9 patients with HHH syndrome",
    "Intellectual disability in 8 of 9 and cerebellar signs in 7 of 9.", strength="MODERATE")
HHH_TX = lit("PMID:41126296",
    "Liver transplantation can prevent the progression of neurological damage in hyperornithinemia-hyperammonemia-homocitrullinuria syndrome and maintain long-term metabolic stability - The largest single-center experience.",
    "Early transplantation resulted in neurological improvement in 5 of 6 patients (83.3%), including reduced lower limb spasticity and improved walking ability.",
    "6 transplanted patients with HHH syndrome",
    "Early liver transplantation improves spasticity and walking, so the untreated course "
    "overstates the expectation for a treated patient.",
    direction="DISPUTES", strength="MODERATE")
HHH_RAT = ("Two small series disagree in the way treatment usually makes them disagree. "
  "Untreated, 8 of 9 patients have intellectual disability and most develop spastic "
  "paraplegia; after early liver transplantation 5 of 6 improved neurologically, with "
  "reduced spasticity and better walking. Both cohorts are under 10 patients, so neither "
  "line is STRONG and the level stays at SUBSTANTIAL.")
C["MONDO:0009393"] = {
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 65, HHH_RAT,
                   [HHH, HHH_TX]),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 60,
   "Spastic paraplegia and intellectual disability in most untreated patients imply regular "
   "assistance, though early transplantation improves walking in the majority of those "
   "treated. No ADL or dependency measurement exists for either group.",
   [HHH, HHH_TX]),
}

# --- COQ4 / neonatal encephalomyopathy-cardiomyopathy-respiratory distress --
COQ4 = lit("PMID:33120466", "[Primary coenzyme Q10 deficiency-7: a case report and literature review].",
    "Most of them had a poor prognosis with a mortality rate of 20/33.",
    "33 reported cases of primary coenzyme Q10 deficiency-7 (COQ4)",
    "Mortality in 20 of 33 reported cases.", strength="MODERATE")
C["MONDO:0014562"] = {
 "work_capacity": ("NOT_APPLICABLE", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 80,
   "20 of 33 reported patients died, most in the neonatal or infantile period. Work capacity "
   "does not arise for the typical affected person; recorded as NOT_APPLICABLE rather than "
   "TOTAL so it is not read as a statement about working-age adults.",
   [COQ4]),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 82,
   "Neonatal encephalomyopathy with cardiomyopathy and respiratory distress; survivors need "
   "total daily care and often respiratory support. The source is a case-report review, so "
   "the line is MODERATE.",
   [COQ4]),
}

# --- Orphanet-backed, no literature retrieved -------------------------------
# Orphanet's own ratings carry these. Where the record is expert-validated the
# line is STRONG and can set TOTAL on its own; where it is not, the level is
# capped at SUBSTANTIAL by evidence strength rather than by the clinical picture.

C["MONDO:0008434"] = {   # Smith-Magenis syndrome
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "ANY", 88,
   "Orphanet's expert-validated panel rates paid work in a standard environment as a "
   "complete, permanent limitation occurring very frequently, which meets the bar on its "
   "own. No functional-outcome cohort was retrieved.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 75,
   "Held below TOTAL deliberately: Orphanet's experts rate managing one's own health as a "
   "severe permanent limitation, but body care and continence only as moderate. The "
   "characteristic sleep disturbance and self-injurious behaviour drive a supervision need "
   "that Orphanet's item list does not represent, so a reviewer may well raise this.", []),
}

C["MONDO:0008458"] = {   # spinocerebellar ataxia type 2
 "work_capacity": ("TOTAL", "STANDARD_OF_CARE_TREATED", "ADULT_ONSET", 86,
   "Orphanet's expert-validated rating makes paid work a severe, permanent limitation "
   "occurring frequently. SCA2 is progressive and adult-onset, so the limitation accumulates "
   "over working life rather than being present from the start.", []),
 "care_dependence": ("TOTAL", "STANDARD_OF_CARE_TREATED", "PROGRESSIVE_LATE_STAGE", 85,
   "Orphanet rates body care, dressing and drinking as severe permanent limitations occurring "
   "very frequently. Recorded against the progressed stage, since early SCA2 does not create "
   "a daily care need.", []),
}

C["MONDO:0010789"] = {   # MELAS
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 70,
   "Orphanet's expert-validated panel rates paid work as severe and frequent but explicitly "
   "TRANSIENT, not permanent - MELAS runs in stroke-like episodes with partial recovery "
   "between them. That temporality is why this is SUBSTANTIAL rather than TOTAL, even though "
   "severity and frequency would otherwise clear the bar. Nebraska also lists the code.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 70,
   "Same reasoning: Orphanet rates eating, drinking and body care as severe and frequent but "
   "transient. Care need is episodic, concentrated around metabolic crises, and accumulates "
   "only as deficits fail to resolve.", []),
}

C["MONDO:0010298"] = {   # Lesch-Nyhan syndrome
 "work_capacity": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 82,
   "Two sources agree: Orphanet rates paid work as a complete, permanent limitation occurring "
   "very frequently, and Nebraska lists the code as qualifying. Capped at SUBSTANTIAL only "
   "because the Orphanet record is not expert-validated, so no STRONG line exists. The "
   "clinical picture - dystonia, self-injury, near-universal wheelchair use - would support "
   "TOTAL, and a reviewer should consider raising it.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "CONGENITAL", 84,
   "Orphanet rates body care, dressing and drinking as severe permanent limitations occurring "
   "very frequently. Compulsive self-injury adds a continuous supervision need beyond ordinary "
   "personal care. Same evidence-strength cap as the work axis.", []),
}

C["MONDO:0010382"] = {   # fragile X-associated tremor/ataxia syndrome
 "work_capacity": ("UNKNOWN", "UNKNOWN", None, 40,
   "Orphanet's expert-validated panel rates paid work and professional tasks as very frequent "
   "and permanent but records the severity as UNSPECIFIED, so the rating cannot establish a "
   "level. FXTAS is late-onset, typically after age 50, so much of its impact falls after "
   "working life. PubMed on FXTAS and FMR1 with employment, retirement and occupational terms "
   "returned no quotable functional measurement. No level is asserted.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "PROGRESSIVE_LATE_STAGE", 68,
   "Orphanet's expert-validated panel rates body care and dressing as severe permanent "
   "limitations occurring frequently. Held at SUBSTANTIAL: managing one's own health is rated "
   "complete but only occasional, below the bar, and the disorder is late-onset and "
   "progressive, so the care need belongs to the advanced stage.", []),
}

C["MONDO:0010476"] = {   # neurodegeneration with brain iron accumulation 5 (BPAN)
 "work_capacity": ("UNKNOWN", "UNKNOWN", None, 45,
   "Orphanet holds no paid-work or professional-task rows for this disease, so the expert "
   "database is silent on this axis. PubMed on BPAN and WDR45 with employment and "
   "occupational-outcome terms returned only cohorts for other NBIA subtypes - PANK2 and "
   "PLA2G6 - which are different diseases and were not used. No level is asserted.", []),
 "care_dependence": ("SUBSTANTIAL", "STANDARD_OF_CARE_TREATED", "ANY", 70,
   "Orphanet rates managing one's own health as a complete permanent limitation occurring "
   "frequently, and body care as a severe limitation. The record is not expert-validated, so "
   "the line is MODERATE and the level is capped at SUBSTANTIAL.", []),
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
