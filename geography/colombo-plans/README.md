# Colombo town plans, twentieth century

**Status, 17 November 2026: not georeferenced yet.** The work was stopped before any control points were
saved. The only product so far is `motor-1936-colombo/colombo-inset-1936.png`, the Colombo inset cut from the
Motor Map scan (check its frame before use). Next: pick 12 or more control points per plan at road junctions and
stations that have not moved, fit an affine transform, warp to EPSG:3857 with alpha, and check against OSM roads.

Four plans to be georeferenced against modern streets. Each plan has its own folder
with `control-points.csv`, `georeference.py`, `notes.md` and the warped GeoTIFF; `export_atlas.py` (`TOWN_PLANS`)
puts the finished ones on the web atlas under "Town plans".

| Folder | Plan | Source image |
|---|---|---|
| `baedeker-1914/` | Baedeker, Colombo 1:50,000, with tramways and mosques (1914) | `sources/Tramways_and_Mosques_in_Colombo_1914.jpg`, Wikimedia Commons, public domain |
| `wickwar-1927/` | City of Colombo, 50 chains to an inch, Survey Department, 4 February 1927 | `sources/city-of-colombo-wickwar-1927.jpg`, supplied by the project owner; where the scan came from is not recorded |
| `french-1930/` | City of Colombo sketch plan from a French colonial handbook (1930) | `sources/Colombo_Map_1930.jpg`, Wikimedia Commons, public domain |
| `motor-1936-colombo/` | Colombo inset of the 1936 Survey Department Motor Map | cut from the David Rumsey scan (office machine: `/mnt/data/jic823/gis/maps/archive_org/dr_survey-department-motor-map-of-ceylon-10791002/10791002.jp2`) |

The Motor Map sheet has about twenty such town insets, Kandy among them; none of the others is done.
Not yet found for Kandy: any twentieth-century plan beyond that inset and the Baedeker 1914 "Kandy and environs"
(Wikimedia Commons). Skeen's *Guide to Kandy* (1903, archive.org `cu31924088807106`) and Cave's *Book of Ceylon*
(1908, archive.org `bookofceylonbein00cave`) have town maps and are not downloaded.
