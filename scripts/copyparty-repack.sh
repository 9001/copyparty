#!/bin/bash
repacker=1
set -e

# -- download latest copyparty (source.tgz and sfx),
# -- build minimal sfx versions,
# -- create a .tar.gz bundle
#
# convenient for deploying updates to inconvenient locations
#  (and those are usually linux so bash is good inaff)
#   (but that said this even has macos support)
#
# output summary (filesizes and contents):
#
# 535672  copyparty-extras/sfx-full/copyparty-sfx.sh
# 550760  copyparty-extras/sfx-full/copyparty-sfx.py
#           `- original unmodified sfx from github
#
# 572923  copyparty-extras/sfx-full/copyparty-sfx-gz.py
#           `- unmodified but recompressed from bzip2 to gzip
#
# 341792  copyparty-extras/sfx-ent/copyparty-sfx.sh
# 353975  copyparty-extras/sfx-ent/copyparty-sfx.py
# 376934  copyparty-extras/sfx-ent/copyparty-sfx-gz.py
#           `- removed iOS ogg/opus/vorbis audio decoder,
#              removed the audio tray mouse cursor,
#              "enterprise edition"
#
# 259288  copyparty-extras/sfx-lite/copyparty-sfx.sh
# 270004  copyparty-extras/sfx-lite/copyparty-sfx.py
# 293159  copyparty-extras/sfx-lite/copyparty-sfx-gz.py
#           `- also removed the codemirror markdown editor,
#              only essential features remaining
#
# 646297  copyparty-extras/copyparty-1.0.14.tar.gz
#   4823  copyparty-extras/copyparty-repack.sh
#           `- source files from github
#
#  23663  copyparty-extras/up2k.py
#           `- standalone utility to upload or search for files
#
#  32280  copyparty-extras/copyparty-fuse.py
#           `- standalone to mount a URL as a local read-only filesystem
#
# 270004  copyparty
#           `- minimal binary, same as sfx-lite/copyparty-sfx.py


command -v gnutar && tar() { gnutar "$@"; }
command -v gtar && tar() { gtar "$@"; }
command -v gsed && sed() { gsed "$@"; }
td="$(mktemp -d)"
od="$(pwd)"
cd "$td"
pwd


dl_text() {
	command -v curl >/dev/null && exec curl "$@"
	exec wget -O- "$@"
}
dl_files() {
	command -v curl >/dev/null && exec curl -L --remote-name-all "$@"
	exec wget "$@"
}
export -f dl_files


# if cache exists, use that instead of bothering github
cache="$od/.copyparty-repack.cache"
[ -e "$cache" ] &&
	tar -xf "$cache" ||
{
	# get download links from github
	dl_text https://api.github.com/repos/9001/copyparty/releases/latest |
	(
		# prefer jq if available
		jq -r '.assets[]|select(.name|test("-sfx|tar.gz")).browser_download_url' ||

		# fallback to awk (sorry)
		awk -F\" '/"browser_download_url".*(\.tar\.gz|-sfx\.)/ {print$4}'
	) |
	grep -E '(sfx\.(sh|py)|tar\.gz)$' |
	tee /dev/stderr |
	tr -d '\r' | tr '\n' '\0' |
	xargs -0 bash -c 'dl_files "$@"' _

	tar -czf "$cache" *
}


# move src into copyparty-extras/,
# move sfx into copyparty-extras/sfx-full/
mkdir -p copyparty-extras/sfx-{full,ent,lite}
mv copyparty-sfx.* copyparty-extras/sfx-full/
mv copyparty-*.tar.gz copyparty-extras/


# unpack the source code
( cd copyparty-extras/
tar -xf *.tar.gz
)


# use repacker from release if that is newer
p_other=copyparty-extras/copyparty-*/scripts/copyparty-repack.sh
other=$(awk -F= 'BEGIN{v=-1} NR<10&&/^repacker=/{v=$NF} END{print v}' <$p_other) 
[ $repacker -lt $other ] &&
  cat $p_other >"$od/$0" && cd "$od" && rm -rf "$td" && exec "$0" "$@"


# now drop the cache
rm -f "$cache"


# fix permissions
chmod 755 \
  copyparty-extras/sfx-full/* \
  copyparty-extras/copyparty-*/{scripts,bin}/*


# extract the sfx
( cd copyparty-extras/sfx-full/
./copyparty-sfx.py -h
)


repack() {

	# do the repack
	(cd copyparty-extras/copyparty-*/
	./scripts/make-sfx.sh $2
	)

	# put new sfx into copyparty-extras/$name/,
	( cd copyparty-extras/
	mv copyparty-*/dist/* $1/
	)
}

repack sfx-full "re gz no-sh"
repack sfx-ent  "re no-dd no-ogv"
repack sfx-ent  "re no-dd no-ogv gz no-sh"
repack sfx-lite "re no-dd no-ogv no-cm"
repack sfx-lite "re no-dd no-ogv no-cm gz no-sh"


# move fuse and up2k clients into copyparty-extras/,
# copy lite-sfx.py to ./copyparty,
# delete extracted source code
( cd copyparty-extras/
mv copyparty-*/bin/up2k.py .
mv copyparty-*/bin/copyparty-fuse.py .
cp -pv sfx-lite/copyparty-sfx.py ../copyparty
rm -rf copyparty-{0..9}*.*.*{0..9}
)


# and include the repacker itself too
cp -av "$od/$0" copyparty-extras/ ||
cp -av "$0" copyparty-extras/ ||
true


# create the bundle
printf '\n\n'
fn=copyparty-$(date +%Y-%m%d-%H%M%S).tgz
tar -czvf "$od/$fn" *
cd "$od"
rm -rf "$td"


echo
echo "done, here's your bundle:"
ls -al "$fn"
