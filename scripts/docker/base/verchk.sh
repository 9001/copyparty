#!/bin/bash
set -e

AVER=3.24

v=$AVER-stable
#v=master

mkdir -p cver
rm -rf cver2
mkdir cver2
cd cver2
curl \
    -Lo1 https://raw.githubusercontent.com/alpinelinux/aports/refs/heads/$v/main/musl/APKBUILD \
    -Lo2 https://raw.githubusercontent.com/alpinelinux/aports/refs/heads/$v/main/python3/APKBUILD \
    -Lo3 https://raw.githubusercontent.com/alpinelinux/aports/refs/heads/$v/community/ffmpeg/APKBUILD \
    ;

zlib= ff=
cmp 1 ../cver/1 || zlib=1
cmp 2 ../cver/2 || zlib=1
cmp 3 ../cver/3 || ff=1
echo zlib=$zlib ff=$ff

[ "$1" ] && exit

[ $zlib ] && { make -C.. zlib; cp -pv 1 2 ../cver/; }
[ $ff ] &&   { make -C.. ff;   cp -pv 3 ../cver/; }
rm -rf cver2
