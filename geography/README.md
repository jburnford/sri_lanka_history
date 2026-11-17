# Ceylon geography edges

Historical census and transport GIS, including QGIS, GeoPackage, sources and reproduction notes, is in [historical-gis](historical-gis/README.md).

`wikidata-edges.csv` contains one directed Wikidata edge per row, in the form
`subject_qid,pid,object_qid`. The extract uses the [QLever Wikidata index](https://qlever.dev/wikidata/).

The November 6, 2026 extract contains 20,102 distinct edges across 17 PIDs,
with 13,997 subject QIDs and 14,209 distinct QIDs across both endpoints.

## Scope

The seed items are modern Sri Lanka (Q854), the physical island (Q4526612),
British Ceylon (Q918153), the Dominion of Ceylon (Q2670092), Dutch Ceylon
(Q1841483) and Portuguese Ceylon (Q1709007). The query also selects items linked
to any seed by country (P17), an administrative containment chain (P131), or
physical feature (P706), when they have coordinates or a place-related type.
The resulting footprint follows Wikidata's links and includes some coastal
features and nearby islands. Places with missing links to a seed can be absent.

The output preserves direct Wikidata triples. The P131 path helps find
subjects, but the extract adds no inferred edges. P361, P527, P1365 and P1366
require both endpoints to be in the selected scope. The other properties can
point to items outside it, such as adjacent bodies of water. The direct triples
use Wikidata's truthy projection, which selects preferred rank where present
and otherwise normal rank. It omits statement qualifiers and references, so
an administrative edge here cannot establish jurisdiction for a historical date.

| PID | Wikidata property |
| --- | --- |
| [P17](https://www.wikidata.org/wiki/Property:P17) | country |
| [P47](https://www.wikidata.org/wiki/Property:P47) | shares border with |
| [P131](https://www.wikidata.org/wiki/Property:P131) | located in the administrative territorial entity |
| [P150](https://www.wikidata.org/wiki/Property:P150) | contains the administrative territorial entity |
| [P177](https://www.wikidata.org/wiki/Property:P177) | crosses |
| [P206](https://www.wikidata.org/wiki/Property:P206) | located in or next to body of water |
| [P276](https://www.wikidata.org/wiki/Property:P276) | location |
| [P361](https://www.wikidata.org/wiki/Property:P361) | part of |
| [P403](https://www.wikidata.org/wiki/Property:P403) | mouth of the watercourse |
| [P527](https://www.wikidata.org/wiki/Property:P527) | has part(s) |
| [P706](https://www.wikidata.org/wiki/Property:P706) | located in/on physical feature |
| [P885](https://www.wikidata.org/wiki/Property:P885) | origin of the watercourse |
| [P974](https://www.wikidata.org/wiki/Property:P974) | tributary |
| [P1365](https://www.wikidata.org/wiki/Property:P1365) | replaces |
| [P1366](https://www.wikidata.org/wiki/Property:P1366) | replaced by |
| [P3018](https://www.wikidata.org/wiki/Property:P3018) | located in protected area |
| [P4552](https://www.wikidata.org/wiki/Property:P4552) | mountain range |

Run `python3 geography/extract.py` from the project directory to refresh the
CSV. The script reads `wikidata-places.rq` and then fetches outgoing edges in
batches. It uses only Python's standard library and the public QLever API.

## Dates

The November 6, 2026 extract has 902 date rows across 803 subject QIDs.
There are 879 item-level date rows and 23 date qualifiers on 15 distinct
geographic triples. Five of those triples are in the direct edge CSV.

`wikidata-dates.csv` covers the subject QIDs in `wikidata-edges.csv`. Rows
with an empty `qualifier_pid` are time-valued statements on the item itself.
Other rows are time qualifiers on geographic statements. For these rows,
`in_edge_csv` says whether the same subject, PID and object occur in the
direct edge export. The date extract can surface qualified statements omitted
from that export, such as lower-ranked statements. For the four local-only
PIDs, the date extract keeps the original edge membership requirement.
Qualifiers on other kinds of statements, such as census dates on population
claims, are outside this extract.

Each row retains the Wikidata statement ID, rank, calendar model, and time
precision. For example, precision 9 means year, 10 means month, and 11 means
day. A January 1 timestamp with year precision records only the year.
Each qualifier is a separate row. Group qualifiers by statement ID when
interpreting start and end dates.
[Wikibase RDF time values](https://www.mediawiki.org/wiki/Wikibase/Indexing/RDF_Dump_Format#Time)

Run `python3 geography/extract_dates.py` after generating the edge CSV.

## Historical source

The workspace copy of Simon Casie Chitty's *The Ceylon Gazetteer* is a reprint of
the 1834 edition. It provides period spellings and descriptions for later
matching. The CSV contains only Wikidata edges.
