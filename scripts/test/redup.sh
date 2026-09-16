#!/bin/bash
set -e

td=redump-test

st_orig() { cat <<'EOF'
f1,1,'f1',3660
f2,1,'f2',3720
f3,2,'f3',3960
f4,1,'f4',3840
f5,1,'f5' -> 'f2',3900
f6,2,'f6',3960
f7,1,'f7',4020
f8,1,'f8',4080
f9,1,'f9',4140
EOF
}
st_ref() { cat <<'EOF'
f1,1,'f1',3660
f2,1,'f2',3720
f3,1,'f3',3960
f4,1,'f4',3840
f5,1,'f5',3900
f6,1,'f6',3960
f7,1,'f7',4020
f8,1,'f8',4080
f9,1,'f9',4140
EOF
}
st_sym() { cat <<'EOF'
f1,1,'f1',3660
f2,1,'f2',3720
f3,1,'f3',3960
f4,1,'f4',3840
f5,1,'f5' -> 'f2',3900
f6,1,'f6' -> 'f3',3960
f7,1,'f7' -> 'f4',4020
f8,1,'f8' -> 'f1',4080
f9,1,'f9' -> 'f1',4140
EOF
}
st_hard() { cat <<'EOF'
f1,3,'f1',3600
f2,2,'f2',3600
f3,2,'f3',3600
f4,2,'f4',3600
f5,2,'f5',3600
f6,2,'f6',3600
f7,2,'f7',3600
f8,3,'f8',3600
f9,3,'f9',3600
EOF
}
statchk() {
    (cd $td;stat -c%n,%h,%N,%Y * | sort -n | diff -U9 <($1) -) && return
    cat $td/* | grep -vE '^f1f2f3f4f2f3f4f1f1$' || return
    cat $td.l
    exit 1
}
setup() {
    rm -rf $td
    mkdir $td
    th=19700101010 #..M
    tu=978310800 #unix
    ( cd "$td"
        for n in {1..4}; do echo -n f$n > f$n; done
        ln -s f2 f5
        ln f3 f6
        cp --reflink=always f4 f7
        cp --reflink=never f1 f8
        cp --reflink=never f1 f9
        for n in {1..9}; do touch -ht $th$n f$n; done
    );statchk st_orig
}
export PRTY_NO_ARGON2=1
export PRTY_NO_CFSSL=1
export PRTY_NO_FFMPEG=1
export PRTY_NO_FFPROBE=1
export PRTY_NO_IFADDR=1
export PRTY_NO_IMPRESO=1
export PRTY_NO_MAGIC=1
export PRTY_NO_PARAMIKO=1
export PRTY_NO_PARTFTPY=1
export PRTY_NO_PIL=1
export PRTY_NO_PSUTIL=1
export PRTY_NO_PYFTPD=1
export PRTY_NO_RAW=1
export PRTY_NO_VIPS=1

cmd="python -m copyparty -i no --ign-ebind-all --no-ses --no-fastboot --no-voldump --exit=idx --ansi -v $td::A"

fs=$(stat -fc%T .)
if [ "$fs" = btrfs ]; then
    echo ref:;  setup; $cmd -e2dsa --redup sym,hard,ref=ref >$td.l; statchk st_ref
else
    printf 'detected filesystem [%s] which is not btrfs, will NOT run reflink test\n' "$fs"
fi

echo sym:;  setup; $cmd -e2dsa --redup sym,hard,ref=sym >$td.l; statchk st_sym

echo hard:; setup; $cmd -e2dsa --redup sym,hard,ref=hard >$td.l; touch -ht 197001010100 $td/*; statchk st_hard
# `- ign hard mtimes because redup is order-undefined (or sqlite-row-order rather but ye)

rm -rf $td $td.l
