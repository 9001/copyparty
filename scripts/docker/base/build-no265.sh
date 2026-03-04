#!/bin/bash
set -e

[ $(id -u) -eq 0 ] && {
	echo dont root
	exit 1
}
self=$(cd -- "$(dirname "$BASH_SOURCE")"; pwd -P)
cd "$self"

sarchs="386 amd64 arm/v7 arm64/v8 ppc64le s390x"
archs="amd64 amd64 386 arm64 arm s390x ppc64le"

err=
for x in awk jq podman python3 tar wget ; do
	command -v $x >/dev/null && continue
	err=1; echo ERROR: missing dependency: $x
done
[ $err ] && exit 1

for v in "$@"; do
	[ "$v" = pull ] && pull=1
	[ "$v" = img  ] && img=1
done

[ $# -gt 0 ] || {
	echo "need list of commands, for example: pull img"
	exit 1
}

wt() {
	printf '\033]0;%s\033\\' "$*"
	[ -z "$TMUX" ] || tmux renamew "$*"
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
	mkdir -p "$self/b"

	# enable arm32 crossbuild from aarch64 (macbook or whatever)
	[ $(uname -m) = aarch64 ] && [ ! -e /proc/sys/fs/binfmt_misc/qemu-arm ] &&
		echo ":qemu-arm:M:0:\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/usr/bin/qemu-arm-static:F" |
		sudo tee >/dev/null /proc/sys/fs/binfmt_misc/register

	# kill abandoned builders
	ps aux | awk '/bin\/qemu-[^-]+-static/{print$2}' | xargs -r kill -9

	n=0; set -x
	for a in $archs; do
		n=$((n+1)); wt "$n/$a"
		#[ $n -le 3 ] || continue
		touch b/t.$a.1.$(date +%s)

		tar -c arbeidspakke.sh patch/ffmpeg |
		time nice podman run \
			--rm -i --pull=never -v "$self/b:/root:z" localhost/alpine-$a \
			/bin/ash -c "cd /opt;tar -x;/bin/ash ./arbeidspakke.sh $n $a" 2>&1 |
		tee b/log.$a

		touch b/t.$a.2.$(date +%s)
	done
	wt -;wt ""
}

echo ok

# just-no265
#  4m18.77 x64
#  4m22.81 386
# 45m36.44 arm64 
# 34m31.22 ppc64le
# 50m01.04 s390x

# golflympics
#    4:09 x86_64-hub
#    2:57 x86_64
#    2:54 x86
#   31:13 aarch64
#   22:38 armv7
#   32:17 s390x
#   24:27 ppc64le
# 2:00:35 summa summarum
