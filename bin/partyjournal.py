#!/usr/bin/env python3

"""
partyjournal.py: chronological history of uploads
2021-12-31, v0.1, ed <irc.rizon.net>, MIT-Licensed
https://github.com/9001/copyparty/blob/hovudstraum/bin/partyjournal.py

produces a chronological list of all uploads,
by collecting info from up2k databases and the filesystem

specify subnet `192.168.1.*` with argument `.=192.168.1.`,
affecting all successive mappings

usage:
  ./partyjournal.py > partyjournal.html .=192.168.1. cart=125 steen=114 steen=131 sleepy=121 fscarlet=144 ed=101 ed=123

"""

import sys
import base64
import sqlite3
import argparse
from datetime import datetime, timezone
from urllib.parse import quote_from_bytes as quote
from urllib.parse import unquote_to_bytes as unquote


FS_ENCODING = sys.getfilesystemencoding()
UTC = timezone.utc


class APF(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


##
## snibbed from copyparty


def s3dec(v):
    if not v.startswith("//"):
        return v

    v = base64.urlsafe_b64decode(v.encode("ascii")[2:])
    return v.decode(FS_ENCODING, "replace")


def quotep(txt):
    btxt = txt.encode("utf-8", "replace")
    quot1 = quote(btxt, safe=b"/")
    quot1 = quot1.encode("ascii")
    quot2 = quot1.replace(b" ", b"+")
    return quot2.decode("utf-8", "replace")


def html_escape(s, quote=False, crlf=False):
    """html.escape but also newlines"""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if quote:
        s = s.replace('"', "&quot;").replace("'", "&#x27;")
    if crlf:
        s = s.replace("\r", "&#13;").replace("\n", "&#10;")

    return s


## end snibs
##


def main():
    ap = argparse.ArgumentParser(formatter_class=APF)
    ap.add_argument("who", nargs="*")
    ar = ap.parse_args()

    imap = {}
    subnet = ""
    for v in ar.who:
        if "=" not in v:
            raise Exception("bad who: " + v)

        k, v = v.split("=")
        if k == ".":
            subnet = v
            continue

        imap["{}{}".format(subnet, v)] = k

    print(repr(imap), file=sys.stderr)

    print(
        """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><style>

html, body {
    color: #ccc;
    background: #222;
    font-family: sans-serif;
}
a {
    color: #fc5;
}
td, th {
    padding: .2em .5em;
    border: 1px solid #999;
    border-width: 0 1px 1px 0;
    white-space: nowrap;
}
td:nth-child(1),
td:nth-child(2),
td:nth-child(3) {
    font-family: monospace, monospace;
    text-align: right;
}
tr:first-child {
    position: sticky;
    top: -1px;
}
th {
    background: #222;
    text-align: left;
}

</style></head><body><table><tr>
    <th>wark</th>
    <th>time</th>
    <th>size</th>
    <th>who</th>
    <th>link</th>
</tr>"""
    )

    db_path = ".hist/up2k.db"
    conn = sqlite3.connect(db_path)
    q = r"pragma table_info(up)"
    inf = conn.execute(q).fetchall()
    cols = [x[1] for x in inf]
    print("<!-- " + str(cols) + " -->")
    # ['w', 'mt', 'sz', 'rd', 'fn', 'ip', 'at']

    q = r"select * from up order by case when at > 0 then at else mt end"
    for w, mt, sz, rd, fn, ip, at in conn.execute(q):
        link = "/".join([s3dec(x) for x in [rd, fn] if x])
        if fn.startswith("put-") and sz < 4096:
            try:
                with open(link, "rb") as f:
                    txt = f.read().decode("utf-8", "replace")
            except:
                continue

            if txt.startswith("msg="):
                txt = txt.encode("utf-8", "replace")
                txt = unquote(txt.replace(b"+", b" "))
                link = txt.decode("utf-8")[4:]

        sz = "{:,}".format(sz)
        dt = datetime.fromtimestamp(at if at > 0 else mt, UTC)
        v = [
            w[:16],
            dt.strftime("%Y-%m-%d %H:%M:%S"),
            sz,
            imap.get(ip, ip),
        ]

        row = "<tr>\n  "
        row += "\n  ".join(["<td>{}</th>".format(x) for x in v])
        row += '\n  <td><a href="{}">{}</a></td>'.format(link, html_escape(link))
        row += "\n</tr>"
        print(row)

    print("</table></body></html>")


if __name__ == "__main__":
    main()
