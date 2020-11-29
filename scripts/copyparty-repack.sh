#!/bin/bash
set -e

# -- download latest copyparty (source.tgz and sfx),
# -- build minimal sfx versions,
# -- create a .tar.gz bundle
#
# convenient for deploying updates to inconvenient locations
#  (and those are usually linux so bash is good inaff)
#   (but that said this even has macos support)
#
# bundle will look like:
# -rwxr-xr-x  0 ed ed  183808 Nov 19 00:43 copyparty
# -rw-r--r--  0 ed ed  491318 Nov 19 00:40 copyparty-extras/copyparty-0.5.4.tar.gz
# -rwxr-xr-x  0 ed ed   30254 Nov 17 23:58 copyparty-extras/copyparty-fuse.py
# -rwxr-xr-x  0 ed ed  481403 Nov 19 00:40 copyparty-extras/sfx-full/copyparty-sfx.sh
# -rwxr-xr-x  0 ed ed  506043 Nov 19 00:40 copyparty-extras/sfx-full/copyparty-sfx.py
# -rwxr-xr-x  0 ed ed  167699 Nov 19 00:43 copyparty-extras/sfx-lite/copyparty-sfx.sh
# -rwxr-xr-x  0 ed ed  183808 Nov 19 00:43 copyparty-extras/sfx-lite/copyparty-sfx.py


command -v gtar && tar=gtar || tar=tar
td="$(mktemp -d)"
od="$(pwd)"
cd "$td"
pwd


# debug: if cache exists, use that instead of bothering github
cache="$od/.copyparty-repack.cache"
[ -e "$cache" ] &&
	$tar -xvf "$cache" ||
{
	# get download links from github
	curl https://api.github.com/repos/9001/copyparty/releases/latest |
	(
		# prefer jq if available
		jq -r '.assets[]|select(.name|test("-sfx|tar.gz")).browser_download_url' ||

		# fallback to awk (sorry)
		awk -F\" '/"browser_download_url".*(\.tar\.gz|-sfx\.)/ {print$4}'
	) |
	tee /dev/stderr |
	tr -d '\r' | tr '\n' '\0' | xargs -0 curl -L --remote-name-all

	# debug: create cache
	#$tar -czvf "$cache" *
}


# move src into copyparty-extras/,
# move sfx into copyparty-extras/sfx-full/
mkdir -p copyparty-extras/sfx-{full,lite}
mv copyparty-sfx.* copyparty-extras/sfx-full/
mv copyparty-*.tar.gz copyparty-extras/


# unpack the source code
( cd copyparty-extras/
$tar -xvf *.tar.gz
)


# fix permissions
chmod 755 \
  copyparty-extras/sfx-full/* \
  copyparty-extras/copyparty-*/{scripts,bin}/*


# extract and repack the sfx with less features enabled
( cd copyparty-extras/sfx-full/
./copyparty-sfx.py -h
cd ../copyparty-*/
./scripts/make-sfx.sh re no-ogv no-cm
)


# put new sfx into copyparty-extras/sfx-lite/,
# fuse client into copyparty-extras/,
# copy lite-sfx.py to ./copyparty,
# delete extracted source code
( cd copyparty-extras/
mv copyparty-*/dist/* sfx-lite/
mv copyparty-*/bin/copyparty-fuse.py .
cp -pv sfx-lite/copyparty-sfx.py ../copyparty
rm -rf copyparty-{0..9}*.*.*{0..9}
)


 # and include the repacker itself too
cp -pv "$od/$0" copyparty-extras/ 


# create the bundle
fn=copyparty-$(date +%Y-%m%d-%H%M%S).tgz
$tar -czvf "$od/$fn" *
cd "$od"
rm -rf "$td"


echo
echo "done, here's your bundle:"
ls -al "$fn"
