#!/usr/bin/env python3

import os
import re
import sys


_ = r"""
purpose:
  sync/backup phone gallery (pics/vids) to a nas which runs copyparty

what this hook does:
  redirect photos/videos into date-based folders, named "%Y%m" according
  to filename; that is, "/cam/sort/DCIM/D027/PXL_20250828_202820075.jpg"
  will be redirected to "/cam/pics/ts/202508/PXL_20250828_202820075.jpg"

requires this setup on the server:
  * /cam/ is a volume with all your pics/vids
  * the phone must upload to somewhere below /cam/sort/
  * photo/video filenames match the following regex:
     ^[a-z]{3,4}_([0-9]{6})[0-9]{2}_[0-9]{6}.*\.(jpg|mp4)$
  * so for example these filenames are OK:
    * PXL_20250828_202820075.jpg
    * IMG_20251123_202405.jpg
    * PANO_20180421_121245_03.t8o5.jpg
    * VID_20250307_220250-crf34.mp4

example server config as a volflag:
  -v /mnt/thedisk/gallery:cam:rwa,ed:c,e2ds,xbu=I,~/hooks/phonecam-sorter.py

example server config in a copyparty config file:
  [/cam]
    /mnt/thedisk/gallery
    accs:
      rwa: ed
    flags:
      e2ds
      xbu: I,~/hooks/phonecam-sorter.py

command to run on phone to sync to server, sending new files only:
  ~/bin/u2c.py -te homenas.ca -a '$homenas.pw' https://10.0.0.2:3923/cam/sort/ ~/storage/dcim/Camera

the phone-command above assumes this setup on the phone:
* termux or another linux-like thing with access to gallery files
* homenas.ca is a textfile with the server's CA certificate
* homenas.pw is a textfile with the copyparty password inside
* ~/storage/dcim/ exists; if not, run termux-setup-storage
* ~/bin/u2c.py exists; if not, curl -LO https://10.0.0.2:3923/.cpr/a/u2c.py && chmod 755 u2c.py

unfortunate consequences:
* due to the redirection, u2c -z doesn't do anything, so every local
   file is hashed every time, wasting some time and cpu on the phone
   but otoh certainly avoids corruption on either side (phone/server)

"""


def main(inf):
    log = inf["log"]
    vdir, fn = os.path.split(inf["vp"])
    if not vdir.startswith("cam/sort"):
        return {"rc": 0}  # 2nd call after 1st reloc; already done

    m = re.match(r"^[a-z]{3,4}_([0-9]{6})[0-9]{2}_[0-9]{6}.*\.(jpg|mp4)$", fn.lower())
    if not m:
        return {"rc": 0}  # not recognized; write to original path in /cam/sort/

    ym, ext = m.groups()
    if ext == "jpg":
        dst = f"/cam/pics/ts/{ym}/"
    elif ext == "mp4":
        dst = f"/cam/vids/ts/{ym}/"
    else:
        return {"rc": 0}

    ap = "%s%s" % (inf["ap"].split("/cam/sort/")[0], dst)
    if not os.path.isdir(ap):
        os.makedirs(ap)

    ret = {"rc": 0, "reloc": {"vp": dst}}
    return ret


if __name__ == "__main__":
    main()
