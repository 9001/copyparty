#!/bin/bash
set -e

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
f=../dist/copyparty-sfx
[ -e $f.py ] && s= || s=-gz

$f$s.py --version >/dev/null

[ $parallel -gt 1 ] && {
    printf '\033[%s' s 2r H "0;1;37;44mbruteforcing sfx size -- press enter to terminate" K u "7m $* " K $'27m\n'
    trap "rm -f .sfx-run; printf '\033[%s' s r u" INT TERM EXIT
    touch .sfx-run
    min=99999999
    for ((a=0; a<$parallel; a++)); do
        while [ -e .sfx-run ]; do
            CSN=$a ./make-sfx.sh re "$@"
            sz=$(wc -c <$f$a$s.py | awk '{print$1}')
            [ $sz -ge $min ] && continue
            mv $f$a$s.py $f$s.py.$sz
            min=$sz
        done &
    done
    read
    exit
}

while true; do
    mv $f$s.py $f$s.$(wc -c <$f$s.py | awk '{print$1}').py
    ./make-sfx.sh re "$@"
done

# git tag -d v$v; git push --delete origin v$v
