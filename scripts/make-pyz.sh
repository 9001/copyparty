#!/bin/bash
set -e
echo

# port install gnutar gsed coreutils
gtar=$(command -v gtar || command -v gnutar) || true
[ ! -z "$gtar" ] && command -v gsed >/dev/null && {
	tar()  { $gtar "$@"; }
	sed()  { gsed  "$@"; }
	command -v grealpath >/dev/null &&
		realpath() { grealpath "$@"; }
}

targs=(--owner=1000 --group=1000)
[ "$OSTYPE" = msys ] &&
	targs=()

[ -e copyparty/__main__.py ] || cd ..
[ -e copyparty/__main__.py ] || {
	echo "run me from within the project root folder"
	echo
	exit 1
}

[ -e sfx/copyparty/__main__.py ] || {
    echo "run ./scripts/make-sfx.py first"
    echo
    exit 1
}

rm -rf pyz
mkdir -p pyz
cd pyz

cp -pR ../sfx/{copyparty,partftpy} .
cp -pR ../sfx/{ftp,j2}/* .

ts=$(date -u +%s)
hts=$(date -u +%Y-%m%d-%H%M%S)
ver="$(cat ../sfx/ver)"

mkdir -p ../dist
pyz_out=../dist/copyparty.pyz

echo creating z.tar
( cd copyparty
  tar -cf z.tar "${targs[@]}" --numeric-owner web res
  rm -rf web res
)

echo creating loader
sed -r 's/^(VER = ).*/\1"'"$ver"'"/; s/^(STAMP = ).*/\1'$(date +%s)/ \
    <../scripts/ziploader.py \
    >__main__.py

echo creating pyz
rm -f $pyz_out
zip -9 -q -r $pyz_out *

echo done:
echo "  $(realpath $pyz_out)"
