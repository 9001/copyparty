#!/bin/bash
echo not a script
exit 1


##
## delete all partial uploads
##  (supports linux/macos, probably windows+msys2)

gzip -d < .hist/up2k.snap | jq -r '.[].tnam' | while IFS= read -r f; do rm -f -- "$f"; done
gzip -d < .hist/up2k.snap | jq -r '.[].name' | while IFS= read -r f; do wc -c -- "$f" | grep -qiE '^[^0-9a-z]*0' && rm -f -- "$f"; done


##
## detect partial uploads based on file contents
##  (in case of context loss or old copyparties)

echo; find -type f | while IFS= read -r x; do printf '\033[A\033[36m%s\033[K\033[0m\n' "$x"; tail -c$((1024*1024)) <"$x" | xxd -a | awk 'NR==1&&/^[0: ]+.{16}$/{next} NR==2&&/^\*$/{next} NR==3&&/^[0f]+: [0 ]+65 +.{16}$/{next} {e=1} END {exit e}' || continue; printf '\033[A\033[31msus:\033[33m %s \033[0m\n\n' "$x"; done


##
## create a test payload

head -c $((2*1024*1024*1024)) /dev/zero | openssl enc -aes-256-ctr -pass pass:hunter2 -nosalt > garbage.file


##
## testing multiple parallel uploads
## usage:  para | tee log

para() { for s in 1 2 3 4 5 6 7 8 12 16 24 32 48 64; do echo $s; for r in {1..4}; do for ((n=0;n<s;n++)); do curl -sF "act=bput" -F "f=@garbage.file" http://127.0.0.1:3923/ 2>&1 & done; wait; echo; done; done; }


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
## upload mojibake

fn=$(printf '\xba\xdc\xab.cab')
echo asdf > "$fn"
curl --cookie cppwd=wark -sF "act=bput" -F "f=@$fn" http://127.0.0.1:3923/moji/%ED%91/


##
## test compression

wget -S --header='Accept-Encoding: gzip' -U 'MSIE 6.0; SV1' http://127.0.0.1:3923/.cpr/deps/ogv.js -O- | md5sum; p=~ed/dev/copyparty/copyparty/web/deps/ogv.js.gz; md5sum $p; gzip -d < $p | md5sum


##
## sha512(file) | base64
## usage:  shab64 chunksize_mb filepath

shab64() { sp=$1; f="$2"; v=0; sz=$(stat -c%s "$f"); while true; do w=$((v+sp*1024*1024)); printf $(tail -c +$((v+1)) "$f" | head -c $((w-v)) | sha512sum | cut -c-64 | sed -r 's/ .*//;s/(..)/\\x\1/g') | base64 -w0 | cut -c-43 | tr '+/' '-_'; v=$w; [ $v -lt $sz ] || break; done; }


##
## poll url for performance issues

command -v gdate && date() { gdate "$@"; }; while true; do t=$(date +%s.%N); (time wget http://127.0.0.1:3923/?ls -qO- | jq -C '.files[]|{sz:.sz,ta:.tags.artist,tb:.tags.".bpm"}|del(.[]|select(.==null))' | awk -F\" '/"/{t[$2]++} END {for (k in t){v=t[k];p=sprintf("%" (v+1) "s",v);gsub(/ /,"#",p);printf "\033[36m%s\033[33m%s   ",k,p}}') 2>&1 | awk -v ts=$t 'NR==1{t1=$0} NR==2{sub(/.*0m/,"");sub(/s$/,"");t2=$0;c=2; if(t2>0.3){c=3} if(t2>0.8){c=1} } END{sub(/[0-9]{6}$/,"",ts);printf "%s   \033[3%dm%s   %s\033[0m\n",ts,c,t2,t1}'; sleep 0.1 || break; done


##
## js oneliners

# get all up2k search result URLs
var t=[]; var b=document.location.href.split('#')[0].slice(0, -1); document.querySelectorAll('#u2tab .prog a').forEach((x) => {t.push(b+encodeURI(x.getAttribute("href")))}); console.log(t.join("\n"));


##
## bash oneliners

# get the size and video-id of all youtube vids in folder, assuming filename ends with -id.ext, and create a copyparty search query
find -maxdepth 1 -printf '%s %p\n' | sort -n | awk '!/-([0-9a-zA-Z_-]{11})\.(mkv|mp4|webm)$/{next} {sub(/\.[^\.]+$/,"");n=length($0);v=substr($0,n-10);print $1, v}' | tee /dev/stderr | awk 'BEGIN {p="("} {printf("%s name like *-%s.* ",p,$2);p="or"} END {print ")\n"}' | cat >&2


##
## sqlite3 stuff

# find dupe metadata keys
sqlite3 up2k.db 'select mt1.w, mt1.k, mt1.v, mt2.v from mt mt1 inner join mt mt2 on mt1.w = mt2.w where mt1.k = mt2.k and mt1.rowid != mt2.rowid'

# partial reindex by deleting all tags for a list of files
time sqlite3 up2k.db 'select mt1.w from mt mt1 inner join mt mt2 on mt1.w = mt2.w where mt1.k = +mt2.k and mt1.rowid != mt2.rowid'  > warks
cat warks | while IFS= read -r x; do sqlite3 up2k.db "delete from mt where w = '$x'"; done

# dump all dbs
find -iname up2k.db | while IFS= read -r x; do sqlite3 "$x" 'select substr(w,1,12), rd, fn from up' | sed -r 's/\|/ \| /g' | while IFS= read -r y; do printf '%s | %s\n' "$x" "$y"; done; done


##
## media

# split track into test files
e=6; s=10; d=~/dev/copyparty/srv/aus; n=1; p=0; e=$((e*60)); rm -rf $d; mkdir $d; while true; do ffmpeg -hide_banner -ss $p -i 'nervous_testpilot - office.mp3' -c copy -t $s $d/$(printf %04d $n).mp3; n=$((n+1)); p=$((p+s)); [ $p -gt $e ] && break; done

-v srv/aus:aus:r:ce2dsa:ce2ts:cmtp=fgsfds=bin/mtag/sleep.py
sqlite3 .hist/up2k.db 'select * from mt where k="fgsfds" or k="t:mtp"' | tee /dev/stderr | wc -l


##
## vscode

# replace variable name
# (^|[^\w])oldname([^\w]|$) => $1newname$2

# monitor linter progress
htop -d 2 -p $(ps ax | awk '/electron[ ]/ {printf "%s%s", v, $1;v=","}')

# prep debug env (vscode embedded terminal)
renice 20 -p $$

# cleanup after a busted shutdown
ps ax | awk '/python[23]? -m copyparty|python[ ]-c from multiproc/ {print $1}' | tee /dev/stderr | xargs kill

# last line of each function in a file
cat copyparty/httpcli.py | awk '/^[^a-zA-Z0-9]+def / {printf "%s\n%s\n\n", f, pl; f=$2} /[a-zA-Z0-9]/ {pl=$0}'


##
## meta

# create a folder with symlinks to big files
for d in /usr /var; do find $d -type f -size +30M 2>/dev/null; done | while IFS= read -r x; do ln -s "$x" big/; done

# py2 on osx
brew install python@2
pip install virtualenv

# readme toc
cat README.md | awk '!/^#/{next} {lv=length($1);sub(/[^ ]+ /,"");bab=$0;gsub(/ /,"-",bab)} {printf "%" ((lv-1)*4+1) "s [%s](#%s)\n", "*",$0,bab}'

# fix firefox phantom breakpoints,
# suggestions from bugtracker, doesnt work (debugger is not attachable)
devtools settings >> advanced >> enable browser chrome debugging + enable remote debugging
burger > developer >> browser toolbox  (ctrl-alt-shift-i)
iframe btn topright >> chrome://devtools/content/debugger/index.html
dbg.asyncStore.pendingBreakpoints = {}

# fix firefox phantom breakpoints
about:config >> devtools.debugger.prefs-schema-version = -1

# determine server version
git reset --hard origin/HEAD && git log --format=format:"%H %ai %d" --decorate=full > /dev/shm/revs && cat /dev/shm/revs | while read -r rev extra; do (git reset --hard $rev >/dev/null 2>/dev/null && dsz=$(cat copyparty/web/{util,browser,up2k}.js 2>/dev/null | diff -wNarU0 - <(cat /mnt/Users/ed/Downloads/ref/{util,browser,up2k}.js) | wc -c) && printf '%s %6s %s\n' "$rev" $dsz "$extra") </dev/null; done                


##
## http 206

# az = abcdefghijklmnopqrstuvwxyz

printf '%s\r\n' 'GET /az HTTP/1.1' 'Host: ocv.me' 'Range: bytes=5-10' '' | ncat ocv.me 80 
# Content-Range: bytes 5-10/26
# Content-Length: 6
# fghijk

Range: bytes=0-1    "ab" Content-Range: bytes 0-1/26
Range: bytes=24-24  "y"  Content-Range: bytes 24-24/26
Range: bytes=24-25  "yz" Content-Range: bytes 24-25/26
Range: bytes=24-    "yz" Content-Range: bytes 24-25/26
Range: bytes=25-29  "z"  Content-Range: bytes 25-25/26
Range: bytes=26-         Content-Range: bytes */26
  HTTP/1.1 416 Requested Range Not Satisfiable


##
## md perf

var tsh = [];
function convert_markdown(md_text, dest_dom) {
    tsh.push(Date.now());
    while (tsh.length > 10)
        tsh.shift();
    if (tsh.length > 1) {
        var end = tsh.slice(-2);
        console.log("render", end.pop() - end.pop(), (tsh[tsh.length - 1] - tsh[0]) / (tsh.length - 1));
    }


##
## tmpfiles.d meme

mk() { rm -rf /tmp/foo; sudo -u ed bash -c 'mkdir /tmp/foo; echo hi > /tmp/foo/bar'; }
mk && t0="$(date)" && while true; do date -s "$(date '+ 1 hour')"; systemd-tmpfiles --clean; ls -1 /tmp | grep foo || break; done; echo "$t0"
mk && sudo -u ed flock /tmp/foo sleep 40 & sleep 1; ps aux | grep -E 'sleep 40$' && t0="$(date)" && for n in {1..40}; do date -s "$(date '+ 1 day')"; systemd-tmpfiles --clean; ls -1 /tmp | grep foo || break; done; echo "$t0"
mk && t0="$(date)" && for n in {1..40}; do date -s "$(date '+ 1 day')"; systemd-tmpfiles --clean; ls -1 /tmp | grep foo || break; tar -cf/dev/null /tmp/foo; done; echo "$t0"
