# if someone hits a 404, redirect them to another location


def send_http_302_temporary_redirect(cli, new_path):
    """
    replies with an HTTP 302, which is a temporary redirect;
    "new_path" can be any of the following:
      - "http://a.com/" would redirect to another website,
      - "/foo/bar" would redirect to /foo/bar on the same server;
          note the leading '/' in the location which is important
    """
    cli.reply(b"redirecting...", 302, headers={"Location": new_path})


def send_http_301_permanent_redirect(cli, new_path):
    """
    replies with an HTTP 301, which is a permanent redirect;
    otherwise identical to send_http_302_temporary_redirect
    """
    cli.reply(b"redirecting...", 301, headers={"Location": new_path})


def send_errorpage_with_redirect_link(cli, new_path):
    """
    replies with a website explaining that the page has moved;
    "new_path" must be an absolute location on the same server
    but without a leading '/', so for example "foo/bar"
    would redirect to "/foo/bar"
    """
    cli.redirect(new_path, click=False, msg="this page has moved")


def main(cli, vn, rem):
    """
    this is the function that gets called by copyparty;
    note that vn.vpath and cli.vpath does not have a leading '/'
    so we're adding the slash in the debug messages below
    """
    print(f"this client just hit a 404: {cli.ip}")
    print(f"they were accessing this volume: /{vn.vpath}")
    print(f"and the original request-path (straight from the URL) was /{cli.vpath}")
    print(f"...which resolves to the following filesystem path: {vn.canonical(rem)}")

    new_path = "/foo/bar/"
    print(f"will now redirect the client to {new_path}")

    # uncomment one of these:
    send_http_302_temporary_redirect(cli, new_path)
    # send_http_301_permanent_redirect(cli, new_path)
    # send_errorpage_with_redirect_link(cli, new_path)

    return "true"
