# Plan for the historical GIS, written 17 November 2026

Where the work stands, what comes next, and where every input is. Written so the work can continue on another
machine from a clone of this repository.

## State on 17 November 2026

- `ceylon-history.gpkg` has 34 layers. `build.py` rebuilds it; `build_project.py` writes `ceylon-history.qgz`;
  `../../export_atlas.py` writes the web atlas into `docs/data/`.
- Reviewed and partly fixed today: see `claude_review_2026-11-17.md` (the list of what is not fixed is at its end).
- New today: the Chief Headmen's divisions of 1934 (`headmen_divisions_1934`, 109 polygons; method and doubts in
  `headmen_divisions_1934_method.md`), relief from SRTM, map sheets on the atlas as full-resolution tiles.

## Setting up on another machine

```bash
git clone git@github.com:jburnford/sri_lanka_history.git
cd sri_lanka_history/geography
cp ferguson-1893/ferguson-1893.jpeg.tif ferguson-1893/ferguson-1893.tif   # the QGIS project looks for this name
bash historical-gis/fetch_elevation.sh                                    # SRTM, about 500 MB; not yet run anywhere
```

Use the system Python that has GDAL (`/usr/bin/python3` on the office machine; `python3 -c "from osgeo import ogr"`
must work). `build_project.py` needs PyQGIS: `QT_QPA_PLATFORM=offscreen /usr/bin/python3 build_project.py`.
If the QGIS project shows the elevation layers as missing, run `build_project.py` again after fetching the elevation.

## Where each input is

| Input | In the repository | Otherwise |
|---|---|---|
| GeoPackage, scripts, input tables, QA notes | `geography/historical-gis/` | |
| 1936 Motor Map, georeferenced | `geography/motor-map-1936/ceylon-motor-map-1936.tif` (40 MB) | |
| Ferguson 1893, georeferenced | `geography/ferguson-1893/ferguson-1893.jpeg.tif` (19 MB, JPEG quality 90) | lossless original, 175 MB: office machine, same folder, `ferguson-1893.tif` |
| Malaria report supplement, 1934-35 (maps) | `geography/sources/malaria-report-1934-35-supplement_b32176910_0002.pdf` | https://archive.org/details/b32176910_0002 |
| Census of Ceylon 1911 | `geography/sources/census-1911_b28069365.pdf` | https://archive.org/details/b28069365 |
| Inventory of the 99 downloaded maps | `geography/sources/MAPS_INVENTORY.tsv` (the `path` column is on the office machine) | |
| Blue Book tables, 1834 Gazetteer | `spine/bluebook/`, `spine/gazetteer/` | |
| SRTM 30 m elevation | no; `fetch_elevation.sh` rebuilds it | office: `/mnt/data/jic823/ceylon_hgis_elevation/srtm_30m/` |
| OSM reference for Sri Lanka, 12 Nov 2026 (353 MB) | no, too large | office: `~/Documents/ceylon/kg/spatial/osm-sri-lanka-reference-2026-11-12.gpkg` (built by `kg/spatial/build_osm_reference.py`) |
| The downloaded maps themselves (1.3 GB) | no | office: `/mnt/data/jic823/gis/maps/` |
| GeoNames Sri Lanka extract | no | office: `/mnt/data/jic823/gis/geonames/LK.txt`; or https://download.geonames.org/export/dump/LK.zip |
| Arrowsmith 1805 scans (two, 70 MB each) | no | office: `~/Documents/ceylon/geography/arrowsmith-1805/` |
| Scratch arrays and page images for the divisions tracing | no | office: `~/Documents/ceylon/geography/historical-gis/headmen_1934_work/`; page images are `pdftoppm -r 400 -png -f N -l N` of the malaria PDF |
| VaeSSA 0.5 m elevation (16 GB) | no | office: `/mnt/data/jic823/ceylon_hgis_elevation/vaessa_0_5m/` |

The office machine is `hist-clifford-pgx.usask.ca`. For example:

```bash
rsync -avP hist-clifford-pgx.usask.ca:Documents/ceylon/kg/spatial/osm-sri-lanka-reference-2026-11-12.gpkg kg/spatial/
```

## Next work, in order

1. **Death rates by division, 1934-35.** Maps 17, 18 and 19 of the malaria supplement (PDF pp. 39, 43, 47; key on
   p. 38) shade each division by death rate. Read the class of each of the 112 divisions by eye from 400 dpi
   renders, enter them in a table keyed on `key_number`, and add them to `build.py` as observations joined to
   `headmen_divisions_1934`. Machine reading of the shading failed; the raw measurements are in
   `headmen_1934_work/shading_features.tsv`. While there, read the numbers on Maps 18 and 19 to confirm the
   identities taken from Map 17, above all the Batticaloa cells (61, 62+65, 66, 67) and Matara (35, 36, 39, 40),
   and check whether Badulla town belongs in Wiyaluwa (97) or Yatikinda.
2. **River basins.** Look at the river-basin maps in the same supplement; if usable, trace them as a 1934 picture
   of the rivers.
3. **Three missing 1936 railway lines.** Avissawella-Yatiyantota, Avissawella-Opanake, Nanu Oya-Ragalla. Trace
   from the Motor Map scan (OSM has no track for them) and add to `rail_1936_osm` with a trace-based
   `geometry_method`. Also the Kelani bridge span and the last 568 m into Batticaloa (`railway_qa.md`).
4. **Rail chronology.** Openings for Galle, Kurunegala, Anuradhapura and Opanake; closures. Label
   `rail_1893_traces` as schematic like the 1915 rows.
5. **Water as of 1936.** Needs the OSM reference (3,155 named water areas, no dates). For each reservoir, record
   whether it is drawn on the 1936 Motor Map; those absent are candidates for later works (hydroelectric and
   irrigation schemes). The owner asked for this because the river systems changed in the twentieth century.
6. **Census ids that mix territories.** Puttalam/Chilaw (1871, 1881), Vavuniya/Mullaitivu (1881), Negombo 1901,
   Colombo without the Municipality (1891, 1901). Split the ids or mark the extent on each observation before any
   district time series is used. Then join Blue Book series reported by district or province to the polygons.
7. **1834 Gazetteer.** 250 of 439 entries have no location. Place those that give a distance and bearing from a
   located place, marked approximate. Check Mahagam and Kalani (review item 6). Three headwords look misread
   (Resale, Wedamaha Nuwera, Budumalwal): a fresh OCR of the 1834 scan would settle them.
8. **1911 census plates.** Not yet checked: page through the PDF for district or division maps; if present, an
   earlier set of boundaries to compare with 1934 and 1946.
9. **More maps.** From the inventory: Gill 1933, Stanford 1904, Cave 1908, the Skeen guides. The one-inch survey
   sheets are not downloaded; they would test the 1934 division lines against a proper survey.
10. **Smaller items.** Fa Hien Cave point (review item 5); small islands off Jaffna and Kalpitiya missing from the
    divisions layer; Avissawella and Hatton-Dickoya fall in the neighbouring district polygon.

## Town plans (added late on 17 November)

Four twentieth-century plans of Colombo are collected in `geography/colombo-plans/` (see its README) but not yet
georeferenced. `export_atlas.py` already knows them (`TOWN_PLANS`) and will put each on the atlas once its GeoTIFF
exists. Kandy still needs maps: the Motor Map inset, Baedeker 1914, Skeen 1903 and Cave 1908 are the leads.

## Working rules

- The roads have been reviewed by the owner and use OSM geometry on purpose: leave them.
- Another Claude session owns `spine/bluebook/` and the grounding scripts. Commit only your own paths.
- After changing the database: run `build.py`, `build_project.py`, then `export_atlas.py`, and look at the atlas
  (`python3 -m http.server --directory docs`).
- `SOURCES.md` at the repository root says what may be published.
