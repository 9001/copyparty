# /!\ Warning: be careful, as webdav clients often generate a large number of 404 requets.

# In your `jail.local`, add:
# [copyparty]
# enabled = true
# logtimezone = UTC
# logpath = /path/to/log/file # or keep the default value if you're using systemd

# Create the `copyparty.conf` file in `filter.d` with the following:
# [Definition]
# failregex = ^ <ADDR>$
# ignoreregex =
# datepattern = ^fail2ban: %%Y-%%m-%%dT%%H:%%M:%%S

# First check `--dont-ban`, and if it doesn't match, log the line to be intercepted by fail2ban.
from datetime import datetime, UTC
def main(cli, vn="", rem=""):
    now = datetime.now(UTC).isoformat()[:19]
    msg = "\nfail2ban: %s %s"
    if not vn and not rem:
        # got called by --xban
        cli["log"](msg % (now, cli["ip"]), 3)
        return {"rc": 0}

    cond = cli.args.dont_ban
    if (
        cond == "any"
        or (cond == "auth" and cli.uname != "*")
        or (cond == "aa" and cli.avol)
        or (cond == "av" and cli.can_admin)
        or (cond == "rw" and cli.can_read and cli.can_write)
    ):
        return ""

    cli.log(msg % (now, cli.ip), 3)
    return ""
