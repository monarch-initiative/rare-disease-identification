(function () {
    "use strict";

    var DATA_URL = "data/prioritised-rare-disease-list.yml";
    var EPM_URL = "obo.epm.json";
    var PAGE_SIZE = 25;
    var FEEDBACK_REPO = "monarch-initiative/rare-disease-identification";

    // Display flag: prevalence_per_100k_us values in the source YAML are stored
    // as proportions despite the field name, and several entries have data-entry
    // errors. Hide all prevalence renderings until the upstream data is fixed.
    // Flip to true to re-enable filter, badge, and detail-row.
    var SHOW_PREVALENCE = false;

    var allDiseases = [];
    var filtered = [];
    var currentPage = 1;
    var activeFilters = {
        prioritization: new Set(),
        prevalence: new Set(),
        treatments: new Set(),
        functional: new Set(),
        category: new Set(),
        hpo: new Set(),
    };
    var searchQuery = "";
    var searchTimeout = null;
    var prefixMap = {}; // prefix -> uri_prefix (built from EPM)

    var PREVALENCE_LABELS = {
        L: "Low Prevalence",
        H: "High Prevalence",
        H_star: "High in Some Populations",
        H_uncertain: "Uncertain Prevalence",
    };

    var PRIORITIZATION_LABELS = {
        initial: "Initial Selection",
        expanded: "Expanded Selection",
    };

    var PRIORITIZATION_TOOLTIPS = {
        initial: "First expert-based prioritisation of diseases with high potential for phenotypic characterization impact",
        expanded: "Extended set of diseases added after initial expert review to broaden coverage",
    };

    var PREVALENCE_TOOLTIPS = {
        L: "Low prevalence in the general population",
        H: "High prevalence relative to other rare diseases",
        H_star: "High prevalence in some populations but not others",
        H_uncertain: "Prevalence data uncertain, possibly high",
    };

    var TREATMENT_LABELS = {
        has_indications: "Has approved indications",
        has_research: "Has research data",
        no_treatments: "No treatment data",
    };

    // -- EPM / CURIE resolution --

    var FUNCTIONAL_LABELS = {
        TOTAL: "Work: total impairment",
        SUBSTANTIAL: "Work: substantial",
        MILD: "Work: mild",
        NONE: "Work: none",
        VARIABLE: "Work: varies by subtype",
        NOT_APPLICABLE: "Work: not applicable",
        UNKNOWN: "Assessed, no usable evidence",
        disputed: "Lanes disagree (disputed)",
        not_curated: "Not yet curated"
    };

    function buildPrefixMap(epm) {
        epm.forEach(function (entry) {
            var uri = entry.uri_prefix;
            if (entry.prefix) {
                prefixMap[entry.prefix] = uri;
                prefixMap[entry.prefix.toLowerCase()] = uri;
            }
            (entry.prefix_synonyms || []).forEach(function (syn) {
                if (!prefixMap[syn]) prefixMap[syn] = uri;
                if (!prefixMap[syn.toLowerCase()]) prefixMap[syn.toLowerCase()] = uri;
            });
        });
        // Override some with browser-friendly URLs
        prefixMap["MONDO"] = "https://monarchinitiative.org/MONDO:";
        prefixMap["HP"] = "https://monarchinitiative.org/HP:";
        prefixMap["OMIM"] = "https://omim.org/entry/";
        prefixMap["OMIMPS"] = "https://omim.org/phenotypicSeries/";
        prefixMap["MEDGEN"] = "https://www.ncbi.nlm.nih.gov/medgen/";
        prefixMap["UMLS"] = "https://uts.nlm.nih.gov/uts/umls/concept/";
        prefixMap["Orphanet"] = "https://www.orpha.net/en/disease/detail/";
        prefixMap["GARD"] = "https://rarediseases.info.nih.gov/diseases/";
        prefixMap["DOID"] = "https://disease-ontology.org/?id=DOID:";
        prefixMap["DRUGBANK"] = "https://go.drugbank.com/drugs/";
        prefixMap["HGNC"] = "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:";
        prefixMap["NCIT"] = "https://ncit.nci.nih.gov/ncitbrowser/ConceptReport.jsp?dictionary=NCI_Thesaurus&code=";
        prefixMap["MESH"] = "https://meshb.nlm.nih.gov/record/ui?ui=";
        prefixMap["ICD10CM"] = "https://icd.codes/icd10cm/";
        prefixMap["SCTID"] = "https://browser.ihtsdotools.org/?perspective=full&conceptId1=";
    }

    function curieToUrl(curie) {
        if (!curie || curie.indexOf(":") === -1) return null;
        var idx = curie.indexOf(":");
        var prefix = curie.substring(0, idx);
        var local = curie.substring(idx + 1);
        // Try exact prefix, then lowercase
        var uri = prefixMap[prefix] || prefixMap[prefix.toLowerCase()];
        if (!uri) return null;
        // For Monarch-style URLs that include the prefix in the path
        if (uri.indexOf("monarchinitiative.org") !== -1) return uri + local;
        if (uri.indexOf("disease-ontology.org") !== -1) return uri + local;
        return uri + local;
    }

    function renderCurieLink(curie) {
        var url = curieToUrl(curie);
        if (url) {
            return '<a href="' + url + '" target="_blank" rel="noopener" class="curie-link">' + esc(curie) + '</a>';
        }
        return '<span class="curie-nolink">' + esc(curie) + '</span>';
    }

    // -- Data loading --

    async function loadData() {
        document.getElementById("results-container").innerHTML =
            '<div class="loading">Loading disease data...</div>';

        // Load EPM and data in parallel
        var [epmResp, dataResp] = await Promise.all([
            fetch(EPM_URL).catch(function () { return null; }),
            fetch(DATA_URL),
        ]);

        if (epmResp && epmResp.ok) {
            var epm = await epmResp.json();
            buildPrefixMap(epm);
        }

        var text = await dataResp.text();
        var data = jsyaml.load(text);
        allDiseases = data.diseases || [];
        filtered = allDiseases;
        renderHeaderStats();
        buildAllFilters();
        render();
    }

    function renderHeaderStats() {
        var el = document.getElementById("header-stats");
        el.innerHTML =
            '<span class="header-stat"><strong>' + allDiseases.length.toLocaleString() + '</strong> diseases</span>';
    }

    // -- Filters --

    function buildAllFilters() {
        buildFilterGroup("filter-prioritization", "prioritization",
            function (d) { return d.prioritization_category || "unknown"; }, PRIORITIZATION_LABELS);
        if (SHOW_PREVALENCE) {
            buildFilterGroup("filter-prevalence", "prevalence",
                function (d) { return d.prevalence_category || "unknown"; }, PREVALENCE_LABELS);
        } else {
            var prevGroup = document.getElementById("prevalence-filter-group");
            if (prevGroup) prevGroup.style.display = "none";
        }
        // Functional capacity: group by the work-capacity level, plus an explicit
        // "not yet curated" bucket so the 50 curated diseases are findable among 3,079.
        buildFilterGroup("filter-functional", "functional", function (d) {
            if (!d.work_capacity && !d.care_dependence) return "not_curated";
            if ((d.work_capacity && d.work_capacity.curation_status === "DISPUTED") ||
                (d.care_dependence && d.care_dependence.curation_status === "DISPUTED")) return "disputed";
            return (d.work_capacity && d.work_capacity.impairment) || "UNKNOWN";
        }, FUNCTIONAL_LABELS);

        buildFilterGroup("filter-treatments", "treatments", function (d) {
            if (d.indications && d.indications.length > 0) return "has_indications";
            if (d.research && d.research.length > 0) return "has_research";
            return "no_treatments";
        }, TREATMENT_LABELS);
        buildTopNFilter("filter-category", "category",
            function (d) { return (d.mondo_category_body_system || []).map(function (t) { return t.label || t; }); }, 15);
        buildTopNFilter("filter-hpo", "hpo",
            function (d) { return (d.hpo_high_level_categories || []).map(function (t) { return t.label || t; }); }, 12);
    }

    function buildFilterGroup(containerId, filterKey, accessor, labelMap) {
        var counts = {};
        allDiseases.forEach(function (d) {
            var v = accessor(d);
            counts[v] = (counts[v] || 0) + 1;
        });
        var container = document.getElementById(containerId);
        container.innerHTML = "";
        Object.entries(counts)
            .sort(function (a, b) { return b[1] - a[1]; })
            .forEach(function (pair) {
                var val = pair[0], count = pair[1];
                var label = document.createElement("label");
                var cb = document.createElement("input");
                cb.type = "checkbox";
                cb.value = val;
                cb.addEventListener("change", function () {
                    toggleFilter(filterKey, val, cb.checked);
                });
                label.appendChild(cb);
                var displayName = (labelMap && labelMap[val]) || val;
                label.appendChild(document.createTextNode(" " + displayName + " "));
                var span = document.createElement("span");
                span.className = "count";
                span.textContent = count;
                label.appendChild(span);
                container.appendChild(label);
            });
    }

    function buildTopNFilter(containerId, filterKey, accessor, topN) {
        var counts = {};
        allDiseases.forEach(function (d) {
            accessor(d).forEach(function (c) { counts[c] = (counts[c] || 0) + 1; });
        });
        var entries = Object.entries(counts).sort(function (a, b) { return b[1] - a[1]; }).slice(0, topN);
        var container = document.getElementById(containerId);
        container.innerHTML = "";
        entries.forEach(function (pair) {
            var val = pair[0], count = pair[1];
            var label = document.createElement("label");
            var cb = document.createElement("input");
            cb.type = "checkbox";
            cb.value = val;
            cb.addEventListener("change", function () {
                toggleFilter(filterKey, val, cb.checked);
            });
            label.appendChild(cb);
            label.appendChild(document.createTextNode(" " + val + " "));
            var span = document.createElement("span");
            span.className = "count";
            span.textContent = count;
            label.appendChild(span);
            container.appendChild(label);
        });
    }

    function toggleFilter(key, val, checked) {
        if (checked) activeFilters[key].add(val);
        else activeFilters[key].delete(val);
        applyFilters();
    }

    // -- Filtering --

    function applyFilters() {
        filtered = allDiseases.filter(function (d) {
            if (activeFilters.prioritization.size > 0 &&
                !activeFilters.prioritization.has(d.prioritization_category || "unknown"))
                return false;

            if (SHOW_PREVALENCE && activeFilters.prevalence.size > 0 &&
                !activeFilters.prevalence.has(d.prevalence_category || "unknown"))
                return false;

            if (activeFilters.functional.size > 0) {
                var fcTag;
                if (!d.work_capacity && !d.care_dependence) fcTag = "not_curated";
                else if ((d.work_capacity && d.work_capacity.curation_status === "DISPUTED") ||
                         (d.care_dependence && d.care_dependence.curation_status === "DISPUTED")) fcTag = "disputed";
                else fcTag = (d.work_capacity && d.work_capacity.impairment) || "UNKNOWN";
                if (!activeFilters.functional.has(fcTag)) return false;
            }

            if (activeFilters.treatments.size > 0) {
                var tag = "no_treatments";
                if (d.indications && d.indications.length > 0) tag = "has_indications";
                else if (d.research && d.research.length > 0) tag = "has_research";
                if (!activeFilters.treatments.has(tag)) return false;
            }

            if (activeFilters.category.size > 0) {
                var cats = (d.mondo_category_body_system || []).map(function (t) { return t.label || t; });
                if (!cats.some(function (c) { return activeFilters.category.has(c); })) return false;
            }

            if (activeFilters.hpo.size > 0) {
                var hpos = (d.hpo_high_level_categories || []).map(function (t) { return t.label || t; });
                if (!hpos.some(function (h) { return activeFilters.hpo.has(h); })) return false;
            }

            if (searchQuery) {
                var s = buildSearchString(d);
                if (s.indexOf(searchQuery) === -1) return false;
            }

            return true;
        });
        currentPage = 1;
        render();
    }

    function buildSearchString(d) {
        return [
            d.mondo_label, d.mondo_id,
            ...(d.mondo_synonyms || []),
            ...(d.keywords || []),
            ...(d.mondo_category_body_system || []).map(function (t) { return (t.label || "") + " " + (t.id || ""); }),
            ...(d.hpo_high_level_categories || []).map(function (t) { return (t.label || "") + " " + (t.id || ""); }),
            ...(d.ontology_terminology_codes || []),
            d.misdiagnosis_bias || "",
            ...(d.justification_summary || []),
            d.additional_justification || "",
        ].join(" ").toLowerCase();
    }

    // -- Rendering --

    function render() {
        document.getElementById("result-count").textContent =
            filtered.length + " of " + allDiseases.length + " diseases";
        var start = (currentPage - 1) * PAGE_SIZE;
        var page = filtered.slice(start, start + PAGE_SIZE);
        var container = document.getElementById("results-container");
        if (page.length === 0) {
            container.innerHTML = '<div class="loading">No diseases match your filters.</div>';
        } else {
            container.innerHTML = page.map(renderCard).join("");
        }
        renderPagination();
    }

    function renderCard(d) {
        var prioClass = d.prioritization_category || "";
        var prevCat = d.prevalence_category || "";
        var prevLabel = PREVALENCE_LABELS[prevCat] || prevCat;
        var prevClass = prevCat.startsWith("H") ? "prevalence-h" : "prevalence-l";
        var hasIndications = d.indications && d.indications.length > 0;
        var hasContraindications = d.contraindications && d.contraindications.length > 0;
        var hasResearch = d.research && d.research.length > 0;

        var hl = searchQuery ? function (t) { return highlightText(t, searchQuery); } : esc;
        var matched = findMatchedFields(d, searchQuery);

        var html = '<div class="disease-card">';

        // Match indicator
        if (matched.length > 0) {
            var firstMatch = matched[0];
            html += '<div class="match-indicator">Matched on <strong>' + esc(firstMatch.field) + '</strong>: ' +
                highlightText(truncate(firstMatch.value, 80), searchQuery) + '</div>';
        }

        // Header
        html += '<div class="card-header"><div>';
        html += '<h3>' + hl(d.mondo_label) + '</h3>';
        html += '<span class="mondo-id">' + renderCurieLink(d.mondo_id) + '</span>';
        html += '</div></div>';

        // Badges
        html += '<div class="card-badges">';
        if (prioClass) {
            var prioLabel = PRIORITIZATION_LABELS[prioClass] || prioClass;
            var prioTip = PRIORITIZATION_TOOLTIPS[prioClass] || "";
            html += renderTooltipTag(prioLabel, prioTip, "tag " + prioClass);
        }
        if (SHOW_PREVALENCE && prevCat) {
            var prevTip = PREVALENCE_TOOLTIPS[prevCat] || "";
            html += renderTooltipTag(prevLabel, prevTip, "tag " + prevClass);
        }
        if (hasIndications) html += '<span class="tag has-indications">Approved Indications</span>';
        if (hasContraindications) html += '<span class="tag has-contraindications">Contraindications</span>';
        if (d.work_capacity) html += renderFcBadge("Work", d.work_capacity);
        if (d.care_dependence) html += renderFcBadge("Care", d.care_dependence);
        (d.keywords || []).forEach(function (k) {
            html += '<span class="tag keyword">' + esc(k) + '</span>';
        });
        html += '</div>';

        // Body
        html += '<div class="card-body">';

        if (d.mondo_synonyms && d.mondo_synonyms.length > 0) {
            var syns = d.mondo_synonyms.slice(0, 6);
            html += '<div class="synonyms">Also known as: ' + syns.map(hl).join(", ");
            if (d.mondo_synonyms.length > 6) html += ", ...";
            html += '</div>';
        }

        // Functional capacity — curated work-capacity / care-dependence assessments.
        // Sits directly under the disease identity, above the category and phenotype
        // pill lists: it is a curated claim about the disease, and burying it below
        // a hundred HPO pills made it effectively invisible.
        html += renderFunctionalCapacity(d);

        // Categories — each type in its own labelled section
        var mondoCats = d.mondo_category_body_system || [];
        var hpoCats = d.hpo_high_level_categories || [];
        var histoCats = d.histopheno_categories || [];

        // MONDO high-level sub-categories (nested under Mondo)
        var mondoHLFields = [
            ["Organ/System", d.mondo_category_body_system],
            ["Process", d.mondo_category_developmental],
            ["Cause", d.mondo_category_etiologic],
            ["Genetic Basis", d.mondo_category_genetic],
            ["External Factor", d.mondo_category_extrinsic],
            ["Mechanism", d.mondo_category_molecular],
        ].filter(function (pair) { return pair[1] && pair[1].length > 0; });

        var hasMondo = mondoCats.length > 0 || mondoHLFields.length > 0;
        if (hasMondo || hpoCats.length > 0 || histoCats.length > 0) {
            html += '<div class="categories-block">';
            if (hasMondo) {
                html += '<div class="category-section"><span class="category-label tooltip-wrap">Disease Type' +
                    '<span class="tooltip-text">Disease classifications from the Mondo Disease Ontology, a unified resource for disease definitions</span></span><div>';
                if (mondoCats.length > 0) {
                    html += '<div class="category-list">';
                    mondoCats.forEach(function (t) { html += renderTermPill(t, "mondo"); });
                    html += '</div>';
                }
                if (mondoHLFields.length > 0) {
                    html += '<div class="mondo-hl-nested">';
                    mondoHLFields.forEach(function (pair) {
                        html += '<div class="mondo-hl-row"><span class="mondo-hl-label">' + pair[0] + ':</span> ';
                        html += pair[1].map(function (t) { return renderTermPill(t, "mondo"); }).join(" ");
                        html += '</div>';
                    });
                    html += '</div>';
                }
                html += '</div></div>';
            }
            if (hpoCats.length > 0) {
                html += '<div class="category-section"><span class="category-label tooltip-wrap">Phenotype Area' +
                    '<span class="tooltip-text">Broad clinical areas affected, from the Human Phenotype Ontology (HPO)</span></span>';
                html += '<div class="category-list">';
                hpoCats.forEach(function (t) { html += renderTermPill(t, "hpo"); });
                html += '</div></div>';
            }
            if (histoCats.length > 0) {
                html += '<div class="category-section"><span class="category-label tooltip-wrap">Tissue/System' +
                    '<span class="tooltip-text">Affected body tissues or organ systems</span></span>';
                html += '<div class="category-list">';
                histoCats.forEach(function (c) {
                    html += '<span class="category-pill histopheno">' + esc(c) + '</span>';
                });
                html += '</div></div>';
            }
            html += '</div>';
        }

        // Detail grid
        html += '<div class="detail-grid">';
        if (SHOW_PREVALENCE && d.prevalence_per_100k_us != null) {
            html += '<div class="detail-row"><strong>US Prevalence:</strong> ' +
                d.prevalence_per_100k_us + ' per 100k</div>';
        }
        if (d.hpo_treatment_rank != null) {
            html += '<div class="detail-row"><strong>HPO/Treatment Rank:</strong> ' +
                Number(d.hpo_treatment_rank).toFixed(3) + '</div>';
        }
        if (d.misdiagnosis_bias) {
            html += '<div class="detail-row full-width"><strong>Diagnosis Bias:</strong> ' +
                hl(d.misdiagnosis_bias) + '</div>';
        }
        if (d.justification_summary && d.justification_summary.length > 0) {
            var j = Array.isArray(d.justification_summary) ?
                d.justification_summary.join(", ") : d.justification_summary;
            html += '<div class="detail-row full-width"><strong>Justification:</strong> ' +
                hl(j) + '</div>';
        }
        if (d.additional_justification) {
            html += '<div class="detail-row full-width"><strong>Additional Detail:</strong> ' +
                highlightText(truncate(d.additional_justification, 200), searchQuery) + '</div>';
        }
        html += '</div>'; // detail-grid

        // Cross-references
        if (d.ontology_terminology_codes && d.ontology_terminology_codes.length > 0) {
            html += '<div class="xrefs-section"><strong>Cross-references:</strong> ';
            html += d.ontology_terminology_codes.map(renderCurieLink).join(", ");
            html += '</div>';
        }

        // HPO profiles (SimpleTerm pills, like categories)
        // Collapsed by default: a well-annotated disease carries over a hundred
        // pills here, which pushed everything below it off the screen. The count
        // stays visible so the profile's size is still legible while closed.
        var hpoProfiles = d.curated_hpo_profiles || [];
        if (hpoProfiles.length > 0) {
            var hpoId = "hpo-" + Math.random().toString(36).slice(2, 8);
            html += '<div class="card-subsection">';
            html += '<button class="subsection-toggle tooltip-wrap" onclick="toggleSection(\'' + hpoId + '\', this)">';
            html += '<span class="arrow">&#9654;</span> Phenotype Profile ' +
                '<span class="subsection-count">' + hpoProfiles.length + '</span>';
            html += '<span class="tooltip-text">Key clinical signs and symptoms (phenotypes) associated with this disease, drawn from the Human Phenotype Ontology (HPO)</span>';
            html += '</button>';
            html += '<div class="section-content" id="' + hpoId + '">';
            html += '<div class="category-list">';
            hpoProfiles.forEach(function (t) { html += renderTermPill(t, "hpo"); });
            html += '</div></div></div>';
        }

        html += '</div>'; // card-body

        // Disease context for feedback
        var diseaseCtx = { disease_id: d.mondo_id, disease_label: d.mondo_label };

        // Approved indications section
        if (hasIndications) {
            html += renderCollapsibleSection("indications", d.indications,
                "Approved Indications (" + d.indications.length + ")",
                renderIndicationEntry, diseaseCtx);
        }

        // Contraindications section
        if (hasContraindications) {
            html += renderCollapsibleSection("contraindications", d.contraindications,
                "Contraindications (" + d.contraindications.length + ")",
                renderContraindicationEntry, diseaseCtx);
        }

        // Research section
        if (hasResearch) {
            html += renderCollapsibleSection("research", d.research,
                "Treatment Research (" + d.research.length + " entries)",
                renderResearchEntry, diseaseCtx);
        }

        html += '</div>'; // disease-card
        return html;
    }


    // ---------------------------------------------------------------- Functional capacity
    // Two curated assessments per disease: can affected people sustain work, and do
    // they need daily personal care. Rendering rules that matter here:
    //   * UNKNOWN is shown, never hidden. "Assessed and nothing found" is a curated
    //     result in this dataset, and silently dropping it would misrepresent coverage.
    //   * care_context is always shown next to the level, because an assessment built
    //     from untreated natural history must not be read as the current expectation.
    //   * DISPUTES evidence is styled apart from SUPPORTS, so a reader sees that the
    //     lanes disagreed rather than only the headline.

    var IMPAIRMENT_TIPS = {
        NONE: "Typical affected people are not meaningfully impaired in this capacity.",
        MILD: "Harder, but most affected people manage without help or accommodation.",
        SUBSTANTIAL: "A serious barrier: at least ~30% need accommodation, reduced hours, or regular assistance.",
        TOTAL: "At least ~30% cannot sustain competitive employment at all, or need daily personal assistance.",
        VARIABLE: "Genuinely varies by subtype, stage, or treatment response; no single level is representative.",
        NOT_APPLICABLE: "The question does not arise — chiefly work capacity for a disease lethal before working age.",
        UNKNOWN: "Assessed, but no usable evidence was found. See the rationale for what was searched."
    };
    var CARE_CONTEXT_TIPS = {
        STANDARD_OF_CARE_TREATED: "Describes the course under current standard of care. The only context that may inform policy use.",
        UNTREATED_NATURAL_HISTORY: "Describes the UNTREATED course. Must not be presented as the current expectation.",
        TREATMENT_REFRACTORY: "Describes the course in people who do not respond to standard treatment.",
        UNKNOWN: "The source does not say which course it describes."
    };
    var FC_LANE_TIPS = {
        EXPERT_DATABASE: "A curated database rating functional consequence directly — chiefly Orphanet, which names its validating expert.",
        FEDERAL_POLICY_LIST: "A national determination that the disease qualifies — the SSA Compassionate Allowances list, which certifies that a condition precludes substantial gainful activity.",
        STATE_POLICY_LIST: "A state Medicaid medically-frail condition list, keyed to ICD-10-CM codes.",
        LITERATURE: "A peer-reviewed publication reporting employment, ADL, caregiver-burden or functional outcomes. Every quote is machine-checked against the cached source.",
        MODEL_JUDGEMENT: "A language model's structured judgement from the disease description. Never sufficient alone.",
        COMPUTED_SCORE: "The phenotype-based score. A ranking signal, not a finding."
    };
    var FC_STRENGTH_TIPS = {
        STRONG: "Direct measurement in an identified human cohort, or a named expert's rating of this disease.",
        MODERATE: "Indirect, small, or from a closely related disease.",
        WEAK: "Inference, opinion, or unbenchmarked model output."
    };
    var FC_DIRECTION_TIPS = {
        SUPPORTS: "Supports the stated impairment level.",
        DISPUTES: "Argues for a LOWER impairment level than stated.",
        NEUTRAL: "Relevant but does not move the assessment."
    };
    var FC_STATUS_TIPS = {
        UNREVIEWED: "Proposed by the pipeline; no curator has looked.",
        AI_CURATED: "Evidence gathered and synthesised by an agent, awaiting human review.",
        EXPERT_REVIEWED: "A named human clinician has reviewed and accepted this.",
        DISPUTED: "Evidence lanes conflict and a human must resolve it.",
        REJECTED: "Reviewed and rejected; kept so the rejection stays visible."
    };
    var FC_AXES = [
        ["work_capacity", "Work capacity", "Can affected adults of working age sustain competitive employment?"],
        ["care_dependence", "Care dependence", "Do affected people need daily personal assistance or supervision?"]
    ];

    function fcClass(level) {
        return "fc-" + String(level || "unknown").toLowerCase();
    }

    // Compact badge for the card header, e.g. "Work: TOTAL".
    function renderFcBadge(short, a) {
        var lvl = a.impairment || "UNKNOWN";
        var tip = short + " — " + (IMPAIRMENT_TIPS[lvl] || "");
        if (a.care_context && a.care_context !== "UNKNOWN") {
            tip += " Context: " + a.care_context.replace(/_/g, " ").toLowerCase() + ".";
        }
        var label = short + ": " + lvl.replace(/_/g, " ");
        return withTip('<span class="tag fc-tag ' + fcClass(lvl) + '">' + esc(label) + '</span>', tip);
    }

    function renderFcEvidence(e) {
        var dir = e.direction || "SUPPORTS";
        var html = '<div class="fc-evidence ' + dir.toLowerCase() + '">';

        html += '<div class="fc-ev-top">';
        if (e.lane) {
            html += withTip('<span class="fc-lane ' + e.lane.toLowerCase() + '">' +
                esc(e.lane.replace(/_/g, " ")) + '</span>', FC_LANE_TIPS[e.lane] || "");
        }
        if (dir !== "SUPPORTS") {
            html += withTip('<span class="fc-dir ' + dir.toLowerCase() + '">' + esc(dir) + '</span>',
                FC_DIRECTION_TIPS[dir] || "");
        }
        if (e.strength) {
            html += withTip('<span class="fc-strength ' + e.strength.toLowerCase() + '">' +
                esc(e.strength) + '</span>', FC_STRENGTH_TIPS[e.strength] || "");
        }
        if (e.reference) {
            html += '<span class="fc-ref">' + renderFcRefLink(e.reference) + '</span>';
        }
        html += '</div>';

        if (e.reference_title) {
            html += '<div class="fc-ev-title">' + esc(e.reference_title) + '</div>';
        }
        // A quote is verbatim source text; a source_statement is the structured row a
        // database or policy list asserts. Only one is present per line.
        if (e.quote) {
            html += '<div class="fc-quote">' + esc(e.quote) + '</div>';
        } else if (e.source_statement) {
            html += '<div class="fc-statement">' + esc(e.source_statement) + '</div>';
        }
        if (e.population) {
            html += '<div class="fc-population"><strong>Population:</strong> ' + esc(e.population) + '</div>';
        }
        if (e.explanation) {
            html += '<div class="fc-ev-explanation">' + esc(e.explanation) + '</div>';
        }
        html += '</div>';
        return html;
    }

    // Internal run identifiers (RDIDRUN:) are provenance, not links.
    function renderFcRefLink(ref) {
        if (!ref) return "";
        if (ref.indexOf("RDIDRUN:") === 0) {
            return '<span class="fc-ref-internal">' + esc(ref.replace("RDIDRUN:", "")) + '</span>';
        }
        if (ref.indexOf("SSACAL:") === 0) {
            var sec = ref.replace("SSACAL:", "");
            return '<a href="https://secure.ssa.gov/apps10/poms.nsf/lnx/0' + esc(sec) +
                '" target="_blank" rel="noopener">' + esc(ref) + '</a>';
        }
        if (ref.indexOf("ORPHA:") === 0) {
            return '<a href="https://www.orpha.net/en/disease/detail/' + esc(ref.replace("ORPHA:", "")) +
                '" target="_blank" rel="noopener">' + esc(ref) + '</a>';
        }
        if (ref.indexOf("ICD10CM:") === 0) {
            return '<span class="fc-ref-internal">' + esc(ref) + '</span>';
        }
        return renderRefLink(ref);
    }

    function renderFcAssessment(key, title, axisTip, a) {
        var lvl = a.impairment || "UNKNOWN";
        var html = '<div class="fc-assessment">';

        html += '<div class="fc-head">';
        html += '<span class="fc-axis tooltip-wrap">' + esc(title) +
            '<span class="tooltip-text">' + esc(axisTip) + '</span></span>';
        html += withTip('<span class="fc-level ' + fcClass(lvl) + '">' + esc(lvl.replace(/_/g, " ")) + '</span>',
            IMPAIRMENT_TIPS[lvl] || "");
        if (a.care_context) {
            var ctxClass = a.care_context === "UNTREATED_NATURAL_HISTORY" ? "warn" : "";
            html += withTip('<span class="fc-context ' + ctxClass + '">' +
                esc(a.care_context.replace(/_/g, " ").toLowerCase()) + '</span>',
                CARE_CONTEXT_TIPS[a.care_context] || "");
        }
        if (a.life_stage) {
            html += withTip('<span class="fc-stage">' + esc(a.life_stage.replace(/_/g, " ").toLowerCase()) + '</span>',
                "Life stage this assessment applies to.");
        }
        if (a.curation_status) {
            html += withTip('<span class="fc-status ' + a.curation_status.toLowerCase() + '">' +
                esc(a.curation_status.replace(/_/g, " ")) + '</span>', FC_STATUS_TIPS[a.curation_status] || "");
        }
        html += '</div>';

        if (a.rationale) {
            html += '<div class="fc-rationale">' + esc(a.rationale) + '</div>';
        }

        var ev = a.evidence || [];
        if (ev.length > 0) {
            var evId = "fcev-" + Math.random().toString(36).slice(2, 8);
            var nDisputes = ev.filter(function (e) { return e.direction === "DISPUTES"; }).length;
            var label = ev.length + " evidence line" + (ev.length === 1 ? "" : "s");
            if (nDisputes > 0) label += " · " + nDisputes + " disputing";
            html += '<button class="fc-ev-toggle" onclick="toggleSection(\'' + evId + '\', this)">' +
                '<span class="arrow">&#9654;</span> ' + esc(label) + '</button>';
            html += '<div class="section-content" id="' + evId + '">';
            ev.forEach(function (e) { html += renderFcEvidence(e); });
            html += '</div>';
        }

        html += '</div>';
        return html;
    }

    function renderFunctionalCapacity(d) {
        var present = FC_AXES.filter(function (ax) { return d[ax[0]]; });
        if (present.length === 0) return "";

        var parts = present.map(function (ax) { return ax[1] + " " + (d[ax[0]].impairment || "UNKNOWN"); });
        var id = "fc-" + Math.random().toString(36).slice(2, 8);

        var html = '<div class="card-section">';
        html += '<button class="section-toggle" onclick="toggleSection(\'' + id + '\', this)">';
        html += '<span class="arrow">&#9654;</span> Functional Capacity — ' + esc(parts.join(" · "));
        html += '</button>';
        html += '<div class="section-content" id="' + id + '">';
        html += '<p class="fc-disclaimer">These are disease-level expectations assembled from published ' +
            'sources. They describe what is typical for a disease, and are not an assessment of any person.</p>';
        present.forEach(function (ax) {
            html += renderFcAssessment(ax[0], ax[1], ax[2], d[ax[0]]);
        });
        html += '</div></div>';
        return html;
    }

    // -- SimpleTerm rendering --

    function renderTermPill(term, type) {
        var label = term.label || term;
        var id = term.id || "";
        var cls = "category-pill " + type;
        if (id) {
            var url = curieToUrl(id);
            if (url) {
                return '<a href="' + url + '" target="_blank" rel="noopener" class="' + cls + '">' +
                    esc(label) + ' <span class="pill-id">' + esc(id) + '</span></a>';
            }
        }
        return '<span class="' + cls + '">' + esc(label) + '</span>';
    }

    function renderTermLink(term, type) {
        var label = term.label || term;
        var id = term.id || "";
        if (id) {
            var url = curieToUrl(id);
            if (url) {
                return '<a href="' + url + '" target="_blank" rel="noopener" class="term-link ' + type + '" title="' + esc(id) + '">' + esc(label) + '</a>';
            }
        }
        return '<span class="term-nolink">' + esc(label) + '</span>';
    }

    // -- Collapsible sections --

    function renderCollapsibleSection(type, items, title, renderFn, diseaseCtx) {
        var id = type + "-" + Math.random().toString(36).slice(2, 8);
        var html = '<div class="card-section">';
        html += '<button class="section-toggle" onclick="toggleSection(\'' + id + '\', this)">';
        html += '<span class="arrow">&#9654;</span> ' + title;
        html += '</button>';
        html += '<div class="section-content" id="' + id + '">';
        items.forEach(function (item, idx, arr) { html += renderFn(item, idx, arr, diseaseCtx); });
        html += '</div></div>';
        return html;
    }

    // Tooltip explanations for evidence-card badges. Hover any badge → see what the value means.
    var APPROVAL_STATUS_TIPS = {
        APPROVED: "Drug is approved by this regulator for the indication.",
        WITHDRAWN: "Approval was granted and later withdrawn.",
        DISCONTINUED: "Drug is discontinued.",
        INVESTIGATIONAL: "Drug is under investigation; no approval yet.",
        OFF_LABEL: "Use is off-label (not in the approved indications)."
    };
    var SOURCE_ROLE_TIPS = {
        PRIMARY: "Primary canonical source for this assertion (e.g. official EPAR or BLA record).",
        INTERMEDIARY: "Intermediary or fallback source repeating a primary source (e.g. a DailyMed label mirroring the FDA approval)."
    };
    var EVIDENCE_SOURCE_TIPS = {
        HUMAN_CLINICAL: "Evidence from human clinical data (trial, case report).",
        MODEL_ORGANISM: "Evidence from animal / model organism studies.",
        IN_VITRO: "Evidence from in vitro / cell-based studies.",
        COMPUTATIONAL: "Evidence from computational / in silico analyses.",
        OTHER: "Other or unspecified provenance."
    };
    var SUPPORT_TIPS = {
        SUPPORT: "Evidence supports the assertion.",
        REFUTE: "Evidence refutes the assertion.",
        PARTIAL: "Evidence partially supports the assertion.",
        NO_EVIDENCE: "No evidence either way."
    };
    var SOURCE_TYPE_TIPS = {
        REGULATORY: "Regulatory agency document (drug label, EPAR, etc.).",
        LITERATURE: "Published literature (PMID, PMC, journal article).",
        GUIDELINE: "Clinical practice guideline.",
        DATABASE: "Curated database or registry.",
        POST_MARKET: "Post-market surveillance / real-world evidence."
    };
    var CONFIDENCE_LEVELS = { HIGH: "HIGH", MEDIUM: "MEDIUM", LOW: "LOW" };
    var AUTHORITY_TIPS = {
        FDA: "U.S. Food and Drug Administration",
        EMA: "European Medicines Agency",
        PMDA: "Japan Pharmaceuticals and Medical Devices Agency",
        CDSCO: "Central Drugs Standard Control Organisation (India)",
        MOH_RUSSIA: "Ministry of Health of the Russian Federation",
        NMPA_CHINA: "National Medical Products Administration (China)",
        OTHER: "Other regulator"
    };
    var CURATION_STATUS_TIPS = {
        DRAFT: "Draft / unreviewed by a human curator.",
        IN_REVIEW: "Currently under expert review.",
        APPROVED: "Curator-approved.",
        REJECTED: "Curator-rejected."
    };
    var DEEP_RESEARCH_TIP = "AI deep research was used to surface this association (e.g. Perplexity / Falcon Edison Scientific Literature).";

    function withTip(inner, tip) {
        if (!tip) return inner;
        return '<span class="badge-tip">' + inner + '<span class="tooltip-text">' + esc(tip) + '</span></span>';
    }

    function renderEvidenceCard(e, context) {
        var html = '<div class="evidence-card">';

        // Top row: source, jurisdiction, approval, confidence, source button, feedback button
        html += '<div class="evidence-top-row">';
        html += '<div class="evidence-top-left">';

        // Source badge
        var sourceType = (e.source && e.source.type) || e.source_type || "";
        var sourceName = (e.source && e.source.name) || sourceType || "";
        var jurisdiction = (e.source && e.source.jurisdiction) || e.jurisdiction || "";
        if (sourceName) {
            var badgeClass = sourceType ? sourceType.toLowerCase() : "unknown";
            var displaySource = sourceName;
            if (jurisdiction) displaySource += " (" + jurisdiction + ")";
            var srcTip = (e.source && e.source.description) ||
                SOURCE_TYPE_TIPS[sourceType] ||
                "Where this evidence was extracted from.";
            html += withTip('<span class="evidence-badge ' + badgeClass + '">' + esc(displaySource) + '</span>', srcTip);
        }

        // Source role (PRIMARY / INTERMEDIARY)
        if (e.source_role) {
            var roleTip = SOURCE_ROLE_TIPS[e.source_role] || "Source role";
            html += withTip('<span class="role-badge ' + e.source_role.toLowerCase() + '">' + esc(e.source_role) + '</span>', roleTip);
        }

        // Approval status (+ approval date if present)
        if (e.approval_status) {
            var statusClass = e.approval_status.toLowerCase().replace(/[^a-z]/g, "_");
            var approvalText = e.approval_status;
            if (e.approval_date) approvalText += " · " + e.approval_date;
            var approvalTip = APPROVAL_STATUS_TIPS[e.approval_status] || "Regulatory approval status.";
            if (e.approval_date) approvalTip += " Approval date: " + e.approval_date + ".";
            html += withTip('<span class="approval-badge ' + statusClass + '">' + esc(approvalText) + '</span>', approvalTip);
        } else if (e.approval_date) {
            html += withTip('<span class="date-badge">' + esc(e.approval_date) + '</span>', "Approval date.");
        }

        // Max research phase
        if (e.max_research_phase) {
            html += withTip('<span class="phase-badge">' + esc(e.max_research_phase.replace(/_/g, " ")) + '</span>',
                "Highest research phase reached for this indication.");
        }

        // Evidence source (HUMAN_CLINICAL, etc.)
        if (e.evidence_source) {
            var esTip = EVIDENCE_SOURCE_TIPS[e.evidence_source] || "Provenance of the underlying evidence.";
            html += withTip('<span class="evidence-source-badge">' + esc(e.evidence_source.replace(/_/g, " ")) + '</span>', esTip);
        }

        // Confidence indicators. Three independent dimensions:
        //   drug    — grounding of the source drug string to a CURIE (CHEBI / UNII / DRUGBANK)
        //   disease — grounding of the source disease string to a MONDO ID
        //   link    — extraction quality: did we correctly read the source as asserting a
        //             drug-disease relationship at all? Independent of grounding.
        // Tooltips also surface pre-grounding "original" strings when MEDIC carries them.
        var confDrug = e.confidence_drug || e.confidence || "";
        var confDisease = e.confidence_disease || e.confidence || "";
        var confAssoc = e.confidence_association || e.confidence || "";
        if (confDrug || confDisease || confAssoc) {
            var origDrugLabel = e.original_drug_label || "";
            var origDrugId = e.original_drug_id || "";
            var origDiseaseLabel = e.original_disease_label || "";
            var origDiseaseId = e.original_disease_id || "";
            var drugTip = "Drug grounding — how sure we are the drug name in the source was correctly mapped to its database ID. Currently " + confDrug + ".";
            if (origDrugLabel || origDrugId) {
                drugTip += " Source said: " + (origDrugLabel ? "‘" + origDrugLabel + "’" : "") + (origDrugId ? " [" + origDrugId + "]" : "") + ".";
            }
            var diseaseTip = "Disease grounding — how sure we are the disease name in the source was correctly mapped to a MONDO term. Currently " + confDisease + ".";
            if (origDiseaseLabel || origDiseaseId) {
                diseaseTip += " Source said: " + (origDiseaseLabel ? "‘" + origDiseaseLabel + "’" : "") + (origDiseaseId ? " [" + origDiseaseId + "]" : "") + ".";
            }
            var assocTip = "Drug–disease link — how sure we are the source genuinely asserts this drug for this disease, separate from how well the names were mapped. A label can mention both clearly without strongly linking them. Currently " + confAssoc + ".";
            html += '<span class="confidence-group">';
            if (confDrug) html += '<span class="conf-dot tooltip-wrap ' + confDrug.toLowerCase() + '">drug<span class="tooltip-text">' + esc(drugTip) + '</span></span>';
            if (confDisease) html += '<span class="conf-dot tooltip-wrap ' + confDisease.toLowerCase() + '">disease<span class="tooltip-text">' + esc(diseaseTip) + '</span></span>';
            if (confAssoc) html += '<span class="conf-dot tooltip-wrap ' + confAssoc.toLowerCase() + '">link<span class="tooltip-text">' + esc(assocTip) + '</span></span>';
            html += '</span>';
        }

        // Support indicator
        if (e.support) {
            var supportClass = e.support.toLowerCase().replace(/[^a-z]/g, "_");
            var supTip = SUPPORT_TIPS[e.support] || "Whether evidence supports or refutes the assertion.";
            html += withTip('<span class="support-badge ' + supportClass + '">' + esc(e.support) + '</span>', supTip);
        }

        // Source button — compact link to the regulator/document. Only when reference is a URL.
        var refIsUrl = e.reference && /^https?:\/\//.test(e.reference);
        if (refIsUrl) {
            html += '<a class="source-btn" href="' + esc(e.reference) + '" target="_blank" rel="noopener" ' +
                'title="' + escAttr("Open source document: " + e.reference) + '">' +
                'source <span class="ext-arrow">&#8599;</span></a>';
        }

        html += '</div>'; // evidence-top-left

        // Feedback button
        var feedbackId = "fb-" + Math.random().toString(36).slice(2, 10);
        html += '<button class="feedback-btn" data-feedback-id="' + feedbackId + '" title="Report issue with this evidence">';
        html += '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
            '<path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/>' +
            '</svg>';
        html += '</button>';

        html += '</div>'; // evidence-top-row

        // Reference line — only show when reference is a CURIE / non-URL identifier.
        // URL references are surfaced by the "source" button in the badge row above.
        if ((e.reference && !refIsUrl) || e.reference_title) {
            html += '<div class="evidence-ref-line">';
            if (e.reference && !refIsUrl) {
                html += '<span class="evidence-ref">' + renderRefLink(e.reference) + '</span>';
            }
            if (e.reference_title) {
                html += '<span class="evidence-ref-title">' + esc(e.reference_title) + '</span>';
            }
            html += '</div>';
        }

        // Snippet
        if (e.snippet) {
            html += '<div class="evidence-snippet">' + esc(e.snippet) + '</div>';
        }

        // Explanation / interpreted_text
        var explanation = e.explanation || e.interpreted_text || "";
        if (explanation) {
            html += '<div class="evidence-explanation">' + esc(explanation) + '</div>';
        }

        // Curator. When curator_id is a URL (e.g. AI_AGENT pointing at the SKILL.md),
        // render the curator name as a link to that URL.
        if (e.curator) {
            var curatorIsObj = (typeof e.curator === "object");
            var curatorName = curatorIsObj ? (e.curator.name || "") : String(e.curator);
            var curatorType = curatorIsObj ? (e.curator.curator_type || "") : "";
            var curatorId = curatorIsObj ? (e.curator.curator_id || "") : "";
            var curatorUrl = (curatorId && /^https?:\/\//.test(curatorId)) ? curatorId : "";
            if (curatorName) {
                html += '<div class="evidence-curator">';
                if (curatorType) html += '<span class="curator-type">' + esc(curatorType.replace(/_/g, " ")) + '</span>';
                if (curatorUrl) {
                    html += '<a class="curator-link" href="' + esc(curatorUrl) + '" target="_blank" rel="noopener" ' +
                        'title="' + escAttr("Open curator source: " + curatorUrl) + '">' +
                        esc(curatorName) + ' <span class="ext-arrow">&#8599;</span></a>';
                } else {
                    html += esc(curatorName);
                }
                html += '</div>';
            }
        }

        // Feedback form (hidden by default)
        html += '<div class="feedback-form" id="' + feedbackId + '" ' +
            'data-context="' + escAttr(JSON.stringify(context)) + '">';
        html += '<textarea class="feedback-text" placeholder="Describe what is wrong with this evidence (optional)..." rows="2"></textarea>';
        html += '<div class="feedback-actions">';
        html += '<button class="feedback-submit" data-feedback-id="' + feedbackId + '">Open Issue on GitHub</button>';
        html += '<button class="feedback-cancel" data-feedback-id="' + feedbackId + '">Cancel</button>';
        html += '</div></div>';

        html += '</div>'; // evidence-card
        return html;
    }

    function renderRegulatoryStatusBlock(regList) {
        if (!regList || regList.length === 0) return "";
        var html = '<div class="reg-status-block">';
        html += '<div class="reg-status-label">Regulatory status</div>';
        html += '<ul class="reg-status-list">';
        regList.forEach(function (rs) {
            var authority = rs.authority || "";
            var status = rs.status || "";
            var statusClass = status ? status.toLowerCase().replace(/[^a-z]/g, "_") : "";
            html += '<li class="reg-status-row">';
            if (authority) {
                var authTip = AUTHORITY_TIPS[authority] || "Regulatory authority";
                html += withTip('<span class="reg-authority ' + authority.toLowerCase() + '">' + esc(authority) + '</span>', authTip);
            }
            if (status) {
                var statusTip = APPROVAL_STATUS_TIPS[status] || "Regulatory approval status.";
                html += withTip('<span class="approval-badge ' + statusClass + '">' + esc(status) + '</span>', statusTip);
            }
            if (rs.approval_date) {
                html += withTip('<span class="date-badge">' + esc(rs.approval_date) + '</span>', "Date of approval / market authorisation.");
            }
            if (rs.source_role) {
                var roleTip = SOURCE_ROLE_TIPS[rs.source_role] || "Source role";
                html += withTip('<span class="role-badge ' + rs.source_role.toLowerCase() + '">' + esc(rs.source_role) + '</span>', roleTip);
            }
            if (rs.regulatory_document_url) {
                html += ' <a class="reg-doc-link" href="' + esc(rs.regulatory_document_url) +
                    '" target="_blank" rel="noopener" title="' + escAttr(rs.regulatory_document_url) +
                    '">document &#8599;</a>';
            }
            html += '</li>';
        });
        html += '</ul></div>';
        return html;
    }

    function renderResearchHeaderBlock(r) {
        var bits = [];
        if (r.notes) {
            bits.push('<div class="drug-notes">' + esc(r.notes) + '</div>');
        }
        var meta = [];
        if (r.curation_date) {
            var d = String(r.curation_date).slice(0, 10);
            meta.push('Curated <span class="curation-date">' + esc(d) + '</span>');
        }
        var topCurator = r.curator;
        if (topCurator) {
            var name = (typeof topCurator === "string") ? topCurator : (topCurator.name || "");
            if (name) meta.push('by <span class="curation-curator">' + esc(name) + '</span>');
        }
        if (meta.length) {
            bits.push('<div class="curation-meta">' + meta.join(" ") + '</div>');
        }
        return bits.join("");
    }

    function renderDrugAssocEntry(item, sectionKind, diseaseCtx) {
        var html = '<div class="drug-entry ' + sectionKind + '">';
        html += '<div class="drug-header">';
        html += '<span class="drug-name">' + esc(item.drug_label) + '</span>';
        if (item.drug_id) {
            html += ' ' + renderCurieLink(item.drug_id);
        }
        if (sectionKind === "research") {
            if (item.curation_status) {
                var cs = item.curation_status.toLowerCase().replace(/[^a-z]/g, "_");
                var csTip = CURATION_STATUS_TIPS[item.curation_status] || "Curation lifecycle status.";
                html += withTip('<span class="curation-status-badge ' + cs + '">' + esc(item.curation_status) + '</span>', csTip);
            }
            if (item.deep_research_used) {
                html += withTip('<span class="deep-research-badge">deep research</span>', DEEP_RESEARCH_TIP);
            }
        }
        html += '</div>';

        if (sectionKind === "research") {
            html += renderResearchHeaderBlock(item);
        } else {
            html += renderRegulatoryStatusBlock(item.regulatory_status);
        }

        (item.evidence || []).forEach(function (e) {
            var context = {
                disease_id: diseaseCtx.disease_id,
                disease_label: diseaseCtx.disease_label,
                drug_label: item.drug_label,
                drug_id: item.drug_id || "",
                section: sectionKind,
                source: (e.source && e.source.name) || e.source_type || "",
                reference: e.reference || "",
            };
            html += renderEvidenceCard(e, context);
        });
        html += '</div>';
        return html;
    }

    function renderIndicationEntry(ind, _idx, _arr, diseaseCtx) {
        return renderDrugAssocEntry(ind, "indication", diseaseCtx);
    }

    function renderContraindicationEntry(ci, _idx, _arr, diseaseCtx) {
        return renderDrugAssocEntry(ci, "contraindication", diseaseCtx);
    }

    function renderResearchEntry(r, _idx, _arr, diseaseCtx) {
        return renderDrugAssocEntry(r, "research", diseaseCtx);
    }

    // -- Helpers --

    function highlightText(text, query) {
        if (!query || !text) return esc(text);
        var escaped = esc(text);
        var lc = escaped.toLowerCase();
        var idx = lc.indexOf(query.toLowerCase());
        if (idx === -1) return escaped;
        return escaped.substring(0, idx) +
            '<mark class="search-match">' + escaped.substring(idx, idx + query.length) + '</mark>' +
            escaped.substring(idx + query.length);
    }

    function findMatchedFields(d, query) {
        if (!query) return [];
        var q = query.toLowerCase();
        var matches = [];
        var fields = [
            ["Name", d.mondo_label],
            ["ID", d.mondo_id],
            ["Synonym", (d.mondo_synonyms || []).find(function (s) { return s.toLowerCase().indexOf(q) !== -1; })],
            ["Keyword", (d.keywords || []).find(function (s) { return s.toLowerCase().indexOf(q) !== -1; })],
            ["Disease Type", (d.mondo_category_body_system || []).map(function (t) { return t.label || ""; }).find(function (s) { return s.toLowerCase().indexOf(q) !== -1; })],
            ["Disease Type ID", (d.mondo_category_body_system || []).map(function (t) { return t.id || ""; }).find(function (s) { return s.toLowerCase().indexOf(q) !== -1; })],
            ["Phenotype Area", (d.hpo_high_level_categories || []).map(function (t) { return t.label || ""; }).find(function (s) { return s.toLowerCase().indexOf(q) !== -1; })],
            ["Cross-reference", (d.ontology_terminology_codes || []).find(function (s) { return s.toLowerCase().indexOf(q) !== -1; })],
            ["Diagnosis Bias", d.misdiagnosis_bias],
            ["Justification", (d.justification_summary || []).find(function (s) { return s.toLowerCase().indexOf(q) !== -1; })],
            ["Additional Detail", d.additional_justification],
        ];
        fields.forEach(function (pair) {
            var val = pair[1];
            if (val && String(val).toLowerCase().indexOf(q) !== -1) {
                matches.push({ field: pair[0], value: String(val) });
            }
        });
        return matches;
    }

    function renderTooltipTag(label, tip, cls) {
        if (tip) {
            return '<span class="tooltip-wrap ' + cls + '">' + esc(label) +
                '<span class="tooltip-text">' + esc(tip) + '</span></span>';
        }
        return '<span class="' + cls + '">' + esc(label) + '</span>';
    }

    function esc(s) {
        if (!s) return "";
        var el = document.createElement("span");
        el.textContent = s;
        return el.innerHTML;
    }

    function escAttr(s) {
        if (!s) return "";
        return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#39;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function truncate(s, max) {
        if (!s || s.length <= max) return s;
        return s.substring(0, max) + "...";
    }

    function renderRefLink(ref) {
        if (!ref) return "";
        var url = null;
        if (ref.indexOf("http") === 0) url = ref;
        else if (ref.indexOf("PMID:") === 0) url = "https://pubmed.ncbi.nlm.nih.gov/" + ref.replace("PMID:", "");
        else if (ref.indexOf("PMC:") === 0) url = "https://www.ncbi.nlm.nih.gov/pmc/articles/" + ref.replace("PMC:", "");
        else if (ref.indexOf("DOI:") === 0) url = "https://doi.org/" + ref.replace("DOI:", "");
        if (url) return '<a href="' + url + '" target="_blank" rel="noopener">' + esc(ref) + '</a>';
        return esc(ref);
    }

    // -- Pagination --

    function renderPagination() {
        var totalPages = Math.ceil(filtered.length / PAGE_SIZE);
        var container = document.getElementById("pagination");
        if (totalPages <= 1) { container.innerHTML = ""; return; }

        var html = "";
        if (currentPage > 1)
            html += '<button onclick="goPage(' + (currentPage - 1) + ')">&laquo; Prev</button>';

        var range = paginationRange(currentPage, totalPages);
        range.forEach(function (p) {
            if (p === "...") {
                html += '<span class="ellipsis">...</span>';
            } else {
                html += '<button class="' + (p === currentPage ? "active" : "") +
                    '" onclick="goPage(' + p + ')">' + p + '</button>';
            }
        });

        if (currentPage < totalPages)
            html += '<button onclick="goPage(' + (currentPage + 1) + ')">Next &raquo;</button>';

        container.innerHTML = html;
    }

    function paginationRange(current, total) {
        var delta = 2;
        var range = [];
        var left = Math.max(2, current - delta);
        var right = Math.min(total - 1, current + delta);

        range.push(1);
        if (left > 2) range.push("...");
        for (var i = left; i <= right; i++) range.push(i);
        if (right < total - 1) range.push("...");
        if (total > 1) range.push(total);
        return range;
    }

    // -- Search --

    function setupSearch() {
        var input = document.getElementById("search-input");
        input.addEventListener("input", function () {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(function () {
                searchQuery = input.value.toLowerCase().trim();
                applyFilters();
            }, 200);
        });
    }

    // -- Global functions --
    window.toggleSection = function (id, btn) {
        var el = document.getElementById(id);
        var isOpen = el.classList.toggle("open");
        btn.classList.toggle("open", isOpen);
    };

    window.goPage = function (n) {
        currentPage = n;
        render();
        window.scrollTo({ top: 0, behavior: "smooth" });
    };

    // -- Feedback event delegation --
    document.addEventListener("click", function (e) {
        // Toggle feedback form open
        var fbBtn = e.target.closest(".feedback-btn");
        if (fbBtn) {
            var id = fbBtn.getAttribute("data-feedback-id");
            var el = document.getElementById(id);
            if (el) el.classList.toggle("open");
            return;
        }

        // Cancel feedback
        var cancelBtn = e.target.closest(".feedback-cancel");
        if (cancelBtn) {
            var id = cancelBtn.getAttribute("data-feedback-id");
            var el = document.getElementById(id);
            if (el) el.classList.remove("open");
            return;
        }

        // Submit feedback
        var submitBtn = e.target.closest(".feedback-submit");
        if (submitBtn) {
            var id = submitBtn.getAttribute("data-feedback-id");
            var el = document.getElementById(id);
            if (!el) return;
            var ctx = JSON.parse(el.getAttribute("data-context"));
            var userComment = el.querySelector(".feedback-text").value.trim();

            var title = "[Incorrect Evidence] " + ctx.drug_label + " / " + ctx.disease_label;

            var body = "## Incorrect Evidence Report\n\nThe following evidence record appears to be **incorrect or misleading** and should be reviewed.\n\n";
            body += "| Field | Value |\n|---|---|\n";
            body += "| Disease | " + ctx.disease_label + " (`" + ctx.disease_id + "`) |\n";
            body += "| Drug | " + ctx.drug_label + (ctx.drug_id ? " (`" + ctx.drug_id + "`)" : "") + " |\n";
            body += "| Section | " + ctx.section + " |\n";
            if (ctx.source) body += "| Source | " + ctx.source + " |\n";
            if (ctx.reference) body += "| Reference | " + ctx.reference + " |\n";
            body += "\n";

            if (userComment) {
                body += "## Comment\n\n" + userComment + "\n\n";
            }

            body += "---\n*Filed from the [Rare Disease Identification site](https://monarch-initiative.github.io/rare-disease-identification/)*";

            var url = "https://github.com/" + FEEDBACK_REPO + "/issues/new?" +
                "title=" + encodeURIComponent(title) +
                "&body=" + encodeURIComponent(body) +
                "&labels=" + encodeURIComponent("evidence-feedback");

            window.open(url, "_blank");
            el.classList.remove("open");
            return;
        }
    });

    // -- Init --
    setupSearch();
    var script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.min.js";
    script.onload = loadData;
    document.head.appendChild(script);
})();
