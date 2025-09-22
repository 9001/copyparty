#!/bin/ash
set -ex

# use zlib-ng if available
f=/z/base/zlib_ng-0.5.1-cp312-cp312-linux_$(cat /etc/apk/arch).whl
[ "$1" != min ] && [ -e $f ] && {
  apk add -t .bd !pyc py3-pip
  rm -f /usr/lib/python3*/EXTERNALLY-MANAGED
  pip install $f
  apk del .bd
}
rm -rf /z/base

# cleanup for flavors with python build steps (dj/iv)
rm -rf /var/cache/apk/* /root/.cache

# initial config; common for all flavors
mkdir /state /cfg /w
chmod 777 /state /cfg /w
cat >initcfg <<'EOF'
[global]
  chdir: /w
  no-crt

% /cfg
EOF

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

# speedhack
sed -ri 's/os.environ.get\("PRTY_NO_IMPRESO"\)/"1"/' /usr/lib/python3.*/site-packages/copyparty/util.py

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
  -v .::r --no-crt -qi127.1 --exit=idx -e2dsa -e2ts

########################################################################
# test download-as-tar.gz

t=$(mktemp)
python3 -m copyparty \
  --ign-ebind -p$((1024+RANDOM)),$((1024+RANDOM)),$((1024+RANDOM)) \
  -v .::r --no-crt -qi127.1 --wr-h-eps $t & pid=$!

for n in $(seq 1 900); do sleep 0.2
  v=$(awk '/^127/{print;n=1;exit}END{exit n-1}' $t) && break
done
[ -z "$v" ] && echo SNAAAAAKE && exit 1
rm $t

for n in $(seq 1 900); do sleep 0.2
  wget -O- http://${v/ /:}/?tar=gz:1 >tf && break
done
tar -xzO top/innvikler.sh <tf | cmp innvikler.sh
rm tf

kill $pid; wait $pid

########################################################################

# output from -e2d
rm -rf .hist /cfg/copyparty

# goodbye
exec rm innvikler.sh
