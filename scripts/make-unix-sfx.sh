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

which md5sum 2>/dev/null >/dev/null &&
	md5sum=md5sum ||
	md5sum="md5 -r"

[[ -e copyparty/__main__.py ]] || cd ..
[[ -e copyparty/__main__.py ]] ||
{
	echo "run me from within the project root folder"
	echo
	exit 1
}

rm -rf sfx
mkdir sfx
cd sfx

f=~/Downloads/Jinja2-2.6.tar.gz
[ -e "$f" ] ||
	(url=https://files.pythonhosted.org/packages/25/c8/212b1c2fd6df9eaf536384b6c6619c4e70a3afd2dffdd00e5296ffbae940/Jinja2-2.6.tar.gz;
	cd ~/Downloads && wget "$url" || curl -LO "$url")

tar -xf $f
mv Jinja2-*/jinja2 .
rm -rf Jinja2-*

[ $clean ] && {
	(cd .. && git archive master) | tar -x copyparty
	(cd .. && tar -c copyparty/web/deps) | tar -x
}
[ $clean ] ||
	(cd .. && tar -c copyparty) | tar -x

ver="$(awk '/^VERSION *= \(/ {
	gsub(/[^0-9,]/,""); gsub(/,/,"."); print; exit}' < ../copyparty/__version__.py)"

ts=$(date -u +%s)
hts=$(date -u +%Y-%m%d-%H%M%S) # --date=@$ts (thx osx)
echo h > v$ts

mkdir -p ../dist
sfx_out=../dist/copyparty-$ver.sfx

sed "s/PACK_TS/$ts/; s/PACK_HTS/$hts/; s/CPP_VER/$ver/" >$sfx_out <<'EOF'
# use current/default shell
set -e

dir="$(
	printf '%s\n' "$TMPDIR" /tmp |
	awk '/./ {print; exit}'
)/pe-copyparty"

[ -e "$dir/vPACK_TS" ] || (
	printf '\033[36munpacking copyparty vCPP_VER (sfx-PACK_HTS)\033[1;30m\n\n'
	mkdir -p "$dir.$$"
	ofs=$(awk '$0=="sfx_eof" {print NR+1; exit}' < "$0")
	
	[ -z "$ofs" ] && {
		printf '\033[31mabort: could not find SFX boundary\033[0m\n'
		exit 1
	}
	tail -n +$ofs "$0" | tar -JxC "$dir.$$"
	ln -nsf "$dir.$$" "$dir"
	printf '\033[0m'
	
	now=$(date -u +%s)
	for d in "$dir".*; do
		ts=$(stat -c%Y -- "$d" 2>/dev/null) ||
		ts=$(stat -f %m%n -- "$d" 2>/dev/null)

		[ $((now-ts)) -gt 300 ] &&
			rm -rf "$d"
	done
	true
) >&2 || exit 1

# detect available pythons
(IFS=:; for d in $PATH; do
	printf '%s\n' "$d"/python* "$d"/pypy*;
done) | grep -E '(python|pypy)[0-9\.-]*$' > $dir/pys || true

# see if we made a choice before
[ -z "$pybin" ] && pybin="$(cat $dir/py 2>/dev/null || true)"

# otherwise find a python with jinja2
[ -z "$pybin" ] && pybin="$(cat $dir/pys | while IFS= read -r _py; do
	printf '\033[1;30mlooking for jinja2 in [%s]\033[0m\n' "$_py" >&2
	$_py -c 'import jinja2' 2>/dev/null || continue
	printf '%s\n' "$_py"
	rm -rf $dir/jinja2
	break
done)"

# otherwise find python2 (bundled jinja2 is way old)
[ -z "$pybin" ] && {
	printf '\033[0;33mcould not find jinja2; will use py2 + the bundled version\033[0m\n' >&2
	pybin="$(cat $dir/pys | while IFS= read -r _py; do
		printf '\033[1;30mtesting if py2 [%s]\033[0m\n' "$_py" >&2
		_ver=$($_py -c 'import sys; sys.stdout.write(str(sys.version_info[0]))' 2>/dev/null) || continue
		[ $_ver = 2 ] || continue
		printf '%s\n' "$_py"
		break
	done)"
}

[ -z "$pybin" ] && {
	printf '\033[1;31m\ncould not find a python with jinja2 installed; please do one of these:\n\n  pip install --user jinja2\n\n  install python2\033[0m\n\n' >&2
	exit 1
}

printf '\033[1;30musing [%s]. you can reset with this:\n  rm -rf %s*\033[0m\n\n' "$pybin" "$dir"
printf '%s\n' "$pybin" > $dir/py

PYTHONPATH=$dir exec "$pybin" -m copyparty "$@"

sfx_eof
EOF

echo "compressing..."
tar -c copyparty jinja2 v$ts | xz -cze9T0 >> $sfx_out
chmod 755 $sfx_out

printf "done:\n  %s\n" "$(realpath $sfx_out)"
cd ..
rm -rf sfx
