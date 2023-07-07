# disable permission checks and allow access if client-ip is 1.2.3.4


def main(cli, vn, rem):
    if cli.ip == "1.2.3.4":
        return "allow"
