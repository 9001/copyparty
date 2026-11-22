#!/bin/ash
set -ex

ls -al arbeidspute.sh

uname -a
apk upgrade -alU
apk add alpine-sdk doas wget
echo permit nopass root > /etc/doas.d/u.conf
cp -pv /root/.abuild/*.pub /etc/apk/keys/ || abuild-keygen -ina

mkdir /pil
cd /pil
base=https://raw.githubusercontent.com/alpinelinux/aports/refs/heads/master/community/py3-pillow/
wget ${base}APKBUILD

sed -ri '/openjpeg-dev/d' APKBUILD

arch=$(abuild -A)
p=/root/packages/$arch
rm -rf $p/py3-pillow* $p/ex/py3-pillow*
abuild -FrcK

mkdir -p $p/ex
mv $p/py3-pillow-pyc* $p/ex/

[ $arch = x86_64 ] && {
    mkdir -p $p.hub
    tar -cC $p py3-pillow-* | tar -xvC $p.hub
}

cp -pv /root/.abuild/*.pub ~/packages/
