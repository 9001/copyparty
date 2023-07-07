# assume each requested file exists on another webserver and
# download + mirror them as they're requested
# (basically pretend we're warnish)

import os
import requests

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from copyparty.httpcli import HttpCli


def main(cli: "HttpCli", vn, rem):
    url = "https://mirrors.edge.kernel.org/alpine/" + rem
    abspath = os.path.join(vn.realpath, rem)

    # sneaky trick to preserve a requests-session between downloads
    # so it doesn't have to spend ages reopening https connections;
    # luckily we can stash it inside the copyparty client session,
    # name just has to be definitely unused so "hacapo_req_s" it is
    req_s = getattr(cli.conn, "hacapo_req_s", None) or requests.Session()
    setattr(cli.conn, "hacapo_req_s", req_s)

    try:
        os.makedirs(os.path.dirname(abspath), exist_ok=True)
        with req_s.get(url, stream=True, timeout=69) as r:
            r.raise_for_status()
            with open(abspath, "wb", 64 * 1024) as f:
                for buf in r.iter_content(chunk_size=64 * 1024):
                    f.write(buf)
    except:
        os.unlink(abspath)
        return "false"

    return "retry"
