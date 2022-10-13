#!/bin/bash
set -e
echo

help() { exec cat <<'EOF'

# optional args:
#
# `clean` uses files from git (everything except web/deps),
#   so local changes won't affect the produced sfx
#
# `re` does a repack of an sfx which you already executed once
#   (grabs files from the sfx-created tempdir), overrides `clean`
#
# `ox` builds a pyoxidizer exe instead of py
#
# `gz` creates a gzip-compressed python sfx instead of bzip2
#
# `lang` limits which languages/translations to include,
#   for example `lang eng` or `lang eng|nor`
#
# `no-cm` saves ~82k by removing easymde/codemirror
#   (the fancy markdown editor)
#
# `no-hl` saves ~41k by removing syntax hilighting in the text viewer
#
# `no-fnt` saves ~9k by removing the source-code-pro font
#   (browsers will try to use 'Consolas' instead)
#
# `no-dd` saves ~2k by removing the mouse cursor
#
# ---------------------------------------------------------------------
#
# if you are on windows, you can use msys2:
#   PATH=/c/Users/$USER/AppData/Local/Programs/Python/Python310:"$PATH" ./make-sfx.sh fast

EOF
}

# port install gnutar findutils gsed coreutils
gtar=$(command -v gtar || command -v gnutar) || true
[ ! -z "$gtar" ] && command -v gfind >/dev/null && {
	tar()  { $gtar "$@"; }
	sed()  { gsed  "$@"; }
	find() { gfind "$@"; }
	sort() { gsort "$@"; }
	shuf() { gshuf "$@"; }
	nproc() { gnproc; }
	sha1sum() { shasum "$@"; }
	unexpand() { gunexpand "$@"; }
	command -v grealpath >/dev/null &&
		realpath() { grealpath "$@"; }

	[ -e /opt/local/bin/bzip2 ] &&
		bzip2() { /opt/local/bin/bzip2 "$@"; }
}

gawk=$(command -v gawk || command -v gnuawk || command -v awk)
awk() { $gawk "$@"; }

targs=(--owner=1000 --group=1000)
[ "$OSTYPE" = msys ] &&
	targs=()

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

[ $CSN ] ||
	CSN=sfx

langs=
use_gz=
zopf=2560
while [ ! -z "$1" ]; do
	case $1 in
		clean)  clean=1  ; ;;
		re)     repack=1 ; ;;
		ox)     use_ox=1 ; ;;
		gz)     use_gz=1 ; ;;
		gzz)    shift;use_gzz=$1;use_gz=1; ;;
		no-fnt) no_fnt=1 ; ;;
		no-hl)  no_hl=1  ; ;;
		no-dd)  no_dd=1  ; ;;
		no-cm)  no_cm=1  ; ;;
		fast)   zopf=    ; ;;
		ultra)  ultra=1  ; ;;
		lang)   shift;langs="$1"; ;;
		*)      help     ; ;;
	esac
	shift
done

tmv() {
	touch -r "$1" t
	mv t "$1"
}

stamp=$(
	for d in copyparty scripts; do
		find $d -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n'
	done | sort | tail -n 1 | sha1sum | cut -c-16
)

rm -rf $CSN/*
mkdir -p $CSN build
cd $CSN

tmpdir="$(
	printf '%s\n' "$TMPDIR" /tmp |
	awk '/./ {print; exit}'
)"

[ $repack ] && {
	old="$tmpdir/pe-copyparty.$(id -u)"
	echo "repack of files in $old"
	cp -pR "$old/"*{py2,j2,ftp,copyparty} .
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

	mkdir j2/
	mv {markupsafe,jinja2} j2/

	echo collecting pyftpdlib
	f="../build/pyftpdlib-1.5.6.tar.gz"
	[ -e "$f" ] ||
		(url=https://github.com/giampaolo/pyftpdlib/archive/refs/tags/release-1.5.6.tar.gz;
		wget -O$f "$url" || curl -L "$url" >$f)

	tar -zxf $f
	mv pyftpdlib-release-*/pyftpdlib .
	rm -rf pyftpdlib-release-* pyftpdlib/test

	mkdir ftp/
	mv pyftpdlib ftp/

	echo collecting asyncore, asynchat
	for n in asyncore.py asynchat.py; do
		f=../build/$n
		[ -e "$f" ] ||
			(url=https://raw.githubusercontent.com/python/cpython/c4d45ee670c09d4f6da709df072ec80cb7dfad22/Lib/$n;
			wget -O$f "$url" || curl -L "$url" >$f)
	done

	echo collecting python-magic
	v=0.4.27
	f="../build/python-magic-$v.tar.gz"
	[ -e "$f" ] ||
		(url=https://files.pythonhosted.org/packages/da/db/0b3e28ac047452d079d375ec6798bf76a036a08182dbb39ed38116a49130/python-magic-0.4.27.tar.gz;
		wget -O$f "$url" || curl -L "$url" >$f)

	tar -zxf $f
	mkdir magic
	mv python-magic-*/magic .
	rm -rf python-magic-*
	rm magic/compat.py
	f=magic/__init__.py
	awk '/^def _add_compat/{o=1} !o; /^_add_compat/{o=0}' <$f >t
	tmv "$f"
	mv magic ftp/  # doesn't provide a version label anyways

	# enable this to dynamically remove type hints at startup,
	# in case a future python version can use them for performance
	true || (
		echo collecting strip-hints
		f=../build/strip-hints-0.1.10.tar.gz
		[ -e $f ] ||
			(url=https://files.pythonhosted.org/packages/9c/d4/312ddce71ee10f7e0ab762afc027e07a918f1c0e1be5b0069db5b0e7542d/strip-hints-0.1.10.tar.gz;
			wget -O$f "$url" || curl -L "$url" >$f)

		tar -zxf $f
		mv strip-hints-0.1.10/src/strip_hints .
		rm -rf strip-hints-* strip_hints/import_hooks*
		sed -ri 's/[a-z].* as import_hooks$/"""a"""/' strip_hints/*.py

		cp -pR ../scripts/strip_hints/ .
	)
	cp -pR ../scripts/py2/ .

	# msys2 tar is bad, make the best of it
	echo collecting source
	[ $clean ] && {
		(cd .. && git archive hovudstraum >tar) && tar -xf ../tar copyparty
		(cd .. && tar -cf tar copyparty/web/deps) && tar -xf ../tar
	}
	[ $clean ] || {
		(cd .. && tar -cf tar copyparty) && tar -xf ../tar
	}
	rm -f ../tar

	# insert asynchat
	mkdir copyparty/vend
	for n in asyncore.py asynchat.py; do
		awk 'NR<4||NR>27;NR==4{print"# license: https://opensource.org/licenses/ISC\n"}' ../build/$n >copyparty/vend/$n
	done

	# remove type hints before build instead
	(cd copyparty; "$pybin" ../../scripts/strip_hints/a.py; rm uh)

	licfile=$(realpath copyparty/res/COPYING.txt)
	(cd ../scripts; ./genlic.sh "$licfile")
}

ver=
[ -z "$repack" ] &&
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
		gsub(/[^0-9,a-g-]/,""); gsub(/,/,"."); print; exit}' < copyparty/__version__.py)"

ts=$(date -u +%s)
hts=$(date -u +%Y-%m%d-%H%M%S) # --date=@$ts (thx osx)

mkdir -p ../dist
sfx_out=../dist/copyparty-$CSN

echo cleanup
find -name '*.pyc' -delete
find -name __pycache__ -delete
find -name py.typed -delete

# especially prevent osx from leaking your lan ip (wtf apple)
find -type f \( -name .DS_Store -or -name ._.DS_Store \) -delete
find -type f -name ._\* | while IFS= read -r f; do cmp <(printf '\x00\x05\x16') <(head -c 3 -- "$f") && rm -f -- "$f"; done

echo use smol web deps
rm -f copyparty/web/deps/*.full.* copyparty/web/dbg-* copyparty/web/Makefile

# it's fine dw
grep -lE '\.full\.(js|css)' copyparty/web/* |
while IFS= read -r x; do
	sed -r 's/\.full\.(js|css)/.\1/g' <"$x" >t
	tmv "$x"
done

find copyparty | LC_ALL=C sort | sed 's/\.gz$//;s/$/,/' > have
cat have | while IFS= read -r x; do
	grep -qF -- "$x" ../scripts/sfx.ls || {
		echo "unexpected file: $x"
		exit 1
	}
done
rm have

[ $no_cm ] && {
	rm -rf copyparty/web/mde.* copyparty/web/deps/easymde*
	echo h > copyparty/web/mde.html
	f=copyparty/web/md.html
	sed -r '/edit2">edit \(fancy/d' <$f >t
	tmv "$f"
}

[ $no_hl ] &&
	rm -rf copyparty/web/deps/prism*

[ $no_fnt ] && {
	rm -f copyparty/web/deps/scp.woff2
	f=copyparty/web/ui.css
	gzip -d "$f.gz" || true
	sed -r "s/src:.*scp.*\)/src:local('Consolas')/" <$f >t
	tmv "$f"
}

[ $no_dd ] && {
	rm -rf copyparty/web/dd
	f=copyparty/web/browser.css
	gzip -d "$f.gz" || true
	sed -r 's/(cursor: ?)url\([^)]+\), ?(pointer)/\1\2/; s/[0-9]+% \{cursor:[^}]+\}//; s/animation: ?cursor[^};]+//' <$f >t
	tmv "$f"
}

[ $langs ] &&
	for f in copyparty/web/{browser.js,splash.js}; do
		gzip -d "$f.gz" || true
		awk '/^\}/{l=0} !l; /^var Ls =/{l=1;next} o; /^\t["}]/{o=0} /^\t"'"$langs"'"/{o=1;print}' <$f >t
		tmv "$f"
	done

[ ! $repack ] && [ ! $use_ox ] && {
	# uncomment; oxidized drops 45 KiB but becomes undebuggable
	find | grep -E '\.py$' |
		grep -vE '__version__' |
		tr '\n' '\0' |
		xargs -0 "$pybin" ../scripts/uncomment.py

	# py2-compat
	#find | grep -E '\.py$' | while IFS= read -r x; do
	#	sed -ri '/: TypeAlias = /d' "$x"; done
}

f=j2/jinja2/constants.py
awk '/^LOREM_IPSUM_WORDS/{o=1;print "LOREM_IPSUM_WORDS = u\"a\"";next} !o; /"""/{o=0}' <$f >t
tmv "$f"
rm -f j2/jinja2/async*

grep -rLE '^#[^a-z]*coding: utf-8' j2 |
while IFS= read -r f; do
	(echo "# coding: utf-8"; cat "$f") >t
	tmv "$f"
done

# up2k goes from 28k to 22k laff
awk 'BEGIN{gensub(//,"",1)}' </dev/null &&
echo entabbening &&
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
	' <$f | sed -r 's/;\}$/}/; /\{\}$/d' >t
	tmv "$f"
done
unexpand -h 2>/dev/null &&
find | grep -E '\.(js|html)$' | while IFS= read -r f; do
	unexpand -t 4 --first-only <"$f" >t
	tmv "$f"
done

gzres() {
	[ $zopf ] && command -v zopfli && pk="zopfli --i$zopf"
	[ $zopf ] && command -v pigz && pk="pigz -11 -I $zopf"
	[ -z "$pk" ] && pk='gzip'

	np=$(nproc)
	echo "$pk #$np"

	while IFS=' ' read -r _ f; do
		while true; do
			na=$(ps auxwww | grep -F "$pk" | wc -l)
			[ $na -le $np ] && break
			sleep 0.2
		done
		echo -n .
		$pk "$f" &
	done < <(
		find -printf '%s %p\n' |
		grep -E '\.(js|css)$' |
		grep -vF /deps/ |
		sort -nr
	)
	wait
	echo
}


zdir="$tmpdir/cpp-mk$CSN"
[ -e "$zdir/$stamp" ] || rm -rf "$zdir"
mkdir -p "$zdir"
echo a > "$zdir/$stamp"
nf=$(ls -1 "$zdir"/arc.* | wc -l)
[ $nf -ge 2 ] && [ ! $repack ] && use_zdir=1 || use_zdir=

[ $use_zdir ] || {
	echo "$nf alts += 1"
	gzres
	[ $repack ] ||
		tar -cf "$zdir/arc.$(date +%s)" copyparty/web/*.gz
}
[ $use_zdir ] && {
	arcs=("$zdir"/arc.*)
	n=$(( $RANDOM % ${#arcs[@]} ))
	arc="${arcs[n]}"
	echo "using $arc"
	tar -xf "$arc"
	for f in copyparty/web/*.gz; do
		rm "${f%.*}"
	done
}


[ $use_ox ] && {
	tgt=x86_64-pc-windows-msvc
	tgt=i686-pc-windows-msvc  # 2M smaller (770k after upx)
	bdir=build/$tgt/release/install/copyparty

	t="res web"
	(printf "\n\n\nBUT WAIT! THERE'S MORE!!\n\n";
	cat ../$bdir/COPYING.txt) >> copyparty/res/COPYING.txt ||
		echo "copying.txt 404 pls rebuild"

	mv ftp/* j2/* copyparty/vend/* .
	rm -rf ftp j2 py2 copyparty/vend
	(cd copyparty; tar -cvf z.tar $t; rm -rf $t)
	cd ..
	pyoxidizer build --release --target-triple $tgt
	mv $bdir/copyparty.exe dist/
	cp -pv "$(for d in '/c/Program Files (x86)/Microsoft Visual Studio/'*'/BuildTools/VC/Redist/MSVC'; do
		find "$d" -name vcruntime140.dll; done | sort | grep -vE '/x64/|/onecore/' | head -n 1)" dist/
	dist/copyparty.exe --version
	cp -pv dist/copyparty{,.orig}.exe
	[ $ultra ] && a="--best --lzma" || a=-1
	/bin/time -f %es upx $a dist/copyparty.exe >/dev/null
	ls -al dist/copyparty{,.orig}.exe
	exit 0
}


echo gen tarlist
for d in copyparty j2 ftp py2; do find $d -type f; done |  # strip_hints
sed -r 's/(.*)\.(.*)/\2 \1/' | LC_ALL=C sort |
sed -r 's/([^ ]*) (.*)/\2.\1/' | grep -vE '/list1?$' > list1

for n in {1..50}; do
	(grep -vE '\.(gz|br)$' list1; grep -E '\.(gz|br)$' list1 | (shuf||gshuf) ) >list || true
	s=$( (sha1sum||shasum) < list | cut -c-16)
	grep -q $s "$zdir/h" && continue
	echo $s >> "$zdir/h"
	break
done
[ $n -eq 50 ] && exit

echo creating tar
tar -cf tar "${targs[@]}" --numeric-owner -T list

pc="bzip2 -"; pe=bz2
[ $use_gz ] && pc="gzip -" && pe=gz
[ $use_gzz ] && pc="pigz -11 -I$use_gzz" && pe=gz

echo compressing tar
for n in {2..9}; do cp tar t.$n; nice $pc$n t.$n & done; wait
minf=$(for f in t.*.$pe; do
	s1=$(wc -c <$f)
	s2=$(tr -d '\r\n\0' <$f | wc -c)
	echo "$(( s2+(s1-s2)*3 )) $f"
done | sort -n | awk '{print$2;exit}')
mv -v $minf tar.bz2
rm t.* || true
exts=()


echo creating sfx

py=../scripts/sfx.py
suf=
[ $use_gz ] && {
	sed -r 's/"r:bz2"/"r:gz"/' <$py >$py.t
	py=$py.t
	suf=-gz
}

"$pybin" $py --sfx-make tar.bz2 $ver $ts
mv sfx.out $sfx_out$suf.py

exts+=($suf.py)
[ $use_gz ] &&
	rm $py


chmod 755 $sfx_out*

printf "done:\n"
for ext in ${exts[@]}; do
	printf "  %s\n" "$(realpath $sfx_out)"$ext
done

# apk add bash python3 tar xz bzip2
# while true; do ./make-sfx.sh; f=../dist/copyparty-sfx.py; mv $f $f.$(wc -c <$f | awk '{print$1}'); done
