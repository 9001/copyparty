#!/bin/bash
set -e
echo


# optional args:
#
# `clean` uses files from git (everything except web/deps),
#   so local changes won't affect the produced sfx
#
# `re` does a repack of an sfx which you already executed once
#   (grabs files from the sfx-created tempdir), overrides `clean`
#
# `no-ogv` saves ~500k by removing the opus/vorbis audio codecs
#   (only affects apple devices; everything else has native support)
#
# `no-cm` saves ~90k by removing easymde/codemirror
#   (the fancy markdown editor)


# port install gnutar findutils gsed coreutils
gtar=$(command -v gtar || command -v gnutar) || true
[ ! -z "$gtar" ] && command -v gfind >/dev/null && {
	tar()  { $gtar "$@"; }
	sed()  { gsed  "$@"; }
	find() { gfind "$@"; }
	sort() { gsort "$@"; }
	unexpand() { gunexpand "$@"; }
	command -v grealpath >/dev/null &&
		realpath() { grealpath "$@"; }

	[ -e /opt/local/bin/bzip2 ] &&
		bzip2() { /opt/local/bin/bzip2 "$@"; }
}

gawk=$(command -v gawk || command -v gnuawk || command -v awk)
awk() { $gawk "$@"; }

pybin=$(command -v python3 || command -v python) || {
	echo need python
	exit 1
}

[ -e copyparty/__main__.py ] || cd ..
[ -e copyparty/__main__.py ] ||
{
	echo "run me from within the project root folder"
	echo
	exit 1
}

use_gz=
do_sh=1
do_py=1
while [ ! -z "$1" ]; do
	[ "$1" = clean  ] && clean=1  && shift && continue
	[ "$1" = re     ] && repack=1 && shift && continue
	[ "$1" = gz     ] && use_gz=1 && shift && continue
	[ "$1" = no-ogv ] && no_ogv=1 && shift && continue
	[ "$1" = no-cm  ] && no_cm=1  && shift && continue
	[ "$1" = no-sh  ] && do_sh=   && shift && continue
	[ "$1" = no-py  ] && do_py=   && shift && continue
	break
done

tmv() {
	touch -r "$1" t
	mv t "$1"
}

rm -rf sfx/*
mkdir -p sfx build
cd sfx

[ $repack ] && {
	old="$(
		printf '%s\n' "$TMPDIR" /tmp |
		awk '/./ {print; exit}'
	)/pe-copyparty"

	echo "repack of files in $old"
	cp -pR "$old/"*{dep-j2,copyparty} .
}

[ $repack ] || {
	echo collecting jinja2
	f="../build/Jinja2-2.11.3.tar.gz"
	[ -e "$f" ] ||
		(url=https://files.pythonhosted.org/packages/4f/e7/65300e6b32e69768ded990494809106f87da1d436418d5f1367ed3966fd7/Jinja2-2.11.3.tar.gz;
		wget -O$f "$url" || curl -L "$url" >$f)

	tar -zxf $f
	mv Jinja2-*/src/jinja2 .
	rm -rf Jinja2-*
	
	echo collecting markupsafe
	f="../build/MarkupSafe-1.1.1.tar.gz"
	[ -e "$f" ] ||
		(url=https://files.pythonhosted.org/packages/b9/2e/64db92e53b86efccfaea71321f597fa2e1b2bd3853d8ce658568f7a13094/MarkupSafe-1.1.1.tar.gz;
		wget -O$f "$url" || curl -L "$url" >$f)

	tar -zxf $f
	mv MarkupSafe-*/src/markupsafe .
	rm -rf MarkupSafe-* markupsafe/_speedups.c

	mkdir dep-j2/
	mv {markupsafe,jinja2} dep-j2/

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
}

ver=
git describe --tags >/dev/null 2>/dev/null && {
	git_ver="$(git describe --tags)";  # v0.5.5-2-gb164aa0
	ver="$(printf '%s\n' "$git_ver" | sed -r 's/^v//')";
	t_ver=

	printf '%s\n' "$git_ver" | grep -qE '^v[0-9\.]+$' && {
		# short format (exact version number)
		t_ver="$(printf '%s\n' "$ver" | sed -r 's/\./, /g')";
	}

	printf '%s\n' "$git_ver" | grep -qE '^v[0-9\.]+-[0-9]+-g[0-9a-f]+$' && {
		# long format (unreleased commit)
		t_ver="$(printf '%s\n' "$ver" | sed -r 's/\./, /g; s/(.*) (.*)/\1 "\2"/')"
	}

	[ -z "$t_ver" ] && {
		printf 'unexpected git version format: [%s]\n' "$git_ver"
		exit 1
	}

	dt="$(git log -1 --format=%cd --date=short | sed -E 's/-0?/, /g')"
	printf 'git %3s: \033[36m%s\033[0m\n' ver "$ver" dt "$dt"
	sed -ri '
		s/^(VERSION =)(.*)/#\1\2\n\1 ('"$t_ver"')/;
		s/^(S_VERSION =)(.*)/#\1\2\n\1 "'"$ver"'"/;
		s/^(BUILD_DT =)(.*)/#\1\2\n\1 ('"$dt"')/;
	' copyparty/__version__.py
}

[ -z "$ver" ] && 
	ver="$(awk '/^VERSION *= \(/ {
		gsub(/[^0-9,]/,""); gsub(/,/,"."); print; exit}' < copyparty/__version__.py)"

ts=$(date -u +%s)
hts=$(date -u +%Y-%m%d-%H%M%S) # --date=@$ts (thx osx)

mkdir -p ../dist
sfx_out=../dist/copyparty-sfx

echo cleanup
find .. -name '*.pyc' -delete
find .. -name __pycache__ -delete

# especially prevent osx from leaking your lan ip (wtf apple)
find .. -type f \( -name .DS_Store -or -name ._.DS_Store \) -delete
find .. -type f -name ._\* | while IFS= read -r f; do cmp <(printf '\x00\x05\x16') <(head -c 3 -- "$f") && rm -f -- "$f"; done

echo use smol web deps
rm -f copyparty/web/deps/*.full.* copyparty/web/Makefile

# it's fine dw
grep -lE '\.full\.(js|css)' copyparty/web/* |
while IFS= read -r x; do
	sed -r 's/\.full\.(js|css)/.\1/g' <"$x" >t
	tmv "$x"
done

[ $no_ogv ] &&
	rm -rf copyparty/web/deps/{dynamicaudio,ogv}*

[ $no_cm ] && {
	rm -rf copyparty/web/mde.* copyparty/web/deps/easymde*
	echo h > copyparty/web/mde.html
	f=copyparty/web/md.html
	sed -r '/edit2">edit \(fancy/d' <$f >t && tmv "$f"
}

[ $repack ] ||
find | grep -E '\.py$' |
  grep -vE '__version__' |
  tr '\n' '\0' |
  xargs -0 $pybin ../scripts/uncomment.py

f=dep-j2/jinja2/constants.py
awk '/^LOREM_IPSUM_WORDS/{o=1;print "LOREM_IPSUM_WORDS = u\"a\"";next} !o; /"""/{o=0}' <$f >t
tmv "$f"

# up2k goes from 28k to 22k laff
echo entabbening
find | grep -E '\.css$' | while IFS= read -r f; do
	awk '{
		sub(/^[ \t]+/,"");
		sub(/[ \t]+$/,"");
		$0=gensub(/^([a-z-]+) *: *(.*[^ ]) *;$/,"\\1:\\2;","1");
		sub(/ +\{$/,"{");
		gsub(/, /,",")
	}
	!/\}$/ {printf "%s",$0;next}
	1
	' <$f | sed 's/;\}$/}/' >t
	tmv "$f"
done
find | grep -E '\.(js|html)$' | while IFS= read -r f; do
	unexpand -t 4 --first-only <"$f" >t
	tmv "$f"
done


gzres() {
command -v pigz &&
	pk='pigz -11 -J 34 -I 100' ||
	pk='gzip'

echo "$pk"
find | grep -E '\.(js|css)$' | grep -vF /deps/ | while IFS= read -r f; do
	echo -n .
	$pk "$f"
done
echo
}
gzres


echo gen tarlist
for d in copyparty dep-j2; do find $d -type f; done |
sed -r 's/(.*)\.(.*)/\2 \1/' | LC_ALL=C sort |
sed -r 's/([^ ]*) (.*)/\2.\1/' | grep -vE '/list1?$' > list1

(grep -vE '\.(gz|br)$' list1; grep -E '\.(gz|br)$' list1) >list || true

echo creating tar
args=(--owner=1000 --group=1000)
[ "$OSTYPE" = msys ] &&
	args=()

tar -cf tar "${args[@]}" --numeric-owner -T list

pc=bzip2
pe=bz2
[ $use_gz ] && pc=gzip && pe=gz

echo compressing tar
# detect best level; bzip2 -7 is usually better than -9
[ $do_py ] && { for n in {2..9}; do cp tar t.$n; $pc  -$n t.$n & done; wait; mv -v $(ls -1S t.*.$pe | tail -n 1) tar.bz2; }
[ $do_sh ] && { for n in {2..9}; do cp tar t.$n; xz -ze$n t.$n & done; wait; mv -v $(ls -1S t.*.xz  | tail -n 1) tar.xz; }
rm t.* || true
exts=()


[ $do_sh ] && {
exts+=(.sh)
echo creating unix sfx
(
	sed "s/PACK_TS/$ts/; s/PACK_HTS/$hts/; s/CPP_VER/$ver/" <../scripts/sfx.sh |
	grep -E '^sfx_eof$' -B 9001;
	cat tar.xz
) >$sfx_out.sh
}


[ $do_py ] && {
	echo creating generic sfx

	py=../scripts/sfx.py
	suf=
	[ $use_gz ] && {
		sed -r 's/"r:bz2"/"r:gz"/' <$py >$py.t
		py=$py.t
		suf=-gz
	}

	$pybin $py --sfx-make tar.bz2 $ver $ts
	mv sfx.out $sfx_out$suf.py
	
	exts+=($suf.py)
	[ $use_gz ] &&
		rm $py
}


chmod 755 $sfx_out*

printf "done:\n"
for ext in ${exts[@]}; do
	printf "  %s\n" "$(realpath $sfx_out)"$ext
done

# apk add bash python3 tar xz bzip2
# while true; do ./make-sfx.sh; for f in ..//dist/copyparty-sfx.{sh,py}; do mv $f $f.$(wc -c <$f | awk '{print$1}'); done; done
