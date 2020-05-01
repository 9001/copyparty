#!/bin/ash
set -e

orig_css="$(find /z/fontawesome-fre* -name fontawesome.css | head -n 1)"
orig_woff="$(find /z/fontawesome-fre* -name fa-solid-900.woff | head -n 1)"

# first grab the copyright meme
awk '1; / *\*\// {exit}' <"$orig_css" >/z/dist/mini-fa.css

# then add the static part of our css template
awk '/^:add/ {exit} 1' </z/mini-fa.css >>/z/dist/mini-fa.css

# then take the list of icons to include
awk 'o; /^:add/ {o=1}' </z/mini-fa.css |
while IFS= read -r g; do
    # and grab them from the upstream css
    awk 'o{gsub(/[ ;]+/,"");print;exit} /^\.fa-'$g':before/ {o=1;printf "%s",$0}' <"$orig_css"
done >>/z/dist/mini-fa.css

# expecting this input btw:
# .fa-python:before {
#  content: "\f3e2"; }

# get the codepoints (should produce lines like "f3e2")
awk '/:before .content:"\\/ {sub(/[^"]+"./,""); sub(/".*/,""); print}' </z/dist/mini-fa.css >/z/icon.list

# and finally create a woff with just our icons
pyftsubset "$orig_woff" --unicodes-file=/z/icon.list --no-ignore-missing-unicodes --flavor=woff --with-zopfli --output-file=/z/dist/no-pk/mini-fa.woff --verbose
