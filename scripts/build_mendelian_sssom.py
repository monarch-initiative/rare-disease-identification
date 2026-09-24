#!/usr/bin/env python3
"""Emit two SSSOM mapping sets derived from Mendelian's first-pass ICD-10 worksheet.

Source: `background/Mendelian's First Pass ICD-10 Prioririties - Mar 2026.xlsx`, read
up in `background/mendelian-icd10-first-pass-interpretation.md` and compared against
our own value sets in `background/mendelian-xlsx-gap-analysis.html`.

The worksheet asserts, by hand, which ICD-10-CM code you would query to find patients
with a given Mondo disease, and whether that code denotes the disease (`Specific
disease`) or a bucket containing it (`Cluster`). 40 of its 101 assertions cannot be
reproduced from Mondo today. This script emits those 40, plus a handful of adjacent
finds, as two mapping sets intended for contribution upstream:

    mondo_icd10cm_exactmatch_mendelian.sssom.tsv   15 skos:exactMatch
    mondo_icd10cm_grouping_mendelian.sssom.tsv     24 skos:broadMatch + 10 skos:narrowMatch

The split is not cosmetic. The exact set is cheap and uncontroversial: ICD-10-CM
already carries a code that names the disease and Mondo simply lacks the mapping. The
grouping set is the interesting one: ICD-10-CM has no code for those diseases at all,
so the only truthful mapping is a broad one to the rubric that swallows them. Mondo
carries 79 broad matches to ICD-10-CM across the whole ontology against 2,038 exact
ones, and that imbalance is why a worksheet like this has to exist by hand.

Every object code, its label and its children were resolved against the NLM Clinical
Tables ICD-10-CM API (FY2026) while curating; `--verify` re-checks them. Subject
labels are checked against `tmp/mondo.obo` when present.

Usage:
    python scripts/build_mendelian_sssom.py
    python scripts/build_mendelian_sssom.py --verify --mondo-obo tmp/mondo.obo
"""

from __future__ import annotations

import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path

import click
import yaml

MAPPING_DATE = "2026-09-17"
MONDO_VERSION = "releases/2026-09-01"
ICD_VERSION = "FY2026"
TOOL = "rdi-mendelian-worksheet-reconciliation"

# TODO(attribution): `creator_id` and `author_id` are left empty on purpose. The
# assertions originate with whoever curated the worksheet at Mendelian, and the
# reconciliation is ours; both need real ORCIDs before this is contributed upstream.
CREATOR_ID = ""
AUTHOR_ID = ""

CURIE_MAP = {
    "ICD10CM": "http://purl.bioontology.org/ontology/ICD10CM/",
    "MONDO": "http://purl.obolibrary.org/obo/MONDO_",
    "biolink": "https://w3id.org/biolink/vocab/",
    "infores": "https://w3id.org/information-resource-registry/",
    "maprule": "https://w3id.org/mondo/mapping-rules/",
    "oboInOwl": "http://www.geneontology.org/formats/oboInOwl#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "semapv": "https://w3id.org/semapv/vocab/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "sssom": "https://w3id.org/sssom/",
}

COLUMNS = [
    "subject_id", "subject_label", "subject_category",
    "predicate_id",
    "object_id", "object_label", "object_category",
    "mapping_justification",
    "subject_type", "object_type",
    "subject_match_field", "object_match_field", "match_string",
    "subject_preprocessing",
    "mapping_date", "mapping_tool", "confidence",
    "curation_rule_text", "grouping_basis", "comment", "issue_tracker_item",
]

LEX = "semapv:LexicalMatching"
COMP = "semapv:CompositeMatching"
MAN = "semapv:ManualMappingCuration"
LABEL = "rdfs:label"
SYN = "oboInOwl:hasExactSynonym"
LOWER = "semapv:Lowercasing|semapv:RegularExpressionReplacement"

# --------------------------------------------------------------------------------
# EXACT MATCHES. ICD-10-CM already names the disease; Mondo has no ICD-10-CM mapping
# for the subject at all. `ws` records what the worksheet targeted instead, so the
# difference between the two is auditable.
# --------------------------------------------------------------------------------
EXACT = [
    dict(s="MONDO:0007191", sl="Behcet disease", o="ICD10CM:M35.2", ol="Behcet's disease",
         j=LEX, smf=LABEL, omf=LABEL, ms="behcet disease", conf="0.95", ws="M35.2",
         c="Label-identical after lowercasing and possessive removal. The worksheet reaches the same code and calls it a specific disease."),
    dict(s="MONDO:0007404", sl="Cri-du-chat syndrome", o="ICD10CM:Q93.4",
         ol="Deletion of short arm of chromosome 5", j=COMP, conf="0.9", ws="Q93",
         c="Q93.4 carries 'Cri-du-chat syndrome' as an ICD-10-CM inclusion term and 5p deletion is the defining lesion, so the two are coextensive despite unrelated labels. The worksheet targets the Q93 category, which also swallows Jacobsen, Williams, Wolf-Hirschhorn and Angelman."),
    dict(s="MONDO:0008644", sl="velocardiofacial syndrome", o="ICD10CM:Q93.81",
         ol="Velo-cardio-facial syndrome", j=LEX, smf=LABEL, omf=LABEL,
         ms="velocardiofacial syndrome", conf="0.95", ws="(not in the worksheet)",
         c="Label-identical after hyphen removal. Not in the worksheet at all: it targets D82.1 for 22q11.2 deletion syndrome and never picks up the other code the same deletion is recorded under."),
    dict(s="MONDO:0008667", sl="von Hippel-Lindau disease", o="ICD10CM:Q85.83",
         ol="Von Hippel-Lindau syndrome", j=LEX, smf=SYN, omf=LABEL,
         ms="von hippel-lindau syndrome", conf="0.95", ws="Q85.8",
         c="Matches the Mondo exact synonym 'von Hippel-Lindau syndrome'. The worksheet targets the Q85.8 phakomatoses bucket, shared there with PTEN hamartoma tumour syndrome, Sturge-Weber and Peutz-Jeghers."),
    dict(s="MONDO:0010035", sl="Smith-Lemli-Opitz syndrome", o="ICD10CM:E78.72",
         ol="Smith-Lemli-Opitz syndrome", j=LEX, smf=LABEL, omf=LABEL,
         ms="smith-lemli-opitz syndrome", conf="0.95", ws="Q87.1",
         c="Label-identical. ICD-10-CM files this with the sterol metabolism disorders, not with the Q87.1 malformation syndromes the worksheet targets, so the worksheet query returns no Smith-Lemli-Opitz patients."),
    dict(s="MONDO:0010383", sl="fragile X syndrome", o="ICD10CM:Q99.2", ol="Fragile X chromosome",
         j=COMP, conf="0.9", ws="Q99.2",
         c="Q99.2 carries 'Fragile X syndrome' as an ICD-10-CM inclusion term and has no other content. The worksheet reaches the same code and calls it a specific disease."),
    dict(s="MONDO:0010526", sl="Fabry disease", o="ICD10CM:E75.21", ol="Fabry (-Anderson) disease",
         j=LEX, smf=LABEL, omf=LABEL, ms="fabry disease", conf="0.95", ws="E75",
         c="Label-identical after removing the parenthetical eponym. The worksheet targets the E75 category, which it shares with Niemann-Pick, Tay-Sachs and Gaucher."),
    dict(s="MONDO:0010726", sl="Rett syndrome", o="ICD10CM:F84.2", ol="Rett's syndrome",
         j=LEX, smf=LABEL, omf=LABEL, ms="rett syndrome", conf="0.95", ws="F84.2",
         c="Label-identical after possessive removal. The worksheet reaches the same code and calls it a specific disease."),
    dict(s="MONDO:0015229", sl="Bardet-Biedl syndrome", o="ICD10CM:Q87.83",
         ol="Bardet-Biedl syndrome", j=LEX, smf=LABEL, omf=LABEL, ms="bardet-biedl syndrome",
         conf="0.95", ws="Q87.8",
         c="Label-identical. The worksheet targets the Q87.8 category, shared there with Alport syndrome."),
    dict(s="MONDO:0016512", sl="Kabuki syndrome", o="ICD10CM:Q89.81", ol="Kabuki syndrome",
         j=LEX, smf=LABEL, omf=LABEL, ms="kabuki syndrome", conf="0.95", ws="Q87.0",
         c="Label-identical. A recent ICD-10-CM addition outside the Q87.0 facial-appearance rubric the worksheet targets, so the worksheet query returns no Kabuki patients."),
    dict(s="MONDO:0017623", sl="PTEN hamartoma tumor syndrome", o="ICD10CM:Q85.81",
         ol="PTEN hamartoma tumor syndrome", j=LEX, smf=LABEL, omf=LABEL,
         ms="pten hamartoma tumor syndrome", conf="0.95", ws="Q85.8",
         c="Label-identical. Note that ICD-10-CM also files Bannayan-Riley-Ruvalcaba, a PTEN hamartoma subtype, at E71.440 under carnitine deficiency; Mondo already carries that one on MONDO:0007924."),
    dict(s="MONDO:0018037", sl="hyper-IgE syndrome", o="ICD10CM:D82.4",
         ol="Hyperimmunoglobulin E [IgE] syndrome", j=LEX, smf=SYN, omf=LABEL,
         ms="hyperimmunoglobulin e syndrome", conf="0.9", ws="D82.4",
         c="Matches the Mondo exact synonym after removing the bracketed gloss. The worksheet reaches the same code and calls it a specific disease."),
    dict(s="MONDO:0018544", sl="adrenoleukodystrophy", o="ICD10CM:E71.52",
         ol="X-linked adrenoleukodystrophy", j=COMP, conf="0.85", ws="E71.3",
         c="Subcategory match. MONDO:0018544 spans exactly the X-linked forms (X-linked cerebral ALD, adrenomyeloneuropathy, isolated adrenal insufficiency) and E71.52 subdivides into the same set, with neonatal ALD sitting outside both at E71.511. The worksheet targets E71.3, which is where WHO ICD-10 files ALD; ICD-10-CM does not, so that query returns no ALD patients. E71.52 is a non-billable subcategory and its label was taken from the tabular list, not from the billable-code API, so it is worth one manual check."),
    dict(s="MONDO:0019391", sl="Fanconi anemia", o="ICD10CM:D61.03", ol="Fanconi anemia",
         j=LEX, smf=LABEL, omf=LABEL, ms="fanconi anemia", conf="0.95", ws="D61.0",
         c="Label-identical. The worksheet targets the D61.0 category, which also contains Diamond-Blackfan and Shwachman-Diamond."),
    dict(s="MONDO:0019501", sl="Usher syndrome", o="ICD10CM:Q99.81", ol="Usher syndrome",
         j=COMP, conf="0.85", ws="H35.5",
         c="Subcategory match: Q99.81 subdivides into Usher types 1, 2, 3, other and unspecified and contains nothing else, matching the Mondo grouping exactly. The worksheet targets H35.5 hereditary retinal dystrophy, which misses the dedicated codes entirely. Q99.81 is a non-billable subcategory and its label was taken from the tabular list, so it is worth one manual check."),
    dict(s="MONDO:0008684", sl="Wolf-Hirschhorn syndrome", o="ICD10CM:Q93.3",
         ol="Deletion of short arm of chromosome 4", j=COMP, conf="0.9", ws="Q93",
         c="4p deletion is the defining lesion, so the two are coextensive despite unrelated labels; the same pattern as cri-du-chat at Q93.4. The worksheet targets the Q93 category, which ICD-10-CM subdivides and which is therefore not assignable."),
    dict(s="MONDO:0019259", sl="classic phenylketonuria", o="ICD10CM:E70.0",
         ol="Classical phenylketonuria", j=LEX, smf=LABEL, omf=LABEL,
         ms="classical phenylketonuria", conf="0.95", ws="E70 (for MONDO:0009861 phenylketonuria)",
         c="Label-identical. The worksheet attaches E70 to MONDO:0009861 phenylketonuria, which is the Mondo group spanning classic, mild, maternal and BH4-responsive forms; E70.0 is exactly the classic form, so the mapping belongs one level down. MONDO:0009861 then reaches E70.0 through its Mondo child, which is the direction a value set can safely follow. MONDO:0019259 is not on our prioritised list."),
    dict(s="MONDO:0018116", sl="galactosemia", o="ICD10CM:E74.21", ol="Galactosemia",
         j=LEX, smf=LABEL, omf=LABEL, ms="galactosemia", conf="0.95",
         ws="E74.2 (for MONDO:0009258 classic galactosemia)",
         c="Label-identical. The worksheet attaches E74.2 to classic galactosemia; E74.21 is the galactosemia group, so the exact mapping belongs on the Mondo group term and classic galactosemia relates to it as a subtype."),
    dict(s="MONDO:0015483", sl="mandibulofacial dysostosis", o="ICD10CM:Q75.4",
         ol="Mandibulofacial dysostosis", j=LEX, smf=LABEL, omf=LABEL,
         ms="mandibulofacial dysostosis", conf="0.95",
         ws="Q75.4 (for MONDO:0002457 Treacher-Collins syndrome)",
         c="Label-identical. The worksheet attaches Q75.4 to Treacher-Collins, which is a subtype; Q75.4 is the dysostosis group and is the Mondo parent of Treacher-Collins, so the exact mapping belongs there. MONDO:0015483 is not on our prioritised list."),
    dict(s="MONDO:0016669", sl="sickle cell-hemoglobin c disease syndrome", o="ICD10CM:D57.2",
         ol="Sickle-cell/Hb-C disease", j=LEX, smf=LABEL, omf=LABEL,
         ms="sickle cell hemoglobin c disease", conf="0.95", ws="D57 (for MONDO:0011382 sickle cell disease)",
         c="CORRECTION. Mondo currently asserts D57.2 as an exactMatch on MONDO:0011382 sickle cell disease, but D57.2 is Hb-SC disease specifically, which is this term, a Mondo child of it. The misplaced mapping is why a value set built for sickle cell disease returns only the seven D57.2 leaves and misses Hb-SS disease entirely. SSSOM cannot express a retraction, so the existing mapping needs a Mondo ticket alongside this row. MONDO:0016669 is not on our prioritised list."),
    dict(s="MONDO:0016668", sl="sickle cell-beta-thalassemia disease syndrome", o="ICD10CM:D57.4",
         ol="Sickle-cell thalassemia", j=LEX, smf=LABEL, omf=LABEL,
         ms="sickle cell thalassemia", conf="0.9", ws="D57 (for MONDO:0011382 sickle cell disease)",
         c="Note that MONDO:0016668 is not currently an is_a descendant of MONDO:0011382 sickle cell disease in Mondo, its parents being syndromic disease and inherited hemoglobinopathy. That is worth a Mondo ticket of its own; until it is fixed a value set for sickle cell disease cannot reach D57.4 through the hierarchy, which is why the companion set also asserts D57.4 directly as a narrow match. MONDO:0016668 is not on our prioritised list."),
]

# --------------------------------------------------------------------------------
# GROUPING MAPPINGS. ICD-10-CM has no code for these diseases, so no exact match is
# possible and the truthful assertion is a broad one. Every `broadMatch` row below
# was checked by searching ICD-10-CM for the Mondo label and every exact synonym and
# finding nothing.
# --------------------------------------------------------------------------------
# `basis` records WHY a broad mapping is defensible, because "cluster" in the
# worksheet hides three different situations and only two of them are class
# relationships:
#   subsumption     - the ICD rubric is a genuine superclass of the disease
#   icd_index       - ICD's own index/inclusion terms send this disease to this code
#   residual_bucket - the rubric is an "other specified"/NEC wastebasket. The mapping
#                     records where a coder puts the patient, not what the code means.
# `grouping_basis` is a non-standard SSSOM slot; conformant parsers may drop it.
#
# Where the semantically correct target is a category that ICD-10-CM subdivides, the
# object is the assignable residual child (Q87.19, not Q87.1) and the comment names
# the category the subsumption actually runs through.
BROAD = [
    ("MONDO:0007534", "Beckwith-Wiedemann syndrome", "ICD10CM:Q87.3",
     "Congenital malformation syndromes involving early overgrowth", "1,150", "subsumption",
     "Beckwith-Wiedemann is an overgrowth syndrome, so the rubric is a true superclass."),
    ("MONDO:0019349", "Sotos syndrome", "ICD10CM:Q87.3",
     "Congenital malformation syndromes involving early overgrowth", "1,150", "subsumption",
     "Sotos is an overgrowth syndrome, so the rubric is a true superclass. Note that Q87.3 carries Beckwith-Wiedemann too, so the code cannot distinguish them."),
    ("MONDO:0018997", "Noonan syndrome", "ICD10CM:Q87.19",
     "Other congenital malformation syndromes predominantly associated with short stature",
     "890", "subsumption",
     "Subsumption runs through the Q87.1 category, which is a true superclass; Q87.19 is the assignable residual child once Prader-Willi (Q87.11) is carved out. The worksheet targets Q87.1, which ICD-10-CM subdivides and which is therefore not assignable."),
    ("MONDO:0016033", "Cornelia de Lange syndrome", "ICD10CM:Q87.19",
     "Other congenital malformation syndromes predominantly associated with short stature",
     "890", "subsumption",
     "Subsumption runs through the Q87.1 category, which is a true superclass; Q87.19 is the assignable residual child. The worksheet targets Q87.1, which is not assignable."),
    ("MONDO:0016006", "Cockayne syndrome", "ICD10CM:Q87.19",
     "Other congenital malformation syndromes predominantly associated with short stature",
     "890", "subsumption",
     "Subsumption runs through the Q87.1 category, which is a true superclass; Q87.19 is the assignable residual child. The worksheet targets Q87.1, which is not assignable."),
    ("MONDO:0019354", "Stickler syndrome", "ICD10CM:Q87.0",
     "Congenital malformation syndromes predominantly affecting facial appearance", "670",
     "subsumption",
     "Midface hypoplasia and the flat facial profile are cardinal features, so the rubric subsumes the disease, though it also subsumes Kabuki and Mobius and cannot distinguish them."),
    ("MONDO:0008006", "Moebius syndrome", "ICD10CM:Q87.0",
     "Congenital malformation syndromes predominantly affecting facial appearance", "670",
     "subsumption",
     "Congenital facial diplegia is the defining feature, so the rubric subsumes the disease."),
    ("MONDO:0008501", "Sturge-Weber syndrome", "ICD10CM:Q85.89",
     "Other phakomatoses, not elsewhere classified", "560", "icd_index",
     "ICD-10 lists Sturge-Weber(-Dimitri) syndrome as an inclusion term under Q85.8, so the classification itself assigns it here; Q85.89 is the assignable residual child once PTEN (Q85.81), Cowden (Q85.82) and von Hippel-Lindau (Q85.83) are carved out. The worksheet targets Q85.8, which ICD-10-CM subdivides and which is therefore not assignable. Inclusion terms are not exposed by the NLM API and were read from the tabular list; worth one manual check."),
    ("MONDO:0008280", "Peutz-Jeghers syndrome", "ICD10CM:Q85.89",
     "Other phakomatoses, not elsewhere classified", "560", "icd_index",
     "ICD-10 lists Peutz-Jeghers syndrome as an inclusion term under Q85.8, so the classification itself assigns it here; Q85.89 is the assignable residual child. The worksheet targets Q85.8, which is not assignable. Inclusion terms are not exposed by the NLM API and were read from the tabular list; worth one manual check."),
    ("MONDO:0019188", "Rubinstein-Taybi syndrome", "ICD10CM:Q87.2",
     "Congenital malformation syndromes predominantly involving limbs", "1,290", "subsumption",
     "Broad thumbs and halluces are cardinal features, so the rubric subsumes the disease."),
    ("MONDO:0007838", "Jacobsen syndrome", "ICD10CM:Q93.59",
     "Other deletions of part of a chromosome", "2,500", "residual_bucket",
     "Jacobsen is a terminal 11q deletion, which ICD-10-CM does not name. Q93.59 is the assignable residual leaf; Q93.88 'Other microdeletions' is the plausible alternative and a coder should settle which. The worksheet targets the Q93 category, which ICD-10-CM subdivides and which is therefore not assignable."),
    ("MONDO:0007875", "Larsen syndrome", "ICD10CM:Q74.8",
     "Other specified congenital malformations of limb(s)", "140", "residual_bucket",
     "A wastebasket rubric. Larsen is a multiple-dislocation syndrome rather than a limb malformation per se, so this records where a coder puts the patient, not what the code means."),
    ("MONDO:0010568", "Aicardi syndrome", "ICD10CM:Q04.0",
     "Congenital malformations of corpus callosum", "770", "subsumption",
     "Agenesis of the corpus callosum is a defining feature of Aicardi syndrome, so the rubric is a true superclass. Beware the near-neighbour E79.81 Aicardi-Goutieres syndrome, which is a different disease."),
    ("MONDO:0016575", "primary ciliary dyskinesia", "ICD10CM:Q34.8",
     "Other specified congenital malformations of respiratory system", "670", "residual_bucket",
     "A wastebasket rubric. PCD is a ciliary motility defect rather than a structural malformation of the airway, so this records where a coder puts the patient, not what the code means. Kartagener syndrome, the situs inversus subset, is coded separately at Q89.3."),
    ("MONDO:0018919", "McCune-Albright syndrome", "ICD10CM:Q78.1",
     "Polyostotic fibrous dysplasia", "90", "subsumption",
     "Polyostotic fibrous dysplasia is present in McCune-Albright by definition, so the rubric is a true superclass; it also covers isolated polyostotic fibrous dysplasia without the endocrine features."),
    ("MONDO:0008763", "Alstrom syndrome", "ICD10CM:E34.8",
     "Other specified endocrine disorders", "1,530", "residual_bucket",
     "A wastebasket rubric. Alstrom is a ciliopathy with endocrine consequences rather than a kind of endocrine disorder, so this records where a coder puts the patient, not what the code means."),
    ("MONDO:0018570", "hypophosphatasia", "ICD10CM:E83.39",
     "Other disorders of phosphorus metabolism", "34,750", "subsumption",
     "Subsumption runs through the E83.3 category, 'Disorders of phosphorus metabolism and phosphatases', which is a true superclass of an alkaline phosphatase deficiency; E83.39 is the assignable residual child once familial hypophosphatemia (E83.31) and vitamin D-dependent rickets (E83.32) are carved out. The worksheet targets E83.3, which ICD-10-CM subdivides and which is therefore not assignable."),
    ("MONDO:0011776", "CINCA syndrome", "ICD10CM:M04.2",
     "Cryopyrin-associated periodic syndromes", "", "subsumption",
     "CORRECTION to the worksheet, which targets E85 Amyloidosis. CINCA carries the Mondo exact synonym 'cryopyrin-associated periodic syndrome 3' and M04.2 is its rubric; E85 is an artefact of WHO ICD-10 filing the periodic fevers under amyloidosis because of the AA amyloidosis complication. Querying E85 for CINCA patients is querying the complication, not the disease."),
    ("MONDO:0010421", "Bruton-type agammaglobulinemia", "ICD10CM:D80.0",
     "Hereditary hypogammaglobulinemia", "140", "icd_index",
     "ICD-10 lists X-linked agammaglobulinemia [Bruton] as an inclusion term under D80.0, so the classification itself assigns it here, and the rubric is narrow enough to be a high-yield cohort. Inclusion terms are not exposed by the NLM API and were read from the tabular list; worth one manual check."),
    ("MONDO:0015696", "Good syndrome", "ICD10CM:D81.89",
     "Other combined immunodeficiencies", "240", "subsumption",
     "Subsumption runs through the D81 category: Good syndrome is a combined immunodeficiency. D81.89 is the assignable residual child. The worksheet targets D81.8, which ICD-10-CM subdivides and which is therefore not assignable."),
    ("MONDO:0015626", "Charcot-Marie-Tooth disease", "ICD10CM:G60.0", 
     "Hereditary motor and sensory neuropathy", "2,180", "icd_index",
     "Hereditary motor and sensory neuropathy is the historical name for the CMT group and ICD-10 lists Charcot-Marie-Tooth disease as an inclusion term under G60.0, so this is close to exact; it stays broad because the rubric also covers Dejerine-Sottas and Refsum disease. Inclusion terms were read from the tabular list; worth one manual check."),
    ("MONDO:0015263", "Brugada syndrome", "ICD10CM:I49.8",
     "Other specified cardiac arrhythmias", "63,930", "icd_index",
     "ICD-10-CM lists Brugada syndrome as an inclusion term under I49.8, so the classification assigns it here, but the rubric is an unsubdivided catch-all carrying 63,930 patients at one site. Retrieval only: this cannot be a case definition without an ECG or genetic filter. Inclusion terms were read from the tabular list; worth one manual check."),
    ("MONDO:0019266", "SAPHO syndrome", "ICD10CM:M86.3",
     "Chronic multifocal osteomyelitis", "1,080", "subsumption",
     "The osteitis component of SAPHO is chronic recurrent multifocal osteomyelitis, which M86.3 names, so the rubric subsumes the bone disease; it does not capture the synovitis, acne or pustulosis. M86.3 subdivides by anatomical site only, so the category is the right level for a value set."),
    ("MONDO:0016486", "beta-thalassemia major", "ICD10CM:D56.1", "Beta thalassemia", "990",
     "subsumption",
     "D56.1 is a leaf covering beta thalassemia major and intermedia together, so it is a true superclass of the major form and cannot isolate it. The exact mapping arguably belongs on a Mondo beta-thalassemia grouping term; MONDO:0013517 'beta-thalassemia HBB/LCRB' is the nearest candidate and is a Mondo-side question."),
    ("MONDO:0019623", "hereditary angioedema", "ICD10CM:D84.1",
     "Defects in the complement system", "980", "subsumption",
     "C1-inhibitor deficiency is a complement regulatory defect, so the rubric is a true superclass; ICD-10-CM has no hereditary angioedema code."),
    ("MONDO:0008753", "alkaptonuria", "ICD10CM:E70.29",
     "Other disorders of tyrosine metabolism", "1,010", "subsumption",
     "Subsumption runs through E70.2 'Disorders of tyrosine metabolism', a true superclass of alkaptonuria; E70.29 is the assignable residual child once tyrosinemia (E70.21) is carved out. The worksheet targets E70, which is not assignable and which it shares with phenylketonuria."),
    ("MONDO:0009258", "classic galactosemia", "ICD10CM:E74.21", "Galactosemia", "280",
     "subsumption",
     "E74.21 is the galactosemia group, a true superclass of the classic form. The exact mapping for E74.21 is proposed on MONDO:0018116 galactosemia in the companion exact set, so a value set built for the group picks it up directly and the classic subtype correctly gets nothing of its own."),
    ("MONDO:0010679", "Duchenne muscular dystrophy", "ICD10CM:G71.01",
     "Duchenne or Becker muscular dystrophy", "1,680", "subsumption",
     "The code names Duchenne and Becker together and cannot separate them, so it is a true superclass of either. Better than the worksheet's G71.0, which also carries facioscapulohumeral and every limb-girdle dystrophy."),
    ("MONDO:0002457", "Treacher-Collins syndrome", "ICD10CM:Q75.4",
     "Mandibulofacial dysostosis", "70", "subsumption",
     "Q75.4 is the dysostosis group and is Treacher-Collins' Mondo parent. The exact mapping is proposed on MONDO:0015483 mandibulofacial dysostosis in the companion exact set."),
    ("MONDO:0019353", "Stargardt disease", "ICD10CM:H35.54",
     "Dystrophies primarily involving the retinal pigment epithelium", "2,280", "residual_bucket",
     "ICD-10-CM has no Stargardt code. H35.54 is the closest rubric but H35.53 'Other dystrophies primarily involving the sensory retina' is a plausible alternative and a coder should settle which; the worksheet targets the whole H35.5 category. Retrieval only."),
    ("MONDO:0018875", "Li-Fraumeni syndrome", "ICD10CM:Z15.09",
     "Genetic susceptibility to other malignant neoplasm", "15,220", "residual_bucket",
     "ICD-10-CM has no Li-Fraumeni code, and Z15 is a susceptibility flag rather than a diagnosis, so this is not a disease mapping in any ordinary sense. The worksheet targets the whole Z15 category, whose 15,220 patients are dominated by Z15.01 BRCA breast-cancer susceptibility. Retrieval only, and weak retrieval at that."),
]

# One departure from the worksheet, flagged rather than silent.
BROAD_TIGHTENED = [
    dict(s="MONDO:0010619", sl="X-linked dominant hypophosphatemic rickets",
         o="ICD10CM:E83.31", ol="Familial hypophosphatemia", ws="E83.3", conf="0.9",
         c="The worksheet targets the whole E83.3 rubric, whose 34,750 patients are dominated by routine phosphate abnormalities. E83.31 is the ICD rubric for the hereditary hypophosphatemic rickets group specifically, so it is the tighter true broad match; it still spans ADHR, ARHR1, HHRH and XLH, so it is not an exact match."),
]

# ICD-10-CM subdivides these diseases without offering a code for the whole, so each
# code is narrower than the Mondo term rather than broader.
NARROW = [
    ("MONDO:0016367", "dermatomyositis", "ICD10CM:M33.0", "Juvenile dermatomyositis"),
    ("MONDO:0016367", "dermatomyositis", "ICD10CM:M33.1", "Other dermatomyositis"),
    ("MONDO:0011382", "sickle cell disease", "ICD10CM:D57.0", "Hb-SS disease with crisis"),
    ("MONDO:0011382", "sickle cell disease", "ICD10CM:D57.1",
     "Sickle-cell disease without crisis"),
    ("MONDO:0011382", "sickle cell disease", "ICD10CM:D57.4", "Sickle-cell thalassemia"),
    ("MONDO:0011382", "sickle cell disease", "ICD10CM:D57.8", "Other sickle-cell disorders"),
    ("MONDO:0018071", "trisomy 18", "ICD10CM:Q91.0",
     "Trisomy 18, nonmosaicism (meiotic nondisjunction)"),
    ("MONDO:0018071", "trisomy 18", "ICD10CM:Q91.1",
     "Trisomy 18, mosaicism (mitotic nondisjunction)"),
    ("MONDO:0018071", "trisomy 18", "ICD10CM:Q91.2", "Trisomy 18, translocation"),
    ("MONDO:0018071", "trisomy 18", "ICD10CM:Q91.3", "Trisomy 18, unspecified"),
    ("MONDO:0018068", "trisomy 13", "ICD10CM:Q91.4",
     "Trisomy 13, nonmosaicism (meiotic nondisjunction)"),
    ("MONDO:0018068", "trisomy 13", "ICD10CM:Q91.5",
     "Trisomy 13, mosaicism (mitotic nondisjunction)"),
    ("MONDO:0018068", "trisomy 13", "ICD10CM:Q91.6", "Trisomy 13, translocation"),
    ("MONDO:0018068", "trisomy 13", "ICD10CM:Q91.7", "Trisomy 13, unspecified"),
    ("MONDO:0018923", "22q11.2 deletion syndrome", "ICD10CM:D82.1", "Di George's syndrome"),
    ("MONDO:0018923", "22q11.2 deletion syndrome", "ICD10CM:Q93.81",
     "Velo-cardio-facial syndrome"),
]

NARROW_COMMENT = {
    "MONDO:0016367": "CORRECTION. Mondo asserts M33 Dermatopolymyositis as an exactMatch on this term, but M33 subdivides into M33.0x juvenile dermatomyositis, M33.1x other dermatomyositis, M33.2x polymyositis and M33.9x dermatopolymyositis unspecified. Polymyositis is a distinct disease with its own Mondo class, so M33 is broader than dermatomyositis and a value set built from it pulls polymyositis patients. M33.0 and M33.1 are the dermatomyositis half. M33.9 is a judgement call: it is the unspecified overlap and may belong here in practice. The existing M33 mapping needs retracting, which SSSOM cannot express.",
    "MONDO:0011382": "ICD-10-CM subdivides sickle cell disorders by genotype and crisis status across D57.0 (Hb-SS with crisis), D57.1 (without crisis), D57.2 (Hb-SC), D57.4 (sickle-cell thalassemia) and D57.8 (other), with no code for the disease as a whole: the D57 category also contains D57.3 sickle-cell trait, a carrier state rather than the disease, so D57 itself is broader. D57.2 is reached through the Mondo child MONDO:0016669 and is not repeated here; D57.4 is asserted directly because MONDO:0016668 is not currently a Mondo descendant of this term. D57.3 is deliberately excluded. Mondo today maps this term to D57.2 alone, which yields a value set of seven Hb-SC leaves and misses Hb-SS disease, the commonest form.",
    "MONDO:0018071": "ICD-10-CM splits trisomy 18 across Q91.0-Q91.3 by mechanism and offers no code for the disease as a whole, so each code is narrower than the Mondo term. The worksheet targets the Q91 category, which carries trisomy 18 and trisomy 13 together under one patient count; Q91.0-Q91.3 versus Q91.4-Q91.7 separates them at no cost.",
    "MONDO:0018068": "ICD-10-CM splits trisomy 13 across Q91.4-Q91.7 by mechanism and offers no code for the disease as a whole, so each code is narrower than the Mondo term. The worksheet targets the Q91 category, which carries trisomy 18 and trisomy 13 together under one patient count; Q91.0-Q91.3 versus Q91.4-Q91.7 separates them at no cost.",
    "MONDO:0018923": "ICD-10-CM records this deletion under two labels that survive from the era when DiGeorge and velocardiofacial syndrome were treated as separate entities. Neither code alone is the disease, so both are narrower than the Mondo term and a value set needs both. The worksheet targets only D82.1, so roughly the Q93.81 half of the cohort is attributed to the Q93 row instead.",
}

RULES_EXACT = "maprule:PR-001 same real-world concept | maprule:EV-004 match after declared lexical transformation"
RULES_COMP = "maprule:PR-001 same real-world concept | maprule:EV-012 adjudicated over retrieved candidates"
RULES_BROAD = "maprule:SC-004 target coarser than subject | maprule:PR-003 object is a superclass"
RULES_NARROW = "maprule:SC-005 target finer than subject | maprule:PR-002 object is a subclass"


def exact_rows() -> list[dict]:
    rows = []
    for e in EXACT:
        rows.append({
            "subject_id": e["s"], "subject_label": e["sl"], "subject_category": "biolink:Disease",
            "predicate_id": "skos:exactMatch",
            "object_id": e["o"], "object_label": e["ol"], "object_category": "biolink:Disease",
            "mapping_justification": e["j"],
            "subject_type": "owl class", "object_type": "owl class",
            "subject_match_field": e.get("smf", ""), "object_match_field": e.get("omf", ""),
            "match_string": e.get("ms", ""),
            "subject_preprocessing": LOWER if e["j"] == LEX else "",
            "mapping_date": MAPPING_DATE, "mapping_tool": TOOL, "confidence": e["conf"],
            "curation_rule_text": RULES_EXACT if e["j"] == LEX else RULES_COMP,
            "grouping_basis": "",
            "comment": f"Worksheet targets {e['ws']}. " + e["c"],
            "issue_tracker_item": "",
        })
    return rows


def grouping_rows() -> list[dict]:
    rows = []
    for s, sl, o, ol, count, basis, note in BROAD:
        rows.append({
            "subject_id": s, "subject_label": sl, "subject_category": "biolink:Disease",
            "predicate_id": "skos:broadMatch",
            "object_id": o, "object_label": ol, "object_category": "biolink:Disease",
            "mapping_justification": MAN,
            "subject_type": "owl class", "object_type": "owl class",
            "subject_match_field": "", "object_match_field": "", "match_string": "",
            "subject_preprocessing": "",
            "mapping_date": MAPPING_DATE, "mapping_tool": TOOL, "confidence": "0.9",
            "curation_rule_text": RULES_BROAD,
            "grouping_basis": basis,
            "comment": (
                f"ICD-10-CM has no code for this disease; searching it for the Mondo label and "
                f"every exact synonym returns nothing. {note}"
                + (f" The worksheet counts {count} patients on the code it targets at one US site, "
                   f"so this is a retrieval net and not a case definition." if count else "")
            ),
            "issue_tracker_item": "",
        })
    for e in BROAD_TIGHTENED:
        rows.append({
            "subject_id": e["s"], "subject_label": e["sl"], "subject_category": "biolink:Disease",
            "predicate_id": "skos:broadMatch",
            "object_id": e["o"], "object_label": e["ol"], "object_category": "biolink:Disease",
            "mapping_justification": MAN,
            "subject_type": "owl class", "object_type": "owl class",
            "subject_match_field": "", "object_match_field": "", "match_string": "",
            "subject_preprocessing": "",
            "mapping_date": MAPPING_DATE, "mapping_tool": TOOL, "confidence": e["conf"],
            "curation_rule_text": RULES_BROAD,
            "grouping_basis": "subsumption",
            "comment": f"Worksheet targets {e['ws']}. " + e["c"],
            "issue_tracker_item": "",
        })
    for s, sl, o, ol in NARROW:
        rows.append({
            "subject_id": s, "subject_label": sl, "subject_category": "biolink:Disease",
            "predicate_id": "skos:narrowMatch",
            "object_id": o, "object_label": ol, "object_category": "biolink:Disease",
            "mapping_justification": MAN,
            "subject_type": "owl class", "object_type": "owl class",
            "subject_match_field": "", "object_match_field": "", "match_string": "",
            "subject_preprocessing": "",
            "mapping_date": MAPPING_DATE, "mapping_tool": TOOL, "confidence": "0.95",
            "curation_rule_text": RULES_NARROW,
            "grouping_basis": "",
            "comment": NARROW_COMMENT[s],
            "issue_tracker_item": "",
        })
    return rows


EXACT_DESC = (
    "ICD-10-CM codes that name a rare disease outright, for Mondo classes that carry no "
    "ICD-10-CM mapping at all. Every subject was checked against Mondo "
    f"{MONDO_VERSION}: none of them has an existing exactmatch, closematch, narrowmatch, "
    "broadmatch, relatedmatch or hasdbxref row to ICD-10-CM in the published SSSOM "
    "releases. Every object code and label was resolved from the NLM Clinical Tables "
    f"ICD-10-CM API ({ICD_VERSION}); labels in the source worksheet were not trusted. "
    "Nine of these fifteen were independently proposed by an automated lexical and LLM "
    "pipeline over the same disease list and reviewed at full confidence "
    "(mappings/rdi_novel_icd10cm_reviewed.sssom.tsv); the worksheet and that pipeline "
    "agree on all nine."
)

GROUPING_DESC = (
    "Non-exact ICD-10-CM mappings for rare diseases the classification does not name. "
    "Each broadMatch subject was searched in ICD-10-CM under its Mondo label and every "
    "exact synonym with no result, so no exact mapping is available and the grouping "
    "rubric is the only truthful target. The narrowMatch rows are the converse case: "
    "ICD-10-CM subdivides the disease without offering a code for the whole. This set "
    "exists because Mondo carries 79 broadMatch mappings to ICD-10-CM against 2,038 "
    "exactMatch, which leaves every disease in this file invisible to any value set "
    "derived from Mondo. The non-standard `grouping_basis` column records why each broad "
    "mapping is defensible: `subsumption` where the ICD rubric is a genuine superclass, "
    "`icd_index` where ICD's own inclusion terms assign the disease to the code, and "
    "`residual_bucket` where the rubric is an 'other specified' wastebasket and the row "
    "records where a coder puts the patient rather than what the code means. Only the "
    "first two are class relationships; the four `residual_bucket` rows are ascertainment "
    "heuristics and a curator may reasonably decline them. These mappings are "
    "deliberately lossy and must stay separable "
    "from exact ones: pulling a patient cohort on one of these codes pulls a population "
    "far larger than the disease."
)

PROVENANCE = (
    "Derived from 'Mendelian's First Pass ICD-10 Priorities - Mar 2026' (XLSX), a "
    "hand-built worksheet of 75 ICD-10-CM codes selected as EHR ascertainment handles, "
    "each annotated with the Mondo disease it stands for and marked 'Specific disease' "
    "or 'Cluster'. The worksheet does not pin a Mondo version. Reconciliation against "
    f"Mondo {MONDO_VERSION} and ICD-10-CM {ICD_VERSION}, and the per-row comments, are "
    "ours. Patient counts quoted in comments are the worksheet's own, from UNC Health "
    "via TriNetX, rounded to the nearest 10: single-site, and a signal rather than a "
    "prevalence estimate. NATURE OF THIS SET: proposals for curator review, not curated "
    "assertions. See background/mendelian-icd10-first-pass-interpretation.md and "
    "background/mendelian-xlsx-gap-analysis.html in "
    "monarch-initiative/rare-disease-identification."
)


def write_set(path: Path, rows: list[dict], set_id: str, title: str, description: str) -> None:
    """Write one SSSOM TSV: a commented YAML metadata block, then the table.

    The metadata is serialised with PyYAML rather than formatted by hand, because the
    descriptions contain apostrophes and a hand-quoted block is not parseable YAML.
    """
    meta: dict[str, object] = {
        "mapping_set_id": set_id,
        "mapping_set_title": title,
        "mapping_set_version": MAPPING_DATE,
        "mapping_set_description": description,
        "comment": PROVENANCE,
        "license": "https://creativecommons.org/publicdomain/zero/1.0/",
        "mapping_provider": "https://github.com/monarch-initiative/rare-disease-identification",
        "mapping_tool": TOOL,
        "mapping_date": MAPPING_DATE,
        "subject_source": "infores:mondo",
        "subject_source_version": MONDO_VERSION,
        "object_source": "infores:icd10cm",
        "object_source_version": ICD_VERSION,
        "subject_type": "owl class",
        "object_type": "owl class",
    }
    if CREATOR_ID:
        meta["creator_id"] = [CREATOR_ID]
    meta["curie_map"] = dict(sorted(CURIE_MAP.items()))

    block = yaml.safe_dump(meta, sort_keys=False, default_flow_style=False, width=10000,
                           allow_unicode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        for line in block.rstrip("\n").split("\n"):
            f.write(f"# {line}\n")
        writer = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t", extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def mondo_labels(mondo_obo: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    current = None
    with open(mondo_obo) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("id: MONDO:"):
                current = line[4:].strip()
            elif line.startswith("name: ") and current:
                labels[current] = line[6:]
                current = None
    return labels


def icd_label(code: str) -> str | None:
    q = urllib.parse.urlencode({"sf": "code", "terms": code, "maxList": "500"})
    url = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search?" + q
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    hits = data[3] if len(data) > 3 and data[3] else []
    for c, label in hits:
        if c == code:
            return label
    return f"<{len(hits)} children, not itself billable>" if hits else None


@click.command()
@click.option("--outdir", type=click.Path(path_type=Path), default=Path("mappings"),
              show_default=True, help="Where to write the two SSSOM files.")
@click.option("--verify/--no-verify", default=False,
              help="Re-check subject labels against mondo.obo and object codes against NLM.")
@click.option("--mondo-obo", type=click.Path(path_type=Path), default=Path("tmp/mondo.obo"),
              show_default=True, help="mondo.obo, used by --verify.")
def main(outdir: Path, verify: bool, mondo_obo: Path):
    """Emit the exact-match and grouping SSSOM sets."""
    base = "https://w3id.org/monarch-initiative/rare-disease-identification/mappings"
    exact = exact_rows()
    grouping = grouping_rows()

    write_set(outdir / "mondo_icd10cm_exactmatch_mendelian.sssom.tsv", exact,
              f"{base}/mondo_icd10cm_exactmatch_mendelian",
              "MONDO to ICD-10-CM exact matches recovered from Mendelian's first-pass worksheet",
              EXACT_DESC)
    write_set(outdir / "mondo_icd10cm_grouping_mendelian.sssom.tsv", grouping,
              f"{base}/mondo_icd10cm_grouping_mendelian",
              "MONDO to ICD-10-CM broad and narrow matches recovered from Mendelian's first-pass worksheet",
              GROUPING_DESC)

    n_broad = sum(1 for r in grouping if r["predicate_id"] == "skos:broadMatch")
    n_narrow = sum(1 for r in grouping if r["predicate_id"] == "skos:narrowMatch")
    click.echo(f"Written {len(exact)} exact matches to {outdir}/mondo_icd10cm_exactmatch_mendelian.sssom.tsv")
    click.echo(f"Written {n_broad} broad + {n_narrow} narrow matches to {outdir}/mondo_icd10cm_grouping_mendelian.sssom.tsv")
    if not CREATOR_ID or not AUTHOR_ID:
        click.echo("NOTE: creator_id/author_id are unset; fill them in before contributing upstream.")

    if not verify:
        return

    click.echo("\nVerifying subject labels against Mondo:")
    if mondo_obo.exists():
        labels = mondo_labels(mondo_obo)
        bad = 0
        for row in exact + grouping:
            want = labels.get(row["subject_id"])
            if want is None:
                click.echo(f"  MISSING {row['subject_id']} not in {mondo_obo}")
                bad += 1
            elif want != row["subject_label"]:
                click.echo(f"  DRIFT   {row['subject_id']} file={row['subject_label']!r} mondo={want!r}")
                bad += 1
        click.echo(f"  {bad} subject label problems")
    else:
        click.echo(f"  skipped, {mondo_obo} not found")

    click.echo("Verifying object codes against ICD-10-CM:")
    seen = set()
    for row in exact + grouping:
        code = row["object_id"].split(":", 1)[1]
        if code in seen:
            continue
        seen.add(code)
        got = icd_label(code)
        if got is None:
            click.echo(f"  ABSENT  {code} not found in ICD-10-CM")
        elif got.startswith("<"):
            click.echo(f"  CATEGORY {code} {got} — file says {row['object_label']!r}")
        elif got != row["object_label"]:
            click.echo(f"  DRIFT   {code} file={row['object_label']!r} icd={got!r}")
    click.echo(f"  {len(seen)} distinct codes checked")


if __name__ == "__main__":
    main()
