#!/bin/bash
set -e

curl http://192.168.123.1:3923/cpp/scripts/pyinstaller/build.sh |
tee build2.sh | cmp build.sh && rm build2.sh || {
    echo "new build script; upgrade y/n:"
    while true; do read -u1 -n1 -r r; [[ $r =~ [yYnN] ]] && break; done
    [[ $r =~ [yY] ]] && mv build{2,}.sh && exec ./build.sh
}

dl() { curl -fkLO "$1"; }

cd ~/Downloads

dl https://192.168.123.1:3923/cpp/dist/copyparty-sfx.py
dl https://192.168.123.1:3923/cpp/scripts/pyinstaller/loader.ico
dl https://192.168.123.1:3923/cpp/scripts/pyinstaller/loader.py
dl https://192.168.123.1:3923/cpp/scripts/pyinstaller/loader.rc

rm -rf $TEMP/pe-copyparty*
python copyparty-sfx.py --version

rm -rf mods; mkdir mods
cp -pR $TEMP/pe-copyparty/copyparty/ $TEMP/pe-copyparty/{ftp,j2}/* mods/

rm -rf mods/magic/
grep -lR 'import multiprocessing' | while read x; do
    sed -ri 's/import multiprocessing/import fgsfds/' $x
done

read a b c d _ < <(
    grep -E '^VERSION =' mods/copyparty/__version__.py |
    tail -n 1 |
    sed -r 's/[^0-9]+//;s/[" )]//g;s/[-,]/ /g;s/$/ 0/'
)
sed -r 's/1,2,3,0/'$a,$b,$c,$d'/;s/1\.2\.3/'$a.$b.$c/ <loader.rc >loader.rc2

$APPDATA/python/python37/scripts/pyinstaller \
    -y --clean -p mods --upx-dir=. \
    --version-file loader.rc2 -i loader.ico -n copyparty -c -F loader.py \
    --add-data 'mods/copyparty/res;copyparty/res' \
    --add-data 'mods/copyparty/web;copyparty/web'

# ./upx.exe --best --ultra-brute --lzma -k dist/copyparty.exe

curl -fkT dist/copyparty.exe -b cppwd=wark https://192.168.123.1:3923/
