FROM    alpine:3.23
WORKDIR /z
ENV     ver_hashwasm=4.12.0 \
        ver_marked=4.3.0 \
        ver_dompf=3.4.6 \
        ver_mde=2.18.0 \
        ver_codemirror=5.65.18 \
        ver_fontawesome=5.13.0 \
        ver_prism=1.30.0 \
        ver_zopfli=1.0.3

# versioncheck:
# https://github.com/markedjs/marked/releases
# https://github.com/Ionaru/easy-markdown-editor/tags  # ignore 2.20.0
# https://github.com/codemirror/codemirror5/releases
# https://github.com/cure53/DOMPurify/releases
# https://github.com/Daninet/hash-wasm/releases
# https://github.com/google/zopfli/tags


# download;
# the scp url is regular latin from https://fonts.googleapis.com/css2?family=Source+Code+Pro&display=swap
RUN     mkdir -p /z/dist/no-pk \
        && wget https://ocv.me/dev/fonts/orbitron.woff2 -O /z/dist/no-pk/orbitron.woff2 \
        && sha512sum /z/dist/no-pk/orbitron.woff2 | tee /dev/stderr | grep -q b36a69a1b483ca735a3e7d026cdc5e993b8359bbf69b05deadc369fa759f88fe6087bbbbc0be51e62daf034c090df7ee096e5b07884c494aebf56db0e2bc53f7 \
        && wget https://fonts.gstatic.com/s/sourcecodepro/v11/HI_SiYsKILxRpg3hIP6sJ7fM7PqlPevW.woff2 -O scp.woff2 \
        && apk add \
                bash brotli cmake make g++ git gzip lame npm patch pigz \
                python3 python3-dev py3-pip py3-brotli sox tar unzip wget \
        && rm -f /usr/lib/python3*/EXTERNALLY-MANAGED \
        && pip install strip_hints \
        && wget https://github.com/markedjs/marked/archive/v$ver_marked.tar.gz -O marked.tgz \
        && wget https://github.com/Ionaru/easy-markdown-editor/archive/$ver_mde.tar.gz -O mde.tgz \
        && wget https://github.com/codemirror/codemirror5/archive/$ver_codemirror.tar.gz -O codemirror.tgz \
        && wget https://github.com/cure53/DOMPurify/archive/refs/tags/$ver_dompf.tar.gz -O dompurify.tgz \
        && wget https://github.com/FortAwesome/Font-Awesome/releases/download/$ver_fontawesome/fontawesome-free-$ver_fontawesome-web.zip -O fontawesome.zip \
        && wget https://github.com/google/zopfli/archive/zopfli-$ver_zopfli.tar.gz -O zopfli.tgz \
        && wget https://github.com/Daninet/hash-wasm/releases/download/v$ver_hashwasm/hash-wasm@$ver_hashwasm.zip -O hash-wasm.zip \
        && wget https://github.com/PrismJS/prism/archive/refs/tags/v$ver_prism.tar.gz -O prism.tgz \
        && wget https://files.pythonhosted.org/packages/91/47/746287c8962274f73ee25edb3840d80899464bfffbe2c435424c2d60a071/mfusepy-3.1.1.tar.gz -O mfusepy.tgz \
        && (mkdir hash-wasm \
            && cd hash-wasm \
            && unzip ../hash-wasm.zip) \
        && (tar --no-same-owner -xf marked.tgz \
            && cd marked-$ver_marked \
            && npm install \
            && npm i grunt uglify-js -g ) \
        && (tar --no-same-owner -xf codemirror.tgz \
            && cd codemirror5-$ver_codemirror \
            && npm install ) \
        && (tar --no-same-owner -xf mde.tgz \
            && cd easy-markdown-editor* \
            && npm install \
            && npm i gulp-cli -g ) \
        && tar --no-same-owner -xf dompurify.tgz \
        && tar --no-same-owner -xf prism.tgz \
        && tar --no-same-owner -xf mfusepy.tgz \
        && unzip fontawesome.zip \
        && tar --no-same-owner -xf zopfli.tgz


#COPY    busy-mp3.sh /z/
#RUN     /z/busy-mp3.sh \
#        && mv -v /dev/shm/busy.mp3.gz /z/dist


# build fonttools (which needs zopfli)
RUN     tar --no-same-owner -xf zopfli.tgz \
        && cd zopfli* \
        && cmake \
            -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
            -DCMAKE_INSTALL_PREFIX=/usr \
            -DZOPFLI_BUILD_SHARED=ON \
            -B build \
            -S . \
        && make -C build \
        && make -C build install \
        && python3 -m ensurepip \
        && python3 -m pip install fonttools zopfli


# build hash-wasm
RUN     cd hash-wasm/dist \
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


# build dompurify
RUN     (echo; cat DOMPurify-$ver_dompf/dist/purify.min.js) >> /z/dist/marked.js


# build fontawesome and scp
COPY    mini-fa.sh /z
COPY    mini-fa.css /z
COPY    shiftbase.py /z
RUN     /bin/ash /z/mini-fa.sh


# build prismjs
COPY    genprism.py /z
COPY    genprism.sh /z
RUN     ./genprism.sh $ver_prism


# compress
COPY    zopfli.makefile /z/dist/
RUN     cd /z/dist \
        && make -j$(nproc) -f zopfli.makefile \
        && rm *.makefile \
        && mv no-pk/* . \
        && rmdir no-pk


# build mfusepy -- just sizegolfing for the sfx, mfusepy.py works fine as-is
COPY    uncomment.py unhint.py /z
RUN     mv /z/mfusepy-3.1.1/mfusepy.py /z/dist/ \
        && cd /z/dist \
        && python3 /z/unhint.py \
        && rm -f uh \
        && mv mfusepy.py f1 \
        && python3 /z/uncomment.py f1 \
        && sed -ri '/self.__critical_exception/d; /^from (typing|collections.abc) import/d' f1 \
        && sed -ri '/^(FieldsEntry|BitFieldsEntry|ReadDirResult) =/d' f1 \
        && awk "/if TYPE_CHECKING:/{s=1;sub(/TYPE_CHECKING/,"1");print}!s;/else:/{s=0}" <f1 >f2 \
        && awk '/^def _nullable_dummy_function/{print"class Operations:\n    pass";exit};1' <f2 >f1 \
        && awk '/^# Note that/{s=3} --s<0; /self.use_ns = getattr/{s=16}' <f1 >f2 \
        && awk "/if _machine =/{s=0} /_machine == '(mips|ppc|ppc64)'/{s=1} !s" <f2 >f1 \
        && awk '/else:/{s=0} /elif _system == .NetBSD/{s=1} !s' <f1 >f2 \
        && awk '/^if _system == .NetBSD_False/{s=1;print"if 0:\n    pass"} /^elif/{s=0} !s' <f2 >f1 \
        && rm f2 && mv f1 mfusepy.py


# git diff -U2 --no-index marked-1.1.0-orig/ marked-1.1.0-edit/ -U2 | sed -r '/^index /d;s`^(diff --git a/)[^/]+/(.* b/)[^/]+/`\1\2`; s`^(---|\+\+\+) ([ab]/)[^/]+/`\1 \2`' > ../dev/copyparty/scripts/deps-docker/marked-ln.patch
# d=/home/ed/dev/copyparty/scripts/deps-docker/; tar -cf ../x . && ssh root@$bip "cd $d && tar -xv >&2 && make >&2 && tar -cC ../../copyparty/web deps" <../x | (cd ../../copyparty/web/; cat > the.tgz; tar -xvf the.tgz; rm the.tgz)
# gzip -dkf ../dev/copyparty/copyparty/web/deps/deps/marked.full.js.gz && diff -NarU2 ../dev/copyparty/copyparty/web/deps/{,deps/}marked.full.js
