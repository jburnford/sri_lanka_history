# Ceylon Historical Atlas

Explore the historical GIS on [GitHub Pages](https://jburnford.github.io/sri_lanka_history/). The site includes vector layers, historical map images, census records and related source descriptions.

Open **Explore map** to turn layers on and off, look up a named place or route, or click a feature. The inspector links historical evidence to its locator and shows separate dates for the feature and publication where available. **Browse records** provides search, year filters, record details and CSV export. **Sources** links to the source catalogue and the transport reviews.

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

OpenStreetMap-derived datasets are available under the [Open Database License](https://opendatacommons.org/licenses/odbl/1-0/). © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright). Source and attribution fields are included in the web export. Leaflet is distributed under its [BSD license](docs/vendor/LICENSE).
