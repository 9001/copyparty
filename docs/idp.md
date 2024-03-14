there is a [docker-compose example](./examples/docker/idp-authelia-traefik) which is hopefully a good starting point (meaning you can skip the steps below) -- but if you want to set this up from scratch yourself (or learn about how it works), keep reading:

to configure IdP from scratch, you must place copyparty behind a reverse-proxy which sends all requests through a middleware (the IdP / identity-provider service) which will inject a set of headers into the requests, telling copyparty who the user is

in the copyparty `[global]` config, specify which headers to read client info from; username is required (`idp-h-usr: X-Authooley-User`), group(s) are optional (`idp-h-grp: X-Authooley-Groups`)

* it is also required to specify the subnet that legit requests will be coming from, for example `--xff-src=10.88.0.0/24` to allow 10.88.x.x (or `--xff-src=lan` for all private IPs), and it is recommended to configure the reverseproxy to include a secret header as proof that the other headers are also legit (and not smuggled in by a malicious client), telling copyparty the headername to expect with `idp-h-key: shangala-bangala`
