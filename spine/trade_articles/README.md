# Trade articles: grounding to Wikidata, and what sits below it

Pilot, 18 November 2026. Seven families of Ceylon exports (tea, coffee, cinchona bark, cinnamon, coconut
products, coir, plumbago) on two sides: the Ceylon Blue Book ledgers (`../bluebook/extracted/trade*.tsv.gz`,
exports, 1880–1928) and the UK Annual Statements (`uk_trade_db`, imports, 1868–1900; a separate repository).

## The model

A **printed article** is one heading in one source. It is never merged away. Each is assigned to a **trade
concept** (`pilot/concepts.tsv`), and each concept states its link to Wikidata and **what kind of link it is**:

| relation | meaning | example |
|---|---|---|
| `exact` | the article is the item | Plumbago → graphite (Q5309) |
| `closest_item_differs` | the nearest item is not quite the traded good | Tea → Q6097, which describes the drink, not the dried leaf |
| `narrower` | a state or manufacture of the item | Coir yarn, rope, matting → coir (Q1029620) |
| `part_of_taxon` | another part of the plant | Tea seed → Camellia sinensis (Q101815) |
| `by_product` | waste or refuse of the item | Tea waste, coffee husks |
| `not_the_commodity` | shares the word only | Tea lead, tea machinery, tanners' bark, "cordage other than coir" |
| `heading_lost` | a sub-line whose heading was not read | "Cocoanut", by weight, 1880–1904 |
| `uncertain` | not established | UK "Nuts and Kernels: Coco-nut" |

Distinctions Wikidata does not hold are **facets** on the article (`pilot/article_rules.tsv`): species
(Coffea arabica Q47685, Coffea liberica Q47718), mode of production (plantation, native), grade (plantation or
wild cinnamon; mattress or bristle fibre). Two articles are comparable when concept and facets match, or when
one side's lines sum to the other's: the UK prints one "Coffee, Raw" where Ceylon prints three.

Every QID came from the Wikidata vector search on 18 November 2026, none from memory. No item was looked for
below the level shown (coir yarn, for instance, may have one).

## What the pilot found (`pilot/articles.tsv`, 265 printed articles)

- Ceylon side: 147 headings, 146 assigned. Of the figures under them, about half link `exact`, 28% link to an
  item that is not quite the good (tea, desiccated coconut), 16% are a narrower state, and 3% only share the word.
  Matching on the head word, as the graph does now, puts all of these on one item.
- UK side: 118 headings, 32 assigned, 15 set aside, 71 unassigned. Most unassigned and set-aside headings are
  the UK parser's group mix-ups surfacing under these words ("TEA / Red, in Casks" is wine; "BARK / Herrings";
  "PLUMBAGO / PORK, Salted"), plus tanning barks and manufactured coffee, which are outside the pilot.
- The same good moves between classes: cinchona bark is under Drugs in the UK statements and under "Dyeing
  materials" in Ceylon from 1921. Headings also change form by era (1880–1900 flat, 1901–06 "Class— Sub",
  1907 on "Head, sub—") and carry OCR forms ("Onchona", "Inchona", "malting" for matting).

## The mirror comparison (`pilot/mirror.tsv`, 1880–1900)

Ceylon's recorded exports to the United Kingdom against the UK's recorded imports from Ceylon, by commodity and
year. **Neither side is treated as right.** Each row carries the evidence each side has for its own figure: on the
Ceylon side, whether the UK's share of the article agrees between quantity and value; on the UK side, its trust
rank and how it sits against its neighbouring years. The two governments also counted different things (shipment
and arrival dates, declared destination, cargo sent "for orders"), so a few per cent is the normal state.

| Outcome, of 126 commodity-years | Count |
|---|---:|
| Agree within 5% | 16 |
| Differ 5–15% | 10 |
| Differ more than 15% | 6 |
| Ceylon partial (only a minor line was read, e.g. Liberian coffee) | 9 |
| Ceylon missing | 60 |
| UK missing | 5 |
| Both missing | 20 |

- Tea agrees within 2% in eight of twelve comparable years; coffee within 3.5% in the five years where the
  plantation line was read; cinnamon within 2.5% in both comparable years.
- Two disagreements can be attributed on internal evidence, one to each side. Tea 1891: the Ceylon row gives the
  UK 9% of the quantity but 94% of the value, so its quantity has lost a digit. Tea 1893: the Ceylon row is
  self-consistent and fits the UK's 1892 and 1894 figures, while the UK's own 1893 figure sits 10% below them.
  Neither has been checked against the page.
- Plumbago differs by 6–23% in seven of eight comparable years, in both directions, with both sides
  self-consistent. That looks like a real difference in what was counted, not misreading.
- The main result is the Ceylon-side gap: 69 of 126 commodity-years have no usable figure for the main line.
  The 1880–1900 ledgers were already known to be weak (1,288 of 2,760 articles agree with their printed
  totals); the mirror shows where.
- The unqualified "Cocoanut" line, where it was read, runs at 0.76 to 1.36 times UK coconut oil imports from
  Ceylon, the right order of magnitude for it to be the oil line, but not close enough to settle it.

## Limits
- Rules, not reading: the assignments were made by pattern and read down once by Claude. Not reviewed by a person.
- The UK side is used as exported on 17 August 2026; that repository has later uncommitted work.
- UK readings with no unit are taken in the unit the statements print for that article and marked "(assumed)".
- The neighbour test is weak in fast-moving series (tea before 1885, coffee's collapse), so it only counts
  against the UK figure when the Ceylon figure fits the UK's neighbouring years better than the UK figure does.

## Rebuild
```sh
python spine/trade_articles/pilot/build_pilot.py     # needs duckdb and the UK database (UK_TRADE_DB)
```
