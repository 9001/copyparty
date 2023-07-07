# reply with an endless "noooooooooooooooooooooooo"


def say_no():
    yield b"n"
    while True:
        yield b"o" * 4096


def main(cli, vn, rem):
    cli.send_headers(None, 404, "text/plain")

    for chunk in say_no():
        cli.s.sendall(chunk)

    return "false"
