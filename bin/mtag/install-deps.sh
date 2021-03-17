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
#
# has the following manual dependencies, especially on mac:
#   https://www.vamp-plugins.org/pack.html


win=
[ ! -z "$MSYSTEM" ] || [ -e /msys2.exe ] && {
	[ "$MSYSTEM" = MINGW64 ] || {
		echo windows detected, msys2-mingw64 required
		exit 1
	}
	pacman -S --needed mingw-w64-x86_64-{ffmpeg,python,python-pip,vamp-plugin-sdk}
	win=1
}

mac=
[ $(uname -s) = Darwin ] && {
	#pybin="$(printf '%s\n' /opt/local/bin/python* | (sed -E 's/(.*\/[^/0-9]+)([0-9]?[^/]*)$/\2 \1/' || cat) | (sort -nr || cat) | (sed -E 's/([^ ]*) (.*)/\2\1/' || cat) | grep -E '/(python|pypy)[0-9\.-]*$' | head -n 1)"
	pybin=/opt/local/bin/python3.9
	[ -e "$pybin" ] || {
		echo mac detected, python3 from macports required
		exit 1
	}
	pkgs='ffmpeg python39 py39-wheel'
	ninst=$(port installed | awk '/^  /{print$1}' | sort | uniq | grep -E '^('"$(echo "$pkgs" | tr ' ' '|')"')$' | wc -l)
	[ $ninst -eq 3 ] || {
		sudo port install $pkgs
	}
	mac=1
}

hash -r

[ $mac ] || {
	command -v python3 && pybin=python3 || pybin=python
}

$pybin -m pip install --user numpy


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
	# windows support:
	#   use msys2 in mingw-w64 mode
	#   pacman -S --needed mingw-w64-x86_64-{ffmpeg,python}
	
	github_tarball https://api.github.com/repos/mixxxdj/libkeyfinder/releases/latest

	tar -xf mixxxdj-libkeyfinder-*
	rm -- *.tar.gz
	cd mixxxdj-libkeyfinder*
	
	h="$HOME"
	so="lib/libkeyfinder.so"
	memes=()

	[ $win ] &&
		so="bin/libkeyfinder.dll" &&
		h="$(printf '%s\n' "$USERPROFILE" | tr '\\' '/')" &&
		memes+=(-G "MinGW Makefiles" -DBUILD_TESTING=OFF)
	
	[ $mac ] &&
		so="lib/libkeyfinder.dylib"

	cmake -DCMAKE_INSTALL_PREFIX="$h/pe/keyfinder" "${memes[@]}" -S . -B build
	cmake --build build --parallel $(nproc || echo 4)
	cmake --install build

	# rm -rf /Users/ed/Library/Python/3.9/lib/python/site-packages/*keyfinder*
	CFLAGS="-I$h/pe/keyfinder/include -I/opt/local/include" \
	LDFLAGS="-L$h/pe/keyfinder/lib -L/opt/local/lib" \
	PKG_CONFIG_PATH=/c/msys64/mingw64/lib/pkgconfig \
	$pybin -m pip install --user keyfinder

	pypath="$($pybin -c 'import keyfinder; print(keyfinder.__file__)')"
	libpath="$(echo "$h/pe/keyfinder/$so")"

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


install_vamp() {
	# windows support:
	#   use msys2 in mingw-w64 mode
	#   pacman -S --needed mingw-w64-x86_64-{ffmpeg,python,python-pip,vamp-plugin-sdk}
	
	$pybin -m pip install --user vamp
}


# not in use because it kinda segfaults, also no windows support
install_soundtouch() {
	gitlab_tarball https://gitlab.com/api/v4/projects/soundtouch%2Fsoundtouch/releases
	
	tar -xvf soundtouch-*
	rm -- *.tar.gz
	cd soundtouch-*
	
	# https://github.com/jrising/pysoundtouch
	./bootstrap
	./configure --enable-integer-samples CXXFLAGS="-fPIC" --prefix="$HOME/pe/soundtouch"
	make -j$(nproc || echo 4)
	make install
	
	CFLAGS=-I$HOME/pe/soundtouch/include/ \
	LDFLAGS=-L$HOME/pe/soundtouch/lib \
	$pybin -m pip install --user git+https://github.com/snowxmas/pysoundtouch.git
	
	pypath="$($pybin -c 'import importlib; print(importlib.util.find_spec("soundtouch").origin)')"
	libpath="$(echo "$HOME/pe/soundtouch/lib/")"
	patchelf --set-rpath "$libpath" "$pypath"

	echo
	echo soundtouch successfully installed to the following locations:
	echo "  $libpath"
	echo "  $pypath"
}


[ "$1" = keyfinder ] && { install_keyfinder; exit $?; }
[ "$1" = soundtouch ] && { install_soundtouch; exit $?; }
[ "$1" = vamp ] && { install_vamp; exit $?; }

echo no args provided, installing keyfinder and vamp
install_keyfinder
install_vamp
