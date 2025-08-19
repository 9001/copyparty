#!/bin/bash
set -e

# if specified, keep the following sfx flags last: gz gzz fast

parallel=1

[ -e make-sfx.sh ] || cd scripts
[ -e make-sfx.sh ] && [ -e deps-docker ] || {
    echo cd into the scripts folder first
    exit 1
}

v=$1

[ "$v" = sfx ] || {
    printf '%s\n' "$v" | grep -qE '^[0-9\.]+$' || exit 1
    grep -E "(${v//./, })" ../copyparty/__version__.py || exit 1

    git push all
    git tag v$v
    git push all --tags

    rm -rf ../dist

    ./make-pypi-release.sh u
    (cd .. && python3 ./setup.py clean2)

    ./make-tgz-release.sh $v
}

rm -f ../dist/copyparty-sfx*
shift
./make-sfx.sh "$@"
../dist/copyparty-sfx.py --version >/dev/null
mv ../dist/copyparty-{sfx,int}.py

while [ "$1" ]; do
    case "$1" in
        gz*) break;;
        fast) break;;
    esac
    shift
done

./make-pyz.sh 

./make-sfx.sh re lang eng "$@" 
mv ../dist/copyparty-{sfx,en}.py
mv ../dist/copyparty-{int,sfx}.py

# git tag -d v$v; git push --delete origin v$v
