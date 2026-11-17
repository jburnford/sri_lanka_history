"""Segment Map 7 (-> ws7.npy) and the cleaned Map 17 (-> ws17.npy). Tables: seeds7.tsv, barriers7.tsv, seeds17.tsv, barriers17.tsv."""
import numpy as np, sys
from hd_lib import *
which=sys.argv[1] if len(sys.argv)>1 else 'both'
if which in ('7','both'):
    ink=inkmask('full-15.png')
    ink=add_barriers(ink,[r[:4] for r in read_tsv('barriers7.tsv',4)])
    ws=grow(ink,T=9,extra_seeds=read_tsv('seeds7.tsv',3))
    print('map 7 regions',ws.max()); np.save('ws7.npy',ws)
if which in ('17','both'):
    ink=inkmask('p39-39.png')
    ink=clear_hatched_areas(ink,(900,3700,2300,4850))
    ink=remove_dots(ink)
    ink=add_barriers(ink,[r[:4] for r in read_tsv('barriers17.tsv',4)])
    ws=grow(ink,T=13,extra_seeds=read_tsv('seeds17.tsv',3))
    print('map 17 regions',ws.max()); np.save('ws17.npy',ws)
