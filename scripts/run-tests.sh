#!/bin/bash
set -ex

pids=()
for py in python{2,3}; do
    $py -m unittest discover -s tests >/dev/null &
    pids+=($!)
done

for pid in ${pids[@]}; do
    wait $pid
done
