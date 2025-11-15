import json
import re
import sys

from copyparty.util import fsenc, runcmd


"""
uses exiftool to geotag images based on embedded gps coordinates in exif data

adds four new metadata keys:
    .gps_lat = latitute
    .gps_lon = longitude
    .masl = meters above sea level
    city = "city, subregion, region"

usage: -mtp .masl,.gps_lat,.gps_lon,city=ad,t10,bin/mtag/geotag.py

example: https://a.ocv.me/pub/blog/j7/8/?grid=0
"""


def main():
    cmd = b"exiftool -api geolocation -n".split(b" ")
    rc, so, se = runcmd(cmd + [fsenc(sys.argv[1])])
    ptn = re.compile("([^:]*[^ :]) *: (.*)")
    city = ["", "", ""]
    ret = {}
    for ln in so.split("\n"):
        m = ptn.match(ln)
        if not m:
            continue
        k, v = m.groups()
        if k == "Geolocation City":
            city[2] = v
        elif k == "Geolocation Subregion":
            city[1] = v
        elif k == "Geolocation Region":
            city[0] = v
        elif k == "GPS Latitude":
            ret[".gps_lat"] = "%.04f" % (float(v),)
        elif k == "GPS Longitude":
            ret[".gps_lon"] = "%.04f" % (float(v),)
        elif k == "GPS Altitude":
            ret[".masl"] = str(int(float(v)))
    v = ", ".join(city).strip(", ")
    if v:
        ret["city"] = v
    print(json.dumps(ret))


if __name__ == "__main__":
    main()
