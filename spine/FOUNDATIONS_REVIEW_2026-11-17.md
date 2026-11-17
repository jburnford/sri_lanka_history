# Ceylon knowledge graph foundations review

17 November 2026

Keep the file-backed spine, its links to the Colonial Office List and Empire Evolution, and the rebuildable Neo4j projection. The most consequential errors arise when a source row becomes a person, a trade heading becomes a place, or a second printing becomes another quantity. They survive successful rebuilds and plausible-looking historical queries. I would keep collecting and indexing sources while making the following changes before expanding the accepted graph.

## Findings that affect historical answers today

### 1. Trade headings inherit identities from a different source

On printed page U 8 of the 1907 Blue Book, the chillies return distinguishes British India from “India, exc. British”. The latter appears under Foreign Countries and reports 39 cwt and Rs. 509. I checked the scan. In the live graph, **8,938 ledger observations with that exact excluded-area label resolve to the British Raj**. The generic label matcher tries the text before a comma and accepts a name already resolved for the journal. Even an exact spelling can fail. Of 6,188 trade observations keyed to Victoria, 1,421 explicitly say they are listed under Australia. The key resolves to the Canadian city.

Give a printed trade category its own ID, scoped to the source and period. Preserve hierarchy, exceptions, and the article or country column. A link to a modern place can express exact identity, a component, or a broader area. Only an exact decision should put a quantity into that place's total. The same discipline applies to commodities such as “Oil, citronella”, where falling back to “Oil” changes the scope. [Label matching](bluebook/link_cells.py#L20) · [Observation linking](bluebook/link_observations.py#L46)

### 2. Officer matching combines people whom the source distinguishes

The 1892 index, printed page 39, names John Perera as lighthouse keeper, Joseph Perera as station master, and Jerome Perera as draughtsman. The scan and the extracted index retain the three forenames. The graph combines them in one officer, `bbp:1892:perera:J`, because surname, initials, and volume year form the grouping key. The 167,416 officer nodes therefore count distinct matching keys. They cannot serve as a count of people or person-years.

Give each index or establishment entry an ID using the volume, table, row, and column or block. Attach office, appointment date, and printed name to that entry. A separate person decision can then group entries, cite its evidence, and be split later. A unique Colonial Office List candidate for a merged group does not establish an identity for its individual entries. [Officer extraction](bluebook/extract_officers.py#L86) · [Grouping and matching](bluebook/match_officers.py#L40)

### 3. The acreage example doubles the return

Running the logic of query 12 for coffee in 1868 gives **414,132 acres and eight province rows**. The 1868 and 1869 volumes each give **207,066 acres across the same four reporting provinces**. The extraction preserves evidence of agreement between the two printings. The demo then sums both as independent production.

Keep each printing addressable. Give the underlying return a key covering period, area, crop, measure, and unit. Publish a query that counts that return once and exposes conflicting printings where they exist. Deduplicating on the numeric value alone would also discard genuinely distinct provinces reporting equal acreages. [Acreage query](queries.cypher#L81) · [Second-printing reconciliation](bluebook/extracted/agriculture_second_printing.tsv)

### 4. Money and reporting periods lose their meaning in the projection

I counted **52,611 nonblank monetary ledger figures** whose exported unit is `cwt.`. The measure name carries the currency, while `unit_as_printed` carries the article's quantity unit. The scanned U 8 header puts rupees above the value column and weight beside the article. The graph needs both fields with unambiguous meanings. Otherwise a unit filter includes money in a weight series.

There is a parallel problem with dates. The Statistical View projection takes the first four characters of the period. **43 series and starting-year combinations** have multiple distinct source period labels that collapse to the same integer. Births in `1910` and `1910-11` are one example. The source-period string survives in the observation ID. Trade ledgers also include half-years, and the destination example groups by volume year. Store period label, start, end, precision or assumption, and publication year separately. Make the period and the unit of the measured value available to aggregation queries. [Ledger records](bluebook/jobs/trade_work/read_trade.py#L468) · [Period projection](bluebook/link_observations.py#L58) · [Statistical View projection](bluebook/link_observations.py#L92) · [Trade query](queries.cypher#L74)

### 5. Polity attribution can extend past the polity's lifetime

The resolver tests whether two intervals overlap, then the loader assigns one polity to the posting. I found **30 loaded postings** extending beyond the assigned polity's recorded dates. One posting runs from 1948 to 1958 and points to the Ceylon territory ending in 1948. Separately, **140 posting rows** have multiple direct territories for the recorded colony QID that meet the resolver's overlap test. The direct-match loop takes the first. The ambiguity check used later in the lineage search never sees those ties.

Distinguish full containment, partial overlap, and alternative candidates. A posting spanning a change can keep its original dates and receive dated polity links for the supported portions. Preserve the date source and the resolution path. Use the direction and meaning of each succession or containment relation when deciding where to traverse. [Interval and tie handling](empire.py#L39) · [Posting projection](build_graph_tables.py#L189)

### 6. The taxon importer turns classification into synonymy

The live graph has **ten provisionally accepted species** linked to their genera by `SYNONYM_OF`. For example, it makes *Sitophilus oryzae* a synonym of *Sitophilus*. The importer treats every status other than the literal `accepted` as a synonym and uses the first classification item as the accepted name. A genus is a legitimate classification parent. Following it as an equivalent name changes the biological entity.

Read synonym targets only for supported synonym statuses with evidence for the accepted usage. Preserve provisional acceptance and classification as distinct facts. Apply the correction to both Catalogue of Life import paths, then rebuild the caches or their affected records. The pinned Catalogue of Life release makes these cases reproducible. [Scientific-name importer](ground_taxa_col.py#L35) · [Wikidata taxon join](join_wd_taxa_col.py#L26) · [Graph relationship](load_graph.py#L66)

### 7. The organisation matcher can contradict its own dates

The journal has 20 “Indian Bank” records dated 1898–1899. One May 1898 *Colombo Price Current* passage gives “Indian Bank Minimum Rates”. The accepted high-confidence QID has a 1907 inception in the matcher's own candidate data. The code rejects inception dates after 1945 but never compares them with the article dates. The proposed local organisation register inherits the same QID and again marks it high confidence.

Treat this as unresolved pending evidence for a specific earlier body or predecessor. Check the mention date against the proposed organisation's dates and retain a predecessor as a separate organisation when warranted. The local register is worth pursuing. I checked that its 1,743 assigned name keys each belong to one proposed body. That structural check says nothing about whether the proposed identity is historically correct. Assign durable local IDs to accepted bodies, including those without Wikidata items. [Matcher](ground_names_wd.py#L105) · [Indian Bank decision](grounding/org_wd.jsonl#L485) · [Proposed local register](grounding/org_job/org_bodies.jsonl)

## Evidence and identifiers to preserve before expansion

- **Journal mentions.** An input mention carries the article, printed text, model normalization, role, and chunk. The projection prefers the model normalization as its name key and retains up to three surfaces and roles per article and key. Person links likewise aggregate by article and profile. The mixed W. Fawcett profile has 62 linked articles and identity edges to Wikidata and the Colonial Office List. A career query can attribute every article to one person. Keep citable mention records, ideally linked to page or passage where the source supports it. Resolve at mention level when evidence distinguishes senses. Retain article summaries for fast queries. [Mention projection](build_graph_tables.py#L128) · [Career query](queries.cypher#L19)
- **Scripts and aliases.** The shared key function converts to ASCII and strips everything else. In the project's own Sri Lanka Wikidata cache, 1,843 distinct strings containing Sinhala and 2,613 containing Tamil produce an empty key. The mention builder skips empty keys. Preserve the source string, language or script when known, and a Unicode-normalized lookup key. Keep romanized forms as searchable aliases. Apply the change in both copies of the normalizer with a migration for existing IDs. [Shared key](common.py#L6) · [Name inventory](build_names.py#L13)
- **Citable figures.** Agriculture, ledger, and trade-summary observation IDs include a counter running across the entire extract. Inserting an earlier row renumbers later observations even in another volume. The cell or block locator often survives only in a note. Build attestation IDs from the source edition, table, row, column or block, and measure or component. Record an extraction revision and retain a crosswalk if a later reading changes table segmentation. [Observation IDs](bluebook/link_observations.py#L35) · [Earlier pilot's source-record design](../kg/README.md#L9)
- **Decision provenance.** The files often preserve candidate lists, reasons, proposer, and sample-review history. A projected resolution keeps four properties. An unresolved name can retain only its status in Neo4j. Give decisions IDs and link to their versioned evidence. Distinguish an automated rule, a model proposal, an individually reviewed decision, and a member of a sampled batch. This lets a second colony reuse a decision with the same evidential limits. [Decision files](grounding/name_decisions.jsonl) · [Resolution load](load_graph.py#L71)
- **Gazetteer handoff.** All 189 mapped records refer to existing IDs among the 439 parsed gazetteer entries. The grounded file separates the historical source page, geometry source, geometry date, and location scope. Preserve these in the graph integration. For example, Adam's Berg is described as a hill and its modern coordinate anchors a temple complex. Treating the feature's QID as an unconditional identity for the historical headword would discard that distinction. [Grounded entry](analysis/hgis_chitty_1834_grounded.tsv#L2)
- **OCR confidence.** None of the 434,973 loaded observations came from a table marked suspect in this snapshot. However, **75 label relationships from 20 suspect tables** are available to unfiltered graph queries. Keep such rows available for inspection and expose their status in default research queries. Arithmetic agreement, corroboration of digits on a page, correctness of a cell's row and column, and correctness of an entity link answer different questions. A scan-checked figure can still be attached to the wrong country. [Confidence calculation](bluebook/confidence.py#L198) · [Label loading](load_graph.py#L94)

## Rebuild and release checks

I rebuilt the 17 core load tables in a temporary directory. All 17 matched the existing tables byte for byte after decompression. Rebuilding the Blue Book table index, cell links, table-name links, observations, and officer matches also reproduced their contents. The repository now includes the core load tables. The three extract validators passed for 12,906 agricultural rows, 45,118 Statistical View rows, and 439,225 trade ledger measure rows. The live database was queried read-only. These checks establish repeatability with the current inputs and agreement with the validators. The printed-page comparison was targeted, so it does not estimate corpus-wide accuracy. [Core builder](build_graph_tables.py) · [Agriculture validator](bluebook/jobs/agriculture_work/validate_agriculture.py) · [Statistical View validator](bluebook/jobs/statistical_view_work/validate.py) · [Trade validator](bluebook/jobs/trade_work/verify_trade.py)

The loader counts input rows sent, while a Cypher `MATCH` can omit a relationship. The load table contains 1,176 lineage edges and Neo4j contains 1,160. The 16 missing edges have endpoints absent from the territory manifest. The loader also deletes the serving graph before it opens all inputs, commits each batch separately, and conditionally skips missing Blue Book inputs. A missing file or interrupted run can therefore leave a partial graph in service. Build a named release from an input manifest, check expected and rejected rows per relationship, validate in a staging database, and promote the successful build. Record source repository revisions, authority releases, extraction versions, and checksums for the literal inputs. [Loader](load_graph.py#L19) · [Rebuild sequence](load_graph.py#L45) · [Upstream edge inventory](UPSTREAM_ERRORS.md)

## Order of work

1. **Correct the affected research answers first.** Correct the qualified trade mappings, officer grouping, acreage query, monetary units, polity intervals, and false taxon synonyms. Move the anachronistic bank decision back to review. Retain the old decisions with the reason for supersession.
2. **Prove one source-to-answer path in each major family.** Use the 1892 Perera entries, 1907 chillies, 1868 coffee, one mixed journal profile, and one posting across independence as regression fixtures. Each should lead from a research result back to its attestations and survive a rebuild after insertion of an unrelated record. Exercise a Sinhala and a Tamil name in the same build.
3. **Measure errors at the level the research uses.** For the next trade batch, sample complete records against scans across layouts and periods. Score article, country or category, quantity or currency, period, and figure together. For identities, stratify by source, rule, confidence, and ambiguity, including a sample of unresolved mentions. Keep a fresh sample for the final reader or matcher after fixes. Apply the same checks to a small second-colony slice before promoting the design to a shared foundation.

## Read-only checks for the current graph

These examples reproduce four of the findings on the 17 November snapshot. They also identify the rows to revisit after a correction.

```cypher
MATCH (o:Observation {area_as_printed:'India, exc. British'})
      -[:ABOUT_PLACE]->(:Name)-[:RESOLVES_TO]->(p:Place)
WHERE o.kind STARTS WITH 'trade:'
RETURN p.qid, p.label, count(DISTINCT o) AS observations
```

```cypher
MATCH (o:Observation {kind:'agriculture:acreage_by_crop', year_data:1868})
      -[:MEASURES]->(:Name {key:'coffee'})
WHERE o.value IS NOT NULL AND NOT toLower(o.area_as_printed) CONTAINS 'total'
RETURN o.year_volume AS printing, count(*) AS provinceRows, sum(o.value) AS acres
ORDER BY printing
```

```cypher
MATCH (p:Posting)-[:IN_POLITY]->(t:Territory)
WHERE p.start < t.start OR p.end > t.end
RETURN count(p) AS postingsOutsideAssignedDates
```

```cypher
MATCH (t:Taxon {status:'provisionally accepted'})-[:SYNONYM_OF]->(g:Taxon)
WHERE t.rank = 'species' AND g.rank = 'genus'
RETURN t.name AS species, g.name AS genus ORDER BY species
```
