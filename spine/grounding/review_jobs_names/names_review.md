# Job: propose decisions for crop, plant, animal and commodity names waiting in review

You are working in `/home/jic823/Documents/ceylon/spine/grounding/review_jobs_names`. Create files only in
this folder. Do not edit anything else. No network access: decide only from what is in the input file.
The decisions must be made by reading each record, not by a rule. Aim to finish within about 60 minutes; work
down the file in order (it is sorted by how often the name occurs) and say how far you got.

## Input

`names_review_input.jsonl` — names of organisms (`type` TAXON) and traded goods (`type` COMMODITY) found in a
colonial agricultural journal published in Ceylon (the *Tropical Agriculturist*, 1881–1940s), one JSON object
per line:

- `key`: the name, lower-cased. `surfaces`: the spellings printed, with counts.
- `records`, `articles`, `first`, `last`: how often and when the journal uses it.
- `roles`: how the journal's articles describe it, with counts (`crop (333) | product (260) | pest (4)`).
  This is the main evidence of what is meant.
- `status` and `reason`: why an automatic matcher did not decide. `rejected`: items a reviewer has already
  rejected for this name (never choose one of these).
- `candidates`: Wikidata items found by a search, each with `qid`, `label`, `description`, `kind`
  (taxon / product / disease / other), `sitelinks` (how well known), `exact` (the item's label or an alias
  equals the name), `label_exact` (its own label equals the name), sometimes `taxon_name`.

## What to decide

For each name choose exactly one outcome:

- `match`: one candidate is what the journal means. Give its `qid`.
- `none`: none of the candidates is what is meant (say what the journal seems to mean).
- `ambiguous`: the journal uses the name in more than one sense that the candidates separate (give the
  candidate qids that remain possible), or the evidence cannot choose between two candidates.
- `not_a_thing`: the name is too generic to identify (for example "produce", "goods", "insects").

Rules:

1. Choose only among the candidates listed in that record. Never write a QID from memory.
2. The plant and its product are different items (the cacao tree, the cocoa bean; the tea plant, tea the
   drink). A TAXON name should go to the organism; a COMMODITY name should go to the product where the
   candidates include one, and to the organism only if no product item is listed (say so in the reason).
3. Old trade names are common: plumbago is graphite, not the plant genus; lac is the resin, not a lake;
   coir is coconut fibre; "pepper" in Ceylon is usually black pepper (Piper nigrum), not capsicum. Use the
   roles to decide, and choose `ambiguous` when the roles show both senses.
4. Software, bands, films, ships, people and places are never right.
5. If you are not confident, choose `ambiguous` or `none`. A wrong match is worse than no match.

## Output

`names_review_proposals.jsonl`, one line per name, in input order:

    {"type": ..., "key": ..., "outcome": "match|none|ambiguous|not_a_thing", "qid": "Q..." or null,
     "also_possible": ["Q...", ...], "confidence": "high|medium|low",
     "reason": "one or two sentences quoting the roles or descriptions that decided it"}

When you finish, write `names_review_summary.md`: how many names you decided, counts by outcome and
confidence, and ten decisions you were least sure of. Then run a check that every `qid` and every item of
`also_possible` appears among that record's candidates, and report the result.
