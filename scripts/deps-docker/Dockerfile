FROM    alpine:3.10
WORKDIR /z
ENV     ver_forge=0.8.5 \
        ver_ogvjs=1.6.1

# download
RUN     apk add make g++ git bash npm patch wget tar pigz gzip unzip \
        && wget https://github.com/digitalbazaar/forge/archive/$ver_forge.tar.gz \
        && wget https://github.com/brion/ogv.js/releases/download/$ver_ogvjs/ogvjs-$ver_ogvjs.zip \
        && tar -xf $ver_forge.tar.gz \
        && unzip ogvjs-$ver_ogvjs.zip \
        && cd forge-$ver_forge \
        && npm install

# customize
COPY    forge.patch /z

# build forge
RUN     cd forge-$ver_forge \
        && patch -p1 < /z/forge.patch \
        && npm run build \
        && mkdir /z/dist \
        && cp -pv dist/forge.sha512.* /z/dist

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
