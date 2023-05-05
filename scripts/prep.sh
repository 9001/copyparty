#!/bin/bash
set -e

# general housekeeping before a release

self=$(cd -- "$(dirname "$BASH_SOURCE")"; pwd -P)
ver=$(awk '/^VERSION/{gsub(/[^0-9]/," ");printf "%d.%d.%d\n",$1,$2,$3}' copyparty/__version__.py)

update_arch_pkgbuild() {
    cd "$self/../contrib/package/arch"
    rm -rf x
    mkdir x

    sha=$(sha256sum "$self/../dist/copyparty-$ver.tar.gz" | awk '{print$1}')

    awk -v ver=$ver -v sha=$sha '
        /^pkgver=/{sub(/[0-9\.]+/,ver)};
        /^sha256sums=/{sub(/[0-9a-f]{64}/,sha)};
        1' PKGBUILD >a
    mv a PKGBUILD

    rm -rf x
}

update_nixos_pin() {
    ( cd $self/../contrib/package/nix/copyparty;
      ./update.py $self/../dist/copyparty-sfx.py )
}

update_arch_pkgbuild
update_nixos_pin
