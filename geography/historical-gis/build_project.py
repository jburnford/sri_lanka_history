#!/usr/bin/env python3
"""Create the QGIS comparison project alongside its GeoPackage."""
import argparse
from pathlib import Path

from qgis.PyQt.QtGui import QColor, QFont, QPainter
from qgis.core import (
    Qgis, QgsApplication, QgsCategorizedSymbolRenderer, QgsContrastEnhancement, QgsCoordinateReferenceSystem,
    QgsFillSymbol, QgsLineSymbol, QgsMarkerSymbol, QgsPalLayerSettings, QgsProject,
    QgsRasterLayer, QgsRectangle, QgsReferencedRectangle, QgsRelation, QgsRendererCategory,
    QgsSingleBandGrayRenderer, QgsSingleSymbolRenderer, QgsTextBufferSettings, QgsTextFormat, QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
)

HERE = Path(__file__).resolve().parent
PKG = HERE / 'ceylon-history.gpkg'
PROJECT = HERE / 'ceylon-history.qgz'
NSDI_WMS = 'https://gisapps.nsdi.gov.lk/server/services/SLNSDI/Elevation/MapServer/WMSServer'
SRTM = Path('/mnt/data/jic823/ceylon_hgis_elevation/srtm_30m')
if not SRTM.exists():  # on another machine: made by fetch_elevation.sh
    SRTM = HERE.parent / 'elevation' / 'srtm_30m'
VAESSA_DEM = Path('/mnt/data/jic823/ceylon_hgis_elevation/vaessa_0_5m/VaeSSA_precise_DEM_0.5m_SLD99.img')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-wms', action='store_true', help='Build without the live NSDI connection')
    parser.add_argument('--dem', type=Path, default=VAESSA_DEM, help='Optional local VæSSA elevation raster')
    args = parser.parse_args()
    app = QgsApplication([], False)
    app.initQgis()
    project = QgsProject.instance()
    project.setTitle('Historical GIS of Ceylon')
    project.setFileName(str(PROJECT))
    project.setFilePathStorage(Qgis.FilePathType.Relative)
    project.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
    project.setBackgroundColor(QColor('#f1f6f8'))
    root = project.layerTreeRoot()
    places = root.addGroup('Historic sites')
    census = root.addGroup('Census')
    transport = root.addGroup('Transport chronology')
    historical = root.addGroup('Earlier map traces and control points')
    rasters = root.addGroup('Georeferenced source maps')
    terrain = root.addGroup('Modern elevation reference')
    tables = root.addGroup('Sources and evidence tables')

    def add(name, label, group, symbol=None, visible=True, display=None, optional=False):
        layer = QgsVectorLayer(f'{PKG}|layername={name}', label, 'ogr')
        if not layer.isValid():
            if optional:
                return None
            raise RuntimeError(f'Invalid layer {name}')
        if symbol:
            layer.setRenderer(QgsSingleSymbolRenderer(symbol))
        if display:
            if layer.fields().indexFromName(display) < 0:
                raise RuntimeError(f'Missing display field {name}.{display}')
            layer.setDisplayExpression(f'"{display}"')
        form = layer.editFormConfig()
        for identifier in ('feature_id', 'observation_id', 'evidence_id', 'check_id', 'attestation_id'):
            index = layer.fields().indexFromName(identifier)
            if index >= 0:
                form.setReadOnly(index, True)
        layer.setEditFormConfig(form)
        project.addMapLayer(layer, False)
        node = group.addLayer(layer)
        node.setItemVisibilityChecked(visible)
        node.setExpanded(False)
        return layer

    def raster(file, label):
        layer = QgsRasterLayer(str(HERE.parent / file), label, 'gdal')
        if not layer.isValid():
            raise RuntimeError(f'Invalid raster {file}')
        project.addMapLayer(layer, False)
        node = rasters.addLayer(layer)
        node.setItemVisibilityChecked(False)
        node.setExpanded(False)

    def add_wms_layers():
        for key, title, scale in (
            ('4', 'NSDI contours', 188988.095238),
            ('3', 'NSDI spot heights', 23623.511905),
            ('2', 'NSDI elevation regime', 23623.511905),
        ):
            uri = (f'crs=EPSG:4326&format=image/png&layers={key}'
                   f'&styles=default&url={NSDI_WMS}')
            layer = QgsRasterLayer(uri, title, 'wms')
            if not layer.isValid():
                print(f'Unable to load {title}: {layer.error().summary()}')
                continue
            layer.setScaleBasedVisibility(True)
            layer.setMinimumScale(scale)
            describe(layer, f'Modern Sri Lanka NSDI elevation WMS layer {key}. '
                            f'Visible when zoomed to approximately 1:{scale:,.0f} or closer. '
                            'This service supplies rendered images for display.')
            project.addMapLayer(layer, False)
            node = terrain.addLayer(layer)
            node.setItemVisibilityChecked(False)
            node.setExpanded(False)

    def add_local_dem(path):
        if not path.is_file():
            return
        layer = QgsRasterLayer(str(path.resolve()), 'VæSSA elevation raster (0.5 m, eastern Sri Lanka)', 'gdal')
        if not layer.isValid():
            print(f'Unable to load local DEM: {layer.error().summary()}')
            return
        provider = layer.dataProvider()
        renderer = QgsSingleBandGrayRenderer(provider, 1)
        contrast = QgsContrastEnhancement(provider.dataType(1))
        contrast.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum)
        contrast.setMinimumValue(-3)
        contrast.setMaximumValue(120)
        renderer.setContrastEnhancement(contrast)
        layer.setRenderer(renderer)
        describe(layer, 'World Bank/ESA VæSSA 0.5 m Pléiades elevation raster. '
                        'Actual coverage is an eastern Sri Lanka footprint near Ampara. '
                        'The 0.5 m value is grid spacing, distinct from reported vertical accuracy.')
        project.addMapLayer(layer, False)
        node = terrain.addLayer(layer)
        node.setItemVisibilityChecked(False)
        node.setExpanded(False)

    def add_srtm(folder):
        dem, shade = folder / 'ceylon_srtm_30m.tif', folder / 'ceylon_srtm_30m_hillshade.tif'
        if not (dem.is_file() and shade.is_file()):
            return
        note = ('SRTM 30 m surface (survey of February 2000) from the Tilezen terrain tiles. A modern surface: '
                'reservoirs and other works later than the historical layers are in it. Sea is no data.')
        layer = QgsRasterLayer(str(dem), 'Elevation, SRTM 30 m (metres)', 'gdal')
        if layer.isValid():
            provider = layer.dataProvider()
            renderer = QgsSingleBandGrayRenderer(provider, 1)
            contrast = QgsContrastEnhancement(provider.dataType(1))
            contrast.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum)
            contrast.setMinimumValue(0)
            contrast.setMaximumValue(2524)
            renderer.setContrastEnhancement(contrast)
            layer.setRenderer(renderer)
            describe(layer, note + ' Values are metres above sea level; use this layer for heights and slopes.')
            project.addMapLayer(layer, False)
            node = terrain.addLayer(layer)
            node.setItemVisibilityChecked(False)
            node.setExpanded(False)
        layer = QgsRasterLayer(str(shade), 'Relief shading, SRTM 30 m', 'gdal')
        if layer.isValid():
            layer.setBlendMode(QPainter.CompositionMode_Multiply)     # shades whatever is drawn beneath it
            layer.setOpacity(0.6)
            describe(layer, note + ' Drawn over the other layers with a multiply blend.')
            project.addMapLayer(layer, False)
            node = root.insertLayer(0, layer)
            node.setItemVisibilityChecked(True)
            node.setExpanded(False)

    def line(color, width, style='solid'):
        return QgsLineSymbol.createSimple({'line_color': color, 'line_width': str(width), 'line_style': style})

    def marker(color, size):
        return QgsMarkerSymbol.createSimple({
            'color': color, 'size': str(size), 'outline_color': '#ffffff', 'outline_width': '0.25',
        })

    def relate(key, title, parent, child, field, child_field=None):
        relation = QgsRelation()
        relation.setId(key)
        relation.setName(title)
        relation.setReferencedLayer(parent.id())
        relation.setReferencingLayer(child.id())
        relation.addFieldPair(child_field or field, field)
        if not relation.isValid():
            raise RuntimeError(f'Invalid QGIS relation {key}')
        project.relationManager().addRelation(relation)

    def describe(layer, summary):
        metadata = layer.metadata()
        metadata.setTitle(layer.name())
        metadata.setAbstract(summary)
        layer.setMetadata(metadata)

    def order_table(layer, first, sort_by=None):
        config = layer.attributeTableConfig()
        config.update(layer.fields())
        columns = config.columns()
        priority = {field: index for index, field in enumerate(first)}
        missing = priority.keys() - {column.name for column in columns}
        if missing:
            raise RuntimeError(f'Missing fields in {layer.name()}: {sorted(missing)}')
        columns.sort(key=lambda column: priority.get(column.name, len(priority)))
        for column in columns:
            if column.name == 'fid':
                column.hidden = True
        config.setColumns(columns)
        if sort_by:
            config.setSortExpression(sort_by)
        layer.setAttributeTableConfig(config)

    sites = add('historical_wikidata_places', 'Historic sites (reviewed Wikidata points)',
                places, visible=False, display='name')
    sites.setRenderer(QgsCategorizedSymbolRenderer('category', [
        QgsRendererCategory(k, marker(color, 3.2), label) for k, color, label in (
            ('archaeology', '#996021', 'Archaeology and royal sites'),
            ('religion', '#824486', 'Sacred places'),
            ('fortification', '#98533d', 'Fortifications'),
            ('institution', '#356887', 'Institutions'),
            ('plantation economy', '#3d7245', 'Plantation economy'),
            ('transport', '#415168', 'Transport landmarks'),
        )
    ]))
    describe(sites, 'Source reviewed historical sites and roles. Coordinates are modern Wikidata points or '
                    'representative locations. The reported historical date and the coordinate snapshot are separate.')
    order_table(sites, ('name', 'qid', 'category', 'represented_date', 'date_basis', 'significance',
                        'point_scope', 'source_locator', 'source_url', 'geometry_source_url', 'feature_id'), '"name"')
    chitty = add('gazetteer_1834_points', 'Casie Chitty Gazetteer, 1834 (grounded places)', places,
                 marker('#268176', 2.7), visible=False, display='historical_name')
    describe(chitty, 'Modern reference locations for entries in the 1834 Gazetteer. Read each location scope '
                     'and grounding note alongside the entry link and the coordinate source.')
    order_table(chitty, ('historical_name', 'modern_name', 'category', 'location_scope', 'qid',
                         'source_locator', 'grounding_note', 'source_url', 'geometry_source_url'), '"historical_name"')
    urban = add('urban_census', 'Towns and cities (representative locations)', census,
                marker('#1e6252', 2.9), display='name')
    format_ = QgsTextFormat()
    format_.setFont(QFont('Sans Serif', 9))
    format_.setSize(9)
    format_.setColor(QColor('#173d34'))
    buffer = QgsTextBufferSettings()
    buffer.setEnabled(True)
    buffer.setSize(0.7)
    buffer.setColor(QColor('#fffefb'))
    format_.setBuffer(buffer)
    urban_labels = QgsPalLayerSettings()
    urban_labels.fieldName = ("CASE WHEN \"feature_id\" IN ('urban:colombo', 'urban:kandy', 'urban:galle') "
                              'OR @map_scale < 900000 THEN "name" END')
    urban_labels.isExpression = True
    urban_labels.setFormat(format_)
    urban.setLabeling(QgsVectorLayerSimpleLabeling(urban_labels))
    urban.setLabelsEnabled(True)
    province = add('province_census', 'Provinces (approximate 1936 boundaries)', census,
                   QgsFillSymbol.createSimple({
                       'color': '#f7f2e6', 'outline_color': '#9d9584', 'outline_width': '0.3',
                   }), display='name')
    province_1946 = add('province_census_1946', 'Provinces (approximate 1946 census map boundaries)', census,
                        QgsFillSymbol.createSimple({
                            'style': 'no', 'outline_color': '#506987', 'outline_width': '0.52',
                        }), visible=False, display='name', optional=True)
    if province_1946 is not None:
        describe(province_1946, 'Generalized provincial boundaries assembled from the related district traces. '
                                'Related census observations retain their own dates and enumeration scopes.')
    district = add('district_census_1946', 'Revenue districts (approximate 1946 traces)', census,
                   QgsFillSymbol.createSimple({
                       'style': 'no', 'outline_color': '#785b3c', 'outline_width': '0.36',
                   }), visible=False, display='name', optional=True)
    if district is not None:
        describe(district, 'Generalized revenue districts represented in the Census of Ceylon, 1946. '
                           'The Survey Department map was printed in July 1950. '
                           'Related census observations retain their own dates and enumeration scopes.')
    headmen = add('headmen_divisions_1934', "Chief Headmen's divisions (1934, from the malaria report maps)", census,
                  QgsFillSymbol.createSimple({
                      'style': 'no', 'outline_color': '#8a3d6b', 'outline_width': '0.3',
                  }), visible=True, display='name_key', optional=True)
    if headmen is not None:
        describe(headmen, "Chief Headmen's divisions traced from Map 7 of the 1935 malaria report supplement, "
                          'numbered and named from Map 17 and its key. A 24 miles to an inch plate: lines are good '
                          'to a few km. Check identity_confidence and note on each division.')
    district_join = add('district_census_1946_join', 'Revenue districts for joins (1946 traces grown 5 km seaward)',
                        census, QgsFillSymbol.createSimple({
                            'style': 'no', 'outline_color': '#b08a5a', 'outline_width': '0.26',
                            'outline_style': 'dash',
                        }), visible=False, display='name', optional=True)
    if district_join is not None:
        describe(district_join, 'For point-in-polygon joins only. Each traced district is grown 5 km seaward, '
                                'never into another district; the seaward strip is not on the 1950 sheet. '
                                'For towns, use the printed district in the urban census layer.')
    roads = add('road_ferry_chronology', '1936 road and ferry traces with earlier evidence', transport,
                display='historical_corridor')
    roads.setRenderer(QgsCategorizedSymbolRenderer('mode', [
        QgsRendererCategory('road', line('#9b3928', 0.48), 'Road'),
        QgsRendererCategory('ferry', line('#17737d', 0.62, 'dash'), 'Ferry'),
        QgsRendererCategory(None, line('#675b55', 0.35), 'Unclassified'),
    ]))
    candidates = add('road_1936_osm_candidates', '1936 road candidates (modern OSM geometry)', transport,
                     line('#aa4e33', 0.36), False, 'historical_corridor')
    rails = add('rail_1936_osm', '1936 railway candidates (modern OSM geometry)', transport,
                line('#354775', 0.38), True, 'historical_corridor')
    bridges = add('reviewed_historical_bridges', 'Reviewed historical bridge alignments', transport,
                  line('#67415c', 0.95), visible=False, display='name', optional=True)
    motor_places = add('motor_amenity_places_1936', '1936 travel amenities (locality or station points)',
                       transport, visible=False, display='place_as_printed', optional=True)
    if motor_places is not None:
        categories = []
        for kind, label, shape, color in (
            ('rest_house', 'Rest house (representative locality)', 'square', '#835034'),
            ('petrol_depot', 'Petrol depot (representative locality)', 'diamond', '#ab6320'),
            ('railway_car_booking', 'Motor-car booking (station or representative locality)', 'circle', '#354775'),
        ):
            symbol = QgsMarkerSymbol.createSimple({
                'name': shape, 'color': color, 'size': '3.4', 'outline_color': '#ffffff',
                'outline_width': '0.3',
            })
            categories.append(QgsRendererCategory(kind, symbol, label))
        motor_places.setRenderer(QgsCategorizedSymbolRenderer('facility_kind', categories))
        describe(motor_places, 'Locations use modern gazetteer coordinates. The location role of each feature '
                               'records whether the point represents a locality or the named station. '
                               'The related rows contain source-dated observations.')
    add('road_1893_traces', '1893 Ferguson roads (selected traces)', historical,
        line('#962249', 0.75), False, 'name')
    add('rail_1893_traces', '1893 Ferguson railways', historical,
        line('#6660a3', 0.75), False, 'name')
    add('ferguson_towns_1893', '1893 Ferguson towns', historical,
        marker('#744364', 2.5), False, 'name')
    road_1915 = add('road_1915_traces', '1915 roads (schematic traces)', historical,
                    line('#a85c1a', 0.65, 'dash'), visible=False, display='name', optional=True)
    rail_1915 = add('rail_1915_traces', '1915 railways (schematic, including closed branches)', historical,
                    line('#205e56', 0.75, 'dash'), False, 'name')
    rail_1915_osm = add('rail_1915_osm_candidates', 'Ragama–Chilaw rail comparison (modern OSM geometry)',
                        historical, line('#46623f', 0.46), visible=False, display='name', optional=True)
    add('rail_1915_controls', '1915 control points and position errors', historical,
        marker('#8f301b', 3), False, 'name')
    raster('motor-map-1936/ceylon-motor-map-1936.tif', 'Survey Department Motor Map (1936)')
    raster('ferguson-1893/ferguson-1893.tif', 'Ferguson map (1893)')
    if not args.no_wms:
        add_wms_layers()
    add_local_dem(args.dem)
    add_srtm(SRTM)
    units = add('census_units', 'Census units and Wikidata links', tables, display='name')
    observations = add('census_observations', 'Census observations by metric, date and source', tables,
                       display='source_name')
    verifier = add('census_reconciliation', 'Census sums and exceptions for review', tables, display='total_row')
    order_table(verifier, ('status', 'source_id', 'year', 'metric', 'total_row', 'printed_total',
                           'component_sum', 'difference', 'total_locator', 'source_url'), '"status"')
    attestations = add('gazetteer_1834_attestations', '1834 Gazetteer place and route evidence', tables,
                       display='name_as_printed')
    order_table(attestations, ('name_as_printed', 'place_match', 'qid', 'qid_scope', 'claim_type',
                               'claim', 'represented_date', 'published_date', 'locator', 'source_url'))
    chitty_index = add('gazetteer_1834_index', 'Casie Chitty Gazetteer entry index', tables,
                       display='name_as_printed')
    order_table(chitty_index, ('name_as_printed', 'grounding_status', 'place_match', 'qid', 'source_locator'))
    evidence = add('transport_evidence', 'Transport events and map observations', tables, display='name')
    links = add('transport_evidence_links', 'Transport evidence by corridor', tables)
    crossings = add('road_rail_crossings_1925', '1925 road and rail crossing schedule', tables,
                    display='description')
    inventory_1928 = add('road_inventory_1928', '1928 Blue Book roads open for traffic', tables,
                         display='name', optional=True)
    works_1928 = add('road_works_1928', '1928 Blue Book road construction expenditure', tables,
                     display='name', optional=True)
    motor_listings = add('motor_amenity_listings_1936', '1936 Motor Map travel amenity listings', tables,
                         display='place_as_printed', optional=True)
    motor_observations = add('motor_amenity_observations_1936', '1936 Motor Map amenity observations', tables,
                             optional=True)
    road_review = add('road_alignment_review', 'Historical road alignments reviewed against OSM', tables,
                      display='historical_name', optional=True)
    sources = add('source_catalogue', 'Source catalogue', tables, display='title')

    for key, name, vector in (
        ('road', 'Events and maps for this corridor', roads),
        ('osm_road', 'Events and maps for this corridor', candidates),
        ('rail_1936', 'Events and maps for this railway line', rails),
        ('rail_1915', 'Events and maps for this railway line', rail_1915),
    ):
        relate(key, name, vector, links, 'corridor_id')
    if road_1915 is not None:
        relate('road_1915', 'Events and maps for this road corridor', road_1915, links, 'corridor_id')
    if rail_1915_osm is not None:
        relate('rail_1915_osm', 'Events and maps for this railway line', rail_1915_osm, links, 'corridor_id')
    relate('province_census', 'Census observations for this province', province, observations, 'feature_id')
    relate('urban_census', 'Census observations for this town', urban, observations, 'feature_id')
    if province_1946 is not None:
        relate('province_census_1946', 'Census observations for this province', province_1946, observations, 'feature_id')
    if district is not None:
        relate('district_census', 'Census observations for this district', district, observations, 'feature_id')
    relate('unit_census', 'Census observations for this unit', units, observations, 'feature_id')
    relate('transport_places', 'Corridors linked to this record', evidence, links, 'evidence_id')
    relate('gazette_crossings', 'Crossings listed in this record', evidence, crossings, 'evidence_id')
    if works_1928 is not None and works_1928.fields().indexFromName('evidence_id') >= 0:
        relate('road_works_1928', 'Blue Book expenditure for this record', evidence, works_1928, 'evidence_id')
    if motor_observations is not None:
        if motor_places is not None:
            relate('motor_place_observations', 'Motor Map observations for this listing',
                   motor_places, motor_observations, 'feature_id')
        if motor_listings is not None:
            relate('motor_listing_observations', 'Motor Map observations for this listing',
                   motor_listings, motor_observations, 'feature_id')
    if bridges is not None and road_review is not None:
        relate('bridge_alignment_review', 'OSM ways reviewed for this bridge',
               bridges, road_review, 'feature_id', 'bridge_id')
        relate('bridge_openings', 'Bridge linked to this construction or opening record',
               evidence, bridges, 'evidence_id', 'opening_evidence_id')
    relate('transport_sources', 'Transport evidence from this source', sources, evidence, 'source_id')
    relate('census_sources', 'Census observations from this source', sources, observations, 'source_id')
    relate('historic_place_sources', 'Historic sites supported by this source', sources, sites, 'source_id')
    relate('gazetteer_1834_sources', 'References in the 1834 Gazetteer', sources, attestations, 'source_id')
    relate('gazetteer_1834_locations', 'Grounded locations for this entry', chitty_index, chitty, 'entry_id')

    order_table(observations, (
        'source_name', 'represented_date', 'metric', 'value', 'unit', 'status', 'source_id',
        'published_date', 'locator', 'source_url', 'feature_id', 'observation_id',
    ), '"represented_date"')
    order_table(units, ('name', 'unit_kind', 'qid', 'feature_id'))
    for layer in (urban, province):
        order_table(layer, ('name', 'qid', 'feature_id', 'represented_date', 'source_id'))
    order_table(crossings, ('description', 'rail_section', 'miles', 'chains', 'road_class'),
                '"miles" + "chains" / 80')
    root.setHasCustomLayerOrder(True)
    root.setCustomLayerOrder([sites, chitty] + [layer for layer in (motor_places, bridges) if layer is not None] +
                             [urban, roads, candidates, rails] +
                             [node.layer() for node in historical.findLayers()] +
                             [layer for layer in (province_1946, district) if layer is not None] +
                             [node.layer() for node in terrain.findLayers()] +
                             [node.layer() for node in rasters.findLayers()] + [province] +
                             [units, observations, verifier, attestations, chitty_index, evidence, links, crossings] +
                             [layer for layer in (inventory_1928, works_1928, motor_listings, motor_observations, road_review)
                              if layer is not None] + [sources])
    rasters.setExpanded(False)
    historical.setExpanded(False)
    terrain.setExpanded(False)
    tables.setExpanded(False)
    project.viewSettings().setDefaultViewExtent(
        QgsReferencedRectangle(
            QgsRectangle(79.32, 5.58, 82.22, 10.18), project.crs()
        )
    )
    if not project.write():
        raise RuntimeError(f'Could not save {PROJECT}')
    project.clear()
    app.exitQgis()


if __name__ == '__main__':
    main()
