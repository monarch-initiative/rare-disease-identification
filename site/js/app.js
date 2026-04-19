(function () {
    "use strict";

    var DATA_URL = "data/prioritised-rare-disease-list.yml";
    var EPM_URL = "obo.epm.json";
    var PAGE_SIZE = 25;
    var FEEDBACK_REPO = "monarch-initiative/rare-disease-identification";

    var allDiseases = [];
    var filtered = [];
    var currentPage = 1;
    var activeFilters = {
        prioritization: new Set(),
        prevalence: new Set(),
        treatments: new Set(),
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
        buildFilterGroup("filter-prevalence", "prevalence",
            function (d) { return d.prevalence_category || "unknown"; }, PREVALENCE_LABELS);
        buildFilterGroup("filter-treatments", "treatments", function (d) {
            if (d.indications && d.indications.length > 0) return "has_indications";
            if (d.research && d.research.length > 0) return "has_research";
            return "no_treatments";
        }, TREATMENT_LABELS);
        buildTopNFilter("filter-category", "category",
            function (d) { return (d.mondo_categories || []).map(function (t) { return t.label || t; }); }, 15);
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

            if (activeFilters.prevalence.size > 0 &&
                !activeFilters.prevalence.has(d.prevalence_category || "unknown"))
                return false;

            if (activeFilters.treatments.size > 0) {
                var tag = "no_treatments";
                if (d.indications && d.indications.length > 0) tag = "has_indications";
                else if (d.research && d.research.length > 0) tag = "has_research";
                if (!activeFilters.treatments.has(tag)) return false;
            }

            if (activeFilters.category.size > 0) {
                var cats = (d.mondo_categories || []).map(function (t) { return t.label || t; });
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
            ...(d.mondo_categories || []).map(function (t) { return (t.label || "") + " " + (t.id || ""); }),
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
        if (prevCat) {
            var prevTip = PREVALENCE_TOOLTIPS[prevCat] || "";
            html += renderTooltipTag(prevLabel, prevTip, "tag " + prevClass);
        }
        if (hasIndications) html += '<span class="tag has-indications">Approved Indications</span>';
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

        // Categories — each type in its own labelled section
        var mondoCats = d.mondo_categories || [];
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
        if (d.prevalence_per_100k_us != null) {
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
        var hpoProfiles = d.curated_hpo_profiles || [];
        if (hpoProfiles.length > 0) {
            html += '<div class="card-subsection">';
            html += '<span class="subsection-label tooltip-wrap">Phenotype Profile' +
                '<span class="tooltip-text">Key clinical signs and symptoms (phenotypes) associated with this disease, drawn from the Human Phenotype Ontology (HPO)</span></span>';
            html += '<div class="category-list">';
            hpoProfiles.forEach(function (t) { html += renderTermPill(t, "hpo"); });
            html += '</div></div>';
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

        // Research section
        if (hasResearch) {
            html += renderCollapsibleSection("research", d.research,
                "Treatment Research (" + d.research.length + " entries)",
                renderResearchEntry, diseaseCtx);
        }

        html += '</div>'; // disease-card
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

    function renderEvidenceCard(e, context) {
        var html = '<div class="evidence-card">';

        // Top row: source, jurisdiction, approval, confidence, feedback button
        html += '<div class="evidence-top-row">';
        html += '<div class="evidence-top-left">';

        // Source badge
        var sourceType = (e.source && e.source.type) || e.source_type || "";
        var sourceName = (e.source && e.source.name) || sourceType || "";
        if (sourceName) {
            var badgeClass = sourceType ? sourceType.toLowerCase() : "unknown";
            html += '<span class="evidence-badge ' + badgeClass + '">' + esc(sourceName) + '</span>';
        }

        // Jurisdiction
        var jurisdiction = (e.source && e.source.jurisdiction) || e.jurisdiction || "";
        if (jurisdiction) {
            html += '<span class="evidence-jurisdiction">' + esc(jurisdiction) + '</span>';
        }

        // Approval status
        if (e.approval_status) {
            var statusClass = e.approval_status.toLowerCase().replace(/[^a-z]/g, "_");
            html += '<span class="approval-badge ' + statusClass + '">' + esc(e.approval_status) + '</span>';
        }

        // Max research phase
        if (e.max_research_phase) {
            html += '<span class="phase-badge">' + esc(e.max_research_phase.replace(/_/g, " ")) + '</span>';
        }

        // Evidence source (HUMAN_CLINICAL, etc.)
        if (e.evidence_source) {
            html += '<span class="evidence-source-badge">' + esc(e.evidence_source.replace(/_/g, " ")) + '</span>';
        }

        // Confidence indicators
        var confDrug = e.confidence_drug || e.confidence || "";
        var confDisease = e.confidence_disease || e.confidence || "";
        var confAssoc = e.confidence_association || e.confidence || "";
        if (confDrug || confDisease || confAssoc) {
            html += '<span class="confidence-group">';
            if (confDrug) html += '<span class="conf-dot ' + confDrug.toLowerCase() + '" title="Drug confidence: ' + esc(confDrug) + '">D</span>';
            if (confDisease) html += '<span class="conf-dot ' + confDisease.toLowerCase() + '" title="Disease confidence: ' + esc(confDisease) + '">Dx</span>';
            if (confAssoc) html += '<span class="conf-dot ' + confAssoc.toLowerCase() + '" title="Association confidence: ' + esc(confAssoc) + '">A</span>';
            html += '</span>';
        }

        // Support indicator
        if (e.support) {
            var supportClass = e.support.toLowerCase().replace(/[^a-z]/g, "_");
            html += '<span class="support-badge ' + supportClass + '">' + esc(e.support) + '</span>';
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

        // Reference line
        if (e.reference || e.reference_title) {
            html += '<div class="evidence-ref-line">';
            if (e.reference) {
                html += '<span class="evidence-ref">' + renderRefLink(e.reference) + '</span>';
            }
            if (e.reference_title) {
                html += '<span class="evidence-ref-title">' + esc(e.reference_title) + '</span>';
            }
            html += '</div>';
        }

        // Source description
        if (e.source && e.source.description) {
            html += '<div class="evidence-source-desc">' + esc(e.source.description) + '</div>';
        }

        // Source URL
        if (e.source && e.source.url) {
            html += '<div class="evidence-source-url"><a href="' + esc(e.source.url) + '" target="_blank" rel="noopener">' + esc(truncate(e.source.url, 80)) + '</a></div>';
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

        // Curator
        if (e.curator) {
            var curatorName = (typeof e.curator === "string") ? e.curator : (e.curator.name || "");
            var curatorType = (typeof e.curator === "object") ? (e.curator.curator_type || "") : "";
            if (curatorName) {
                html += '<div class="evidence-curator">';
                if (curatorType) html += '<span class="curator-type">' + esc(curatorType.replace(/_/g, " ")) + '</span>';
                html += esc(curatorName);
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

    function renderIndicationEntry(ind, _idx, _arr, diseaseCtx) {
        var html = '<div class="drug-entry">';
        html += '<div class="drug-header">';
        html += '<span class="drug-name">' + esc(ind.drug_label) + '</span>';
        if (ind.drug_id) {
            html += ' ' + renderCurieLink(ind.drug_id);
        }
        html += '</div>';
        (ind.evidence || []).forEach(function (e) {
            var context = {
                disease_id: diseaseCtx.disease_id,
                disease_label: diseaseCtx.disease_label,
                drug_label: ind.drug_label,
                drug_id: ind.drug_id || "",
                section: "indication",
                source: (e.source && e.source.name) || e.source_type || "",
                reference: e.reference || "",
            };
            html += renderEvidenceCard(e, context);
        });
        html += '</div>';
        return html;
    }

    function renderResearchEntry(r, _idx, _arr, diseaseCtx) {
        var html = '<div class="drug-entry">';
        html += '<div class="drug-header">';
        html += '<span class="drug-name">' + esc(r.drug_label) + '</span>';
        if (r.drug_id) {
            html += ' ' + renderCurieLink(r.drug_id);
        }
        html += '</div>';
        (r.evidence || []).forEach(function (e) {
            var context = {
                disease_id: diseaseCtx.disease_id,
                disease_label: diseaseCtx.disease_label,
                drug_label: r.drug_label,
                drug_id: r.drug_id || "",
                section: "research",
                source: (e.source && e.source.name) || e.source_type || "",
                reference: e.reference || "",
            };
            html += renderEvidenceCard(e, context);
        });
        html += '</div>';
        return html;
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
            ["Disease Type", (d.mondo_categories || []).map(function (t) { return t.label || ""; }).find(function (s) { return s.toLowerCase().indexOf(q) !== -1; })],
            ["Disease Type ID", (d.mondo_categories || []).map(function (t) { return t.id || ""; }).find(function (s) { return s.toLowerCase().indexOf(q) !== -1; })],
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
