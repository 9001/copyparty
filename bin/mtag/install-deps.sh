#!/bin/bash
set -e


# install dependencies for audio-*.py
#
# linux/alpine: requires gcc g++ make cmake patchelf {python3,ffmpeg,fftw,libsndfile}-dev py3-{wheel,pip} py3-numpy{,-dev}
# linux/debian: requires libav{codec,device,filter,format,resample,util}-dev {libfftw3,python3,libsndfile1}-dev python3-{numpy,pip} vamp-{plugin-sdk,examples} patchelf cmake
# linux/fedora: requires gcc gcc-c++ make cmake patchelf {python3,ffmpeg,fftw,libsndfile}-devel python3-numpy vamp-plugin-sdk qm-vamp-plugins
# linux/arch:   requires gcc make cmake patchelf python3 ffmpeg fftw libsndfile python-{numpy,wheel,pip,setuptools}
# win64: requires msys2-mingw64 environment
# macos: requires macports
#
# has the following manual dependencies, especially on mac:
#   https://www.vamp-plugins.org/pack.html
#
# installs stuff to the following locations:
#   ~/pe/
#   whatever your python uses for --user packages
#
# does the following terrible things:
#   modifies the keyfinder python lib to load the .so in ~/pe


linux=1

win=
[ ! -z "$MSYSTEM" ] || [ -e /msys2.exe ] && {
	[ "$MSYSTEM" = MINGW64 ] || {
		echo windows detected, msys2-mingw64 required
		exit 1
	}
	pacman -S --needed mingw-w64-x86_64-{ffmpeg,python,python-pip,vamp-plugin-sdk}
	win=1
	linux=
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
	linux=
}

hash -r

[ $mac ] || {
	command -v python3 && pybin=python3 || pybin=python
}

$pybin -c 'import numpy' ||
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
need ffmpeg
need $pybin
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
	local yolo= ex=
	[ $1 = "yolo" ] && yolo=1 && ex=k && shift
	command -v curl >/dev/null && exec curl -${ex}JOL "$@"
	
	[ $yolo ] && ex=--no-check-certificate
	exec wget --trust-server-names $ex "$@"
}
export -f dl_files


github_tarball() {
	rm -rf g
	mkdir g
	cd g
	dl_text "$1" |
	tee ../json |
	(
		# prefer jq if available
		jq -r '.tarball_url' ||

		# fallback to awk (sorry)
		awk -F\" '/"tarball_url": "/ {print$4}'
	) |
	tee /dev/stderr |
	head -n 1 |
	tr -d '\r' | tr '\n' '\0' |
	xargs -0 bash -c 'dl_files "$@"' _
	mv * ../tgz
	cd ..
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
	head -n 1 |
	tr -d '\r' | tr '\n' '\0' |
	tee links |
	xargs -0 bash -c 'dl_files "$@"' _
}


install_keyfinder() {
	# windows support:
	#   use msys2 in mingw-w64 mode
	#   pacman -S --needed mingw-w64-x86_64-{ffmpeg,python}
	
	[ -e $HOME/pe/keyfinder ] && {
		echo found a keyfinder build in ~/pe, skipping
		return
	}

	cd "$td"
	github_tarball https://api.github.com/repos/mixxxdj/libkeyfinder/releases/latest
	ls -al

	tar -xf tgz
	rm tgz
	cd mixxxdj-libkeyfinder*
	
	h="$HOME"
	so="lib/libkeyfinder.so"
	memes=(-DBUILD_TESTING=OFF)

	[ $win ] &&
		so="bin/libkeyfinder.dll" &&
		h="$(printf '%s\n' "$USERPROFILE" | tr '\\' '/')" &&
		memes+=(-G "MinGW Makefiles")
	
	[ $mac ] &&
		so="lib/libkeyfinder.dylib"

	cmake -DCMAKE_INSTALL_PREFIX="$h/pe/keyfinder" "${memes[@]}" -S . -B build
	cmake --build build --parallel $(nproc || echo 4)
	cmake --install build

	libpath="$h/pe/keyfinder/$so"
	[ $linux ] && [ ! -e "$libpath" ] &&
		so=lib64/libkeyfinder.so
	
	libpath="$h/pe/keyfinder/$so"
	[ -e "$libpath" ] || {
		echo "so not found at $sop"
		exit 1
	}
	
	# rm -rf /Users/ed/Library/Python/3.9/lib/python/site-packages/*keyfinder*
	CFLAGS="-I$h/pe/keyfinder/include -I/opt/local/include -I/usr/include/ffmpeg" \
	LDFLAGS="-L$h/pe/keyfinder/lib -L$h/pe/keyfinder/lib64 -L/opt/local/lib" \
	PKG_CONFIG_PATH=/c/msys64/mingw64/lib/pkgconfig \
	$pybin -m pip install --user keyfinder

	pypath="$($pybin -c 'import keyfinder; print(keyfinder.__file__)')"
	for pyso in "${pypath%/*}"/*.so; do
		[ -e "$pyso" ] || break
		patchelf --set-rpath "${libpath%/*}" "$pyso" ||
			echo "WARNING: patchelf failed (only fatal on musl-based distros)"
	done
	
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


have_beatroot() {
	$pybin -c 'import vampyhost, sys; plugs = vampyhost.list_plugins(); sys.exit(0 if "beatroot-vamp:beatroot" in plugs else 1)'
}


install_vamp() {
	# windows support:
	#   use msys2 in mingw-w64 mode
	#   pacman -S --needed mingw-w64-x86_64-{ffmpeg,python,python-pip,vamp-plugin-sdk}
	
	$pybin -m pip install --user vamp || {
		printf '\n\033[7malright, trying something else...\033[0m\n'
		$pybin -m pip install --user --no-build-isolation vamp
	}

	cd "$td"
	echo '#include <vamp-sdk/Plugin.h>' | g++ -x c++ -c -o /dev/null - || [ -e ~/pe/vamp-sdk ] || {
		printf '\033[33mcould not find the vamp-sdk, building from source\033[0m\n'
		(dl_files yolo https://ocv.me/mirror/vamp-plugin-sdk-2.10.0.tar.gz)
		sha512sum -c <(
			echo "153b7f2fa01b77c65ad393ca0689742d66421017fd5931d216caa0fcf6909355fff74706fabbc062a3a04588a619c9b515a1dae00f21a57afd97902a355c48ed  -"
		) <vamp-plugin-sdk-2.10.0.tar.gz
		tar -xf vamp-plugin-sdk-2.10.0.tar.gz
		rm -- *.tar.gz
		ls -al
		cd vamp-plugin-sdk-*
		printf '%s\n' "int main(int argc, char **argv) { return 0; }" > host/vamp-simple-host.cpp
		./configure --disable-programs --prefix=$HOME/pe/vamp-sdk
		make -j1 install
	}

	cd "$td"
	have_beatroot || {
		printf '\033[33mcould not find the vamp beatroot plugin, building from source\033[0m\n'
		(dl_files yolo https://ocv.me/mirror/beatroot-vamp-v1.0.tar.gz)
		sha512sum -c <(
			echo "1f444d1d58ccf565c0adfe99f1a1aa62789e19f5071e46857e2adfbc9d453037bc1c4dcb039b02c16240e9b97f444aaff3afb625c86aa2470233e711f55b6874  -"
		) <beatroot-vamp-v1.0.tar.gz
		tar -xf beatroot-vamp-v1.0.tar.gz 
		rm -- *.tar.gz
		cd beatroot-vamp-v1.0
		[ -e ~/pe/vamp-sdk ] &&
			sed -ri 's`^(CFLAGS :=.*)`\1 -I'$HOME'/pe/vamp-sdk/include`' Makefile.linux ||
			sed -ri 's`^(CFLAGS :=.*)`\1 -I/usr/include/vamp-sdk`' Makefile.linux
		make -f Makefile.linux -j4 LDFLAGS="-L$HOME/pe/vamp-sdk/lib -L/usr/lib64"
		# /home/ed/vamp /home/ed/.vamp /usr/local/lib/vamp
		mkdir ~/vamp
		cp -pv beatroot-vamp.* ~/vamp/
	}
	
	have_beatroot &&
		printf '\033[32mfound the vamp beatroot plugin, nice\033[0m\n' ||
		printf '\033[31mWARNING: could not find the vamp beatroot plugin, please install it for optimal results\033[0m\n'
}


# not in use because it kinda segfaults, also no windows support
install_soundtouch() {
	cd "$td"
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
