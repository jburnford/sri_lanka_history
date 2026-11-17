# Working notes, headmen's divisions 1934 (written after the restart of 17 Nov; state of knowledge before it)

## Sources and scale
- PDF /mnt/data/jic823/ceylon_new_sources/ia/b32176910_0002/b32176910_0002.pdf. Page 15 = Map 7 (3141x5161 px at 400 dpi),
  pages 39/43/47 = Maps 17/18/19 (3054x5118). About 97 m per pixel.
- Key is on page 38 (lower half, three columns) and repeated on page 46. Read in full from page 38: key_raw.txt (112 numbers, all legible).
- Legends: Map 17 "Death rate from all causes, average 1929-33, per 1000": blank <20, dots 20-30, hatch 30-40, heavy hatch 40-50, solid 50+.
  Map 18 "Mortality during epidemic 1934/35 Nov-April, death rates per 1000": blank <20, dots 20-40, hatch 40-60, cross-hatch 60-80, (more below, not yet read).
  Map 19 "Excess mortality, actual death rate Nov-Apr as % of average": blank <150, hatch 150-250, heavy hatch 250-400, solid 400+; thick line = boundary of epidemic.
- Combined numbers printed on Map 17: "45-6", "62+65", "63+64", "101+104", "107-8", "109-112".

## Method decided
- Geometry from Map 7 (dotted lines survive as barriers; lines of Map 17 agree with them where compared, e.g. Puttalam).
- Identity from Map 17 numbers. Map 17 is segmented only in the unhatched south-west; its regions are labelled with key numbers,
  warped to Map 7 (affine from land-mask overlap, then cubic polynomial from block matching of Map 17 region edges against Map 7 ink;
  inlier residual about 5 px median) and each Map 7 fragment takes the majority number. Elsewhere Map 7 fragments are labelled by hand
  from side-by-side views.
- Segmentation improvement over seg.py: fill pin-holes (<80 px) in ink; grow seeds level by level (dist>=L for L=T..1), each pixel taking the
  nearest labelled pixel in its own connected piece; remaining ink goes to nearest label (edges on line centres). Sea = label at page corner.
- Map 17 ink cleaning: shading dots = components with max dimension <=22 px, dropped unless within 34 px of two separate large strokes;
  hatched areas (opening with 61 px lines at 28-36 degrees, closed with a 14 px disc) are wiped except thick strokes and their outline kept.
  This loses thin lines inside hatching (100|102 redrawn by hand; 42|43 not recovered -> use Map 7 there).
- Affine Map7->Map17 from land masks (4x downsampled, Powell): X17=0.98173x-0.00262y+58.1, Y17=0.00262x+0.98756y+245.8 (approx).
  Maps 18, 19 similar (scale 0.987/0.992, rotation -0.012).

## Identity findings so far (Map 7 side)
- Jaffna: Valikamam N and E are one cell ("45-6"); Jaffna Division (44) small triangle on the south coast; Vadamaradchi (48) the NE strip;
  Tenmaradchi 50; Pachchilaipallai 49. Jaffna lagoon is enclosed by lines and must be dropped as water. Islands: Delft carries 54, one island 53.
- Mannar: a mainland band between two dotted lines south-east of the island is hatched like 55 on Map 17 -> Mannar Island Division (inferred from shading).
- Vavuniya North 59 has a text-split fragment under "N.P."; Hurulu palata 88 is split by the word ANURADHAPURA (southern lobe between two dotted lines is solid like 88 on Map 17).
- Trincomalee: 72 small coastal cell; 73 Kaddukulam (+ text fragment); 75 Tampalakamam (2 fragments); 74 Koddiyar (3 fragments).
- Eravur and Koralai are one cell ("63+64"). Batticaloa lagoon area: Map 17 line west of the lagoon does not coincide with either Map 7 dotted line; UNRESOLVED,
  needs a close look (61 vs 62+65 vs strip 66).
- Puttalam: Kalpitiya division (83) = mainland strip north of the lagoon, west of dotted line x~540; Demala hatpattu (82) = east of that line AND the lobe south of the
  word PUTTALAM east of dotted line x~560; Puttalam pattu (84) = west of it. Kalpitiya peninsula carries no number and is dotted like 84 (83 is hatched) on Map 17: keep as separate uncertain feature unless Maps 18/19 settle it. Puttalam lagoon = water.
- Small cell between Nuwaragam and Kalagam south of a dotted arc at about (1050,2110): unresolved.
- Matale: 59-type fragments; "MATAL" fragment belongs with Matale North by shading; fragments along the vertical text near (1500,2700-2800) unresolved (22 or 24).
- Hambantota and the south: Map 7 dotted lines are clean (Giruwa E/W, Magam, Morawak, Hinidum, Kukulu etc.).

## Identity findings (Map 17 side, south-west)
- Text/dot splits to merge: 4 (two parts), 14 (two), 16 (two), 22 (two), 27 (two), 28 (two), 33 (two), 37 (two), 40 (three), 103 (three, incl. a northern tail between
  the Kalutara district line and Nawadun), 105 (two), 107-8 (two).
- 19 Udunuwara's cell is filled by its digits and needs a seed at about Map 17 (1304,3335).
- Unnumbered cells: Colombo town (cluster of small cells north of the cell with "1"), Kandy town (small dotted cell between 13 and 14 with a blob), Galle town (two tiny hatched cells beside 29).
  These are towns excluded from the key ("exclusive of Town", "beyond Municipal limits"); to be separate features marked as unnumbered.
- Strip south of 25 between Kotmale (26) and the Uva boundary: separated from 25's cell only by a thick S-shaped dash, from 26 by a thin solid line -> same cell as 25 probably; check.
- Barriers/seeds used on Map 17 (page px): barrier (930,4284)-(992,4268) gap between 10 and 33; 100|102 polyline (1380,4237)(1484,4229)(1532,4255)(1578,4276)(1613,4295)(1651,4310)(1675,4320);
  seeds (933,4665,r6) cell 29; (883,4666,r4),(866,4650,r4) Galle town; (1297,4755,r6),(1379,4749,r5) cell 36; (1251,4760,r4),(1189,4761,r3) cell 35.

## After the restart (17 Nov, afternoon)
- All scripts rebuilt in this folder: hd_lib.py, s1_segment.py, s2_register.py (results identical to before: 236 Map 7 fragments, affine and polynomial as noted).
- Hand tables are point-based (ident7.tsv, ident17.tsv: x, y, key) so they survive re-segmentation.
- Batticaloa resolved by cell order and by where Map 17 prints its numbers: Map 7 draws a Koralai|Eravur line that Map 17 omits ("63+64"), so Map 7's cell with the "P" of E.P. is
  Eravur (part of 63+64); the next cell south (west shore of the lagoon) carries "61" at its position on Map 17; the cell under "TICALOA" plus the lagoon strip = 62+65; Sammanturai 67 the big cell; the coastal cell east of it 66.
  The Map 17 lines here sit 6-13 km from Map 7's, so these identities are inferred, not read.
- Giruwa: W = west of the dotted line that runs from the Kolonna boundary to the coast (fragments split by the lettering), E = between it and the Magam line.
- Cell south of the dotted arc at (1050,2110): on the Kalagam side of the dots, split off only by the letter K -> 89.
- Fragment 24 by "Karaichchi": west of the district dashes -> 51.
- Strip south of "25": same cell as 25 (only the digits and a thick dash divide them).
- Unnumbered dotted tongue inside 80 on Map 17 = western tongue of Dambadeni (78), outlined by dots on Map 7.
- Small cell on the coast between Pitigal N and S (Chilaw town?) is unnumbered: key CHI.
- Rule settled for the south-west: a Map 7 fragment with no hand label takes the majority number of the warped Map 17 regions; only fragments flagged S17 in ident7.tsv
  (lettering hides the dotted lines: Negombo/Colombo/Kalutara/Kandy/Galle) are cut pixel by pixel along the Map 17 lines.
  Reason: Map 17's interior lines sit up to 5-8 km from Map 7's in Matara, Hambantota (42|43), Ratnapura (100|102) and Batticaloa, so Map 7's own cells are kept wherever they are complete.
- Matara: Map 7 cells by position: under "MATARA" = Kandaboda 39, next south = Gangaboda 40, SE coast = Wellaboda 36, small coast cell = Four Gravets 35 (inferred by position), W = Weligam 37.
- Checked whole island in side-by-side tiles (qa.py). Batticaloa: Map 17's 63+64 southern line coincides with Map 7's line south of the "P" cell, so the P cell is Eravur (inside 63+64) - confirmed.
- Kalpitiya peninsula: unnumbered on all three maps and shaded like 84 (not 83) on Maps 17, 18 and 19. Kept as its own feature, marked uncertain.
- Small islands whose outline ring has no ink-free core (several off Jaffna, one in Puttalam lagoon mouth, Karaitivu strip) are not in the segmentation and are left out.
- names_map7.tsv written (66 names read on Map 7). Kalutara: Map 7 prints "Totamune Div." and "Mudaliyar's" in two coastal strips; Map 17 has a single cell 9.
- s4_georef.py: fit of plate land to SRTM land (affine, then quadratic); running.
- Georeferencing done (s4_georef.py, about 15 min). Affine: land mismatch 2.5%, landmark coast shifts RMS 1.3 km (max Trincomalee 2.7). Quadratic: 2.3%, RMS 0.9 km (max Mannar 1.6, Dondra 1.5). georef.npy = quadratic.
- Death-rate classes: automatic reading (s5_classes.py, shading_features.tsv) not reliable: band vs solid is a continuum of ink share, cross-hatch often unclassified. Decision: leave classes out of the GeoJSON.
- s6_polygons.py written (arc-based vectorisation with shared simplified edges), confidence.tsv written.
- DONE 17 Nov: outputs written (geojson 109 features, key.tsv, method.md, build.py); build.py rerun reproduces the GeoJSON byte for byte; checks in checks.txt; vs_district1946.tsv.
