#!/usr/bin/env python3
"""Build the historical GIS GeoPackage from the transcriptions and local map layers."""
import csv
from contextlib import closing
from datetime import date
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import re
import sqlite3
from tempfile import TemporaryDirectory

import numpy as np
from osgeo import gdal, ogr, osr
from audit_census import COLS as AUDIT_COLUMNS, checks as census_checks

HERE = Path(__file__).resolve().parent
MOTOR = HERE.parent / 'motor-map-1936'
FERGUSON = HERE.parent / 'ferguson-1893' / 'ferguson-1893.gpkg'
SPINE_ANALYSIS = HERE.parent.parent / 'spine' / 'analysis'
S, I, R = ogr.OFTString, ogr.OFTInteger, ogr.OFTReal

gdal.UseExceptions()
ogr.UseExceptions()
gdal.SetConfigOption('OGR_SQLITE_JOURNAL', 'DELETE')
WGS84 = osr.SpatialReference()
WGS84.ImportFromEPSG(4326)
WGS84.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)


def read(name):
    with (HERE / f'{name}.tsv').open(encoding='utf-8', newline='') as file:
        return list(csv.DictReader(file, delimiter='\t'))


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def make_layer(db, name, fields, geometry=ogr.wkbNone, crs=None):
    layer = db.CreateLayer(name, srs=crs, geom_type=geometry)
    for field, typ in fields.items():
        layer.CreateField(ogr.FieldDefn(field, typ))
    return layer


def insert(layer, data, geometry=None):
    record = ogr.Feature(layer.GetLayerDefn())
    for field, value in data.items():
        if value is not None and value != '':
            record.SetField(field, json.dumps(value) if isinstance(value, list) else value)
    if geometry is not None:
        record.SetGeometry(geometry)
    layer.CreateFeature(record)


def copy_layer(db, source, input_name, output_name, extra_fields, enrich):
    original = source.GetLayerByName(input_name)
    list_types = (ogr.OFTIntegerList, ogr.OFTInteger64List, ogr.OFTRealList, ogr.OFTStringList)
    fields = {f.GetName(): S if f.GetType() in list_types else f.GetType() for f in original.schema}
    fields.update(extra_fields)
    output = make_layer(db, output_name, fields, original.GetGeomType(), original.GetSpatialRef())
    names = [f.GetName() for f in original.schema]
    for feature in original:
        data = {name: feature[name] for name in names}
        data.update(enrich(data))
        insert(output, data, feature.GetGeometryRef())


def point(lon, lat):
    geometry = ogr.Geometry(ogr.wkbPoint)
    geometry.AddPoint_2D(float(lon), float(lat))
    return geometry


def add_historical_places(db, sources):
    layer = make_layer(db, 'historical_wikidata_places', {
        'feature_id': S, 'qid': S, 'name': S, 'category': S, 'significance': S,
        'date_basis': S, 'point_scope': S, 'geometry_note': S,
        'wikidata_label_en': S, 'wikidata_label_si': S, 'wikidata_label_ta': S,
        'wikidata_aliases_en': S, 'wikidata_description': S, 'instance_of_qids': S,
        'admin_parent_qids': S, 'gazetteer_snapshot_date': S,
        'qid_source_id': S, 'wikidata_url': S, **PROVENANCE_FIELDS,
    }, ogr.wkbPoint, WGS84)
    for row in read('historical_places'):
        qid = row['qid']
        assert row['feature_id'].startswith('historical-place:') and re.fullmatch(r'Q[1-9][0-9]*', qid)
        assert 5.8 < float(row['lat']) < 10.1 and 79.45 < float(row['lon']) < 82.15, qid
        url = f'https://www.wikidata.org/wiki/{qid}'
        provenance = geo_provenance(
            sources, 'wikidata-sri-lanka', f'{qid}, coordinate location (P625), local snapshot',
            row['source_id'], row['source_locator'], row['represented_date'])
        provenance['geometry_source_url'] = url + '#P625'
        insert(layer, {
            **{k: row[k] for k in (
                'feature_id', 'qid', 'name', 'category', 'significance', 'date_basis',
                'point_scope', 'geometry_note', 'wikidata_label_en', 'wikidata_label_si',
                'wikidata_label_ta', 'wikidata_aliases_en', 'wikidata_description',
                'instance_of_qids', 'admin_parent_qids',
            )},
            'gazetteer_snapshot_date': row['snapshot_date'],
            'qid_source_id': 'wikidata-sri-lanka', 'wikidata_url': url,
            **provenance,
        }, point(row['lon'], row['lat']))

    source_id = 'gazetteer-chitty-1834'
    attestations = make_layer(db, 'gazetteer_1834_attestations', {
        'attestation_id': S, 'name_as_printed': S, 'place_match': S, 'qid': S, 'qid_scope': S,
        'claim_type': S, 'represented_date': S, 'value': S, 'unit': S, 'locator': S, 'claim': S,
        'geometry_status': S, 'source_id': S, 'published_date': S, 'source_url': S,
    })
    for row in read('gazetteer_1834_attestations'):
        insert(attestations, {**row, 'source_id': source_id, 'published_date': sources[source_id]['date'],
                              'source_url': page_url(sources[source_id]['url'], row['locator'])})


def add_chitty_index(db):
    def rows(name):
        with (SPINE_ANALYSIS / f'hgis_chitty_1834_{name}.tsv').open(newline='', encoding='utf-8') as file:
            return list(csv.DictReader(file, delimiter='\t'))

    point_rows = rows('grounded')
    index_rows = rows('index')
    points = make_layer(db, 'gazetteer_1834_points', {
        field: S for field in point_rows[0] if field not in ('longitude', 'latitude')
    } | {'source_id': S, 'represented_date': S, 'published_date': S}, ogr.wkbPoint, WGS84)
    index = make_layer(db, 'gazetteer_1834_index', {
        field: S for field in index_rows[0]
    } | {'source_id': S, 'represented_date': S, 'published_date': S})
    source = {'source_id': 'gazetteer-chitty-1834', 'represented_date': '1834', 'published_date': '1834'}
    by_entry = {row['entry_id']: row['feature_id'] for row in point_rows}
    assert len(by_entry) == len(point_rows)
    for row in point_rows:
        lon, lat = float(row['longitude']), float(row['latitude'])
        assert 79.55 < lon < 82 and 5.9 < lat < 10
        fields = {k: v for k, v in row.items() if k not in ('longitude', 'latitude')}
        insert(points, {**fields, **source}, point(lon, lat))
    for row in index_rows:
        assert row['feature_id'] == by_entry.get(row['entry_id'], '')
        insert(index, {**row, **source})


def unit_id(kind, name):
    if kind == 'country':
        return 'country:ceylon'
    if kind in ('municipality', 'urban council', 'local board'):
        key = name.removesuffix(' Town').removesuffix(' Municipality').removesuffix(' Local Board')
        return f'urban:{slug(key)}'
    return f'{kind}:{slug(name.replace("Kegalle", "Kegalla"))}'


def add_census(db, sources):
    census_dates = {int(r['year']): r for r in read('census_dates')}
    unit_fields = {'feature_id': S, 'unit_kind': S, 'name': S, **IDENTITY_FIELDS}
    town_locators = {r['unit_name']: r['locator'] for r in read('census_1946_final')}
    registry = make_layer(db, 'census_units', {
        **unit_fields, 'represented_date': S, 'published_date': S,
        'source_id': S, 'locator': S, 'source_url': S,
    })
    unit_lookup = {}
    for row in read('census_units'):
        unit_lookup[row['feature_id']] = row
        source_id = 'census-1946-final'
        locator = {
            'country': 'Table 3, p. 57, PDF p. 87',
            'province': 'Table 10, p. 72, PDF p. 104',
            'district': 'Table 97, p. 147, PDF p. 195',
            'urban': town_locators.get(row['name']),
        }.get(row['unit_kind'])
        if row['feature_id'] == 'district:puttalam-and-chilaw':
            source_id, locator = 'gazette-9533', 'p. 489, PDF p. 1'
        represented = '1946-03-19'
        if row['feature_id'] in EARLIER_CENSUS_UNITS:
            source_id, locator = 'census-1891', EARLIER_CENSUS_UNITS[row['feature_id']]
            represented = '1891-02-26'
        assert locator, row['feature_id']
        insert(registry, {
            **row, 'represented_date': represented, 'published_date': sources[source_id]['date'],
            'source_id': source_id, 'locator': locator, 'source_url': page_url(sources[source_id]['url'], locator),
        })

    observations = make_layer(db, 'census_observations', {
        'observation_id': S, 'feature_id': S, 'source_unit_kind': S, 'source_name': S,
        'source_parent': S, 'represented_date': S, 'year': I, 'metric': S, 'value': R, 'unit': S,
        'published_value': S, 'published_unit': S, 'count_resolution_persons': I, 'status': S,
        'source_id': S, 'published_date': S, 'locator': S, 'source_url': S,
        'scope': S, 'transcription_note': S,
    })
    verification = make_layer(db, 'census_reconciliation', {
        field: I if field == 'year' else S for field in AUDIT_COLUMNS
    })
    for check in census_checks():
        insert(verification, check)

    def observe(source_id, row, year, metric, raw_value, locator, scope, status, note=''):
        if raw_value in (None, '', '..'):
            return
        fid = row.get('feature_id') or unit_id(row['kind'], row.get('unit_name') or row['name'])
        assert fid in unit_lookup, fid
        unit = METRIC_UNITS.get(metric, 'persons')
        published_unit = unit
        resolution = None
        numeric_text = raw_value
        if source_id == 'dcs-table-2.1' and raw_value == 'W25.1':
            assert row['name'] == 'Mannar' and year == 1931
            numeric_text = raw_value.removeprefix('W')
            note = 'The printed value is prefixed W. Table 2.1 does not explain that marker.'
        value = sum(Fraction(piece) for piece in numeric_text.replace(',', '').split())
        if unit == 'persons':
            resolution = 1
        if source_id == 'dcs-table-2.1':
            published_unit = 'thousand persons'
            resolution = 100
            value *= 1000
        row_date = row.get(f'date_{year}') or census_dates[year]['represented_date']
        insert(observations, {
            'observation_id': f'{source_id}:{row_date}:{fid}:{metric}', 'feature_id': fid,
            'source_unit_kind': row['kind'], 'source_name': row['name'], 'source_parent': row.get('parent'),
            'represented_date': row_date, 'year': year, 'metric': metric, 'value': float(value), 'unit': unit,
            'published_value': raw_value, 'published_unit': published_unit,
            'count_resolution_persons': resolution, 'status': status,
            'source_id': source_id, 'published_date': sources[source_id]['date'],
            'locator': locator, 'source_url': row.get('source_url') or page_url(sources[source_id]['url'], locator),
            'scope': scope, 'transcription_note': note or row.get('note'),
        })

    gazette = read('census_gazette')
    for source_id, rows, years, locator, scope, status in (
        ('dcs-table-2.1', read('census_dcs'), tuple(census_dates), 'Table 2.1, PDF p. 1',
         'Both sexes. Historical district groupings as published.', 'retrospective rounded series'),
        ('census-1921', read('census_1921'), (1911, 1921), 'PDF p. 13',
         'National total excludes military and shipping. 1921 national total includes train enumeration (743) and Basses (8).',
         'official comparative table'),
        ('gazette-9533', gazette, (1931, 1946), '',
         'National total excludes shipping and services. 1931 comparators for newly constituted Urban Councils aggregate constituent units.',
         ''),
        ('census-1911-towns', read('census_1911_towns'), (1901, 1911), '',
         'Municipal or Local Board limits as tabulated. Excludes military and shipping. Census-era literacy definition.',
         'official comparative table'),
    ):
        for row in rows:
            for year in years:
                cite = locator or row['page']
                flag = status
                if source_id == 'gazette-9533':
                    cite = f"p. {cite}, PDF p. {int(cite) - 488}"
                    flag = '1931 comparator' if year == 1931 else 'provisional release'
                row_scope = scope
                if source_id == 'census-1921' and row['kind'] == 'province' and year == 1911:
                    row_scope = '1911 figures adjusted where necessary for area changes since the census.'
                observe(source_id, row, year, 'population', row[str(year)], cite, row_scope, flag)
                for suffix, metric in CENSUS_DETAIL.items():
                    observe(source_id, row, year, metric, row.get(f'{year}_{suffix}'), cite, row_scope, flag)

    for row in read('census_1891_comparison'):
        for year in (1881, 1891):
            scope = ('Population excluding military and shipping. ' + row[f'scope_{year}']).strip()
            for suffix, metric in (('', 'population'), ('_male', 'population_male'), ('_female', 'population_female')):
                observe('census-1891', row, year, metric, row[f'{year}{suffix}'], row['locator'],
                        scope, 'official comparative table')
    for row in read('census_1891_area_density'):
        for suffix, metric in (('area_sq_mi', 'area'), ('density', 'population_density')):
            scope = row['area_scope']
            if metric == 'population_density':
                scope = (scope + ' Population excludes military and shipping.').strip()
            observe('census-1891', row, 1891, metric, row[f'1891_{suffix}'], row['locator'], scope,
                    'census report')
    for row in read('census_1901_comparison'):
        for year in (1871, 1881, 1891, 1901):
            for suffix, metric in (('', 'population'), ('_male', 'population_male'),
                                   ('_female', 'population_female'), ('_houses', 'occupied_houses')):
                observe(row['source_id'], row, year, metric, row[f'{year}{suffix}'], row['locator'],
                        row['scope'], 'official comparative table')

    final = 'census-1946-final'
    for year, row in census_dates.items():
        observe(final, {'kind': 'country', 'name': 'Ceylon'}, year,
                'population', row['population'], 'Table 3, p. 57, PDF p. 87',
                'National population excluding Services and Shipping.', 'final report')
    for row in read('census_1946_final'):
        area_scope = ('Province area includes inland water. Population excludes shipping and services.'
                      if row['kind'] == 'province' else
                      'Town, municipal or council area as tabulated.')
        for year in (1931, 1946):
            cite = row['locator']
            observe(final, row, year, 'population', row[str(year)], cite, area_scope, 'final report')
            observe(final, row, year, 'population_density', row[f'{year}_density'], cite, area_scope, 'final report')
        observe(final, row, 1946, 'area', row['area_sq_mi'], cite, area_scope, 'final report',
                note='One area value is published. Province table uses that area alongside both census years.'
                if row['kind'] == 'province' else '')
    for row in read('census_1946_districts'):
        cite = 'Table 97, p. 147, PDF p. 195'
        scope = 'Revenue district as tabulated by sex.'
        for year in (1921, 1946):
            male, female = row[f'{year}_male'], row[f'{year}_female']
            observe(final, row, year, 'population_male', male, cite, scope, 'final report')
            observe(final, row, year, 'population_female', female, cite, scope, 'final report')
            observe(final, row, year, 'population', str(int(male) + int(female)), cite, scope, 'derived from final report',
                    note='Sum of the published male and female counts.')

    places = {r['name']: r for r in read('census_places')}
    urban = make_layer(db, 'urban_census', {
        **unit_fields, **PROVENANCE_FIELDS, 'anchor_name': S, 'geonames_id': S,
        'gazetteer_snapshot': S, 'location_note': S,
        'district_1946': S, 'district_1946_feature_id': S, 'district_1946_locator': S,
    }, ogr.wkbPoint, WGS84)
    # The census table prints each town's district. That is the authority for town-in-district; the traced
    # district polygons are fitted to about 3 km and put some boundary and coastal towns in the wrong polygon.
    printed_district = {}
    for final_row in read('census_1946_final'):
        if final_row['kind'] != 'province':
            printed_district[final_row['unit_name']] = printed_district[final_row['name']] = final_row
    for row in unit_lookup.values():
        if row['unit_kind'] != 'urban':
            continue
        place = places[row['name']]
        qid = row['qid'] or row['anchor_qid']
        assert qid == place['gazetteer_qid'], row['feature_id']
        provenance = geo_provenance(sources, 'wikidata-sri-lanka', f'{qid}, coordinate location (P625)',
                                    'census-1946-final', town_locators[row['name']], '1946-03-19')
        provenance['geometry_source_url'] = f'https://www.wikidata.org/wiki/{qid}#P625'
        insert(urban, {
            **row, **provenance, 'anchor_name': place['anchor_name'],
            'geonames_id': place['geonames_id'], 'gazetteer_snapshot': place['gazetteer_snapshot'],
            'location_note': place['note'],
            **({'district_1946': printed_district[row['name']]['parent'],
                'district_1946_feature_id': unit_id('district', printed_district[row['name']]['parent']),
                'district_1946_locator': printed_district[row['name']]['locator']}
               if row['name'] in printed_district else {}),
        }, point(place['wikidata_lon'], place['wikidata_lat']))

    def province_fields(feature):
        name = feature['name'].removesuffix(' Province')
        row = unit_lookup[unit_id('province', name)]
        return {
            **row, 'name': feature['name'],
            **geo_provenance(sources, 'province-1936-local', f"Approximate province derivative, OSM {feature['osm_id']}",
                             'rumsey-10791.002', 'Main sheet, province boundaries', '1936'),
            'geometry_note': ('Approximate 1936 province from a modern OSM administrative area, cut to the '
                              '1946 traced land plus 5 km (the OSM areas run far out to sea). Not traced '
                              'from the 1936 sheet. Census-year boundary correspondence is unverified.'),
        }

    provinces = ogr.Open(str(MOTOR / 'ceylon-provinces-1936-approximate.gpkg'))
    copy_layer(db, provinces, 'gis_osm_adminareas_a_free', 'province_census',
               {**unit_fields, **PROVENANCE_FIELDS, 'geometry_note': S}, province_fields)
    add_districts(db, sources, unit_lookup, unit_fields)


def add_districts(db, sources, units, unit_fields):
    source_id = 'census-1946-district-map'
    geometry_fields = {
        'geometry_id': S, 'represented_date_basis': S, 'geometry_method': S, 'geometry_note': S,
        'fit_rmse_km': R, 'fit_loo_rmse_km': R,
    }
    layer = make_layer(db, 'district_census_1946', {
        **unit_fields, **PROVENANCE_FIELDS, **geometry_fields,
    }, ogr.wkbMultiPolygon, WGS84)
    provinces = make_layer(db, 'province_census_1946', {
        **unit_fields, **PROVENANCE_FIELDS, **geometry_fields,
        'district_grouping_source_id': S, 'district_grouping_locator': S,
    }, ogr.wkbMultiPolygon, WGS84)
    grouping = {unit_id('district', row['name']): row['parent'] for row in read('census_1946_districts')}
    groups = {}
    features = json.loads((HERE / 'district_1946.geojson').read_text())['features']
    assert len(features) == 20
    sheet = features[0]['properties']
    properties = {
        **geo_provenance(sources, source_id, sheet['source_page'], source_id, sheet['source_page'],
                         sheet['represented_date'], sheet['represented_date']),
        'represented_date_basis': sheet['represented_date_basis'],
        'geometry_method': sheet['geometry_method'], 'geometry_note': sheet['geometry_use'],
        'fit_rmse_km': sheet['fit_rmse_km'], 'fit_loo_rmse_km': sheet['fit_loo_rmse_km'],
    }
    for feature in features:
        row = feature['properties']
        unit = units[row['feature_id']]
        geom = ogr.CreateGeometryFromJson(json.dumps(feature['geometry']))
        assert geom.IsValid() and not geom.IsEmpty(), row['feature_id']
        insert(layer, {**unit, **properties, 'geometry_id': f'1946-map:{unit["feature_id"]}'}, geom)
        province = grouping[unit['feature_id']]
        group = groups.setdefault(province, ogr.Geometry(ogr.wkbMultiPolygon))
        for polygon in geom:
            group.AddGeometry(polygon)
    for name, group in groups.items():
        fid = unit_id('province', name)
        merged = ogr.ForceToMultiPolygon(group.UnionCascaded())
        assert merged.IsValid() and not merged.IsEmpty(), fid
        insert(provinces, {
            **units[fid], **properties, 'name': name + ' Province', 'geometry_id': f'1946-map:{fid}',
            'geometry_method': 'Union of traced districts on the Survey Department sheet',
            'district_grouping_source_id': 'census-1946-final',
            'district_grouping_locator': 'Table 10 and Table 97, pp. 72 and 147 (PDF pp. 104 and 195)',
        }, merged)

    # The traced coast is simplified and the fit is about 3 km, so coastal towns can fall just outside every
    # district. For point-in-polygon joins, each district is grown seaward in 250 m steps to 5 km, never into
    # another district. The traced layer above stays as drawn on the sheet.
    utm = osr.SpatialReference(); utm.ImportFromEPSG(32644)
    utm.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    there, back = osr.CoordinateTransformation(WGS84, utm), osr.CoordinateTransformation(utm, WGS84)
    grown = {}
    for feature in features:
        geom = ogr.CreateGeometryFromJson(json.dumps(feature['geometry'])); geom.Transform(there)
        grown[feature['properties']['feature_id']] = geom
    for _ in range(20):
        everything = None
        for geom in grown.values():
            everything = geom.Clone() if everything is None else everything.Union(geom)
        step = {}
        for fid, geom in grown.items():
            ring = geom.Buffer(250, 8).Difference(everything)
            step[fid] = ring
        taken = None
        for fid in sorted(step):                       # a new strip claimed by two districts goes to one of them
            ring = step[fid] if taken is None else step[fid].Difference(taken)
            taken = ring.Clone() if taken is None else taken.Union(ring)
            grown[fid] = grown[fid].Union(ring)
    joins = make_layer(db, 'district_census_1946_join', {
        **unit_fields, 'geometry_id': S, 'geometry_method': S, 'geometry_note': S, 'source_id': S,
        'represented_date': S, 'published_date': S,
    }, ogr.wkbMultiPolygon, WGS84)
    land = None
    for fid, geom in grown.items():
        geom = geom.Buffer(0); geom.Transform(back)
        geom = ogr.ForceToMultiPolygon(geom.Buffer(0))
        assert geom.IsValid() and not geom.IsEmpty(), fid
        land = geom.Clone() if land is None else land.Union(geom)
        insert(joins, {
            **units[fid], 'geometry_id': f'1946-map-join:{fid}', 'source_id': source_id,
            'represented_date': properties['represented_date'], 'published_date': properties['published_date'],
            'geometry_method': 'Traced district grown 5 km seaward in 250 m steps, never into another district',
            'geometry_note': ('For point-in-polygon joins only. The seaward strip is not on the sheet. Inland '
                              'boundaries are as traced (fit about 3 km): for towns use urban_census.district_1946.'),
        }, geom)
    # The 1936 proxy provinces came from modern administrative areas that run far out to sea. Keep the land.
    proxy = db.GetLayerByName('province_census')
    for feature in proxy:
        clipped = ogr.ForceToMultiPolygon(feature.GetGeometryRef().Intersection(land))
        assert clipped.IsValid() and not clipped.IsEmpty(), feature['feature_id']
        feature.SetGeometry(clipped)
        proxy.SetFeature(feature)
    proxy.ResetReading()


IDENTITY_FIELDS = dict(qid=S, anchor_qid=S, qid_source_id=S, qid_relation=S)
PROVENANCE_FIELDS = {
    'represented_date': S, 'published_date': S, 'source_id': S, 'source_locator': S, 'source_url': S,
    'geometry_source_id': S, 'geometry_source_locator': S, 'geometry_source_url': S,
    'geometry_source_published_date': S, 'geometry_reference_date': S,
}
METRIC_UNITS = {
    'area': 'square miles', 'population_density': 'persons per square mile', 'occupied_houses': 'houses',
    'habitable_buildings': 'buildings',
}
CENSUS_DETAIL = {
    'houses': 'occupied_houses', 'male': 'population_male', 'female': 'population_female',
    'literate_male': 'literates_male', 'literate_female': 'literates_female',
    'buildings': 'habitable_buildings',
}
EARLIER_CENSUS_UNITS = {
    'district:colombo-excluding-municipality': 'Table III, p. 12, PDF p. 17',
    'district:negombo': 'Table III, p. 12, PDF p. 17',
    'district:mullaitivu': 'Table III, p. 12, PDF p. 17',
    'urban:negombo-1881-local-board-limits': 'Table III, p. 13, PDF p. 18',
}


def page_url(url, locator):
    match = re.search(r'PDF p\. (\d+)', locator)
    return f'{url.split("#")[0]}#page={match[1]}' if match and '.pdf' in url.lower() else url


def geo_provenance(sources, geometry_source, geometry_locator, source_id, locator, represented,
                   geometry_date=None):
    return {
        'represented_date': represented, 'published_date': sources[source_id]['date'],
        'source_id': source_id, 'source_locator': locator,
        'source_url': page_url(sources[source_id]['url'], locator),
        'geometry_source_id': geometry_source, 'geometry_source_locator': geometry_locator,
        'geometry_source_url': page_url(sources[geometry_source]['url'], geometry_locator),
        'geometry_source_published_date': sources[geometry_source]['date'],
        'geometry_reference_date': geometry_date,
    }


RAIL_IDS = {
    'Main Line': 'main', 'Coast Line': 'coast', 'Matale Line': 'matale', 'Northern Line': 'northern',
    'Mannar Line': 'mannar', 'Puttalam Line': 'puttalam', 'Kelani Valley Line': 'kelani-valley',
    'Batticaloa Line': 'batticaloa', 'Trincomalee Line': 'trincomalee',
}


def map_claim(evidence_id, mode, section, keys, name, year, source, locator, details, event='mapped'):
    return dict(evidence_id=evidence_id, mode=mode, section_id=section, corridor_ids=keys,
                name=name, event=event, date=str(year), date_relation='edition',
                source_id=source, locator=locator, details=details)


def add_ferguson_roads(db, sources, source_id):
    layer = db.GetLayerByName('road_1893_traces')
    with (FERGUSON.parent / 'graticule-controls.csv').open(newline='') as file:
        controls = list(csv.DictReader(file))
    scan_scale = 11993 / 1500

    def basis(points):
        x, y = ((np.asarray(points) - [510, 750]) / [460, 680]).T
        return np.stack((np.ones_like(x), x, y, x*y), axis=-1)

    fit = []
    for axis in ('longitude', 'latitude'):
        ticks = [row for row in controls if row[f'printed_{axis}']]
        pixels = [[float(row[key]) / scan_scale for key in ('scan_col', 'scan_row')] for row in ticks]
        fit.append(np.linalg.lstsq(basis(pixels), [float(row[f'printed_{axis}']) for row in ticks], rcond=None)[0])
    projected = layer.GetSpatialRef().Clone()
    projected.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    transform = osr.CoordinateTransformation(WGS84, projected)
    claims = []
    for row in read('road_traces_1893'):
        identifier = f"1893-road:{row['key']}"
        vertices = [[int(v) for v in pair.split(',')] for pair in row['pixels'].split()]
        geom = ogr.Geometry(ogr.wkbLineString)
        for lon, lat in basis(vertices) @ np.array(fit).T:
            assert 79 < lon < 83 and 5.5 < lat < 10, identifier
            geom.AddPoint_2D(*transform.TransformPoint(float(lon), float(lat))[:2])
        locator = row['locator']
        insert(layer, {
            'source_catalogue': 'David Rumsey 11597.002', 'map_year': 1893, 'represented_year': 1893,
            'geometry_role': 'depiction on historical map', 'feature_id': identifier,
            'geometry_id': f'{identifier}:ferguson', 'name': row['name'], 'legend_class': row['legend_class'],
            'georef_method': 'Border graticule fit, historical datum approximated by WGS84',
            'method': 'Manual trace of the printed road strokes. ' + row['note'],
            'coverage': 'Selected corridors', 'review_status': 'traced',
            'segment_id': identifier, 'corridor_id': identifier, 'evidence_id': identifier,
            **geo_provenance(sources, source_id, locator, source_id, locator, '1893', '1893'),
        }, geom)
        claims.append(map_claim(identifier, 'road', identifier, row['modern_key'], row['name'], 1893,
                                source_id, locator, f"{row['legend_class']}. {row['note']}"))
    return claims


def rail_basis(pixels):
    x, y = (np.asarray(pixels) - [600, 800]).T / 500
    return np.stack((x * 0 + 1, x, y, x*y, x*x, y*y), axis=-1)


def map_line(pixel_text, fit):
    line = ogr.Geometry(ogr.wkbLineString)
    vertices = [[int(v) for v in p.split(',')] for p in pixel_text.split()]
    for lon, lat in rail_basis(vertices) @ fit:
        line.AddPoint_2D(float(lon), float(lat))
    return line


RAIL_IDENTITY_FIELDS = {'corridor_qid': S, 'corridor_qid_source_id': S}


def rail_identity(families, corridor):
    family = families[corridor.removeprefix('rail:')]
    return {'corridor_qid': family['qid'], 'corridor_qid_source_id': family['qid_source_id']}


def add_ferguson_towns(db, source, sources, map_id):
    names = {
        row['name'].removesuffix(' Town'): row
        for row in read('census_units') if row['unit_kind'] == 'urban'
    }
    names.update({row['name']: row for row in read('rail_control_qids')})
    names['Mannar'] = {'qid': 'Q1280127', 'qid_source_id': 'wikidata-sri-lanka'}
    names['Haputale'] = {'qid': 'Q3533257', 'qid_source_id': 'wikidata-sri-lanka'}
    names['Avisawella'] = names['Avissawella']
    locator = 'Main sheet, named town symbol'
    with (FERGUSON.parent / 'town-checks.csv').open(newline='', encoding='utf-8') as file:
        offsets = {row['name']: row for row in csv.DictReader(file)}

    def match(feature):
        key = feature['name']
        identity = names[key]
        return {
            'qid': identity['qid'], 'qid_source_id': identity['qid_source_id'],
            'qid_relation': 'named settlement shown on map',
            **geo_provenance(sources, map_id, locator, map_id, locator, '1893', '1893'),
            'reference_offset_m': int(offsets[key]['offset_m']) if key in offsets else None,
            'reference_offset_note': (f"Distance from the map position to {offsets[key]['reference_source']} "
                                      f"node {offsets[key]['osm_node_id']}; a measure of the sheet's fit here"
                                      if key in offsets else None),
        }

    copy_layer(db, source, 'towns', 'ferguson_towns_1893',
               {**IDENTITY_FIELDS, **PROVENANCE_FIELDS, 'reference_offset_m': I, 'reference_offset_note': S},
               match)


def add_1915(db, sources, families):
    map_id = 'rumsey-13440.000'
    locator = 'Ceylon portion, green railway'
    control_qids = {r['name']: r for r in read('rail_control_qids')}
    controls = read('rail_1915_controls')
    pixels = [(int(row['x']), int(row['y'])) for row in controls]
    reference = np.array([(float(row['lon']), float(row['lat'])) for row in controls])
    design = rail_basis(pixels)
    fit = np.linalg.lstsq(design, reference, rcond=None)[0]

    def errors_km(predicted, target):
        return np.linalg.norm((predicted - target) * [110, 111], axis=-1)

    residuals = errors_km(design @ fit, reference)
    holdouts = []
    control_layer = make_layer(db, 'rail_1915_controls', {
        'feature_id': S, 'name': S, 'x': I, 'y': I, 'geonames_id': S,
        'fit_residual_km': R, 'holdout_error_km': R, **IDENTITY_FIELDS, **PROVENANCE_FIELDS,
    }, ogr.wkbPoint, WGS84)
    for i, row in enumerate(controls):
        keep = np.arange(len(controls)) != i
        model = np.linalg.lstsq(design[keep], reference[keep], rcond=None)[0]
        error = float(errors_km(design[i] @ model, reference[i]))
        holdouts.append(error)
        match = control_qids[row['name']]
        prov = geo_provenance(sources, 'geonames-lk', f"GeoNames {row['geonames_id']}",
                              map_id, 'Ceylon portion, named railway town or station', '1915-03')
        prov['geometry_source_url'] = f"https://www.geonames.org/{row['geonames_id']}/"
        insert(control_layer, {
            **{key: row[key] for key in ('name', 'x', 'y', 'geonames_id')},
            **prov, 'feature_id': f"1915-control:{match['key']}",
            'qid': match['qid'], 'qid_source_id': match['qid_source_id'],
            'qid_relation': 'named control-point reference place',
            'fit_residual_km': float(residuals[i]), 'holdout_error_km': error,
        }, point(row['lon'], row['lat']))
    rms = float(np.sqrt(np.mean(np.square(holdouts))))
    layer = make_layer(db, 'rail_1915_traces', {
        'feature_id': S, 'corridor_id': S, 'name': S, 'map_year': I, 'gauge_mm': I,
        'gauge_source_id': S, 'gauge_source_locator': S, 'geometry_role': S, 'holdout_rms_km': R,
        'source_pixels': S, 'note': S, **RAIL_IDENTITY_FIELDS, **PROVENANCE_FIELDS,
    }, ogr.wkbLineString, WGS84)
    claims = []
    for row in read('rail_1915_traces'):
        narrow = row['gauge_mm'] == '762'
        insert(layer, {
            'feature_id': row['segment_id'], 'corridor_id': row['corridor_id'], 'name': row['name'],
            'map_year': 1915, 'gauge_mm': row['gauge_mm'],
            'gauge_source_id': 'cgr-narrow' if narrow else map_id,
            'gauge_source_locator': 'Gauge discussion and opening table' if narrow else 'Gauge legend and line width',
            'geometry_role': 'schematic map trace',
            'holdout_rms_km': rms, 'source_pixels': row['pixels'], 'note': row['note'],
            **rail_identity(families, row['corridor_id']),
            **geo_provenance(sources, map_id, locator, map_id, locator, '1915-03', '1915-03'),
        }, map_line(row['pixels'], fit))
        claims.append(map_claim(row['segment_id'], 'rail', row['segment_id'],
                                row['corridor_id'].split(':')[1], row['name'], '1915-03', map_id,
                                locator, row['note'] or 'Green railway symbol.'))
    roads = make_layer(db, 'road_1915_traces', {
        'feature_id': S, 'section_id': S, 'corridor_id': S, 'name': S, 'map_year': I,
        'geometry_role': S, 'holdout_rms_km': R, 'source_pixels': S, 'note': S, **PROVENANCE_FIELDS,
    }, ogr.wkbLineString, WGS84)
    road_locator = 'Ceylon portion, thin black roadway symbol per legend'
    for row in read('road_1915_traces'):
        corridor = f"motor-1936:{row['corridor_ids']}" if row['corridor_ids'] else ''
        insert(roads, {
            'feature_id': row['feature_id'], 'section_id': row['section_id'], 'name': row['name'],
            'corridor_id': corridor, 'map_year': 1915, 'geometry_role': 'schematic map trace',
            'holdout_rms_km': rms, 'source_pixels': row['pixels'], 'note': row['note'],
            **geo_provenance(sources, map_id, road_locator, map_id, road_locator, '1915-03', '1915-03'),
        }, map_line(row['pixels'], fit))
        claims.append(map_claim(row['feature_id'], 'road', row['section_id'], row['corridor_ids'],
                                row['name'], '1915-03', map_id, road_locator, row['note']))
    return claims


def add_transport(db, sources):
    transport = ogr.Open(str(MOTOR / 'transport-1936.gpkg'))
    ferguson = ogr.Open(str(FERGUSON))
    traces = transport.GetLayerByName('roads_1936_map_trace')
    known_road_ids = {feature['corridor_id'].split(':')[1] for feature in traces}
    traces.ResetReading()
    families = {r['key']: r for r in read('rail_families')}
    evidence = (read('transport_records') + read('railway_later_records')
                + add_1915(db, sources, families) + add_blue_book(db, sources))
    ferguson_id = 'rumsey-11597.002'
    road_1893 = {'Colombo–Avisawella': 'colombo-avissawella', 'Avisawella–Ratnapura': 'avissawella-ratnapura'}
    rail_1893 = {
        'Colombo–Peradeniya': 'main', 'Peradeniya–Kandy': 'main', 'Peradeniya–Haputale': 'main',
        'Colombo–Galle': 'coast', 'Galle–Matara': 'coast',
    }
    for mode, mapping in (('road', road_1893), ('rail', rail_1893)):
        def tag_1893(feature):
            key = slug(feature['name'])
            segment = f'1893-{mode}:{key}'
            corridor = f'{"motor-1936" if mode == "road" else "rail"}:{mapping[feature["name"]]}'
            event = 'mapped' if feature['map_status'] != 'uncertain' else 'map_status_uncertain'
            detail = f"Legend class: {feature['legend_class']}."
            if event == 'map_status_uncertain':
                detail += ' Printed phase of works unresolved. No opening inferred.'
            evidence.append(map_claim(segment, mode, segment, mapping[feature['name']],
                                      feature['name'], 1893, ferguson_id,
                                      'Main sheet and transport legend', detail, event))
            return {
                'segment_id': segment, 'corridor_id': corridor, 'evidence_id': segment,
                **(rail_identity(families, corridor) if mode == 'rail' else {}),
                **geo_provenance(sources, ferguson_id, 'Main sheet, traced cartographic line',
                                 ferguson_id, 'Main sheet and transport legend', '1893', '1893'),
            }

        name = 'road_traces' if mode == 'road' else 'railway_traces'
        copy_layer(db, ferguson, name, f'{mode}_1893_traces',
                   {'segment_id': S, 'corridor_id': S, 'evidence_id': S, **PROVENANCE_FIELDS,
                    **(RAIL_IDENTITY_FIELDS if mode == 'rail' else {})}, tag_1893)
    added_road_claims = add_ferguson_roads(db, sources, ferguson_id)
    evidence.extend(added_road_claims)
    add_ferguson_towns(db, ferguson, sources, ferguson_id)
    for row in traces:
        identifier = row['corridor_id']
        key = identifier.split(':')[1]
        mode = 'ferry' if key.endswith('-ferry') else 'road'
        evidence.append(map_claim(identifier, mode, identifier, key, row['historical_corridor'], 1936,
                                  'rumsey-10791.002', 'Main sheet', row['legend_class']))
    for label, key in RAIL_IDS.items():
        evidence.append(map_claim(f'motor-1936-rail:{key}', 'rail', f'rail:{key}', key, label,
                                  1936, 'rumsey-10791.002', 'Main sheet',
                                  'Line represented in existing 1936 railway comparison. Spatial layer uses modern OSM geometry.'))

    by_corridor = {record['evidence_id']: [record] for record in added_road_claims}
    for record in evidence:
        for key in filter(None, record['corridor_ids'].split('|')):
            if record['mode'] == 'rail':
                assert key in set(RAIL_IDS.values()) | {'uda-pussellawa'}, key
                corridor = f'rail:{key}'
            else:
                assert key in known_road_ids, key
                corridor = f'motor-1936:{key}'
            by_corridor.setdefault(corridor, []).append(record)

    def chronology(corridor):
        records = by_corridor[corridor]
        dated = [r for r in records if r['date'] and r['date_relation'] != 'edition' and r['event'] != 'mapped']
        maps = [int(r['date'][:4]) for r in records if r['event'] == 'mapped' and r['date_relation'] != 'approximate']
        approximate_maps = [int(r['date'][:4]) for r in records if r['event'] == 'mapped' and r['date_relation'] == 'approximate']
        return {
            'first_checked_map_year': min(maps, default=None),
            'first_approx_map_year': min(approximate_maps, default=None),
            'earliest_linked_record_year': min((int(r['date'][:4]) for r in dated), default=None),
            'linked_record_count': len(dated),
        }

    chronology_fields = {'first_checked_map_year': I, 'first_approx_map_year': I,
                         'earliest_linked_record_year': I, 'linked_record_count': I}

    motor_id = 'rumsey-10791.002'

    def tag_road(feature):
        corridor = feature['corridor_id']
        type_ = 'ferry' if corridor.endswith('-ferry') else 'road'
        return {
            'feature_id': corridor, 'mode': type_, **chronology(corridor),
            **geo_provenance(sources, motor_id, 'Main sheet, traced cartographic line',
                             motor_id, 'Main sheet and transport legend', '1936', '1936'),
        }

    copy_layer(db, transport, 'roads_1936_map_trace', 'road_ferry_chronology',
               {'feature_id': S, 'mode': S, **chronology_fields, **PROVENANCE_FIELDS}, tag_road)

    def osm_tag(feature):
        osm_key = f"{feature['osm_type']}/{feature['osm_id']}"
        prov = geo_provenance(sources, 'osm-local', osm_key, motor_id,
                              'Main sheet, historical corridor comparison', '1936', feature['snapshot'])
        prov['geometry_source_url'] = f'https://www.openstreetmap.org/{osm_key}'
        qid = feature['wikidata'] or ''
        qid = qid if re.fullmatch(r'Q[1-9][0-9]*', qid) else ''
        return {
            **prov,
            'qid': qid, 'qid_source_id': 'osm-local' if qid else '',
            'qid_relation': 'OSM Wikidata tag for this feature' if qid else '',
        }

    def tag_rail(feature):
        corridor = f"rail:{RAIL_IDS[feature['historical_corridor']]}"
        narrow = corridor == 'rail:kelani-valley'      # OSM's gauge tag is the present track
        return {
            'corridor_id': corridor, **chronology(corridor),
            **osm_tag(feature), **rail_identity(families, corridor),
            'gauge_mm_1936': 762 if narrow else None,
            'gauge_source_id': 'cgr-narrow' if narrow else None,
            'gauge_source_locator': 'Gauge discussion and opening table' if narrow else None,
            'attribute_note': ('The gauge field is the modern OSM tag (track later converted to broad gauge); '
                               'gauge_mm_1936 is the gauge in 1936. ' if narrow else '') +
                              'OSM attributes describe the present track. Lengths are track, not route, length.',
        }

    copy_layer(db, transport, 'rails_1936_osm', 'rail_1936_osm',
               {'corridor_id': S, **chronology_fields, **PROVENANCE_FIELDS,
                **IDENTITY_FIELDS, **RAIL_IDENTITY_FIELDS, 'gauge_mm_1936': I, 'gauge_source_id': S,
                'gauge_source_locator': S, 'attribute_note': S}, tag_rail)
    def tag_osm_road(feature):
        source_feature = feature['feature_id']
        start, end = feature['from_node'], feature['to_node']
        fid = f"{feature['corridor_id']}:osm:{feature['osm_id']}:{start}:{end}"
        return {
            **osm_tag(feature), 'feature_id': fid, 'osm_feature_id': source_feature,
            **chronology(feature['corridor_id']),
        }

    copy_layer(db, transport, 'roads_1936_osm_candidates', 'road_1936_osm_candidates',
               {**PROVENANCE_FIELDS, **IDENTITY_FIELDS, **chronology_fields, 'osm_feature_id': S},
               tag_osm_road)
    add_rail_1915_osm(db, sources, families)

    event_layer = make_layer(db, 'transport_evidence', {
        'evidence_id': S, 'mode': S, 'section_id': S, 'name': S, 'event': S, 'represented_date': S,
        'event_year': I, 'date_precision': S, 'date_relation': S, 'source_id': S, 'locator': S,
        'published_date': S, 'source_url': S, 'details': S, 'length_miles': R, 'length_chains': R,
        'cost': R, 'currency': S,
    })
    links = make_layer(db, 'transport_evidence_links', {
        'corridor_id': S, 'evidence_id': S, 'link_scope': S, 'name': S, 'event': S, 'represented_date': S,
        'source_id': S, 'locator': S, 'published_date': S, 'source_url': S, 'details': S,
    })
    for row in evidence:
        data = {k: v for k, v in row.items() if k not in ('date', 'corridor_ids')}
        stamp = row['date']
        if stamp:
            date.fromisoformat((stamp + '-01-01')[:10] if len(stamp) == 4 else
                               stamp + '-01' if len(stamp) == 7 else stamp)
        precision = {0: None, 4: 'year', 7: 'month', 10: 'day'}[len(stamp)]
        data.update(represented_date=stamp, date_precision=precision, event_year=stamp[:4],
                    published_date=sources[row['source_id']]['date'],
                    source_url=page_url(sources[row['source_id']]['url'], row['locator']))
        insert(event_layer, data)
    for corridor, records in by_corridor.items():
        for row in records:
            data = {key: row[key] for key in ('evidence_id', 'name', 'event', 'source_id', 'locator', 'details')}
            is_original = corridor == row['evidence_id']
            scope = 'same source trace' if is_original else (
                'rail line includes or relates to named section' if corridor.startswith('rail:') else
                'historically related corridor or part of corridor')
            insert(links, dict(data, corridor_id=corridor, link_scope=scope, represented_date=row['date'],
                               published_date=sources[row['source_id']]['date'],
                               source_url=page_url(sources[row['source_id']]['url'], row['locator'])))
    add_crossings(db, sources, {record['evidence_id']: record for record in evidence})


def add_rail_1915_osm(db, sources, families):
    comparison = ogr.Open(str(HERE / 'rail_1915_osm.geojson'))
    map_id = 'rumsey-13440.000'

    def provenance(feature):
        ways = 'OSM ways ' + ', '.join(str(way) for way in feature['osm_way_ids'])
        return {
            **rail_identity(families, feature['corridor_id']),
            **geo_provenance(sources, 'osm-local', ways, map_id, 'Ceylon portion, Ragama–Chilaw',
                             feature['historical_map_date'], feature['osm_snapshot']),
        }

    copy_layer(db, comparison, 'rail_1915_osm', 'rail_1915_osm_candidates',
               {**PROVENANCE_FIELDS, **RAIL_IDENTITY_FIELDS}, provenance)


def add_blue_book(db, sources):
    source_id = 'blue-book-1928'
    source = sources[source_id]
    fields = {'source_id': S, 'locator': S, 'source_url': S, 'represented_date': S, 'published_date': S}
    inventory = make_layer(db, 'road_inventory_1928', {
        'record_id': S, 'name': S, 'province_as_printed': S, 'table_scope': S,
        'length_miles': R, 'length_as_printed': S, 'symbol': S, 'traffic_class': S, 'note': S,
        'evidence_id': S, **fields,
    })
    works = make_layer(db, 'road_works_1928', {
        'work_id': S, 'evidence_id': S, 'name': S, 'estimate_id': S, 'work_kind': S,
        'start_date': S, 'represented_period': S, 'estimated_rupees': R, 'expenditure_rupees': R,
        'prior_expenditure_rupees': R, 'status': S, 'note': S, **fields,
    })
    matches = {r['name']: r for r in read('road_inventory_matches_1928')}
    rows = read('road_inventory_1928_west_central') + read('road_inventory_1928_rest')
    claims = []
    totals = {}
    for row in rows:
        page = int(re.search(r'PDF p\. (\d+)', row['locator'])[1])
        province = row['province_as_printed']
        principal = province == 'Lengths of some of the Principal Roads'
        record_id = row['record_id']
        match = matches.pop(row['name'], None)
        length = row['length_open_miles']
        if not principal:
            totals[province] = totals.get(province, Decimal(0)) + Decimal(length)
        traffic = blue_book_traffic(page, row['symbol'])
        if match:
            details = ' '.join(filter(None, (traffic, row['note'], match['note'])))
            claims.append(record_claim(record_id, match['section_id'], match['corridor_ids'], row['name'],
                                       'route_length_reported' if principal else 'open_length_reported',
                                       '1928', source_id, row['locator'], details, length))
        insert(inventory, {
            'record_id': record_id, 'name': row['name'], 'province_as_printed': province,
            'table_scope': 'principal route lengths' if principal else 'existing road inventory',
            'length_miles': length, 'length_as_printed': length, 'symbol': row['symbol'],
            'traffic_class': traffic, 'note': row['note'], 'evidence_id': record_id if match else '',
            'source_id': source_id, 'locator': row['locator'], 'source_url': source['url'],
            'represented_date': '1928', 'published_date': source['date'],
        })
    assert not matches, list(matches)
    assert len(totals) == 9 and sum(totals.values()) == Decimal('4978.22'), totals
    for row in read('road_works_1928'):
        identifier = row['work_id']
        stamp = row['start_date']
        details = ' '.join(filter(None, (
            row['work_kind'].capitalize() + f". Return status {row['status']} for {row['represented_period']}.",
            row['note'],
        )))
        claims.append(record_claim(identifier, row['section_id'], row['corridor_ids'], row['name'],
                                   'work_started' if stamp else 'expenditure_reported', stamp or '1928',
                                   source_id, row['locator'], details))
        insert(works, {
            **{k: v for k, v in row.items() if k not in ('section_id', 'corridor_ids')},
            'evidence_id': identifier, 'source_id': source_id, 'source_url': source['url'],
            'represented_date': '1928', 'published_date': source['date'],
        })
    return claims


def blue_book_traffic(page, symbol):
    if not symbol:
        return ''
    categories = {
        426: {'*': 'lorry', '†': 'motor car', '‡': 'unsuitable for motor cars', '§': 'weather-dependent motor car'},
        427: {'*': 'weather-dependent motor car', '†': 'lorry', '‡': 'motor car', '§': 'unsuitable for motor cars'},
        428: {'*': 'lorry', '†': 'motor car', '‡': 'unsuitable for motor cars', '§': 'weather-dependent motor car',
              '* and †': 'mixed, see note'},
        429: {'*': 'motor car', '†': 'lorry', '‡': 'unsuitable for motor cars', '§': 'weather-dependent motor car'},
        430: {'*': 'motor car', '†': 'lorry', '‡': 'motor car up to fifth milepost'},
    }
    return categories[page][symbol]


def record_claim(identifier, section, keys, name, event, stamp, source_id, locator, details, length=None):
    return {
        'evidence_id': identifier, 'mode': 'road', 'section_id': section, 'corridor_ids': keys,
        'name': name, 'event': event, 'date': stamp, 'date_relation': 'reported',
        'source_id': source_id, 'locator': locator, 'details': details, 'length_miles': length,
    }


def add_crossings(db, sources, evidence):
    crossings = make_layer(db, 'road_rail_crossings_1925', {
        'feature_id': S, 'evidence_id': S, 'rail_section': S, 'miles': I, 'chains': R,
        'description': S, 'road_class': S, 'represented_date': S, 'published_date': S,
        'source_id': S, 'locator': S, 'source_url': S,
    })
    for row in read('road_rail_crossings_1925'):
        claim = evidence[row['evidence_id']]
        source = sources[claim['source_id']]
        insert(crossings, {
            **{k: v for k, v in row.items() if k in {
                'feature_id', 'evidence_id', 'rail_section', 'miles', 'chains', 'description', 'road_class',
            }},
            'represented_date': claim['date'], 'published_date': source['date'],
            'source_id': claim['source_id'], 'locator': claim['locator'],
            'source_url': page_url(source['url'], claim['locator']),
        })


def add_headmen_divisions(db, sources):
    """Chief Headmen's divisions as drawn in the 1935 malaria report maps. See headmen_divisions_1934_method.md."""
    source_id = 'malaria-1935-maps'
    features = json.loads((HERE / 'headmen_divisions_1934.geojson').read_text())['features']
    fields = [k for k in features[0]['properties'] if k != 'source']
    layer = make_layer(db, 'headmen_divisions_1934', {
        **{field: S for field in fields}, 'represented_date': S, 'published_date': S, 'source_id': S,
        'source_locator': S, 'source_url': S, 'geometry_method': S, 'geometry_note': S,
    }, ogr.wkbMultiPolygon, WGS84)
    for feature in features:
        geom = ogr.ForceToMultiPolygon(ogr.CreateGeometryFromJson(json.dumps(feature['geometry'])))
        assert geom.IsValid() and not geom.IsEmpty(), feature['properties']['feature_id']
        insert(layer, {
            **{field: feature['properties'].get(field) for field in fields},
            'represented_date': '1934', 'published_date': sources[source_id]['date'], 'source_id': source_id,
            'source_locator': 'Map 7 (PDF p. 15) for the lines; Map 17 and its key (PDF pp. 38-39) for the numbers and names',
            'source_url': sources[source_id]['url'],
            'geometry_method': ('Regions segmented from the 400 dpi scan of Map 7 and merged by hand; plate fitted to '
                                'the modern coast (quadratic, about 1 km at eight coastal landmarks)'),
            'geometry_note': ('A 24 miles to an inch plate: lines are good to a few km. Maps 7 and 17 differ by '
                              '5-13 km in places. Read identity_confidence and note before relying on a division.'),
        }, geom)


def add_motor_amenities(db, sources):
    source_id = 'rumsey-10791.002'
    source = sources[source_id]
    naming = {'feature_id': S, 'facility_kind': S, 'place_as_printed': S, 'province_as_printed': S,
              'note': S}
    citing = {'represented_date': S, 'published_date': S, 'source_id': S, 'source_locator': S,
              'source_url': S}
    records = make_layer(db, 'motor_amenity_listings_1936', {**naming, **citing})
    observations = make_layer(db, 'motor_amenity_observations_1936', {
        'observation_id': S, 'feature_id': S, 'metric': S, 'value': I, **citing,
    })
    points = make_layer(db, 'motor_amenity_places_1936', {
        **naming, **PROVENANCE_FIELDS, 'qid': S, 'qid_source_id': S, 'anchor_name': S,
        'match_method': S, 'location_role': S, 'gazetteer_snapshot': S,
        'geonames_id': S, 'coordinate_note': S,
    }, ogr.wkbPoint, WGS84)
    listings = read('motor_map_1936_transport_listings')
    listings.extend(dict(row, facility_kind='rest_house') for row in read('motor_map_1936_resthouses'))
    matches = {row['feature_id']: row for row in read('motor_1936_place_matches')}
    titles = {'petrol_depot': 'Petrol Depots', 'rest_house': 'Rest Houses',
              'railway_car_booking': 'Railway Stations Which Accept the Booking of Motor Cars'}
    for row in listings:
        identifier = row['feature_id']
        where = row.get('province_as_printed') or f"column {row['map_column']}, row {row['source_row']}"
        locator = f"Left margin, {titles[row['facility_kind']]}, {where}, {row['place_as_printed']}"
        cite = {
            'represented_date': '1936', 'published_date': source['date'], 'source_id': source_id,
            'source_locator': locator, 'source_url': source['url'],
        }
        name_data = {key: row.get(key) for key in naming}
        insert(records, {**name_data, **cite})
        metrics = {'listed': 1}
        if row['facility_kind'] == 'rest_house':
            metrics.update(
                bedrooms=row['bedroom_count'], beds=row['bed_count'],
                second_class_mark=row['second_class'],
            )
            if '2 Rest Houses' in row['note']:
                metrics['rest_houses_reported'] = 2
        for metric, value in metrics.items():
            if value in ('', None):
                continue
            insert(observations, {
                **cite, 'observation_id': f'{identifier}:{metric}', 'feature_id': identifier,
                'metric': metric, 'value': value,
            })
        if identifier not in matches:
            continue
        match = matches[identifier]
        qid = match['place_qid']
        prov = geo_provenance(sources, 'wikidata-sri-lanka', f'{qid}, coordinate location (P625)',
                              source_id, locator, '1936')
        prov['geometry_source_url'] = f'https://www.wikidata.org/wiki/{qid}#P625'
        if match.get('geonames_id'):       # reviewed: the Wikidata coordinate was rejected for this place
            prov = geo_provenance(sources, 'geonames-lk', f"GeoNames {match['geonames_id']}",
                                  source_id, locator, '1936')
            prov['geometry_source_url'] = f"https://www.geonames.org/{match['geonames_id']}/"
        insert(points, {
            **name_data, **prov, 'qid': qid, 'qid_source_id': 'wikidata-sri-lanka',
            **{key: match.get(key) or None for key in ('anchor_name', 'match_method', 'location_role',
                                                        'gazetteer_snapshot', 'geonames_id', 'coordinate_note')},
        }, point(match['lon'], match['lat']))


def add_bridge_review(db, sources):
    rows = read('road_alignment_review')
    fields = {key: S for key in rows[0] if key != 'geometry_wkt_epsg4326'}
    fields.update(osm_way_id=ogr.OFTInteger64, osm_way_version=I, length_m=R)
    review = make_layer(db, 'road_alignment_review', {
        **fields, 'represented_date': S, 'published_date': S, 'reviewed_on': S,
        'source_id': S, 'geometry_source_id': S, 'bridge_id': S,
    })
    bridges = make_layer(db, 'reviewed_historical_bridges', {
        'feature_id': S, 'name': S, 'corridor_id': S, 'review_id': S,
        'event_basis': S, 'geometry_note': S, 'historical_reference_url': S,
        'corroboration_url': S, 'osm_way_id': ogr.OFTInteger64, 'osm_way_version': I,
        'osm_node_ids': S, 'length_m': R, 'opening_evidence_id': S,
        'identity_source_id': S, 'inspection_source_id': S,
        'imagery_accuracy_m_reported': R, 'digitized_from_pixels': S,
        **IDENTITY_FIELDS, **PROVENANCE_FIELDS,
    }, ogr.wkbLineString, WGS84)
    map_id = 'rumsey-10791.002'
    mawanella_id = 'bridge:mawanella:brick-maha-oya'
    kallady_id = 'road-bridge:lk:batticaloa:lady-manning'
    for row in rows:
        insert(review, {
            **{key: row[key] for key in fields},
            'represented_date': '1936', 'published_date': sources[map_id]['date'],
            'reviewed_on': '2026-11-16', 'source_id': map_id, 'geometry_source_id': 'osm-local',
            'bridge_id': kallady_id if ':kallady:' in row['review_id'] else mawanella_id,
        })
        if row['status'] != 'retained_same_structure':
            continue
        geom = ogr.CreateGeometryFromWkt(row['geometry_wkt_epsg4326'])
        prov = geo_provenance(sources, 'osm-local', f"OSM way {row['osm_way_id']} v{row['osm_way_version']}",
                              map_id, row['map_locator'], '1936', row['osm_snapshot'])
        prov['geometry_source_url'] = row['osm_url']
        insert(bridges, {
            **prov, 'feature_id': mawanella_id,
            'name': row['historical_name'], 'corridor_id': 'motor-1936:colombo-kandy',
            'review_id': row['review_id'], 'qid': 'Q104853160', 'qid_source_id': 'wikidata-sri-lanka',
            'qid_relation': 'same named physical crossing',
            'event_basis': row['finding'], 'geometry_note': row['uncertainty'],
            'historical_reference_url': row['historical_reference_url'],
            'corroboration_url': row['corroboration_url'],
            'identity_source_id': 'spc-mawanella-bridge', 'opening_evidence_id': 'r-mawanella',
            **{key: row[key] for key in ('osm_way_id', 'osm_way_version', 'osm_node_ids', 'length_m')},
        }, geom)
    deck = json.loads((HERE / 'lady_manning_bridge.geojson').read_text())['features'][0]
    row = deck['properties']
    assert row['feature_id'] == kallady_id
    image_source = 'kallady-ortho-2024'
    geometry_locator = row['coordinate_source_pixels']
    prov = geo_provenance(sources, image_source, geometry_locator, map_id, row['historical_map_locator'],
                          str(row['historical_map_year']), row['coordinate_source_acquired'])
    insert(bridges, {
        **prov, 'feature_id': kallady_id, 'name': row['name'],
        'corridor_id': 'motor-1936:pottuvil-batticaloa',
        'event_basis': row['geometry_role'], 'geometry_note': row['coordinate_uncertainty'],
        'qid': 'Q6353480', 'qid_source_id': 'wikidata-sri-lanka',
        'qid_relation': 'historic bridge name, independently located on old steel deck',
        'historical_reference_url': row['historical_opening_source_url'],
        'corroboration_url': row['identity_source_url'] + ' | ' + row['survival_source_url'],
        'opening_evidence_id': 'r-kallady-open-1928', 'length_m': row['length_m'],
        'identity_source_id': 'jica-kallady-study', 'inspection_source_id': 'kallady-inspection-2025',
        'imagery_accuracy_m_reported': row['coordinate_source_reported_accuracy_m'],
        'digitized_from_pixels': row['coordinate_source_pixels'],
    }, ogr.CreateGeometryFromJson(json.dumps(deck['geometry'])))


def write_package(temp):
    db = ogr.GetDriverByName('GPKG').CreateDataSource(str(temp))
    sources = {r['source_id']: r for table in (
        'sources', 'railway_later_sources', 'historical_place_sources'
    ) for r in read(table)}
    try:
        db.StartTransaction()
        source_layer = make_layer(db, 'source_catalogue', {
            'source_id': S, 'title': S, 'published_date': S, 'kind': S,
            'url': S, 'local_reference': S, 'note': S,
        })
        for row in sources.values():
            insert(source_layer, {k if k != 'date' else 'published_date': v for k, v in row.items()})
        source_layer = None
        add_historical_places(db, sources)
        add_chitty_index(db)
        add_census(db, sources)
        add_headmen_divisions(db, sources)
        add_transport(db, sources)
        add_motor_amenities(db, sources)
        add_bridge_review(db, sources)
        db.CommitTransaction()
    finally:
        db = None
    with closing(sqlite3.connect(temp)) as con, con:
        for table, fields in [
            ('source_catalogue', 'source_id'), ('census_observations', 'observation_id'),
            ('census_reconciliation', 'check_id'),
            ('census_units', 'feature_id'), ('urban_census', 'feature_id'), ('province_census', 'feature_id'),
            ('district_census_1946', 'feature_id'), ('headmen_divisions_1934', 'feature_id'), ('road_1915_traces', 'feature_id'),
            ('province_census_1946', 'feature_id'),
            ('rail_1915_osm_candidates', 'feature_id'),
            ('transport_evidence', 'evidence_id'), ('transport_evidence_links', 'corridor_id,evidence_id'),
            ('road_ferry_chronology', 'feature_id'), ('road_1936_osm_candidates', 'feature_id'),
            ('rail_1936_osm', 'feature_id'), ('rail_1915_traces', 'feature_id'),
            ('rail_1915_controls', 'feature_id'), ('road_1893_traces', 'feature_id'),
            ('rail_1893_traces', 'feature_id'), ('ferguson_towns_1893', 'feature_id'),
            ('road_rail_crossings_1925', 'feature_id'),
            ('road_inventory_1928', 'record_id'), ('road_works_1928', 'work_id'),
            ('motor_amenity_listings_1936', 'feature_id'),
            ('motor_amenity_observations_1936', 'observation_id'),
            ('motor_amenity_places_1936', 'feature_id'),
            ('road_alignment_review', 'review_id'), ('reviewed_historical_bridges', 'feature_id'),
            ('historical_wikidata_places', 'feature_id'),
            ('gazetteer_1834_attestations', 'attestation_id'),
            ('gazetteer_1834_points', 'feature_id'), ('gazetteer_1834_index', 'entry_id'),
        ]:
            con.execute(f'CREATE UNIQUE INDEX {table}_key ON {table}({fields})')
        con.execute('CREATE INDEX census_unit_year ON census_observations(feature_id,year,metric)')
        con.execute('CREATE UNIQUE INDEX historical_wikidata_qid ON historical_wikidata_places(qid)')
        assert con.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert not con.execute('''
            SELECT l.evidence_id FROM transport_evidence_links l
            LEFT JOIN transport_evidence e USING (evidence_id) WHERE e.evidence_id IS NULL
        ''').fetchall()
        assert not con.execute('''
            SELECT o.feature_id FROM census_observations o
            LEFT JOIN census_units u USING (feature_id) WHERE u.feature_id IS NULL
        ''').fetchall()
        assert not con.execute('''
            SELECT b.opening_evidence_id FROM reviewed_historical_bridges b
            LEFT JOIN transport_evidence e ON b.opening_evidence_id = e.evidence_id
            WHERE e.evidence_id IS NULL
        ''').fetchall()


def build():
    with TemporaryDirectory(prefix='.historical-gis-', dir=HERE) as directory:
        temp = Path(directory) / 'ceylon-history.gpkg'
        write_package(temp)
        temp.replace(HERE / temp.name)


if __name__ == '__main__':
    try:
        build()
    finally:
        WGS84 = None
