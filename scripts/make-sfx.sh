#!/bin/bash
set -e
echo

berr() { p=$(head -c 72 </dev/zero | tr '\0' =); printf '\n%s\n\n' $p; cat; printf '\n%s\n\n' $p; }

help() { exec cat <<'EOF'

# optional args:
#
# `fast` builds faster, with cheaper js/css compression
#
# `clean` uses files from git (everything except web/deps),
#   so local changes won't affect the produced sfx
#
# `re` does a repack of an sfx which you already executed once
#   (grabs files from the sfx-created tempdir), overrides `clean`
#
# `gz` creates a gzip-compressed python sfx instead of bzip2
#
# `lang` limits which languages/translations to include,
#   for example `lang eng` or `lang eng|nor`
#
# _____________________________________________________________________
# core features:
#
# `no-ftp` saves ~30k by removing the ftp server, disabling --ftp
#
# `no-tfp` saves ~10k by removing the tftp server, disabling --tftp
#
# `no-smb` saves ~3.5k by removing the smb / cifs server
#
# `no-zm` saves ~k by removing the zeroconf mDNS server
#
# _____________________________________________________________________
# web features:
#
# `no-cm` saves ~89k by removing easymde/codemirror
#   (the fancy markdown editor)
#
# `no-hl` saves ~41k by removing syntax hilighting in the text viewer
#
# `no-fnt` saves ~9k by removing the source-code-pro font
#   (browsers will try to use 'Consolas' instead)
#
# `no-dd` saves ~2k by removing the mouse cursor
#
# _____________________________________________________________________
# build behavior:
#
# `dl-wd` automatically downloads webdeps if necessary
#
# `ign-wd` allows building an sfx without webdeps
#
# ---------------------------------------------------------------------
#
# if you are on windows, you can use msys2:
#   PATH=/c/Users/$USER/AppData/Local/Programs/Python/Python310:"$PATH" ./make-sfx.sh fast

EOF
}

# port install gnutar findutils gsed gawk coreutils
gtar=$(command -v gtar || command -v gnutar) || true
[ ! -z "$gtar" ] && command -v gfind >/dev/null && {
	tar()  { $gtar "$@"; }
	tr()   { gtr   "$@"; }
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

langs=
use_gz=
zopf=2560
while [ ! -z "$1" ]; do
	case $1 in
		clean)  clean=1  ; ;;
		re)     repack=1 ; ;;
		gz)     use_gz=1 ; ;;
		gzz)    shift;use_gzz=$1;use_gz=1; ;;
		no-ftp) no_ftp=1 ; ;;
		no-tfp) no_tfp=1 ; ;;
		no-smb) no_smb=1 ; ;;
		no-zm)  no_zm=1  ; ;;
		no-fnt) no_fnt=1 ; ;;
		no-hl)  no_hl=1  ; ;;
		no-dd)  no_dd=1  ; ;;
		no-cm)  no_cm=1  ; ;;
		dl-wd)  dl_wd=1  ; ;;
		ign-wd) ign_wd=1 ; ;;
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
iawk() {
	awk "$1" <"$2" >t
	tmv "$2"
}
ised() {
	sed -r "$1" <"$2" >t
	tmv "$2"
}

stamp=$(
	for d in copyparty scripts; do
		find $d -type f -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n'
	done | sort | tail -n 1 | sha1sum | cut -c-16
)

rm -rf sfx$CSN/*
mkdir -p sfx$CSN build
cd sfx$CSN

tmpdir="$(
	printf '%s\n' "$TMPDIR" /tmp |
	awk '/./ {print; exit}'
)"

necho() {
	printf '\033[G%s ... \033[K' "$*"
}

[ $repack ] && {
	old="$tmpdir/pe-copyparty.$(id -u)"
	echo "repack of files in $old"
	cp -pR "$old/"*{py2,py37,magic,j2,copyparty} .
	cp -pR "$old/"*partftpy . || true
	cp -pR "$old/"*ftp . || true
}

[ $repack ] || {
	necho collecting ipaddress
	f="../build/ipaddress-1.0.23.tar.gz"
	[ -e "$f" ] ||
		(url=https://files.pythonhosted.org/packages/b9/9a/3e9da40ea28b8210dd6504d3fe9fe7e013b62bf45902b458d1cdc3c34ed9/ipaddress-1.0.23.tar.gz;
		wget -O$f "$url" || curl -L "$url" >$f)

	tar -zxf $f
	mkdir py37
	mv ipaddress-*/ipaddress.py py37/
	rm -rf ipaddress-*

	necho collecting jinja2
	f="../build/Jinja2-2.11.3.tar.gz"
	[ -e "$f" ] ||
		(url=https://files.pythonhosted.org/packages/4f/e7/65300e6b32e69768ded990494809106f87da1d436418d5f1367ed3966fd7/Jinja2-2.11.3.tar.gz;
		wget -O$f "$url" || curl -L "$url" >$f)

	tar -zxf $f
	mv Jinja2-*/src/jinja2 .
	rm -rf Jinja2-*
	
	necho collecting markupsafe
	f="../build/MarkupSafe-1.1.1.tar.gz"
	[ -e "$f" ] ||
		(url=https://files.pythonhosted.org/packages/b9/2e/64db92e53b86efccfaea71321f597fa2e1b2bd3853d8ce658568f7a13094/MarkupSafe-1.1.1.tar.gz;
		wget -O$f "$url" || curl -L "$url" >$f)

	tar -zxf $f
	mv MarkupSafe-*/src/markupsafe .
	rm -rf MarkupSafe-* markupsafe/_speedups.c

	mkdir j2/
	mv {markupsafe,jinja2} j2/

	necho collecting pyftpdlib
	f="../build/pyftpdlib-1.5.9.tar.gz"
	[ -e "$f" ] ||
		(url=https://github.com/giampaolo/pyftpdlib/archive/refs/tags/release-1.5.9.tar.gz;
		wget -O$f "$url" || curl -L "$url" >$f)

	tar -zxf $f
	mv pyftpdlib-release-*/pyftpdlib .
	rm -rf pyftpdlib-release-* pyftpdlib/test
	for f in pyftpdlib/_async{hat,ore}.py; do
		[ -e "$f" ] || continue;
		iawk 'NR<4||NR>27||!/^#/;NR==4{print"# license: https://opensource.org/licenses/ISC\n"}' $f
	done

	mkdir ftp/
	mv pyftpdlib ftp/

	necho collecting partftpy
	f="../build/partftpy-0.3.1.tar.gz"
	[ -e "$f" ] ||
		(url=https://files.pythonhosted.org/packages/37/79/1a1de1d3fdf27ddc9c2d55fec6552e7b8ed115258fedac6120679898b83d/partftpy-0.3.1.tar.gz;
		wget -O$f "$url" || curl -L "$url" >$f)

	tar -zxf $f
	mv partftpy-*/partftpy .
	rm -rf partftpy-* partftpy/bin

	necho collecting python-magic
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
	iawk '/^def _add_compat/{o=1} !o; /^_add_compat/{o=0}' magic/__init__.py

	# enable this to dynamically remove type hints at startup,
	# in case a future python version can use them for performance
	true && (
		necho collecting strip-hints
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
	cp -pR ../scripts/py2 .

	# msys2 tar is bad, make the best of it
	necho collecting source
	echo
	[ $clean ] && {
		(cd .. && git archive hovudstraum >tar) && tar -xf ../tar copyparty
		(cd .. && tar -cf tar copyparty/web/deps) && tar -xf ../tar
	}
	[ $clean ] || {
		(cd .. && tar -cf tar copyparty) && tar -xf ../tar
	}
	rm -f ../tar

	# resolve symlinks
	find -type l |
	while IFS= read -r f1; do (
		cd "${f1%/*}"
		f1="./${f1##*/}"
		f2="$(readlink "$f1")"
		[ -e "$f2" ] || f2="../$f2"
		[ -e "$f2" ] || {
			echo could not resolve "$f1"
			exit 1
		}
		rm "$f1"
		cp -p "$f2" "$f1"
	); done

	# resolve symlinks on windows
	[ "$OSTYPE" = msys ] &&
	(cd ..; git ls-files -s | awk '/^120000/{print$4}') |
	while IFS= read -r x; do
		[ $(wc -l <"$x") -gt 1 ] && continue
		(cd "${x%/*}"; cp -p "../$(cat "${x##*/}")" ${x##*/})
	done

	rm -f copyparty/stolen/*/README.md

	# remove type hints before build instead
	(cd copyparty; PYTHONPATH="..:$PYTHONPATH" "$pybin" ../../scripts/strip_hints/a.py; rm uh)

	licfile=$(realpath copyparty/res/COPYING.txt)
	(cd ../scripts; ./genlic.sh "$licfile")
}

[ ! -e copyparty/web/deps/mini-fa.woff ] && [ $dl_wd ] && {
	echo "could not find webdeps; downloading..."
	url=https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py
	wget -Ox.py "$url" || curl -L "$url" >x.py

	echo "extracting webdeps..."
	wdsrc="$("$pybin" x.py --version 2>&1 | tee /dev/stderr | awk '/sfxdir:/{sub(/.*: /,"");print;exit}')"
	[ "$wdsrc" ] || {
		echo failed to discover tempdir of reference copyparty-sfx.py
		exit 1
	}
	rm -rf copyparty/web/deps
	cp -pvR "$wdsrc/copyparty/web/deps" copyparty/web/

	# also copy it out into the source-tree for next time
	rm -rf ../copyparty/web/deps
	cp -pR copyparty/web/deps ../copyparty/web

	rm x.py
}

[ -e copyparty/web/deps/mini-fa.woff ] || [ $ign_wd ] || { berr <<'EOF'
ERROR:
  could not find webdeps; the front-end will not be fully functional

please choose one of the following:

A) add the argument "dl-wd" to fix it automatically; this will
    download copyparty-sfx.py and extract the webdeps from there

B) build the webdeps from source:  make -C scripts/deps-docker

C) add the argument "ign-wd" to continue building the sfx without webdeps

alternative A is a good choice if you are only intending to
modify the copyparty source code (py/html/css/js) and do not
plan to make any changes to the mostly-third-party webdeps

there may be additional hints in the devnotes:
https://github.com/9001/copyparty/blob/hovudstraum/docs/devnotes.md#building
EOF
	exit 1
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
		t_ver="$(printf '%s\n' "$ver" | sed -r 's/[-.]/, /g; s/(.*) (.*)/\1 "\2"/')"
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

echo "$ver" >ver  # pyz

ts=$(date -u +%s)
hts=$(date -u +%Y-%m%d-%H%M%S) # --date=@$ts (thx osx)

mkdir -p ../dist
sfx_out=../dist/copyparty-sfx$CSN

echo cleanup
find -name '*.pyc' -delete
find -name __pycache__ -delete
find -name py.typed -delete

# especially prevent macos/osx from leaking your lan ip (wtf apple)
find -type f \( -name .DS_Store -or -name ._.DS_Store \) -delete
find -type f -name ._\* | while IFS= read -r f; do cmp <(printf '\x00\x05\x16') <(head -c 3 -- "$f") && rm -fv -- "$f"; done

rm -f copyparty/web/deps/*.full.* copyparty/web/dbg-* copyparty/web/Makefile

find copyparty | LC_ALL=C sort | sed -r 's/\.gz$//;s/$/,/' > have
cat have | while IFS= read -r x; do
	grep -qF -- "$x" ../scripts/sfx.ls || {
		echo "unexpected file: $x"
		exit 1
	}
done
rm have

ised /fork_process/d ftp/pyftpdlib/servers.py
iawk '/^class _Base/{s=1}!s' ftp/pyftpdlib/authorizers.py
iawk '/^ {0,4}[^ ]/{s=0}/^ {4}def (serve_forever|_loop)/{s=1}!s' ftp/pyftpdlib/servers.py
rm -f ftp/pyftpdlib/{__main__,prefork}.py

[ $no_ftp ] &&
	rm -rf copyparty/ftpd.py ftp

[ $no_tfp ] &&
	rm -rf copyparty/tftpd.py partftpy

[ $no_smb ] &&
	rm -f copyparty/smbd.py

[ $no_zm ] &&
	rm -rf copyparty/mdns.py copyparty/stolen/dnslib

[ $no_cm ] && {
	rm -rf copyparty/web/mde.* copyparty/web/deps/easymde*
	echo h > copyparty/web/mde.html
	ised '/edit2">edit \(fancy/d' copyparty/web/md.html
}

[ $no_hl ] &&
	rm -rf copyparty/web/deps/prism*

[ $no_fnt ] && {
	rm -f copyparty/web/deps/scp.woff2
	f=copyparty/web/ui.css
	gzip -d "$f.gz" || true
	ised "s/src:.*scp.*\)/src:local('Consolas')/" $f
}

[ $no_dd ] && {
	rm -rf copyparty/web/dd
	f=copyparty/web/browser.css
	gzip -d "$f.gz" || true
	ised 's/(cursor: ?)url\([^)]+\), ?(pointer)/\1\2/; s/[0-9]+% \{cursor:[^}]+\}//; s/animation: ?cursor[^};]+//' $f
}

[ $langs ] &&
	for f in copyparty/web/{browser.js,splash.js}; do
		gzip -d "$f.gz" || true
		iawk '/^\}/{l=0} !l; /^var Ls =/{l=1;next} o; /^\t["}]/{o=0} /^\t"'"$langs"'"/{o=1;print}' $f
	done

[ ! $repack ] && {
	# uncomment
	find | grep -E '\.py$' |
		grep -vE '__version__' |
		tr '\n' '\0' |
		xargs -0 "$pybin" ../scripts/uncomment.py

	# py2-compat
	#find | grep -E '\.py$' | while IFS= read -r x; do
	#	sed -ri '/: TypeAlias = /d' "$x"; done
}

rm -f j2/jinja2/constants.py
iawk '/^ {4}def /{s=0}/^ {4}def compile_templates\(/{s=1}!s' j2/jinja2/environment.py
ised '/generate_lorem_ipsum/d' j2/jinja2/defaults.py
iawk '/^def /{s=0}/^def generate_lorem_ipsum/{s=1}!s' j2/jinja2/utils.py
iawk '/^(class|def) /{s=0}/^(class InternationalizationExtension|def _make_new_n?gettext)/{s=1}!s' j2/jinja2/ext.py
iawk '/^[^ ]/{s=0}/^def babel_extract/{s=1}!s' j2/jinja2/ext.py
ised '/InternationalizationExtension/d' j2/jinja2/ext.py
iawk '/^class/{s=0}/^class (Package|Dict|Function|Prefix|Choice|Module)Loader/{s=1}!s' j2/jinja2/loaders.py
sed -ri '/^from .bccache | (Package|Dict|Function|Prefix|Choice|Module)Loader$/d' j2/jinja2/__init__.py
rm -f j2/jinja2/async* j2/jinja2/{bccache,sandbox}.py
cat > j2/jinja2/_identifier.py <<'EOF'
import re
pattern = re.compile(r"\w+")
EOF

grep -rLE '^#[^a-z]*coding: utf-8' j2 |
while IFS= read -r f; do
	(echo "# coding: utf-8"; cat "$f") >t
	tmv "$f"
done

# up2k goes from 28k to 22k laff
awk 'BEGIN{gensub(//,"",1)}' </dev/null 2>/dev/null &&
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
done ||
	echo "WARNING: your awk does not have gensub, so the sfx will not have optimal compression"

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


zdir="$tmpdir/cpp-mksfx$CSN"
[ -e "$zdir/$stamp" ] || rm -rf "$zdir"
mkdir -p "$zdir"
echo a > "$zdir/$stamp"
nf=$(ls -1 "$zdir"/arc.* 2>/dev/null | wc -l)
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


echo gen tarlist
for d in copyparty partftpy magic j2 py2 py37 ftp; do find $d -type f || true; done |  # strip_hints
sed -r 's/(.*)\.(.*)/\2 \1/' | LC_ALL=C sort |
sed -r 's/([^ ]*) (.*)/\2.\1/' | grep -vE '/list1?$' > list1

for n in {1..50}; do
	(grep -vE '\.gz$' list1; grep -E '\.gz$' list1 | (shuf||gshuf) ) >list || true
	s=$( (sha1sum||shasum) < list | cut -c-16)
	grep -q $s "$zdir/h" 2>/dev/null && continue
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
