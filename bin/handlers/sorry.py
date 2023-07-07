# sends a custom response instead of the usual 404


def main(cli, vn, rem):
    msg = f"sorry {cli.ip} but {cli.vpath} doesn't exist"

    return str(cli.reply(msg.encode("utf-8"), 404, "text/plain"))
