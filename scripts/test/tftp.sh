#!/bin/bash
set -ex

# PYTHONPATH=.:~/dev/partftpy/ taskset -c 0 python3 -m copyparty -v srv::r -v srv/junk:junk:A --tftp 3969 

get_src=~/dev/copyparty/srv/ro/palette.flac
get_fp=ro/${get_src##*/}  # server url
get_fn=${get_fp##*/}  # just filename

put_src=~/Downloads/102.zip
put_dst=~/dev/copyparty/srv/junk/102.zip

export PATH="$PATH:$HOME/src/atftp-0.8.0"

cd /dev/shm

echo curl get 1428 v4; curl --tftp-blksize 1428 tftp://127.0.0.1:3969/$get_fp | cmp $get_src || exit 1
echo curl get 1428 v6; curl --tftp-blksize 1428 tftp://[::1]:3969/$get_fp | cmp $get_src || exit 1

echo curl put 1428 v4; rm -f $put_dst && curl --tftp-blksize 1428 -T $put_src tftp://127.0.0.1:3969/junk/ && cmp $put_src $put_dst || exit 1
echo curl put 1428 v6; rm -f $put_dst && curl --tftp-blksize 1428 -T $put_src tftp://[::1]:3969/junk/ && cmp $put_src $put_dst || exit 1

echo atftp get 1428; rm -f $get_fn && atftp --option "blksize 1428" -g -r $get_fp -l $get_fn 127.0.0.1 3969 && cmp $get_fn $get_src || exit 1

echo atftp put 1428; rm -f $put_dst && atftp --option "blksize 1428" 127.0.0.1 3969 -p -l $put_src -r junk/102.zip && cmp $put_src $put_dst || exit 1

echo tftp-hpa get; rm -f $get_fn && tftp -v -m binary 127.0.0.1 3969 -c get $get_fp && cmp $get_src $get_fn || exit 1

echo tftp-hpa put; rm -f $put_dst && tftp -v -m binary 127.0.0.1 3969 -c put $put_src junk/102.zip && cmp $put_src $put_dst || exit 1

echo curl get 512; curl tftp://127.0.0.1:3969/$get_fp | cmp $get_src || exit 1

echo curl put 512; rm -f $put_dst && curl -T $put_src tftp://127.0.0.1:3969/junk/ && cmp $put_src $put_dst || exit 1

echo atftp get 512; rm -f $get_fn && atftp -g -r $get_fp -l $get_fn 127.0.0.1 3969 && cmp $get_fn $get_src || exit 1

echo atftp put 512; rm -f $put_dst && atftp 127.0.0.1 3969 -p -l $put_src -r junk/102.zip && cmp $put_src $put_dst || exit 1

echo nice

rm -f $get_fn
