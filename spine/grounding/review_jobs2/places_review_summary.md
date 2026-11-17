# Place review summary

Reviewed all **1,754 of 1,754 names**, from `bambarabotuwa` through `hedigalla`, in input order. No names remain unreviewed.

Decisions were made by reading each record and its supplied candidates, using only the input file. No network access or external sources were used. Scripts formatted records, saved manually written decisions in batches of 50 (plus the final four), and performed validation.

## Counts

| Outcome | Count |
| --- | ---: |
| match | 423 |
| none | 583 |
| ambiguous | 727 |
| not_a_place | 21 |

| Confidence | Count |
| --- | ---: |
| high | 889 |
| medium | 640 |
| low | 225 |

Confidence describes certainty in the proposed outcome. A high-confidence ambiguous decision can therefore reflect clear evidence that the record combines multiple places.

## Ten least-certain decisions

These ten were particularly difficult because candidates overlap, descriptions are missing, or the roles do not distinguish localities. All are left ambiguous at low confidence.

- **kendeng** (input line 14; Q56389082, Q25122106, Q25116870, Q24883685, Q24883708, Q26732435): 'Place of growth', 'origin of cinchona bark' and 'mountain range' lack a locality that distinguishes the several Indonesian Kendeng mountains; no range is clearly identified.
- **gudalur** (input line 103; Q2407283, Q1708408, Q20587109): 'Town at the foot of the peermaad ghat' favours a Theni-area Gudalur, while 'chembaly estate' does not establish whether other uses concern Nilgiris. The two Theni items are also not separated by their descriptions.
- **hmawbi** (input line 181; Q13063195, Q19710904, Q13073403): 'Agricultural station' and 'central farm' place the work at Hmawbi but do not separate the township, sparsely described settlement and town items; the listed town coordinates also differ substantially.
- **uduwawela** (input line 234; Q7877377, Q27448993, Q7877383, Q7876955, Q7877382): 'Experiment centre' and 'experiment site' provide no district. Several closely spelled Sri Lankan villages or localities remain possible for Uduwawela.
- **upper chindwin** (input line 667; Q21086301): 'District' and 'region in burma' identify Upper Chindwin, but the sole candidate has no label or description verifying identity.
- **champagne** (input line 736; Q29509595): 'Province in france' and 'region' identify Champagne, but the sole candidate has no label or description verifying its identity.
- **elagala** (input line 1016; Q49317570): The roles are empty and the sole candidate has no label or description, so Elagala's identity cannot be verified.
- **paragua** (input line 1258; Q2566275, Q7134653, Q56402130): 'River' does not separate Bolivian Paraguá and Venezuelan Paragua; 'island' adds an absent sense and the exact item is undescribed.
- **kotakota** (input line 1668; Q3199145, Q31935064): 'Place on lake nyasa' requires Kotakota town; neither unlabeled item verifies that locality and Kotakota Pan is not explicitly a town.
- **hedigalla** (input line 1754; Q27445841): 'Crown land lease', 'cart road' and 'bungalow' identify Hedigalla locality; Haddagala is only a possible spelling relation with no description verifying it.

## Validation

**PASS** — all 1,754 output records parse as JSON and correspond one-to-one to the input in its original order.
Every non-null `qid` (423 selections) and every `also_possible` entry (1,391 entries) appears among that record’s supplied candidates. **Zero invalid candidate QIDs and zero rejected candidates selected.**

Outcome values, confidence values, required fields, null-QID conventions, alternative-list placement, unique alternatives, and nonempty reasons also passed.
