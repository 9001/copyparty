#!/bin/bash
set -e
echo

# osx support
sed=$( which gsed  2>/dev/null || which sed)
find=$(which gfind 2>/dev/null || which find)
sort=$(which gsort 2>/dev/null || which sort)

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
