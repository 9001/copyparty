#!/bin/bash
set -e

AVER=3.24

[ $(id -u) -eq 0 ] && {
	echo dont root
	exit 1
}
self=$(cd -- "$(dirname "$BASH_SOURCE")"; pwd -P)
cd "$self"

sarchs="386 amd64 arm/v7 arm64/v8 ppc64le s390x"
archs="amd64 386 arm64 arm s390x ppc64le"

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
	for a in $sarchs; do
		podman pull --arch=$a alpine:$AVER
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

	n=0; set -xo pipefail
	for a in $archs; do
		n=$((n+1)); wt "$n/$a"
		#[ $n -le 3 ] || continue
		touch b/t2.$n.$a.1.$(date +%s)

		tar -c arbeidspute.sh |
		time nice podman run \
			--rm -i --pull=never -v "$self/b:/root:z" localhost/alpine-$a \
			/bin/ash -c "cd /opt;tar -x;/bin/ash ./arbeidspute.sh $n $a" 2>&1 |
		awk '{getline a<"/proc/uptime";close("/proc/uptime");sub(/ .*/,"",a);printf"%.2f %s\n",a-p,$0;p=a}' |
		tee b/log2.$n.$a

		touch b/t2.$n.$a.2.$(date +%s)
	done
	wt -;wt ""
}

echo ok
