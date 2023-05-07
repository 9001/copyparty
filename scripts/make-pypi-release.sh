#!/bin/bash
set -e
echo

# osx support
# port install gnutar findutils gsed coreutils
gtar=$(command -v gtar || command -v gnutar) || true
[ ! -z "$gtar" ] && command -v gfind >/dev/null && {
	tar()  { $gtar "$@"; }
	sed()  { gsed  "$@"; }
	find() { gfind "$@"; }
	sort() { gsort "$@"; }
	command -v grealpath >/dev/null &&
		realpath() { grealpath "$@"; }
}

mode="$1"
fast="$2"

[ -z "$mode" ] &&
{
	echo "need argument 1:  (D)ry, (T)est, (U)pload"
	echo " optional arg 2:  fast"
	echo
	exit 1
}

[ -e copyparty/__main__.py ] || cd ..
[ -e copyparty/__main__.py ] ||
{
	echo "run me from within the copyparty folder"
	echo
	exit 1
}


# one-time stuff, do this manually through copy/paste
true ||
{
	cat > ~/.pypirc <<EOF
[distutils]
index-servers =
  pypi
  pypitest

[pypi]
repository: https://upload.pypi.org/legacy/
username: qwer
password: asdf

[pypitest]
repository: https://test.pypi.org/legacy/
username: qwer
password: asdf
EOF

	# set pypi password
	chmod 600 ~/.pypirc
	sed -ri 's/qwer/username/;s/asdf/password/' ~/.pypirc
}



pydir="$(
	which python |
	sed -r 's@[^/]*$@@'
)"

[ -e "$pydir/activate" ] &&
{
	echo '`deactivate` your virtualenv'
	exit 1
}

function have() {
	python -c "import $1; $1; getattr($1,'__version__',0)"
}

function load_env() {
	. buildenv/bin/activate
	have setuptools
	have wheel
	have build
	have twine
	have jinja2
	have strip_hints
}

load_env || {
	echo creating buildenv
	deactivate || true
	rm -rf buildenv
	python3 -m venv buildenv
	(. buildenv/bin/activate && pip install \
		setuptools wheel build twine jinja2 strip_hints )
	load_env
}

# cleanup
rm -rf unt build/pypi

# grab licenses
scripts/genlic.sh copyparty/res/COPYING.txt

# clean-ish packaging env
rm -rf build/pypi
mkdir -p build/pypi
cp -pR pyproject.toml README.md LICENSE copyparty contrib bin scripts/strip_hints build/pypi/
tar -c docs/lics.txt scripts/genlic.sh build/*.txt | tar -xC build/pypi/
cd build/pypi

# delete junk
find -name '*.pyc' -delete
find -name __pycache__ -delete
find -name py.typed -delete
find -type f \( -name .DS_Store -or -name ._.DS_Store \) -delete
find -type f -name ._\* | while IFS= read -r f; do cmp <(printf '\x00\x05\x16') <(head -c 3 -- "$f") && rm -f -- "$f"; done

# remove type hints to support python < 3.9
f=../strip-hints-0.1.10.tar.gz
[ -e $f ] || 
	(url=https://files.pythonhosted.org/packages/9c/d4/312ddce71ee10f7e0ab762afc027e07a918f1c0e1be5b0069db5b0e7542d/strip-hints-0.1.10.tar.gz;
	wget -O$f "$url" || curl -L "$url" >$f)
tar --strip-components=2 -xf $f strip-hints-0.1.10/src/strip_hints
python3 -c 'from strip_hints.a import uh; uh("copyparty")'

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
(cd ../..; git ls-files -s | awk '/^120000/{print$4}') |
while IFS= read -r x; do
	[ $(wc -l <"$x") -gt 1 ] && continue
	(cd "${x%/*}"; cp -p "../$(cat "${x##*/}")" ${x##*/})
done

rm -rf contrib
[ $fast ] && sed -ri s/5730/10/ copyparty/web/Makefile
(cd copyparty/web && make -j$(nproc) && rm Makefile)

# build
python3 -m build

[ "$mode" == t ] && twine upload -r pypitest dist/*
[ "$mode" == u ] && twine upload -r pypi dist/*
