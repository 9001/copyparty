#!/bin/bash
set -ex

pids=()
for py in python{2,3}; do
    nice $py -m unittest discover -s tests >/dev/null &
    pids+=($!)
done

python3 scripts/test/smoketest.py &
pids+=($!)

for pid in ${pids[@]}; do
    wait $pid
done
