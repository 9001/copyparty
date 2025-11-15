#!/bin/bash
set -e

# usage: ./scripts/rls.sh 1.9.11 gzz 50  # create full release
# usage: ./scripts/rls.sh sfx gzz 10     # just create sfx.py + en.py + helptext
#
# if specified, keep the following sfx-args last:  gz gzz xz nopk udep fast
#
# WARNING: when creating full release, will DELETE all of ../dist/,
#   and all docker-images matching 'localhost/(copyparty|alpine)-'

[ -e make-sfx.sh ] || cd scripts
[ -e make-sfx.sh ] && [ -e deps-docker ] || {
    echo cd into the scripts folder first
    exit 1
}

v=$1; shift
[ "$v" = sfx ] &&
    rls= || rls=1

[ $rls ] && {
    printf '%s\n' "$v" | grep -qE '^[0-9\.]+$' || exit 1
    grep -E "(${v//./, })" ../copyparty/__version__.py || exit 1

    ./make-sfx.sh nopk gz
    ../dist/copyparty-sfx.py --version >/dev/null

    git tag v$v
    rm -rf ../dist
    ./make-pypi-release.sh u
    ./make-tgz-release.sh $v
}

rm -rf /tmp/pe-copyparty* ../sfx ../dist/copyparty-sfx*
./make-sfx.sh "$@"
../dist/copyparty-sfx.py --version >/dev/null
mv ../dist/copyparty-{sfx,int}.py

while [ "$1" ]; do
    case "$1" in
        gz*) break;;
        xz) break;;
        nopk) break;;
        udep) break;;
        fast) break;;
    esac
    shift
done

./make-pyz.sh 
mv ../dist/copyparty{,-int}.pyz

./make-sfx.sh re lang eng "$@" 
mv ../dist/copyparty-{sfx,en}.py

rm -rf /tmp/pe-copyparty* ../sfx
../dist/copyparty-en.py --version >/dev/null 2>&1

./make-sfx.sh re no-smb "$@"
./make-pyz.sh
mv ../dist/copyparty{,-en}.pyz
mv ../dist/copyparty{-int,}.pyz
mv ../dist/copyparty-{int,sfx}.py

./genhelp.sh

[ $rls ] || exit 0  # ----------------------------------------------------

./prep.sh
git add ../contrib/package/arch/PKGBUILD ../contrib/package/makedeb-mpr/PKGBUILD ../contrib/package/nix/copyparty/pin.json
git commit -m "update pkgs to $v"
git log | head

( cd docker
    #./make.sh purge
    ./make.sh hclean
    ./make.sh hclean
    ./make.sh hclean pull img push
)

git push
git push --all
git push --tags
git push all
git push all --all
git push all --tags
# git tag -d v$v; git push --delete origin v$v
