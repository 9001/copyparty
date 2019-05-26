##
## prep debug env (vscode embedded terminal)

renice 20 -p $$


##
## testing multiple parallel uploads
## usage:  para | tee log

para() { for s in 1 2 3 4 5 6 7 8 12 16 24 32 48 64; do echo $s; for r in {1..5}; do for ((n=0;n<s;n++)); do curl -sF "f=@Various.zip" http://127.0.0.1:1234/32 2>&1 & done; wait; echo; done; done; }


##
## display average speed
## usage: avg logfile

avg() { awk 'function pr(ncsz) {if (nsmp>0) {printf "%3s %s\n", csz, sum/nsmp} csz=$1;sum=0;nsmp=0} {sub(/\r$/,"")} /^[0-9]+$/ {pr($1);next} / MiB/ {sub(/ MiB.*/,"");sub(/.* /,"");sum+=$1;nsmp++} END {pr(0)}' "$1"; }
