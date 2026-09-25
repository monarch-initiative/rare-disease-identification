# Auto generated from rare_disease_prioritisation.yaml by pythongen.py version: 0.0.1
# Generation date: 2026-09-25T14:23:05
# Schema: rare_disease_prioritisation
#
# id: https://w3id.org/rare-disease-identification
# description: Schema for prioritised rare diseases for phenotypic characterization, including drug-disease associations (indications, contraindications, research) merged from the MeDIC knowledge base.
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

from linkml_runtime.linkml_model.types import Boolean, Date, Float, Integer, String, Uri, Uriorcurie
from linkml_runtime.utils.metamodelcore import Bool, URI, URIorCURIE, XSDDate

metamodel_version = "1.7.0"
version = None

# Namespaces
HP = CurieNamespace('HP', 'http://purl.obolibrary.org/obo/HP_')
ICD10CM = CurieNamespace('ICD10CM', 'http://purl.bioontology.org/ontology/ICD10CM/')
MONDO = CurieNamespace('MONDO', 'http://purl.obolibrary.org/obo/MONDO_')
SNOMEDCT = CurieNamespace('SNOMEDCT', 'http://snomed.info/id/')
DCTERMS = CurieNamespace('dcterms', 'http://purl.org/dc/terms/')
INFORES = CurieNamespace('infores', 'https://w3id.org/information-resource-registry/')
LINKML = CurieNamespace('linkml', 'https://w3id.org/linkml/')
OA = CurieNamespace('oa', 'http://www.w3.org/ns/oa#')
RDID = CurieNamespace('rdid', 'https://w3id.org/rare-disease-identification/')
SKOS = CurieNamespace('skos', 'http://www.w3.org/2004/02/skos/core#')
DEFAULT_ = RDID


# Types

# Class references
class SimpleTermId(extended_str):
    pass


class RareDiseaseMondoId(extended_str):
    pass


class ValueSetEntryCode(URIorCURIE):
    pass


class ProxyEntryCode(ValueSetEntryCode):
    pass


class ExcludedCodeCode(URIorCURIE):
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
class Source(YAMLRoot):
    """
    A description of the source from which evidence was extracted.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["Source"]
    class_class_curie: ClassVar[str] = "rdid:Source"
    class_name: ClassVar[str] = "Source"
    class_model_uri: ClassVar[URIRef] = RDID.Source

    name: Optional[str] = None
    type: Optional[Union[str, "SourceTypeEnum"]] = None
    jurisdiction: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    file: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.name is not None and not isinstance(self.name, str):
            self.name = str(self.name)

        if self.type is not None and not isinstance(self.type, SourceTypeEnum):
            self.type = SourceTypeEnum(self.type)

        if self.jurisdiction is not None and not isinstance(self.jurisdiction, str):
            self.jurisdiction = str(self.jurisdiction)

        if self.url is not None and not isinstance(self.url, str):
            self.url = str(self.url)

        if self.description is not None and not isinstance(self.description, str):
            self.description = str(self.description)

        if self.file is not None and not isinstance(self.file, str):
            self.file = str(self.file)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Curator(YAMLRoot):
    """
    The agent (human, pipeline or AI) that produced the evidence record.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["Curator"]
    class_class_curie: ClassVar[str] = "rdid:Curator"
    class_name: ClassVar[str] = "Curator"
    class_model_uri: ClassVar[URIRef] = RDID.Curator

    name: Optional[str] = None
    curator_type: Optional[Union[str, "CuratorTypeEnum"]] = None
    curator_id: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.name is not None and not isinstance(self.name, str):
            self.name = str(self.name)

        if self.curator_type is not None and not isinstance(self.curator_type, CuratorTypeEnum):
            self.curator_type = CuratorTypeEnum(self.curator_type)

        if self.curator_id is not None and not isinstance(self.curator_id, str):
            self.curator_id = str(self.curator_id)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class AggregateConfidence(YAMLRoot):
    """
    MeDIC's rolled-up confidence for a whole drug-disease association, combining the per-assertion confidences across
    every source that produced the assertion.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["AggregateConfidence"]
    class_class_curie: ClassVar[str] = "rdid:AggregateConfidence"
    class_name: ClassVar[str] = "AggregateConfidence"
    class_model_uri: ClassVar[URIRef] = RDID.AggregateConfidence

    method: Optional[str] = None
    overall: Optional[float] = None
    n_assertions: Optional[int] = None
    n_sources: Optional[int] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.method is not None and not isinstance(self.method, str):
            self.method = str(self.method)

        if self.overall is not None and not isinstance(self.overall, float):
            self.overall = float(self.overall)

        if self.n_assertions is not None and not isinstance(self.n_assertions, int):
            self.n_assertions = int(self.n_assertions)

        if self.n_sources is not None and not isinstance(self.n_sources, int):
            self.n_sources = int(self.n_sources)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class RegulatoryStatus(YAMLRoot):
    """
    A regulatory market-authorisation record for a drug-disease relationship, recorded per authority. Multiple
    statuses can coexist (FDA, EMA, PMDA).
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["RegulatoryStatus"]
    class_class_curie: ClassVar[str] = "rdid:RegulatoryStatus"
    class_name: ClassVar[str] = "RegulatoryStatus"
    class_model_uri: ClassVar[URIRef] = RDID.RegulatoryStatus

    authority: Optional[Union[str, "RegulatoryAuthorityEnum"]] = None
    status: Optional[Union[str, "RegulatoryStatusEnum"]] = None
    approval_date: Optional[str] = None
    source_role: Optional[Union[str, "SourceRoleEnum"]] = None
    regulatory_document_url: Optional[str] = None
    source: Optional[str] = None
    source_document_url: Optional[str] = None
    setid: Optional[str] = None
    product_id: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.authority is not None and not isinstance(self.authority, RegulatoryAuthorityEnum):
            self.authority = RegulatoryAuthorityEnum(self.authority)

        if self.status is not None and not isinstance(self.status, RegulatoryStatusEnum):
            self.status = RegulatoryStatusEnum(self.status)

        if self.approval_date is not None and not isinstance(self.approval_date, str):
            self.approval_date = str(self.approval_date)

        if self.source_role is not None and not isinstance(self.source_role, SourceRoleEnum):
            self.source_role = SourceRoleEnum(self.source_role)

        if self.regulatory_document_url is not None and not isinstance(self.regulatory_document_url, str):
            self.regulatory_document_url = str(self.regulatory_document_url)

        if self.source is not None and not isinstance(self.source, str):
            self.source = str(self.source)

        if self.source_document_url is not None and not isinstance(self.source_document_url, str):
            self.source_document_url = str(self.source_document_url)

        if self.setid is not None and not isinstance(self.setid, str):
            self.setid = str(self.setid)

        if self.product_id is not None and not isinstance(self.product_id, str):
            self.product_id = str(self.product_id)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class Evidence(YAMLRoot):
    """
    A single piece of evidence supporting or refuting a drug-disease association.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["Evidence"]
    class_class_curie: ClassVar[str] = "rdid:Evidence"
    class_name: ClassVar[str] = "Evidence"
    class_model_uri: ClassVar[URIRef] = RDID.Evidence

    source: Optional[Union[dict, Source]] = None
    source_type: Optional[Union[str, "SourceTypeEnum"]] = None
    source_role: Optional[Union[str, "SourceRoleEnum"]] = None
    jurisdiction: Optional[str] = None
    reference: Optional[str] = None
    reference_title: Optional[str] = None
    page_or_section: Optional[str] = None
    source_document_url: Optional[str] = None
    original_drug_label: Optional[str] = None
    original_drug_id: Optional[str] = None
    original_disease_label: Optional[str] = None
    setid: Optional[str] = None
    document_id: Optional[str] = None
    product_id: Optional[str] = None
    snippet: Optional[str] = None
    explanation: Optional[str] = None
    support: Optional[str] = None
    confidence: Optional[Union[str, "ConfidenceEnum"]] = None
    confidence_drug: Optional[Union[str, "ConfidenceEnum"]] = None
    confidence_disease: Optional[Union[str, "ConfidenceEnum"]] = None
    confidence_association: Optional[Union[str, "ConfidenceEnum"]] = None
    evidence_source: Optional[Union[str, "EvidenceSourceEnum"]] = None
    approval_status: Optional[Union[str, "RegulatoryStatusEnum"]] = None
    approval_date: Optional[str] = None
    max_research_phase: Optional[str] = None
    curator: Optional[Union[dict, Curator]] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self.source is not None and not isinstance(self.source, Source):
            self.source = Source(**as_dict(self.source))

        if self.source_type is not None and not isinstance(self.source_type, SourceTypeEnum):
            self.source_type = SourceTypeEnum(self.source_type)

        if self.source_role is not None and not isinstance(self.source_role, SourceRoleEnum):
            self.source_role = SourceRoleEnum(self.source_role)

        if self.jurisdiction is not None and not isinstance(self.jurisdiction, str):
            self.jurisdiction = str(self.jurisdiction)

        if self.reference is not None and not isinstance(self.reference, str):
            self.reference = str(self.reference)

        if self.reference_title is not None and not isinstance(self.reference_title, str):
            self.reference_title = str(self.reference_title)

        if self.page_or_section is not None and not isinstance(self.page_or_section, str):
            self.page_or_section = str(self.page_or_section)

        if self.source_document_url is not None and not isinstance(self.source_document_url, str):
            self.source_document_url = str(self.source_document_url)

        if self.original_drug_label is not None and not isinstance(self.original_drug_label, str):
            self.original_drug_label = str(self.original_drug_label)

        if self.original_drug_id is not None and not isinstance(self.original_drug_id, str):
            self.original_drug_id = str(self.original_drug_id)

        if self.original_disease_label is not None and not isinstance(self.original_disease_label, str):
            self.original_disease_label = str(self.original_disease_label)

        if self.setid is not None and not isinstance(self.setid, str):
            self.setid = str(self.setid)

        if self.document_id is not None and not isinstance(self.document_id, str):
            self.document_id = str(self.document_id)

        if self.product_id is not None and not isinstance(self.product_id, str):
            self.product_id = str(self.product_id)

        if self.snippet is not None and not isinstance(self.snippet, str):
            self.snippet = str(self.snippet)

        if self.explanation is not None and not isinstance(self.explanation, str):
            self.explanation = str(self.explanation)

        if self.support is not None and not isinstance(self.support, str):
            self.support = str(self.support)

        if self.confidence is not None and not isinstance(self.confidence, ConfidenceEnum):
            self.confidence = ConfidenceEnum(self.confidence)

        if self.confidence_drug is not None and not isinstance(self.confidence_drug, ConfidenceEnum):
            self.confidence_drug = ConfidenceEnum(self.confidence_drug)

        if self.confidence_disease is not None and not isinstance(self.confidence_disease, ConfidenceEnum):
            self.confidence_disease = ConfidenceEnum(self.confidence_disease)

        if self.confidence_association is not None and not isinstance(self.confidence_association, ConfidenceEnum):
            self.confidence_association = ConfidenceEnum(self.confidence_association)

        if self.evidence_source is not None and not isinstance(self.evidence_source, EvidenceSourceEnum):
            self.evidence_source = EvidenceSourceEnum(self.evidence_source)

        if self.approval_status is not None and not isinstance(self.approval_status, RegulatoryStatusEnum):
            self.approval_status = RegulatoryStatusEnum(self.approval_status)

        if self.approval_date is not None and not isinstance(self.approval_date, str):
            self.approval_date = str(self.approval_date)

        if self.max_research_phase is not None and not isinstance(self.max_research_phase, str):
            self.max_research_phase = str(self.max_research_phase)

        if self.curator is not None and not isinstance(self.curator, Curator):
            self.curator = Curator(**as_dict(self.curator))

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class DrugAssociation(YAMLRoot):
    """
    A drug associated with a disease in a specific modality (indication, contraindication, research), carrying
    evidence and modality-specific metadata (regulatory status, curation status, ...).
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["DrugAssociation"]
    class_class_curie: ClassVar[str] = "rdid:DrugAssociation"
    class_name: ClassVar[str] = "DrugAssociation"
    class_model_uri: ClassVar[URIRef] = RDID.DrugAssociation

    drug_label: str = None
    drug_id: Optional[str] = None
    relationship_type: Optional[Union[str, "RelationshipTypeEnum"]] = None
    reliability: Optional[Union[str, "ConfidenceEnum"]] = None
    confidence: Optional[Union[dict, AggregateConfidence]] = None
    is_allergen: Optional[Union[bool, Bool]] = None
    is_diagnostic_agent: Optional[Union[bool, Bool]] = None
    regulatory_status: Optional[Union[Union[dict, RegulatoryStatus], list[Union[dict, RegulatoryStatus]]]] = empty_list()
    curation_status: Optional[Union[str, "CurationStatusEnum"]] = None
    curation_date: Optional[str] = None
    curator: Optional[Union[dict, Curator]] = None
    deep_research_used: Optional[Union[bool, Bool]] = None
    notes: Optional[str] = None
    evidence: Optional[Union[Union[dict, Evidence], list[Union[dict, Evidence]]]] = empty_list()

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.drug_label):
            self.MissingRequiredField("drug_label")
        if not isinstance(self.drug_label, str):
            self.drug_label = str(self.drug_label)

        if self.drug_id is not None and not isinstance(self.drug_id, str):
            self.drug_id = str(self.drug_id)

        if self.relationship_type is not None and not isinstance(self.relationship_type, RelationshipTypeEnum):
            self.relationship_type = RelationshipTypeEnum(self.relationship_type)

        if self.reliability is not None and not isinstance(self.reliability, ConfidenceEnum):
            self.reliability = ConfidenceEnum(self.reliability)

        if self.confidence is not None and not isinstance(self.confidence, AggregateConfidence):
            self.confidence = AggregateConfidence(**as_dict(self.confidence))

        if self.is_allergen is not None and not isinstance(self.is_allergen, Bool):
            self.is_allergen = Bool(self.is_allergen)

        if self.is_diagnostic_agent is not None and not isinstance(self.is_diagnostic_agent, Bool):
            self.is_diagnostic_agent = Bool(self.is_diagnostic_agent)

        if not isinstance(self.regulatory_status, list):
            self.regulatory_status = [self.regulatory_status] if self.regulatory_status is not None else []
        self.regulatory_status = [v if isinstance(v, RegulatoryStatus) else RegulatoryStatus(**as_dict(v)) for v in self.regulatory_status]

        if self.curation_status is not None and not isinstance(self.curation_status, CurationStatusEnum):
            self.curation_status = CurationStatusEnum(self.curation_status)

        if self.curation_date is not None and not isinstance(self.curation_date, str):
            self.curation_date = str(self.curation_date)

        if self.curator is not None and not isinstance(self.curator, Curator):
            self.curator = Curator(**as_dict(self.curator))

        if self.deep_research_used is not None and not isinstance(self.deep_research_used, Bool):
            self.deep_research_used = Bool(self.deep_research_used)

        if self.notes is not None and not isinstance(self.notes, str):
            self.notes = str(self.notes)

        if not isinstance(self.evidence, list):
            self.evidence = [self.evidence] if self.evidence is not None else []
        self.evidence = [v if isinstance(v, Evidence) else Evidence(**as_dict(v)) for v in self.evidence]

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
    dismech_url: Optional[Union[str, URI]] = None
    work_capacity: Optional[Union[dict, "FunctionalCapacityAssessment"]] = None
    care_dependence: Optional[Union[dict, "FunctionalCapacityAssessment"]] = None
    hpo_high_level_categories: Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]] = empty_dict()
    histopheno_categories: Optional[Union[str, list[str]]] = empty_list()
    keywords: Optional[Union[str, list[str]]] = empty_list()
    ontology_terminology_codes: Optional[Union[str, list[str]]] = empty_list()
    value_sets: Optional[Union[Union[dict, "TerminologyValueSet"], list[Union[dict, "TerminologyValueSet"]]]] = empty_list()
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
    indications: Optional[Union[Union[dict, DrugAssociation], list[Union[dict, DrugAssociation]]]] = empty_list()
    contraindications: Optional[Union[Union[dict, DrugAssociation], list[Union[dict, DrugAssociation]]]] = empty_list()
    research: Optional[Union[Union[dict, DrugAssociation], list[Union[dict, DrugAssociation]]]] = empty_list()

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

        if self.dismech_url is not None and not isinstance(self.dismech_url, URI):
            self.dismech_url = URI(self.dismech_url)

        if self.work_capacity is not None and not isinstance(self.work_capacity, FunctionalCapacityAssessment):
            self.work_capacity = FunctionalCapacityAssessment(**as_dict(self.work_capacity))

        if self.care_dependence is not None and not isinstance(self.care_dependence, FunctionalCapacityAssessment):
            self.care_dependence = FunctionalCapacityAssessment(**as_dict(self.care_dependence))

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

        self._normalize_inlined_as_list(slot_name="value_sets", slot_type=TerminologyValueSet, key_name="terminology", keyed=False)

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

        self._normalize_inlined_as_list(slot_name="indications", slot_type=DrugAssociation, key_name="drug_label", keyed=False)

        self._normalize_inlined_as_list(slot_name="contraindications", slot_type=DrugAssociation, key_name="drug_label", keyed=False)

        self._normalize_inlined_as_list(slot_name="research", slot_type=DrugAssociation, key_name="drug_label", keyed=False)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class FunctionalCapacityEvidence(YAMLRoot):
    """
    One evidence line. Flattened SEPIO EvidenceLine: what kind of evidence, which way it points, how strong, and the
    item itself.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["FunctionalCapacityEvidence"]
    class_class_curie: ClassVar[str] = "rdid:FunctionalCapacityEvidence"
    class_name: ClassVar[str] = "FunctionalCapacityEvidence"
    class_model_uri: ClassVar[URIRef] = RDID.FunctionalCapacityEvidence

    lane: Union[str, "EvidenceLaneEnum"] = None
    strength: Union[str, "EvidenceStrengthEnum"] = None
    reference: Union[str, URIorCURIE] = None
    explanation: str = None
    direction: Union[str, "EvidenceDirectionEnum"] = 'SUPPORTS'
    reference_title: Optional[str] = None
    quote: Optional[str] = None
    quote_verified: Optional[Union[bool, Bool]] = None
    source_statement: Optional[str] = None
    population: Optional[str] = None
    eco_code: Optional[Union[str, URIorCURIE]] = None
    curator: Optional[str] = None
    curator_type: Optional[Union[str, "CuratorTypeEnum2"]] = None
    retrieved_on: Optional[Union[str, XSDDate]] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.lane):
            self.MissingRequiredField("lane")
        if not isinstance(self.lane, EvidenceLaneEnum):
            self.lane = EvidenceLaneEnum(self.lane)

        if self._is_empty(self.direction):
            self.MissingRequiredField("direction")
        if not isinstance(self.direction, EvidenceDirectionEnum):
            self.direction = getattr(EvidenceDirectionEnum, self.direction)

        if self._is_empty(self.strength):
            self.MissingRequiredField("strength")
        if not isinstance(self.strength, EvidenceStrengthEnum):
            self.strength = EvidenceStrengthEnum(self.strength)

        if self._is_empty(self.reference):
            self.MissingRequiredField("reference")
        if not isinstance(self.reference, URIorCURIE):
            self.reference = URIorCURIE(self.reference)

        if self._is_empty(self.explanation):
            self.MissingRequiredField("explanation")
        if not isinstance(self.explanation, str):
            self.explanation = str(self.explanation)

        if self.reference_title is not None and not isinstance(self.reference_title, str):
            self.reference_title = str(self.reference_title)

        if self.quote is not None and not isinstance(self.quote, str):
            self.quote = str(self.quote)

        if self.quote_verified is not None and not isinstance(self.quote_verified, Bool):
            self.quote_verified = Bool(self.quote_verified)

        if self.source_statement is not None and not isinstance(self.source_statement, str):
            self.source_statement = str(self.source_statement)

        if self.population is not None and not isinstance(self.population, str):
            self.population = str(self.population)

        if self.eco_code is not None and not isinstance(self.eco_code, URIorCURIE):
            self.eco_code = URIorCURIE(self.eco_code)

        if self.curator is not None and not isinstance(self.curator, str):
            self.curator = str(self.curator)

        if self.curator_type is not None and not isinstance(self.curator_type, CuratorTypeEnum2):
            self.curator_type = CuratorTypeEnum2(self.curator_type)

        if self.retrieved_on is not None and not isinstance(self.retrieved_on, XSDDate):
            self.retrieved_on = XSDDate(self.retrieved_on)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class FunctionalCapacityAssessment(YAMLRoot):
    """
    One curated capacity assessment for one disease. Either work capacity or care dependence - the two are separate
    assessments and are not derived from each other.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["FunctionalCapacityAssessment"]
    class_class_curie: ClassVar[str] = "rdid:FunctionalCapacityAssessment"
    class_name: ClassVar[str] = "FunctionalCapacityAssessment"
    class_model_uri: ClassVar[URIRef] = RDID.FunctionalCapacityAssessment

    impairment: Union[str, "ImpairmentLevelEnum"] = None
    care_context: Union[str, "CareContextEnum"] = None
    rationale: str = None
    curation_status: Union[str, "FCCurationStatusEnum"] = 'UNREVIEWED'
    score: Optional[float] = None
    score_method: Optional[str] = None
    score_version: Optional[str] = None
    model_confidence: Optional[int] = None
    life_stage: Optional[Union[str, "LifeStageEnum"]] = None
    evidence: Optional[Union[Union[dict, FunctionalCapacityEvidence], list[Union[dict, FunctionalCapacityEvidence]]]] = empty_list()
    claims_selectable: Optional[Union[bool, Bool]] = None
    icd10cm_codes: Optional[Union[Union[str, URIorCURIE], list[Union[str, URIorCURIE]]]] = empty_list()
    assessed_by: Optional[Union[str, URIorCURIE]] = None
    assessed_on: Optional[Union[str, XSDDate]] = None
    notes: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.impairment):
            self.MissingRequiredField("impairment")
        if not isinstance(self.impairment, ImpairmentLevelEnum):
            self.impairment = ImpairmentLevelEnum(self.impairment)

        if self._is_empty(self.care_context):
            self.MissingRequiredField("care_context")
        if not isinstance(self.care_context, CareContextEnum):
            self.care_context = CareContextEnum(self.care_context)

        if self._is_empty(self.rationale):
            self.MissingRequiredField("rationale")
        if not isinstance(self.rationale, str):
            self.rationale = str(self.rationale)

        if self._is_empty(self.curation_status):
            self.MissingRequiredField("curation_status")
        if not isinstance(self.curation_status, FCCurationStatusEnum):
            self.curation_status = getattr(FCCurationStatusEnum, self.curation_status)

        if self.score is not None and not isinstance(self.score, float):
            self.score = float(self.score)

        if self.score_method is not None and not isinstance(self.score_method, str):
            self.score_method = str(self.score_method)

        if self.score_version is not None and not isinstance(self.score_version, str):
            self.score_version = str(self.score_version)

        if self.model_confidence is not None and not isinstance(self.model_confidence, int):
            self.model_confidence = int(self.model_confidence)

        if self.life_stage is not None and not isinstance(self.life_stage, LifeStageEnum):
            self.life_stage = LifeStageEnum(self.life_stage)

        self._normalize_inlined_as_list(slot_name="evidence", slot_type=FunctionalCapacityEvidence, key_name="lane", keyed=False)

        if self.claims_selectable is not None and not isinstance(self.claims_selectable, Bool):
            self.claims_selectable = Bool(self.claims_selectable)

        if not isinstance(self.icd10cm_codes, list):
            self.icd10cm_codes = [self.icd10cm_codes] if self.icd10cm_codes is not None else []
        self.icd10cm_codes = [v if isinstance(v, URIorCURIE) else URIorCURIE(v) for v in self.icd10cm_codes]

        if self.assessed_by is not None and not isinstance(self.assessed_by, URIorCURIE):
            self.assessed_by = URIorCURIE(self.assessed_by)

        if self.assessed_on is not None and not isinstance(self.assessed_on, XSDDate):
            self.assessed_on = XSDDate(self.assessed_on)

        if self.notes is not None and not isinstance(self.notes, str):
            self.notes = str(self.notes)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ValueSetEntry(YAMLRoot):
    """
    One code in a disease's value set, with the Mondo assertion it came from and the codes a query should actually use.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["ValueSetEntry"]
    class_class_curie: ClassVar[str] = "rdid:ValueSetEntry"
    class_name: ClassVar[str] = "ValueSetEntry"
    class_model_uri: ClassVar[URIRef] = RDID.ValueSetEntry

    code: Union[str, ValueSetEntryCode] = None
    label: str = None
    provenance: Union[str, "ValueSetProvenanceEnum"] = None
    expanded_codes: Optional[Union[Union[str, URIorCURIE], list[Union[str, URIorCURIE]]]] = empty_list()
    via_mondo_id: Optional[str] = None
    via_mondo_label: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.code):
            self.MissingRequiredField("code")
        if not isinstance(self.code, ValueSetEntryCode):
            self.code = ValueSetEntryCode(self.code)

        if self._is_empty(self.label):
            self.MissingRequiredField("label")
        if not isinstance(self.label, str):
            self.label = str(self.label)

        if self._is_empty(self.provenance):
            self.MissingRequiredField("provenance")
        if not isinstance(self.provenance, ValueSetProvenanceEnum):
            self.provenance = ValueSetProvenanceEnum(self.provenance)

        if not isinstance(self.expanded_codes, list):
            self.expanded_codes = [self.expanded_codes] if self.expanded_codes is not None else []
        self.expanded_codes = [v if isinstance(v, URIorCURIE) else URIorCURIE(v) for v in self.expanded_codes]

        if self.via_mondo_id is not None and not isinstance(self.via_mondo_id, str):
            self.via_mondo_id = str(self.via_mondo_id)

        if self.via_mondo_label is not None and not isinstance(self.via_mondo_label, str):
            self.via_mondo_label = str(self.via_mondo_label)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ProxyEntry(ValueSetEntry):
    """
    A code broader than the disease. Pulling it returns a population the disease is a minority of, so it is a
    candidate list needing a second filter, never a case definition.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["ProxyEntry"]
    class_class_curie: ClassVar[str] = "rdid:ProxyEntry"
    class_name: ClassVar[str] = "ProxyEntry"
    class_model_uri: ClassVar[URIRef] = RDID.ProxyEntry

    code: Union[str, ProxyEntryCode] = None
    label: str = None
    provenance: Union[str, "ValueSetProvenanceEnum"] = None
    basis: Union[str, "ProxyBasisEnum"] = None
    comment: str = None
    approximate_cohort_size: Optional[int] = None
    cohort_size_source: Optional[str] = None
    curator: Optional[Union[str, URIorCURIE]] = None
    curation_date: Optional[Union[str, XSDDate]] = None
    upstream_request: Optional[Union[str, URIorCURIE]] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.code):
            self.MissingRequiredField("code")
        if not isinstance(self.code, ProxyEntryCode):
            self.code = ProxyEntryCode(self.code)

        if self._is_empty(self.basis):
            self.MissingRequiredField("basis")
        if not isinstance(self.basis, ProxyBasisEnum):
            self.basis = ProxyBasisEnum(self.basis)

        if self._is_empty(self.comment):
            self.MissingRequiredField("comment")
        if not isinstance(self.comment, str):
            self.comment = str(self.comment)

        if self.approximate_cohort_size is not None and not isinstance(self.approximate_cohort_size, int):
            self.approximate_cohort_size = int(self.approximate_cohort_size)

        if self.cohort_size_source is not None and not isinstance(self.cohort_size_source, str):
            self.cohort_size_source = str(self.cohort_size_source)

        if self.curator is not None and not isinstance(self.curator, URIorCURIE):
            self.curator = URIorCURIE(self.curator)

        if self.curation_date is not None and not isinstance(self.curation_date, XSDDate):
            self.curation_date = XSDDate(self.curation_date)

        if self.upstream_request is not None and not isinstance(self.upstream_request, URIorCURIE):
            self.upstream_request = URIorCURIE(self.upstream_request)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class ExcludedCode(YAMLRoot):
    """
    A code ruled out of this disease's value set, with the reason.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["ExcludedCode"]
    class_class_curie: ClassVar[str] = "rdid:ExcludedCode"
    class_name: ClassVar[str] = "ExcludedCode"
    class_model_uri: ClassVar[URIRef] = RDID.ExcludedCode

    code: Union[str, ExcludedCodeCode] = None
    reason: str = None
    label: Optional[str] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.code):
            self.MissingRequiredField("code")
        if not isinstance(self.code, ExcludedCodeCode):
            self.code = ExcludedCodeCode(self.code)

        if self._is_empty(self.reason):
            self.MissingRequiredField("reason")
        if not isinstance(self.reason, str):
            self.reason = str(self.reason)

        if self.label is not None and not isinstance(self.label, str):
            self.label = str(self.label)

        super().__post_init__(**kwargs)


@dataclass(repr=False)
class TerminologyValueSet(YAMLRoot):
    """
    The three tiers for one disease in one terminology. What each returns when you query it:
    `exact` - the disease, no more and no less.
    `narrower` - a subset. Everyone returned has the disease; you miss people. The error is invisible in the data,
    which is the reason to take the whole subtree rather than cherry-pick leaves.
    `proxy` - a superset. Recall is high, precision is not.
    `exact` and `narrower` are regenerated from Mondo on every build and are not hand-editable. `proxy` is the only
    curated tier, and even there the SUBSUMPTION and TERMINOLOGY_INDEX entries should migrate to Mondo over time,
    leaving only CODING_CONVENTION behind.
    """
    _inherited_slots: ClassVar[list[str]] = []

    class_class_uri: ClassVar[URIRef] = RDID["TerminologyValueSet"]
    class_class_curie: ClassVar[str] = "rdid:TerminologyValueSet"
    class_name: ClassVar[str] = "TerminologyValueSet"
    class_model_uri: ClassVar[URIRef] = RDID.TerminologyValueSet

    terminology: Union[str, "TerminologyEnum"] = None
    exact: Optional[Union[dict[Union[str, ValueSetEntryCode], Union[dict, ValueSetEntry]], list[Union[dict, ValueSetEntry]]]] = empty_dict()
    narrower: Optional[Union[dict[Union[str, ValueSetEntryCode], Union[dict, ValueSetEntry]], list[Union[dict, ValueSetEntry]]]] = empty_dict()
    proxy: Optional[Union[dict[Union[str, ProxyEntryCode], Union[dict, ProxyEntry]], list[Union[dict, ProxyEntry]]]] = empty_dict()
    excluded: Optional[Union[dict[Union[str, ExcludedCodeCode], Union[dict, ExcludedCode]], list[Union[dict, ExcludedCode]]]] = empty_dict()
    mondo_version: Optional[str] = None
    terminology_version: Optional[str] = None
    generated_on: Optional[Union[str, XSDDate]] = None

    def __post_init__(self, *_: str, **kwargs: Any):
        if self._is_empty(self.terminology):
            self.MissingRequiredField("terminology")
        if not isinstance(self.terminology, TerminologyEnum):
            self.terminology = TerminologyEnum(self.terminology)

        self._normalize_inlined_as_list(slot_name="exact", slot_type=ValueSetEntry, key_name="code", keyed=True)

        self._normalize_inlined_as_list(slot_name="narrower", slot_type=ValueSetEntry, key_name="code", keyed=True)

        self._normalize_inlined_as_list(slot_name="proxy", slot_type=ProxyEntry, key_name="code", keyed=True)

        self._normalize_inlined_as_list(slot_name="excluded", slot_type=ExcludedCode, key_name="code", keyed=True)

        if self.mondo_version is not None and not isinstance(self.mondo_version, str):
            self.mondo_version = str(self.mondo_version)

        if self.terminology_version is not None and not isinstance(self.terminology_version, str):
            self.terminology_version = str(self.terminology_version)

        if self.generated_on is not None and not isinstance(self.generated_on, XSDDate):
            self.generated_on = XSDDate(self.generated_on)

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

class RelationshipTypeEnum(EnumDefinitionImpl):
    """
    Type of drug-disease relationship.
    """
    INDICATION = PermissibleValue(
        text="INDICATION",
        description="Drug is indicated for the disease")
    CONTRAINDICATION = PermissibleValue(
        text="CONTRAINDICATION",
        description="Drug is contraindicated for the disease")
    ADVERSE_EVENT = PermissibleValue(
        text="ADVERSE_EVENT",
        description="Drug is associated with an adverse event in the context of the disease")
    RESEARCH = PermissibleValue(
        text="RESEARCH",
        description="Drug is investigated for the disease (research / off-label)")

    _defn = EnumDefinition(
        name="RelationshipTypeEnum",
        description="Type of drug-disease relationship.",
    )

class SourceRoleEnum(EnumDefinitionImpl):
    """
    Whether a source is the primary canonical evidence record (e.g. official EMA EPAR) or an intermediary source (e.g.
    a DailyMed label that mirrors the FDA approval).
    """
    PRIMARY = PermissibleValue(
        text="PRIMARY",
        description="Primary canonical source for the assertion")
    INTERMEDIARY = PermissibleValue(
        text="INTERMEDIARY",
        description="Intermediary source repeating or fallback to a primary source")

    _defn = EnumDefinition(
        name="SourceRoleEnum",
        description="""Whether a source is the primary canonical evidence record (e.g. official EMA EPAR) or an intermediary source (e.g. a DailyMed label that mirrors the FDA approval).""",
    )

class RegulatoryAuthorityEnum(EnumDefinitionImpl):
    """
    Regulatory authority granting approval / market authorisation.
    """
    FDA = PermissibleValue(
        text="FDA",
        description="U.S. Food and Drug Administration")
    EMA = PermissibleValue(
        text="EMA",
        description="European Medicines Agency")
    PMDA = PermissibleValue(
        text="PMDA",
        description="Japan Pharmaceuticals and Medical Devices Agency")
    CDSCO = PermissibleValue(
        text="CDSCO",
        description="India Central Drugs Standard Control Organisation")
    OTHER = PermissibleValue(
        text="OTHER",
        description="Other regulator")

    _defn = EnumDefinition(
        name="RegulatoryAuthorityEnum",
        description="Regulatory authority granting approval / market authorisation.",
    )

class RegulatoryStatusEnum(EnumDefinitionImpl):
    """
    Regulatory approval status.
    """
    APPROVED = PermissibleValue(
        text="APPROVED",
        description="Approved for marketing")
    WITHDRAWN = PermissibleValue(
        text="WITHDRAWN",
        description="Approval withdrawn")
    DISCONTINUED = PermissibleValue(
        text="DISCONTINUED",
        description="Discontinued")
    INVESTIGATIONAL = PermissibleValue(
        text="INVESTIGATIONAL",
        description="Under investigation")
    OFF_LABEL = PermissibleValue(
        text="OFF_LABEL",
        description="Used off-label")

    _defn = EnumDefinition(
        name="RegulatoryStatusEnum",
        description="Regulatory approval status.",
    )

class CurationStatusEnum(EnumDefinitionImpl):
    """
    Curation lifecycle status of a drug-disease association.
    """
    DRAFT = PermissibleValue(
        text="DRAFT",
        description="Draft / unreviewed")
    IN_REVIEW = PermissibleValue(
        text="IN_REVIEW",
        description="Under expert review")
    APPROVED = PermissibleValue(
        text="APPROVED",
        description="Curator-approved")
    REJECTED = PermissibleValue(
        text="REJECTED",
        description="Curator-rejected")

    _defn = EnumDefinition(
        name="CurationStatusEnum",
        description="Curation lifecycle status of a drug-disease association.",
    )

class CuratorTypeEnum(EnumDefinitionImpl):
    """
    Type of curator that produced an evidence record.
    """
    AI_AGENT = PermissibleValue(
        text="AI_AGENT",
        description="AI agent (LLM-based or other)")
    PIPELINE = PermissibleValue(
        text="PIPELINE",
        description="Automated extraction pipeline")
    HUMAN = PermissibleValue(
        text="HUMAN",
        description="Human curator")

    _defn = EnumDefinition(
        name="CuratorTypeEnum",
        description="Type of curator that produced an evidence record.",
    )

class SourceTypeEnum(EnumDefinitionImpl):
    """
    Broad category of evidence source.
    """
    REGULATORY = PermissibleValue(
        text="REGULATORY",
        description="Regulatory agency document (label, EPAR, etc.)")
    LITERATURE = PermissibleValue(
        text="LITERATURE",
        description="Published literature (PMID, PMC, journal article)")
    GUIDELINE = PermissibleValue(
        text="GUIDELINE",
        description="Clinical practice guideline")
    DATABASE = PermissibleValue(
        text="DATABASE",
        description="Curated database or registry")
    POST_MARKET = PermissibleValue(
        text="POST_MARKET",
        description="Post-market surveillance / real-world evidence")

    _defn = EnumDefinition(
        name="SourceTypeEnum",
        description="Broad category of evidence source.",
    )

class ConfidenceEnum(EnumDefinitionImpl):
    """
    Confidence level for an evidence record.
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
        description="Confidence level for an evidence record.",
    )

class EvidenceSourceEnum(EnumDefinitionImpl):
    """
    Provenance of the underlying evidence.
    """
    HUMAN_CLINICAL = PermissibleValue(
        text="HUMAN_CLINICAL",
        description="Human clinical evidence (trial, case report)")
    MODEL_ORGANISM = PermissibleValue(
        text="MODEL_ORGANISM",
        description="Animal / model organism evidence")
    IN_VITRO = PermissibleValue(
        text="IN_VITRO",
        description="In vitro / cell-based evidence")
    COMPUTATIONAL = PermissibleValue(
        text="COMPUTATIONAL",
        description="Computational / in silico evidence")
    OTHER = PermissibleValue(
        text="OTHER",
        description="Other / unspecified provenance")

    _defn = EnumDefinition(
        name="EvidenceSourceEnum",
        description="Provenance of the underlying evidence.",
    )

class ImpairmentLevelEnum(EnumDefinitionImpl):
    """
    How much the disease impairs the capacity in question, for a typical affected person under standard of care.
    Mirrors Orphanet's severity bands (Low / Moderate / Severe / Complete) so the two can be compared.
    """
    NONE = PermissibleValue(
        text="NONE",
        description="Typical affected people are not meaningfully impaired in this capacity.")
    MILD = PermissibleValue(
        text="MILD",
        description="Harder, but most affected people manage without help or accommodation.")
    SUBSTANTIAL = PermissibleValue(
        text="SUBSTANTIAL",
        description="""A serious barrier. A substantial proportion (>=30%) need accommodation, reduced hours, or regular assistance.""")
    TOTAL = PermissibleValue(
        text="TOTAL",
        description="""A substantial proportion (>=30%) cannot sustain competitive employment at all, or need daily personal assistance from another person.""")
    VARIABLE = PermissibleValue(
        text="VARIABLE",
        description="""Genuinely varies by subtype, stage, or treatment response; no single level is representative. Use the rationale to say what it varies with.""")
    NOT_APPLICABLE = PermissibleValue(
        text="NOT_APPLICABLE",
        description="""The question does not arise. Chiefly: work capacity for a disease that is near-universally lethal before working age.""")
    UNKNOWN = PermissibleValue(
        text="UNKNOWN",
        description="Not yet assessed, or assessed and found to have no usable evidence.")

    _defn = EnumDefinition(
        name="ImpairmentLevelEnum",
        description="""How much the disease impairs the capacity in question, for a typical affected person under standard of care. Mirrors Orphanet's severity bands (Low / Moderate / Severe / Complete) so the two can be compared.""",
    )

class CareContextEnum(EnumDefinitionImpl):
    """
    Which course the assessment describes. Required, because untreated natural history and treated course diverge
    sharply for screened metabolic disease and this is the single largest source of false positives.
    """
    STANDARD_OF_CARE_TREATED = PermissibleValue(
        text="STANDARD_OF_CARE_TREATED",
        description="The course under current standard of care. The only context that may inform policy use.")
    UNTREATED_NATURAL_HISTORY = PermissibleValue(
        text="UNTREATED_NATURAL_HISTORY",
        description="The untreated course. Must never be presented as the current expectation.")
    TREATMENT_REFRACTORY = PermissibleValue(
        text="TREATMENT_REFRACTORY",
        description="The course in people who do not respond to standard treatment.")
    UNKNOWN = PermissibleValue(
        text="UNKNOWN",
        description="The source does not say which course it describes.")

    _defn = EnumDefinition(
        name="CareContextEnum",
        description="""Which course the assessment describes. Required, because untreated natural history and treated course diverge sharply for screened metabolic disease and this is the single largest source of false positives.""",
    )

class LifeStageEnum(EnumDefinitionImpl):
    """
    The life stage the assessment applies to.
    """
    CONGENITAL = PermissibleValue(
        text="CONGENITAL",
        description="Present from birth")
    PAEDIATRIC = PermissibleValue(
        text="PAEDIATRIC",
        description="Onset and impact in childhood")
    ADULT_ONSET = PermissibleValue(
        text="ADULT_ONSET",
        description="Onset in adulthood")
    PROGRESSIVE_LATE_STAGE = PermissibleValue(
        text="PROGRESSIVE_LATE_STAGE",
        description="Applies only once the disease has progressed")
    ANY = PermissibleValue(
        text="ANY",
        description="Applies across life stages")
    PRE_MANIFEST_EXCLUDED = PermissibleValue(
        text="PRE_MANIFEST_EXCLUDED",
        description="Explicitly excludes pre-manifest carriers")

    _defn = EnumDefinition(
        name="LifeStageEnum",
        description="The life stage the assessment applies to.",
    )

class EvidenceLaneEnum(EnumDefinitionImpl):
    """
    The independent lanes evidence can come from. A well-curated assessment draws on more than one, and lanes that
    disagree are recorded, not reconciled away.
    Policy evidence is split in two because a federal disability adjudication and a state Medicaid frailty code are
    genuinely independent decisions - different statutes, different bodies, different qualifying tests - and
    collapsing them into one lane made concordant government determinations look like a single source.
    """
    EXPERT_DATABASE = PermissibleValue(
        text="EXPERT_DATABASE",
        description="""A curated database rating functional consequence directly - chiefly Orphanet's functional-consequences dataset, which names its validating expert.""")
    FEDERAL_POLICY_LIST = PermissibleValue(
        text="FEDERAL_POLICY_LIST",
        description="""A national-level determination that this disease qualifies, made by the body that administers the benefit - chiefly the SSA Compassionate Allowances list (POMS DI 23022.080), which certifies that a condition precludes substantial gainful activity. Because that is an adjudication of the work question itself rather than a proxy for it, this lane is only used on work_capacity.""")
    STATE_POLICY_LIST = PermissibleValue(
        text="STATE_POLICY_LIST",
        description="""A sub-national government or payer list that already treats this disease as qualifying - state Medicaid medically-frail condition lists, which are keyed to ICD-10-CM codes. Independent of the federal lane: different statute, different body, different qualifying test.""")
    LITERATURE = PermissibleValue(
        text="LITERATURE",
        description="""A peer-reviewed publication reporting employment, ADL, caregiver-burden or functional outcomes. Requires a verified quote.""")
    MODEL_JUDGEMENT = PermissibleValue(
        text="MODEL_JUDGEMENT",
        description="""A language model's structured judgement from the disease description. Never sufficient alone; benchmarked against EXPERT_DATABASE before use.""")
    PHENOTYPE_ANCHOR = PermissibleValue(
        text="PHENOTYPE_ANCHOR",
        description="""Specific, functionally decisive HPO findings that HPOA curates as occurring in >=30% of affected people - the same bar the impairment levels use. Structurally this is the same kind of object as an Orphanet row (a named finding with a curated frequency), and unlike COMPUTED_SCORE it cites the findings rather than a weighted sum of them.
Benchmarked against the 538-disease Orphanet validation set, the tightest usable rule reaches a positive predictive value of only 59-65%, so this lane must never set a level on its own: one assertion in three would be wrong. Its purpose is to make an UNKNOWN legible - to say what the phenotype profile suggests and why it was not enough.
Derived from the same HPOA data as COMPUTED_SCORE, so the two are never independent sources and this lane replaces rather than supplements that one.""")
    COMPUTED_SCORE = PermissibleValue(
        text="COMPUTED_SCORE",
        description="The phenotype-based score. A ranking signal, not a finding.")

    _defn = EnumDefinition(
        name="EvidenceLaneEnum",
        description="""The independent lanes evidence can come from. A well-curated assessment draws on more than one, and lanes that disagree are recorded, not reconciled away.
Policy evidence is split in two because a federal disability adjudication and a state Medicaid frailty code are genuinely independent decisions - different statutes, different bodies, different qualifying tests - and collapsing them into one lane made concordant government determinations look like a single source.""",
    )

class EvidenceDirectionEnum(EnumDefinitionImpl):
    """
    Whether this evidence line supports or disputes the assessment.
    """
    SUPPORTS = PermissibleValue(
        text="SUPPORTS",
        description="Supports the stated impairment level")
    DISPUTES = PermissibleValue(
        text="DISPUTES",
        description="Argues for a lower impairment level than stated")
    NEUTRAL = PermissibleValue(
        text="NEUTRAL",
        description="Relevant but does not move the assessment")

    _defn = EnumDefinition(
        name="EvidenceDirectionEnum",
        description="Whether this evidence line supports or disputes the assessment.",
    )

class EvidenceStrengthEnum(EnumDefinitionImpl):
    """
    How much weight this line carries.
    """
    STRONG = PermissibleValue(
        text="STRONG",
        description="""Direct measurement in an identified human cohort, or a named expert's rating of this specific disease.""")
    MODERATE = PermissibleValue(
        text="MODERATE",
        description="Indirect, small, or from a closely related disease.")
    WEAK = PermissibleValue(
        text="WEAK",
        description="Inference, opinion, or unbenchmarked model output.")

    _defn = EnumDefinition(
        name="EvidenceStrengthEnum",
        description="How much weight this line carries.",
    )

class FCCurationStatusEnum(EnumDefinitionImpl):
    """
    Curation lifecycle of the assessment.
    """
    UNREVIEWED = PermissibleValue(
        text="UNREVIEWED",
        description="Proposed by pipeline, no curator has looked")
    AI_CURATED = PermissibleValue(
        text="AI_CURATED",
        description="Evidence gathered and synthesised by an agent, awaiting human review")
    EXPERT_REVIEWED = PermissibleValue(
        text="EXPERT_REVIEWED",
        description="A named human clinician has reviewed and accepted")
    DISPUTED = PermissibleValue(
        text="DISPUTED",
        description="Evidence lanes conflict and a human must resolve")
    REJECTED = PermissibleValue(
        text="REJECTED",
        description="Reviewed and rejected; kept so the rejection is visible")

    _defn = EnumDefinition(
        name="FCCurationStatusEnum",
        description="Curation lifecycle of the assessment.",
    )

class CuratorTypeEnum2(EnumDefinitionImpl):
    """
    Who produced an evidence line.
    """
    AI_AGENT = PermissibleValue(
        text="AI_AGENT",
        description="LLM-based agent")
    PIPELINE = PermissibleValue(
        text="PIPELINE",
        description="Deterministic script")
    HUMAN = PermissibleValue(
        text="HUMAN",
        description="Human curator")

    _defn = EnumDefinition(
        name="CuratorTypeEnum2",
        description="Who produced an evidence line.",
    )

class TerminologyEnum(EnumDefinitionImpl):
    """
    The code system a value set is expressed in. Extend as new targets are added; the tier semantics below are the
    same for all of them.
    """
    ICD10CM = PermissibleValue(
        text="ICD10CM",
        description="ICD-10-CM, the US clinical modification. Anchors expand to billable leaf codes.",
        meaning=INFORES["icd10cm"])
    ICD10 = PermissibleValue(
        text="ICD10",
        description="WHO ICD-10. Note that placement often differs from ICD-10-CM.")
    ICD11 = PermissibleValue(
        text="ICD11",
        description="WHO ICD-11.")
    ICD9CM = PermissibleValue(
        text="ICD9CM",
        description="ICD-9-CM, for historical records.")
    SNOMEDCT = PermissibleValue(
        text="SNOMEDCT",
        description="""SNOMED CT. Anchors expand through the subsumption hierarchy rather than to billable leaves, so an expansion is larger and is bounded by the edition and release.""",
        meaning=INFORES["snomedct"])
    OPCS4 = PermissibleValue(
        text="OPCS4",
        description="OPCS-4 procedure codes, where a disease is ascertained by intervention.")
    READV2 = PermissibleValue(
        text="READV2",
        description="Read codes v2, for UK primary care records.")
    CTV3 = PermissibleValue(
        text="CTV3",
        description="Clinical Terms Version 3, for UK primary care records.")

    _defn = EnumDefinition(
        name="TerminologyEnum",
        description="""The code system a value set is expressed in. Extend as new targets are added; the tier semantics below are the same for all of them.""",
    )

class ValueSetProvenanceEnum(EnumDefinitionImpl):
    """
    Where an entry came from. Everything but LOCAL_CURATION is regenerated from Mondo on every build; LOCAL_CURATION
    survives regeneration. The subject side is always Mondo, whatever the target terminology.
    """
    MONDO_EXACT_MATCH = PermissibleValue(
        text="MONDO_EXACT_MATCH",
        description="`skos:exactMatch` asserted by Mondo on this disease.",
        meaning=SKOS["exactMatch"])
    MONDO_NARROW_MATCH = PermissibleValue(
        text="MONDO_NARROW_MATCH",
        description="""`skos:narrowMatch` asserted by Mondo on this disease. The code denotes a part of the disease, typically because the terminology subdivides it with no code for the whole.""",
        meaning=SKOS["narrowMatch"])
    MONDO_DESCENDANT = PermissibleValue(
        text="MONDO_DESCENDANT",
        description="""Reached through an `is_a` descendant of this disease in Mondo, which carries the mapping itself. A subtype's code is by construction narrower than the disease, so it is always safe. `via_mondo_id` names the descendant.""")
    MONDO_BROAD_MATCH = PermissibleValue(
        text="MONDO_BROAD_MATCH",
        description="""`skos:broadMatch` asserted by Mondo. The code is broader than the disease, so this can only ever be a PROXY entry.""",
        meaning=SKOS["broadMatch"])
    LOCAL_CURATION = PermissibleValue(
        text="LOCAL_CURATION",
        description="""Curated here, because the relationship is a fact about the terminology's structure rather than about the disease and Mondo will not carry it. PROXY entries only.""")

    _defn = EnumDefinition(
        name="ValueSetProvenanceEnum",
        description="""Where an entry came from. Everything but LOCAL_CURATION is regenerated from Mondo on every build; LOCAL_CURATION survives regeneration. The subject side is always Mondo, whatever the target terminology.""",
    )

class ProxyBasisEnum(EnumDefinitionImpl):
    """
    Why a proxy code is defensible. Only the last value is genuinely outside what an ontology should assert; the first
    two are class relationships that belong in Mondo as `skos:broadMatch` and should migrate there.
    """
    SUBSUMPTION = PermissibleValue(
        text="SUBSUMPTION",
        description="""The rubric is a genuine superclass of the disease. Beckwith-Wiedemann is an overgrowth syndrome; Aicardi syndrome always has corpus callosum agenesis.""")
    TERMINOLOGY_INDEX = PermissibleValue(
        text="TERMINOLOGY_INDEX",
        description="""The terminology's own index, inclusion terms or coding guidance assign the disease to this code, so coders were instructed to use it. Higher yield than SUBSUMPTION, because the instruction is what coders followed.""")
    CODING_CONVENTION = PermissibleValue(
        text="CODING_CONVENTION",
        description="""An \"other specified\" or NEC rubric that is a superclass only tautologically. Alstrom syndrome is not a kind of \"other specified endocrine disorder\"; it is filed at ICD10CM:E34.8 because ICD had nowhere else to put it. Records where a coder puts the patient, not what the code means.""")

    _defn = EnumDefinition(
        name="ProxyBasisEnum",
        description="""Why a proxy code is defensible. Only the last value is genuinely outside what an ontology should assert; the first two are class relationships that belong in Mondo as `skos:broadMatch` and should migrate there.""",
    )

# Slots
class slots:
    pass

slots.simpleTerm__id = Slot(uri=RDID.id, name="simpleTerm__id", curie=RDID.curie('id'),
                   model_uri=RDID.simpleTerm__id, domain=None, range=URIRef)

slots.simpleTerm__label = Slot(uri=RDID.label, name="simpleTerm__label", curie=RDID.curie('label'),
                   model_uri=RDID.simpleTerm__label, domain=None, range=Optional[str])

slots.source__name = Slot(uri=RDID.name, name="source__name", curie=RDID.curie('name'),
                   model_uri=RDID.source__name, domain=None, range=Optional[str])

slots.source__type = Slot(uri=RDID.type, name="source__type", curie=RDID.curie('type'),
                   model_uri=RDID.source__type, domain=None, range=Optional[Union[str, "SourceTypeEnum"]])

slots.source__jurisdiction = Slot(uri=RDID.jurisdiction, name="source__jurisdiction", curie=RDID.curie('jurisdiction'),
                   model_uri=RDID.source__jurisdiction, domain=None, range=Optional[str])

slots.source__url = Slot(uri=RDID.url, name="source__url", curie=RDID.curie('url'),
                   model_uri=RDID.source__url, domain=None, range=Optional[str])

slots.source__description = Slot(uri=RDID.description, name="source__description", curie=RDID.curie('description'),
                   model_uri=RDID.source__description, domain=None, range=Optional[str])

slots.source__file = Slot(uri=RDID.file, name="source__file", curie=RDID.curie('file'),
                   model_uri=RDID.source__file, domain=None, range=Optional[str])

slots.curator__name = Slot(uri=RDID.name, name="curator__name", curie=RDID.curie('name'),
                   model_uri=RDID.curator__name, domain=None, range=Optional[str])

slots.curator__curator_type = Slot(uri=RDID.curator_type, name="curator__curator_type", curie=RDID.curie('curator_type'),
                   model_uri=RDID.curator__curator_type, domain=None, range=Optional[Union[str, "CuratorTypeEnum"]])

slots.curator__curator_id = Slot(uri=RDID.curator_id, name="curator__curator_id", curie=RDID.curie('curator_id'),
                   model_uri=RDID.curator__curator_id, domain=None, range=Optional[str])

slots.aggregateConfidence__method = Slot(uri=RDID.method, name="aggregateConfidence__method", curie=RDID.curie('method'),
                   model_uri=RDID.aggregateConfidence__method, domain=None, range=Optional[str])

slots.aggregateConfidence__overall = Slot(uri=RDID.overall, name="aggregateConfidence__overall", curie=RDID.curie('overall'),
                   model_uri=RDID.aggregateConfidence__overall, domain=None, range=Optional[float])

slots.aggregateConfidence__n_assertions = Slot(uri=RDID.n_assertions, name="aggregateConfidence__n_assertions", curie=RDID.curie('n_assertions'),
                   model_uri=RDID.aggregateConfidence__n_assertions, domain=None, range=Optional[int])

slots.aggregateConfidence__n_sources = Slot(uri=RDID.n_sources, name="aggregateConfidence__n_sources", curie=RDID.curie('n_sources'),
                   model_uri=RDID.aggregateConfidence__n_sources, domain=None, range=Optional[int])

slots.regulatoryStatus__authority = Slot(uri=RDID.authority, name="regulatoryStatus__authority", curie=RDID.curie('authority'),
                   model_uri=RDID.regulatoryStatus__authority, domain=None, range=Optional[Union[str, "RegulatoryAuthorityEnum"]])

slots.regulatoryStatus__status = Slot(uri=RDID.status, name="regulatoryStatus__status", curie=RDID.curie('status'),
                   model_uri=RDID.regulatoryStatus__status, domain=None, range=Optional[Union[str, "RegulatoryStatusEnum"]])

slots.regulatoryStatus__approval_date = Slot(uri=RDID.approval_date, name="regulatoryStatus__approval_date", curie=RDID.curie('approval_date'),
                   model_uri=RDID.regulatoryStatus__approval_date, domain=None, range=Optional[str])

slots.regulatoryStatus__source_role = Slot(uri=RDID.source_role, name="regulatoryStatus__source_role", curie=RDID.curie('source_role'),
                   model_uri=RDID.regulatoryStatus__source_role, domain=None, range=Optional[Union[str, "SourceRoleEnum"]])

slots.regulatoryStatus__regulatory_document_url = Slot(uri=RDID.regulatory_document_url, name="regulatoryStatus__regulatory_document_url", curie=RDID.curie('regulatory_document_url'),
                   model_uri=RDID.regulatoryStatus__regulatory_document_url, domain=None, range=Optional[str])

slots.regulatoryStatus__source = Slot(uri=RDID.source, name="regulatoryStatus__source", curie=RDID.curie('source'),
                   model_uri=RDID.regulatoryStatus__source, domain=None, range=Optional[str])

slots.regulatoryStatus__source_document_url = Slot(uri=RDID.source_document_url, name="regulatoryStatus__source_document_url", curie=RDID.curie('source_document_url'),
                   model_uri=RDID.regulatoryStatus__source_document_url, domain=None, range=Optional[str])

slots.regulatoryStatus__setid = Slot(uri=RDID.setid, name="regulatoryStatus__setid", curie=RDID.curie('setid'),
                   model_uri=RDID.regulatoryStatus__setid, domain=None, range=Optional[str])

slots.regulatoryStatus__product_id = Slot(uri=RDID.product_id, name="regulatoryStatus__product_id", curie=RDID.curie('product_id'),
                   model_uri=RDID.regulatoryStatus__product_id, domain=None, range=Optional[str])

slots.evidence__source = Slot(uri=RDID.source, name="evidence__source", curie=RDID.curie('source'),
                   model_uri=RDID.evidence__source, domain=None, range=Optional[Union[dict, Source]])

slots.evidence__source_type = Slot(uri=RDID.source_type, name="evidence__source_type", curie=RDID.curie('source_type'),
                   model_uri=RDID.evidence__source_type, domain=None, range=Optional[Union[str, "SourceTypeEnum"]])

slots.evidence__source_role = Slot(uri=RDID.source_role, name="evidence__source_role", curie=RDID.curie('source_role'),
                   model_uri=RDID.evidence__source_role, domain=None, range=Optional[Union[str, "SourceRoleEnum"]])

slots.evidence__jurisdiction = Slot(uri=RDID.jurisdiction, name="evidence__jurisdiction", curie=RDID.curie('jurisdiction'),
                   model_uri=RDID.evidence__jurisdiction, domain=None, range=Optional[str])

slots.evidence__reference = Slot(uri=RDID.reference, name="evidence__reference", curie=RDID.curie('reference'),
                   model_uri=RDID.evidence__reference, domain=None, range=Optional[str])

slots.evidence__reference_title = Slot(uri=RDID.reference_title, name="evidence__reference_title", curie=RDID.curie('reference_title'),
                   model_uri=RDID.evidence__reference_title, domain=None, range=Optional[str])

slots.evidence__page_or_section = Slot(uri=RDID.page_or_section, name="evidence__page_or_section", curie=RDID.curie('page_or_section'),
                   model_uri=RDID.evidence__page_or_section, domain=None, range=Optional[str])

slots.evidence__source_document_url = Slot(uri=RDID.source_document_url, name="evidence__source_document_url", curie=RDID.curie('source_document_url'),
                   model_uri=RDID.evidence__source_document_url, domain=None, range=Optional[str])

slots.evidence__original_drug_label = Slot(uri=RDID.original_drug_label, name="evidence__original_drug_label", curie=RDID.curie('original_drug_label'),
                   model_uri=RDID.evidence__original_drug_label, domain=None, range=Optional[str])

slots.evidence__original_drug_id = Slot(uri=RDID.original_drug_id, name="evidence__original_drug_id", curie=RDID.curie('original_drug_id'),
                   model_uri=RDID.evidence__original_drug_id, domain=None, range=Optional[str])

slots.evidence__original_disease_label = Slot(uri=RDID.original_disease_label, name="evidence__original_disease_label", curie=RDID.curie('original_disease_label'),
                   model_uri=RDID.evidence__original_disease_label, domain=None, range=Optional[str])

slots.evidence__setid = Slot(uri=RDID.setid, name="evidence__setid", curie=RDID.curie('setid'),
                   model_uri=RDID.evidence__setid, domain=None, range=Optional[str])

slots.evidence__document_id = Slot(uri=RDID.document_id, name="evidence__document_id", curie=RDID.curie('document_id'),
                   model_uri=RDID.evidence__document_id, domain=None, range=Optional[str])

slots.evidence__product_id = Slot(uri=RDID.product_id, name="evidence__product_id", curie=RDID.curie('product_id'),
                   model_uri=RDID.evidence__product_id, domain=None, range=Optional[str])

slots.evidence__snippet = Slot(uri=RDID.snippet, name="evidence__snippet", curie=RDID.curie('snippet'),
                   model_uri=RDID.evidence__snippet, domain=None, range=Optional[str])

slots.evidence__explanation = Slot(uri=RDID.explanation, name="evidence__explanation", curie=RDID.curie('explanation'),
                   model_uri=RDID.evidence__explanation, domain=None, range=Optional[str])

slots.evidence__support = Slot(uri=RDID.support, name="evidence__support", curie=RDID.curie('support'),
                   model_uri=RDID.evidence__support, domain=None, range=Optional[str])

slots.evidence__confidence = Slot(uri=RDID.confidence, name="evidence__confidence", curie=RDID.curie('confidence'),
                   model_uri=RDID.evidence__confidence, domain=None, range=Optional[Union[str, "ConfidenceEnum"]])

slots.evidence__confidence_drug = Slot(uri=RDID.confidence_drug, name="evidence__confidence_drug", curie=RDID.curie('confidence_drug'),
                   model_uri=RDID.evidence__confidence_drug, domain=None, range=Optional[Union[str, "ConfidenceEnum"]])

slots.evidence__confidence_disease = Slot(uri=RDID.confidence_disease, name="evidence__confidence_disease", curie=RDID.curie('confidence_disease'),
                   model_uri=RDID.evidence__confidence_disease, domain=None, range=Optional[Union[str, "ConfidenceEnum"]])

slots.evidence__confidence_association = Slot(uri=RDID.confidence_association, name="evidence__confidence_association", curie=RDID.curie('confidence_association'),
                   model_uri=RDID.evidence__confidence_association, domain=None, range=Optional[Union[str, "ConfidenceEnum"]])

slots.evidence__evidence_source = Slot(uri=RDID.evidence_source, name="evidence__evidence_source", curie=RDID.curie('evidence_source'),
                   model_uri=RDID.evidence__evidence_source, domain=None, range=Optional[Union[str, "EvidenceSourceEnum"]])

slots.evidence__approval_status = Slot(uri=RDID.approval_status, name="evidence__approval_status", curie=RDID.curie('approval_status'),
                   model_uri=RDID.evidence__approval_status, domain=None, range=Optional[Union[str, "RegulatoryStatusEnum"]])

slots.evidence__approval_date = Slot(uri=RDID.approval_date, name="evidence__approval_date", curie=RDID.curie('approval_date'),
                   model_uri=RDID.evidence__approval_date, domain=None, range=Optional[str])

slots.evidence__max_research_phase = Slot(uri=RDID.max_research_phase, name="evidence__max_research_phase", curie=RDID.curie('max_research_phase'),
                   model_uri=RDID.evidence__max_research_phase, domain=None, range=Optional[str])

slots.evidence__curator = Slot(uri=RDID.curator, name="evidence__curator", curie=RDID.curie('curator'),
                   model_uri=RDID.evidence__curator, domain=None, range=Optional[Union[dict, Curator]])

slots.drugAssociation__drug_id = Slot(uri=RDID.drug_id, name="drugAssociation__drug_id", curie=RDID.curie('drug_id'),
                   model_uri=RDID.drugAssociation__drug_id, domain=None, range=Optional[str])

slots.drugAssociation__drug_label = Slot(uri=RDID.drug_label, name="drugAssociation__drug_label", curie=RDID.curie('drug_label'),
                   model_uri=RDID.drugAssociation__drug_label, domain=None, range=str)

slots.drugAssociation__relationship_type = Slot(uri=RDID.relationship_type, name="drugAssociation__relationship_type", curie=RDID.curie('relationship_type'),
                   model_uri=RDID.drugAssociation__relationship_type, domain=None, range=Optional[Union[str, "RelationshipTypeEnum"]])

slots.drugAssociation__reliability = Slot(uri=RDID.reliability, name="drugAssociation__reliability", curie=RDID.curie('reliability'),
                   model_uri=RDID.drugAssociation__reliability, domain=None, range=Optional[Union[str, "ConfidenceEnum"]])

slots.drugAssociation__confidence = Slot(uri=RDID.confidence, name="drugAssociation__confidence", curie=RDID.curie('confidence'),
                   model_uri=RDID.drugAssociation__confidence, domain=None, range=Optional[Union[dict, AggregateConfidence]])

slots.drugAssociation__is_allergen = Slot(uri=RDID.is_allergen, name="drugAssociation__is_allergen", curie=RDID.curie('is_allergen'),
                   model_uri=RDID.drugAssociation__is_allergen, domain=None, range=Optional[Union[bool, Bool]])

slots.drugAssociation__is_diagnostic_agent = Slot(uri=RDID.is_diagnostic_agent, name="drugAssociation__is_diagnostic_agent", curie=RDID.curie('is_diagnostic_agent'),
                   model_uri=RDID.drugAssociation__is_diagnostic_agent, domain=None, range=Optional[Union[bool, Bool]])

slots.drugAssociation__regulatory_status = Slot(uri=RDID.regulatory_status, name="drugAssociation__regulatory_status", curie=RDID.curie('regulatory_status'),
                   model_uri=RDID.drugAssociation__regulatory_status, domain=None, range=Optional[Union[Union[dict, RegulatoryStatus], list[Union[dict, RegulatoryStatus]]]])

slots.drugAssociation__curation_status = Slot(uri=RDID.curation_status, name="drugAssociation__curation_status", curie=RDID.curie('curation_status'),
                   model_uri=RDID.drugAssociation__curation_status, domain=None, range=Optional[Union[str, "CurationStatusEnum"]])

slots.drugAssociation__curation_date = Slot(uri=RDID.curation_date, name="drugAssociation__curation_date", curie=RDID.curie('curation_date'),
                   model_uri=RDID.drugAssociation__curation_date, domain=None, range=Optional[str])

slots.drugAssociation__curator = Slot(uri=RDID.curator, name="drugAssociation__curator", curie=RDID.curie('curator'),
                   model_uri=RDID.drugAssociation__curator, domain=None, range=Optional[Union[dict, Curator]])

slots.drugAssociation__deep_research_used = Slot(uri=RDID.deep_research_used, name="drugAssociation__deep_research_used", curie=RDID.curie('deep_research_used'),
                   model_uri=RDID.drugAssociation__deep_research_used, domain=None, range=Optional[Union[bool, Bool]])

slots.drugAssociation__notes = Slot(uri=RDID.notes, name="drugAssociation__notes", curie=RDID.curie('notes'),
                   model_uri=RDID.drugAssociation__notes, domain=None, range=Optional[str])

slots.drugAssociation__evidence = Slot(uri=RDID.evidence, name="drugAssociation__evidence", curie=RDID.curie('evidence'),
                   model_uri=RDID.drugAssociation__evidence, domain=None, range=Optional[Union[Union[dict, Evidence], list[Union[dict, Evidence]]]])

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

slots.rareDisease__dismech_url = Slot(uri=RDID.dismech_url, name="rareDisease__dismech_url", curie=RDID.curie('dismech_url'),
                   model_uri=RDID.rareDisease__dismech_url, domain=None, range=Optional[Union[str, URI]])

slots.rareDisease__work_capacity = Slot(uri=RDID.work_capacity, name="rareDisease__work_capacity", curie=RDID.curie('work_capacity'),
                   model_uri=RDID.rareDisease__work_capacity, domain=None, range=Optional[Union[dict, FunctionalCapacityAssessment]])

slots.rareDisease__care_dependence = Slot(uri=RDID.care_dependence, name="rareDisease__care_dependence", curie=RDID.curie('care_dependence'),
                   model_uri=RDID.rareDisease__care_dependence, domain=None, range=Optional[Union[dict, FunctionalCapacityAssessment]])

slots.rareDisease__hpo_high_level_categories = Slot(uri=RDID.hpo_high_level_categories, name="rareDisease__hpo_high_level_categories", curie=RDID.curie('hpo_high_level_categories'),
                   model_uri=RDID.rareDisease__hpo_high_level_categories, domain=None, range=Optional[Union[dict[Union[str, SimpleTermId], Union[dict, SimpleTerm]], list[Union[dict, SimpleTerm]]]])

slots.rareDisease__histopheno_categories = Slot(uri=RDID.histopheno_categories, name="rareDisease__histopheno_categories", curie=RDID.curie('histopheno_categories'),
                   model_uri=RDID.rareDisease__histopheno_categories, domain=None, range=Optional[Union[str, list[str]]])

slots.rareDisease__keywords = Slot(uri=RDID.keywords, name="rareDisease__keywords", curie=RDID.curie('keywords'),
                   model_uri=RDID.rareDisease__keywords, domain=None, range=Optional[Union[str, list[str]]])

slots.rareDisease__ontology_terminology_codes = Slot(uri=RDID.ontology_terminology_codes, name="rareDisease__ontology_terminology_codes", curie=RDID.curie('ontology_terminology_codes'),
                   model_uri=RDID.rareDisease__ontology_terminology_codes, domain=None, range=Optional[Union[str, list[str]]])

slots.rareDisease__value_sets = Slot(uri=RDID.value_sets, name="rareDisease__value_sets", curie=RDID.curie('value_sets'),
                   model_uri=RDID.rareDisease__value_sets, domain=None, range=Optional[Union[Union[dict, TerminologyValueSet], list[Union[dict, TerminologyValueSet]]]])

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
                   model_uri=RDID.rareDisease__indications, domain=None, range=Optional[Union[Union[dict, DrugAssociation], list[Union[dict, DrugAssociation]]]])

slots.rareDisease__contraindications = Slot(uri=RDID.contraindications, name="rareDisease__contraindications", curie=RDID.curie('contraindications'),
                   model_uri=RDID.rareDisease__contraindications, domain=None, range=Optional[Union[Union[dict, DrugAssociation], list[Union[dict, DrugAssociation]]]])

slots.rareDisease__research = Slot(uri=RDID.research, name="rareDisease__research", curie=RDID.curie('research'),
                   model_uri=RDID.rareDisease__research, domain=None, range=Optional[Union[Union[dict, DrugAssociation], list[Union[dict, DrugAssociation]]]])

slots.functionalCapacityEvidence__lane = Slot(uri=RDID.lane, name="functionalCapacityEvidence__lane", curie=RDID.curie('lane'),
                   model_uri=RDID.functionalCapacityEvidence__lane, domain=None, range=Union[str, "EvidenceLaneEnum"])

slots.functionalCapacityEvidence__direction = Slot(uri=RDID.direction, name="functionalCapacityEvidence__direction", curie=RDID.curie('direction'),
                   model_uri=RDID.functionalCapacityEvidence__direction, domain=None, range=Union[str, "EvidenceDirectionEnum"])

slots.functionalCapacityEvidence__strength = Slot(uri=RDID.strength, name="functionalCapacityEvidence__strength", curie=RDID.curie('strength'),
                   model_uri=RDID.functionalCapacityEvidence__strength, domain=None, range=Union[str, "EvidenceStrengthEnum"])

slots.functionalCapacityEvidence__reference = Slot(uri=DCTERMS.references, name="functionalCapacityEvidence__reference", curie=DCTERMS.curie('references'),
                   model_uri=RDID.functionalCapacityEvidence__reference, domain=None, range=Union[str, URIorCURIE],
                   pattern=re.compile(r'^(PMID|DOI|PMC|ORPHA|ICD10CM|SSACAL|MTFRAIL|HPOA|RDIDRUN):\S+$'))

slots.functionalCapacityEvidence__reference_title = Slot(uri=DCTERMS.title, name="functionalCapacityEvidence__reference_title", curie=DCTERMS.curie('title'),
                   model_uri=RDID.functionalCapacityEvidence__reference_title, domain=None, range=Optional[str])

slots.functionalCapacityEvidence__quote = Slot(uri=OA.exact, name="functionalCapacityEvidence__quote", curie=OA.curie('exact'),
                   model_uri=RDID.functionalCapacityEvidence__quote, domain=None, range=Optional[str])

slots.functionalCapacityEvidence__quote_verified = Slot(uri=RDID.quote_verified, name="functionalCapacityEvidence__quote_verified", curie=RDID.curie('quote_verified'),
                   model_uri=RDID.functionalCapacityEvidence__quote_verified, domain=None, range=Optional[Union[bool, Bool]])

slots.functionalCapacityEvidence__source_statement = Slot(uri=RDID.source_statement, name="functionalCapacityEvidence__source_statement", curie=RDID.curie('source_statement'),
                   model_uri=RDID.functionalCapacityEvidence__source_statement, domain=None, range=Optional[str])

slots.functionalCapacityEvidence__population = Slot(uri=RDID.population, name="functionalCapacityEvidence__population", curie=RDID.curie('population'),
                   model_uri=RDID.functionalCapacityEvidence__population, domain=None, range=Optional[str])

slots.functionalCapacityEvidence__explanation = Slot(uri=RDID.explanation, name="functionalCapacityEvidence__explanation", curie=RDID.curie('explanation'),
                   model_uri=RDID.functionalCapacityEvidence__explanation, domain=None, range=str)

slots.functionalCapacityEvidence__eco_code = Slot(uri=RDID.eco_code, name="functionalCapacityEvidence__eco_code", curie=RDID.curie('eco_code'),
                   model_uri=RDID.functionalCapacityEvidence__eco_code, domain=None, range=Optional[Union[str, URIorCURIE]])

slots.functionalCapacityEvidence__curator = Slot(uri=RDID.curator, name="functionalCapacityEvidence__curator", curie=RDID.curie('curator'),
                   model_uri=RDID.functionalCapacityEvidence__curator, domain=None, range=Optional[str])

slots.functionalCapacityEvidence__curator_type = Slot(uri=RDID.curator_type, name="functionalCapacityEvidence__curator_type", curie=RDID.curie('curator_type'),
                   model_uri=RDID.functionalCapacityEvidence__curator_type, domain=None, range=Optional[Union[str, "CuratorTypeEnum2"]])

slots.functionalCapacityEvidence__retrieved_on = Slot(uri=RDID.retrieved_on, name="functionalCapacityEvidence__retrieved_on", curie=RDID.curie('retrieved_on'),
                   model_uri=RDID.functionalCapacityEvidence__retrieved_on, domain=None, range=Optional[Union[str, XSDDate]])

slots.functionalCapacityAssessment__impairment = Slot(uri=RDID.impairment, name="functionalCapacityAssessment__impairment", curie=RDID.curie('impairment'),
                   model_uri=RDID.functionalCapacityAssessment__impairment, domain=None, range=Union[str, "ImpairmentLevelEnum"])

slots.functionalCapacityAssessment__score = Slot(uri=RDID.score, name="functionalCapacityAssessment__score", curie=RDID.curie('score'),
                   model_uri=RDID.functionalCapacityAssessment__score, domain=None, range=Optional[float])

slots.functionalCapacityAssessment__score_method = Slot(uri=RDID.score_method, name="functionalCapacityAssessment__score_method", curie=RDID.curie('score_method'),
                   model_uri=RDID.functionalCapacityAssessment__score_method, domain=None, range=Optional[str])

slots.functionalCapacityAssessment__score_version = Slot(uri=RDID.score_version, name="functionalCapacityAssessment__score_version", curie=RDID.curie('score_version'),
                   model_uri=RDID.functionalCapacityAssessment__score_version, domain=None, range=Optional[str])

slots.functionalCapacityAssessment__model_confidence = Slot(uri=RDID.model_confidence, name="functionalCapacityAssessment__model_confidence", curie=RDID.curie('model_confidence'),
                   model_uri=RDID.functionalCapacityAssessment__model_confidence, domain=None, range=Optional[int])

slots.functionalCapacityAssessment__care_context = Slot(uri=RDID.care_context, name="functionalCapacityAssessment__care_context", curie=RDID.curie('care_context'),
                   model_uri=RDID.functionalCapacityAssessment__care_context, domain=None, range=Union[str, "CareContextEnum"])

slots.functionalCapacityAssessment__life_stage = Slot(uri=RDID.life_stage, name="functionalCapacityAssessment__life_stage", curie=RDID.curie('life_stage'),
                   model_uri=RDID.functionalCapacityAssessment__life_stage, domain=None, range=Optional[Union[str, "LifeStageEnum"]])

slots.functionalCapacityAssessment__rationale = Slot(uri=RDID.rationale, name="functionalCapacityAssessment__rationale", curie=RDID.curie('rationale'),
                   model_uri=RDID.functionalCapacityAssessment__rationale, domain=None, range=str)

slots.functionalCapacityAssessment__evidence = Slot(uri=RDID.evidence, name="functionalCapacityAssessment__evidence", curie=RDID.curie('evidence'),
                   model_uri=RDID.functionalCapacityAssessment__evidence, domain=None, range=Optional[Union[Union[dict, FunctionalCapacityEvidence], list[Union[dict, FunctionalCapacityEvidence]]]])

slots.functionalCapacityAssessment__curation_status = Slot(uri=RDID.curation_status, name="functionalCapacityAssessment__curation_status", curie=RDID.curie('curation_status'),
                   model_uri=RDID.functionalCapacityAssessment__curation_status, domain=None, range=Union[str, "FCCurationStatusEnum"])

slots.functionalCapacityAssessment__claims_selectable = Slot(uri=RDID.claims_selectable, name="functionalCapacityAssessment__claims_selectable", curie=RDID.curie('claims_selectable'),
                   model_uri=RDID.functionalCapacityAssessment__claims_selectable, domain=None, range=Optional[Union[bool, Bool]])

slots.functionalCapacityAssessment__icd10cm_codes = Slot(uri=RDID.icd10cm_codes, name="functionalCapacityAssessment__icd10cm_codes", curie=RDID.curie('icd10cm_codes'),
                   model_uri=RDID.functionalCapacityAssessment__icd10cm_codes, domain=None, range=Optional[Union[Union[str, URIorCURIE], list[Union[str, URIorCURIE]]]],
                   pattern=re.compile(r'^ICD10CM:[A-Z][0-9A-Z.]+$'))

slots.functionalCapacityAssessment__assessed_by = Slot(uri=RDID.assessed_by, name="functionalCapacityAssessment__assessed_by", curie=RDID.curie('assessed_by'),
                   model_uri=RDID.functionalCapacityAssessment__assessed_by, domain=None, range=Optional[Union[str, URIorCURIE]],
                   pattern=re.compile(r'^(ORCID|RDIDAGENT):\S+$'))

slots.functionalCapacityAssessment__assessed_on = Slot(uri=RDID.assessed_on, name="functionalCapacityAssessment__assessed_on", curie=RDID.curie('assessed_on'),
                   model_uri=RDID.functionalCapacityAssessment__assessed_on, domain=None, range=Optional[Union[str, XSDDate]])

slots.functionalCapacityAssessment__notes = Slot(uri=RDID.notes, name="functionalCapacityAssessment__notes", curie=RDID.curie('notes'),
                   model_uri=RDID.functionalCapacityAssessment__notes, domain=None, range=Optional[str])

slots.valueSetEntry__code = Slot(uri=RDID.code, name="valueSetEntry__code", curie=RDID.curie('code'),
                   model_uri=RDID.valueSetEntry__code, domain=None, range=URIRef,
                   pattern=re.compile(r'^[A-Za-z][A-Za-z0-9._-]*:[A-Za-z0-9][A-Za-z0-9._-]*$'))

slots.valueSetEntry__label = Slot(uri=RDID.label, name="valueSetEntry__label", curie=RDID.curie('label'),
                   model_uri=RDID.valueSetEntry__label, domain=None, range=str)

slots.valueSetEntry__expanded_codes = Slot(uri=RDID.expanded_codes, name="valueSetEntry__expanded_codes", curie=RDID.curie('expanded_codes'),
                   model_uri=RDID.valueSetEntry__expanded_codes, domain=None, range=Optional[Union[Union[str, URIorCURIE], list[Union[str, URIorCURIE]]]])

slots.valueSetEntry__provenance = Slot(uri=RDID.provenance, name="valueSetEntry__provenance", curie=RDID.curie('provenance'),
                   model_uri=RDID.valueSetEntry__provenance, domain=None, range=Union[str, "ValueSetProvenanceEnum"])

slots.valueSetEntry__via_mondo_id = Slot(uri=RDID.via_mondo_id, name="valueSetEntry__via_mondo_id", curie=RDID.curie('via_mondo_id'),
                   model_uri=RDID.valueSetEntry__via_mondo_id, domain=None, range=Optional[str],
                   pattern=re.compile(r'^MONDO:\d{7}$'))

slots.valueSetEntry__via_mondo_label = Slot(uri=RDID.via_mondo_label, name="valueSetEntry__via_mondo_label", curie=RDID.curie('via_mondo_label'),
                   model_uri=RDID.valueSetEntry__via_mondo_label, domain=None, range=Optional[str])

slots.proxyEntry__basis = Slot(uri=RDID.basis, name="proxyEntry__basis", curie=RDID.curie('basis'),
                   model_uri=RDID.proxyEntry__basis, domain=None, range=Union[str, "ProxyBasisEnum"])

slots.proxyEntry__comment = Slot(uri=RDID.comment, name="proxyEntry__comment", curie=RDID.curie('comment'),
                   model_uri=RDID.proxyEntry__comment, domain=None, range=str)

slots.proxyEntry__approximate_cohort_size = Slot(uri=RDID.approximate_cohort_size, name="proxyEntry__approximate_cohort_size", curie=RDID.curie('approximate_cohort_size'),
                   model_uri=RDID.proxyEntry__approximate_cohort_size, domain=None, range=Optional[int])

slots.proxyEntry__cohort_size_source = Slot(uri=RDID.cohort_size_source, name="proxyEntry__cohort_size_source", curie=RDID.curie('cohort_size_source'),
                   model_uri=RDID.proxyEntry__cohort_size_source, domain=None, range=Optional[str])

slots.proxyEntry__curator = Slot(uri=RDID.curator, name="proxyEntry__curator", curie=RDID.curie('curator'),
                   model_uri=RDID.proxyEntry__curator, domain=None, range=Optional[Union[str, URIorCURIE]],
                   pattern=re.compile(r'^(ORCID|RDIDAGENT):\S+$'))

slots.proxyEntry__curation_date = Slot(uri=DCTERMS.created, name="proxyEntry__curation_date", curie=DCTERMS.curie('created'),
                   model_uri=RDID.proxyEntry__curation_date, domain=None, range=Optional[Union[str, XSDDate]])

slots.proxyEntry__upstream_request = Slot(uri=RDID.upstream_request, name="proxyEntry__upstream_request", curie=RDID.curie('upstream_request'),
                   model_uri=RDID.proxyEntry__upstream_request, domain=None, range=Optional[Union[str, URIorCURIE]])

slots.excludedCode__code = Slot(uri=RDID.code, name="excludedCode__code", curie=RDID.curie('code'),
                   model_uri=RDID.excludedCode__code, domain=None, range=URIRef,
                   pattern=re.compile(r'^[A-Za-z][A-Za-z0-9._-]*:[A-Za-z0-9][A-Za-z0-9._-]*$'))

slots.excludedCode__label = Slot(uri=RDID.label, name="excludedCode__label", curie=RDID.curie('label'),
                   model_uri=RDID.excludedCode__label, domain=None, range=Optional[str])

slots.excludedCode__reason = Slot(uri=RDID.reason, name="excludedCode__reason", curie=RDID.curie('reason'),
                   model_uri=RDID.excludedCode__reason, domain=None, range=str)

slots.terminologyValueSet__terminology = Slot(uri=RDID.terminology, name="terminologyValueSet__terminology", curie=RDID.curie('terminology'),
                   model_uri=RDID.terminologyValueSet__terminology, domain=None, range=Union[str, "TerminologyEnum"])

slots.terminologyValueSet__exact = Slot(uri=RDID.exact, name="terminologyValueSet__exact", curie=RDID.curie('exact'),
                   model_uri=RDID.terminologyValueSet__exact, domain=None, range=Optional[Union[dict[Union[str, ValueSetEntryCode], Union[dict, ValueSetEntry]], list[Union[dict, ValueSetEntry]]]])

slots.terminologyValueSet__narrower = Slot(uri=RDID.narrower, name="terminologyValueSet__narrower", curie=RDID.curie('narrower'),
                   model_uri=RDID.terminologyValueSet__narrower, domain=None, range=Optional[Union[dict[Union[str, ValueSetEntryCode], Union[dict, ValueSetEntry]], list[Union[dict, ValueSetEntry]]]])

slots.terminologyValueSet__proxy = Slot(uri=RDID.proxy, name="terminologyValueSet__proxy", curie=RDID.curie('proxy'),
                   model_uri=RDID.terminologyValueSet__proxy, domain=None, range=Optional[Union[dict[Union[str, ProxyEntryCode], Union[dict, ProxyEntry]], list[Union[dict, ProxyEntry]]]])

slots.terminologyValueSet__excluded = Slot(uri=RDID.excluded, name="terminologyValueSet__excluded", curie=RDID.curie('excluded'),
                   model_uri=RDID.terminologyValueSet__excluded, domain=None, range=Optional[Union[dict[Union[str, ExcludedCodeCode], Union[dict, ExcludedCode]], list[Union[dict, ExcludedCode]]]])

slots.terminologyValueSet__mondo_version = Slot(uri=RDID.mondo_version, name="terminologyValueSet__mondo_version", curie=RDID.curie('mondo_version'),
                   model_uri=RDID.terminologyValueSet__mondo_version, domain=None, range=Optional[str])

slots.terminologyValueSet__terminology_version = Slot(uri=RDID.terminology_version, name="terminologyValueSet__terminology_version", curie=RDID.curie('terminology_version'),
                   model_uri=RDID.terminologyValueSet__terminology_version, domain=None, range=Optional[str])

slots.terminologyValueSet__generated_on = Slot(uri=RDID.generated_on, name="terminologyValueSet__generated_on", curie=RDID.curie('generated_on'),
                   model_uri=RDID.terminologyValueSet__generated_on, domain=None, range=Optional[Union[str, XSDDate]])

