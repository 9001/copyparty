#!/bin/bash
echo not a script
exit 1


##
## prep debug env (vscode embedded terminal)

renice 20 -p $$


##
## cleanup after a busted shutdown

ps ax | awk '/python[23]?[ ]-m copyparty/ {print $1}' | tee /dev/stderr | xargs kill


##
## create a test payload

head -c $((2*1024*1024*1024)) /dev/zero | openssl enc -aes-256-ctr -pass pass:hunter2 -nosalt > garbage.file


##
## testing multiple parallel uploads
## usage:  para | tee log

para() { for s in 1 2 3 4 5 6 7 8 12 16 24 32 48 64; do echo $s; for r in {1..4}; do for ((n=0;n<s;n++)); do curl -sF "f=@garbage.file" http://127.0.0.1:1234/32 2>&1 & done; wait; echo; done; done; }


##
## display average speed
## usage: avg logfile

avg() { awk 'function pr(ncsz) {if (nsmp>0) {printf "%3s %s\n", csz, sum/nsmp} csz=$1;sum=0;nsmp=0} {sub(/\r$/,"")} /^[0-9]+$/ {pr($1);next} / MiB/ {sub(/ MiB.*/,"");sub(/.* /,"");sum+=$1;nsmp++} END {pr(0)}' "$1"; }


##
## vscode

# replace variable name
# (^|[^\w])oldname([^\w]|$) => $1newname$2
