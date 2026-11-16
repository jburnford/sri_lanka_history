"""Run queries.cypher against the spine graph read-only and print compact results. Usage: run_queries.py [n ...]"""
import logging, re, sys
from pathlib import Path
from neo4j import GraphDatabase, READ_ACCESS
logging.getLogger("neo4j").setLevel(logging.ERROR)
HERE = Path(__file__).parent
auth = tuple((HERE.parent / "neo4j-local/auth-spine.env").read_text().strip().removeprefix("NEO4J_AUTH=").split("/", 1))
blocks = [b.strip() for b in re.split(r"\n(?=// \d+\.)", (HERE / "queries.cypher").read_text()) if re.match(r"// \d+\.", b.strip())]
want = set(sys.argv[1:])
with GraphDatabase.driver("bolt://127.0.0.1:7691", auth=auth) as db, db.session(database="neo4j", default_access_mode=READ_ACCESS) as s:
    for b in blocks:
        num = re.match(r"// (\d+)\.", b).group(1)
        if want and num not in want: continue
        print("\n" + b.splitlines()[0])
        q = "\n".join(l for l in b.splitlines() if not l.startswith("//")).rstrip(";")
        res = list(s.run(q))
        for r in res[:22]: print("   ", " | ".join(f"{v}" for v in r.values()))
        print(f"    ({len(res)} rows; columns: {', '.join(res[0].keys()) if res else '-'})")
