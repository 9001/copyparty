#!/bin/bash
set -e
e=0

cd ~/dev/pyi

ckpypi() {
	deps=(
		altgraph
		pefile
		pyinstaller
		pyinstaller-hooks-contrib
		pywin32-ctypes
		Jinja2
		MarkupSafe
		mutagen
		Pillow
	)
	for dep in "${deps[@]}"; do
		k=
		echo -n .
		curl -s https://pypi.org/pypi/$dep/json >h
		ver=$(jq <h -r '.releases|keys|.[]' | sort -V | tail -n 1)
		while IFS= read -r fn; do
			[ -e "$fn" ] && k="$fn" && break
		done < <(
			jq -r '.releases["'"$ver"'"]|.[]|.filename' <h
		)
		[ -z "$k" ] && echo "outdated: $dep" && cp h "ng-$dep" && e=1
	done
	true
}

ckgh() {
	deps=(
		upx/upx
	)
	for dep in "${deps[@]}"; do
		k=
		echo -n .
		while IFS= read -r fn; do
			[ -e "$fn" ] && k="$fn" && break
		done < <(
			curl -s https://api.github.com/repos/$dep/releases | tee h |
			jq -r 'first|.assets|.[]|.name'
		)
		[ -z "$k" ] && echo "outdated: $dep" && cp h "ng-$dep" e=1
	done
	true
}

ckpypi
ckgh

rm h
exit $e
