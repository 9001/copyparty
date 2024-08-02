the following setup appears to work (copyparty starts, accepts uploads, is able to persist config)

tested on debian 12 using [portainer-ce](https://docs.portainer.io/start/install-ce/server/docker/linux) with [docker-ce](https://docs.docker.com/engine/install/debian/) as root (not rootless)

before making the container, first `mkdir /etc/copyparty /srv/pub` which will be bind-mounts into the container

> both `/etc/copyparty` and `/srv/pub` are examples; you can change them if you'd like

put your copyparty config files directly into `/etc/copyparty` and the files to share inside `/srv/pub`

on first startup, copyparty will create a subfolder inside `/etc/copyparty` called `copyparty` where it puts some runtime state; for example replacing `/etc/copyparty/copyparty/cert.pem` with another TLS certificate is a quick and dirty way to get valid HTTPS (if you really want copyparty to handle that and not a reverse-proxy)


## in portainer:

```
environments -> local -> containers -> add container:

       name = copyparty-ac
   registry = docker hub
      image = copyparty/ac
always pull = no

manual network port publishing:
  3923 to 3923 [TCP]

advanced -> command & logging:
  console = interactive & tty

advanced -> volumes -> map additional volume:
  container = /cfg  [Bind]
  host = /etc/copyparty  [Writable]

advanced -> volumes -> map additional volume:
  container = /w  [Bind]
  host = /srv/pub  [Writable]
```

notes:

* `/cfg` is where copyparty expects to find its config files; `/etc/copyparty` is just an example mapping to that

* `/w` is where copyparty expects to find the folder to share; `/srv/pub` is just an example mapping to that

* the volumes must be bind-mounts to avoid permission issues (or so the theory goes)
