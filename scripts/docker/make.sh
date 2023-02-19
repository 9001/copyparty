#!/bin/bash
set -e

[ $(id -u) -eq 0 ] && {
    echo dont root
    exit 1
}

sarchs="386 amd64 arm/v7 arm64/v8 ppc64le s390x"
archs="amd64 arm s390x 386 arm64 ppc64le"
imgs="min im ac iv dj"
dhub_order="iv dj min im ac"
ghcr_order="ac im min dj iv"
ngs=(
    iv-ppc64le
    dj-ppc64le
)

for v in "$@"; do
    [ "$v" = clean  ] && clean=1
    [ "$v" = hclean ] && hclean=1
    [ "$v" = purge  ] && purge=1
    [ "$v" = pull   ] && pull=1
    [ "$v" = img    ] && img=1
    [ "$v" = push   ] && push=1
    [ "$v" = sh     ] && sh=1
done

[ $# -gt 0 ] || {
    echo "need list of commands, for example: hclean pull img push"
    exit 1
}

[ $sh ] && {
    printf "\n\033[1;31mopening a shell in the most recently created docker image\033[0m\n"
    podman run --rm -it --entrypoint /bin/ash $(podman images -aq | head -n 1)
    exit $?
}

filt=
[ $clean  ] && filt='/<none>/{print$$3}'
[ $hclean ] && filt='/localhost\/copyparty-|^<none>.*localhost\/alpine-/{print$3}'
[ $purge  ] && filt='NR>1{print$3}'
[ $filt ] && {
    [ $purge ] && {
        podman kill $(podman ps -q)
        podman rm   $(podman ps -qa)
    }
	podman rmi -f $(podman images -a --history | awk "$filt") || true
}

[ $pull ] && {
    for a in $sarchs; do  # arm/v6
        podman pull --arch=$a alpine:latest
    done
    
    podman images --format "{{.ID}} {{.History}}" |
    awk '/library\/alpine/{print$1}' |
    while read id; do
        tag=alpine-$(podman inspect $id | jq -r '.[]|.Architecture' | tr / -)
        [ -e .tag-$tag ] && continue
        touch .tag-$tag
        echo tagging $tag
        podman untag $id
        podman tag $id $tag
    done
    rm .tag-*
}

[ $img ] && {
    fp=../../dist/copyparty-sfx.py
    [ -e $fp ] || {
        echo downloading copyparty-sfx.py ...
        mkdir -p ../../dist
        wget https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py -O $fp
    }
    
    rm -rf i err
    mkdir i
    tar -cC../.. dist/copyparty-sfx.py bin/mtag | tar -xvCi

    ps aux | awk '/bin\/qemu-[^-]+-static/{print$2}' | xargs -r kill -9

    for i in $imgs; do
        podman rm copyparty-$i || true
        for a in $archs; do
            [[ " ${ngs[*]} " =~ " $i-$a " ]] && continue
            aa="$(printf '%7s' $a)"
            # --pull=never does nothing at all btw
            (set -x
            podman build \
                --pull=never \
                --from localhost/alpine-$a \
                --manifest copyparty-$i \
                -t copyparty-$i-$a \
                -f Dockerfile.$i . || (echo $? $a >> err)
            ) 2> >(tee $a.err | sed "s/^/$aa:/" >&2) > >(tee $a.out | sed "s/^/$aa:/") &
        done
        set +x
        wait
        [ -e err ] && {
            echo somethign died,
            cat err
            exit 1
        }
        for a in $archs; do
            rm -f $a.{out,err}
        done
    done
}

[ $push ] && {
    for i in $dhub_order; do
        podman manifest push --all copyparty-$i copyparty/$i:latest
    done
    for i in $ghcr_order; do
        podman manifest push --all copyparty-$i ghcr.io/9001/copyparty-$i:latest
    done
}

echo ok
