there is a [docker-compose example](./examples/docker/idp-authelia-traefik) which is hopefully a good starting point (meaning you can skip the steps below) -- but if you want to set this up from scratch yourself (or learn about how it works), keep reading:

to configure IdP from scratch, you must place copyparty behind a reverse-proxy which sends all requests through a middleware (the IdP / identity-provider service) which will inject a set of headers into the requests, telling copyparty who the user is

in the copyparty `[global]` config, specify which headers to read client info from; username is required (`idp-h-usr: X-Authooley-User`), group(s) are optional (`idp-h-grp: X-Authooley-Groups`)

* it is also required to specify the subnet that legit requests will be coming from, for example `--xff-src=10.88.0.0/24` to allow 10.88.x.x (or `--xff-src=lan` for all private IPs), and it is recommended to configure the reverseproxy to include a secret header as proof that the other headers are also legit (and not smuggled in by a malicious client), telling copyparty the headername to expect with `idp-h-key: shangala-bangala`


# important notes

## IdP volumes are forgotten on shutdown

IdP volumes, meaning dynamically-created volumes, meaning volumes that contain `${u}` or `${g}` in their URL, will be forgotten during a server restart and then "revived" when the volume's owner sends their first request after the restart

until each IdP volume is revived, it will inherit the permissions of its parent volume (if any)

this means that, if an IdP volume is located inside a folder that is readable by anyone, then each of those IdP volumes will **also become readable by anyone** until the volume is revived

and likewise -- if the IdP volume is inside a folder that is only accessible by certain users, but the IdP volume is configured to allow access from unauthenticated users, then the contents of the volume will NOT be accessible until it is revived

until this limitation is fixed (if ever), it is recommended to place IdP volumes inside an appropriate parent volume, so they can inherit acceptable permissions until their revival; see the "strategic volumes" at the bottom of [./examples/docker/idp/copyparty.conf](./examples/docker/idp/copyparty.conf)


## Connecting webdav clients

If you use only idp and want to connect via rclone you have to adapt a few things.
The following steps are for Authelia, but should be easy adaptable to other IdPs and clients. There may be better/smarter ways to do this, but this is a known solution.

1. Add a rule for your domain and set it to one factor
```
  rules:
    - domain: 'sub.domain.tld'
      policy: one_factor
```
2. After you created your rclone config find its location with `rclone config file` and add the headers option to it, change the string to `username:password` base64 encoded. Make sure to set the right url location, otherwise you will get a 401 from copyparty.
```
[servername-dav]
type = webdav
url = https://sub.domain.tld/u/user/priv/
vendor = owncloud
pacer_min_sleep = 0.01ms
headers = Proxy-Authorization,basic base64encodedstring==
```