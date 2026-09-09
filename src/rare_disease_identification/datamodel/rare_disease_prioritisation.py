# Auto generated from rare_disease_prioritisation.yaml by pythongen.py version: 0.0.1
# Generation date: 2026-05-07T23:09:59
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

from linkml_runtime.linkml_model.types import Boolean, Float, String
from linkml_runtime.utils.metamodelcore import Bool

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
    indications_text: Optional[str] = None
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

        if self.indications_text is not None and not isinstance(self.indications_text, str):
            self.indications_text = str(self.indications_text)

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

        self._normalize_inlined_as_list(slot_name="indications", slot_type=DrugAssociation, key_name="drug_label", keyed=False)

        self._normalize_inlined_as_list(slot_name="contraindications", slot_type=DrugAssociation, key_name="drug_label", keyed=False)

        self._normalize_inlined_as_list(slot_name="research", slot_type=DrugAssociation, key_name="drug_label", keyed=False)

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

slots.drugAssociation__indications_text = Slot(uri=RDID.indications_text, name="drugAssociation__indications_text", curie=RDID.curie('indications_text'),
                   model_uri=RDID.drugAssociation__indications_text, domain=None, range=Optional[str])

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
                   model_uri=RDID.rareDisease__indications, domain=None, range=Optional[Union[Union[dict, DrugAssociation], list[Union[dict, DrugAssociation]]]])

slots.rareDisease__contraindications = Slot(uri=RDID.contraindications, name="rareDisease__contraindications", curie=RDID.curie('contraindications'),
                   model_uri=RDID.rareDisease__contraindications, domain=None, range=Optional[Union[Union[dict, DrugAssociation], list[Union[dict, DrugAssociation]]]])

slots.rareDisease__research = Slot(uri=RDID.research, name="rareDisease__research", curie=RDID.curie('research'),
                   model_uri=RDID.rareDisease__research, domain=None, range=Optional[Union[Union[dict, DrugAssociation], list[Union[dict, DrugAssociation]]]])

