![][image1]

**Monarch Initiative**

# Mondo Mapping Curation Guide

## **Last updated: June 2025**

# **OVERVIEW**

Here we present our mapping curation guidelines for Mondo. The report is targeting Mondo curators and users who want to understand how Mondo mapping curation works. 

# **GOALS**

1. Define a tiered approach for mapping curation  
2. Provide a set of mapping rules for common problems

# **Tiered approach for mapping curation**

There are three levels of mapping rigor in the Mondo curation pipeline:

1. **Core team-curated, precise mappings (Tier 1\)** include precision qualifiers such as “exact” or “broad” and are curated individually by Mondo curators  
2. **Community-curated, precise mappings (Tier 2\)** include precision qualifiers such as “exact” or “broad” and are curated by the disease community, but not always reviewed by the Mondo core team  
3. **AI-curated, precise mappings (Tier 3\)** include precision qualifiers such as “exact” or “broad” and are curated by an AI workflow, but not always reviewed by the Mondo core team  
4. **Community-curated mappings without explicit semantic precision (Tier 4\)** do not, or not consistently,  include precision qualifiers such as “exact” or “broad” and are curated by the disease community, but rarely reviewed by the Mondo core team.

We will discuss these groups in detail here

## **Core team-curated, precise mappings (Tier 1\)**

### Mapping representation:

* Mapping predicate MUST correspond to either skos:exactMatch, skos:narrowMatch, skos:relatedMatch, skos:closeMatch, or skos:broadMatch (in the Mondo ontology, these are represented by the following source annotations: MONDO:equivalentTo, MONDO:relatedTo, MONDO:mondoIsNarrowerThanSource, MONDO:relatedTo, and MONDO:mondoIsBroaderThanSource, respectively)  
* Mapping predicate SHOULD correspond to either skos:exactMatch or skos:broadMatch (the external concept is narrower). All other mapping predicates are very difficult to use analytically and should therefore be avoided. In cases where the external disease concept is fully out of scope for Mondo, a different predicate is acceptable, but an exclusion reason MUST be provided.  
* Mapping provenance MUST be one of the following:  
  * External source confirmation, i.e the ID of the class from which this mapping was sourced.  
    * The ID MUST correspond to an *explicit* skos:exactMatch to the Mondo class  
  * ORCID from a Mondo core team member

### Mapping rules:

* R1: Determine the correct mapping predicate:  
  * R1.1 If the two terms describe the same real-world concept, use skos:exactMatch. Please [study our guide](https://oboacademy.github.io/obook/howto/are-two-entities-the-same/) before reading this section \- this is a very hard task in practice.  
    * R1.1.1: The external concept MUST be a disease, not a phenotypic feature (sign or symptom) or a gene. For a detailed discussion on how to distinguish disease and phenotype, see [here](https://github.com/monarch-initiative/mondo/issues/7359).  
    * R1.1.2: The external concept MAY be conceptually conflated. We are open to the possibility that some conditions are represented in ICD-10 or SNOMED as *signs or symptoms*, while Mondo represents them as diseases. This is a murky area of disease data integration, so we choose to conflate diseases (disorders), signs, and symptoms (clinical findings) in some cases. SNOMED views, for example, disorders as subclasses for findings that are always abnormal. To support our use case (integrating all disease knowledge in a knowledge graph), we decide it is better to conflate the two. Not conflating would mean missing out on a potentially significant number of interesting associations in the data. Whether a symptom and a disease should be conflated or not is a very difficult problem that requires experience.  
      * Examples  
        * Acceptable conflations:  
          * disease/disorder (these are technically distinct)  
          * disease/phenotype(sign, symptom, clinical finding): cases where the distinction is murky, see [here](https://github.com/monarch-initiative/mondo/issues/7359).  
        * Not acceptable conflations:  
          * disease/phenotype(sign, symptom, clinical finding): cases were the distinction is clear-cut, see [here](https://github.com/monarch-initiative/mondo/issues/7359).  
    * R1.1.3 The external concept MUST NOT correspond to an undefined subset (see R2).  
  * R1.2: If the external term maps conceptually to a subclass of the Mondo class, and there is no other Mondo class that is equivalent to the external term (ie this disease does not exist in Mondo), use skos:narrowMatch (Mondo concept is broader than the external concept).  
  * R1.3: If the external term maps conceptually to a superclass of the Mondo class, and there is no other Mondo class that is equivalent to the external term (ie this disease does not exist in Mondo), use skos:broadMatch (Mondo concept is narrower than the external concept).  
  * R1.3: If the external term maps conceptually to a sibling of the Mondo class, and there is no other Mondo class that is equivalent to the external term (ie this disease does not exist in Mondo), use skos:closeMatch.  
  * R1.4: If the external term is conceptually related to the Mondo class, and there is no other Mondo class that is a suitable equivalent, broad, narrow or close match, use skos:relatedMatch. This should happen rarely, but usually occurs when the Mondo term is conceptually in a different branch (e.g. pheochromocytoma can refer to a benign tumor in one classification, and to a malignant one in another).  
* R2: External resource defines a concept that describes **a semantically undefined subset** of a larger class of diseases:  
  * “OTHER disease”:   
    * Example: “Epilepsy” in Mondo and “Other forms of epilepsy” in external terminology  
    * Rules:   
      * External concept MUST NOT be included in Mondo (as a MONDO id)  
      * External concept SHOULD be mapped as skos:narrowMatch (Mondo is BROADER than the external concept) to the Mondo more general term  
      * External concept should be excluded on the grounds of “MONDO:undefinedGrouping”  
  * “RELATED disease”  
    * Example: “Cancer” in Mondo and “cancer-related conditions” in external resource  
    * Rules:   
      * External concept SHOULD NOT be included in Mondo (if it does, it should be well justified)  
      * External concept MUST be mapped as skos:relatedMatch  
  * “disease UNSPECIFIED/EXCLUDING X”  
    * Example: ICD10CM G62.9 (Polyneuropathy, unspecified) excludes alcoholic polyneuropathy (G62.1)  
    * External concept MUST NOT be included as an exact match in Mondo (i.e., have a skos:exactMatch)  
    * External concept SHOULD be mapped as skos:narrowMatch (Mondo is BROADER than the external concept)  
    * External concept should be excluded on the grounds of “MONDO:undefinedGrouping”  
    * Note for curators: this class of disease terms should be ????

### Tier 1 resources in Mondo

* OMIM  
* Orphanet  
* DOID  
* NCIT  
* ICD10CM  
* ICD11 Foundation

## **Community-curated, precise mappings (Tier 2\)**

These mappings currently mostly come from the externally managed content (EMC) workflow.

### Mapping representation:

* Mapping predicate MUST correspond to either skos:exactMatch, skos:narrowMatch, skos:relatedMatch, skos:closeMatch or skos:broadMatch  
* Mapping predicate SHOULD correspond to either skos:exactMatch or skos:broadMatch (the external concept is narrower). All other mapping predicates are very difficult to use analytically and should therefore be avoided. In cases where the external disease concept is fully out of scope for Mondo, a different predicate is acceptable, but an exclusion reason MUST be provided.  
* Mapping provenance MUST be one of the following:  
  * External source confirmation (see Tier 1\)  
  * ORCID from a Mondo core team or community member  
  * ID of a known EMC (externally managed content) provider, e.g. MONDO:NORD or MONDO:MEDGEN.

### Mapping rules:

* R1: Proxy merges (two external concepts of the same resources are exact matches to a single Mondo ID) MUST NOT occur with community-curated mappings. If they do, a Mondo core curator needs to resolve the proxy merge.  
* R2: Reverse proxy merges (two Mondo concepts are exact matches to a single external resource ID) MUST NOT occur with community-curated mappings.

### Tier 2 resources in Mondo

* MEDGEN  
* UMLS  
* NORD

## **AI-curated, precise mappings (Tier 3\)**

### Mapping representation:

* Mapping predicate MUST correspond to either skos:exactMatch, skos:narrowMatch, skos:relatedMatch, skos:closeMatch or skos:broadMatch  
* Mapping predicate SHOULD correspond to either skos:exactMatch or skos:broadMatch (the external concept is narrower). All other mapping predicates are very difficult to use analytically and should therefore be avoided. In cases where the external disease concept is fully out of scope for Mondo, a different predicate is acceptable, but an exclusion reason MUST be provided.  
* Mapping provenance MUST be one of the following:  
  * sssom:mapping\_tool\_id and sssom:mapping\_tool\_version

### Mapping rules:

* R1: Proxy merges (two external concepts of the same resources are exact matches to a single Mondo ID) MUST NOT occur with AI-curated mappings. If they do, a Mondo core curator needs to resolve the proxy merge.  
* R2: Reverse proxy merges (two Mondo concepts are exact matches to a single external resource ID) MUST NOT occur with AI-curated mappings.

### Tier 3 resources in Mondo

* NA (Meddra, Mesh, ICD9?)

## **Community-curated mappings, without explicit semantic precision (Tier 4\)**

These mappings do not include semantic precision because the nature of the external source does not allow for a clear distinction. For example, NANDO terms represent both untractable diseases and diseases of childhood, without making the distinction between both. Therefore, it is not possible to determine whether a disease is specific to the “childhood onset” version of a disease or to the general disease. Therefore, precise semantics are not possible.

### Mapping representation:

* Mapping predicate SHOULD correspond to either skos:exactMatch or skos:broadMatch (the external concept is narrower), see Tier 1\.  
* Mapping provenance MUST be one of the following:  
  * External source confirmation (see Tier 1\)  
  * ORCID from a Mondo core team or community member  
  * ID of a known EMC (externally managed content) provider, e.g. MONDO:NANDO or MONDO:GARD.

### Mapping rules:

* R1: Proxy merges (two external concepts of the same resources are exact matches to a single Mondo ID) are acceptable  
* R2: Reverse proxy merges (two Mondo concepts are exact matches to a single external resource ID) MUST NOT occur with community-curated mappings.

### Tier 4 resources in Mondo

* NANDO  
* GARD

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAnAAAAAHCAYAAACIq3DzAAAAQUlEQVR4Xu3WMQ0AIADAMFziCFGYgx8FLOnRZwo25l4HAICO8QYAAP5m4AAAYgwcAECMgQMAiDFwAAAxBg4AIOYClIUh9UOLBN8AAAAASUVORK5CYII=>