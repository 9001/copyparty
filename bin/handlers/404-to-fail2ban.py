# In your `jail.local`, add:
# [copyparty]
# enabled = true
# logpath = /path/to/log/file # or keep the default value if you're using systemd

# Create the `copyparty.conf` file in `filter.d` with the following:
# [Definition]
# failregex = ^ fail2ban\s*WARN: <ADDR>$
# ignoreregex =
# datepattern = ^%%H:%%M:%%S\.%%f

# First check `--dont-ban`, and if it doesn't match, log the line to be intercepted by fail2ban.
def main(cli, vn, rem):
    cond = cli.args.dont_ban
    if (
        cond == "any"
        or (cond == "auth" and cli.uname != "*")
        or (cond == "aa" and cli.avol)
        or (cond == "av" and cli.can_admin)
        or (cond == "rw" and cli.can_read and cli.can_write)
    ):
        return ""

    cli.log_func("fail2ban", f"{cli.ip}", 3)
    return ""
