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

which md5sum 2>/dev/null >/dev/null &&
	md5sum=md5sum ||
	md5sum="md5 -r"

mode="$1"

[ -z "$mode" ] &&
{
	echo "need argument 1:  (D)ry, (T)est, (U)pload"
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

	# if PY2: create build env
	cd ~/dev/copyparty && virtualenv buildenv
	(. buildenv/bin/activate && pip install twine)

	# if PY3: create build env
	cd ~/dev/copyparty && python3 -m venv buildenv
	(. buildenv/bin/activate && pip install twine wheel)
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
	python -c "import $1; $1; $1.__version__"
}

. buildenv/bin/activate
have setuptools
have wheel
have twine

# remove type hints to support python < 3.9
rm -rf build/pypi
mkdir -p build/pypi
cp -pR setup.py README.md LICENSE copyparty tests bin scripts/strip_hints build/pypi/
cd build/pypi
tar --strip-components=2 -xf ../strip-hints-0.1.10.tar.gz strip-hints-0.1.10/src/strip_hints
python3 -c 'from strip_hints.a import uh; uh("copyparty")'

./setup.py clean2
./setup.py sdist bdist_wheel --universal

[ "$mode" == t ] && twine upload -r pypitest dist/*
[ "$mode" == u ] && twine upload -r pypi dist/*

cat <<EOF


    all done!
    
    to clean up the source tree:
    
       cd ~/dev/copyparty
       ./setup.py clean2
   
EOF
