#!/bin/bash
set -e

# upload $datalen worth of generated data with a random filename,
# using a single connection for all chunks


##
## config

datalen=$((2*1024*1024*1024))
target=127.0.0.1
posturl=/inc
passwd=wark


##
## derived/generated

salt=$(head -c 21 /dev/urandom | base64 -w0 | tr '+/' '-_')
datalen=$((datalen-3))

openssl enc -aes-256-ctr -pass pass:$salt -nosalt < /dev/zero 2>/dev/null |
head -c 524287 > /dev/shm/$salt.bin  #2147483647


##
## functions

# produce a stream of data
gendata() {
    while true; do
        cat /dev/shm/$salt.bin{,,,,,,,,,,,,,,,,,,}
    done
}

# pipe a chunk, get the base64 checksum
gethash() {
    printf $(
        sha512sum | cut -c-64 |
        sed -r 's/ .*//;s/(..)/\\x\1/g'
    ) |
    base64 -w0 | cut -c-43 |
    tr '+/' '-_'
}

# division except ceil() instead of floor()
ceildiv() {
    local num=$1
    local div=$2
    echo $(((num+div-1)/div))
}

# provide filesize, get correct chunksize
getchunksize() {
    local filesize=$1
    local chunksize=$((1024 * 1024))
    local stepsize=$((512 * 1024))
    while true; do
        for mul in 1 2; do
            local nchunks=$(ceildiv filesize chunksize)
            
            [ $nchunks -le 256 ] ||
            [ $chunksize -ge $((32 * 1024 * 1024)) ] && {
                echo $chunksize
                return
            }

            chunksize=$((chunksize+stepsize))
            stepsize=$((stepsize*mul))
        done
    done
}

# pipe data + provide full length, get all chunk checksums
gethashes() {
    local datalen=$1
    local chunksize=$(getchunksize $datalen)
    local nchunks=$(ceildiv $datalen $chunksize)
    
    echo >&2
    while [ $nchunks -gt 0 ]
    do
        head -c $chunksize | gethash
        nchunks=$((nchunks-1))
        printf '\033[Ahash %s \n' $nchunks >&2
    done
}

# pipe handshake response, get wark
getwark() {
    awk '/"wark": ?"/ {sub(/.*"wark": ?"/,"");sub(/".*/,"");print}'
}


##
## create handshake json

chunksize=$(getchunksize $datalen)

printf '{"name":"%s.bin","size":%d,"hash":[' $salt $datalen >/dev/shm/$salt.hs

printf '\033[33m'
gendata |
head -c $datalen |
gethashes $datalen > /dev/shm/$salt.hl
printf '\033[0m'

IFS=$'\n' GLOBIGNORE='*' command eval 'HASHES=($(cat "/dev/shm/$salt.hl"))'

awk '{printf "%s\"%s\"", v, $0; v=","}' /dev/shm/$salt.hl >> /dev/shm/$salt.hs

printf ']}' >> /dev/shm/$salt.hs


##
## post handshake

printf '\033[36m'

#curl "http://$target:1234$posturl/handshake.php" -H "Content-Type: text/plain;charset=UTF-8" -H "Cookie: cppwd=$passwd" --data "$(cat "/dev/shm/$salt.hs")" | tee /dev/shm/$salt.res

{
    {
        cat <<EOF
POST $posturl/handshake.php HTTP/1.1
Connection: Close
Cookie: cppwd=$passwd
Content-Type: text/plain;charset=UTF-8
Content-Length: $(cat /dev/shm/$salt.hs | wc -c)

EOF
    } | sed -r 's/$/\r/'

    cat /dev/shm/$salt.hs
} |
tee /dev/shm/$salt.hsb |
ncat $target 1234 |
tee /dev/shm/$salt.hs1r

wark="$(cat /dev/shm/$salt.hs1r | getwark)"
printf '\033[0m\nwark: %s\n' $wark


##
## wait for signal to continue

w8=/dev/shm/$salt.w8
touch $w8

echo "ready;  rm -f $w8"

while [ -e $w8 ]; do
    sleep 0.2
done


##
## post chunks

t0=$(date +%s.%N)
remains=$datalen
nchunk=0

gendata |
head -c $datalen |
while [ $remains -gt 0 ]; do
    [ $remains -ge $chunksize ] &&
        postlen=$chunksize ||
        postlen=$remains
    
    printf '\n\n=> %s %s\n' $remains $postlen >&2

    remains=$((remains-postlen))
    
    {
        cat <<EOF
POST $posturl/chunkpit.php HTTP/1.1
Connection: Keep-Alive
Cookie: cppwd=$passwd
Content-Type: application/octet-stream
Content-Length: $postlen
X-Up2k-Hash: ${HASHES[$nchunk]}
X-Up2k-Wark: $wark

EOF
    } | sed -r 's/$/\r/'

    head -c $postlen
    nchunk=$((nchunk+1))

done |
ncat $target 1234 |
tee /dev/shm/$salt.pr

t=$(date +%s.%N)


##
## handshake again

printf '\033[36m'

ncat $target 1234 < /dev/shm/$salt.hsb |
tee /dev/shm/$salt.hs2r |
grep -E '"hash": ?\[ *\]'

rv=$?

[ $rv -eq 0 ] &&
    printf '\033[32mok\033[0m\n' ||
    printf '\033[31mERROR\033[0m\n'

td=$(echo "scale=3; $t-$t0" | bc)
spd=$(echo "scale=3; ($datalen/$td)/(1024.0*1024)" | bc)

printf '%.3f sec, %.3f MiB/s\n' $td $spd |
tee /dev/shm/$salt.spd

exit $rv

# find /dev/shm/ -maxdepth 1 -type f | grep -E '/[a-zA-Z0-9_-]{28}\.[a-z0-9]+$' | xargs rm; for n in {1..8}; do ./up2k.sh & done; wait; cat /dev/shm/*.spd | sort -n
