#!/bin/bash
set -e

parallel=2

cd ~/dev/copyparty/scripts

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
f=../dist/copyparty-sfx
[ -e $f.py ] || 
    f=../dist/copyparty-sfx-gz

$f.py -h >/dev/null

[ $parallel -gt 1 ] && {
    printf '\033[%s' s 2r H "0;1;37;44mbruteforcing sfx size -- press enter to terminate" K u "7m $* " K $'27m\n'
    trap "rm -f .sfx-run; printf '\033[%s' s r u" INT TERM EXIT
    touch .sfx-run
    for ((a=0; a<$parallel; a++)); do
        while [ -e .sfx-run ]; do
            CSN=sfx$a ./make-sfx.sh re "$@"
            mv $f$a.py $f.$(wc -c <$f$a.py | awk '{print$1}').py
        done &
    done
    read
    exit
}

while true; do
    mv $f.py $f.$(wc -c <$f.py | awk '{print$1}').py
    ./make-sfx.sh re "$@"
done

# git tag -d v$v; git push --delete origin v$v
