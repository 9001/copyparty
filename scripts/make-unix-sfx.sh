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
	(cd ~/Downloads && wget https://files.pythonhosted.org/packages/25/c8/212b1c2fd6df9eaf536384b6c6619c4e70a3afd2dffdd00e5296ffbae940/Jinja2-2.6.tar.gz)

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
#!/bin/bash
set -e

dir="$(
	printf '%s\n' "$TMPDIR" /tmp |
	awk '/./ {print; exit}'
)/pe-copyparty"

printf '%s\n' "$pybin" | grep -qE ... && [ -e "$pybin" ] && py="$pybin" ||
py="$(command -v python3)" ||
py="$(command -v python)"  ||
py="$(command -v python2)" || {
	printf '\033[1;31mpls install python\033[0m\n' >&2
	exit 1
}

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

	# delete the bundled jinja2 if we have a better one
	python3 -c 'import jinja2' 2>/dev/null &&
		rm -rf $dir/jinja2
	true
) >&2 || exit 1

PYTHONPATH=$dir exec "$py" -m copyparty "$@"

sfx_eof
EOF

echo "compressing..."
tar -c copyparty jinja2 v$ts | xz -cze9T0 >> $sfx_out
chmod 755 $sfx_out

printf "done:\n  %s\n" "$(realpath $sfx_out)"
cd ..
rm -rf sfx
