FROM    alpine:3.11
WORKDIR /z
ENV     ver_asmcrypto=2821dd1dedd1196c378f5854037dda5c869313f3 \
        ver_markdownit=10.0.0 \
        ver_showdown=1.9.1 \
        ver_marked=1.0.0 \
        ver_ogvjs=1.6.1 \
        ver_mde=2.10.1 \
        ver_codemirror=5.53.2 \
        ver_fontawesome=5.13.0 \
        ver_zopfli=1.0.3


# download;
# the scp url is latin from https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap
RUN     mkdir -p /z/dist/no-pk \
        && wget https://fonts.gstatic.com/s/sourcecodepro/v11/HI_SiYsKILxRpg3hIP6sJ7fM7PqlPevW.woff2 -O scp.woff2 \
        && apk add cmake make g++ git bash npm patch wget tar pigz brotli gzip unzip python3 python3-dev brotli py3-brotli \
        && wget https://github.com/brion/ogv.js/releases/download/$ver_ogvjs/ogvjs-$ver_ogvjs.zip -O ogvjs.zip \
        && wget https://github.com/asmcrypto/asmcrypto.js/archive/$ver_asmcrypto.tar.gz -O asmcrypto.tgz \
        && wget https://github.com/markedjs/marked/archive/v$ver_marked.tar.gz -O marked.tgz \
        && wget https://github.com/Ionaru/easy-markdown-editor/archive/$ver_mde.tar.gz -O mde.tgz \
        && wget https://github.com/codemirror/CodeMirror/archive/$ver_codemirror.tar.gz -O codemirror.tgz \
        && wget https://github.com/FortAwesome/Font-Awesome/releases/download/$ver_fontawesome/fontawesome-free-$ver_fontawesome-web.zip -O fontawesome.zip \
        && wget https://github.com/google/zopfli/archive/zopfli-$ver_zopfli.tar.gz -O zopfli.tgz \
        && unzip ogvjs.zip \
        && (tar -xf asmcrypto.tgz \
            && cd asmcrypto.js-$ver_asmcrypto \
            && npm install ) \
        && (tar -xf marked.tgz \
            && cd marked-$ver_marked \
            && npm install \
            && npm i grunt uglify-js -g ) \
        && (tar -xf codemirror.tgz \
            && cd CodeMirror-$ver_codemirror \
            && npm install ) \
        && (tar -xf mde.tgz \
            && cd easy-markdown-editor* \
            && npm install \
            && npm i gulp-cli -g ) \
        && unzip fontawesome.zip \
        && tar -xf zopfli.tgz


# uncomment if you wanna test the abandoned markdown converters
#ENV     build_abandoned=1


RUN     [ $build_abandoned ] || exit 0; \
        git clone --depth 1 --branch $ver_showdown https://github.com/showdownjs/showdown/ \
        && wget https://github.com/markdown-it/markdown-it/archive/$ver_markdownit.tar.gz -O markdownit.tgz \
        && (cd showdown \
            && npm install \
            && npm i grunt -g ) \
        && (tar -xf markdownit.tgz \
            && cd markdown-it-$ver_markdownit \
            && npm install )


# build fonttools (which needs zopfli)
RUN     tar -xf zopfli.tgz \
        && cd zopfli* \
        && cmake \
            -DCMAKE_INSTALL_PREFIX=/usr \
            -DZOPFLI_BUILD_SHARED=ON \
            -B build \
            -S . \
        && make -C build \
        && make -C build install \
        && python3 -m pip install fonttools zopfli


# build asmcrypto
RUN     cd asmcrypto.js-$ver_asmcrypto \
        && echo "export { Sha512 } from './hash/sha512/sha512';" > src/entry-export_all.ts \
        && node -r esm build.js \
        && mv asmcrypto.all.es5.js /z/dist/sha512.js


# build ogvjs
RUN     cd ogvjs-$ver_ogvjs \
        && cp -pv \
            ogv.js \
            ogv-worker-audio.js \
            ogv-demuxer-ogg.js \
            ogv-demuxer-ogg-wasm.js \
            ogv-demuxer-ogg-wasm.wasm \
            ogv-demuxer-webm.js \
            ogv-demuxer-webm-wasm.js \
            ogv-demuxer-webm-wasm.wasm \
            ogv-decoder-audio-opus.js \
            ogv-decoder-audio-opus-wasm.js \
            ogv-decoder-audio-opus-wasm.wasm \
            ogv-decoder-audio-vorbis.js \
            ogv-decoder-audio-vorbis-wasm.js \
            ogv-decoder-audio-vorbis-wasm.wasm \
            dynamicaudio.swf \
            /z/dist


# build marked
RUN     wget https://github.com/markedjs/marked/commit/5c166d4164791f643693478e4ac094d63d6e0c9a.patch -O marked-git-1.patch \
        && wget https://patch-diff.githubusercontent.com/raw/markedjs/marked/pull/1652.patch -O marked-git-2.patch

COPY    marked.patch /z/
COPY    marked-ln.patch /z/
RUN     cd marked-$ver_marked \
        && patch -p1 < /z/marked-git-1.patch \
        && patch -p1 < /z/marked-git-2.patch \
        && patch -p1 < /z/marked-ln.patch \
        && patch -p1 < /z/marked.patch \
        && npm run build \
        && cp -pv marked.min.js /z/dist/marked.js \
        && cp -pv lib/marked.js /z/dist/marked.full.js \
        && mkdir -p /z/nodepkgs \
        && ln -s $(pwd) /z/nodepkgs/marked
#        && npm run test \


# build codemirror
COPY    codemirror.patch /z/
RUN     cd CodeMirror-$ver_codemirror \
        && patch -p1 < /z/codemirror.patch \
        && sed -ri '/^var urlRE = /d' mode/gfm/gfm.js \
        && npm run build \
        && ln -s $(pwd) /z/nodepkgs/codemirror


# build easymde
COPY    easymde.patch /z/
RUN     cd easy-markdown-editor-$ver_mde \
        && patch -p1 < /z/easymde.patch \
        && sed -ri 's`https://registry.npmjs.org/marked/-/marked-0.8.2.tgz`file:/z/nodepkgs/marked`' package-lock.json \
        && sed -ri 's`("marked": ")[^"]+`\1file:/z/nodepkgs/marked`' ./package.json \
        && sed -ri 's`("codemirror": ")[^"]+`\1file:/z/nodepkgs/codemirror`' ./package.json \
        && npm install

COPY    easymde-ln.patch /z/
RUN     cd easy-markdown-editor-$ver_mde \
        && patch -p1 < /z/easymde-ln.patch \
        && gulp \
        && cp -pv dist/easymde.min.css /z/dist/easymde.css \
        && cp -pv dist/easymde.min.js /z/dist/easymde.js \
        && sed -ri '/pipe.terser/d; /cleanCSS/d' gulpfile.js \
        && gulp \
        && cp -pv dist/easymde.min.css /z/dist/easymde.full.css \
        && cp -pv dist/easymde.min.js /z/dist/easymde.full.js


# build showdown (abandoned; disabled by default)
COPY    showdown.patch /z/
RUN     [ $build_abandoned ] || exit 0; \
        cd showdown \
        && rm -rf bin dist \
#       # remove ellipsis plugin \
        && rm \
            src/subParsers/ellipsis.js \
            test/cases/ellipsis* \
#       # remove html-to-md converter \
        && rm \
            test/node/testsuite.makemd.js \
            test/node/showdown.Converter.makeMarkdown.js \
#       # remove emojis \
        && rm src/subParsers/emoji.js \
        && awk '/^showdown.helper.emojis/ {o=1} !o; /^\}/ {o=0}' \
            >f <src/helpers.js \
        && mv f src/helpers.js \
        && rm -rf test/features/emojis \
#       # remove ghmentions \
        && rm test/features/ghMentions.* \
#       # remove option descriptions \
        && sed -ri '/descri(ption|be): /d' src/options.js \
        && patch -p1 < /z/showdown.patch

RUN     [ $build_abandoned ] || exit 0; \
        cd showdown \
        && grunt build \
        && sed -ri '/sourceMappingURL=showdown.min.js.map/d' dist/showdown.min.js \
        && mv dist/showdown.min.js /z/dist/showdown.js \
        && ls -al /z/dist/showdown.js


# build markdownit (abandoned; disabled by default)
COPY    markdown-it.patch /z/
RUN     [ $build_abandoned ] || exit 0; \
        cd markdown-it-$ver_markdownit \
        && patch -p1 < /z/markdown-it.patch \
        && make browserify \
        && cp -pv dist/markdown-it.min.js /z/dist/markdown-it.js \
        && cp -pv dist/markdown-it.js /z/dist/markdown-it-full.js


# build fontawesome and scp
COPY    mini-fa.sh /z
COPY    mini-fa.css /z
RUN     /bin/ash /z/mini-fa.sh


# compress
COPY    zopfli.makefile /z/dist/Makefile
RUN     cd /z/dist \
        && make -j$(nproc) \
        && rm Makefile \
        && mv no-pk/* . \
        && rmdir no-pk


# d=/home/ed/dev/copyparty/scripts/deps-docker/; tar -cf ../x . && ssh root@$bip "cd $d && tar -xv >&2 && make >&2 && tar -cC ../../copyparty/web deps" <../x | (cd ../../copyparty/web/; cat > the.tgz; tar -xvf the.tgz)
# gzip -dkf ../dev/copyparty/copyparty/web/deps/deps/marked.full.js.gz && diff -NarU2 ../dev/copyparty/copyparty/web/deps/{,deps/}marked.full.js
