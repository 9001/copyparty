#!/bin/bash
set -e

outfile="$($(command -v realpath || command -v grealpath) "$1")"

[ -e genlic.sh ] || cd scripts
[ -e genlic.sh ]

f=../build/mit.txt
[ -e $f ] ||
	curl https://opensource.org/licenses/MIT |
	awk '/div>/{o=0}o>1;o{o++}/;COPYRIGHT HOLDER/{o=1}' |
	awk '{gsub(/<[^>]+>/,"")};1' >$f

f=../build/isc.txt
[ -e $f ] ||
	curl https://opensource.org/licenses/ISC |
	awk '/div>/{o=0}o>2;o{o++}/;OWNER/{o=1}' |
	awk '{gsub(/<[^>]+>/,"")};/./{b=0}!/./{b++}b>1{next}1' >$f

f=../build/2bsd.txt
[ -e $f ] ||
	curl https://opensource.org/licenses/BSD-2-Clause |
	awk '/div>/{o=0}o>1;o{o++}/HOLDER/{o=1}' |
	awk '{gsub(/<[^>]+>/,"")};1' >$f

f=../build/3bsd.txt
[ -e $f ] ||
	curl https://opensource.org/licenses/BSD-3-Clause |
	awk '/div>/{o=0}o>1;o{o++}/HOLDER/{o=1}' |
	awk '{gsub(/<[^>]+>/,"")};1' >$f

f=../build/ofl.txt
[ -e $f ] ||
	curl https://opensource.org/licenses/OFL-1.1 |
	awk '/PREAMBLE/{o=1}/sil\.org/{o=0}!o{next}/./{printf "%s ",$0;next}{print"\n"}' |
	awk '{gsub(/<[^>]+>/,"");gsub(/^\s+/,"");gsub(/&amp;/,"\\&")}/./{b=0}!/./{b++}b>1{next}1' >$f

(sed -r 's/^L: /License: /;s/^C: /Copyright (c) /' <../docs/lics.txt
printf '\n\n--- MIT License ---\n\n'; cat ../build/mit.txt
printf '\n\n--- ISC License ---\n\n'; cat ../build/isc.txt
printf '\n\n--- BSD 2-Clause License ---\n\n'; cat ../build/2bsd.txt
printf '\n\n--- BSD 3-Clause License ---\n\n'; cat ../build/3bsd.txt
printf '\n\n--- SIL Open Font License v1.1 ---\n\n'; cat ../build/ofl.txt
) |
while IFS= read -r x; do
	[ "${x:0:4}" = "--- " ] || {
		printf '%s\n' "$x"
		continue
	}
	n=${#x}
	p=$(( (80-n)/2 ))
	printf "%${p}s\033[07m%s\033[0m\n" "" "$x"
done > "$outfile"
