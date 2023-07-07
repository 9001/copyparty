replace the standard 404 / 403 responses with plugins


# usage

load plugins either globally with `--on404 ~/dev/copyparty/bin/handlers/sorry.py` or for a specific volume with `:c,on404=~/handlers/sorry.py`


# api

each plugin must define a `main()` which takes 3 arguments;

* `cli` is an instance of [copyparty/httpcli.py](https://github.com/9001/copyparty/blob/hovudstraum/copyparty/httpcli.py) (the monstrosity itself)
* `vn` is the VFS which overlaps with the requested URL, and
* `rem` is the URL remainder below the VFS mountpoint
    * so `vn.vpath + rem` == `cli.vpath` == original request


# examples

## on404

* [sorry.py](answer.py) replies with a custom message instead of the usual 404
* [nooo.py](nooo.py) replies with an endless noooooooooooooo
* [never404.py](never404.py) 100% guarantee that 404 will never be a thing again as it automatically creates dummy files whenever necessary
* [caching-proxy.py](caching-proxy.py) transforms copyparty into a squid/varnish knockoff

## on403

* [ip-ok.py](ip-ok.py) disables security checks if client-ip is 1.2.3.4


# notes

* on403 only works for trivial stuff (basic http access) since I haven't been able to think of any good usecases for it (was just easy to add while doing on404)
