# Review: is this printed name the person in de Silva's History?

You are judging 150-odd proposed matches between a person named in a modern history of Sri Lanka and a group of
records that share a printed name in colonial lists. Work only in `spine/people/desilva_review/`. Standard-library
Python only (`/home/jic823/miniforge3/bin/python`). No network. Do not change any file outside this folder.

## What you are given
`input.tsv`, one row per pair:
- the **de Silva person**: name, aliases, the years in which the book mentions them, birth and death if the book
  gives them, the offices the book gives, a one-line summary (ours, not the book's words), and the printed pages;
- the **printed name**: a key (surname and initials), the forms printed, and every record under it by year. Records
  are Ceylon Blue Book civil establishment entries (1863-1917, an office title per volume) or, where marked
  `[directory]`, a role in Ferguson's Ceylon Directory for 1921-22. A printed name is not a person: "J. Perera"
  gathers several men. `colonial_office_list_match` gives a biography matched by program, if any;
- `basis`: why the pair was proposed.

You may read these for more evidence (read-only; never copy sentences from them into your outputs):
- `/home/jic823/ceylon/timeline/desilva_timeline.json`: the full timeline. `events` list the people involved
  (by `id`) with dates and descriptions; `relations` tie people to offices, places and each other.
- `../desilva_people.json`: the people file the atlas uses.
- `../../bluebook/extracted/officer_matches.tsv`: the Blue Book name groups, with every office as printed.
- `../../graph/col_persons.tsv.gz` and `../../graph/postings.tsv.gz`: Colonial Office List biographies and careers.

## The judgement
For each pair decide whether the records under the printed name include the de Silva person.
- `same_person`: the sources given here agree on something specific beyond the name: an office the book also
  gives, a career that fits the book's account in rank and date, or a Colonial Office List biography that fits.
- `probably_same`: the name is distinctive and the dates and standing fit, but nothing specific confirms it; or
  you know it from general knowledge and the sources here do not show it. Say which.
- `namesake`: the records are of someone else: wrong dates, or an office that cannot be the person the book
  describes (a politician or scholar the book never places in government service is not a railway clerk).
- `some_records`: the printed name clearly gathers more than one man and only some records are the de Silva
  person. Give the years that are his in `years_that_fit`.
- `unclear`: not enough to say. Prefer this to a guess.
Being a common surname with common initials is a strong reason for `namesake` or `unclear`. A senior office in
the right years under a rare name is a strong reason for `same_person`.

Keep what you know from outside these files apart from what the files show. If a decision rests on outside
knowledge, put it in `outside_knowledge` and do not go above `probably_same`.

## Test cases (your output must agree)
- Sir Hugh Clifford (`person:hugh-clifford` or similar id) with key `clifford:h`: `same_person` (Colonial
  Secretary 1907-1911 in the Blue Books; the book has him as Colonial Secretary under McCallum).
- John de Silva with any `de-silva:j_*` clerk, translator or apothecary: `namesake`.
- James Pieris (`pieris:j_*` customs and fiscal clerks, police inspectors): `namesake`.
- Ananda Coomaraswamy with `coomaraswamy:a_k` (Director, Mineralogical Survey, 1905-1906): the files here do not
  give the book's Coomaraswamy that office, so at most `probably_same`, with the outside knowledge stated.

## Outputs
- `decisions.tsv`: `pair_id`, `desilva_id`, `printed_name_key`, `decision`, `years_that_fit` (blank unless
  `some_records`), `evidence` (under 200 characters, your own words: what in the files decided it, naming the
  office and years), `outside_knowledge` (blank if none), `files_consulted` (which of the extra files you opened
  for this pair). One row for every row of `input.tsv`, same order.
- `check.py`: asserts every pair has exactly one decision from the list, the test cases hold, no field is over
  200 characters, and prints the count of each decision.
- `README.md` (under 60 lines): counts by decision; the ten pairs you found hardest and why; any de Silva person
  whose own entry looks wrong (a likely misread name, two people merged, a wrong date), listed by id for the
  person who maintains that file; what a human reviewer should look at first.

Decide every pair by reading its row, and the extra files where the row is not enough. Do not decide by rule.
Stop when the three outputs are written and `check.py` passes.
