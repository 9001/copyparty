FROM    alpine:3.16
WORKDIR /z
ENV     ver_asmcrypto=5b994303a9d3e27e0915f72a10b6c2c51535a4dc \
        ver_hashwasm=4.9.0 \
        ver_marked=4.0.17 \
        ver_mde=2.16.1 \
        ver_codemirror=5.65.6 \
        ver_fontawesome=5.13.0 \
        ver_zopfli=1.0.3


# download;
# the scp url is regular latin from https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap
RUN     mkdir -p /z/dist/no-pk \
        && wget https://fonts.gstatic.com/s/sourcecodepro/v11/HI_SiYsKILxRpg3hIP6sJ7fM7PqlPevW.woff2 -O scp.woff2 \
        && apk add cmake make g++ git bash npm patch wget tar pigz brotli gzip unzip python3 python3-dev brotli py3-brotli \
        && wget https://github.com/openpgpjs/asmcrypto.js/archive/$ver_asmcrypto.tar.gz -O asmcrypto.tgz \
        && wget https://github.com/markedjs/marked/archive/v$ver_marked.tar.gz -O marked.tgz \
        && wget https://github.com/Ionaru/easy-markdown-editor/archive/$ver_mde.tar.gz -O mde.tgz \
        && wget https://github.com/codemirror/CodeMirror/archive/$ver_codemirror.tar.gz -O codemirror.tgz \
        && wget https://github.com/FortAwesome/Font-Awesome/releases/download/$ver_fontawesome/fontawesome-free-$ver_fontawesome-web.zip -O fontawesome.zip \
        && wget https://github.com/google/zopfli/archive/zopfli-$ver_zopfli.tar.gz -O zopfli.tgz \
        && wget https://github.com/Daninet/hash-wasm/releases/download/v$ver_hashwasm/hash-wasm@$ver_hashwasm.zip -O hash-wasm.zip \
        && (mkdir hash-wasm \
            && cd hash-wasm \
            && unzip ../hash-wasm.zip) \
        && (tar -xf asmcrypto.tgz \
            && cd asmcrypto.js-$ver_asmcrypto \
            && npm install ) \
        && (tar -xf marked.tgz \
            && cd marked-$ver_marked \
            && npm install \
            && npm i grunt uglify-js -g ) \
        && (tar -xf codemirror.tgz \
            && cd codemirror5-$ver_codemirror \
            && npm install ) \
        && (tar -xf mde.tgz \
            && cd easy-markdown-editor* \
            && npm install \
            && npm i gulp-cli -g ) \
        && unzip fontawesome.zip \
        && tar -xf zopfli.tgz


# todo
# https://prismjs.com/download.html#themes=prism-funky&languages=markup+css+clike+javascript+autohotkey+bash+basic+batch+c+csharp+cpp+cmake+diff+docker+go+ini+java+json+kotlin+latex+less+lisp+lua+makefile+objectivec+perl+powershell+python+r+jsx+ruby+rust+sass+scss+sql+swift+systemd+toml+typescript+vbnet+verilog+vhdl+yaml&plugins=line-highlight+line-numbers+autolinker


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
        && python3 -m ensurepip \
        && python3 -m pip install fonttools zopfli


# build asmcrypto
RUN     cd asmcrypto.js-$ver_asmcrypto \
        && echo "export { Sha512 } from './hash/sha512/sha512';" > src/entry-export_all.ts \
        && node -r esm build.js \
        && awk '/HMAC state/{o=1}  /var HEAP/{o=0}  /function hmac_reset/{o=1}  /return \{/{o=0}  /var __extends =/{o=1}  /var Hash =/{o=0}  /hmac_|pbkdf2_/{next}  o{next}  {gsub(/IllegalStateError/,"Exception")}  {sub(/^ +/,"");sub(/^\/\/ .*/,"");sub(/;$/," ;")}  1' < asmcrypto.all.es5.js > /z/dist/sha512.ac.js


# build hash-wasm
RUN     cd hash-wasm \
        && mv sha512.umd.min.js /z/dist/sha512.hw.js


# build marked
COPY    marked.patch /z/
COPY    marked-ln.patch /z/
RUN     cd marked-$ver_marked \
        && patch -p1 < /z/marked-ln.patch \
        && patch -p1 < /z/marked.patch \
        && npm run build \
        && cp -pv marked.min.js /z/dist/marked.js \
        && mkdir -p /z/nodepkgs \
        && ln -s $(pwd) /z/nodepkgs/marked
#        && npm run test \


# build codemirror
COPY    codemirror.patch /z/
RUN     cd codemirror5-$ver_codemirror \
        && patch -p1 < /z/codemirror.patch \
        && sed -ri '/^var urlRE = /d' mode/gfm/gfm.js \
        && npm run build \
        && ln -s $(pwd) /z/nodepkgs/codemirror


# build easymde
COPY    easymde.patch /z/
RUN     cd easy-markdown-editor-$ver_mde \
        && patch -p1 < /z/easymde.patch \
        && sed -ri 's`https://registry.npmjs.org/marked/-/marked-[0-9\.]+.tgz`file:/z/nodepkgs/marked`' package-lock.json \
        && sed -ri 's`https://registry.npmjs.org/codemirror/-/codemirror-[0-9\.]+.tgz`file:/z/nodepkgs/codemirror`' package-lock.json \
        && sed -ri 's`("marked": ")[^"]+`\1file:/z/nodepkgs/marked`' ./package.json \
        && sed -ri 's`("codemirror": ")[^"]+`\1file:/z/nodepkgs/codemirror`' ./package.json \
        && sed -ri 's`^var marked = require\(.marked.\).marked;$`var marked = window.marked;`' src/js/easymde.js \
        && npm install

COPY    easymde-ln.patch /z/
RUN     cd easy-markdown-editor-$ver_mde \
        && patch -p1 < /z/easymde-ln.patch \
        && gulp \
        && cp -pv dist/easymde.min.css /z/dist/easymde.css \
        && cp -pv dist/easymde.min.js /z/dist/easymde.js


# build fontawesome and scp
COPY    mini-fa.sh /z
COPY    mini-fa.css /z
COPY    shiftbase.py /z
RUN     /bin/ash /z/mini-fa.sh


# compress
COPY    zopfli.makefile /z/dist/Makefile
RUN     cd /z/dist \
        && make -j$(nproc) \
        && rm Makefile \
        && mv no-pk/* . \
        && rmdir no-pk


# git diff -U2 --no-index marked-1.1.0-orig/ marked-1.1.0-edit/ -U2 | sed -r '/^index /d;s`^(diff --git a/)[^/]+/(.* b/)[^/]+/`\1\2`; s`^(---|\+\+\+) ([ab]/)[^/]+/`\1 \2`' > ../dev/copyparty/scripts/deps-docker/marked-ln.patch
# d=/home/ed/dev/copyparty/scripts/deps-docker/; tar -cf ../x . && ssh root@$bip "cd $d && tar -xv >&2 && make >&2 && tar -cC ../../copyparty/web deps" <../x | (cd ../../copyparty/web/; cat > the.tgz; tar -xvf the.tgz; rm the.tgz)
# gzip -dkf ../dev/copyparty/copyparty/web/deps/deps/marked.full.js.gz && diff -NarU2 ../dev/copyparty/copyparty/web/deps/{,deps/}marked.full.js
