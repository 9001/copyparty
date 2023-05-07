#!/bin/bash
set -e

# grep '">encodings.cp' C:/Users/ed/dev/copyparty/bin/dist/xref-up2k.html | sed -r 's/.*encodings.cp//;s/<.*//' | sort -n | uniq | tr '\n' ,
# grep -i encodings -A1 build/up2k/xref-up2k.html | sed -r 's/.*(Missing|Excluded)Module.*//' | grep moduletype -B1 | grep -v moduletype

ex=(
  ftplib lzma pickle ssl tarfile bz2 zipfile tracemalloc zlib
  urllib3.util.ssl_ urllib3.contrib.pyopenssl urllib3.contrib.socks certifi idna chardet charset_normalizer
  email.contentmanager email.policy
  encodings.{zlib_codec,base64_codec,bz2_codec,charmap,hex_codec,palmos,punycode,rot_13}
);
cex=(); for a in "${ex[@]}"; do cex+=(--exclude "$a"); done
$APPDATA/python/python37/scripts/pyi-makespec --version-file up2k.rc2 -i up2k.ico -n u2c -c -F u2c.py "${cex[@]}"
