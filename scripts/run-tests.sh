#!/bin/bash
set -ex

if uname | grep -iE '^(msys|mingw)'; then
    pids=()

    python -m unittest discover -s tests >/dev/null &
    pids+=($!)

    python scripts/test/smoketest.py &
    pids+=($!)

    for pid in ${pids[@]}; do
        wait $pid
    done
    exit $?
fi

# osx support
gtar=$(command -v gtar || command -v gnutar) || true
[ ! -z "$gtar" ] && command -v gfind >/dev/null && {
	tar()  { $gtar "$@"; }
	sed()  { gsed  "$@"; }
	find() { gfind "$@"; }
	sort() { gsort "$@"; }
	command -v grealpath >/dev/null &&
		realpath() { grealpath "$@"; }
}

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
    [ "${1:0:6}" = python ] && [ "$1" != $py ] && continue

    PYTHONPATH=
    [ $py = python2 ] && PYTHONPATH=../scripts/py2:../sfx/py37:../sfx/j2
    export PYTHONPATH

    [ $py = python2 ] && py=$(command -v python2.7 || echo $py)

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
