FROM    alpine:3.10
WORKDIR /z
ENV     ver_asmcrypto=2821dd1dedd1196c378f5854037dda5c869313f3 \
        ver_ogvjs=1.6.1

# download
RUN     apk add make g++ git bash npm patch wget tar pigz gzip unzip \
        && wget https://github.com/brion/ogv.js/releases/download/$ver_ogvjs/ogvjs-$ver_ogvjs.zip \
        && wget https://github.com/asmcrypto/asmcrypto.js/archive/$ver_asmcrypto.tar.gz \
        && unzip ogvjs-$ver_ogvjs.zip \
        && tar -xf $ver_asmcrypto.tar.gz \
        && cd asmcrypto.js-$ver_asmcrypto \
        && npm install \
        && mkdir /z/dist

# build asmcrypto
RUN     cd asmcrypto.js-$ver_asmcrypto \
        && echo "export { Sha512 } from './hash/sha512/sha512';" > src/entry-export_all.ts \
        && node -r esm build.js \
        && mv asmcrypto.all.es5.js /z/dist/sha512.js \
        && mv dist_es5/hash/sha512/sha512.asm.js /z/dist/

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

# compress
COPY    zopfli.makefile /z/dist/Makefile
RUN     cd /z/dist \
        && make -j$(nproc) \
        && rm Makefile
