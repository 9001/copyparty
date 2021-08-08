#!/bin/bash
set -e

# runs copyparty in a chroot
#
# assumption: all items within the following directories are owned by root
sysdirs=(bin lib lib32 lib64 sbin usr)


# read arguments
{
	jail="$1"; shift
	uid="$1"; shift
	gid="$1"; shift
	
	vols=()
	while true; do
		v="$1"; shift
		[ "$v" = -- ] && break  # end of volumes
		[ "$#" -eq 0 ] && break  # invalid usage
		vols+=("$v")
	done
	cpp="$1"; shift
} || {
	echo "usage: ./prisonparty.sh <ROOTDIR> <UID> <GID> [VOLDIR [VOLDIR...]] -- copyparty-sfx.py [...]"
	echo "example: ./prisonparty.sh /var/jail 1000 1000 /mnt/nas/music -- copyparty-sfx.py -v /mnt/nas/music::rwmd"
	exit 1
}


# debug/vis
echo "chroot-dir: [$jail]"
echo "user:group: [$uid:$gid]"
echo " copyparty: [$cpp]"
for v in "${vols[@]}"; do
	echo "     mount: [$v]"
done


# resolve and remove trailing slash
jail="$(realpath "$jail")"
jail="${jail%/}"


# bind-mount system directories and volumes
for v in "${sysdirs[@]}" "${vols[@]}"; do
  mkdir -p "$jail/$v"
  mount | grep -qF " on $jail/$v " ||
    mount --bind /$v "$jail/$v"
done


# create a tmp
mkdir -p "$jail/tmp"
chown -R "$uid:$gid" "$jail/tmp"


# copy sfx into jail
cp -pv "$cpp" "$jail/copyparty.py"


# run copyparty
/sbin/chroot --userspec=$uid:$gid "$jail" "$(which python3)" /copyparty.py "$@"


# cleanup if not in use
lsof "$jail" | grep -qF "$jail" ||
mount | grep -F " on $jail" | awk '{sub(/ type .*/,"");sub(/.* on /,"");print}' | LC_ALL=C sort -r  | tr '\n' '\0' | xargs -r0 umount
