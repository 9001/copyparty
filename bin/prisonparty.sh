#!/bin/bash
set -e

# runs copyparty (or any other program really) in a chroot
#
# assumption: these directories, and everything within, are owned by root
sysdirs=(); for v in /bin /lib /lib32 /lib64 /sbin /usr /etc/alternatives ; do
	[ -e $v ] && sysdirs+=($v)
done

# error-handler
help() { cat <<'EOF'

usage:
  ./prisonparty.sh <ROOTDIR> <UID> <GID> [VOLDIR [VOLDIR...]] -- python3 copyparty-sfx.py [...]

example:
  ./prisonparty.sh /var/lib/copyparty-jail 1000 1000 /mnt/nas/music -- python3 copyparty-sfx.py -v /mnt/nas/music::rwmd

example for running straight from source (instead of using an sfx):
  PYTHONPATH=$PWD ./prisonparty.sh /var/lib/copyparty-jail 1000 1000 /mnt/nas/music -- python3 -um copyparty -v /mnt/nas/music::rwmd

note that if you have python modules installed as --user (such as bpm/key detectors),
  you should add /home/foo/.local as a VOLDIR

EOF
exit 1
}


# read arguments
trap help EXIT
jail="$(realpath "$1")"; shift
uid="$1"; shift
gid="$1"; shift

vols=()
while true; do
	v="$1"; shift
	[ "$v" = -- ] && break  # end of volumes
	[ "$#" -eq 0 ] && break  # invalid usage
	vols+=( "$(realpath "$v" || echo "$v")" )
done
pybin="$1"; shift
pybin="$(command -v "$pybin")"
pyarg=
while true; do
	v="$1"
	[ "${v:0:1}" = - ] || break
	pyarg="$pyarg $v"
	shift
done
cpp="$1"; shift
[ -d "$cpp" ] && cppdir="$PWD" || {
	# sfx, not module
	cpp="$(realpath "$cpp")"
	cppdir="$(dirname "$cpp")"
}
trap - EXIT


# debug/vis
echo
echo "chroot-dir = $jail"
echo "user:group = $uid:$gid"
echo " copyparty = $cpp"
echo
printf '\033[33m%s\033[0m\n' "copyparty can access these folders and all their subdirectories:"
for v in "${vols[@]}"; do
	printf '\033[36m ├─\033[0m %s \033[36m ── added by (You)\033[0m\n' "$v"
done
printf '\033[36m ├─\033[0m %s \033[36m ── where the copyparty binary is\033[0m\n' "$cppdir"
printf '\033[36m ╰─\033[0m %s \033[36m ── the folder you are currently in\033[0m\n' "$PWD"
vols+=("$cppdir" "$PWD")
echo


# remove any trailing slashes
jail="${jail%/}"


# bind-mount system directories and volumes
printf '%s\n' "${sysdirs[@]}" "${vols[@]}" | sed -r 's`/$``' | LC_ALL=C sort | uniq |
while IFS= read -r v; do
	[ -e "$v" ] || {
		printf '\033[1;31mfolder does not exist:\033[0m %s\n' "$v"
		continue
	}
	i1=$(stat -c%D.%i "$v"      2>/dev/null || echo a)
	i2=$(stat -c%D.%i "$jail$v" 2>/dev/null || echo b)
	# echo "v [$v] i1 [$i1] i2 [$i2]"
	[ $i1 = $i2 ] && continue
	
	mkdir -p "$jail$v"
	mount --bind "$v" "$jail$v"
done


cln() {
	rv=$?
	wait -f -p rv $p || true
	cd /
	echo "stopping chroot..."
	lsof "$jail" | grep -F "$jail" &&
		echo "chroot is in use; will not unmount" ||
	{
		mount | grep -F " on $jail" |
		awk '{sub(/ type .*/,"");sub(/.* on /,"");print}' |
		LC_ALL=C sort -r  | tee /dev/stderr | tr '\n' '\0' | xargs -r0 umount
	}
	exit $rv
}
trap cln EXIT


# create a tmp
mkdir -p "$jail/tmp"
chmod 777 "$jail/tmp"


# create a dev
(cd $jail; mkdir -p dev; cd dev
[ -e null ]    || mknod -m 666 null    c 1 3
[ -e zero ]    || mknod -m 666 zero    c 1 5
[ -e random ]  || mknod -m 444 random  c 1 8
[ -e urandom ] || mknod -m 444 urandom c 1 9
)


# run copyparty
export HOME=$(getent passwd $uid | cut -d: -f6)
export USER=$(getent passwd $uid | cut -d: -f1)
export LOGNAME="$USER"
#echo "pybin [$pybin]"
#echo "pyarg [$pyarg]"
#echo "cpp [$cpp]"
chroot --userspec=$uid:$gid "$jail" "$pybin" $pyarg "$cpp" "$@" &
p=$!
trap 'kill -USR1 $p' USR1
trap 'kill $p' INT TERM
wait
