"""Validate the de Silva review against the proposed pairs."""

import csv
import re
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
PAIR_FIELDS = ("pair_id", "desilva_id", "printed_name_key")
OUTPUT_FIELDS = PAIR_FIELDS + (
    "decision", "years_that_fit", "evidence", "outside_knowledge", "files_consulted",
)
DECISIONS = ("same_person", "probably_same", "namesake", "some_records", "unclear")
CLERICAL_OFFICES = re.compile(r"\b(?:clerk|translator|apothecary)s?\b", re.I)


def read_tsv(filename):
    with (HERE / filename).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, dialect="excel-tab", strict=True)
        return tuple(reader.fieldnames or ()), list(reader)


def check():
    _, proposed = read_tsv("input.tsv")
    fields, reviewed = read_tsv("decisions.tsv")
    assert fields == OUTPUT_FIELDS, f"Unexpected output columns: {fields}"
    assert len(reviewed) == len(proposed), "Expected one decision per input row"
    assert len({row["pair_id"] for row in reviewed}) == len(reviewed), "Duplicate pair_id"

    counts = Counter()
    test_cases = Counter()
    for pair, row in zip(proposed, reviewed):
        pair_id = pair["pair_id"]
        assert None not in row and all(value is not None for value in row.values()), pair_id
        assert all(len(value) <= 200 for value in row.values()), pair_id
        assert all(row[field] == pair[field] for field in PAIR_FIELDS), pair_id

        decision = row["decision"]
        assert decision in DECISIONS, pair_id
        assert 0 < len(row["evidence"].strip()) < 200, pair_id
        years = row["years_that_fit"]
        assert bool(years) == (decision == "some_records"), pair_id
        if years:
            assert re.fullmatch(r"[0-9]{4}(?:,[0-9]{4})*", years), pair_id
            listed = list(map(int, years.split(",")))
            first, last = map(int, pair["record_years"].split("-"))
            assert listed == sorted(set(listed)), pair_id
            assert first <= listed[0] <= listed[-1] <= last, pair_id
        if row["outside_knowledge"]:
            assert decision in {"probably_same", "namesake", "unclear"}, pair_id
        counts[decision] += 1

        person, key = row["desilva_id"], row["printed_name_key"]
        if person in {"person:hugh-clifford", "person:sir-hugh-clifford"} and key == "clifford:h":
            assert decision == "same_person", pair_id
            test_cases["Clifford"] += 1
        if (person == "person:john-de-silva" and key.startswith("de-silva:j_")
                and CLERICAL_OFFICES.search(pair["offices_by_year"])):
            assert decision == "namesake", pair_id
            test_cases["John de Silva"] += 1
        if person == "person:james-pieris" and (key == "pieris:j" or key.startswith("pieris:j_")):
            assert decision == "namesake", pair_id
            test_cases["James Pieris"] += 1
        if person == "person:ananda-coomaraswamy" and key == "coomaraswamy:a_k":
            assert decision == "probably_same", pair_id
            assert row["outside_knowledge"].strip(), pair_id
            test_cases["Coomaraswamy"] += 1

    assert set(test_cases) == {"Clifford", "John de Silva", "James Pieris", "Coomaraswamy"}
    for decision in DECISIONS:
        print(f"{decision}\t{counts[decision]}")
    print(f"total\t{sum(counts.values())}")


if __name__ == "__main__":
    check()
