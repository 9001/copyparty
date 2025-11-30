#!/bin/bash
set -e

command -v gfind >/dev/null &&
command -v gsed  >/dev/null &&
command -v gsort >/dev/null && {
    sed()  { gsed "$@"; }
}

[ -e make-sfx.sh ] || cd scripts
[ -e make-sfx.sh ] && [ -e deps-docker ] || {
    echo cd into the scripts folder first
    exit 1
}

cd ../dist

kwds='-bind -accounts -auth -auth-ord -flags -handlers -hooks -idp -urlform -exp -ls -dbd -chmod -pwhash -zm'

html() {
    for a in '' $kwds; do
        echo "html$a" >&2
        COLUMNS=140 ./copyparty-sfx.py --ansi --help$a 2>/dev/null
        printf '\n\n\n%0139d\n\n'
    done | aha -b --no-xml | sed -r '
        s/color:black/color:#222/g;
        s/color:dimgray\b/color:#606060/g;
        s/color:red\b/color:#c75b79/g;
        s/color:lime\b/color:#b8e346/g;
        s/color:yellow\b/color:#ffa402/g;
        s/color:#3333[Ff]{2}\b/color:#02a2ff/g;
        s/color:fuchsia\b/color:#f65be3/g;
        s/color:aqua\b/color:#3da698/g;
        s/color:white\b/color:#fff/g;
        s/style="filter:[^;]+/style="/g;
    ' |
    HLPTXT=CAT python3 ../scripts/help2html.py
}

txt() {
    (for a in '' $kwds; do
        echo "txt$a" >&2
        COLUMNS=9001 ./copyparty-sfx.py --help$a 2>/dev/null
        printf '\n\n\n%0255d\n\n\n'
    done;printf '\n\n\n') |
    HLPTXT=CAT ../scripts/help2txt.sh
}

html
txt
