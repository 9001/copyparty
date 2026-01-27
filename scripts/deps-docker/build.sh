#!/bin/bash
# shellcheck disable=SC2016

set -o errexit
set -o pipefail

ver_hashwasm=4.12.0
ver_marked=4.3.0
ver_dompf=3.3.1
ver_mde=2.18.0
ver_codemirror=5.65.18
ver_fontawesome=5.13.0
ver_prism=1.30.0

# versioncheck:
# https://github.com/markedjs/marked/releases
# https://github.com/Ionaru/easy-markdown-editor/tags  # ignore 2.20.0
# https://github.com/codemirror/codemirror5/releases
# https://github.com/cure53/DOMPurify/releases
# https://github.com/Daninet/hash-wasm/releases

explode() {
  return 1
}

build() {
  case $1 in
    busy-mp3)
      /z/busy-mp3.sh
      mv -v /dev/shm/busy.mp3.gz /z/dist
    ;;
    hash-wasm)
      cd hash-wasm/dist
      mv sha512.umd.min.js /z/dist/sha512.hw.js
    ;;
    marked)
      cd marked-$ver_marked
      patch -p1 < /z/marked-ln.patch
      patch -p1 < /z/marked.patch
      npm run build
      cp -pv marked.min.js /z/dist/marked.js
      mkdir -p /z/nodepkgs
      ln -s "$(pwd)" /z/nodepkgs/marked
      # npm run test
    ;;
    codemirror)
        cd codemirror5-$ver_codemirror
        patch -p1 < /z/codemirror.patch
        sed -ri '/^var urlRE = /d' mode/gfm/gfm.js
        npm run build
        ln -s "$(pwd)" /z/nodepkgs/codemirror
    ;;
    easymde)
        cd easy-markdown-editor-$ver_mde
        patch -p1 < /z/easymde.patch
        sed -ri 's`https://registry.npmjs.org/marked/-/marked-[0-9\.]+.tgz`file:/z/nodepkgs/marked`' package-lock.json
        sed -ri 's`https://registry.npmjs.org/codemirror/-/codemirror-[0-9\.]+.tgz`file:/z/nodepkgs/codemirror`' package-lock.json
        sed -ri 's`("marked": ")[^"]+`\1file:/z/nodepkgs/marked`' ./package.json
        sed -ri 's`("codemirror": ")[^"]+`\1file:/z/nodepkgs/codemirror`' ./package.json
        sed -ri 's`^var marked = require\(.marked.\).marked;$`var marked = window.marked;`' src/js/easymde.js
        npm install
        patch -p1 < /z/easymde-ln.patch
        gulp
        cp -pv dist/easymde.min.css /z/dist/easymde.css
        cp -pv dist/easymde.min.js /z/dist/easymde.js
    ;;
    dompurify)
      (echo; cat DOMPurify-$ver_dompf/dist/purify.min.js) >> /z/dist/marked.js
    ;;
    fonts)
      # build fontawesome and scp
      /bin/ash /z/mini-fa.sh
    ;;
    prismjs)
      ./genprism.sh $ver_prism
    ;;
    *)
      echo "idk how to build that"
      explode
    ;;
  esac
}

case $1 in
  download)
    # the scp url is regular latin from https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap
    echo "download things"
    wget https://fonts.gstatic.com/s/sourcecodepro/v11/HI_SiYsKILxRpg3hIP6sJ7fM7PqlPevW.woff2 -O scp.woff2
    wget https://github.com/markedjs/marked/archive/v$ver_marked.tar.gz -O marked.tgz
    wget https://github.com/Ionaru/easy-markdown-editor/archive/$ver_mde.tar.gz -O mde.tgz
    wget https://github.com/codemirror/codemirror5/archive/$ver_codemirror.tar.gz -O codemirror.tgz
    wget https://github.com/cure53/DOMPurify/archive/refs/tags/$ver_dompf.tar.gz -O dompurify.tgz
    wget https://github.com/FortAwesome/Font-Awesome/releases/download/$ver_fontawesome/fontawesome-free-$ver_fontawesome-web.zip -O fontawesome.zip
    wget https://github.com/Daninet/hash-wasm/releases/download/v$ver_hashwasm/hash-wasm@$ver_hashwasm.zip -O hash-wasm.zip
    wget https://github.com/PrismJS/prism/archive/refs/tags/v$ver_prism.tar.gz -O prism.tgz
    wget https://files.pythonhosted.org/packages/04/0b/4506cb2e831cea4b0214d3625430e921faaa05a7fb520458c75a2dbd2152/fusepy-3.0.1.tar.gz -O fusepy.tgz
    ;;
  unpack)
    (mkdir hash-wasm \
      && cd hash-wasm \
      && unzip ../hash-wasm.zip)
    (tar --no-same-owner -xf marked.tgz \
      && cd marked-$ver_marked \
      && npm install \
      && npm i grunt uglify-js -g )
    (tar --no-same-owner -xf codemirror.tgz \
      && cd codemirror5-$ver_codemirror \
      && npm install )
    (tar --no-same-owner -xf mde.tgz \
      && cd easy-markdown-editor* \
      && npm install \
      && npm i gulp-cli -g )
    tar --no-same-owner -xf dompurify.tgz
    tar --no-same-owner -xf prism.tgz
    tar --no-same-owner -xf fusepy.tgz
    unzip fontawesome.zip
    ;;
  build)
    build "$2"
  ;;
  *)
    echo "idk"
    explode
  ;;
esac
