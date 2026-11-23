"use strict";

// People view and People layer. Data: docs/data/people/, built by spine/people/build_atlas_people.py.
// Uses the helpers in atlas.js (byId, add, elt, action, link, details, normalized, note, showView, route).
//
// Kinds of record: "o" an official as printed in one Blue Book volume, "d" a person in a directory listing,
// "b" a person in the timeline read from de Silva's History; "x" is a pointer to a similar printed name.
// Records are grouped under a printed-name key (surname and initials). A group is not an identified person.

const PEOPLE_PAGE = 40;
const PEOPLE_COLOR = "#3f5f8a";
const peopleFiles = new Map();
const people = {
  summary: null, places: null, placeById: new Map(), index: null,
  layer: null, markers: new Map(), ring: null, year: "", shown: false,
  state: { q: "", kind: "", page: 0, key: "" }, results: [], version: 0, bound: false,
  place: { id: "", kind: "", page: 0, rows: null },
};

function peopleFetch(name) {
  if (!peopleFiles.has(name)) {
    peopleFiles.set(name, fetch("data/people/" + name).then(async (response) => {
      if (!response.ok) throw new Error("The people data (" + name + ") could not be loaded.");
      const bytes = new Uint8Array(await response.arrayBuffer());
      if (bytes[0] === 0x1f && bytes[1] === 0x8b) {   // a server may already have removed the gzip layer
        const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
        return JSON.parse(await new Response(stream).text());
      }
      return JSON.parse(new TextDecoder().decode(bytes));
    }).catch((error) => {
      peopleFiles.delete(name);
      throw error;
    }));
  }
  return peopleFiles.get(name);
}

async function peopleBase() {
  if (!people.places) {
    const [summary, places] = await Promise.all([peopleFetch("summary.json"), peopleFetch("places.json")]);
    people.summary = summary;
    people.places = places;
    for (const place of places) people.placeById.set(place.id, place);
  }
  return people;
}

// How far a record has been taken (set by build_atlas_people.py, stage()). The badge shows the furthest stage
// reached; it uses the look of the Blue Book confidence badges (styles.css .bb-level).
const PEOPLE_STAGES = {
  1: { title: "Read", key: "read from the page (and placed where named)", text: "Read from the page by program or language model, and placed where its office or listing names a place. Not joined to other records." },
  2: { title: "Joined", key: "one person joined across records", text: "Joined to other records as one person by a reviewed decision (made by a language model, sampled by a second reader)." },
  3: { title: "On the List", key: "matched to the Colonial Office List", text: "Matched to a Colonial Office List biography by program (surname, initials, dates); not checked by a person." },
  4: { title: "Identifier", key: "tied to an identifier", text: "Tied to a Wikidata identifier through its Colonial Office List match." },
};

function peopleStage(parent, stage) {
  const info = PEOPLE_STAGES[stage];
  if (!info) return null;
  const tag = add(parent, "span", info.title, "bb-level people-stage st-" + stage);
  tag.title = info.text;
  return tag;
}

function peopleStageKey(parent) {
  const line = add(parent, "p", "Stage reached: ", "people-stage-key");
  for (const [stage, info] of Object.entries(PEOPLE_STAGES)) {
    peopleStage(line, stage);
    line.append(" " + info.key + (stage === "4" ? "." : " · "));
  }
  return line;
}

const peopleYearLabel = (value) => value === "d" ? "Directory, 1921–22" : value === "b" ? "de Silva’s History (1981)" : value ? "Blue Book " + value : "All years";

// How many records a place has under the year filter: "" all, "d" directory only, "b" de Silva's History, or a Blue Book year.
function peopleCount(place) {
  if (!people.year) return place.o + place.d + (place.b || 0);
  if (people.year === "d") return place.d;
  if (people.year === "b") return place.b || 0;
  let total = 0;
  for (const [kind, year, n] of place.years) if (kind === "o" && String(year) === people.year) total += n;
  return total;
}

// ---- map layer -----------------------------------------------------------------------------------------------

async function peopleInit() {
  const root = byId("layer-list");
  const section = add(root, "details", undefined, "layer-group");
  section.open = true;
  add(section, "summary", "People");
  const row = add(section, "label", undefined, "layer-row");
  row.title = "Officials, directory people, and people in de Silva’s History, counted at the place their office, listing, or entry names.";
  const check = add(row, "input");
  check.type = "checkbox";
  check.id = "people-layer-check";
  check.addEventListener("change", () => peopleToggle(check.checked));
  const swatch = add(row, "span", undefined, "swatch points");
  swatch.style.setProperty("--swatch", PEOPLE_COLOR);
  const title = add(row, "span", "Officials, directory & History");
  add(title, "small", "By place named in the record");
  const yearRow = add(section, "label", "Show", "people-layer-year");
  const select = add(yearRow, "select");
  select.id = "people-layer-year";
  add(select, "option", "All years").value = "";
  select.addEventListener("change", () => {
    people.year = select.value;
    peopleRestyle();
    if (!people.shown) peopleToggle(true);   // choosing what to show means showing it
    if (peoplePlaceShown()) peoplePaintPlace();
  });
  action(section, "Search people by name →", () => showView("people", true, true));
  try {
    await peopleBase();
    add(select, "option", peopleYearLabel("d")).value = "d";
    if (people.summary.book) add(select, "option", peopleYearLabel("b")).value = "b";
    for (const year of people.summary.official_years) add(select, "option", peopleYearLabel(String(year))).value = String(year);
  } catch (error) { note(error.message); }
}

function peopleRadius(count) {
  return Math.min(24, 2.6 + Math.sqrt(count) / 5.2);
}

function peopleRestyle() {
  if (!people.layer) return;
  for (const [id, marker] of people.markers) {
    const count = peopleCount(people.placeById.get(id));
    if (count) {
      marker.setRadius(peopleRadius(count));
      if (!people.layer.hasLayer(marker)) people.layer.addLayer(marker);
    } else people.layer.removeLayer(marker);
  }
}

async function peopleToggle(show) {
  people.shown = show;
  byId("people-layer-check").checked = show;
  if (!show) {
    people.layer?.remove();
    return;
  }
  try {
    await peopleBase();
  } catch (error) {
    byId("people-layer-check").checked = false;
    people.shown = false;
    return note(error.message);
  }
  if (!people.layer) {
    people.layer = L.layerGroup();
    // Largest first, so that small places stay clickable on top of the large circles.
    for (const place of people.places) {
      const marker = L.circleMarker([place.lat, place.lon], {
        pane: "markers", radius: peopleRadius(place.o + place.d + (place.b || 0)), color: "#fff9ec", weight: 1,
        fillColor: PEOPLE_COLOR, fillOpacity: .5,
      });
      marker.bindTooltip(() => elt("span", place.name + " · " + peopleCount(place).toLocaleString("en") + " records"),
        { sticky: true, className: "feature-tip" });
      marker.on("click", (event) => {
        L.DomEvent.stopPropagation(event);
        peopleSelectPlace(place.id, false);
      });
      people.markers.set(place.id, marker);
      people.layer.addLayer(marker);
    }
    peopleRestyle();
  }
  if (people.shown) people.layer.addTo(map);
}

function peopleReset() {
  const select = byId("people-layer-year");
  if (select) select.value = "";
  people.year = "";
  if (byId("people-layer-check")) peopleToggle(false);
  if (peoplePlaceShown()) clearSelection();
}

// The atlas's own selection replaces `highlight`; while ours is still the highlight, a place is selected here.
function peoplePlaceShown() {
  return Boolean(people.ring && highlight === people.ring && map.hasLayer(people.ring));
}

async function peopleSelectPlace(id, zoom) {
  try { await peopleBase(); } catch (error) { return note(error.message); }
  const place = people.placeById.get(id);
  if (!place) return note("That place has no people records.");
  selection = undefined;
  showView("map", false);
  await peopleToggle(true);
  highlight?.remove();
  people.ring = highlight = L.circleMarker([place.lat, place.lon], {
    pane: "selected", interactive: false, radius: peopleRadius(peopleCount(place) || 1) + 5, fill: false, weight: 2.5, color: "#832f22",
  }).addTo(map);
  if (zoom) {
    map.invalidateSize();
    map.setView([place.lat, place.lon], Math.max(map.getZoom(), 10), { animate: false });
  }
  people.place = { id, kind: "", page: 0, rows: null };
  updateHash("people-place=" + encodeURIComponent(id));
  peoplePaintPlace();
}

// On a phone the panel sits below the map; a bar above the map says it is there (hidden by CSS on wider screens,
// and by atlas.js paintInspector when another selection takes the inspector over).
function peopleJump(place) {
  let bar = byId("people-jump");
  if (!bar) {
    bar = elt("button", "", "people-jump");
    bar.id = "people-jump";
    bar.type = "button";
    bar.addEventListener("click", () => byId("inspector").scrollIntoView({ block: "start" }));
    document.querySelector(".atlas").insertBefore(bar, document.querySelector(".map-shell"));
  }
  bar.textContent = "People named at " + place.name + ": " + peopleCount(place).toLocaleString("en") + " records. Go to the list ↓";
  bar.hidden = false;
}

async function peoplePaintPlace() {
  const ticket = ++renderVersion;   // takes the inspector over from atlas.js
  const root = byId("inspector");
  const place = people.placeById.get(people.place.id);
  root.replaceChildren();
  peopleJump(place);
  add(root, "span", "People named at this place", "tag");
  add(root, "h2", place.name);
  add(root, "p", "Officials, directory people, and people in de Silva’s History whose office, listing, or entry names this place. The place is the one printed in the record, which is usually but not always where the person lived or worked.", "help");
  details(root, [
    ["Officials (Blue Books 1863–1917)", place.o ? place.o.toLocaleString("en") + " name-and-volume records" : "none"],
    ["Directory people (1921–22)", place.d ? place.d.toLocaleString("en") + " roles" : "none"],
    ["In de Silva’s History", place.b ? place.b + (place.b === 1 ? " person" : " people") : ""],
    ["How the place was recognised", place.basis],
  ]);
  const filter = add(root, "div", undefined, "people-filter");
  const yearLabel = add(filter, "label", "Year");
  const year = add(yearLabel, "select");
  add(year, "option", "All years").value = "";
  if (place.d) add(year, "option", peopleYearLabel("d")).value = "d";
  if (place.b) add(year, "option", peopleYearLabel("b")).value = "b";
  for (const y of place.oy) add(year, "option", String(y)).value = String(y);
  year.value = people.year;
  if (year.value !== people.year) year.value = "";
  year.addEventListener("change", () => {
    people.year = year.value;
    const layerYear = byId("people-layer-year");
    if (layerYear) layerYear.value = people.year;
    peopleRestyle();
    people.place.page = 0;
    list();
  });
  const orderLabel = add(filter, "label", "Order");
  const order = add(orderLabel, "select");
  for (const [value, text] of [["new", "Latest year first"], ["old", "Earliest year first"], ["office", "By office"]]) add(order, "option", text).value = value;
  order.value = people.place.order || "new";
  order.addEventListener("change", () => { people.place.order = order.value; people.place.page = 0; list(); });
  const findLabel = add(filter, "label", "Name or office");
  const find = add(findLabel, "input");
  find.type = "search";
  find.placeholder = "e.g. Interpreter";
  find.addEventListener("input", () => { people.place.page = 0; list(); });
  const count = add(root, "p", "Loading…", "help");
  peopleStageKey(root);
  const ul = add(root, "ul", undefined, "people-list");
  const pager = add(root, "div", undefined, "inspector-links");
  const refs = add(root, "div", undefined, "inspector-links");
  if (place.qid) link(refs, "https://www.wikidata.org/wiki/" + encodeURIComponent(place.qid), place.qid + " ↗");
  action(refs, "Island overview", clearSelection);

  if (!people.place.rows) {
    try {
      const rows = await peopleFetch("place/" + place.id + ".json.gz");
      if (ticket !== renderVersion) return;
      people.place.rows = rows;
    } catch (error) {
      if (ticket === renderVersion) count.textContent = error.message;
      return;
    }
  }
  list();

  function list() {
    if (ticket !== renderVersion) return;
    const needle = normalized(find.value).trim();
    const rows = people.place.rows.filter(([kind, y, , name, office]) =>
      (!year.value || (year.value === "d" ? kind === "d" : year.value === "b" ? kind === "b" : kind === "o" && String(y) === year.value)) &&
      (!needle || normalized(name + " " + office).includes(needle)));
    // A dated list printed inside the directory (past office-holders, one line per year) repeats a name year after
    // year: the same printed name, office and page become one line carrying all its years. Every record still counts.
    const lines = [];
    const folded = new Map();
    for (const row of rows) {
      if (row[0] === "d" && row[7] === 1) {
        const id = row[2] + "\u0000" + row[4] + "\u0000" + row[5];
        if (folded.has(id)) { folded.get(id).years.push(row[1]); continue; }
        const line = { row, years: [row[1]] };
        folded.set(id, line);
        lines.push(line);
      } else if (row[0] === "b" && row[7] && row[7] !== row[1]) {
        lines.push({ row, years: [row[1], row[7]] });
      } else lines.push({ row, years: [row[1]] });
    }
    const latest = (line) => Math.max(...line.years);
    const byName = (a, b) => a.row[2].localeCompare(b.row[2]);
    if (order.value === "old") lines.sort((a, b) => Math.min(...a.years) - Math.min(...b.years) || byName(a, b));
    else if (order.value === "office") {
      const office = (line) => normalized(line.row[4]).replace(/^[^a-z]+/, "");   // ". Clerk", "10th Master" sort by their words
      lines.sort((a, b) => office(a).localeCompare(office(b)) || latest(b) - latest(a) || byName(a, b));
    }
    else lines.sort((a, b) => latest(b) - latest(a) || byName(a, b));
    const pages = Math.max(1, Math.ceil(lines.length / PEOPLE_PAGE));
    people.place.page = Math.min(people.place.page, pages - 1);
    const start = people.place.page * PEOPLE_PAGE;
    const foldNote = lines.length < rows.length ? " in " + lines.length.toLocaleString("en") + " lines (a name repeated through a dated list in the directory is one line)" : "";
    count.textContent = rows.length.toLocaleString("en") + " records" + foldNote + (lines.length > PEOPLE_PAGE ? ", showing " + (start + 1) + "–" + Math.min(lines.length, start + PEOPLE_PAGE) : "") + ".";
    ul.replaceChildren();
    for (const { row: [kind, y, key, name, office, ref, stage, extra], years } of lines.slice(start, start + PEOPLE_PAGE)) {
      const li = add(ul, "li");
      action(li, name, () => peopleOpen(key));
      peopleStage(li, stage);
      let when = String(y);
      if (kind === "b" && extra && extra !== y) when = y + "–" + extra;
      else if (years.length > 1) when = "dated list, " + years.length + " years between " + Math.min(...years) + " and " + Math.max(...years);
      add(li, "small", (kind === "d" ? "Directory " : kind === "b" ? "de Silva’s History · events dated " : "") + when + (office ? " · " + office : ""));
      const src = add(li, "span", undefined, "people-src");
      if (kind === "o" && ref && ref[0]) action(src, "Blue Book table →", () => peopleOpenTable(ref[0]));
      if (kind === "d") src.textContent = "Ferguson’s Directory 1922, PDF p. " + ref;
      if (kind === "b" && ref) link(src, people.summary.book_source.pdf + "#page=" + ref[0], "A History of Sri Lanka, p. " + (ref[1] || "(scan " + ref[0] + ")") + " ↗");
    }
    pager.replaceChildren();
    if (pages > 1) {
      action(pager, "← Previous", () => { people.place.page--; list(); }).disabled = people.place.page === 0;
      action(pager, "Next →", () => { people.place.page++; list(); }).disabled = people.place.page >= pages - 1;
    }
  }
}

function peopleOpenTable(id) {
  history.pushState(null, "", "#bluebook=" + id);
  route();
  window.scrollTo(0, 0);
}

// ---- People view ---------------------------------------------------------------------------------------------

function peopleHash() {
  if (people.state.key) return "people=" + encodeURIComponent(people.state.key);
  const params = new URLSearchParams();
  if (people.state.q) params.set("q", people.state.q);
  if (people.state.kind) params.set("kind", people.state.kind);
  if (people.state.page) params.set("page", String(people.state.page + 1));
  const text = params.toString();
  return "people" + (text ? "?" + text : "");
}

// hash is location.hash without "#", starting with "people"
function peopleRoute(hash) {
  if (hash.startsWith("people-place=")) {
    let id = "";
    try { id = decodeURIComponent(hash.slice("people-place=".length)); } catch (error) { id = ""; }
    if (peoplePlaceShown() && people.place.id === id) return showView("map", false);
    return peopleSelectPlace(id, true);
  }
  showView("people", false);
  peopleBind();
  const rest = hash.slice("people".length);
  if (rest.startsWith("=")) {
    let key = "";
    try { key = decodeURIComponent(rest.slice(1)); } catch (error) { key = ""; }
    people.state.key = key;
    return peopleShow();
  }
  const params = new URLSearchParams(rest.startsWith("?") ? rest.slice(1) : "");
  people.state = {
    q: params.get("q") || "", kind: params.get("kind") || "", key: "",
    page: Math.max(0, (parseInt(params.get("page"), 10) || 1) - 1),
  };
  peopleShow();
}

function peopleShowSearch() {
  peopleBind();
  peopleShow();
}

function peopleBind() {
  if (people.bound) return;
  people.bound = true;
  const changed = () => {
    people.state.q = byId("people-q").value.trim();
    people.state.kind = byId("people-kind").value;
    people.state.page = 0;
    people.state.key = "";
    updateHash(peopleHash());
    peopleShow();
  };
  byId("people-q").addEventListener("input", changed);
  byId("people-kind").addEventListener("change", changed);
  byId("people-prev").addEventListener("click", () => { people.state.page--; updateHash(peopleHash()); peopleShow(); });
  byId("people-next").addEventListener("click", () => { people.state.page++; updateHash(peopleHash()); peopleShow(); });
}

function peopleOpen(key) {
  people.state.key = key;
  showView("people", false);
  peopleBind();
  history.pushState(null, "", "#" + peopleHash());
  peopleShow();
  window.scrollTo(0, 0);
}

async function peopleShow() {
  const ticket = ++people.version;
  byId("people-q").value = people.state.q;
  byId("people-kind").value = people.state.kind;
  const body = byId("people-results");
  const count = byId("people-count");
  const detail = byId("people-detail");
  byId("people-search").hidden = Boolean(people.state.key);
  detail.hidden = !people.state.key;
  try {
    await peopleBase();
    if (!people.index) people.index = await peopleFetch("names.json.gz");
  } catch (error) {
    if (ticket === people.version) count.textContent = error.message;
    return;
  }
  if (ticket !== people.version) return;
  const s = people.summary;
  byId("people-summary").textContent = s.officials.toLocaleString("en") + " official records (one per name and Blue Book volume), of which " +
    s.officials_placed.toLocaleString("en") + " name a place on the map; " + s.directory.toLocaleString("en") +
    " directory roles; " + (s.book || 0).toLocaleString("en") + " people from de Silva’s History; " + s.names.toLocaleString("en") + " printed names." +
    Object.entries(s.officials_left_out || {}).map(([why, n]) => " Left out: " + n.toLocaleString("en") + " Blue Book lines whose name column holds an " + why + ".").join("");
  if (people.state.key) return peopleDetail(ticket);

  const words = normalized(people.state.q).split(/[^a-z0-9]+/).filter(Boolean);
  const kind = people.state.kind;
  body.replaceChildren();
  if (!words.length && !kind) {
    count.textContent = "Type a surname to search, or choose a source above to browse. Initials narrow the list: “fernando j”.";
    byId("people-prev").disabled = byId("people-next").disabled = true;
    return;
  }
  people.results = people.index.filter(([key, display, , , , kinds]) => {
    if (kind && !kinds.includes(kind)) return false;
    if (!words.length) return true;
    const hay = normalized(display) + " " + key.replace(/[:_]/g, " ");
    return words.every((word) => word.length === 1 ? (" " + hay + " ").includes(" " + word + " ") : hay.includes(word));
  });
  const first = words[0];
  if (first) people.results.sort((a, b) => (a[0].startsWith(first) ? 0 : 1) - (b[0].startsWith(first) ? 0 : 1) || a[0].localeCompare(b[0]));
  else people.results.sort((a, b) => a[0].localeCompare(b[0]));
  const pages = Math.max(1, Math.ceil(people.results.length / PEOPLE_PAGE));
  people.state.page = Math.min(people.state.page, pages - 1);
  const start = people.state.page * PEOPLE_PAGE;
  count.textContent = people.results.length.toLocaleString("en") + " printed names" + (people.results.length ? ", page " + (people.state.page + 1) + " of " + pages : "") + ".";
  byId("people-prev").disabled = people.state.page === 0;
  byId("people-next").disabled = people.state.page >= pages - 1;
  for (const [key, display, from, to, n, kinds] of people.results.slice(start, start + PEOPLE_PAGE)) {
    const tr = add(body, "tr");
    const cell = add(tr, "td");
    action(cell, display, () => peopleOpen(key));
    add(tr, "td", from === to ? String(from) : from + "–" + to);
    add(tr, "td", String(n));
    add(tr, "td", [kinds.includes("o") ? "Blue Books" : "", kinds.includes("d") ? "Directory 1922" : "", kinds.includes("b") ? "de Silva’s History" : ""].filter(Boolean).join(" + "));
    tr.addEventListener("click", (event) => { if (event.target.tagName !== "BUTTON") peopleOpen(key); });
  }
}

async function peopleDetail(ticket) {
  const root = byId("people-detail");
  const key = people.state.key;
  root.replaceChildren();
  const back = add(root, "p");
  action(back, "← Search people", () => {
    people.state.key = "";
    history.pushState(null, "", "#" + peopleHash());
    peopleShow();
  });
  const shard = (key.replace(/[^a-z]/g, "").slice(0, 2) || "zz").padEnd(2, "_");
  let entries;
  try {
    entries = (await peopleFetch("names/" + shard + ".json.gz"))[key];
  } catch (error) {
    if (ticket === people.version) add(root, "p", error.message, "help");
    return;
  }
  if (ticket !== people.version) return;
  if (!entries) return add(root, "p", "No records are filed under this printed name.", "help");
  const pointers = entries.filter((e) => e.k === "x");
  entries = entries.filter((e) => e.k !== "x");
  const names = [...new Set(entries.map((e) => e.name))];
  add(root, "div", "PRINTED NAME", "eyebrow");
  add(root, "h1", names[0]);
  if (names.length > 1) add(root, "p", "Also printed as: " + names.slice(1, 12).join("; ") + (names.length > 12 ? "; …" : ""), "help");
  const caution = entries.length === 1
    ? (entries[0].k === "b"
      ? "One entry is filed under this printed name, read from K. M. de Silva’s History (1981) and linked to the pages of the book."
      : "One record is filed under this printed name. An identification, where one has been proposed, is shown in the last column with its basis.")
    : "These " + entries.length + " records share a surname and initials as printed. That is a reason to compare them, not proof that they are one person: common names, fathers and sons, and misread initials all occur. An identification, where one has been proposed, is shown in the last column with its basis.";
  add(root, "p", caution, "people-caution");
  peopleStageKey(root);
  const frame = add(root, "div", undefined, "table-frame");
  const table = add(frame, "table", undefined, "people-entries");
  const head = add(add(table, "thead"), "tr");
  const columns = ["Year", "Office or role", "Place named", "Source", "Identification proposed"];
  for (const title of columns) add(head, "th", title).scope = "col";
  const body = add(table, "tbody");
  for (const e of entries) {
    const tr = add(body, "tr");
    const year = add(tr, "td", e.y2 && e.y2 !== e.y ? e.y + "–" + e.y2 : String(e.y));
    if (e.k === "d") add(year, "small", e.dated);
    if (e.k === "b") add(year, "small", "date of events in the book that name this person, not dates of office");
    peopleStage(year, e.st);
    const office = add(tr, "td");
    if (e.k === "o") office.textContent = e.office || "No office printed with this name";
    else if (e.k === "b") {
      office.textContent = e.office || e.name;
      if (e.desc) add(office, "small", e.desc);
      const life = [e.community, e.born ? "born " + e.born : "", e.died ? "died " + e.died : ""].filter(Boolean).join(" · ");
      if (life) add(office, "small", life);
    } else {
      office.textContent = [e.office, e.firm].filter(Boolean).join(", ");
      if (e.address) add(office, "small", e.address);
      if (e.trades) add(office, "small", e.trades);
      if (e.doubt) add(office, "small", e.doubt);
    }
    const where = add(tr, "td");
    for (const [id, name, how] of e.places) {
      const button = action(where, name, () => {
        history.pushState(null, "", "#people-place=" + encodeURIComponent(id));
        peopleSelectPlace(id, true);
      });
      button.title = "Recognised as: " + how;
      add(where, "small", how);
    }
    if (!e.places.length) add(where, "span", e.k === "o" ? "none printed" : e.town || "—", "muted");
    if (e.k === "b") {
      const source = add(tr, "td");
      const book = people.summary.book_source;
      link(source, book.item, "K. M. de Silva, A History of Sri Lanka (1981) ↗");
      const pages = add(source, "small");
      pages.append("pp. ");
      (e.pages || []).forEach(([pdf, printed], i) => {
        if (i) pages.append(", ");
        link(pages, book.pdf + "#page=" + pdf, printed || "scan " + pdf);
      });
      const about = add(tr, "td", undefined, "people-id");
      about.textContent = "A named person in a modern history; summary in our words, read from the scan by program.";
      for (const r of e.reviews || []) {
        const label = { same_person: "Reviewed: the Blue Book or directory records on this page are this person.", probably_same: "Reviewed: the records on this page are probably this person.", some_records: "Reviewed: some of the records on this page are this person; they are marked.", namesake: "Reviewed: the other records on this page are a namesake, not this person.", unclear: "Reviewed: whether the other records on this page are this person is not established." }[r.decision];
        add(about, "small", label + " " + r.basis + (r.outside ? " (From outside these sources: " + r.outside + ")" : ""));
      }
      continue;
    }
    const source = add(tr, "td");
    if (e.k === "o") {
      add(source, "span", "Blue Book " + e.y);
      for (const id of e.tables || []) {
        add(source, "br");
        action(source, "table " + id.split(":").slice(1).join(" ") + " →", () => peopleOpenTable(id));
      }
    } else {
      link(source, people.summary.directory_source, "Ferguson’s Ceylon Directory 1922 ↗");
      add(source, "small", "PDF p. " + e.page + " · " + e.section);
      add(source, "small", e.ref);
    }
    const ident = add(tr, "td", undefined, "people-id");
    if (e.col) {
      ident.textContent = "Colonial Office List biography: " + (e.col.name || e.col.id) + (e.col.born ? ", born " + e.col.born : "");
      add(ident, "small", "confidence: " + (e.col.conf || "not stated") + "; matched by surname, initials and dates, not checked by a person");
      if (e.col.qid) link(ident, "https://www.wikidata.org/wiki/" + encodeURIComponent(e.col.qid), e.col.qid + " ↗");
    }
    if (e.roster) add(ident, "small", "Also in the Colonial Office List " + e.roster.edition + " establishment: " + e.roster.office);
    if (e.ds) {
      const line = add(ident, "small");
      line.append("De Silva’s History: " + e.ds.wording + " ");
      action(line, e.ds.name, () => peopleOpen(e.ds.key));
      line.append(". " + e.ds.basis + (e.ds.outside ? " (From outside these sources: " + e.ds.outside + ")" : "") + " Decided by a language model, sampled.");
    }
    if (!e.col && !e.roster && !e.ds) add(ident, "span", "—", "muted");
  }
  for (const tr of body.rows) [...tr.cells].forEach((td, i) => { td.dataset.label = columns[i]; });   // read on a phone
  if (pointers.length) {
    add(root, "h2", "Linked printed names");
    add(root, "p", "Printed names under another spelling or set of initials that a review linked to a person on this page. Each link was decided by a language model from the records and sampled by a second reader.", "help");
    const ul = add(root, "ul", undefined, "people-list");
    for (const x of pointers) {
      const li = add(ul, "li");
      action(li, x.name, () => peopleOpen(x.key));
      add(li, "small", (x.book ? "In de Silva’s History · events dated " : x.n + " records · ") + (x.y2 && x.y2 !== x.y ? x.y + "–" + x.y2 : x.y) + " · " + x.note);
    }
  }
}
