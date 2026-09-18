> [!WARNING]  
> this is modified version of [idp-authelia-traefik](../idp-authelia-traefik/), similiar to what i use, all work is based on that example and my own developments, everything written in readme of idp-authelia-traefik applies here as well

to try this out with minimal adjustments:
* specify what filesystem-path to share with copyparty, replacing the default/example value `/srv/pub` in `docker-compose.yml`
* add `127.0.0.1 fs.example.com traefik.example.com authelia.example.com` to your `/etc/hosts`
* `sudo docker-compose up`
* login to https://fs.example.com/ with username `authelia` password `authelia`

# performance

7840hs, nvme ssd and ubuntu 25.10

| 1MB files D/L | https D/L |  http D/L  | approach |
| -------------:| ---------:|:----------:| -------- |
|  385 files/s  | 790 MiB/s | 1.7+ GiB/s | `copyparty/ac` port forwarding |
|  294 files/s  | 750 MiB/s | n/a        | `copyparty/ac` behind caddy |
|  108 files/s  | 750 MiB/s | n/a        | caddy and authelia **(you are here)** |
