#!/usr/bin/env python3
"""Export an atlas snapshot from the Ceylon historical GIS GeoPackage."""
import argparse
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

from osgeo import gdal, ogr, osr

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "docs" / "data"
LAYERS = [
    ("province_census_1946", "Provinces, 1946", "Boundaries", "Approximate reconstruction used for the census map.", "#8c644c", True),
    ("district_census_1946", "Districts, 1946", "Boundaries", "Approximate district boundaries. Compare census source dates in the selected unit.", "#9b816a", False),
    ("headmen_divisions_1934", "Chief Headmen’s divisions, 1934", "Boundaries", "Traced from the small maps in the 1934–35 malaria report. Lines are good to a few kilometres; each division says how its identity was read.", "#7a5a94", False),
    ("province_census", "Province reference", "Boundaries", "Generalized modern OSM boundaries used as an approximate reference.", "#817589", False),
    ("urban_census", "Census towns", "Places", "Modern coordinates for census settlements and municipality anchors.", "#8f5f31", True),
    ("historical_wikidata_places", "Historic landmarks", "Places", "Reviewed landmarks, with historical evidence and modern coordinates documented separately.", "#a36a25", True),
    ("gazetteer_1834_points", "1834 Gazetteer places", "Places", "Modern reference points for grounded entries in Casie Chitty’s Gazetteer.", "#267c71", False),
    ("motor_amenity_places_1936", "Motor map amenities, 1936", "Places", "Matched places from the map’s amenity lists. Points locate places, not individual establishments.", "#76609a", False),
    ("ferguson_towns_1893", "Ferguson towns, 1893", "Places", "Towns plotted on the 1893 map.", "#766c49", False),
    ("road_ferry_chronology", "Roads & ferries, 1936", "Transport", "Traced corridors. Earlier evidence is linked where available.", "#ae593b", True),
    ("rail_1936_osm", "Railways, 1936", "Transport", "Working reconstruction, mostly with modern OSM geometry. See railway review for known gaps.", "#285968", True),
    ("reviewed_historical_bridges", "Historical bridges", "Transport", "Individually reviewed bridge traces.", "#ad5037", False),
    ("road_1936_osm_candidates", "Road alignment candidates", "Transport", "Modern OSM candidates for 1936 corridors. Review the alignment before use.", "#a77758", False),
    ("road_1915_traces", "Roads, 1915", "Transport", "Approximate lines taken from a schematic railway map.", "#a36a48", False),
    ("rail_1915_traces", "Railways, 1915", "Transport", "Approximate schematic rail traces.", "#4a738e", False),
    ("rail_1915_osm_candidates", "Rail alignment candidate, 1915", "Transport", "Modern geometry compared with historical evidence.", "#477785", False),
    ("road_1893_traces", "Ferguson road traces, 1893", "Transport", "Selected corridors traced from the printed road symbols. The map sheet shows additional roads.", "#962249", False),
    ("rail_1893_traces", "Railways, 1893", "Transport", "Mapped railway alignments and statuses from Ferguson’s map.", "#51758c", False),
    ("rail_1915_controls", "Rail map controls, 1915", "Transport", "Control points and residuals for registration of the schematic map.", "#635687", False),
]
TABLES = [
    ("census_observations", "Census observations", ["source_name","year","metric","value","unit","status","source_id"]),
    ("census_units", "Census units", ["name","unit_kind","qid","represented_date"]),
    ("census_reconciliation", "Census verification", ["total_row","year","metric","printed_total","component_sum","difference","status"]),
    ("transport_evidence", "Transport evidence", ["name","mode","event","represented_date","date_relation","source_id"]),
    ("transport_evidence_links", "Corridor references", ["name","corridor_id","event","represented_date","link_scope"]),
    ("road_inventory_1928", "Road inventory, 1928", ["name","province_as_printed","length_miles","traffic_class","represented_date"]),
    ("road_works_1928", "Road works, 1928", ["name","work_kind","start_date","expenditure_rupees","status"]),
    ("road_rail_crossings_1925", "Road–rail crossings, 1925", ["description","rail_section","miles","chains","road_class"]),
    ("road_alignment_review", "Road alignment review", ["historical_name","status","finding","uncertainty","reviewed_on"]),
    ("gazetteer_1834_attestations", "Gazetteer attestations, 1834", ["name_as_printed","place_match","claim_type","claim","represented_date"]),
    ("gazetteer_1834_index", "1834 Gazetteer entry index", ["name_as_printed","place_match","grounding_status","qid","source_locator"]),
    ("motor_amenity_listings_1936", "Motor map amenity listings", ["place_as_printed","facility_kind","province_as_printed","note"]),
    ("motor_amenity_observations_1936", "Motor map amenity observations", ["feature_id","metric","value","represented_date"]),
    ("historical_wikidata_places", "Historic landmarks", ["name","category","represented_date","significance","qid"]),
    ("source_catalogue", "Source catalogue", ["title","published_date","kind","source_id"]),
]
OMIT = {"fid", "geom", "local_reference", "tags_json", "osm_nodes_json", "source_pixels_json", "source_pixels"}
RASTERS = [
    ("motor1936", "Motor Map, 1936", "motor-map-1936/ceylon-motor-map-1936.tif", "Georeferenced image of the 1936 Survey Department Motor Map.", "https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~332276~90100738", 1900),
    ("ferguson1893", "Ferguson’s map, 1893", "ferguson-1893/ferguson-1893.tif", "Georeferenced image of Ferguson’s 1893 map of Ceylon.", "https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~338023~90105863", 1900),
]


def write(filename, value):
    (DATA / filename).write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str))


def export_raster(identifier, source, maximum):
    with tempfile.TemporaryDirectory() as work:
        tif = str(Path(work) / "warped.tif")
        gdal.Warp(tif, str(source), dstSRS="EPSG:3857", dstAlpha=True, resampleAlg="bilinear")
        raster = gdal.Open(tif)
        geom = raster.GetGeoTransform()
        crs = osr.SpatialReference()
        crs.ImportFromEPSG(3857)
        wgs = osr.SpatialReference()
        wgs.ImportFromEPSG(4326)
        wgs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        transform = osr.CoordinateTransformation(crs, wgs)
        left, top, _ = transform.TransformPoint(geom[0], geom[3])
        right, bottom, _ = transform.TransformPoint(geom[0] + raster.RasterXSize * geom[1],
                                                    geom[3] + raster.RasterYSize * geom[5])
        scale = maximum / max(raster.RasterXSize, raster.RasterYSize)
        destination = str(DATA / (identifier + ".webp"))
        gdal.Translate(destination, raster, format="WEBP", creationOptions=["QUALITY=88"], width=round(raster.RasterXSize * scale),
                       height=round(raster.RasterYSize * scale), resampleAlg="average")
    return [[bottom, left], [top, right]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gpkg", nargs="?", type=Path,
                        default=ROOT / "geography/historical-gis/ceylon-history.gpkg")
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    gdal.UseExceptions()
    dataset = ogr.Open(str(args.gpkg))
    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)
    target.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    with sqlite3.connect(f"{args.gpkg.resolve().as_uri()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        available = {row[0] for row in conn.execute("SELECT table_name FROM gpkg_contents")}

        def table(name):
            return [{k: v for k, v in dict(row).items() if k not in OMIT and v is not None}
                    for row in conn.execute(f'SELECT * FROM "{name}"')]

        layers = []
        for identifier, title, group, description, color, visible in LAYERS:
            if identifier == "gazetteer_1834_points" and identifier not in available:
                continue
            collection = []
            points = False
            layer = dataset.GetLayerByName(identifier)
            source = layer.GetSpatialRef().Clone()
            source.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
            transform = osr.CoordinateTransformation(source, target)
            for f in layer:
                geometry = f.GetGeometryRef()
                if geometry is None or geometry.IsEmpty():
                    continue
                geometry = geometry.Clone()
                geometry.Transform(transform)
                west, east, south, north = geometry.GetEnvelope()
                if not (78 < west <= east < 84 and 4 < south <= north < 12):
                    raise ValueError(f"{identifier} contains out-of-range coordinates {geometry.GetEnvelope()}")
                points = geometry.GetGeometryName() == "POINT"
                props = {k: v for k, v in f.items().items() if k not in OMIT and v is not None}
                geom = json.loads(geometry.ExportToJson(["COORDINATE_PRECISION=5"]))
                collection.append({"type": "Feature", "properties": props, "geometry": geom})
            write(identifier + ".json", {"type": "FeatureCollection", "features": collection})
            layers.append(dict(id=identifier, title=title, group=group, description=description,
                               color=color, visible=visible, points=points, count=len(collection)))

        tables = []
        for identifier, title, fields in TABLES:
            if identifier == "gazetteer_1834_index" and identifier not in available:
                continue
            rows = table(identifier)
            write(identifier + ".records.json", rows)
            tables.append(dict(id=identifier, title=title, fields=fields, count=len(rows)))

    rasters = []
    for identifier, title, relative, description, url, maximum in RASTERS:
        source = args.gpkg.parent.parent / relative
        if source.exists():
            bounds = export_raster(identifier, source, maximum)
            rasters.append(dict(id=identifier, title=title, group="Map sheets", description=description,
                                url=url, bounds=bounds, visible=False))

    write("atlas.json", dict(layers=layers, tables=tables, rasters=rasters,
                            revision=hashlib.sha256(args.gpkg.read_bytes()).hexdigest()[:12]))
    print(f"Exported {len(layers)} vector layers, {len(tables)} record tables and {len(rasters)} map sheets.")


if __name__ == "__main__":
    main()
