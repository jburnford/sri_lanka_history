"use strict";

const byId = (id) => document.getElementById(id);
const files = new Map();
const activeLayers = new Map();
const collections = new Map();
let searchIndex = null;
let searchIndexLoading = null;
let mapInitialized = false;
const EMPTY_TILE = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7";
const instant = new Intl.NumberFormat("en", { maximumFractionDigits: 4 });
const label = (key) => String(key || "").replaceAll("_", " ").replace(/^./, (c) => c.toUpperCase());
const isYearField = (field) => typeof field === "string" && /(^|[_\s])year$/i.test(field);
const printable = (value, field) => typeof value === "number"
  ? (isYearField(field) ? String(value) : instant.format(value))
  : String(value ?? "—");
const nameOf = (p) => p.historical_corridor || p.name || p.name_key || p.historical_name || p.place_as_printed || p.feature_id || "Unnamed feature";
const normalized = (s) => String(s ?? "").normalize("NFKD").replace(/\p{Diacritic}/gu, "").toLowerCase();
const featureId = (f) => String(f.properties.feature_id);
const coordKey = (f) => f.geometry?.type === "Point" ? f.geometry.coordinates.slice(0, 2).join(",") : "";
const COUNTRY = "country:ceylon";
const PAGE_SIZE = 40;
const countryBounds = [[5.86, 79.42], [9.88, 82.06]];
const shortlist = new Set(["Jaffna", "Colombo", "Kandy", "Galle", "Batticaloa", "Trincomalee", "Anuradhapura", "Badulla", "Polonnaruwa"]);
let atlas;
let map;
let view = "map";
let selection;
let highlight;
let renderVersion = 0;
let recordVersion = 0;
let recordPage = 0;
let filtered = [];
let selectedDataset;
let layerEpoch = new Map();
let mapNoteTimer;

function elt(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function add(parent, tag, text, className) {
  const node = elt(tag, text, className);
  parent.append(node);
  return node;
}

function request(filename) {
  if (!files.has(filename)) {
    files.set(filename, fetch("data/" + filename).then((response) => {
      if (!response.ok) throw new Error(filename + " could not be loaded.");
      return response.json();
    }).catch((error) => {
      files.delete(filename);
      throw error;
    }));
  }
  return files.get(filename);
}

const records = (id) => request(id + ".records.json");
const getLayer = (id) => atlas.layers.find((layer) => layer.id === id);
const getRaster = (id) => atlas.rasters.find((layer) => layer.id === id);
const safeUrl = (value) => {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  } catch { return null; }
};

function link(parent, url, text) {
  const target = safeUrl(url);
  if (!target) return;
  const a = add(parent, "a", text);
  a.href = target;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  return a;
}

function action(parent, text, handler, className = "text-button") {
  const button = add(parent, "button", text, className);
  button.type = "button";
  button.addEventListener("click", handler);
  return button;
}

function details(parent, items) {
  const dl = add(parent, "dl", undefined, "detail-list");
  for (const [name, value] of items) {
    if (value === null || value === undefined || value === "") continue;
    add(dl, "dt", name);
    const dd = add(dl, "dd");
    if (safeUrl(value)) link(dd, value, "Open reference ↗");
    else dd.textContent = printable(value, name);
  }
  return dl;
}

function note(text) {
  const node = byId("map-note");
  node.textContent = text;
  node.hidden = false;
  clearTimeout(mapNoteTimer);
  mapNoteTimer = setTimeout(() => { node.hidden = true; }, 6500);
}

function makeMap() {
  map = L.map("map", { zoomSnap: 0.25, zoomDelta: 0.5, minZoom: 5, maxZoom: 17 });
  map.attributionControl.setPrefix(false);
  map.attributionControl.addAttribution('<a href="https://www.openstreetmap.org/copyright">© OpenStreetMap contributors</a>');
  for (const [name, z] of [["relief", 230], ["paper", 406], ["grid", 240], ["boundary", 380], ["route", 420], ["markers", 440], ["towns", 450], ["selected", 480]]) {
    const pane = map.createPane(name);
    pane.style.zIndex = z;
  }
  L.control.scale({ imperial: false, maxWidth: 110 }).addTo(map);
  const gridStyle = { weight: 1, color: "#73999a", opacity: .27, dashArray: "2 5", interactive: false, pane: "grid" };
  for (let longitude = 78; longitude <= 84; longitude += 0.5) {
    L.polyline([[4, longitude], [11, longitude]], gridStyle).addTo(map);
  }
  for (let latitude = 4; latitude <= 11; latitude += 0.5) {
    L.polyline([[latitude, 78], [latitude, 84]], gridStyle).addTo(map);
  }
  fitIsland();
  byId("fit-island").addEventListener("click", fitIsland);
}

function fitIsland() {
  map.fitBounds(countryBounds, { padding: [20, 20], animate: false });
}

function layerStyle(meta, feature) {
  if (meta.group === "Boundaries") {
    const district = meta.id === "district_census_1946" || meta.id === "headmen_divisions_1934";
    return { color: meta.color, weight: district ? 1 : 1.35, fillColor: "#f4e9d5", fillOpacity: district ? (reliefShown() ? .04 : .15) : reliefShown() ? .22 : .96, opacity: .84, pane: "boundary" };
  }
  const ferry = feature.properties.mode === "ferry";
  const candidate = meta.id.includes("candidate");
  return {
    color: ferry ? "#775b88" : meta.color,
    weight: ferry ? 2.6 : meta.id === "road_ferry_chronology" ? 1.8 : 2,
    opacity: candidate ? .63 : .91,
    dashArray: ferry ? "4 4" : candidate ? "3 4" : null,
    pane: "route",
  };
}

function vector(meta, collection) {
  const towns = meta.id === "urban_census";
  const markerStyle = {
    pane: towns ? "towns" : "markers",
    radius: towns ? 4 : 3.4,
    color: "#fff9ec",
    weight: 1.35,
    fillColor: meta.color,
    fillOpacity: .97,
  };
  let amenitiesAt;
  if (meta.id === "motor_amenity_places_1936") {
    amenitiesAt = new Map();
    for (const f of collection.features) {
      const k = coordKey(f);
      if (!k) continue;
      const kinds = amenitiesAt.get(k) || [];
      if (f.properties.facility_kind) kinds.push(label(f.properties.facility_kind));
      amenitiesAt.set(k, kinds);
    }
  }
  return L.geoJSON(collection, {
    pane: meta.points ? markerStyle.pane : meta.group === "Boundaries" ? "boundary" : "route",
    style: (feature) => meta.points ? markerStyle : layerStyle(meta, feature),
    pointToLayer: (_, coordinate) => L.circleMarker(coordinate, markerStyle),
    onEachFeature(feature, layer) {
      const title = nameOf(feature.properties);
      const atlasLabel = feature.properties.anchor_name || title;
      const permanent = meta.id === "urban_census" && shortlist.has(atlasLabel);
      let tip = permanent ? atlasLabel : title;
      if (amenitiesAt) {
        const kinds = [...new Set(amenitiesAt.get(coordKey(feature)) || [])];
        if (kinds.length) tip = title + " (" + kinds.join(", ") + ")";
      }
      layer.bindTooltip(elt("span", tip), permanent
        ? { permanent: true, direction: "right", offset: [6, 0], className: "town-label" }
        : { sticky: true, className: "feature-tip" });
      layer.on("click", (event) => {
        L.DomEvent.stopPropagation(event);
        selectFeature(meta, feature, false);
      });
    },
  });
}

function geometry(id) {
  return request(id + ".json").then((collection) => {
    collections.set(id, collection);
    return collection;
  });
}

function hasTile(ranges, z, x, y) {
  const runs = ranges?.[String(z)]?.[String(x)];
  if (!runs) return false;
  for (let i = 0; i < runs.length; i += 2) {
    if (y >= runs[i] && y <= runs[i + 1]) return true;
  }
  return false;
}

function rasterLayer(id, raster) {
  const rumsey = '<a href="https://www.davidrumsey.com/about/copyright-and-permissions">David Rumsey Map Collection, Stanford University Libraries</a>';
  const options = {
    opacity: raster.base ? 1 : .82, pane: raster.base ? "relief" : "paper",
    attribution: raster.attribution || rumsey,
  };
  if (!raster.tiles) return L.imageOverlay("data/" + id + ".webp", raster.bounds, { ...options, alt: raster.title });
  const layer = L.tileLayer(raster.tiles, {
    ...options, bounds: raster.bounds, minNativeZoom: raster.min_zoom, maxNativeZoom: raster.max_zoom, maxZoom: 17,
  });
  if (raster.tile_ranges) {
    const baseUrl = layer.getTileUrl.bind(layer);
    layer.getTileUrl = function (coords) {
      const z = this._getZoomForUrl();
      return hasTile(raster.tile_ranges, z, coords.x, coords.y) ? baseUrl(coords) : EMPTY_TILE;
    };
  }
  return layer;
}

// With the relief underneath, boundary fills thin out so the hills show through.
const reliefShown = () => atlas.rasters.some((raster) => raster.base && activeLayers.has(raster.id));

function restyleBoundaries() {
  for (const meta of atlas.layers) {
    if (meta.group === "Boundaries") activeLayers.get(meta.id)?.setStyle((feature) => layerStyle(meta, feature));
  }
}

async function toggle(id, show) {
  const epoch = (layerEpoch.get(id) || 0) + 1;
  layerEpoch.set(id, epoch);
  if (!show) {
    activeLayers.get(id)?.remove();
    activeLayers.delete(id);
    if (getRaster(id)?.base) restyleBoundaries();
    return;
  }
  if (activeLayers.has(id)) return;
  try {
    const raster = getRaster(id);
    const meta = getLayer(id);
    const layer = raster
      ? rasterLayer(id, raster)
      : vector(meta, await geometry(id));
    if (layerEpoch.get(id) !== epoch) return;
    layer.addTo(map);
    activeLayers.set(id, layer);
    if (raster?.base) restyleBoundaries();
  } catch (error) {
    if (layerEpoch.get(id) === epoch) {
      const input = document.querySelector('[data-layer="' + id + '"]');
      if (input) input.checked = false;
      note(error.message);
    }
  }
}

function addLayerControls() {
  const root = byId("layer-list");
  root.replaceChildren();
  for (const group of ["Relief", "Boundaries", "Places", "Map sheets", "Town plans", "Transport"]) {
    const entries = [...atlas.layers, ...atlas.rasters].filter((item) => item.group === group);
    if (!entries.length) continue;
    const section = add(root, "details", undefined, "layer-group");
    section.open = true;
    add(section, "summary", group);
    for (const entry of entries) {
      const row = add(section, "label", undefined, "layer-row");
      row.title = entry.description;
      const check = add(row, "input");
      check.dataset.layer = entry.id;
      check.type = "checkbox";
      check.checked = entry.visible;
      check.addEventListener("change", () => toggle(entry.id, check.checked));
      const swatch = add(row, "span", undefined, "swatch");
      swatch.style.setProperty("--swatch", entry.color ?? "#aa8751");
      if (entry.points) swatch.classList.add("points");
      if (group === "Boundaries" || group === "Map sheets" || group === "Town plans" || group === "Relief") swatch.classList.add("area");
      const title = add(row, "span", entry.title);
      if (entry.id === "rail_1936_osm") add(title, "small", "Working reconstruction");
      if (entry.id === "road_1936_osm_candidates") add(title, "small", "Modern comparison");
      if (entry.id === "road_1893_traces") add(title, "small", entry.count + " selected traces");
      if (entry.id === "gazetteer_1834_points") add(title, "small", entry.count + " grounded entries");
    }
    if (group === "Places" && getLayer("gazetteer_1834_points")) {
      action(section, "Browse Gazetteer index →", () => openRecords("gazetteer_1834_index"));
    }
  }
  byId("reset-layers").addEventListener("click", resetLayers);
}

function resetLayers() {
  for (const entry of [...atlas.layers, ...atlas.rasters]) {
    const input = document.querySelector('[data-layer="' + entry.id + '"]');
    if (input) input.checked = Boolean(entry.visible);
    toggle(entry.id, Boolean(entry.visible));
  }
  peopleReset();
}

function updateHash(value, push = false) {
  const target = value ? "#" + value : location.pathname + location.search;
  if (push) history.pushState(null, "", target);
  else history.replaceState(null, "", target);
}

function selectFeature(meta, feature, zoom) {
  selection = { meta, feature };
  showView("map", false);
  highlight?.remove();
  highlight = L.geoJSON(feature, {
    pane: "selected", interactive: false,
    style: { color: "#832f22", weight: 4, opacity: .94, fillOpacity: .08 },
    pointToLayer: (_, ll) => L.circleMarker(ll, {
      pane: "selected", interactive: false, radius: 9, fill: false, weight: 2.5, color: "#832f22",
    }),
  }).addTo(map);
  if (zoom) {
    map.invalidateSize();
    map.fitBounds(highlight.getBounds().pad(.06), { maxZoom: meta.points ? 11 : 12, padding: [45, 45], animate: false });
  }
  updateHash("map=" + encodeURIComponent(meta.id) + "/" + encodeURIComponent(featureId(feature)));
  paintInspector();
  if (matchMedia("(max-width: 580px)").matches && !zoom) {
    byId("inspector").scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
}

function clearSelection() {
  selection = undefined;
  highlight?.remove();
  updateHash("map");
  paintInspector();
}

async function paintInspector() {
  const ticket = ++renderVersion;
  const root = byId("inspector");
  root.replaceChildren();
  const peopleBar = byId("people-jump");   // people.js: the phone bar pointing to a place's people list
  if (peopleBar) peopleBar.hidden = true;
  if (!selection) {
    add(root, "span", "Island overview", "tag");
    add(root, "h2", "Ceylon");
    add(root, "p", "Select a feature on the map or search for a place or route.", "help");
    await censusInspector(root, COUNTRY, ticket);
    return;
  }

  const { meta, feature } = selection;
  const p = feature.properties;
  add(root, "span", meta.title, "tag");
  add(root, "h2", nameOf(p));
  if (meta.id === "gazetteer_1834_points") {
    add(root, "p", p.modern_name, "help");
    details(root, [
      ["Gazetteer attestation", p.represented_date],
      ["Original publication", p.published_date],
      ["Variants", p.historical_aliases],
      ["Feature", p.category],
      ["Location", p.location_scope],
      ["Place match", p.grounding_note],
      ["Entry locator", p.source_locator],
      ["Coordinate locator", p.geometry_source_locator],
      ["Coordinate reference date", p.geometry_reference_date],
    ]);
    if (p.excerpt) {
      add(root, "h3", "Entry opening");
      add(root, "p", p.excerpt, "help");
    }
    const refs = add(root, "div", undefined, "inspector-links");
    link(refs, p.source_url, "Gazetteer page ↗");
    link(refs, p.geometry_source_url, "Coordinate source ↗");
    if (p.qid) link(refs, "https://www.wikidata.org/wiki/" + encodeURIComponent(p.qid), p.qid + " ↗");
    action(refs, "Island overview", clearSelection);
    return;
  }
  add(root, "p", p.significance || p.geometry_note || p.location_note || p.note || meta.description, "help");
  const info = [];
  if (meta.id === "headmen_divisions_1934") {
    info.push(
      ["Number in the printed key", p.key_number],
      ["Name on the administrative map", p.name_map7],
      ["District", p.district],
      ["Province", p.province],
      ["How the identity was read", p.identity_confidence],
      ["Note", p.note],
    );
  }
  if (meta.id === "motor_amenity_places_1936" && p.facility_kind) {
    info.push(["Facility", label(p.facility_kind)]);
  }
  info.push(
    ["Represented date", p.represented_date || p.map_year],
    ["Published date", p.published_date],
    ["Geometry", p.geometry_role || p.geometry_method || p.location_role || p.point_scope],
    ["Review", p.review_status || p.osm_match_status],
    ["Legend", p.legend_class],
    ["Coverage", p.coverage],
    ["Distance", p.length_km == null ? null : instant.format(p.length_km) + " km"],
    ["Source locator", p.source_locator],
  );
  details(root, info);
  const links = add(root, "div", undefined, "inspector-links");
  link(links, p.evidence_url || p.source_url || p.historical_map_url, "Historical source ↗");
  if (p.geometry_source_url && p.geometry_source_url !== p.source_url) link(links, p.geometry_source_url, "Geometry source ↗");
  if (p.qid) link(links, "https://www.wikidata.org/wiki/" + encodeURIComponent(p.qid), p.qid + " ↗");
  action(links, "Island overview", clearSelection);
  if (meta.id === "road_1893_traces" && getRaster("ferguson1893")) {
    action(links, "Show Ferguson’s map", () => {
      document.querySelector('[data-layer="ferguson1893"]').checked = true;
      toggle("ferguson1893", true);
    });
  }
  if ((meta.group === "Boundaries" && meta.id !== "headmen_divisions_1934") || meta.id === "urban_census") await censusInspector(root, p.feature_id, ticket);
  if (meta.group === "Transport" && p.corridor_id) await transportInspector(root, p.corridor_id, ticket);
  if (meta.id === "motor_amenity_places_1936") {
    const col = collections.get(meta.id) || await geometry(meta.id);
    if (ticket !== renderVersion) return;
    const hereKey = coordKey(feature);
    const colocated = hereKey
      ? col.features.filter((f) => coordKey(f) === hereKey)
      : [feature];
    const kindById = new Map(colocated.map((f) => [featureId(f), f.properties.facility_kind ? label(f.properties.facility_kind) : ""]));
    if (colocated.length > 1) {
      add(root, "h3", "Facilities at this place (" + colocated.length + ")");
      for (const item of colocated) {
        const ip = item.properties;
        const kind = ip.facility_kind ? label(ip.facility_kind) : nameOf(ip);
        observation(root, kind, ip.note || "", ip);
      }
    }
    const ids = new Set(colocated.map(featureId));
    const rows = (await records("motor_amenity_observations_1936")).filter((row) => ids.has(row.feature_id));
    if (ticket !== renderVersion || !rows.length) return;
    add(root, "h3", "Amenity observations");
    for (const row of rows) {
      const prefix = colocated.length > 1 && kindById.get(row.feature_id) ? kindById.get(row.feature_id) + " · " : "";
      observation(root, prefix + label(row.metric), printable(row.value, row.metric), row);
    }
  }
}

async function censusInspector(root, unit, ticket) {
  const [all, catalogue] = await Promise.all([records("census_observations"), records("source_catalogue")]);
  if (ticket !== renderVersion) return;
  const found = all.filter((row) => row.feature_id === unit);
  add(root, "h3", "Census observations");
  if (!found.length) {
    add(root, "p", "This feature has no linked census observations.", "help");
    return;
  }
  const names = new Map(catalogue.map((source) => [source.source_id, source.title]));
  const metricLabel = add(root, "label", "Metric");
  const metric = add(metricLabel, "select");
  for (const value of [...new Set(found.map((row) => row.metric))].sort()) {
    add(metric, "option", label(value)).value = value;
  }
  if (found.some((row) => row.metric === "population")) metric.value = "population";
  const sourceLabel = add(root, "label", "Census source");
  const sourceMenu = add(sourceLabel, "select");
  const chartRoot = add(root, "div");
  const selectedRoot = add(root, "div");
  const seriesRows = () => found.filter((row) => row.metric === metric.value);
  function sources() {
    sourceMenu.replaceChildren();
    add(sourceMenu, "option", "All census sources").value = "";
    for (const id of [...new Set(seriesRows().map((row) => row.source_id))]) {
      add(sourceMenu, "option", names.get(id) || id).value = id;
    }
    if (unit === COUNTRY && [...sourceMenu.options].some((option) => option.value === "census-1946-final")) {
      sourceMenu.value = "census-1946-final";
    }
    draw();
  }
  function draw() {
    const visible = seriesRows().filter((row) => !sourceMenu.value || row.source_id === sourceMenu.value)
      .sort((a, b) => a.year - b.year);
    chartRoot.replaceChildren();
    chart(chartRoot, visible, names, (row) => {
      selectedRoot.replaceChildren();
      observation(selectedRoot, String(row.year) + " · " + (names.get(row.source_id) || row.source_id),
        printable(row.value) + " " + (row.unit || ""), row);
      if (row.transcription_note) add(selectedRoot, "p", row.transcription_note, "help");
    });
  }
  metric.addEventListener("change", sources);
  sourceMenu.addEventListener("change", draw);
  sources();
  action(root, "Browse census records →", () => openRecords("census_observations", unit));
}

function svg(parent, tag, attrs) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  parent.append(node);
  return node;
}

function chart(root, rows, sourceNames, onSelect) {
  if (!rows.length) return;
  const years = [...new Set(rows.map((row) => row.year))];
  const values = rows.map((row) => Number(row.value));
  const low = Math.min(...values);
  const high = Math.max(...values);
  const margin = (high - low || Math.abs(high) * .1 || 1) * .10;
  const min = low - margin;
  const max = high + margin;
  const x = (row) => years.length === 1 ? 156 : 43 + (row.year - years[0]) / (years.at(-1) - years[0]) * 224;
  const y = (row) => 12 + (max - Number(row.value)) / (max - min) * 78;
  const colors = ["#276478", "#aa573d", "#7d567f", "#996718", "#47774c", "#4e567e", "#a2415b", "#675947"];
  const sourceIds = [...new Set(rows.map((row) => row.source_id))];
  if (sourceIds.length > 1) {
    const key = add(root, "div", undefined, "chart-key");
    sourceIds.forEach((id, i) => {
      const item = add(key, "div", undefined, "chart-key-item");
      const dot = add(item, "span");
      dot.style.background = colors[i % colors.length];
      item.append(sourceNames.get(id) || id);
    });
  }
  const s = svg(root, "svg", { class: "chart", viewBox: "0 0 282 110", role: "group", "aria-label": "Census observations by year. Select a point to read its source." });
  const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 2 });
  for (const [i, v] of [max, (min + max) / 2, min].entries()) {
    const yy = 12 + i * 39;
    svg(s, "line", { x1: 40, x2: 267, y1: yy, y2: yy, stroke: "#ded8ca" });
    svg(s, "text", { x: 2, y: yy + 3 }).textContent = compact.format(v);
  }
  const marked = years.length <= 5 ? years : [years[0], years[Math.floor(years.length / 2)], years.at(-1)];
  for (const year of marked) svg(s, "text", { x: x({ year }), y: 105, "text-anchor": "middle" }).textContent = year;
  const dots = [];
  for (const [i, id] of sourceIds.entries()) {
    const series = rows.filter((row) => row.source_id === id);
    const color = colors[i % colors.length];
    if (series.length > 1) svg(s, "polyline", {
      points: series.map((row) => x(row) + "," + y(row)).join(" "),
      stroke: color, "stroke-width": 2, fill: "none",
    });
    for (const row of series) {
      const point = svg(s, "circle", {
        cx: x(row), cy: y(row), r: 4, fill: color, tabindex: 0, role: "button",
        "aria-label": row.year + ", " + printable(row.value) + (row.unit ? " " + row.unit : "") + ", " + id,
      });
      svg(point, "title", {}).textContent = row.year + " · " + printable(row.value) + " · " + id;
      const select = () => {
        dots.forEach(({ point: dot }) => dot.classList.toggle("selected", dot === point));
        onSelect(row);
      };
      point.addEventListener("click", select);
      point.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          select();
        }
      });
      dots.push({ row, point, select });
    }
  }
  dots.sort((a, b) => b.row.year - a.row.year)[0]?.select();
}

function observation(parent, title, value, row) {
  const item = add(parent, "div", undefined, "record-item");
  add(item, "b", title);
  add(item, "div", value);
  const meta = [row.status, row.locator || row.source_locator].filter(Boolean).join(" · ");
  if (meta) add(item, "small", meta + " ");
  link(item, row.source_url, "Source ↗");
  return item;
}

async function transportInspector(root, corridor, ticket) {
  const [links, evidence] = await Promise.all([records("transport_evidence_links"), records("transport_evidence")]);
  if (ticket !== renderVersion) return;
  const ids = new Set(links.filter((row) => row.corridor_id === corridor).map((row) => row.evidence_id));
  const relevant = evidence.filter((row) => ids.has(row.evidence_id))
    .sort((a, b) => String(a.represented_date).localeCompare(String(b.represented_date)));
  if (!relevant.length) return;
  add(root, "h3", "Transport evidence");
  for (const row of relevant) {
    observation(root, [row.represented_date, label(row.event)].filter(Boolean).join(" · "),
      [row.name, row.details].filter(Boolean).join(" — "), row);
  }
}

function loadSearchIndex() {
  if (searchIndex) return Promise.resolve(searchIndex);
  if (!searchIndexLoading) {
    searchIndexLoading = request("search_index.json").then((rows) => {
      searchIndex = rows.map(([id, fid, title, sub, extras]) => ({
        id, fid, title, sub,
        normTitle: normalized(title),
        hay: normalized([title, sub, extras].filter(Boolean).join(" ")),
      }));
      if (!byId("search-results").hidden) paintSearch();
      return searchIndex;
    }).catch(() => {
      searchIndexLoading = null;
      return [];
    });
  }
  return searchIndexLoading;
}

function searchFeature(query) {
  const needle = normalized(query).trim();
  if (!needle || !searchIndex) return [];
  const matches = [];
  for (const item of searchIndex) {
    if (!item.hay.includes(needle)) continue;
    const meta = getLayer(item.id);
    if (!meta) continue;
    const exact = item.normTitle === needle;
    matches.push({
      meta, item,
      rank: exact ? 0 : item.normTitle.startsWith(needle) ? 1 : 2,
    });
  }
  return matches.sort((a, b) => a.rank - b.rank || a.item.title.localeCompare(b.item.title) || a.item.sub.localeCompare(b.item.sub)).slice(0, 12);
}

function paintSearch() {
  const field = byId("place-search");
  const menu = byId("search-results");
  menu.replaceChildren();
  const query = field.value.trim();
  menu.hidden = !query;
  if (!query) return;
  if (!searchIndex) {
    add(menu, "button", "Loading search index…").disabled = true;
    loadSearchIndex();
    return;
  }
  const shown = searchFeature(query);
  for (const { meta, item } of shown) {
    const button = action(menu, item.title, async () => {
      menu.hidden = true;
      field.value = item.title;
      try {
        const col = await geometry(meta.id);
        const feature = col.features.find((f) => featureId(f) === item.fid);
        if (!feature) return note("That feature could not be found.");
        const check = document.querySelector('[data-layer="' + meta.id + '"]');
        if (check) check.checked = true;
        toggle(meta.id, true);
        selectFeature(meta, feature, true);
      } catch (error) { note(error.message); }
    }, "");
    add(button, "small", item.sub ? meta.title + " · " + item.sub : meta.title);
  }
  if (!shown.length) {
    add(menu, "button", "No matching map features.").disabled = true;
    // People are not map features: offer the same text to the People view (people.js)
    const toPeople = action(menu, "Search People for “" + query + "” →", () => {
      menu.hidden = true;
      history.pushState(null, "", "#people?q=" + encodeURIComponent(query));
      route();
      window.scrollTo(0, 0);
    }, "");
    add(toPeople, "small", "Officials, directory people and de Silva’s History");
  }
}

function bindSearch() {
  const field = byId("place-search");
  const list = byId("search-results");
  field.addEventListener("input", paintSearch);
  field.addEventListener("focus", () => { loadSearchIndex(); paintSearch(); });
  field.addEventListener("keydown", (event) => {
    if (event.key === "Escape") list.hidden = true;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      list.querySelector("button:not(:disabled)")?.focus();
    }
    if (event.key === "Enter") {
      event.preventDefault();
      list.querySelector("button:not(:disabled)")?.click();
    }
  });
  list.addEventListener("keydown", (event) => {
    if (event.key === "Escape") { list.hidden = true; field.focus(); list.hidden = true; }
    if (event.key === "ArrowDown") { event.preventDefault(); event.target.nextElementSibling?.focus(); }
    if (event.key === "ArrowUp") { event.preventDefault(); (event.target.previousElementSibling || field).focus(); }
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".search-shell")) list.hidden = true;
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && view === "map" && !event.target.matches("input,select,textarea,[contenteditable]")) {
      event.preventDefault();
      field.focus();
    }
  });
}

function ensureMapInit() {
  if (mapInitialized) return;
  mapInitialized = true;
  makeMap();
  addLayerControls();
  peopleInit();   // people.js: adds the People group to the layer panel
  resetLayers();
}

function recordsHash() {
  const params = new URLSearchParams();
  if (selectedDataset && selectedDataset !== atlas.tables[0].id) params.set("dataset", selectedDataset);
  const q = byId("record-search").value.trim();
  if (q) params.set("q", q);
  const y = byId("record-year").value;
  if (y) params.set("year", y);
  if (recordPage) params.set("page", String(recordPage + 1));
  const text = params.toString();
  return "records" + (text ? "?" + text : "");
}

function showView(id, setHash = true, push = false) {
  view = id;
  document.querySelectorAll(".view").forEach((section) => { section.hidden = section.id !== "view-" + id; });
  document.querySelectorAll("[data-view]").forEach((button) => {
    if (button.dataset.view === id) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  if (id === "map") ensureMapInit();
  if (setHash) {
    if (id === "map" && selection) {
      updateHash("map=" + encodeURIComponent(selection.meta.id) + "/" + encodeURIComponent(featureId(selection.feature)), push);
    } else if (id === "map" && peoplePlaceShown()) updateHash("people-place=" + encodeURIComponent(people.place.id), push);
    else if (id === "records") updateHash(recordsHash(), push);
    else if (id === "bluebook") updateHash(bluebookHash(), push);
    else if (id === "people") updateHash(peopleHash(), push);
    else updateHash(id, push);
  }
  if (id === "map") {
    requestAnimationFrame(() => map.invalidateSize());
    if (setHash && !selection && !peoplePlaceShown() && !byId("inspector").querySelector(".tag")) paintInspector();
  }
  if (id === "records") paintRecords();
  if (id === "sources") paintSources();
  if (id === "bluebook" && setHash) bluebookShowSearch();
  if (id === "people" && setHash) peopleShowSearch();
}

function openRecords(id, query = "", push = true) {
  selectedDataset = id;
  byId("dataset").value = id;
  byId("record-search").value = query;
  byId("record-year").value = "";
  recordPage = 0;
  showView("records", true, push);
  window.scrollTo(0, 0);
}

function recordYear(row) {
  return String(row.year ?? row.event_year ?? row.represented_date ?? row.start_date ?? row.published_date ?? "").match(/^\d{4}/)?.[0] || "";
}

async function paintRecords() {
  const ticket = ++recordVersion;
  const meta = atlas.tables.find((item) => item.id === selectedDataset) || atlas.tables[0];
  const yearMenu = byId("record-year");
  const query = normalized(byId("record-search").value).trim();
  const rows = await records(meta.id);
  if (ticket !== recordVersion) return;
  const year = yearMenu.dataset.pendingYear || yearMenu.value;
  delete yearMenu.dataset.pendingYear;
  yearMenu.replaceChildren();
  add(yearMenu, "option", "All years").value = "";
  for (const y of [...new Set(rows.map(recordYear).filter(Boolean))].sort()) add(yearMenu, "option", y).value = y;
  if ([...yearMenu.options].some((option) => option.value === year)) yearMenu.value = year;
  filtered = rows.filter((row) => (!yearMenu.value || recordYear(row) === yearMenu.value)
    && (!query || normalized(Object.values(row).join(" ")).includes(query)));
  recordPage = Math.min(recordPage, Math.max(0, Math.ceil(filtered.length / PAGE_SIZE) - 1));
  const head = byId("record-head");
  const body = byId("record-body");
  head.replaceChildren();
  body.replaceChildren();
  const headings = add(head, "tr");
  for (const field of meta.fields) add(headings, "th", label(field)).scope = "col";
  if (!filtered.length) {
    const message = add(add(body, "tr"), "td", "No records match these filters.", "muted");
    message.colSpan = meta.fields.length;
  }
  const first = recordPage * PAGE_SIZE;
  for (const row of filtered.slice(first, first + PAGE_SIZE)) {
    const tr = add(body, "tr");
    meta.fields.forEach((field, index) => {
      const td = add(tr, "td");
      if (index === 0) action(td, printable(row[field], field), () => showRecord(row, row[field] || meta.title), "table-open");
      else td.textContent = printable(row[field], field);
    });
  }
  byId("record-count").textContent = filtered.length
    ? (first + 1) + "–" + Math.min(first + PAGE_SIZE, filtered.length) + " of " + instant.format(filtered.length)
    : "0 records";
  byId("prev-page").disabled = recordPage === 0;
  byId("next-page").disabled = first + PAGE_SIZE >= filtered.length;
  byId("csv").disabled = filtered.length === 0;
}

function showRecord(row, title) {
  byId("record-title").textContent = title;
  const body = byId("record-details");
  body.replaceChildren();
  if (row.feature_id && selectedDataset === "gazetteer_1834_index") {
    action(body, "Show on map →", async () => {
      const id = "gazetteer_1834_points";
      const point = (await geometry(id)).features.find((item) => featureId(item) === row.feature_id);
      if (!point) return;
      byId("record-dialog").close();
      ensureMapInit();
      document.querySelector('[data-layer="' + id + '"]').checked = true;
      toggle(id, true);
      selectFeature(getLayer(id), point, true);
    });
  }
  details(body, Object.entries(row).filter(([key]) => key !== "components").map(([key, value]) => [label(key), value]));
  if (row.components) {
    add(body, "h3", "Components");
    const list = add(body, "ul");
    try {
      for (const part of JSON.parse(row.components)) {
        add(list, "li", [part.row, part.value === "" || part.value == null ? "missing" : part.value, part.locator].filter(Boolean).join(" · "));
      }
    } catch { add(list, "li", row.components); }
  }
  byId("record-dialog").showModal();
}

function downloadCSV() {
  if (!filtered.length) return;
  const fields = [...new Set(filtered.flatMap(Object.keys))];
  const quote = (value) => {
    const str = String(value ?? "");
    const safe = typeof value === "string" && /^[=+@-]/.test(str) && !/^-?\d+(?:\.\d+)?$/.test(str) ? "'" + str : str;
    return '"' + safe.replaceAll('"', '""') + '"';
  };
  const rows = [fields, ...filtered.map((row) => fields.map((key) => row[key]))];
  const blob = new Blob(["\ufeff", rows.map((row) => row.map(quote).join(",")).join("\r\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = elt("a");
  a.href = url;
  a.download = selectedDataset + ".csv";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function paintSources() {
  const rows = await records("source_catalogue");
  const target = byId("source-list");
  const query = normalized(byId("source-search").value).trim();
  target.replaceChildren();
  for (const row of rows) {
    if (query && !normalized(Object.values(row).join(" ")).includes(query)) continue;
    const card = add(target, "article", undefined, "source-card");
    add(card, "small", [label(row.kind), row.published_date, row.source_id].filter(Boolean).join(" · "));
    add(card, "h3", row.title);
    if (row.note) add(card, "p", row.note, "help");
    link(card, row.url, "Open source ↗");
  }
  if (!target.children.length) add(target, "p", "No sources match this search.", "help");
}

function bindViews() {
  // Moving between views (or leaving a detail page back to search) adds a history entry for the browser's Back button.
  document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => {
    const id = button.dataset.view;
    const leavingDetail = (id === "people" && Boolean(people.state.key))
      || (id === "bluebook" && !byId("bb-detail").hidden);
    if (id === "people") people.state.key = "";
    showView(id, true, id !== view || leavingDetail);
  }));
  document.querySelector(".brand").addEventListener("click", (event) => {
    event.preventDefault();
    showView("map");
    clearSelection();
    fitIsland();
  });
  const datasets = byId("dataset");
  for (const table of atlas.tables) add(datasets, "option", table.title).value = table.id;
  selectedDataset = atlas.tables[0].id;
  datasets.addEventListener("change", () => {
    selectedDataset = datasets.value;
    byId("record-search").value = "";
    byId("record-year").value = "";
    recordPage = 0;
    updateHash(recordsHash());
    paintRecords();
  });
  for (const id of ["record-search", "record-year"]) {
    byId(id).addEventListener(id === "record-search" ? "input" : "change", () => {
      recordPage = 0;
      updateHash(recordsHash());
      paintRecords();
    });
  }
  byId("prev-page").addEventListener("click", () => { recordPage--; updateHash(recordsHash()); paintRecords(); });
  byId("next-page").addEventListener("click", () => { recordPage++; updateHash(recordsHash()); paintRecords(); });
  byId("csv").addEventListener("click", downloadCSV);
  byId("source-search").addEventListener("input", paintSources);
  byId("verification-link").addEventListener("click", () => openRecords("census_reconciliation", "human review"));
  const gazetteer = byId("gazetteer-index-link");
  gazetteer.hidden = !getLayer("gazetteer_1834_points");
  gazetteer.addEventListener("click", () => openRecords("gazetteer_1834_index"));
}

async function start() {
  atlas = await request("atlas.json");
  bindViews();
  bindSearch();
  window.addEventListener("popstate", route);
  await route();
}

// Show the view named in the URL hash. Runs at start and whenever the browser moves through history.
async function route() {
  const hash = location.hash.slice(1);
  if (hash === "sources") return showView("sources", false);
  if (hash === "records" || hash.startsWith("records?")) {
    const params = new URLSearchParams(hash.includes("?") ? hash.slice(hash.indexOf("?") + 1) : "");
    const ds = params.get("dataset");
    selectedDataset = atlas.tables.some((t) => t.id === ds) ? ds : atlas.tables[0].id;
    byId("dataset").value = selectedDataset;
    byId("record-search").value = params.get("q") || "";
    const yearMenu = byId("record-year");
    yearMenu.dataset.pendingYear = params.get("year") || "";
    recordPage = Math.max(0, (parseInt(params.get("page"), 10) || 1) - 1);
    return showView("records", false);
  }
  if (hash.startsWith("bluebook")) {
    showView("bluebook", false);
    return bluebookRoute(hash);
  }
  if (hash.startsWith("people")) return peopleRoute(hash);
  if (hash.startsWith("map=")) {
    try {
      const [id, ref] = hash.slice(4).split("/").map(decodeURIComponent);
      const meta = getLayer(id);
      if (!meta || !ref) return showView("map", false);
      if (selection && selection.meta.id === id && featureId(selection.feature) === ref) return showView("map", false);
      ensureMapInit();
      const feature = (await geometry(id)).features.find((f) => featureId(f) === ref);
      if (feature) {
        document.querySelector('[data-layer="' + id + '"]').checked = true;
        toggle(id, true);
        selectFeature(meta, feature, true);
      } else showView("map", false);
    } catch { note("The linked feature could not be loaded."); }
    return;
  }
  showView("map", false);
  if (selection || peoplePlaceShown()) clearSelection();
  else paintInspector();
}

start().catch((error) => {
  byId("inspector").textContent = "The atlas could not start. " + error.message;
  byId("layer-list").textContent = "Reload the page to try again.";
});
