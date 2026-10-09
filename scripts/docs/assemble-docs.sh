#!/usr/bin/env sh

rm ./out -r

pandoc ../../README.md \
  --output=out/ \
  --from=gfm \
  --to=chunkedhtml \
  --standalone \
  --table-of-contents \
  --toc-depth=3 \
  --css=./docs.css \
  --chunk-template="%i.html" \
  --template ./template.html \
  --metadata title="readme" \
  --title-prefix="copyparty"

cp ./docs.css out/