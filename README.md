# Sri Lanka / Ceylon history: knowledge graph and historical GIS

A research project that builds interoperable historical data for colonial Ceylon on top of two existing
foundations: the Colonial Office List graph and the Empire Evolution graph, joined through Wikidata identifiers.

| Folder | What it is |
|---|---|
| `docs/`, `export_atlas.py` | The online historical atlas, served by GitHub Pages. See "Ceylon Historical Atlas" below. |
| `spine/` | The entity layer: places, taxa, commodities, organisations and people named in the *Tropical Agriculturist* and the Ceylon Blue Books, each tied to a shared identifier by a recorded, reversible decision. Start with `spine/README.md` and `spine/STATUS.md`. |

`SOURCES.md` says where each body of material came from and what may be published.

## Ceylon Historical Atlas

Explore the historical GIS on [GitHub Pages](https://jburnford.github.io/sri_lanka_history/). The site includes vector layers, historical map images, census records and related source descriptions.

Open **Explore map** to turn layers on and off, look up a named place or route, or click a feature. The inspector links historical evidence to its locator and shows separate dates for the feature and publication where available. **Browse records** provides search, year filters, record details and CSV export. **Sources** links to the source catalogue and the transport reviews.

Under **Places**, **1834 Gazetteer places** uses modern reference points for 189 entries in Casie Chitty’s gazetteer. **Browse Gazetteer index** opens all 393 indexed entries, including places still awaiting a location and entries describing areas. Each mapped entry gives the historical page, the source of its coordinates, and a Wikidata ID where the identity was established. [Grounding decisions](spine/analysis/hgis_chitty_1834_grounded.tsv), [gazetteer scan](https://archive.org/details/in.ernet.dli.2015.94788).

**Ferguson road traces, 1893** covers 11 selected road sections. The traces follow the printed road symbols and inherit positional uncertainty from the map, especially along folds. Use **Show Ferguson’s map** to inspect the linework against the sheet. The trace register gives the source panels and pixel coordinates for the nine added sections on the 1500-pixel-high reference image. [Trace register](docs/notes/ferguson_road_traces_1893.tsv), [Ferguson’s 1893 map](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~338023~90105863).

GitHub Pages serves `docs/` from the main branch. To preview locally from this directory:

```sh
python3 -m http.server --directory docs
```

The browser reads GeoJSON and JSON exports in `docs/data/`. To refresh them, run the exporter with the GDAL Python bindings and the path to `ceylon-history.gpkg`. The georeferenced images are read from the adjacent `motor-map-1936` and `ferguson-1893` directories when present.

```sh
/usr/bin/python3 export_atlas.py /path/to/geography/historical-gis/ceylon-history.gpkg
```

The web export is a snapshot. Its geometry is in WGS84 and its image overlays are downsampled. The working historical GIS includes additional material such as the local elevation raster. The transport review notes include known gaps, and early schematic lines and modern alignment candidates are labelled in the atlas.

Map credit: David Rumsey Map Collection, David Rumsey Map Center, Stanford University Libraries. The atlas displays georeferenced, resized adaptations of [Ferguson’s 1893 map](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~338023~90105863) and the [1936 Survey Department map](https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~332276~90100738). See the [collection’s image permissions](https://www.davidrumsey.com/about/copyright-and-permissions).

OpenStreetMap-derived datasets are available under the Open Database License. © OpenStreetMap contributors. [License](https://opendatacommons.org/licenses/odbl/1-0/), [OpenStreetMap copyright](https://www.openstreetmap.org/copyright). Gazetteer coordinates drawn from GeoNames are credited individually in the web export. [GeoNames data and license](https://www.geonames.org/export/). Leaflet is distributed under its BSD license. [Leaflet license](docs/vendor/LICENSE).
