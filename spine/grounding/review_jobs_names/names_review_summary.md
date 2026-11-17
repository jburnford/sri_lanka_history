# Name review summary

Reviewed all **681 of 681 names**, in input order: record 1 (`COMMODITY: cocoa`) through record 681 (`COMMODITY: penang cloves`). No records remain unreviewed.

Each proposal was chosen individually after reading its name, surfaces, roles and candidate descriptions. Decisions use only the supplied input; no network access or external sources were used. The Python script validates the proposals and does not choose outcomes.

## Outcomes

| Outcome | Names |
| --- | ---: |
| match | 241 |
| none | 398 |
| ambiguous | 27 |
| not_a_thing | 15 |

## Confidence

| Confidence | Names |
| --- | ---: |
| high | 435 |
| medium | 231 |
| low | 15 |

Confidence describes confidence in the proposed decision, including a decision to leave a name unmatched or ambiguous. A `none` outcome means that the listed candidates do not adequately identify the intended entity; it does not mean the journal name is meaningless. Named cultivars, processed derivatives and regional trade categories were left unmatched when the candidates only described a broader or different entity. Organism fallbacks for commodities are explained in the relevant reasons.

## Ten decisions with greatest remaining uncertainty

These ten low-confidence cases need the most useful follow-up evidence. Other unresolved cases remain explicitly marked in the proposals.

| Input line | Type and name | Outcome | Remaining candidates | Uncertainty |
| ---: | --- | --- | --- | --- |
| 13 | TAXON: dadap | ambiguous, low | Q715744 (Erythrina variegata); Q3635975 (Erythrina subumbrans) | “Shade tree (80)” and “green manure plant (14)” fit a dadap tree, but the two Erythrina species remain unresolved by these roles. The place candidates do not fit. |
| 76 | COMMODITY: red wood | ambiguous, low | Q124303847 (red sandalwood); Q96780079 (redwood) | “Traded product (31)” and “ordinary to fine bright (1)” identify a wood commodity, but do not distinguish the listed red sandalwood and redwood materials. |
| 121 | TAXON: custard apple | ambiguous, low | Q275620 (Annona squamosa); Q472653 (Annona reticulata) | “Custard apple” with “fruit tree (4)” supports an Annona organism, but the roles do not distinguish Annona squamosa from Annona reticulata. |
| 177 | TAXON: rubber tree | ambiguous, low | Q156538 (Hevea brasiliensis); Q160576 (Ficus elastica) | “Source of rubber (5)” and “rubber tree” do not distinguish Hevea brasiliensis from Ficus elastica; both plant candidates remain possible. |
| 308 | TAXON: weevil | ambiguous, low | Q7415384 (Curculionidae); Q906802 (Anthribidae) | “Pest attacking stored paddy (2)” and “enemy of cinchona (1)” indicate potentially different weevils; the evidence cannot resolve the listed weevil families or justify one species. |
| 345 | TAXON: coffee borer | ambiguous, low | Q510963 (Hypothenemus hampei); Q8069840 (Zeuzera coffeae) | “Coffee borer” and “enemy of coffee (1)” do not specify whether the intended pest is Hypothenemus hampei or Zeuzera coffeae. |
| 380 | TAXON: leptocorisa varicornis | ambiguous, low | Q13111923 (Leptocorisa oratorius); Q24957069 (Leptocorisa acuta) | “Scientific name of the rice-bug (1)” supports Leptocorisa, but the evidence does not resolve Leptocorisa oratorius versus Leptocorisa acuta for the historical name varicornis. |
| 392 | TAXON: elk | ambiguous, low | Q35517 (moose); Q180404 (Cervus canadensis) | “Game animal (5)” and “hunted animal (2)” do not distinguish the moose and Cervus canadensis senses of “elk”; no species-specific evidence is supplied. |
| 402 | COMMODITY: cotton goods | ambiguous, low | Q3695916 (cotton fabric); Q11457 (cotton) | “Imported goods (3)” and “cotton goods” could denote cotton fabric or fibre goods; the roles do not establish the processing level. |
| 652 | TAXON: balsam | ambiguous, low | Q158748 (Impatiens noli-tangere); Q654064 (Impatiens Walleriana) | “Flower (1)” and “softwooded plant (1)” support an ornamental balsam, but the supplied descriptions do not distinguish the two Impatiens candidates. |

## Validation

**PASS:** all 681 proposal identities and their order agree with the input. Every `qid` and every item in `also_possible` appears among the candidates of its own input record: **297 QID references checked, zero invalid references**. None selects an item in that record’s `rejected` list.

The check also verifies required fields, outcome and confidence values, nonempty reasons, distinct alternatives, one QID for each match, and null QIDs for nonmatches. This is a structural and eligibility check; unresolved semantic uncertainty is retained in the decisions.

Re-run the check from this folder with:

```sh
python validate_names_review.py
```
