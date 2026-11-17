# Job: propose decisions for place names waiting in review

You are working in `/home/jic823/Documents/ceylon/spine/grounding/review_jobs2`. Create files only in this
folder. Do not edit anything else. No network access: decide only from what is in the input file.
Use `/home/jic823/miniforge3/bin/python` if you need a script, but the decisions must be made by reading each
record, not by a rule. An earlier run of this job decided 600 names in its time; this file is longer. Work steadily for about 90 minutes and get as far as you can, writing proposals to the output file as you go (append every 50 names) so that nothing is lost; work down the file in order (it is sorted by
how often the name occurs) and say how far you got.

## Input

`places_review_input.jsonl` — 1,754 place names found in a colonial agricultural journal published in Ceylon
(the *Tropical Agriculturist*, 1881–1940s), one JSON object per line:

- `key`: the name, lower-cased. `surfaces`: the spellings printed, with counts.
- `records`, `articles`, `first`, `last`: how often and when the journal uses it.
- `roles`: how the journal's articles describe the place, with counts (for example
  `district (37) | town (4) | origin of labourers (1)`). This is the main evidence of which place is meant.
- `reason`: why an automatic matcher did not decide. `proposed` / `rejected`: a candidate it leaned to, or one
  a reviewer has already rejected (never choose a rejected one).
- `candidates`: Wikidata items found by a search, each with `qid`, `label`, `description`, `kind`
  (settlement / area), `classes`, `in_sri_lanka`, `sitelinks` (how well known), `lat`, `lon`, and `exact`
  (true when the item's own label or alias equals the name).

## What to decide

For each name choose exactly one outcome:

- `match`: one candidate is the place the journal means. Give its `qid`.
- `none`: none of the candidates is the place meant (say what the journal seems to mean).
- `ambiguous`: the journal uses the name for more than one place, or the evidence cannot separate two
  candidates (give the candidate qids that remain possible).
- `not_a_place`: the name is not a place (a crop, a person, a generic phrase).

Rules:

1. Choose only among the candidates listed in that record. Never write a QID from memory, and never add one
   that is not in the record.
2. The journal's period is 1881–1945 and its world is the British Empire and the tropics. Prefer the
   historical sense: "Madras" may mean the Presidency (an area) as well as the city; "Assam" the province;
   "Ireland" the island. A modern state is not the right item for a colonial-era territory unless nothing
   else fits; in that case say so in the reason and choose `ambiguous`.
3. Where the roles say district or region and the candidate is a town of the same name (or the reverse),
   prefer a candidate of the right kind; if there is none, choose `ambiguous`, not the wrong kind.
4. A name with roles pointing to Ceylon ("estate in dimbula", "village in kandy district") should not be
   matched to a place elsewhere, however well known.
5. If you are not confident, choose `ambiguous` or `none`. A wrong match is worse than no match.

## Output

`places_review_proposals.jsonl`, one line per name, in input order:

    {"key": ..., "outcome": "match|none|ambiguous|not_a_place", "qid": "Q..." or null,
     "also_possible": ["Q...", ...], "confidence": "high|medium|low",
     "reason": "one or two sentences quoting the roles or descriptions that decided it"}

When you finish, write `places_review_summary.md`: how many names you decided, counts by outcome and
confidence, and ten decisions you were least sure of. Then run a check that every `qid` and every item of
`also_possible` appears among that record's candidates, and report the result.
