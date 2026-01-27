FROM    alpine:3.23
WORKDIR /z


RUN     apk add \
                bash brotli make git gzip npm patch pigz tar unzip wget \
                python3 python3-dev py3-brotli py3-fonttools py3-zopfli


RUN     mkdir -p /z/dist/no-pk
COPY    build.sh /z/
RUN     /z/build.sh download
RUN     /z/build.sh unpack


# build hash-wasm
RUN     /z/build.sh build hash-wasm


# build marked
COPY    marked.patch /z/
COPY    marked-ln.patch /z/
RUN     /z/build.sh build marked


# build codemirror
COPY    codemirror.patch /z/
RUN     /z/build.sh build codemirror


# build easymde
COPY    easymde.patch /z/
COPY    easymde-ln.patch /z/
RUN     /z/build.sh build easymde


# build dompurify
RUN     /z/build.sh build dompurify


# build fontawesome and scp
COPY    mini-fa.sh /z
COPY    mini-fa.css /z
COPY    shiftbase.py /z
RUN     /z/build.sh build fonts


# build prismjs
COPY    genprism.py /z
COPY    genprism.sh /z
RUN     /z/build.sh build prismjs


# compress
COPY    zopfli.makefile /z/dist/
RUN     cd /z/dist \
        && make -j$(nproc) -f zopfli.makefile \
        && rm *.makefile \
        && mv no-pk/* . \
        && rmdir no-pk


# build fusepy
COPY    uncomment.py /z
RUN     mv /z/fusepy-3.0.1/fuse.py /z/dist/f1 \
        && cd /z/dist \
        && python3 /z/uncomment.py f1 \
        && sed -ri '/self.__critical_exception = e/d' f1 \
        && awk '/^log =/{s=0} !s; /^from traceback im/{s=1;print"from functools import partial";print"basestring = str"}' <f1 >f2 \
        && awk '/LoggingMixIn:/{exit} --s<0;/self.use_ns = getattr/{s=7}' <f2 >f1 \
        && awk "/if _machine =/{s=0} /'(mips|ppc|ppc64)'/{s=1} !s" <f1 >f2 \
        && rm f1 && mv f2 fuse.py


# git diff -U2 --no-index marked-1.1.0-orig/ marked-1.1.0-edit/ -U2 | sed -r '/^index /d;s`^(diff --git a/)[^/]+/(.* b/)[^/]+/`\1\2`; s`^(---|\+\+\+) ([ab]/)[^/]+/`\1 \2`' > ../dev/copyparty/scripts/deps-docker/marked-ln.patch
# d=/home/ed/dev/copyparty/scripts/deps-docker/; tar -cf ../x . && ssh root@$bip "cd $d && tar -xv >&2 && make >&2 && tar -cC ../../copyparty/web deps" <../x | (cd ../../copyparty/web/; cat > the.tgz; tar -xvf the.tgz; rm the.tgz)
# gzip -dkf ../dev/copyparty/copyparty/web/deps/deps/marked.full.js.gz && diff -NarU2 ../dev/copyparty/copyparty/web/deps/{,deps/}marked.full.js
