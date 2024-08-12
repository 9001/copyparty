#!/bin/ash
set -ex

# cleanup for flavors with python build steps (dj/iv)
rm -rf /var/cache/apk/* /root/.cache

# initial config; common for all flavors
mkdir /cfg /w
chmod 777 /cfg /w
echo % /cfg > initcfg

# unpack sfx and dive in
python3 copyparty-sfx.py --version
cd /tmp/pe-copyparty.0

# steal the stuff we need
mv copyparty partftpy ftp/* /usr/lib/python3.*/site-packages/

# golf
cd /usr/lib/python3.*/
rm -rf \
  /tmp/pe-* /z/copyparty-sfx.py \
  ensurepip pydoc_data turtle.py turtledemo lib2to3

# drop bytecode
find / -xdev -name __pycache__ -print0 | xargs -0 rm -rf

# build the stuff we want
python3 -m compileall -qj4 site-packages sqlite3 xml

# drop the stuff we dont
find -name __pycache__ |
  grep -E 'ty/web/|/pycpar' |
  tr '\n' '\0' | xargs -0 rm -rf

# two-for-one:
# 1) smoketest copyparty even starts
# 2) build any bytecode we missed
# this tends to race other builders (alle gode ting er tre)
cd /z
python3 -m copyparty \
  --ign-ebind -p$((1024+RANDOM)),$((1024+RANDOM)),$((1024+RANDOM)) \
  --no-crt -qi127.1 --exit=idx -e2dsa -e2ts

# output from -e2d
rm -rf .hist
