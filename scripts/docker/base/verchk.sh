#!/bin/bash
set -e

v=3.23

mkdir -p cver
rm -rf cver2
mkdir cver2
cd cver2
curl \
    -Lo1 https://raw.githubusercontent.com/alpinelinux/aports/refs/heads/$v-stable/main/musl/APKBUILD \
    -Lo2 https://raw.githubusercontent.com/alpinelinux/aports/refs/heads/$v-stable/main/python3/APKBUILD \
    -Lo3 https://raw.githubusercontent.com/alpinelinux/aports/refs/heads/$v-stable/community/ffmpeg/APKBUILD \
    ;

zlib= ff=
cmp 1 ../cver/1 || zlib=1
cmp 2 ../cver/2 || zlib=1
cmp 3 ../cver/3 || ff=1
echo zlib=$zlib ff=$ff

[ $zlib ] && { make zlib; cp -pv 1 2 ../cver/; }
[ $ff ] &&   { make ff;   cp -pv 3 ../cver/; }
rm -rf cver2
