"""Display selected source tables: python inspect_tables.py YEAR PAGE [PAGE ...]."""
import gzip,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
y=int(sys.argv[1]); pages=set(map(int,sys.argv[2:]))
for l in gzip.open(ROOT/f'tables/{y}.jsonl.gz','rt'):
 t=json.loads(l)
 if t['pdf_page'] in pages:
  print('\n',t['id'],t.get('printed_page'),t.get('section'),t['headings'],'header_rows',t['header_rows'])
  for i,r in enumerate(t['rows']):print(i,repr(r))
