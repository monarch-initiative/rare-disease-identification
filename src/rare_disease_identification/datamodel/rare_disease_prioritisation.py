# Auto generated from rare_disease_prioritisation.yaml by pythongen.py version: 0.0.1
# Generation date: 2026-04-09T10:50:54
# Schema: rare_disease_prioritisation
#
# id: https://w3id.org/rare-disease-identification
# description: Schema for prioritised rare diseases for phenotypic characterization.
# license: https://creativecommons.org/publicdomain/zero/1.0/

import dataclasses
import re
from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    time
)
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Union
)

from jsonasobj2 import (
    JsonObj,
    as_dict
)
from linkml_runtime.linkml_model.meta import (
    EnumDefinition,
    PermissibleValue,
    PvFormulaOptions
)
from linkml_runtime.utils.curienamespace import CurieNamespace
from linkml_runtime.utils.enumerations import EnumDefinitionImpl
from linkml_runtime.utils.formatutils import (
    camelcase,
    sfx,
    underscore
)
from linkml_runtime.utils.metamodelcore import (
    bnode,
    empty_dict,
    empty_list
)
from linkml_runtime.utils.slot import Slot
from linkml_runtime.utils.yamlutils import (
    YAMLRoot,
    extended_float,
    extended_int,
    extended_str
)
from rdflib import (
    Namespace,
    URIRef
)

from linkml_runtime.linkml_model.types import Float, String

metamodel_version = "1.7.0"
version = None

# Namespaces
HP = CurieNamespace('HP', 'http://purl.obolibrary.org/obo/HP_')
MONDO = CurieNamespace('MONDO', 'http://purl.obolibrary.org/obo/MONDO_')
LINKML = CurieNamespace('linkml', 'https://w3id.org/linkml/')
RDID = CurieNamespace('rdid', 'https://w3id.org/rare-disease-identification/')
DEFAULT_ = RDID


# Types

# Class references
class SimpleTermId(extended_str):
    pass


class RareDiseaseMondoId(extended_str):
    pass


@dataclass(repr=False)
class SimpleTerm(YAMLRoot):
    """
    A simple ontology term with an identifier and a label.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["SimpleTerm"]
    class_class_curie: ClassVar[str] = "rdid:SimpleTerm"
    class_name: ClassVar[str] = "SimpleTerm"
    class_model_uri: ClassVar[URIRef] = RDID.SimpleTerm

    id: Union[str, SimpleTermId] = None
    label: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.id):
            self.MissingRequiredField("id")
        if not isinstance(self.id, SimpleTermId):
            self.id = SimpleTermId(self.id)

        if self.label is not None and not isinstance(self.label, str):
            self.label = str(self.label)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class RareDiseaseCollection(YAMLRoot):
    """
    A collection of prioritised rare diseases.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["RareDiseaseCollection"]
    class_class_curie: ClassVar[str] = "rdid:RareDiseaseCollection"
    class_name: ClassVar[str] = "RareDiseaseCollection"
    class_model_uri: ClassVar[URIRef] = RDID.RareDiseaseCollection

    title: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    diseases: Optional[Union[dict[Union[str, RareDiseaseMondoId], Union[dict, "RareDisease"]], list[Union[dict, "RareDisease"]]]] = empty_dict()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.title is not None and not isinstance(self.title, str):
            self.title = str(self.title)

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        if self.version is not None and not isinstance(self.version, str):
            self.version = str(self.version)

        self._normalize_inlined_as_list(slot_name="diseases", slot_type=RareDisease, key_name="mondo_id", keyed=True)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class RareDisease(YAMLRoot):
    """
    A rare disease entry with prioritisation metadata.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["RareDisease"]
    class_class_curie: ClassVar[str] = "rdid:RareDisease"
    class_name: ClassVar[str] = "RareDisease"
    class_model_uri: ClassVar[URIRef] = RDID.RareDisease

    mondo_id: Union[str, RareDiseaseMondoId] = None
    mondo_label: str = None
    mondo_synonyms: Optional[Union[str, list[str]]] = empty_list()
    mondo_categories: Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]] = empty_dict()
    hpo_high_level_categories: Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]] = empty_dict()
    histopheno_categories: Optional[Union[str, list[str]]] = empty_list()
    keywords: Optional[Union[str, list[str]]] = empty_list()
    ontology_terminology_codes: Optional[Union[str, list[str]]] = empty_list()
    prevalence_category: Optional[Union[str, "PrevalenceCategoryEnum"]] = None
    misdiagnosis_bias: Optional[str] = None
    prevalence_per_100k_us: Optional[float] = None
    prioritization_category: Optional[Union[str, "PrioritizationCategoryEnum"]] = None
    justification_summary: Optional[Union[str, list[str]]] = empty_list()
    additional_justification: Optional[str] = None
    hpo_treatment_rank: Optional[float] = None
    curated_hpo_profiles: Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]] = empty_dict()
    mondo_category_body_system: Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]] = empty_dict()
    mondo_category_developmental: Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]] = empty_dict()
    mondo_category_etiologic: Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]] = empty_dict()
    mondo_category_genetic: Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]] = empty_dict()
    mondo_category_extrinsic: Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]] = empty_dict()
    mondo_category_molecular: Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]] = empty_dict()
    indications: Optional[Union[Union[dict, "DrugIndication"], list[Union[dict, "DrugIndication"]]]] = empty_list()
    research: Optional[Union[Union[dict, "DrugResearch"], list[Union[dict, "DrugResearch"]]]] = empty_list()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.mondo_id):
            self.MissingRequiredField("mondo_id")
        if not isinstance(self.mondo_id, RareDiseaseMondoId):
            self.mondo_id = RareDiseaseMondoId(self.mondo_id)

        if self._is_empty(self.mondo_label):
            self.MissingRequiredField("mondo_label")
        if not isinstance(self.mondo_label, str):
            self.mondo_label = str(self.mondo_label)

        if not isinstance(self.mondo_synonyms, list):
            self.mondo_synonyms = [self.mondo_synonyms] if self.mondo_synonyms is not None else []
        self.mondo_synonyms = [v if isinstance(v, str) else str(v) for v in self.mondo_synonyms]

        self._normalize_inlined_as_list(slot_name="mondo_categories", slot_type=SimpleTerm, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="hpo_high_level_categories", slot_type=SimpleTerm, key_name="id", keyed=True)

        if not isinstance(self.histopheno_categories, list):
            self.histopheno_categories = [self.histopheno_categories] if self.histopheno_categories is not None else []
        self.histopheno_categories = [v if isinstance(v, str) else str(v) for v in self.histopheno_categories]

        if not isinstance(self.keywords, list):
            self.keywords = [self.keywords] if self.keywords is not None else []
        self.keywords = [v if isinstance(v, str) else str(v) for v in self.keywords]

        if not isinstance(self.ontology_terminology_codes, list):
            self.ontology_terminology_codes = [self.ontology_terminology_codes] if self.ontology_terminology_codes is not None else []
        self.ontology_terminology_codes = [v if isinstance(v, str) else str(v) for v in self.ontology_terminology_codes]

        if self.prevalence_category is not None and not isinstance(self.prevalence_category, PrevalenceCategoryEnum):
            self.prevalence_category = PrevalenceCategoryEnum(self.prevalence_category)

        if self.misdiagnosis_bias is not None and not isinstance(self.misdiagnosis_bias, str):
            self.misdiagnosis_bias = str(self.misdiagnosis_bias)

        if self.prevalence_per_100k_us is not None and not isinstance(self.prevalence_per_100k_us, float):
            self.prevalence_per_100k_us = float(self.prevalence_per_100k_us)

        if self.prioritization_category is not None and not isinstance(self.prioritization_category, PrioritizationCategoryEnum):
            self.prioritization_category = PrioritizationCategoryEnum(self.prioritization_category)

        if not isinstance(self.justification_summary, list):
            self.justification_summary = [self.justification_summary] if self.justification_summary is not None else []
        self.justification_summary = [v if isinstance(v, str) else str(v) for v in self.justification_summary]

        if self.additional_justification is not None and not isinstance(self.additional_justification, str):
            self.additional_justification = str(self.additional_justification)

        if self.hpo_treatment_rank is not None and not isinstance(self.hpo_treatment_rank, float):
            self.hpo_treatment_rank = float(self.hpo_treatment_rank)

        self._normalize_inlined_as_list(slot_name="curated_hpo_profiles", slot_type=SimpleTerm, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="mondo_category_body_system", slot_type=SimpleTerm, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="mondo_category_developmental", slot_type=SimpleTerm, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="mondo_category_etiologic", slot_type=SimpleTerm, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="mondo_category_genetic", slot_type=SimpleTerm, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="mondo_category_extrinsic", slot_type=SimpleTerm, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="mondo_category_molecular", slot_type=SimpleTerm, key_name="id", keyed=True)

        self._normalize_inlined_as_list(slot_name="indications", slot_type=DrugIndication, key_name="drug_label", keyed=False)

        self._normalize_inlined_as_list(slot_name="research", slot_type=DrugResearch, key_name="drug_label", keyed=False)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class DrugIndication(YAMLRoot):
    """
    An approved drug indication for a disease.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["DrugIndication"]
    class_class_curie: ClassVar[str] = "rdid:DrugIndication"
    class_name: ClassVar[str] = "DrugIndication"
    class_model_uri: ClassVar[URIRef] = RDID.DrugIndication

    drug_label: str = None
    drug_id: Optional[str] = None
    evidence: Optional[Union[Union[dict, "RegulatoryEvidence"], list[Union[dict, "RegulatoryEvidence"]]]] = empty_list()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.drug_label):
            self.MissingRequiredField("drug_label")
        if not isinstance(self.drug_label, str):
            self.drug_label = str(self.drug_label)

        if self.drug_id is not None and not isinstance(self.drug_id, str):
            self.drug_id = str(self.drug_id)

        if not isinstance(self.evidence, list):
            self.evidence = [self.evidence] if self.evidence is not None else []
        self.evidence = [v if isinstance(v, RegulatoryEvidence) else RegulatoryEvidence(**as_dict(v)) for v in self.evidence]

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class RegulatoryEvidence(YAMLRoot):
    """
    Regulatory evidence for a drug indication.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["RegulatoryEvidence"]
    class_class_curie: ClassVar[str] = "rdid:RegulatoryEvidence"
    class_name: ClassVar[str] = "RegulatoryEvidence"
    class_model_uri: ClassVar[URIRef] = RDID.RegulatoryEvidence

    source_type: Optional[Union[str, "SourceTypeEnum"]] = None
    jurisdiction: Optional[str] = None
    explanation: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.source_type is not None and not isinstance(self.source_type, SourceTypeEnum):
            self.source_type = SourceTypeEnum(self.source_type)

        if self.jurisdiction is not None and not isinstance(self.jurisdiction, str):
            self.jurisdiction = str(self.jurisdiction)

        if self.explanation is not None and not isinstance(self.explanation, str):
            self.explanation = str(self.explanation)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class DrugResearch(YAMLRoot):
    """
    A drug or treatment research entry for a disease.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["DrugResearch"]
    class_class_curie: ClassVar[str] = "rdid:DrugResearch"
    class_name: ClassVar[str] = "DrugResearch"
    class_model_uri: ClassVar[URIRef] = RDID.DrugResearch

    drug_label: str = None
    evidence: Optional[Union[Union[dict, "Evidence"], list[Union[dict, "Evidence"]]]] = empty_list()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.drug_label):
            self.MissingRequiredField("drug_label")
        if not isinstance(self.drug_label, str):
            self.drug_label = str(self.drug_label)

        if not isinstance(self.evidence, list):
            self.evidence = [self.evidence] if self.evidence is not None else []
        self.evidence = [v if isinstance(v, Evidence) else Evidence(**as_dict(v)) for v in self.evidence]

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Evidence(YAMLRoot):
    """
    A single piece of evidence for a drug or treatment.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["Evidence"]
    class_class_curie: ClassVar[str] = "rdid:Evidence"
    class_name: ClassVar[str] = "Evidence"
    class_model_uri: ClassVar[URIRef] = RDID.Evidence

    source_type: Optional[Union[str, "SourceTypeEnum"]] = None
    reference: Optional[str] = None
    interpreted_text: Optional[str] = None
    confidence: Optional[Union[str, "ConfidenceEnum"]] = None
    evidence_source: Optional[Union[str, "EvidenceSourceEnum"]] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.source_type is not None and not isinstance(self.source_type, SourceTypeEnum):
            self.source_type = SourceTypeEnum(self.source_type)

        if self.reference is not None and not isinstance(self.reference, str):
            self.reference = str(self.reference)

        if self.interpreted_text is not None and not isinstance(self.interpreted_text, str):
            self.interpreted_text = str(self.interpreted_text)

        if self.confidence is not None and not isinstance(self.confidence, ConfidenceEnum):
            self.confidence = ConfidenceEnum(self.confidence)

        if self.evidence_source is not None and not isinstance(self.evidence_source, EvidenceSourceEnum):
            self.evidence_source = EvidenceSourceEnum(self.evidence_source)

        super().__post_init__(**kwargs)


# Enumerations
class PrevalenceCategoryEnum(EnumDefinitionImpl):
    """
    Prevalence category indicating whether the disease is low or high prevalence.
    """
    L = PermissibleValue(
        text="L",
        description="Low prevalence")
    H = PermissibleValue(
        text="H",
        description="High prevalence")
    H_star = PermissibleValue(
        text="H_star",
        description="High prevalence in some populations")
    H_uncertain = PermissibleValue(
        text="H_uncertain",
        description="Uncertain high prevalence")

    _defn = EnumDefinition(
        name="PrevalenceCategoryEnum",
        description="Prevalence category indicating whether the disease is low or high prevalence.",
    )

class PrioritizationCategoryEnum(EnumDefinitionImpl):
    """
    Category indicating the prioritization tier for the disease.
    """
    initial = PermissibleValue(
        text="initial",
        description="""First expert-based prioritisation of diseases with high potential for phenotypic characterization impact""")
    expanded = PermissibleValue(
        text="expanded",
        description="Extended set of diseases added after initial expert review to broaden coverage")

    _defn = EnumDefinition(
        name="PrioritizationCategoryEnum",
        description="Category indicating the prioritization tier for the disease.",
    )

class SourceTypeEnum(EnumDefinitionImpl):
    """
    Type of evidence source.
    """
    LITERATURE = PermissibleValue(
        text="LITERATURE",
        description="Published literature")
    DATABASE = PermissibleValue(
        text="DATABASE",
        description="Database or registry")
    REGULATORY = PermissibleValue(
        text="REGULATORY",
        description="Regulatory agency approval")

    _defn = EnumDefinition(
        name="SourceTypeEnum",
        description="Type of evidence source.",
    )

class ConfidenceEnum(EnumDefinitionImpl):
    """
    Confidence level of the evidence.
    """
    LOW = PermissibleValue(
        text="LOW",
        description="Low confidence")
    MEDIUM = PermissibleValue(
        text="MEDIUM",
        description="Medium confidence")
    HIGH = PermissibleValue(
        text="HIGH",
        description="High confidence")

    _defn = EnumDefinition(
        name="ConfidenceEnum",
        description="Confidence level of the evidence.",
    )

class EvidenceSourceEnum(EnumDefinitionImpl):
    """
    Category of evidence source.
    """
    HUMAN_CLINICAL = PermissibleValue(
        text="HUMAN_CLINICAL",
        description="Human clinical evidence")

    _defn = EnumDefinition(
        name="EvidenceSourceEnum",
        description="Category of evidence source.",
    )

# Slots
class slots:
    pass

slots.simpleTerm__id = Slot(uri=RDID.id, name="simpleTerm__id", curie=RDID.curie('id'),
                   model_uri=RDID.simpleTerm__id, domain=None, range=URIRef)

slots.simpleTerm__label = Slot(uri=RDID.label, name="simpleTerm__label", curie=RDID.curie('label'),
                   model_uri=RDID.simpleTerm__label, domain=None, range=Optional[str])

slots.rareDiseaseCollection__title = Slot(uri=RDID.title, name="rareDiseaseCollection__title", curie=RDID.curie('title'),
                   model_uri=RDID.rareDiseaseCollection__title, domain=None, range=Optional[str])

slots.rareDiseaseCollection__description = Slot(uri=RDID.description, name="rareDiseaseCollection__description", curie=RDID.curie('description'),
                   model_uri=RDID.rareDiseaseCollection__description, domain=None, range=Optional[str])

slots.rareDiseaseCollection__version = Slot(uri=RDID.version, name="rareDiseaseCollection__version", curie=RDID.curie('version'),
                   model_uri=RDID.rareDiseaseCollection__version, domain=None, range=Optional[str])

slots.rareDiseaseCollection__diseases = Slot(uri=RDID.diseases, name="rareDiseaseCollection__diseases", curie=RDID.curie('diseases'),
                   model_uri=RDID.rareDiseaseCollection__diseases, domain=None, range=Optional[Union[dict[Union[str, RareDiseaseMondoId], Union[dict, RareDisease]], list[Union[dict, RareDisease]]]])

slots.rareDisease__mondo_id = Slot(uri=RDID.mondo_id, name="rareDisease__mondo_id", curie=RDID.curie('mondo_id'),
                   model_uri=RDID.rareDisease__mondo_id, domain=None, range=URIRef,
                   pattern=re.compile(r'^MONDO:\d{7}$'))

slots.rareDisease__mondo_label = Slot(uri=RDID.mondo_label, name="rareDisease__mondo_label", curie=RDID.curie('mondo_label'),
                   model_uri=RDID.rareDisease__mondo_label, domain=None, range=str)

slots.rareDisease__mondo_synonyms = Slot(uri=RDID.mondo_synonyms, name="rareDisease__mondo_synonyms", curie=RDID.curie('mondo_synonyms'),
                   model_uri=RDID.rareDisease__mondo_synonyms, domain=None, range=Optional[Union[str, list[str]]])

slots.rareDisease__mondo_categories = Slot(uri=RDID.mondo_categories, name="rareDisease__mondo_categories", curie=RDID.curie('mondo_categories'),
                   model_uri=RDID.rareDisease__mondo_categories, domain=None, range=Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]])

slots.rareDisease__hpo_high_level_categories = Slot(uri=RDID.hpo_high_level_categories, name="rareDisease__hpo_high_level_categories", curie=RDID.curie('hpo_high_level_categories'),
                   model_uri=RDID.rareDisease__hpo_high_level_categories, domain=None, range=Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]])

slots.rareDisease__histopheno_categories = Slot(uri=RDID.histopheno_categories, name="rareDisease__histopheno_categories", curie=RDID.curie('histopheno_categories'),
                   model_uri=RDID.rareDisease__histopheno_categories, domain=None, range=Optional[Union[str, list[str]]])

slots.rareDisease__keywords = Slot(uri=RDID.keywords, name="rareDisease__keywords", curie=RDID.curie('keywords'),
                   model_uri=RDID.rareDisease__keywords, domain=None, range=Optional[Union[str, list[str]]])

slots.rareDisease__ontology_terminology_codes = Slot(uri=RDID.ontology_terminology_codes, name="rareDisease__ontology_terminology_codes", curie=RDID.curie('ontology_terminology_codes'),
                   model_uri=RDID.rareDisease__ontology_terminology_codes, domain=None, range=Optional[Union[str, list[str]]])

slots.rareDisease__prevalence_category = Slot(uri=RDID.prevalence_category, name="rareDisease__prevalence_category", curie=RDID.curie('prevalence_category'),
                   model_uri=RDID.rareDisease__prevalence_category, domain=None, range=Optional[Union[str, "PrevalenceCategoryEnum"]])

slots.rareDisease__misdiagnosis_bias = Slot(uri=RDID.misdiagnosis_bias, name="rareDisease__misdiagnosis_bias", curie=RDID.curie('misdiagnosis_bias'),
                   model_uri=RDID.rareDisease__misdiagnosis_bias, domain=None, range=Optional[str])

slots.rareDisease__prevalence_per_100k_us = Slot(uri=RDID.prevalence_per_100k_us, name="rareDisease__prevalence_per_100k_us", curie=RDID.curie('prevalence_per_100k_us'),
                   model_uri=RDID.rareDisease__prevalence_per_100k_us, domain=None, range=Optional[float])

slots.rareDisease__prioritization_category = Slot(uri=RDID.prioritization_category, name="rareDisease__prioritization_category", curie=RDID.curie('prioritization_category'),
                   model_uri=RDID.rareDisease__prioritization_category, domain=None, range=Optional[Union[str, "PrioritizationCategoryEnum"]])

slots.rareDisease__justification_summary = Slot(uri=RDID.justification_summary, name="rareDisease__justification_summary", curie=RDID.curie('justification_summary'),
                   model_uri=RDID.rareDisease__justification_summary, domain=None, range=Optional[Union[str, list[str]]])

slots.rareDisease__additional_justification = Slot(uri=RDID.additional_justification, name="rareDisease__additional_justification", curie=RDID.curie('additional_justification'),
                   model_uri=RDID.rareDisease__additional_justification, domain=None, range=Optional[str])

slots.rareDisease__hpo_treatment_rank = Slot(uri=RDID.hpo_treatment_rank, name="rareDisease__hpo_treatment_rank", curie=RDID.curie('hpo_treatment_rank'),
                   model_uri=RDID.rareDisease__hpo_treatment_rank, domain=None, range=Optional[float])

slots.rareDisease__curated_hpo_profiles = Slot(uri=RDID.curated_hpo_profiles, name="rareDisease__curated_hpo_profiles", curie=RDID.curie('curated_hpo_profiles'),
                   model_uri=RDID.rareDisease__curated_hpo_profiles, domain=None, range=Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]])

slots.rareDisease__mondo_category_body_system = Slot(uri=RDID.mondo_category_body_system, name="rareDisease__mondo_category_body_system", curie=RDID.curie('mondo_category_body_system'),
                   model_uri=RDID.rareDisease__mondo_category_body_system, domain=None, range=Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]])

slots.rareDisease__mondo_category_developmental = Slot(uri=RDID.mondo_category_developmental, name="rareDisease__mondo_category_developmental", curie=RDID.curie('mondo_category_developmental'),
                   model_uri=RDID.rareDisease__mondo_category_developmental, domain=None, range=Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]])

slots.rareDisease__mondo_category_etiologic = Slot(uri=RDID.mondo_category_etiologic, name="rareDisease__mondo_category_etiologic", curie=RDID.curie('mondo_category_etiologic'),
                   model_uri=RDID.rareDisease__mondo_category_etiologic, domain=None, range=Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]])

slots.rareDisease__mondo_category_genetic = Slot(uri=RDID.mondo_category_genetic, name="rareDisease__mondo_category_genetic", curie=RDID.curie('mondo_category_genetic'),
                   model_uri=RDID.rareDisease__mondo_category_genetic, domain=None, range=Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]])

slots.rareDisease__mondo_category_extrinsic = Slot(uri=RDID.mondo_category_extrinsic, name="rareDisease__mondo_category_extrinsic", curie=RDID.curie('mondo_category_extrinsic'),
                   model_uri=RDID.rareDisease__mondo_category_extrinsic, domain=None, range=Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]])

slots.rareDisease__mondo_category_molecular = Slot(uri=RDID.mondo_category_molecular, name="rareDisease__mondo_category_molecular", curie=RDID.curie('mondo_category_molecular'),
                   model_uri=RDID.rareDisease__mondo_category_molecular, domain=None, range=Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]])

slots.rareDisease__indications = Slot(uri=RDID.indications, name="rareDisease__indications", curie=RDID.curie('indications'),
                   model_uri=RDID.rareDisease__indications, domain=None, range=Optional[Union[Union[dict, DrugIndication], list[Union[dict, DrugIndication]]]])

slots.rareDisease__research = Slot(uri=RDID.research, name="rareDisease__research", curie=RDID.curie('research'),
                   model_uri=RDID.rareDisease__research, domain=None, range=Optional[Union[Union[dict, DrugResearch], list[Union[dict, DrugResearch]]]])

slots.drugIndication__drug_label = Slot(uri=RDID.drug_label, name="drugIndication__drug_label", curie=RDID.curie('drug_label'),
                   model_uri=RDID.drugIndication__drug_label, domain=None, range=str)

slots.drugIndication__drug_id = Slot(uri=RDID.drug_id, name="drugIndication__drug_id", curie=RDID.curie('drug_id'),
                   model_uri=RDID.drugIndication__drug_id, domain=None, range=Optional[str])

slots.drugIndication__evidence = Slot(uri=RDID.evidence, name="drugIndication__evidence", curie=RDID.curie('evidence'),
                   model_uri=RDID.drugIndication__evidence, domain=None, range=Optional[Union[Union[dict, RegulatoryEvidence], list[Union[dict, RegulatoryEvidence]]]])

slots.regulatoryEvidence__source_type = Slot(uri=RDID.source_type, name="regulatoryEvidence__source_type", curie=RDID.curie('source_type'),
                   model_uri=RDID.regulatoryEvidence__source_type, domain=None, range=Optional[Union[str, "SourceTypeEnum"]])

slots.regulatoryEvidence__jurisdiction = Slot(uri=RDID.jurisdiction, name="regulatoryEvidence__jurisdiction", curie=RDID.curie('jurisdiction'),
                   model_uri=RDID.regulatoryEvidence__jurisdiction, domain=None, range=Optional[str])

slots.regulatoryEvidence__explanation = Slot(uri=RDID.explanation, name="regulatoryEvidence__explanation", curie=RDID.curie('explanation'),
                   model_uri=RDID.regulatoryEvidence__explanation, domain=None, range=Optional[str])

slots.drugResearch__drug_label = Slot(uri=RDID.drug_label, name="drugResearch__drug_label", curie=RDID.curie('drug_label'),
                   model_uri=RDID.drugResearch__drug_label, domain=None, range=str)

slots.drugResearch__evidence = Slot(uri=RDID.evidence, name="drugResearch__evidence", curie=RDID.curie('evidence'),
                   model_uri=RDID.drugResearch__evidence, domain=None, range=Optional[Union[Union[dict, Evidence], list[Union[dict, Evidence]]]])

slots.evidence__source_type = Slot(uri=RDID.source_type, name="evidence__source_type", curie=RDID.curie('source_type'),
                   model_uri=RDID.evidence__source_type, domain=None, range=Optional[Union[str, "SourceTypeEnum"]])

slots.evidence__reference = Slot(uri=RDID.reference, name="evidence__reference", curie=RDID.curie('reference'),
                   model_uri=RDID.evidence__reference, domain=None, range=Optional[str])

slots.evidence__interpreted_text = Slot(uri=RDID.interpreted_text, name="evidence__interpreted_text", curie=RDID.curie('interpreted_text'),
                   model_uri=RDID.evidence__interpreted_text, domain=None, range=Optional[str])

slots.evidence__confidence = Slot(uri=RDID.confidence, name="evidence__confidence", curie=RDID.curie('confidence'),
                   model_uri=RDID.evidence__confidence, domain=None, range=Optional[Union[str, "ConfidenceEnum"]])

slots.evidence__evidence_source = Slot(uri=RDID.evidence_source, name="evidence__evidence_source", curie=RDID.curie('evidence_source'),
                   model_uri=RDID.evidence__evidence_source, domain=None, range=Optional[Union[str, "EvidenceSourceEnum"]])

