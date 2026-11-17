"""The period each trade ledger table covers, from the caption printed at the head of its run of pages.

Most volumes print one set of ledgers for the calendar year. Two do not: the 1910 volume has one set for the six
months ended June 1910 and another for the twelve months ended June 1911, and the 1921 volume has one set for
each half of the year. A figure from those tables is not a calendar-year figure.

A ledger table takes the most recent caption at or before its page, of the same flow (imports or exports).
Where no caption was read for a flow (the OCR missed it), the calendar year of the volume is assumed and
`basis` says so.

Output: bluebook/extracted/trade_periods.tsv   table_id, flow, period_as_printed, months, period_end, caption_page, basis
"""
import csv, gzip, json, re, sys
from pathlib import Path

BB = Path(__file__).parent
sys.path.insert(0, str(BB / "jobs/trade_work"))
from read_trade import ledger_flow

CAPTION = re.compile(r"GENERAL\s+(IMPORTS|EXPORTS)\b[^.]{0,90}?\b(?:for|during|in)\s+(?:the\s+)?"
                     r"(Year|Six Months|Twelve Months)(?:\s+ended)?(?:\s+(January|February|March|April|May|June|July|August|"
                     r"September|October|November|December),?)?\s+(\d{4})", re.I)
MONTH = {m: i for i, m in enumerate("january february march april may june july august september october november december".split(), 1)}


def main():
    out = []
    for f in sorted((BB / "tables").glob("*.jsonl.gz")):
        key = f.name.split(".")[0]
        tables = [json.loads(l) for l in gzip.open(f, "rt")]
        ledgers = [(t["id"], t["pdf_page"], ledger_flow(t)) for t in tables if t["rows"] and ledger_flow(t)]
        if not ledgers: continue
        caps = []
        for l in gzip.open(BB / f"pages/{key}.jsonl.gz", "rt"):
            p = json.loads(l)
            for s in p["headings"] + p["text"]:
                m = CAPTION.search(re.sub(r"\s+", " ", s))
                if m:
                    months = 6 if m[2].lower().startswith("six") else 12
                    end = f"{m[4]}-{MONTH.get((m[3] or 'december').lower(), 12):02d}"
                    caps.append((p["pdf_page"], m[1].lower()[:-1], re.sub(r"\s+", " ", m[0]), months, end))
        year = int(key[:4])
        for tid, page, flow in ledgers:
            c = [x for x in caps if x[0] <= page and x[1] == flow]
            if c:
                pg, _, text, months, end = c[-1]
                out.append((tid, flow, text, months, end, pg, "caption"))
            else:
                # no caption of this flow before the table: take the period of the other flow's caption nearest before
                # it (imports and exports of one set share a period), else assume the volume's calendar year
                o = [x for x in caps if x[0] <= page]
                if o: out.append((tid, flow, o[-1][2], o[-1][3], o[-1][4], o[-1][0], "caption of the other flow"))
                else: out.append((tid, flow, "", 12, f"{year}-12", "", "assumed: calendar year of the volume"))
    with open(BB / "extracted/trade_periods.tsv", "w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["table_id", "flow", "period_as_printed", "months", "period_end", "caption_page", "basis"]); w.writerows(out)
    import collections
    print(len(out), collections.Counter((r[0].split(":")[0][2:], r[3], r[4], r[6].split(":")[0]) for r in out).most_common(40))


if __name__ == "__main__":
    main()
