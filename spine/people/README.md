# People in the atlas

`build_atlas_people.py` writes `docs/data/people/`, which the atlas's People view and People layer read
(`docs/people.js`, `docs/people.css`; small hooks in `docs/atlas.js` and `docs/index.html`). Standard library only:

```sh
python spine/people/build_atlas_people.py
```

## What goes in

| Kind | Source | Unit | Records |
|---|---|---|---:|
| Officials | `bluebook/extracted/officer_matches.tsv` (Blue Books 1863–1917) | one name in one volume | 167,801 |
| Directory people | `directories/ferguson_1922/roles.jsonl` (Ferguson 1922: Kandy, Colombo, associations and banks) | one role in one listing | 1,458 |

Colonial Office List matches (`col_person`, and the establishment-list matches in `col_roster/`) are carried
through and shown as proposed identifications with their confidence.

## How a record gets onto the map

A record is placed where its office title, department or directory town **names a place the gazetteer knows**.
The gazetteer is, in order of preference: census towns, towns on Ferguson's 1893 map, places in the 1936 Motor Map
lists, settlements in the 1834 Gazetteer layer (all from `docs/data/*.json`), then settlements in
`gazetteer/sri_lanka_wikidata.jsonl` (chosen by their description). `place_spellings.tsv` maps printed spellings
to a gazetteer name. Each place in a record carries how it was recognised.

53,104 of the 167,801 official records name such a place (343 places). The rest are departmental posts with no
place printed ("Clerk, Railway Department") or name a place the gazetteer does not have.

Read the placement as "the place printed in the office", not as a residence. Known ways it goes wrong:
- an office that names two places (a road, a railway section, a court circuit) is counted at both;
- a Wikidata village that shares its name with something else in an office title; `place_matches_review.tsv`
  lists every place with the number of records it drew, for reading down;
- a name shared by several Wikidata places takes the best-known one and says "one of N places of this name";
- provinces and districts are not places here yet ("Western Province" is unplaced).

`unplaced_office_endings.tsv` lists the commonest endings of unplaced offices: the next spellings to add.

## Printed names are not people

Records are grouped under a printed-name key: surname plus the first letter of each given name, with titles and
post-nominals left out. 39,205 keys. A key gathers "J. Perera" from 90 volume records that are certainly several
men. The viewer says this on every name page. Only the Colonial Office List matches are identifications, and
those were made by program (surname, initials, dates) and have not been checked by a person.

## Known weak points
- Office text is as the extractor left it: ditto marks ("do"), row letters, and two offices run together.
- Some official names were split wrongly into surname and initials upstream; they sit under odd keys.
- The Colombo section of the directory is being re-read; about one record in seven was wrong at the last check.
- Directory people are placed at their town only. Street addresses are carried as text and not yet mapped.
- Nothing here has been compared with the page by a person.
