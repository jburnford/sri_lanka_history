#!/usr/bin/env python3
"""Create the station-bounded OSM comparison for the 1915 Ragama–Chilaw corridor."""
import csv
import json
from collections import defaultdict, deque
from pathlib import Path

from osgeo import ogr, osr


HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parents[1] / 'kg/spatial/osm-sri-lanka-reference-2026-11-12.gpkg'
REVIEW = HERE.parent / 'motor-map-1936/transport-1936.gpkg'
OUTPUT = HERE / 'rail_1915_osm.geojson'
HISTORICAL_SEGMENT = '1915-rail:chilaw'
STATIONS = (
    ('Ragama', 5769656115, 12630531706),
    ('Chilaw', 1137448708, 12630567654),
)


def read_rows(stem):
    with (HERE / f'{stem}.tsv').open(encoding='utf-8', newline='') as file:
        return list(csv.DictReader(file, delimiter='\t'))


def station_anchor(reference, snapshot, station):
    name, label_id, stop_id = station
    points = reference.GetLayerByName('transport_points')
    points.SetAttributeFilter(f'osm_id IN ({label_id}, {stop_id}) AND osm_type = \'node\'')
    anchors = {
        feature['osm_id']: (feature['name'], feature['railway'], feature['snapshot'],
                            feature.GetGeometryRef().GetPoint_2D())
        for feature in points
    }
    if (anchors[label_id][:3] != (name, 'station', snapshot)
            or anchors[stop_id][:3] != (name, 'stop', snapshot)):
        raise ValueError(f'OSM station or stop record changed at {name}')
    return anchors[stop_id][3]


def rail_network(reference, review, snapshot):
    vetted = review.GetLayerByName('rails_1936_osm')
    vetted.SetAttributeFilter("historical_corridor = 'Puttalam Line'")
    way_ids = sorted({feature['osm_id'] for feature in vetted})
    if not way_ids:
        raise ValueError('No reviewed Puttalam Line ways')
    rail = reference.GetLayerByName('rail')
    if rail.GetSpatialRef().GetAuthorityCode(None) != '4326':
        raise ValueError('Expected WGS84 coordinates in OSM reference')
    rail.SetAttributeFilter(f"osm_id IN ({','.join(map(str, way_ids))}) AND osm_type = 'way'")

    graph = defaultdict(dict)
    coordinates = {}
    versions = {}
    for feature in rail:
        way = feature['osm_id']
        if (feature['snapshot'] != snapshot or feature['railway'] != 'rail'
                or feature['service'] or feature['gauge'] != '1676'):
            raise ValueError(f'Unexpected track class or snapshot for OSM way {way}')
        nodes = json.loads(feature['osm_nodes_json'])
        points = feature.GetGeometryRef().GetPoints()
        if len(points) != len(nodes):
            raise ValueError(f'Geometry and OSM node count differ for way {way}')
        versions[way] = feature['osm_version']
        for node, coordinate in zip(nodes, points, strict=True):
            point = tuple(coordinate[:2])
            if coordinates.setdefault(node, point) != point:
                raise ValueError(f'Shared OSM node {node} has differing coordinates')
        for start, end in zip(nodes, nodes[1:]):
            if start == end or end in graph[start]:
                raise ValueError(f'Duplicate OSM rail edge {start}–{end}')
            graph[start][end] = graph[end][start] = way
    if set(versions) != set(way_ids):
        raise ValueError('OSM reference lacks a reviewed Puttalam Line way')
    return graph, coordinates, versions


def find_path(graph, start, end, skip=None):
    pending = deque([start])
    previous = {start: None}
    while pending and end not in previous:
        node = pending.popleft()
        for neighbor in graph[node]:
            if neighbor not in previous and (node, neighbor) != skip and (neighbor, node) != skip:
                previous[neighbor] = node
                pending.append(neighbor)
    if end not in previous:
        return []
    path = [end]
    while path[-1] != start:
        path.append(previous[path[-1]])
    return path[::-1]


def main():
    ogr.UseExceptions()
    reference = ogr.Open(str(REFERENCE))
    review = ogr.Open(str(REVIEW))
    snapshot = reference.GetMetadataItem('OSM_SNAPSHOT')
    if not snapshot:
        raise ValueError('Missing reference snapshot')
    graph, coordinates, versions = rail_network(reference, review, snapshot)
    for station in STATIONS:
        if coordinates.get(station[2]) != station_anchor(reference, snapshot, station):
            raise ValueError(f'OSM stop position is not an exact track node at {station[0]}')

    start, end = (station[2] for station in STATIONS)
    path = find_path(graph, start, end)
    edges = list(zip(path, path[1:]))
    if not edges:
        raise ValueError('No connected Ragama–Chilaw path in the reviewed rail ways')
    if any(find_path(graph, start, end, skip=edge) for edge in edges):
        raise ValueError('More than one Ragama–Chilaw path in the reviewed rail ways')
    ways = list(dict.fromkeys(graph[a][b] for a, b in edges))
    track = [coordinates[node] for node in path]
    geometry = ogr.Geometry(ogr.wkbLineString)
    for point in track:
        geometry.AddPoint_2D(*point)
    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)
    wgs84.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    utm = osr.SpatialReference()
    utm.ImportFromEPSG(32644)
    geometry.Transform(osr.CoordinateTransformation(wgs84, utm))

    source_urls = {row['source_id']: row['url'] for row in read_rows('sources')}
    source_urls.update({row['source_id']: row['url'] for row in read_rows('railway_later_sources')})
    historical = next(row for row in read_rows('rail_1915_traces')
                      if row['segment_id'] == HISTORICAL_SEGMENT)
    later = next(row for row in read_rows('transport_records') if row['evidence_id'] == 's-puttalam')
    opening = next(row for row in read_rows('railway_later_records') if row['evidence_id'] == 'ag-chilaw-all')
    feature_id = 'rail-comparison:1915:ragama-chilaw'
    properties = {
        'feature_id': feature_id,
        'name': 'Ragama–Chilaw via Negombo',
        'geometry_role': 'Present-day alignment candidate for comparison with the 1915 map',
        'review_status': 'Connected on reviewed OSM rail ways',
        'historical_segment_id': historical['segment_id'],
        'corridor_id': historical['corridor_id'],
        'historical_map_date': '1915-03',
        'historical_map_url': source_urls['rumsey-13440.000'],
        'chilaw_all_traffic_opening_date': opening['date'],
        'chilaw_all_traffic_opening_evidence_id': opening['evidence_id'],
        'chilaw_all_traffic_opening_locator': opening['locator'],
        'chilaw_all_traffic_opening_url': f"{source_urls[opening['source_id']]}#page=36",
        'later_extension_evidence_id': later['evidence_id'],
        'later_extension_reported_year': int(later['date']),
        'later_extension_source_url': source_urls[later['source_id']],
        'osm_snapshot': snapshot,
        'osm_extract_url': reference.GetMetadataItem('SOURCE'),
        'osm_license': 'ODbL 1.0',
        'osm_attribution': '© OpenStreetMap contributors',
        'way_selection': 'Puttalam Line way IDs from the local 1936 rail review',
        'way_selection_source': '../motor-map-1936/transport-1936.gpkg:rails_1936_osm',
        'start_station_node': STATIONS[0][1],
        'end_station_node': STATIONS[1][1],
        'start_track_node': start,
        'end_track_node': end,
        'osm_way_ids': ways,
        'osm_way_versions': [versions[way] for way in ways],
        'osm_track_node_count': len(path),
        'length_km': round(geometry.Length() / 1000, 3),
        'evidence_note': 'The March 1915 map depicts the corridor to Chilaw before its documented '
                         'openings in 1916. The OSM path represents current track geometry '
                         'between modern stops.',
    }
    result = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'id': feature_id, 'properties': properties,
         'geometry': {'type': 'LineString', 'coordinates': track}}
    ]}
    temporary = OUTPUT.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n',
                         encoding='utf-8')
    temporary.replace(OUTPUT)
    print(f"{len(ways)} OSM ways, {len(path)} track nodes, {properties['length_km']:.3f} km")


if __name__ == '__main__':
    main()
