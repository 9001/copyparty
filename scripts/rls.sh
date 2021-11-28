#!/bin/bash
set -e

cd ~/dev/copyparty/scripts

v=$1
printf '%s\n' "$v" | grep -qE '^[0-9\.]+$' || exit 1
grep -E "(${v//./, })" ../copyparty/__version__.py || exit 1

git push all
git tag v$v
git push all --tags

rm -rf ../dist

./make-pypi-release.sh u
(cd .. && python3 ./setup.py clean2)

./make-tgz-release.sh $v

rm -f ../dist/copyparty-sfx.*
./make-sfx.sh no-sh
../dist/copyparty-sfx.py -h

ar=
while true; do
    for ((a=0; a<100; a++)); do
        for f in ../dist/copyparty-sfx.{py,sh}; do
            [ -e $f ] || continue;
            mv $f $f.$(wc -c <$f | awk '{print$1}')
        done
        ./make-sfx.sh re $ar
    done
    ar=no-sh
done

# git tag -d v$v; git push --delete origin v$v
