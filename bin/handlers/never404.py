# create a dummy file and let copyparty return it


def main(cli, vn, rem):
    print("hello", cli.ip)

    abspath = vn.canonical(rem)
    with open(abspath, "wb") as f:
        f.write(b"404? not on MY watch!")

    return "retry"
