# Errors and doubts found in upstream projects

Kept while building the Ceylon entity spine, so the source projects can be fixed. Each row says what was
seen and how sure it is. "Confirmed" means the evidence is in the files or in the Wikidata item itself.
"Check" means it looks wrong from here but needs the source context to decide.

## col_matching (Imperial Careers) — `data/kg/graph_stage3/places.jsonl`

| # | Place string | QID in file | Problem | Status |
|---|---|---|---|---|
| 1 | New York | Q769668 Province of New York | Wikidata describes this as a former colony in North America; it ended in the 1780s, before the first CO List (1862). Almost certainly the city (or state). | Confirmed anachronism |
| 2 | Singapore | Q4373718 Colony of Singapore | Item is the postwar crown colony (1946–1963) but is the only QID for "Singapore", so pre-1946 events get a polity that did not exist yet. | Confirmed anachronism for pre-1946 events |
| 3 | Aden | Q49910 Colony of Aden | Item covers 1937–1967 only; earlier Aden events need a different item. | Confirmed anachronism for pre-1937 events |
| 4 | Egypt | Q127861 Khedivate of Egypt | Item covers 1867–1914 only; used for all dates. | Confirmed anachronism outside 1867–1914 |
| 5 | Victoria | Q2132 Victoria (city, British Columbia) | Only QID for "Victoria" (13 events, `mcp_unverified`). Could be the Australian colony, Hong Kong's Victoria, or others. | Check each event |
| 6 | Sind | Q7522091 Sind Province | Item covers 1936–1955; earlier Sind was part of Bombay Presidency. | Check dates of events |
| 7 | Rhodesia | Q750583 Southern Rhodesia | Item covers 1923–1980; "Rhodesia" before 1923, or Northern Rhodesia, would be wrong. | Check |
| 8 | Kenya | Q2538511 Kenya Colony | Item covers 1920–1963; earlier events belong to the East Africa Protectorate. | Check dates of events |
| 9 | (general) | — | 2,378 of 3,207 place rows have `match_type: mcp_unverified`. The verification gate described in the grounding paper has not been run over them. | Confirmed from the file |
| 10 | (general) | — | Period-polity items are used as the single QID for a place name regardless of event year (rows 2–4, 6–8). Resolving the polity per event year through the Empire Evolution graph handles this without changing the stored QID; see the cross-check section. | Design issue, mostly handled by the resolver |
| 11 | (colony) "United Kingdom (metropole)" | Q84 London | `colony_qid` Q84 is the city of London but carries the label "United Kingdom (metropole)" on 2,623 career events. The United Kingdom and London are different items. | Confirmed from the file; which was intended needs deciding |
| 12 | (persons) | — | `persons.jsonl` has 58 person rows whose surname has no two letters together (first row: surname "6)", given names "F.R.G.S."), and 4 whose given names are a post-nominal such as "C.M.G.". These are parsing fragments, not people. | Confirmed from the file |

## Cross-check: Colonial Office List events against Empire Evolution polities

Produced by `check_col_vs_empire.py` (resolver in `empire.py`) on 16 Nov 2026. Tables:
`grounding/col_polity_check.tsv` (every QID) and `grounding/col_polity_unresolved.tsv`.

Of 115,119 links from a career event to an Empire Evolution territory:
- 106,922 fall inside the territory's own dates;
- 6,948 fall outside them but are placed by following the graph's lineage relationships to the single polity
  that existed in that year (Penang 1900 -> Straits Settlements). These are not errors in either project. My
  first pass counted them as anachronisms because it joined on QID alone; that reading was wrong and is withdrawn.
- 1,249 cannot be placed. About 500 of these have no territory in the lineage covering the years (real gaps or
  errors, listed below). About 700 reach several territories at once, so no single polity can be named:
  "Australia" before 1901 reaches six colonies. The resolver now returns nothing for those instead of picking
  one; an earlier version of it picked the latest-founded, which was wrong.

### Unresolved: needs a fix on one side

| QID | Label | Territory dates | Events | Event years | Reading (mine, unconfirmed) |
|---|---|---|---:|---|---|
| Q585408 | Northern Nigeria | 1900–1914 | 106 | 1961–1965 | Empire graph: no successor after 1960 in the lineage (independent Nigeria / Northern Region). CO List: QID is the 1900–14 protectorate, used for the later Northern Region. |
| Q2046345 | Colony and Protectorate of Nigeria | 1914–1960 | 75 | 1961–1966 | Same gap after independence. |
| Q1097943 | Uganda | 1894–1962 | 52 | 1893–1965 | Edges of the range; post-1962 successor missing from lineage. |
| Q541455 | Anglo-Egyptian Sudan | 1899–1956 | 43 | 1882–1965 | Pre-1899 events need an earlier polity; post-1956 successor missing. |
| Q193714 | Palestine | 1920–1948 | 39 | 1903–1919 | Pre-mandate events (Ottoman period / OETA) have no territory. |
| Q30059027 | Sierra Leone Colony | to 1961 | 23 | 1962–1965 | Post-independence successor missing. |
| Q1028835 | British Cameroons | 1916–1961 | 23 | 1896–1915 | Pre-1916 events: German Kamerun not in lineage, or CO List place is wrong. |
| Q2538511 | Kenya Colony | 1920–1963 | 23 | 1875–1965 | Edges of the range. |
| Q918153 | Ceylon | 1795–1948 | 12 | 1949–1988 | Dominion of Ceylon / Sri Lanka not reachable in the lineage, or CO List years wrong (1988 is after the last List). |
| others | 26 more QIDs | | 108 | | See the unresolved table. |

Event years after 1966 (the last Colonial Office List) are suspect on the CO List side whatever the polity.

### Resolved, but the resolution looks doubtful

| Case | What the resolver returned | Doubt |
|---|---|---|
| Penang and Malacca, 1946 onward (45 events) | Singapore Crown Colony (1946–1963) | Should be Malayan Union / Federation of Malaya. The lineage reaches Singapore first; either a missing Penang -> Malayan Union link or a resolver tie-break. |
| Sarawak, 1963 onward (10 events) | a territory row with an empty name (1963–) | Empire manifest: a row with no name. |
| Australian colonies after 1901 (about 1,180 events) | Commonwealth of Australia | True as the containing polity, but the colony continued as a state. Holding both needs state rows, or a status period on the colony row. |

### Standing design note

The CO List grounding uses one QID per place name for all years, and some of those QIDs are polities
(Colony of Singapore 1946–63) where the place is meant. The fix that keeps the nuance: keep the place item,
and resolve the polity per event year through `empire.py`. No dates in the manifest need stretching.

## Empire Evolution graph — `data/britishempire_kg_export.cypher` and `data/qid_manifest.tsv`

| # | Problem | Status |
|---|---|---|
| 1 | Eight territory ids appear in the Cypher export but not in `qid_manifest.tsv`: `antigua_montserrat_barbuda_1816_1833`, `bengal_province_partitioned_1905_1912`, `bengal_province_reunited_1912_1947`, `java_british_occupation_1811_1816`, `mesopotamia_british_occupied_1914_1920`, `moluccas_british_occupation_1810_1817`, `netherlands_east_indies_british_administration_1945_1946`, `stkitts_nevis_anguilla_1816_1833`. Sixteen lineage relationships touch them and are dropped when loading from the manifest. | Confirmed from the files |
| 2 | One manifest row has an empty `name` (it is what Sarawak resolves to after 1963). | Confirmed |
| 3 | 33 QIDs are shared by more than one manifest row (for example Northern Rhodesia 1924–1953 and 1963–). Intended for successive periods of one polity, but worth a check that none is a copy-paste. | Check |
| 4 | `data/wikidata_qid_issues.csv` already lists 117 QID problems found earlier (wrong QID, wrong-era QID, deleted QID). I have not checked which are fixed in the manifest. | Open |

## Ceylon graph built by Codex (`kg/` loaders, Neo4j `neo4j-ceylon`)

| # | Problem | Status |
|---|---|---|
| 1 | London, Britain, China, Java, Madras, Calcutta and 73 other places are local nodes with no QID; they absorb 79,642 mention links. | Confirmed by query, 16 Nov 2026 |
| 2 | Every "Ceylon" mention (24,096) is linked to four candidate places at once. | Confirmed |
| 3 | 14,210 Wikidata places were imported with edges only; 84 have a name. | Confirmed |
| 4 | Person profiles carry `colist_person_id` and `proposed_qid` as properties, but no relationship joins a profile to its Person node (310 profiles have a CO List id; 187 of those have a Person node). | Confirmed |
| 5 | Mention and article keys embed a per-year build digest, so a rebuilt index changes every key. The extraction files themselves use a stable article id. | Confirmed |
| 6 | `ceylon/` is not a git repository; the loaders are unversioned. The GIS Python environment is in `/tmp`. | Confirmed |

## Tropical Agriculturist person links — from the research assistant's review

Source: the research assistant's latest review export in `gold/` (not published) (22 of 100 sampled profiles answered so
far), scored with the pipeline's own `score_gold.py`; results in `gold/scorer/results/`. Her file is unedited.

| Profile | Finding | Side at fault | Status |
|---|---|---|---|
| J. H. Hart (TAP-P-000079) | Pipeline had no QID; RA found Q21515534 John Hinchley Hart, British botanist (alias "J.H.Hart"). Item exists and fits. | Pipeline miss: the vector search did not return him | Applied in spine as `ra_found_qid` |
| W. Small (TAP-P-000152) | Pipeline left it unsure; RA confirmed Q47126427 William Small, botanist, with a primary source (Index Fungorum, Uganda Blue Book 1915). | Pipeline too cautious | Applied in spine |
| Thomas Farr (TAP-P-000155) | RA proposes Q75321051 (a peerage stub) via the Horton Plains link, and says herself the sources may be circular. | Undecided | Kept as a proposal, marked unsure |
| J. E. Taylor (TAP-P-000054) | Profile is mixed: the "Mr. Taylor of Loolcundra" mentions are James Taylor the tea pioneer (Q6144040); only one mention is Dr. J. E. Taylor (Q6231692, RA's QID, not yet looked up by me). | Pipeline: bare-surname mentions attached to the wrong Taylor | Flagged `mixed_profile`; needs splitting |
| John Anderson | Profile is mixed: the Governor (Q6218961), a planter James Anderson of Bandarapola, and possibly an Oriental Bank officer. | Pipeline | Flagged `mixed_profile` |
| W. Fawcett | One of four sampled mentions is Henry Fawcett MP, not the botanist. QID for the botanist confirmed. | Pipeline (one stray mention) | Flagged `mixed_profile` |
| C. H. Collins | No Wikidata item exists for Sir Charles Henry Collins, CMG (1887–1962), Ceylon Civil Service. RA expects him in the CO Lists; the pipeline has no CO List link for the profile. | Wikidata gap; CO List link missed by the pipeline | Linked in the spine to CO List `kgp_col1931-p985b15` (COLLINS, CHARLES HENRY, born 1887, editions 1913–1940) via `grounding/people_corrections.jsonl`; still needs a minted id in place of a QID |
| G. W. Sturgess | No Wikidata item; has a CO List link. RA also found an OCR error in the passage: "Yet" printed for "Vet". | Wikidata gap; OCR | Mint a local id |
| D. S. Cameron | No Wikidata item; found in the planters registry. A bare "Cameron" in a list of soil scientists is probably someone else. | Wikidata gap; one doubtful mention | Mint a local id |

Applied in `col_matching` on 16 Nov 2026 (uncommitted): three rows appended to
`data/kg/graph_stage3/person_grounding.final.jsonl` with `source: REVIEW`, `tier: R`, reviewer and evidence —
Hart `kgp_col1908-p662b7` -> Q21515534, Small `kgp_col1933-p1000b12` -> Q47126427, Fawcett
`kgp_col1909-p709b20` -> Q3568610. The same rows are in `person_grounding_reviewed.jsonl` beside it (that path
is git-ignored). `persons.jsonl` will show the QIDs only after the spine is re-emitted. Small's Wikidata item
has no birth or death date, so that link rests on name, occupation and career (Uganda botanist 1913, Ceylon
mycologist 1926), not on a date match. Hart's item carries two birth years (1847 and 1867).

### Found while applying them

- `kg_merge_person_grounding.py` no longer reproduces the committed `person_grounding.final.jsonl`. Run on the
  committed inputs it removes 38 rows and adds 107 (1,066 -> 1,135), because later curation (removed namesake
  groundings, merged persons) was applied to the final file and not to the script's inputs. Re-running it would
  undo that curation. I ran it once, saw this, and restored the file from git.
- That run also overwrote `data/kg/person_grounding_merge_dropped.jsonl`, a git-ignored diagnostic file, with
  its own output (3 rows). I could not restore the previous version; it is a derived log, not source data.

## Tropical Agriculturist extraction (`ner/`)

| # | Problem | Status |
|---|---|---|
| 1 | The extractor's `norm` field supplies names from world knowledge (already documented for persons in `ner/persons/README.md`). Seen for places too: "Observer" → "Ceylon Observer". Use `text` as evidence and `norm` only as a hint. | Confirmed |
| 2 | Adjectives are extracted as places: "Indian", "American", "Brazilian", "English" are folded into India, America, Brazil, England. | Confirmed in `names/PLACE.tsv` |

## Wikidata

Found while grounding; none edited (editing Wikidata is your call).

| Item | Problem | Seen |
|---|---|---|
| Q161426 (taxon name *Oryza sativa*) | English label reads "Oryza molida" in the API on 16 Nov 2026; the scientific name (P225) is correct. The spine matches on the taxon name, so the link is right, but the label shown is wrong. Check again in the 20261109 dump. | `gazetteer/name_candidates_wikidata.jsonl` |
| Q1548030 bell pepper, Q130878 chewing gum, Q2813 Coca-Cola, Q311359 lac operon | Carry the bare aliases "pepper", "gum", "coke", "lac". Not errors in Wikidata, but they capture historical commodity names; refused in `grounding/name_rejections.jsonl`. | spot checks |

## Empire Evolution manifest: end dates and names (found 16 Nov, afternoon)

`data/qid_manifest.tsv` and the graph export disagree about how complete the dates are, and anything that reads
only the manifest gets open-ended territories.

| Problem | Count | Example | Effect |
|---|---:|---|---|
| `end_date` empty in the manifest while the graph node has `independence_year` | 330 of 739 rows | `new_zealand_colony_1840_1907`: manifest end empty, graph `independence_year: 1907` | A year-aware lookup that trusts the manifest treats the 1840 colony as still current in 1925. Two territories with one QID are then told apart only by file order. |
| `end_date` empty and no `independence_year` either | 175 rows | `alberta_1905`, many princely states | Truly open-ended or unknown; needs a decision per row. |
| manifest `end_date` and graph `independence_year` differ | 7 rows | `bengal_presidency_crown_1858_1912` (1905 / 1912); `colony_of_newfoundland_1610_1949` (1949 / 1907); `dominion_of_newfoundland_1907_1934` (1949 / 1934) | One of the two is wrong, or they mean different things. Holding both, as you asked, would need two named fields (end of this form of government / end of British rule). |
| `name` empty (only `canonical_name` filled) | 49 rows | `united_states_1776`, `irish_free_state_1922_1937`, `dominion_of_new_zealand_1907_1947` | Blank labels in anything that shows `name`. |

Local handling (`empire.py`): end = manifest `end_date`, else the graph's `independence_year` when it is later
than the start, with the source recorded in `end_source`; name = `name`, else `canonical_name`. The cross-check
figures above were recomputed with this. Proposed upstream fix: fill the manifest's `end_date` and `name` from
the graph export for these rows (I have not edited the checkout).
