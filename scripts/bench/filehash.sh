#!/bin/bash
set -euo pipefail

# check how fast copyparty is able to hash files during indexing
# assuming an infinitely fast HDD to read from (alternatively,
# checks whether you will be bottlenecked by CPU or HDD)
#
# uses copyparty's default config of using, well, it's complicated:
# * if you have more than 8 cores, then 5 threads,
# * if you have between 4 and 8, then 4 threads,
# * anything less and it takes your number of cores
#
# can be adjusted with --hash-mt (but alpine caps out at 5)

[ $# -ge 1 ] || {
	echo 'need arg 1: path to copyparty-sfx.py'
	echo ' (remaining args will be passed on to copyparty,'
	echo '  for example to tweak the hasher settings)'
	exit 1
}
sfx="$1"
shift
sfx="$(realpath "$sfx" || readlink -e "$sfx" || echo "$sfx")"
awk=$(command -v gawk || command -v awk)

# try to use /dev/shm to avoid hitting filesystems at all,
# otherwise fallback to mktemp which probably uses /tmp
td=/dev/shm/cppbenchtmp
mkdir $td || td=$(mktemp -d)
trap "rm -rf $td" INT TERM EXIT
cd $td

echo creating 256 MiB testfile in $td
head -c $((1024*1024*256)) /dev/urandom > 1

echo creating 127 symlinks to it
for n in $(seq 2 128); do ln -s 1 $n; done

echo warming up cache
cat 1 >/dev/null

echo ok lets go
python3 "$sfx" -p39204 -e2dsa --dbd=yolo --exit=idx -lo=t -q "$@"

echo and the results are...
$awk '/1 volumes in / {printf "%s MiB/s\n", 256*128/$(NF-1)}' <t

echo deleting $td and exiting

##
## some results:

# MiB/s @ cpu or device  (copyparty, pythonver, distro/os)  // comment

#  3608 @ Ryzen 5 4500U  (cpp 1.9.5, py 3.11.5, fedora 38)  // --hash-mt=6; laptop
#  2726 @ Ryzen 5 4500U  (cpp 1.9.5, py 3.11.5, fedora 38)  // --hash-mt=4 (old-default)
#  2202 @ Ryzen 5 4500U  (cpp 1.9.5, py 3.11.5, docker-alpine 3.18.3) ??? alpine slow
#  2719 @ Ryzen 5 4500U  (cpp 1.9.5, py 3.11.2, docker-debian 12.1)

#  5544 @ Intel i5-12500 (cpp 1.9.5, py 3.11.2, debian 12.0)  // --hash-mt=12; desktop
#  5197 @ Ryzen 7 3700X  (cpp 1.9.5, py 3.9.18, freebsd 13.2)  // --hash-mt=8; 2u server
#  2606 @ Ryzen 7 3700X  (cpp 1.9.5, py 3.9.18, freebsd 13.2)  // --hash-mt=4 (old-default)
#  1436 @ Ryzen 5 5500U  (cpp 1.9.5, py 3.11.4, alpine 3.18.3)  // nuc
#  1065 @ Pixel 7        (cpp 1.9.5, py 3.11.5, termux 2023-09)

# notes,
# podman run --rm -it --shm-size 512m --entrypoint /bin/ash localhost/copyparty-min
# podman <filehash.sh run --rm -i --shm-size 512m --entrypoint /bin/ash localhost/copyparty-min -s - /z/copyparty-sfx.py
