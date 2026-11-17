# Job: group the organisation names of a colonial agricultural journal into bodies

You are working in `/home/jic823/Documents/ceylon/spine/grounding/org_job`. Create files only in this folder.
Do not edit anything else. No network access: decide only from the input file. The grouping must be done by
reading the names and their evidence, not by a string-similarity rule (you may use a script to sort, count and
check). Aim to finish within about 75 minutes; work down the file in order (most frequent first), save your
output every 100 names, and say how far you got.

## Input

`org_names_input.tsv` — 2,265 organisation names (each in 5 or more articles) from the *Tropical
Agriculturist*, published in Ceylon, 1881–1945. Columns:

- `key`: the name, lower-cased, punctuation removed. `surfaces`: the spellings printed, with counts.
- `records`, `articles`, `first`, `last`: how often and when the journal uses it.
- `roles`: how the journal's articles describe it, with counts (`association (140) | kandy (9)`).
- `wikidata_status`, `wikidata_qid`, `wikidata_label`: where an earlier step already matched the name to a
  Wikidata item (`matched`), or skipped it as generic (`skip`).

Most of these bodies are not in Wikidata: planters' associations, government departments of Ceylon and India,
agency houses and firms, estate companies, research stations, botanic gardens, societies, banks, shipping
lines, newspapers. The aim is a local authority list: one entry per real body, with the printed names that
refer to it.

## What to produce

`org_bodies.jsonl`, one JSON object per body:

    {"body_id": "org-0001", "preferred_name": "Planters' Association of Ceylon",
     "kind": "association | government department | company | agency house | estate company | research station |
              botanic garden | society | bank | shipping line | newspaper or periodical | school or college |
              international body | other",
     "place": "Kandy, Ceylon" or "" (only if the names or roles say so),
     "country_or_colony": "Ceylon" or "" (only if the evidence says so),
     "member_keys": ["planters association of ceylon", "ceylon planters association", ...],
     "wikidata_qid": "Q..." or null (only a QID already given in the input for one of the member keys),
     "confidence": "high | medium | low",
     "evidence": "one or two sentences quoting the surfaces or roles that justify the grouping"}

`org_names_decisions.tsv`, one row per input name, in input order: key, outcome, body_id, note. Outcomes:

- `body`: the name refers to one body (give its body_id).
- `generic`: the name means a different body in each article and cannot be assigned ("department of
  agriculture", "the government", "planters association" with no place, "the company", "the board").
  Say in the note which bodies it could mean if the roles show them (for example the roles of
  "department of agriculture" name Cape Town and Washington as well as Ceylon).
- `not_an_organisation`: a place, person, product, publication title used as a title, or OCR debris.
- `unclear`: you cannot tell.

Rules:

1. Join names only when the evidence shows they are the same body: the same words in a different order, a
   clear abbreviation with a matching role, an OCR variant. Bodies of the same kind in different places are
   different bodies (the Planters' Association of Ceylon, the United Planters' Association of Southern India,
   the Dimbula Planters' Association). When in doubt, keep them apart and say so in the note.
2. A name that changes over time (a department renamed, a "Royal" added) may be joined if the roles and dates
   show continuity; say so in the evidence and set confidence medium.
3. Never invent a QID. Never state a founding date, place or fact that is not in the input.
4. A generic name must not be forced into a body just because one body dominates.

When you finish (or stop), write `org_summary.md`: names decided, counts by outcome, number of bodies and
their kinds, the twenty largest bodies with their member names, and twenty groupings you were least sure of.
Then run a check that every member key exists in the input, that no key belongs to two bodies, and that every
`body` row points to an existing body_id; report the result.
