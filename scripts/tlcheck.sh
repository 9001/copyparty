#!/bin/bash
set -e

[ -f "$1" ] && [ -f "$2" ] && [ $# = 2 ] || {
    echo usage: ./scripts/tlcheck.sh scripts/tl.js copyparty/web/tl/nor.js 
    exit 1
}

cat "$1" "$2" | awk '
    /^\}/{fa=0;fb=0}
    /^Ls\./{if(nln++){fb=1}else{fa=1}}
    !/":/{next}
    fa{a[ia++]=$0}
    fb{b[ib++]=$0}
    END{for (i=0;i<ia;i++) printf "%s\n%s\n\n",a[i],b[i]}
' |
awk -v apos=\' -v quot=\" '
    # count special chars and prefix to line
    function c(ch) {
        m=$0;
        gsub(ch,"",m);
        t=t sprintf("%s%d ", ch, length($0)-length(m))
    }
    !$0 && t!=tp {
        print "\n\033[1;37;41m====DIFF===="
    }
    !$0 && s==sp {
        print "\n\033[1;37;44m====IDENTICAL===="
    }
    !$0 { print; next; }
    {
        sp=s; s=$0;
        tp=t; t="";
        c(quot);
        c(apos);
        c("<");
        c(">");
        c("{");
        c("}");
        c("&");
        c("\\\$");
        c("\\\\");
        print t $0;
    }
' |
sed -r $'
    s/\\\\/\033[1;37;41m\\\\\033[0m/g;
    s/\$N/\033[1;37;45m$N\033[0m/g;
    s/([{}])/\033[34m\\1\033[0m/g;
    s/"/\033[44m"\033[0m/g;
    s/\'/\033[45m\'\033[0m/g;
    s/&/\033[1;43;30m&\033[0m/g;
    s/([<>])/\033[30;47m\\1\033[0m/g
' |
sed -r 's/\t+//' |
less -R
