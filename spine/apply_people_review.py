"""Fold the research assistant's person check into the spine as a human-review overlay.

Reads the latest export in gold/*/ (never edited) and the frozen gold profile table, and writes
grounding/people_review.jsonl: one row per profile the RA answered, with her verdict, her note, and what the
spine does with it. Then rewrites grounding/people.jsonl with the overlay applied:
  proposed   RA confirmed the pipeline's QID          -> review_status ra_confirmed
  other      RA found a QID the pipeline did not have -> QID added, qid_source ra_review, pending a second look
  none       RA says no Wikidata item fits            -> no QID; mint a local id
  unsure / ? RA could not decide                      -> unchanged, review_status ra_unsure
  mixed      RA says the profile holds several people -> mixed_profile flag; profile-level identity must not
                                                         be applied to every mention
"""
import csv, glob, json
from common import *

def main():
    export = sorted(glob.glob(str(HERE / "gold/*/person_check_*.tsv")))[-1]
    gp = {r["gid"]: r for r in csv.DictReader(open(HERE / "gold/scorer/gold_profiles.tsv"), delimiter="\t")}
    rows = list(csv.DictReader(open(export, encoding="utf-8-sig"), delimiter="\t"))
    ment = {}
    for r in rows:
        if r["row_type"] == "mention" and r["mention_certainty"]:
            ment.setdefault(r["gid"], []).append({"mention_key": r["mention_key"], "certainty": int(r["mention_certainty"])})
    review = {}
    for r in rows:
        if r["row_type"] != "person" or not (r["one_person"] or r["wd_choice"]): continue
        g = gp[r["gid"]]
        d = {"profile_id": g["tap_id"], "gold_id": r["gid"], "name": g["display"], "reviewer": r["student"],
             "export": Path(export).name, "pipeline_qid": g["final_qid"] if g["final_qid"] not in ("", "none") else None,
             "ra_one_person": r["one_person"], "ra_wd_choice": r["wd_choice"],
             "ra_qid": r["wd_qid"] if r["wd_qid"].startswith("Q") else None, "ra_note": r["note"],
             "ra_mention_ratings": ment.get(r["gid"], [])}
        d["action"] = {"proposed": "confirm", "other": "add_qid", "none": "no_wikidata_item", "unsure": "leave"}.get(r["wd_choice"], "leave")
        d["mixed_profile"] = r["one_person"] == "mixed"
        review[g["tap_id"]] = d
    with open(HERE / "grounding/people_review.jsonl", "w") as fh:
        for d in review.values(): fh.write(json.dumps(d, ensure_ascii=False) + "\n")
    people = read_jsonl(HERE / "grounding/people.jsonl")
    seen = set()
    for p in people:
        d = review.get(p["profile_id"])
        if not d: continue
        seen.add(p["profile_id"])
        p["mixed_profile"] = d["mixed_profile"]
        if d["action"] == "confirm": p["review_status"] = "ra_confirmed"
        elif d["action"] == "add_qid":
            p.update(wikidata_qid=d["ra_qid"], qid_source="ra_review", qid_confidence="ra_" + ("unsure" if d["ra_one_person"] == "?" else "found"),
                     review_status="ra_found_qid")
        elif d["action"] == "no_wikidata_item": p["review_status"] = "ra_no_wikidata_item"
        else: p["review_status"] = "ra_unsure"
    for pid, d in review.items():          # profiles the pipeline had not linked at all
        if pid in seen: continue
        people.append({"type": "PERSON", "profile_id": pid, "name": d["name"], "wikidata_qid": d["ra_qid"] if d["action"] == "add_qid" else None,
                       "qid_source": "ra_review" if d["action"] == "add_qid" else None, "colist_person_id": None,
                       "mixed_profile": d["mixed_profile"], "source": "RA review only",
                       "review_status": {"add_qid": "ra_found_qid", "no_wikidata_item": "ra_no_wikidata_item"}.get(d["action"], "ra_unsure")})
    with open(HERE / "grounding/people.jsonl", "w") as fh:
        for p in people: fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    import collections
    print("reviewed profiles:", len(review), dict(collections.Counter(d["action"] for d in review.values())), "mixed:", sum(d["mixed_profile"] for d in review.values()))
    for p in people:
        if p["profile_id"] in review:
            print(f"  {p['name'][:20]:20} {p['review_status']:20} qid={p.get('wikidata_qid')} col={p.get('colist_person_id')} mixed={p.get('mixed_profile')}")

if __name__ == "__main__":
    main()
