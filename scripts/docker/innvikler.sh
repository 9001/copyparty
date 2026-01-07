#!/bin/ash
set -ex

tmv() {
	touch -r "$1" t
	mv t "$1"
}
iawk() {
	awk "$1" <"$2" >t
	tmv "$2"
}
ised() {
	sed -r "$1" <"$2" >t
	tmv "$2"
}

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

cd /usr/lib/python3.*/site-packages/copyparty/
rm stolen/surrogateescape.py
iawk '/^[^ ]/{s=0}/^if not VENDORED:/{s=1}!s' qrkode.py
iawk '/^[^ ]/{s=0}/^    DNS_VND = False/{s=1;print"    raise"}!s' mdns.py

# speedhack
ised 's/os.environ.get\("PRTY_NO_IMPRESO"\)/"1"/' util.py

# drop bytecode
find / -xdev -name __pycache__ -print0 | xargs -0 rm -rf

# build the stuff we want
python3 -m compileall -qj4 site-packages sqlite3 xml

# drop the stuff we dont
find -name __pycache__ |
  grep -E 'ty/web/|/pycpar' |
  tr '\n' '\0' | xargs -0 rm -rf





smoketest() {

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

}

smoketest





[ "$1" == min ] && {
  # shrink amd64 from 45.5 to 33.2 MiB

  # libstdc++ is pulled in by libmpdec++ in libmpdec; keep libmpdec.so
  cd /usr/lib ; rm -rf \
  libmpdec++.so* \
  libncurses* \
  libpanelw* \
  libreadline* \
  libstdc++.so* \
  --

  cd /usr/lib/python3.*/lib-dynload/ ; rm -rf \
  *audioop.* \
  _asyncio.* \
  _ctypes_test.* \
  _curses* \
  _test* \
  _xx* \
  ossaudio.* \
  readline.* \
  xx* \
  --

  # keep http/client for u2c
  cd /usr/lib/python3.*/ ; rm -rf \
  site-packages/*.dist-info \
  aifc.py \
  asyncio \
  bdb.py \
  cgi.py \
  config-3.*/Makefile \
  ctypes/macholib \
  dbm \
  difflib.py \
  doctest.py \
  email/_header_value_parser.py \
  html \
  http/cookiejar.* \
  http/server.* \
  imaplib.py \
  importlib/resources \
  mailbox.py \
  nntplib.py \
  pickletools.py \
  pydoc.py \
  smtplib.py \
  statistics.py \
  tomllib \
  unittest \
  urllib/request.* \
  venv \
  wsgiref \
  xml/dom \
  xml/sax \
  xmlrpc \
  --

  set +x
  find -iname '*.pyc' |
  grep -viE 'tftpy' |
  while IFS= read -r x; do
    y="$(printf '%s\n' "$x" | sed -r 's`/__pycache__/([^/]+)\.cpython-312\.pyc$`/\1.py`')"
    [ -e "$y" ] || continue
    [ "$y" = "$x" ] && continue
    rm "$y"
    mv "$x" "${y}c"
  done
  find -iname __pycache__ -print0 | xargs -0 rm -rf --
  rm -rf /a
  set -x

  smoketest

  # printf '%s\n' 'FROM localhost/copyparty-min-amd64' 'COPY a /' 'RUN /bin/ash /a' >Dockerfile
  # podman rmi localhost/m2 ; podman build --squash-all -t m2 . && podman images && podman run --rm -it localhost/m2 --exit=idx && podman images
}





# goodbye
exec rm innvikler.sh
