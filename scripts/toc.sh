#!/bin/bash
set -e

for f in README.md docs/devnotes.md; do

cat $f | awk '
    function pr() {
        if (!h) {return};
        if (/^ *[*!#|]/||!s) {
            printf "%s\n",h;
            h=0;
            return
        };
        if (/.../) {
            printf "%s - %s\n",h,$0;
            h=0
        };
    };
    /^#/{s=1;pr()} /^#* *(install on android|dev env setup|just the sfx|complete release|optional gpl stuff)|`$/{s=0}
    /^#/{
        lv=length($1);
        sub(/[^ ]+ /,"");
        bab=$0;
        gsub(/ /,"-",bab);
        gsub(/\./,"",bab);
        h=sprintf("%" ((lv-1)*4+1) "s [%s](#%s)", "*",$0,bab);
        next
    }
    !h{next}
    {sub(/  .*/,"");sub(/[:;,]$/,"")}
    {pr()}
' > toc

grep -E '^#+ [^ ]+ toc$' -B1000 -A2 <$f >p1

h2="$(awk '/^#+ [^ ]+ toc$/{o=1;next} o&&/^#/{print;exit}' <$f)"

grep -F "$h2" -B2 -A999999 <$f >p2

(cat p1; grep -F "${h2#* }" -A1000 <toc; cat p2) >$f

rm p1 p2 toc

done
