#!/bin/bash
set -ex

rm -rf unt
mkdir -p unt/srv
cp -pR copyparty tests unt/
cd unt
python3 ../scripts/strip_hints/a.py

pids=()
for py in python{2,3}; do
    [ ${1:0:6} = python ] && [ $1 != $py ] && continue

    PYTHONPATH=
    [ $py = python2 ] && PYTHONPATH=../scripts/py2
    export PYTHONPATH

    nice $py -m unittest discover -s tests >/dev/null &
    pids+=($!)
done

[ "$1" ] || {
    python3 ../scripts/test/smoketest.py &
    pids+=($!)
}

for pid in ${pids[@]}; do
    wait $pid
done
