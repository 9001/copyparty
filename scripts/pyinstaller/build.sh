#!/bin/bash
set -e

curl -k https://192.168.123.1:3923/cpp/scripts/pyinstaller/build.sh |
tee build2.sh | cmp build.sh && rm build2.sh || {
    [ -s build2.sh ] || exit 1
    echo "new build script; upgrade y/n:"
    while true; do read -u1 -n1 -r r; [[ $r =~ [yYnN] ]] && break; done
    [[ $r =~ [yY] ]] && mv build{2,}.sh && exec ./build.sh
}

clean=--clean
[ "$1" = f ] && clean= && shift

uname -s | grep WOW64 && m=64 || m=32
uname -s | grep NT-10 && w10=1 || w7=1
[ $w7 ] && [ -e up2k.sh ] && [ ! "$1" ] && ./up2k.sh

[ $w7 ] && pyv=37 || pyv=311
esuf=
[ $w7 ] && [ $m = 32 ] && esuf=32
[ $w7 ] && [ $m = 64 ] && esuf=-winpe64

appd=$(cygpath.exe "$APPDATA")
spkgs=$appd/Python/Python$pyv/site-packages

dl() { curl -fkLO "$1"; }

cd ~/Downloads

dl https://192.168.123.1:3923/cpp/dist/copyparty-sfx.py
dl https://192.168.123.1:3923/cpp/scripts/pyinstaller/loader.ico
dl https://192.168.123.1:3923/cpp/scripts/pyinstaller/loader.py
dl https://192.168.123.1:3923/cpp/scripts/pyinstaller/loader.rc

rm -rf $TEMP/pe-copyparty*
python copyparty-sfx.py --version

rm -rf mods; mkdir mods
cp -pR $TEMP/pe-copyparty/{copyparty,partftpy}/ $TEMP/pe-copyparty/{ftp,j2}/* mods/
[ $w10 ] && rm -rf mods/{jinja2,markupsafe}

af() { awk "$1" <$2 >tf; mv tf "$2"; }

rm -rf mods/magic/

[ $w7 ] && {
    sed -ri /pickle/d mods/jinja2/_compat.py
    sed -ri '/(bccache|PackageLoader)/d' mods/jinja2/__init__.py
    af '/^class/{s=0}/^class PackageLoader/{s=1}!s' mods/jinja2/loaders.py
}
[ $w10 ] && {
    sed -ri '/(bccache|PackageLoader)/d' $spkgs/jinja2/__init__.py
    for f in nodes async_utils; do
        sed -ri 's/\binspect\b/os/' $spkgs/jinja2/$f.py
    done
}

sed -ri /fork_process/d mods/pyftpdlib/servers.py
af '/^class _Base/{s=1}!s' mods/pyftpdlib/authorizers.py

read a b c d _ < <(
    grep -E '^VERSION =' mods/copyparty/__version__.py |
    tail -n 1 |
    sed -r 's/[^0-9]+//;s/[" )]//g;s/[-,]/ /g;s/$/ 0/'
)
sed -r 's/1,2,3,0/'$a,$b,$c,$d'/;s/1\.2\.3/'$a.$b.$c/ <loader.rc >loader.rc2
sed -ri s/copyparty.exe/copyparty$esuf.exe/ loader.rc2

excl=(
    asyncio
    copyparty.broker_mp
    copyparty.broker_mpw
    copyparty.smbd
    ctypes.macholib
    curses
    email._header_value_parser
    email.header
    email.parser
    inspect
    multiprocessing
    packaging
    pdb
    pickle
    PIL.EpsImagePlugin
    pyftpdlib.prefork
    urllib.request
    urllib.response
    urllib.robotparser
    zipfile
)
[ $w10 ] && excl+=(
    PIL.ImageQt
    PIL.ImageShow
    PIL.ImageTk
    PIL.ImageWin
    PIL.PdfParser
) || excl+=(
    PIL
    PIL.ExifTags
    PIL.Image
    PIL.ImageDraw
    PIL.ImageOps
)
excl=( "${excl[@]/#/--exclude-module }" )

$APPDATA/python/python$pyv/scripts/pyinstaller \
    -y $clean -p mods --upx-dir=. \
    ${excl[*]} \
    --version-file loader.rc2 -i loader.ico -n copyparty -c -F loader.py \
    --add-data 'mods/copyparty/res;copyparty/res' \
    --add-data 'mods/copyparty/web;copyparty/web'

# ./upx.exe --best --ultra-brute --lzma -k dist/copyparty.exe

printf $(sha512sum ~/Downloads/dist/copyparty.exe | head -c 18 | sed -r 's/(..)/\\x\1/g') |
base64 | head -c12 >> dist/copyparty.exe

dist/copyparty.exe --version

csum=$(sha512sum <dist/copyparty.exe | cut -c-56)

curl -fkT dist/copyparty.exe -b cppwd=wark https://192.168.123.1:3923/copyparty$esuf.exe >uplod.log
cat uplod.log

grep -q $csum uplod.log && echo upload OK || {
    echo UPLOAD FAILED
    exit 1
}
