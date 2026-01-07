# place new key cl_rcm below cl_hcancel, and cdt_ren below cdt_hsort, and so on
# (existing keys (ut_ow) are NOT updated; todo)
gawk <tl.txt '/^var /{lang=$2;k="xxxx"} {p=k} /"cl_rcm"/{p="cl_hcancel"} /"cdt_ren"/{p="cdt_hsort"} /"rc_opn"/{p="ur_sm"} /"/{k=$1;gsub(/[" ]/,"",k);sub(/:.*/,"",k);print lang " " p " " $0}' | while read lang after ln; do gawk -v p="\"$after\":" -v v="$ln" <$lang.js '1;$0~p{print "\t" v}' >t; mv t $lang.js; done 
