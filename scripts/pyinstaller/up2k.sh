#!/bin/bash
set -e

curl -k https://192.168.123.1:3923/cpp/scripts/pyinstaller/up2k.sh |
tee up2k2.sh | cmp up2k.sh && rm up2k2.sh || {
    [ -s up2k2.sh ] || exit 1
    echo "new up2k script; upgrade y/n:"
    while true; do read -u1 -n1 -r r; [[ $r =~ [yYnN] ]] && break; done
    [[ $r =~ [yY] ]] && mv up2k{2,}.sh && exec ./up2k.sh
}

uname -s | grep -E 'WOW64|NT-10' && echo need win7-32 && exit 1

dl() { curl -fkLO "$1"; }
cd ~/Downloads

dl https://192.168.123.1:3923/cpp/bin/u2c.py
dl https://192.168.123.1:3923/cpp/scripts/pyinstaller/up2k.ico
dl https://192.168.123.1:3923/cpp/scripts/pyinstaller/up2k.rc
dl https://192.168.123.1:3923/cpp/scripts/pyinstaller/up2k.spec

# $LOCALAPPDATA/programs/python/python37-32/python -m pip install --user -U pyinstaller

sed -ri 's/^(import .*), selectors$/\1\ntry: import selectors\nexcept: pass/' $LOCALAPPDATA/programs/python/python37-32/Lib/socket.py

sed -ri 's/(add_argument."-t[de]",.*help=")[^"]+/\1not applicable; HTTPS is disabled in this exe/; s/for some reason/in this exe for safety reasons/' u2c.py
sed -ri '/^import platform/d;s/^(VT100 = )pla.*/\1False/' u2c.py

read a b _ < <(awk -F\" '/^S_VERSION =/{$0=$2;sub(/\./," ");print}' < u2c.py)
sed -r 's/1,2,3,0/'$a,$b,0,0'/;s/1\.2\.3/'$a.$b.0/ <up2k.rc >up2k.rc2

#python uncomment.py u2c.py
$APPDATA/python/python37/scripts/pyinstaller -y --clean --upx-dir=. up2k.spec

./dist/u2c.exe --version

csum=$(sha512sum <dist/u2c.exe | cut -c-56)

curl -fkT dist/u2c.exe -HPW:wark https://192.168.123.1:3923/ >uplod.log
cat uplod.log

grep -q $csum uplod.log && echo upload OK || {
    echo UPLOAD FAILED
    exit 1
}
