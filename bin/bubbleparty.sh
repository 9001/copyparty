#!/bin/bash
# usage: ./bubbleparty.sh ./copyparty-sfx.py ....
bwrap \
  --unshare-all \
  --ro-bind /usr /usr \
  --ro-bind /bin /bin \
  --ro-bind /lib /lib \
  --ro-bind /etc/resolv.conf /etc/resolv.conf \
  --dev-bind /dev /dev \
  --dir /tmp \
  --dir /var \
  --bind "$(pwd)" "$(pwd)" \
  --share-net \
  --die-with-parent \
  --file 11 /etc/passwd \
  --file 12 /etc/group \
  "$@" \
  11< <(getent passwd $(id -u) 65534) \
  12< <(getent group $(id -g) 65534) 
