"use strict";
// Blue Book view: search the parsed Ceylon Blue Book tables and check each one against its printed page.
// Loaded before atlas.js; uses its helpers (byId, add, elt, link, action, normalized, instant, svg) at call time only.
// Data: docs/data/bluebook/, written by spine/bluebook/export_viewer.py. The .gz files are decompressed here.

const BB_PAGE_SIZE = 40;
const BB_TABLE_ID = /^bb(\w+):p(\d+):t(\d+)$/;
const BB_LEVELS = {
  summed: {
    title: "Summed",
    text: "Every printed total that could be checked equals the sum of its parts, and at least one of them is a real sum (a non-zero total of two or more non-zero figures). The figures inside those totals were read correctly and sit in the right rows and columns. Figures outside the checked totals are not covered by this test.",
  },
  two_readings: {
    title: "Two readings",
    text: "At least 90% of this table’s numbers of three or more digits also appear in a second, independent reading of the same page, and the table has at least 10 distinct such numbers. This shows the digits are printed on the page. It does not show that each number is in the right row or column: a row shift, figures under the wrong country or heading, or headers the OCR made up can still pass. Compare the layout with the page image.",
  },
  partly: {
    title: "Partly confirmed",
    text: "Some support, but not enough for a higher level: at least half of the printed totals agree (one of them a real sum), or at least 70% of five or more distinct numbers appear in the second reading.",
  },
  unconfirmed: {
    title: "Unconfirmed",
    text: "Nothing confirms or contradicts this table: it has no usable printed total and no usable second reading. This is not evidence of error. Most such tables are lists of names and words, tables with few numbers, sideways pages, or come from the 1880–1894 volumes, where the second reading is poor.",
  },
  suspect: {
    title: "Suspect",
    text: "The page is probably blank or carries only a section title, and the OCR model has invented this table. Do not use it. Check the page image.",
  },
};
const BB_FLAGS = {
  no_page_number: "No printed page number or running section was found on this page.",
  modern_words: "The table contains modern words (such as “quarterly statements”, “GDP” or “Q1”) that a Blue Book would not print, a sign of invented content.",
  repeated_number: "One number fills most of the cells in a column, a sign of invented content.",
  no_second_reading: "The second reading found almost no text on this page. Either the page is blank or the table is printed sideways.",
  no_ink_in_outline: "The scan has no dark pixels inside the area where this table was read.",
  blank_page: "Blank page: the second reading finds no text and the scan has no ink inside the table’s outline.",
  title_page_only: "The second reading finds only a short title on this page and almost none of the table’s numbers.",
  only_trivial_totals: "The totals that agree are trivial (zero, or a total of a single figure), so they prove little.",
};
const bbFiles = new Map();
const bb = {
  volumes: null, index: null, labels: null, labelKeys: null, acreage: null,
  state: { vol: "", q: "", label: "", level: "", show: "", page: 0 },
  results: [], matchedLabel: new Map(), searchVersion: 0, detailVersion: 0, volStart: new Map(),
  bound: false, imagePage: 0,
};

function bbFetch(name) {
  if (!bbFiles.has(name)) {
    bbFiles.set(name, fetch("data/bluebook/" + name).then(async (response) => {
      if (!response.ok) throw new Error(name + " could not be loaded.");
      const bytes = new Uint8Array(await response.arrayBuffer());
      // A server may already have removed the gzip layer (Content-Encoding); only inflate real gzip bytes.
      if (bytes[0] === 0x1f && bytes[1] === 0x8b) {
        const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"));
        return JSON.parse(await new Response(stream).text());
      }
      return JSON.parse(new TextDecoder().decode(bytes));
    }).catch((error) => {
      bbFiles.delete(name);
      throw error;
    }));
  }
  return bbFiles.get(name);
}

async function bbBase() {
  if (!bb.volumes) {
    const [volumes, index] = await Promise.all([bbFetch("volumes.json"), bbFetch("index.json.gz")]);
    if (bb.volumes) return;
    bb.volumes = volumes.volumes;
    bb.levelNames = volumes.levels;
    bb.sections = index.sections;
    bb.index = index.tables.map((row, pos) => ({
      pos, vol: row[0], page: row[1], t: row[2], printed: row[3], section: row[4] < 0 ? "" : index.sections[row[4]],
      headings: row[5], rows: row[6], cols: row[7], level: volumes.levels[row[8]], checked: row[9], agree: row[10],
      obs: row[11], officers: row[12],
    }));
    for (const entry of bb.index) {
      entry.key = bb.volumes[entry.vol].key;
      entry.id = "bb" + entry.key + ":p" + entry.page + ":t" + entry.t;
      entry.text = normalized(entry.section + " " + entry.headings + " " + entry.printed);
      if (!bb.volStart.has(entry.vol)) bb.volStart.set(entry.vol, entry.pos);
    }
    bb.byId = new Map(bb.index.map((entry) => [entry.id, entry]));
  }
}

async function bbLabelIndex() {
  if (!bb.labelKeys) {
    const labels = await bbFetch("labels.json.gz");
    if (bb.labelKeys) return;
    bb.labels = labels;
    bb.labelKeys = [];
    for (const kind of ["r", "c"]) {
      for (const key of Object.keys(labels[kind])) bb.labelKeys.push({ kind, key, norm: normalized(key) });
    }
  }
}

function bbPostings(entry) {
  const out = [];
  let at = 0;
  for (const delta of bb.labels[entry.kind][entry.key]) out.push(at += delta);
  return out;
}

const bbVolumeName = (v) => v.year + (v.key !== String(v.year) ? " (part 2)" : "") + (v.note && !/^part/.test(v.note) ? " · " + v.note : "");
// archive.org serves each page image at full size (n<i>.jpg) or scaled to a width (n<i>_w1600.jpg, about a seventh of the bytes)
const bbPageImage = (ia, page, width) => "https://archive.org/download/" + encodeURIComponent(ia) + "/page/n" + (page - 1) + (width ? "_w" + width : "") + ".jpg";
const bbPageLink = (ia, page) => "https://archive.org/details/" + encodeURIComponent(ia) + "/page/n" + (page - 1) + "/mode/1up";

function bbBadge(parent, level) {
  const tag = add(parent, "span", (BB_LEVELS[level] || { title: level }).title, "bb-level lv-" + level);
  tag.title = (BB_LEVELS[level] || {}).text || "";
  return tag;
}

// ---- routing -------------------------------------------------------------------------------------------------

function bluebookHash() {
  const params = new URLSearchParams();
  for (const key of ["vol", "q", "label", "level", "show"]) if (bb.state[key]) params.set(key, bb.state[key]);
  if (bb.state.page) params.set("page", String(bb.state.page + 1));
  const text = params.toString();
  return "bluebook" + (text ? "?" + text : "");
}

// hash is location.hash without "#", starting with "bluebook"
function bluebookRoute(hash) {
  bbBind();
  const rest = hash.slice("bluebook".length);
  if (rest.startsWith("=")) {
    const id = decodeURIComponent(rest.slice(1));
    if (BB_TABLE_ID.test(id)) bbShowDetail(id);
    else bbShowDetail("an unreadable id");
    return;
  }
  const params = new URLSearchParams(rest.startsWith("?") ? rest.slice(1) : "");
  bb.state = {
    vol: params.get("vol") || "", q: params.get("q") || "", label: params.get("label") || "",
    level: params.get("level") || "", show: params.get("show") || "",
    page: Math.max(0, (parseInt(params.get("page"), 10) || 1) - 1),
  };
  bbShowSearch();
}

function bluebookShowSearch() {
  bbBind();
  bbShowSearch();
}

// history.state.bbDepth counts the table pages opened since the search results (0: reached some other way),
// so "Search tables" can go back to the results instead of to the previous table.
function bbOpenTable(id) {
  const fromSearch = view === "bluebook" && !byId("bb-search").hidden;
  history.pushState({ bbDepth: fromSearch ? 1 : 0 }, "", "#bluebook=" + id);
  bbShowDetail(id);
  window.scrollTo(0, 0);
}

function bbBackToSearch() {
  const depth = history.state && history.state.bbDepth;
  if (depth > 0) history.go(-depth);
  else {
    history.pushState(null, "", "#" + bluebookHash());
    bbShowSearch();
  }
}

// ---- search --------------------------------------------------------------------------------------------------

function bbBind() {
  if (bb.bound) return;
  bb.bound = true;
  const levelMenu = byId("bb-level");
  for (const [level, info] of Object.entries(BB_LEVELS)) add(levelMenu, "option", info.title).value = level;
  const help = byId("bb-level-help");
  for (const [level, info] of Object.entries(BB_LEVELS)) {
    const item = add(help, "div", undefined, "bb-level-row");
    bbBadge(item, level);
    add(item, "p", info.text, "help");
  }
  add(help, "p", "A printed total that does not agree is weak evidence of a misread: in the cases read by eye the numbers were usually right and the check was wrong (a table continued from another page, a running subtotal, or columns of different units under one heading). The tests cannot see a figure placed in the wrong row or under the wrong heading; only the page image shows that.", "help");
  const fields = { "bb-volume": "vol", "bb-query": "q", "bb-label": "label", "bb-level": "level", "bb-show": "show" };
  let typing;
  for (const [id, key] of Object.entries(fields)) {
    const control = byId(id);
    const update = () => {
      bb.state[key] = control.value.trim();
      bb.state.page = 0;
      history.replaceState(null, "", "#" + bluebookHash());
      bbRunSearch();
    };
    if (control.tagName === "INPUT") control.addEventListener("input", () => { clearTimeout(typing); typing = setTimeout(update, 220); });
    else control.addEventListener("change", update);
  }
  byId("bb-prev").addEventListener("click", () => bbTurn(-1));
  byId("bb-next").addEventListener("click", () => bbTurn(1));
  byId("bb-crop").addEventListener("change", () => bbSeriesAreas());
  byId("bb-area").addEventListener("change", () => bbDrawSeries());
}

function bbTurn(step) {
  bb.state.page += step;
  history.replaceState(null, "", "#" + bluebookHash());
  bbPaintResults();
  byId("bb-results").closest(".table-frame").scrollIntoView({ block: "nearest" });
}

async function bbShowSearch() {
  byId("bb-search").hidden = false;
  byId("bb-detail").hidden = true;
  const body = byId("bb-results");
  if (!bb.index) {
    body.replaceChildren();
    add(add(body, "tr"), "td", "Loading the table index…", "muted").colSpan = 8;
  }
  try {
    await bbBase();
  } catch (error) {
    body.replaceChildren();
    add(add(body, "tr"), "td", error.message + " Reload the page to try again.", "muted").colSpan = 8;
    return;
  }
  const volumeMenu = byId("bb-volume");
  if (volumeMenu.options.length === 1) {
    for (const v of bb.volumes) add(volumeMenu, "option", bbVolumeName(v)).value = v.key;
  }
  volumeMenu.value = bb.volumes.some((v) => v.key === bb.state.vol) ? bb.state.vol : "";
  byId("bb-query").value = bb.state.q;
  byId("bb-label").value = bb.state.label;
  byId("bb-level").value = BB_LEVELS[bb.state.level] ? bb.state.level : "";
  byId("bb-show").value = ["extracted", "differ"].includes(bb.state.show) ? bb.state.show : "";
  bbRunSearch();
  bbSeries();
}

async function bbRunSearch() {
  const ticket = ++bb.searchVersion;
  const s = bb.state;
  const note = byId("bb-volume-note");
  note.replaceChildren();
  const vol = bb.volumes.findIndex((v) => v.key === s.vol);
  if (vol >= 0) {
    const v = bb.volumes[vol];
    note.append(bbVolumeName(v) + " · " + instant.format(v.pages) + " pages · " + instant.format(v.tables) + " tables: ");
    bb.levelNames.forEach((level, i) => {
      const part = add(note, "span", undefined, "bb-count-chip");
      bbBadge(part, level);
      part.append(" " + instant.format(v.levels[i]) + " ");
    });
    note.append(" ");
    link(note, "https://archive.org/details/" + encodeURIComponent(v.ia), "Volume on archive.org ↗");
  }
  const words = normalized(s.q).split(/\s+/).filter(Boolean);
  let labelHits = null;
  bb.matchedLabel = new Map();
  const needle = normalized(s.label).trim();
  if (needle) {
    if (!bb.labelKeys) {
      byId("bb-count").textContent = "Loading the label index…";
      try { await bbLabelIndex(); } catch (error) {
        if (ticket === bb.searchVersion) byId("bb-count").textContent = error.message;
        return;
      }
      if (ticket !== bb.searchVersion) return;
    }
    labelHits = new Set();
    const exact = [];
    const partial = [];
    for (const entry of bb.labelKeys) {
      if (entry.norm === needle) exact.push(entry);
      else if (entry.norm.includes(needle)) partial.push(entry);
    }
    for (const entry of [...exact, ...partial]) {
      for (const pos of bbPostings(entry)) {
        labelHits.add(pos);
        if (!bb.matchedLabel.has(pos)) bb.matchedLabel.set(pos, (entry.kind === "r" ? "row: " : "column: ") + entry.key);
      }
    }
  }
  bb.results = bb.index.filter((e) => (vol < 0 || e.vol === vol)
    && (!s.level || e.level === s.level)
    && (s.show !== "extracted" || e.obs || e.officers)
    && (s.show !== "differ" || e.agree < e.checked)
    && (!labelHits || labelHits.has(e.pos))
    && words.every((w) => e.text.includes(w)));
  bbPaintResults();
}

function bbPaintResults() {
  const body = byId("bb-results");
  body.replaceChildren();
  const rows = bb.results;
  const pages = Math.max(1, Math.ceil(rows.length / BB_PAGE_SIZE));
  bb.state.page = Math.min(Math.max(0, bb.state.page), pages - 1);
  const first = bb.state.page * BB_PAGE_SIZE;
  if (!rows.length) add(add(body, "tr"), "td", "No tables match these filters.", "muted").colSpan = 8;
  for (const e of rows.slice(first, first + BB_PAGE_SIZE)) {
    const tr = add(body, "tr");
    const idCell = add(tr, "td");
    const open = action(idCell, e.id, () => bbOpenTable(e.id), "table-open");
    open.title = "Open table and page image";
    add(tr, "td", String(bb.volumes[e.vol].year) + (e.key !== String(bb.volumes[e.vol].year) ? " pt 2" : ""));
    add(tr, "td", (e.printed ? e.printed + " · " : "") + "pdf " + e.page);
    add(tr, "td", e.section || "—");
    const headCell = add(tr, "td", e.headings || "—", "bb-headings");
    if (bb.matchedLabel.has(e.pos)) add(headCell, "small", "Label " + bb.matchedLabel.get(e.pos));
    add(tr, "td", e.rows + " × " + e.cols);
    const levelCell = add(tr, "td");
    bbBadge(levelCell, e.level);
    if (e.checked) add(levelCell, "small", e.agree + " of " + e.checked + " totals agree");
    add(tr, "td", [e.obs ? e.obs + " figures" : "", e.officers ? e.officers + " names" : ""].filter(Boolean).join(", ") || "—");
  }
  byId("bb-count").textContent = rows.length
    ? (first + 1) + "–" + Math.min(first + BB_PAGE_SIZE, rows.length) + " of " + instant.format(rows.length) + " tables"
    : "0 tables";
  byId("bb-prev").disabled = bb.state.page === 0;
  byId("bb-next").disabled = first + BB_PAGE_SIZE >= rows.length;
}

// ---- table detail --------------------------------------------------------------------------------------------

async function bbShowDetail(id) {
  const ticket = ++bb.detailVersion;
  byId("bb-search").hidden = true;
  const root = byId("bb-detail");
  root.hidden = false;
  root.replaceChildren();
  add(root, "p", "Loading table…", "muted");
  let entry, volume, extracted;
  try {
    await bbBase();
    entry = bb.byId.get(id);
    if (!entry) throw new Error("There is no Blue Book table " + id + ".");
    const meta = bb.volumes[entry.vol];
    [volume, extracted] = await Promise.all([
      bbFetch("vol/" + meta.key + ".json.gz"),
      entry.obs || entry.officers ? bbFetch("extracted/" + meta.key + ".json.gz") : null,
    ]);
  } catch (error) {
    if (ticket !== bb.detailVersion) return;
    root.replaceChildren();
    action(root, "← Search tables", bbBackToSearch);
    add(root, "p", error.message, "help");
    return;
  }
  if (ticket !== bb.detailVersion) return;
  const meta = bb.volumes[entry.vol];
  const short = "p" + entry.page + ":t" + entry.t;
  const table = volume.tables[short];
  bb.imagePage = entry.page;
  root.replaceChildren();

  const nav = add(root, "div", undefined, "bb-nav");
  action(nav, "← Search tables", bbBackToSearch);
  const prev = bb.index[entry.pos - 1];
  const next = bb.index[entry.pos + 1];
  const navRight = add(nav, "span", undefined, "bb-nav-step");
  if (prev && prev.vol === entry.vol) action(navRight, "← Previous table (" + prev.id + ")", () => bbOpenSibling(prev.id));
  if (next && next.vol === entry.vol) action(navRight, "Next table (" + next.id + ") →", () => bbOpenSibling(next.id));

  add(root, "div", "BLUE BOOK " + meta.year + (meta.key !== String(meta.year) ? " · PART 2" : "") + " · PDF PAGE " + entry.page
    + (entry.printed ? " · PRINTED PAGE " + entry.printed : ""), "eyebrow");
  add(root, "h1", entry.id, "bb-title");
  if (entry.section) add(root, "p", "Running section: " + entry.section, "lede");
  if (table.headings.length) {
    const list = add(root, "ul", undefined, "bb-heading-list");
    for (const heading of table.headings) add(list, "li", heading);
  } else add(root, "p", "No heading was read above this table.", "help");
  const onPage = bb.index.filter((e) => e.vol === entry.vol && e.page === entry.page);
  if (onPage.length > 1) {
    const others = add(root, "p", "Tables on this page: ", "help");
    for (const e of onPage) {
      if (e.id === entry.id) add(others, "b", "t" + e.t + " ");
      else { action(others, "t" + e.t, () => bbOpenSibling(e.id)); others.append(" "); }
    }
  }

  const checks = add(root, "section", undefined, "bb-checks");
  const grid = add(root, "div", undefined, "bb-detail-grid");
  const left = add(grid, "div", undefined, "bb-left");
  const right = add(grid, "div", undefined, "bb-right");
  const tableBox = add(left, "section", undefined, "bb-parsed");
  add(tableBox, "h2", "Parsed table");
  add(tableBox, "p", entry.rows + " rows × " + entry.cols + " columns. Row and column numbers count from 0, as in the data files and the checks above. Grey header rows are the OCR’s guess (" + table.header_rows + " header row" + (table.header_rows === 1 ? "" : "s") + ") and may be wrong.", "help");
  const cells = bbTable(tableBox, table);
  bbChecks(checks, table.confidence, cells);
  bbPage(right, meta, entry);
  bbExtracted(root, extracted, short, cells);
}

function bbOpenSibling(id) {
  const depth = history.state && history.state.bbDepth;
  history.pushState({ bbDepth: depth > 0 ? depth + 1 : 0 }, "", "#bluebook=" + id);
  bbShowDetail(id);
}

function bbTable(parent, table) {
  const frame = add(parent, "div", undefined, "bb-table-frame");
  const t = add(frame, "table", undefined, "bb-table");
  const width = Math.max(1, ...table.rows.map((r) => r.length));
  const head = add(t, "thead");
  const gutter = add(head, "tr", undefined, "bb-gutter");
  add(gutter, "th", "");
  for (let j = 0; j < width; j++) add(gutter, "th", String(j)).scope = "col";
  const body = add(t, "tbody");
  const cells = { get: (i, j) => t.querySelector('[data-cell="' + i + ":" + j + '"]'), row: (i) => t.querySelector('[data-row="' + i + '"]'), clear() {
    t.querySelectorAll(".hit").forEach((node) => node.classList.remove("hit"));
  } };
  const number = /^[\s(£$-]*[\d][\d,.\s½¼¾]*\)?$/;
  table.rows.forEach((row, i) => {
    const tr = add(body, "tr");
    tr.dataset.row = String(i);
    if (i < table.header_rows) tr.className = "bb-header-row";
    add(tr, "th", String(i), "bb-rownum").scope = "row";
    for (let j = 0; j < width; j++) {
      const td = add(tr, "td", row[j] ?? "");
      td.dataset.cell = i + ":" + j;
      if (j >= row.length) td.classList.add("bb-missing");
      else if (number.test(row[j])) td.classList.add("num");
    }
  });
  return cells;
}

function bbFocus(cells, i, j) {
  cells.clear();
  const target = j >= 0 ? cells.get(i, j) : cells.row(i);
  if (!target) return;
  target.classList.add("hit");
  target.scrollIntoView({ block: "center", inline: "center", behavior: "smooth" });
}

function bbChecks(root, c, cells) {
  const level = c.level || "unconfirmed";
  const head = add(root, "div", undefined, "bb-check-head");
  add(head, "h2", "Confidence");
  bbBadge(head, level);
  add(root, "p", (BB_LEVELS[level] || {}).text || "", "bb-level-text");
  const totals = Number(c.totals_checked) || 0;
  const facts = [];
  if (totals) {
    facts.push(["Printed totals checked", totals]);
    facts.push(["Totals that agree", c.totals_agree + (Number(c.nontrivial_totals_agree) ? " (" + c.nontrivial_totals_agree + " real sum" + (c.nontrivial_totals_agree === "1" ? "" : "s") + ")" : "")]);
    if (Number(c.off_by_one_digit)) facts.push(["Off in one digit", c.off_by_one_digit]);
    if (Number(c.differ)) facts.push(["Differ more", c.differ]);
    if (Number(c.numbers_confirmed_by_totals)) facts.push(["Cells inside agreeing totals", c.numbers_confirmed_by_totals]);
  } else facts.push(["Printed totals", "none that could be checked"]);
  const n3 = Number(c.numbers_3plus_digits) || 0;
  if (c.share_in_second_reading !== "") {
    facts.push(["Second reading", c.also_in_second_reading + " of " + n3 + " numbers of 3+ digits (" + Math.round(Number(c.share_in_second_reading) * 100) + "%), " + c.distinct_numbers_3plus + " distinct"]);
  } else facts.push(["Second reading", n3 ? "not usable for this page (" + n3 + " numbers of 3+ digits)" : "no numbers of 3+ digits"]);
  details(root, facts);
  const flags = (c.flags || "").split(";").filter(Boolean);
  const parts = (c.disagreements || "").split(";").map((part) => part.trim()).filter(Boolean);
  const side = flags.length || parts.length ? add(root, "div", undefined, "bb-side") : root;
  if (flags.length) {
    add(side, "h3", "Flags");
    const list = add(side, "ul", undefined, "bb-flags");
    for (const flag of flags) {
      const [name, count] = flag.split(":");
      const item = add(list, "li");
      add(item, "code", name);
      item.append(" ");
      item.append(name === "subtotals_agree"
        ? count + " unlabelled row" + (count === "1" ? "" : "s") + " read as running subtotals agree with the figures above. Such rows are only kept when they agree, so they do not count towards the level."
        : BB_FLAGS[name] || "");
    }
  }
  if (parts.length) {
    add(side, "h3", "Totals that do not agree");
    add(side, "p", "Select one to find the printed total in the parsed table. A total that does not agree is weak evidence: the check is often wrong (a table continued from another page, a running subtotal, columns of different units), so read the page.", "help");
    const list = add(side, "ul", undefined, "bb-disagreements");
    const pattern = /^r(\d+)c(\d+) printed (-?\d+) sum off by ([+-]\d+)$/;
    for (const part of parts) {
      const m = part.match(pattern);
      const item = add(list, "li");
      if (!m) { item.textContent = part + " (cut short in the source file)"; continue; }
      const [i, j, printed, diff] = [Number(m[1]), Number(m[2]), Number(m[3]), Number(m[4])];
      const cell = cells.get(i, j);
      if (cell) cell.classList.add("bad");
      action(item, "Row " + i + ", column " + j, () => bbFocus(cells, i, j));
      item.append(": printed " + instant.format(printed) + ", the parts add up to " + instant.format(printed + diff) + " (" + (diff > 0 ? "+" : "") + instant.format(diff) + ")");
    }
    const failing = (Number(c.totals_checked) || 0) - (Number(c.totals_agree) || 0);
    const shown = list.querySelectorAll("button").length;
    if (failing > shown) add(side, "p", "The source file keeps only the first 300 characters of this list, so " + shown + " of the " + failing + " totals that do not agree are listed.", "help");
  }
  add(root, "p", "None of these tests checks that a figure is in the right row or column. Compare the layout with the page image.", "help bb-caveat");
}

function bbPage(root, meta, entry) {
  const box = add(root, "div", undefined, "bb-page");
  const bar = add(box, "div", undefined, "bb-page-bar");
  const label = add(bar, "span", "", "bb-page-label");
  const controls = add(bar, "span");
  const frame = add(box, "div", undefined, "bb-image-frame");
  const status = add(frame, "p", "", "help");
  const img = add(frame, "img");
  img.alt = "Scan of the printed page from archive.org";
  const canvas = add(frame, "canvas");
  canvas.hidden = true;
  canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", "Scan of the printed page from archive.org, rotated");
  // Sideways tables are easier to compare once the scan is turned; a canvas keeps the layout box the right shape.
  const draw = () => {
    const turn = bb.rotation || 0;
    if (!img.complete || !img.naturalWidth) return;
    status.hidden = true;
    img.hidden = turn !== 0;
    canvas.hidden = turn === 0;
    if (turn === 0) return;
    const w = img.naturalWidth, h = img.naturalHeight;
    canvas.width = turn === 180 ? w : h;
    canvas.height = turn === 180 ? h : w;
    const ctx = canvas.getContext("2d");
    ctx.save();
    ctx.translate(canvas.width / 2, canvas.height / 2);
    ctx.rotate(turn * Math.PI / 180);
    ctx.drawImage(img, -w / 2, -h / 2);
    ctx.restore();
  };
  const links = add(box, "div", undefined, "inspector-links");
  const show = () => {
    const page = bb.imagePage;
    label.textContent = "PDF page " + page + (page === entry.page ? " (this table)" : " (" + (page > entry.page ? "+" : "") + (page - entry.page) + ")");
    status.textContent = "Loading page image from archive.org…";
    status.hidden = false;
    img.hidden = true;
    canvas.hidden = true;
    img.src = bbPageImage(meta.ia, page, frame.classList.contains("zoomed") ? 0 : 1600);
    links.replaceChildren();
    link(links, bbPageLink(meta.ia, page), "Open page on archive.org ↗");
    link(links, bbPageImage(meta.ia, page), "Full-size image ↗");
    prevPage.disabled = page <= 1;
    nextPage.disabled = page >= meta.pages;
    back.hidden = page === entry.page;
  };
  img.addEventListener("load", draw);
  img.addEventListener("error", () => { status.textContent = "The page image could not be loaded from archive.org. Use the link below."; });
  const prevPage = action(controls, "◀", () => { bb.imagePage--; show(); }, "bb-small");
  prevPage.title = "Previous page";
  const back = action(controls, "This table’s page", () => { bb.imagePage = entry.page; show(); }, "bb-small");
  const nextPage = action(controls, "▶", () => { bb.imagePage++; show(); }, "bb-small");
  nextPage.title = "Next page";
  const zoom = action(controls, "Zoom", () => {
    frame.classList.toggle("zoomed");
    zoom.textContent = frame.classList.contains("zoomed") ? "Fit width" : "Zoom";
    show();
  }, "bb-small");
  const rotate = action(controls, "Rotate ↻", () => {
    bb.rotation = ((bb.rotation || 0) + 90) % 360;
    rotate.textContent = "Rotate ↻" + (bb.rotation ? " " + bb.rotation + "°" : "");
    draw();
  }, "bb-small");
  rotate.title = "Turn the scan a quarter turn clockwise (for tables printed sideways)";
  if (bb.rotation) rotate.textContent = "Rotate ↻ " + bb.rotation + "°";
  add(box, "p", "archive.org item " + meta.ia + ": image n" + (entry.page - 1) + " is PDF page " + entry.page + ". The item has as many page images as the PDF has pages, so the page shown should be the page the table was read from; if it is not, use ◀ ▶.", "help");
  show();
}

function bbExtracted(root, extracted, short, cells) {
  if (!extracted) return;
  const obs = extracted.obs[short] || [];
  const officers = extracted.officers[short] || [];
  const establishment = extracted.establishment[short] || [];
  if (!obs.length && !officers.length && !establishment.length) return;
  const section = add(root, "section", undefined, "bb-extracted");
  if (obs.length) {
    add(section, "h2", "Figures extracted from this table (" + instant.format(obs.length) + ")");
    add(section, "p", "From observations.tsv.gz. Select a row to find its source cell (or row, where the extract records no column).", "help");
    bbList(section, ["Kind", "Year of data", "Area as printed", "Measure as printed", "Unit", "Value as printed", "Value", "Source"], obs.map((o) => ({
      cells: [extracted.kinds[o[0]].replace(/^[^:]+:/, "").replaceAll("_", " "), o[1], [o[2], o[3] ? "(" + o[3] + ")" : ""].filter(Boolean).join(" "),
        o[4], o[5], o[6], o[7], o[10] || "—"],
      focus: o[8] >= 0 ? () => bbFocus(cells, o[8], o[9]) : null,
    })));
  }
  if (establishment.length) {
    add(section, "h2", "Officers in the civil establishment returns (" + instant.format(establishment.length) + ")");
    add(section, "p", "From extracted/civil_establishment.tsv. Select a row to find it in the parsed table.", "help");
    bbList(section, ["Row", "Name as printed", "Office as printed", "Department", "Appointed", "Salary as printed"], establishment.map((o) => ({
      cells: [o[0], o[1], o[2], [o[3], o[4]].filter(Boolean).join(" · "), o[5], o[6]],
      focus: () => bbFocus(cells, o[0], -1),
    })));
  }
  if (officers.length) {
    add(section, "h2", "Names in the alphabetical list of officers (" + instant.format(officers.length) + ")");
    add(section, "p", "From extracted/officers_index.tsv. Select a row to find it in the parsed table.", "help");
    bbList(section, ["Row", "Name as printed", "Office as printed", "Page"], officers.map((o) => ({
      cells: [o[0], o[1], o[2], o[3]],
      focus: () => bbFocus(cells, o[0], -1),
    })));
  }
}

function bbList(parent, fields, rows) {
  const frame = add(parent, "div", undefined, "table-frame bb-list");
  const t = add(frame, "table");
  const head = add(add(t, "thead"), "tr");
  for (const field of fields) add(head, "th", field).scope = "col";
  const body = add(t, "tbody");
  for (const row of rows) {
    const tr = add(body, "tr");
    row.cells.forEach((value, k) => {
      const td = add(tr, "td");
      if (k === 0 && row.focus) action(td, String(value ?? "—"), row.focus, "table-open");
      else td.textContent = value === "" || value == null ? "—" : String(value);
    });
  }
}

// ---- acreage series -----------------------------------------------------------------------------------------

async function bbSeries() {
  if (bb.acreage) return;
  try {
    const data = await bbFetch("acreage.json");
    if (bb.acreage) return;
    // A figure with no data year (the 1928 estimates) is placed at its volume's year and drawn hollow.
    bb.acreage = data.rows.map((r) => ({ crop: r[0], area: r[1], areaPrinted: r[2], volume: r[3], dated: r[4] > 0, year: r[4] || r[3],
      value: r[5], printed: r[6], table: r[7], level: r[8], note: r[9] }));
  } catch (error) {
    byId("bb-chart").textContent = error.message;
    return;
  }
  const crops = new Map();
  for (const row of bb.acreage) crops.set(row.crop, (crops.get(row.crop) || 0) + 1);
  const menu = byId("bb-crop");
  for (const crop of [...crops.keys()].sort()) add(menu, "option", crop.replace(/^./, (ch) => ch.toUpperCase()) + " (" + crops.get(crop) + ")").value = crop;
  menu.value = crops.has("paddy") ? "paddy" : menu.options[0]?.value;
  bbSeriesAreas();
}

function bbSeriesAreas() {
  const crop = byId("bb-crop").value;
  const rows = bb.acreage.filter((r) => r.crop === crop);
  const years = new Map();
  for (const r of rows) {
    if (!years.has(r.area)) years.set(r.area, new Set());
    years.get(r.area).add(r.year);
  }
  const menu = byId("bb-area");
  const previous = menu.options.length ? menu.value : "ceylon (island total)";
  menu.replaceChildren();
  const areas = [...years.keys()].sort((a, b) => years.get(b).size - years.get(a).size || a.localeCompare(b));
  for (const area of areas) add(menu, "option", (area || "(no area printed)") + " · " + years.get(area).size + " yr").value = area;
  menu.value = areas.includes(previous) ? previous : areas[0] ?? "";
  bbDrawSeries();
}

function bbDrawSeries() {
  const crop = byId("bb-crop").value;
  const area = byId("bb-area").value;
  const rows = bb.acreage.filter((r) => r.crop === crop && r.area === area).sort((a, b) => a.year - b.year || a.volume - b.volume);
  const root = byId("bb-chart");
  root.replaceChildren();
  byId("bb-point").replaceChildren();
  if (!rows.length) return;
  const key = add(root, "div", undefined, "bb-chart-key");
  for (const level of Object.keys(BB_LEVELS)) {
    if (!rows.some((r) => r.level === level)) continue;
    const item = add(key, "span", undefined, "bb-key-item");
    add(item, "i", undefined, "bb-dot lv-" + level);
    item.append(BB_LEVELS[level].title);
  }
  if (rows.some((r) => !r.dated)) {
    const item = add(key, "span", undefined, "bb-key-item");
    add(item, "i", undefined, "bb-dot undated");
    item.append("No single data year (shown at the volume’s year)");
  }
  const W = 520, H = 190, L = 58, R = 14, T = 12, B = 26;
  const years = rows.map((r) => r.year);
  const lowYear = Math.min(...years), highYear = Math.max(...years);
  const values = rows.map((r) => r.value);
  const high = Math.max(...values) * 1.08 || 1;
  const x = (year) => highYear === lowYear ? (L + W - R) / 2 : L + (year - lowYear) / (highYear - lowYear) * (W - L - R);
  const y = (value) => T + (1 - value / high) * (H - T - B);
  const s = svg(root, "svg", { class: "chart bb-chart", viewBox: "0 0 " + W + " " + H, role: "group", "aria-label": "Acreage of " + crop + " in " + (area || "unlabelled area") + " by year of data. Select a point to read it." });
  const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
  for (const v of [0, high / 2, high]) {
    svg(s, "line", { x1: L, x2: W - R, y1: y(v), y2: y(v), stroke: "#ded8ca" });
    svg(s, "text", { x: L - 6, y: y(v) + 3, "text-anchor": "end" }).textContent = compact.format(v);
  }
  let lastLabel = -Infinity;
  for (const year of [...new Set(years)].sort((a, b) => a - b)) {
    if (x(year) - lastLabel < 30) continue;
    lastLabel = x(year);
    svg(s, "text", { x: x(year), y: H - 8, "text-anchor": "middle" }).textContent = year;
  }
  const oneEach = new Set(years).size === years.length && rows.every((r) => r.dated);
  if (oneEach && rows.length > 1) svg(s, "polyline", { points: rows.map((r) => x(r.year) + "," + y(r.value)).join(" "), stroke: "#9aa8a3", "stroke-width": 1.5, fill: "none", "stroke-dasharray": "3 3" });
  const dots = [];
  rows.forEach((r) => {
    const sameYear = rows.filter((o) => o.year === r.year);
    const offset = sameYear.length > 1 ? (sameYear.indexOf(r) - (sameYear.length - 1) / 2) * 7 : 0;
    const when = r.dated ? String(r.year) : "no single year (" + r.volume + " volume)";
    const dot = svg(s, "circle", { cx: x(r.year) + offset, cy: y(r.value), r: 5, class: "bb-dot-svg lv-" + r.level + (r.dated ? "" : " undated"), tabindex: 0, role: "button",
      "aria-label": when + ": " + r.printed + " acres, " + BB_LEVELS[r.level].title + ", table " + r.table });
    svg(dot, "title", {}).textContent = when + " · " + r.printed + " acres · " + BB_LEVELS[r.level].title + " · " + r.table;
    const select = () => {
      dots.forEach((d) => d.classList.toggle("selected", d === dot));
      const out = byId("bb-point");
      out.replaceChildren();
      add(out, "b", when + " · " + (r.areaPrinted || "unlabelled total row") + " · " + r.printed + " acres ");
      bbBadge(out, r.level);
      out.append(" printed in the " + r.volume + " volume, ");
      action(out, r.table, () => bbOpenTable(r.table));
      if (r.note) add(out, "small", "Extraction note: " + r.note);
    };
    dot.addEventListener("click", select);
    dot.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); select(); }
    });
    dots.push(dot);
  });
}
