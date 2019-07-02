#!/bin/bash
echo not a script
exit 1


##
## create a test payload

head -c $((2*1024*1024*1024)) /dev/zero | openssl enc -aes-256-ctr -pass pass:hunter2 -nosalt > garbage.file


##
## testing multiple parallel uploads
## usage:  para | tee log

para() { for s in 1 2 3 4 5 6 7 8 12 16 24 32 48 64; do echo $s; for r in {1..4}; do for ((n=0;n<s;n++)); do curl -sF "act=bput" -F "f=@garbage.file" http://127.0.0.1:1234/ 2>&1 & done; wait; echo; done; done; }


##
## display average speed
## usage: avg logfile

avg() { awk 'function pr(ncsz) {if (nsmp>0) {printf "%3s %s\n", csz, sum/nsmp} csz=$1;sum=0;nsmp=0} {sub(/\r$/,"")} /^[0-9]+$/ {pr($1);next} / MiB/ {sub(/ MiB.*/,"");sub(/.* /,"");sum+=$1;nsmp++} END {pr(0)}' "$1"; }


##
## bad filenames

dirs=("$HOME/vfs/ほげ" "$HOME/vfs/ほげ/ぴよ" "$HOME/vfs/$(printf \\xed\\x91)" "$HOME/vfs/$(printf \\xed\\x91/\\xed\\x92)")
mkdir -p "${dirs[@]}"
for dir in "${dirs[@]}"; do for fn in ふが "$(printf \\xed\\x93)" 'qwe,rty;asd fgh+jkl%zxc&vbn <qwe>"rty'"'"'uio&asd&nbsp;fgh'; do echo "$dir" > "$dir/$fn.html"; done; done


##
## test compression

wget -S --header='Accept-Encoding: gzip' -U 'MSIE 6.0; SV1' http://127.0.0.1:1234/.cpr/deps/ogv.js -O- | md5sum; p=~ed/dev/copyparty/copyparty/web/deps/ogv.js.gz; md5sum $p; gzip -d < $p | md5sum


##
## sha512(file) | base64
## usage:  shab64 chunksize_mb filepath

shab64() { sp=$1; f="$2"; v=0; sz=$(stat -c%s "$f"); while true; do w=$((v+sp*1024*1024)); printf $(tail -c +$((v+1)) "$f" | head -c $((w-v)) | sha512sum | cut -c-64 | sed -r 's/ .*//;s/(..)/\\x\1/g') | base64 -w0 | cut -c-43 | tr '+/' '-_'; v=$w; [ $v -lt $sz ] || break; done; }


##
## vscode

# replace variable name
# (^|[^\w])oldname([^\w]|$) => $1newname$2

# monitor linter progress
htop -d 2 -p $(ps ax | awk '/electron[ ]/ {printf "%s%s", v, $1;v=","}')

# prep debug env (vscode embedded terminal)
renice 20 -p $$

# cleanup after a busted shutdown
ps ax | awk '/python[23]? -m copyparty/ {print $1}' | tee /dev/stderr | xargs kill
