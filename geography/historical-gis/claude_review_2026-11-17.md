# Review of the Ceylon historical GIS, 17 November 2026

A second reading of `ceylon-history.gpkg` (built by Codex Sol), made by Claude. Nothing in the database was
changed. Roads were given integrity checks only: the owner has reviewed them and asked for OSM alignment.
"Confirmed" means I ran the query myself; "reported" means a subagent ran it and I did not repeat it; "from
memory" means a figure recalled, not taken from a source.

## Errors

1. **Kitulgala is about 48 km out of place** in `motor_amenity_places_1936` (confirmed). The rest house and
   petrol depot rows sit at 80.25 E, 6.59 N. The 1834 gazetteer layer in the same database has Kitulgala at
   80.4068 E, 6.9966 N. The Wikidata coordinate looks like 6°59′ / 80°25′ entered as decimals. Smaller offsets
   reported by the same check: Kalpitiya 8.3 km, Piliyandara 6.2 km. 56 of 170 amenity QIDs have no GeoNames
   cross-reference and were not checked.
2. **The traced 1946 districts fail point-in-polygon joins on the coast** (confirmed for three towns).
   Hambantota and Trincomalee fall in no district; Avissawella falls in Kegalla, not Colombo. Reported:
   Tangalla also falls outside. The fit (3.41 km) is on every row, but nothing says joins will fail. Topology
   is clean: no overlaps or gaps, and the provinces equal the union of the districts.
3. **`rail_1936_osm` carries modern attributes** (gauge confirmed). The Kelani Valley ways have gauge 1676 or
   blank; the line was 762 mm in 1936 (from memory; `rail_1915_traces` has 762). Reported: no geometry for
   Avissawella–Yatiyantota, Avissawella–Opanake or Nanu Oya–Ragalla, and the Kelani bridge span and the last
   568 m into Batticaloa are missing. All of this is in `railway_qa.md` and on no feature. Summed lengths are
   track length, not route length.

## Doubts

4. **One census `feature_id` holds counts for different territories** (reported). `district:puttalam` 1871 and
   1881 include Chilaw in the DCS series and exclude it in the 1891/1901 tables; `district:vavuniya` 1881
   includes Mullaitivu in one source; `urban:negombo` 1901 is 19,819 or 11,040; `district:colombo` excludes
   the Municipality in 1891/1901. A time series by `feature_id` shows swings of −61% and +219%. Two DCS cells
   differ from exact counts beyond rounding: Hambantota 1946 (150,000 / 149,686), Kandy 1931 (587,700 / 587,916).
5. **Fa Hien Cave** in `historical_wikidata_places` sits about 5 km south of Yatagampitiya (reported, from
   memory).
6. **1834 gazetteer points** (my own check). 65 of Chitty's "N miles <direction> of <place>" statements were
   tested against the plotted points: 53 agree. The 12 others look like split numbers in the OCR or rough
   bearings in the text, not wrong towns. Worth a look: Mahagam (printed 2 miles from Hambantota, plotted 14)
   and Kalani (10 miles from Colombo, plotted 4).

## Limitations that should be on the features

7. **`province_census` (the 1936 proxy provinces) is nearly half sea** (reported): 97,037 km² against a printed
   65,612 km². Northern is 7,762 sq mi against 3,429 printed. Its geometry is an OSM derivative dated 1936. The
   traced 1946 provinces are within −4.0% to +4.8% of the printed areas.
8. **1893 and 1915 traces are several km off** (reported). 13 of 18 `ferguson_towns_1893` points are more than
   3 km from their QID's coordinate (Haputale 10.9, Ratnapura 10.3). `rail_1893_traces` has Peradeniya–Kandy at
   18.7 km (about 6 km in fact) and marks Colombo–Galle as made, though the line reached Galle in 1894 (from
   memory). `rail_1915_traces` puts Maradana about 18 km inland. The 1915 rows are labelled schematic; the
   1893 rows are not.
9. **The rail chronology has no closures** and lacks openings for Galle, Kurunegala, Anuradhapura and Opanake
   (reported). Dates on `rail_1936_osm` are corridor-wide, so the Badulla end shows 1893 / 1858.
10. **The 1834 gazetteer index is short.** After the re-parse of 17 November (439 entries, commit `c2faf88`),
    `gazetteer_1834_index` (393 entries) lacks 46 entries, among them Ceylon, Kandyan Provinces, the three
    Pomparippoo entries, the Putlam district and province, and Quiparawa.

## Sound

No null or invalid geometry; every source, evidence and unit key resolves; no duplicate ids. Census arithmetic
holds: male + female = persons, province sums equal island totals for 1871–1911 and 1946, and the 1921
difference of 751 is trains and the Basses. The island totals match the published figures as I remember them.
The README's counts match the database. `build.py` needs nothing from `/tmp` or the network, and its inputs
are on disk.

## Not checked

Census transcription against the scans; source URLs; `build_project.py` and the QGIS project; the road
findings in `transport_qa.md`; district areas for 1946 (no printed figures in the tables).

## Fixed on 17 November 2026

Rebuilt with `build.py`; the web atlas data was re-exported.

- **1.** Kitulgala, Kalpitiya and Piliyandala use the GeoNames point (`COORDINATE_REVIEW` in
  `match_motor_places.py`; `coordinate_note` on the feature). All 170 amenity places were compared by name with
  GeoNames; no other is more than 4.3 km out.
- **2.** New layer `district_census_1946_join` (districts grown 5 km seaward) and the printed district on each
  town (`urban_census.district_1946`). All 42 towns now fall in a polygon. Avissawella (printed Colombo) and
  Hatton-Dickoya (printed Kandy) still fall in the neighbouring polygon: that is the inland trace, not changed.
- **3.** `gauge_mm_1936` = 762 on the Kelani Valley ways, with a note that OSM attributes are modern. The three
  missing lines are not added: the local OSM data has no abandoned track for them, so they need tracing from
  the 1936 sheet.
- **7.** `province_census` cut to land plus 5 km: 28,355 sq mi against 37,466 before and 25,333 printed.
- **8.** `reference_offset_m` on the seven Ferguson towns that have a measured offset.
- **10.** The gazetteer index holds all 439 entries (189 placed, 250 not).

Not fixed: 4 (census ids that mix territories), 5 (Fa Hien Cave), 9 (rail chronology), the `rail_1893_traces`
labels, and the 1915 schematic traces.

## Housekeeping

This folder is git-ignored, so the scripts, input tables and QA notes have no version history.
