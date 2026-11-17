# Chief Headmen's Divisions, 1934: how the layer was made

`headmen_divisions_1934.geojson` holds 109 multipolygons: 104 numbered cells covering all 112 numbers of the printed key, and 5 unnumbered cells. It was made on 17 November 2026 from *Ceylon Malaria Epidemic 1934-35, Supplement: Maps and Charts* (1935), scan `b32176910_0002.pdf`. The plates are at 24 miles to an inch; one pixel of the 400 dpi page image is about 97 m on the ground. Treat positions as good to a few kilometres at best.

## Sources used

- PDF page 15, Map 7 "Administrative Divisions": geometry. Dotted division lines, dash-dot district lines, solid province lines.
- PDF page 39, Map 17: identity. The same divisions with numbers.
- PDF page 38, the key "Numbers Given in Maps 17, 18, and 19": number to name, district and province. Read from the 400 dpi page image, not from the OCR. All 112 entries were legible. The repeat of the key on page 46 was not compared with it.
- PDF pages 43 and 47, Maps 18 and 19: looked at only for the Kalpitiya peninsula and for the shading test described below.

## Steps

1. **Segmentation of Map 7** (`s1_segment.py`, `hd_lib.py`). Ink is thresholded against the local background. Ink-free cores more than 9 px from any ink are seeds. Seeds are grown outward level by level, each pixel joining the nearest seed within its own connected piece, so that regions meet in the gaps of the dotted lines. Ink pixels then go to the nearest region, which puts edges on the centre of the printed lines. Result: 235 land fragments. Lettering over the map splits many divisions into several fragments.
2. **Segmentation of Map 17**, south-west only, after removing shading: small round components (dots) are dropped unless they sit between two larger strokes; hatched areas are found by morphological opening with long lines at the hatch angle and wiped, keeping their outline. Seven seeds and seven barrier segments were added by hand (`seeds17.tsv`, `barriers17.tsv`); the barriers redraw the 100|102 line, which is lost with the hatching, and close one gap in a district line.
3. **Plate-to-plate registration** (`s2_register.py`). Map 17 was fitted to Map 7 by an affine that maximises overlap of the two land masks (2.2% of land mismatched), then refined in the south-west with a cubic polynomial from block matching of Map 17 region edges against Map 7 ink (172 of 223 blocks kept; median residual 5 px, 90th percentile 9 px). The two plates are not the same drawing: interior lines differ by up to 5-8 km in Matara, Hambantota, Ratnapura and by 6-13 km round the Batticaloa lagoon.
4. **Identity** (`s3_identity.py`, tables `ident17.tsv`, `ident7.tsv`). Each Map 17 region in the south-west was given the number printed in it (75 points). Each Map 7 fragment then got a key number in one of three ways:
   - by hand, from side-by-side views of Map 7 and Map 17 (130 fragments, 81% of the land area; this covers the north, east, centre and south-east, where Map 7's cells are clean);
   - by the majority number of the Map 17 regions lying over it (82 fragments, 16%);
   - by cutting it along the Map 17 lines where lettering on Map 7 hides the dotted lines (23 fragments, 3.4%, in Negombo, Colombo, Kalutara, Kandy and Galle).
   `fragments.tsv` lists every fragment, its number and which rule gave it. Water bodies enclosed by lines (Jaffna lagoon, Puttalam lagoon, the inlet north of Batticaloa, legend-box fragments) are marked W and left out.
5. **Georeferencing** (`s4_georef.py`). Plate pixels were fitted to longitude and latitude by maximising overlap between the plate's land and the SRTM 30 m land mask (resampled to 0.001 degrees). No control points were used.
6. **Vectorising** (`s6_polygons.py`). Boundaries are traced on the pixel lattice as arcs between junctions; each arc is simplified once (Douglas-Peucker, 1.5 px, about 150 m) and every polygon is assembled from those shared arcs, so neighbours have identical edges. 89,471 lattice vertices became 5,472.

## Fit and residuals

| fit | land mismatch | RMS at 8 landmarks | largest |
|---|---|---|---|
| affine (6 parameters) | 2.5% | 1.3 km | Trincomalee 2.7 km |
| quadratic (12 parameters), used | 2.3% | 0.9 km | Mannar island 1.6 km, Dondra Head 1.5 km |

Quadratic fit, shift of the plate's coast against the modern coast: Point Pedro 0.0 km, Dondra Head 1.5, Kalpitiya peninsula tip 0.3, Mannar island 1.6, Trincomalee 0.4, Batticaloa lagoon mouth 0.0, Colombo 0.9, Hambantota 0.7.

These residuals are not independent control-point errors. Each is the shift that best aligns the plate's coast with the SRTM coast inside a 43 km window centred on the landmark, and the landmark coordinates were typed from memory only to place the window. They measure how well coast matches coast locally, on the same data the fit used. They say nothing direct about interior boundaries. The affine is adequate for the stated accuracy; the quadratic was kept because it halves the Trincomalee error.

## Attributes

- `key_number`: as printed on Map 17, including the combined forms `45-6`, `62+65`, `63+64`, `101+104`, `107-8`, `109-112`. Empty for the five unnumbered cells.
- `name_key`: names from the key; combined cells carry all their names separated by semicolons.
- `name_map7`: the name as lettered on Map 7, for the 66 cells where I read one. Blank means not printed or not read; Map 7 was not searched exhaustively, and the count of divisions per district was not checked against Map 7's lettering.
- `district`, `province`: from the key's headings (21 districts, Negombo and Mullaittivu among them). `district_1946` maps these to the names used in the `urban_census` layer (Negombo to Colombo, Puttalam and Chilaw to "Puttalam and Chilaw"; Mullaittivu to Vavuniya is my assumption).
- `identity_confidence`: 95 "printed number read directly", 12 "inferred", 2 "uncertain: ...". `note` gives the reason. Table: `headmen_1934_work/confidence.tsv`.

## Uncertain or inferred

- **Batticaloa (61, 62+65, 66, 67).** Map 17's lines round the lagoon do not coincide with Map 7's. Cells were matched by order along the coast and by where Map 17 prints each number. 62+65 joins the cell under the word BATTICALOA with the lagoon strip.
- **63+64.** Map 7 draws a line inside it (Koralai | Eravur) that Map 17 omits. Kept as one cell.
- **Matara (35, 36, 39, 40).** Numbers read on Map 17, cells matched to Map 7 by position. 35 is the small coastal cell.
- **42|43 and 100|102.** Geometry is Map 7's; Map 17 draws these lines several kilometres away.
- **Kalpitiya peninsula.** No number on any of the three maps. It is shaded like 84 (Puttalam pattu), not 83 (Kalpitiya division), on all three, although Kalpitiya town is on it. Own feature, marked uncertain. The mainland strip north of the lagoon is 83.
- **Unnumbered town cells.** Colombo, Kandy and Galle are small unnumbered cells on Map 17; the key says "exclusive of Town" or "beyond Municipal limits" for the neighbouring divisions. Their outlines are rough. A small coastal cell on Map 7 between Pitigal North and South, not on Map 17, is kept as "unnumbered cell at Chilaw", uncertain.
- **55 Mannar Island Division** includes a mainland sliver opposite the island, by its shading on Map 17.
- **53 Islands.** Only three island outlines segmented; all are given to 53 though only one carries the number. Smaller islands off Jaffna, the islet at the mouth of Puttalam lagoon and the long islet north of Kalpitiya are missing from the layer. There is no "unassigned islands" feature.
- **22 Matale South.** Its boundary with 23 and 24 is uncertain by about 3 km under the lettering.
- **Colombo, Negombo, Kalutara, Kandy, Galle.** Parts of these outlines follow Map 17 because Map 7's dots are under lettering. Kalutara: Map 7 has two coastal strips ("Totamune Div." and "Mudaliyar's"), Map 17 one cell 9.
- **25** includes the strip south of the figure 25; **89** includes a small cell cut off only by a letter.

## Death-rate classes: left out

The legends are legible (Map 17: under 20, 20-30, 30-40, 40-50, 50 and over per 1000; Map 18: under 20, 20-40, 40-60, 60-80, 80-100, 100 and over; Map 19: under 150, 150-250, 250-400, 400 and over per cent). I tried to read the class of each division from ink statistics (`s5_classes.py`, `shading_features.tsv`). It separates blank, dotted and hatched cells but not the two darkest classes, whose ink share runs continuously from 0.73 to 0.99, and it leaves 9 to 13 cells per map unclassified and 13 too small to measure. I did not check the automatic classes by eye. No class is in the GeoJSON.

## Checks run (`s7_checks.py`, `s8_vs_district1946.py`; output in `headmen_1934_work/checks.txt`)

- Key numbers: 112; all 112 are on the map, in 104 cells.
- Geometry: no invalid or empty polygons; no pair overlaps by more than 0.01 sq km; sum of areas equals area of the union (25,711.6 sq mi), so no overlaps. The union has one hole, 28.5 sq mi at 81.62 E 7.73 N, the outlined inlet north of Batticaloa left out as water. There are no other gaps.
- Total area 25,712 sq mi against 25,332 printed (+1.5%). The plate's thick coast line and the inclusion of small lagoons account for some of this; I did not separate the causes.
- Area by province, sq mi (layer / reference / difference): Western 1452 / 1432 / +1.4%; Southern 2234 / 2146 / +4.1%; Northern 3528 / 3429 / +2.9%; Eastern 3896 / 3840 / +1.5%; North Western 3151 / 3016 / +4.5%. Against the references given from memory: Central 2255 / 2290 / -1.5%; North Central 3990 / 4009 / -0.5%; Uva 3289 / 3277 / +0.4%; Sabaragamuwa 1917 / 1893 / +1.3%.
- Towns (`urban_census`, 42 with a district): 38 fall in a division of the right district. Avissawella (Colombo) falls in 109-112 (Kegalla), 1.1 km from the Colombo polygons. Three fall just off the coast: Galle Town 0.1 km, Negombo 1.5 km, Chilaw 2.0 km from the nearest polygon, which is of the right district in each case.
- Against the existing `district_1946.geojson` (read only): every one of the 109 cells has its expected district as the district it overlaps most; 96 lie at least 80% inside it. The 13 below 80% are border, coastal or island cells (lowest: Trincomalee Town and Gravets 36%, Pachchilaipallai 64%).

## Not verified

- No independent ground control; interior accuracy is untested apart from the town and district comparisons above.
- The key on page 46 was not compared with page 38.
- Map 18 and Map 19 numbers were not read cell by cell to confirm Map 17's.
- `name_map7` is partial.
- Division-level identity inside a district rests on my reading of Map 17; no outside source was consulted.

## Rebuilding

`/usr/bin/python3 headmen_divisions_1934_build.py` reruns the steps from the page images and the hand tables in `headmen_1934_work/` and reproduces the GeoJSON byte for byte (checked once). It reuses the two saved fits; `--refit` recomputes them, about 15 minutes. The polynomial plate-to-plate fit was computed before the last Map 17 seed (cell 19) was added, so a refit may move south-western lines by a pixel or so.
