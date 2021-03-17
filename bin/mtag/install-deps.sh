#!/bin/bash
set -e


# install optional dependencies
# works on linux, maybe on macos eventually
#
# enables the following features:
#   bpm detection
#   tempo detection
#  
# installs stuff to the following locations:
#   ~/pe/
#   whatever your python uses for --user packages
#
# does the following terrible things:
#   modifies the keyfinder python lib to load the .so in ~/pe


echo the stuff installed by thsi script is not actually used by copyparty yet so continuing is mostly pointless
echo press enter if you want to anyways
read


command -v gnutar && tar() { gnutar "$@"; }
command -v gtar && tar() { gtar "$@"; }
command -v gsed && sed() { gsed "$@"; }


need() {
	command -v $1 >/dev/null || {
		echo need $1
		exit 1
	}
}
need cmake
#need patchelf


td="$(mktemp -d)"
cln() {
	rm -rf "$td"
}
trap cln EXIT
cd "$td"
pwd


dl_text() {
	command -v curl >/dev/null && exec curl "$@"
	exec wget -O- "$@"
}
dl_files() {
	command -v curl >/dev/null && exec curl -JOL "$@"
	exec wget --trust-server-names "$@"
}
export -f dl_files


github_tarball() {
	dl_text "$1" |
	tee json |
	(
		# prefer jq if available
		jq -r '.tarball_url' ||

		# fallback to awk (sorry)
		awk -F\" '/"tarball_url".*\.tar\.gz/ {print$4}'
	) |
	tee /dev/stderr |
	tr -d '\r' | tr '\n' '\0' |
	xargs -0 bash -c 'dl_files "$@"' _
}


gitlab_tarball() {
	dl_text "$1" |
	tee json |
	(
		# prefer jq if available
		jq -r '.[0].assets.sources[]|select(.format|test("tar.gz")).url' ||

		# fallback to abomination
		tr \" '\n' | grep -E '\.tar\.gz$' | head -n 1
	) |
	tee /dev/stderr |
	tr -d '\r' | tr '\n' '\0' |
	tee links |
	xargs -0 bash -c 'dl_files "$@"' _
}


install_keyfinder() {
	github_tarball https://api.github.com/repos/mixxxdj/libkeyfinder/releases/latest

	tar -xvf mixxxdj-libkeyfinder-*
	rm -- *.tar.gz
	cd mixxxdj-libkeyfinder*
	cmake -DCMAKE_INSTALL_PREFIX=$HOME/pe/keyfinder -S . -B build
	cmake --build build --parallel $(nproc)
	cmake --install build

	command -v python3 && c=python3 || c=python
	
	CFLAGS=-I$HOME/pe/keyfinder/include \
	LDFLAGS=-L$HOME/pe/keyfinder/lib \
	$c -m pip install --user keyfinder

	pypath="$($c -c 'import keyfinder; print(keyfinder.__file__)')"
	libpath="$(echo "$HOME/pe/keyfinder/lib/libkeyfinder.so")"

	mv "$pypath"{,.bak}
	(
		printf 'import ctypes\nctypes.cdll.LoadLibrary("%s")\n' "$libpath"
		cat "$pypath.bak"
	) >"$pypath"

	echo
	echo libkeyfinder successfully installed to the following locations:
	echo "  $libpath"
	echo "  $pypath"
}


# not in use because it kinda segfaults
install_soundtouch() {
	gitlab_tarball https://gitlab.com/api/v4/projects/soundtouch%2Fsoundtouch/releases
	
	tar -xvf soundtouch-*
	rm -- *.tar.gz
	cd soundtouch-*
	
	# https://github.com/jrising/pysoundtouch
	./bootstrap
	./configure --enable-integer-samples CXXFLAGS="-fPIC" --prefix="$HOME/pe/soundtouch"
	make -j$(nproc)
	make install
	
	command -v python3 && c=python3 || c=python
	
	CFLAGS=-I$HOME/pe/soundtouch/include/ \
	LDFLAGS=-L$HOME/pe/soundtouch/lib \
	$c -m pip install --user git+https://github.com/snowxmas/pysoundtouch.git
	
	pypath="$($c -c 'import importlib; print(importlib.util.find_spec("soundtouch").origin)')"
	libpath="$(echo "$HOME/pe/soundtouch/lib/")"
	patchelf --set-rpath "$libpath" "$pypath"

	echo
	echo soundtouch successfully installed to the following locations:
	echo "  $libpath"
	echo "  $pypath"
}


[ "$1" = keyfinder ] && { install_keyfinder; exit $?; }
[ "$1" = soundtouch ] && { install_soundtouch; exit $?; }

echo need arg 1: keyfinder or soundtouch
