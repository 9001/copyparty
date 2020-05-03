#!/bin/bash
set -e
echo

# clean=1 to export clean files from git;
# will use current working tree otherwise
clean=1
clean=

tar=$( which gtar  2>/dev/null || which tar)
sed=$( which gsed  2>/dev/null || which sed)
find=$(which gfind 2>/dev/null || which find)
sort=$(which gsort 2>/dev/null || which sort)

[[ -e copyparty/__main__.py ]] || cd ..
[[ -e copyparty/__main__.py ]] ||
{
	echo "run me from within the project root folder"
	echo
	exit 1
}

$find -name '*.pyc' -delete
$find -name __pycache__ -delete

rm -rf sfx/*
mkdir -p sfx build
cd sfx

echo collecting jinja2
f="../build/Jinja2-2.6.tar.gz"
[ -e "$f" ] ||
	(url=https://files.pythonhosted.org/packages/25/c8/212b1c2fd6df9eaf536384b6c6619c4e70a3afd2dffdd00e5296ffbae940/Jinja2-2.6.tar.gz;
	 wget -O$f "$url" || curl -L "$url" >$f)

tar -zxf $f
mv Jinja2-*/jinja2 .
rm -rf Jinja2-*

# msys2 tar is bad, make the best of it
echo collecting source
[ $clean ] && {
	(cd .. && git archive master >tar) && tar -xf ../tar copyparty
	(cd .. && tar -cf tar copyparty/web/deps) && tar -xf ../tar
}
[ $clean ] || {
	(cd .. && tar -cf tar copyparty) && tar -xf ../tar
}
rm -f ../tar

echo creating tar
ver="$(awk '/^VERSION *= \(/ {
	gsub(/[^0-9,]/,""); gsub(/,/,"."); print; exit}' < ../copyparty/__version__.py)"

tar -cf tar copyparty jinja2

echo compressing tar
bzip2 -9 tar

echo creating sfx
python ../scripts/sfx.py --sfx-make tar.bz2 $ver

mkdir -p ../dist
sfx_out=../dist/copyparty-$ver-sfx.py
mv sfx.out $sfx_out
chmod 755 $sfx_out

printf "done:\n  %s\n" "$(realpath $sfx_out)"
cd ..
rm -rf sfx
