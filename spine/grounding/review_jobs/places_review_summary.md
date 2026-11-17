# Place review proposals — partial review

Reviewed **600 of 1077 names** in input order: records **1–600**, from **malabar** through **jacksonville**. **477 remain unreviewed**. Continue at record **601: bambarabotuwa**.

The JSONL contains only this reviewed prefix, one proposal per reviewed name. There are no placeholder decisions for the remaining names. Decisions were individually authored by reading each record; the Python helper only serializes those decisions and validates their references. No network was used.

## Outcomes and confidence

| Outcome | High | Medium | Low | Total |
| --- | ---: | ---: | ---: | ---: |
| match | 121 | 39 | 0 | 160 |
| none | 133 | 16 | 0 | 149 |
| ambiguous | 24 | 201 | 63 | 288 |
| not_a_place | 2 | 1 | 0 | 3 |
| **Total** | **280** | **257** | **63** | **600** |

Confidence describes confidence in the proposed outcome, including a clear finding of ambiguity; it is not a probability that an ambiguous candidate is correct. A single alternative on an ambiguous row identifies a plausible related candidate whose historical extent or geographic kind is not established. An empty alternatives list for `poonac` records uncertainty between a commodity heading and a locality without a supported candidate.

## Ten decisions least certain

These ten are selected by manual judgment among the low-confidence decisions; they are not a unique statistical ranking. All remain ambiguous.

| Input record | Key | Remaining listed QIDs | Why unresolved |
| ---: | --- | --- | --- |
| 232 | poonac | None supported | Repeated "origin of coconut cake (27)" and "location for coconut cake (7)" leave unclear whether Poonac is a commodity heading misread as an origin or an actual locality. None of the listed candidates establishes either interpretation, so a place or nonplace classification cannot be made confidently. |
| 275 | kachcheri | Q6344630 | "Meeting venue (11)" and "meeting place (4)" require a physical Kachcheri venue. The exact-name candidate has no description, classes, or coordinates, so its identity as a particular venue cannot be established. |
| 558 | topare | Q6148961 | The roles are empty and the sole candidate is an unnamed Spanish settlement. Without a label or contextual role, the input cannot establish whether it represents Topare. |
| 427 | kirama | Q135473094 | "Meteorological station (2)" and "school location (1)" suggest Kirama locality. The undescribed exact-name settlement item has no country or coordinates to establish identity; the other candidates' supplied locations do not establish the Ceylon station context. |
| 480 | weragoda | Q27449725, Q27457750, Q27449056, Q27457516 | "Location of experimental garden (2)" requires Weragoda locality. Four unnamed Sri Lankan areas are possible but have no labels establishing identity; the disambiguation page and person are not the garden locality. |
| 571 | dedigama | Q5249830, Q56529646, Q139317547 | "Location of agricultural show (2)" requires Dedigama locality. The exact-name item and two unnamed items are too sparsely described to establish identity; electoral divisions are not identified as the show locality. |
| 596 | shenzi | Q59775234 | "Origin of pepper (4)" and "origin of rhubarb (2)" suggest Shenzi as a trade-origin locality. The sole possibly relevant exact-name item has no description, classes, or coordinates; the people and fictional hyenas cannot establish it. |
| 348 | iriyagama division | Q27444232, Q27444230 | "Division of the experiment station (6)" identifies a particular Iriyagama research division. Uda Iriyagama East and Pahala Iriyagama are possible related areas, but neither sparse description identifies the experiment-station division. |
| 125 | rajpore | Q60380849, Q60499156, Q31787127 | "Origin of myrobalans (13)" and printed "Rhajpore" suggest a trade locality but supply no district or country to distinguish similar Indian names. Rajpur, Ranjapur, and Rajapur remain weak possibilities; the evidence does not justify selecting one. |
| 209 | nagrak | Q1154535, Q10955214, Q11035533, Q12499879, Q13544202, Q10954952 | "Plantation site (4)" and "place of growth (2)" give no province or district to distinguish the six West Java Nagrak candidates. No description specifically identifies the plantation. |

## Validation

**PASS**: independently reread `places_review_proposals.jsonl` and checked **600 rows** and **688 QID references**. Every non-null `qid` and every `also_possible` value appears among that same input record's candidates. **Zero invalid candidate references and zero rejected-candidate references.**

Also checked exact output fields, allowed outcomes and confidence values, outcome/QID consistency, nonempty reasons, duplicate references, unique keys, and preservation of the contiguous input order. This validation covers the reviewed prefix only; it does not imply completion of all 1,077 names.

Machine-readable check results: `places_review_validation.json`. The audit source is `places_review_decisions.tsv`; `build_places_review.py` recreates the proposals from those individually authored decisions.
