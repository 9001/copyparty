#!/bin/bash
set -e

# general housekeeping before a release

self=$(cd -- "$(dirname "$BASH_SOURCE")"; pwd -P)
ver=$(awk '/^VERSION/{gsub(/[^0-9]/," ");printf "%d.%d.%d\n",$1,$2,$3}' copyparty/__version__.py)

update_arch_pkgbuild() {
    cd "$self/../contrib/package/arch"
    rm -rf x
    mkdir x

    (echo "$self/../dist/copyparty-sfx.py"
    awk -v self="$self" '
        /^\)/{o=0}
        /^source=/{o=1;next}
        {
            sub(/..pkgname./,"copyparty");
            sub(/.*pkgver./,self "/..");
            sub(/^ +"/,"");sub(/"/,"")
        }
        o&&!/https/' PKGBUILD
    ) |
    xargs sha256sum > x/sums

    (awk -v ver=$ver '
        /^pkgver=/{sub(/[0-9\.]+/,ver)};
        /^sha256sums=/{exit};
        1' PKGBUILD
    echo -n 'sha256sums=('
    p=; cat x/sums | while read s _; do
        echo "$p\"$s\""
        p='            '
    done
    awk '/^sha256sums=/{o=1} o&&/^\)/{o=2} o==2' PKGBUILD
    ) >a
    mv a PKGBUILD

    rm -rf x
}

update_arch_pkgbuild
