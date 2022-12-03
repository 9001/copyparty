#!/bin/bash
set -ex

rm -rf unt
mkdir -p unt/srv
cp -pR copyparty tests unt/
cd unt

# resolve symlinks
set +x
find -type l |
while IFS= read -r f1; do (
    cd "${f1%/*}"
    f1="./${f1##*/}"
    f2="$(readlink "$f1")"
    [ -e "$f2" ] || f2="../$f2"
    [ -e "$f2" ] || {
        echo could not resolve "$f1"
        exit 1
    }
    rm "$f1"
    cp -p "$f2" "$f1"
); done
set -x

python3 ../scripts/strip_hints/a.py

pids=()
for py in python{2,3}; do
    [ ${1:0:6} = python ] && [ $1 != $py ] && continue

    PYTHONPATH=
    [ $py = python2 ] && PYTHONPATH=../scripts/py2:../sfx/py37
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
