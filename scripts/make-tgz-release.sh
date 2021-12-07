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

ver="$1"

[ "x$ver" = x ] &&
{
	echo "need argument 1:  version"
	echo
	exit 1
}

[ -e copyparty/__main__.py ] || cd ..
[ -e copyparty/__main__.py ] ||
{
	echo "run me from within the project root folder"
	echo
	exit 1
}

mkdir -p dist
zip_path="$(pwd)/dist/copyparty-$ver.zip"
tgz_path="$(pwd)/dist/copyparty-$ver.tar.gz"

[ -e "$zip_path" ] ||
[ -e "$tgz_path" ] &&
{
	echo "found existing archives for this version"
	echo "  $zip_path"
	echo "  $tgz_path"
	echo
	echo "continue?"
	read -u1
}
rm "$zip_path" 2>/dev/null || true
rm "$tgz_path" 2>/dev/null || true

#sed -ri "s/^(ADMIN_PWD *= *u).*/\1'hunter2'/" copyparty/config.py

tmp="$(mktemp -d)"
rls_dir="$tmp/copyparty-$ver"
mkdir "$rls_dir"

echo ">>> export from git"
git archive hovudstraum | tar -xC "$rls_dir"

echo ">>> export untracked deps"
tar -c copyparty/web/deps | tar -xC "$rls_dir"

cd "$rls_dir"
find -type d -exec chmod 755 '{}' \+
find -type f -exec chmod 644 '{}' \+

commaver="$(
	printf '%s\n' "$ver" |
	sed -r 's/\./, /g'
)"

grep -qE "^VERSION *= \(${commaver}\)$" copyparty/__version__.py ||
{
	echo "$tmp"
	echo "bad version"
	echo
	echo " arg: $commaver"
	echo "code: $(
		cat copyparty/__version__.py |
		grep -E '^VERSION'
	)"
	echo
	echo "continue?"
	read -u1
}

rm -rf .vscode
rm \
  .gitattributes \
  .gitignore

mv LICENSE LICENSE.txt

# the regular cleanup memes
find -name '*.pyc' -delete
find -name __pycache__ -delete
find -type f \( -name .DS_Store -or -name ._.DS_Store \) -delete
find -type f -name ._\* | while IFS= read -r f; do cmp <(printf '\x00\x05\x16') <(head -c 3 -- "$f") && rm -f -- "$f"; done

# also messy because osx support
find -type f -exec $md5sum '{}' \+ |
sed -r 's/(.{32})(.*)/\2\1/' | LC_COLLATE=c sort |
sed -r 's/(.*)(.{32})/\2\1/' |
sed -r 's/^(.{32}) \./\1  ./' > ../.sums.md5
mv ../.sums.md5 .

cd ..
pwd
echo ">>> tar"; tar -czf "$tgz_path" --owner=1000 --group=1000 --numeric-owner "copyparty-$ver"
echo ">>> zip"; zip  -qr "$zip_path" "copyparty-$ver"

rm -rf "$tmp"
echo
echo "done:"
echo "  $zip_path"
echo "  $tgz_path"
echo

# function alr() { ls -alR copyparty-$1 | sed -r "s/copyparty-$1/copyparty/" | sed -r 's/[A-Z][a-z]{2} [0-9 ]{2} [0-9]{2}:[0-9]{2}//' > $1; }; for x in hovudstraum rls src ; do alr $x; done

