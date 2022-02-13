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
f=../dist/copyparty-sfx.py
./make-sfx.sh
$f -h

while true; do
    mv $f $f.$(wc -c <$f | awk '{print$1}')
    ./make-sfx.sh re $ar
done

# git tag -d v$v; git push --delete origin v$v
