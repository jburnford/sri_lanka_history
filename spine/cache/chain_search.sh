#!/bin/bash
cd /home/jic823/Documents/ceylon/spine
while pgrep -f "search_places_wd.py" >/dev/null; do sleep 20; done
for t in TAXON COMMODITY ORG; do /home/jic823/miniforge3/bin/python search_names_wd.py $t 15; done
echo chain done
