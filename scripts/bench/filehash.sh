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

fsize=256
nfiles=128
pybin=$(command -v python3 || command -v python)
#pybin=~/.pyenv/versions/nogil-3.9.10-2/bin/python3

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
uname -s | grep -E MSYS && win=1 || win=
totalsize=$((fsize*nfiles))

# try to use /dev/shm to avoid hitting filesystems at all,
# otherwise fallback to mktemp which probably uses /tmp
td=/dev/shm/cppbenchtmp
mkdir $td || td=$(mktemp -d)
trap "rm -rf $td" INT TERM EXIT
cd $td

echo creating $fsize MiB testfile in $td
sz=$((1024*1024*fsize))
head -c $sz /dev/zero | openssl enc -aes-256-ctr -iter 1 -pass pass:k -nosalt 2>/dev/null >1 || true
wc -c 1 | awk '$1=='$sz'{r=1}END{exit 1-r}' || head -c $sz /dev/urandom >1

echo creating $((nfiles-1)) symlinks to it
for n in $(seq 2 $nfiles); do MSYS=winsymlinks:nativestrict ln -s 1 $n; done

echo warming up cache
cat 1 >/dev/null

echo ok lets go
$pybin "$sfx" -p39204 -e2dsa --dbd=yolo --exit=idx -lo=t -q "$@" && err= || err=$?
[ $win ] && [ $err = 15 ] && err=  # sigterm doesn't hook on windows, ah whatever
[ $err ] && echo ERROR $err && exit $err

echo and the results are...
LC_ALL=C $awk '/1 volumes in / {s=$(NF-1); printf "speed: %.1f MiB/s  (time=%.2fs)\n", '$totalsize'/s, s}' <t

echo deleting $td and exiting

##
## some results:

# MiB/s @ cpu or device  (copyparty, pythonver, distro/os)  // comment

#  3887 @ Ryzen 5 4500U  (cpp 1.9.5, nogil 3.9, fedora 39)  // --hash-mt=6; laptop
#  3732 @ Ryzen 5 4500U  (cpp 1.9.5, py 3.12.1, fedora 39)  // --hash-mt=6; laptop
#  3608 @ Ryzen 5 4500U  (cpp 1.9.5, py 3.11.5, fedora 38)  // --hash-mt=6; laptop
#  2726 @ Ryzen 5 4500U  (cpp 1.9.5, py 3.11.5, fedora 38)  // --hash-mt=4 (old-default)
#  2202 @ Ryzen 5 4500U  (cpp 1.9.5, py 3.11.5, docker-alpine 3.18.3) ??? alpine slow
#  2719 @ Ryzen 5 4500U  (cpp 1.9.5, py 3.11.2, docker-debian 12.1)

#  7746 @ mbp 2023 m3pro (cpp 1.9.5, py 3.11.7, macos 14.1)  // --hash-mt=6
#  6687 @ mbp 2023 m3pro (cpp 1.9.5, py 3.11.7, macos 14.1)  // --hash-mt=5 (default)
#  5544 @ Intel i5-12500 (cpp 1.9.5, py 3.11.2, debian 12.0)  // --hash-mt=12; desktop
#  5197 @ Ryzen 7 3700X  (cpp 1.9.5, py 3.9.18, freebsd 13.2)  // --hash-mt=8; 2u server
#  4551 @ mbp 2020 m1    (cpp 1.9.5, py 3.11.7, macos 14.2.1)
#  4190 @ Ryzen 7 5800X  (cpp 1.9.5, py 3.11.6, fedora 37)  // --hash-mt=8 (vbox-VM on win10-17763.4974)
#  3028 @ Ryzen 7 5800X  (cpp 1.9.5, py 3.11.6, fedora 37)  // --hash-mt=5 (vbox-VM on win10-17763.4974)
#  2629 @ Ryzen 7 5800X  (cpp 1.9.5, py 3.11.7, win10-ltsc-1809-17763.4974)  // --hash-mt=5 (default)
#  2576 @ Ryzen 7 5800X  (cpp 1.9.5, py 3.11.7, win10-ltsc-1809-17763.4974)  // --hash-mt=8 (hello??)
#  2606 @ Ryzen 7 3700X  (cpp 1.9.5, py 3.9.18, freebsd 13.2)  // --hash-mt=4 (old-default)
#  1436 @ Ryzen 5 5500U  (cpp 1.9.5, py 3.11.4, alpine 3.18.3)  // nuc
#  1065 @ Pixel 7        (cpp 1.9.5, py 3.11.5, termux 2023-09)
#   945 @ Pi 5B v1.0     (cpp 1.9.5, py 3.11.6, alpine 3.19.0)
#   548 @ Pi 4B v1.5     (cpp 1.9.5, py 3.11.6, debian 11)
#   435 @ Pi 4B v1.5     (cpp 1.9.5, py 3.11.6, alpine 3.19.0)
#   212 @ Pi Zero2W v1.0 (cpp 1.9.5, py 3.11.6, alpine 3.19.0)
#  10.0 @ Pi Zero W v1.1 (cpp 1.9.5, py 3.11.6, alpine 3.19.0)

# notes,
# podman run --rm -it --shm-size 512m --entrypoint /bin/ash localhost/copyparty-min
# podman <filehash.sh run --rm -i --shm-size 512m --entrypoint /bin/ash localhost/copyparty-min -s - /z/copyparty-sfx.py
