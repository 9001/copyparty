when running behind a reverse-proxy, or a WAF, or another protection service such as cloudflare:

if you (and maybe everybody else) keep getting a message that says `thank you for playing`, then you've gotten banned for malicious traffic. This ban applies to the IP-address that copyparty *thinks* identifies the shady client -- so, depending on your setup, you might have to tell copyparty where to find the correct IP

knowing the correct IP is also crucial for some other features, such as the unpost feature which lets you delete your own recent uploads -- but if everybody has the same IP, well...

----

for most common setups, there should be a helpful message in the server-log explaining what to do, something like `--xff-src=10.88.0.0/16` or `--xff-src=lan` to accept the `X-Forwarded-For` header from your reverse-proxy with a LAN IP of `10.88.x.y`

if you are behind cloudflare, it is recommended to also set `--xff-hdr=cf-connecting-ip` to use a more trustworthy source of info, but then it's also very important to ensure your reverse-proxy does not accept connections from anything BUT cloudflare; you can do this by generating an ip-address allowlist and reject all other connections

* if you are using nginx as your reverse-proxy, see the [example nginx config](https://github.com/9001/copyparty/blob/hovudstraum/contrib/nginx/copyparty.conf) on how the cloudflare allowlist can be done

----

the server-log will give recommendations in the form of commandline arguments;

to do the same thing using config files, take the options that are suggested in the serverlog and put them into the `[global]` section in your `copyparty.conf` like so:

```yaml
[global]
  xff-src: lan
  xff-hdr: cf-connecting-ip
```

----

# but if you just want to get it working:

...and don't care about security, you can optionally disable the bot-detectors, either by specifying commandline-args `--ban-404=no --ban-403=no --ban-422=no --ban-url=no --ban-pw=no`

or by adding these lines inside the `[global]` section in your `copyparty.conf`:

```yaml
[global]
  ban-404: no
  ban-403: no
  ban-422: no
  ban-url: no
  ban-pw: no
```

but remember that this will make other features insecure as well, such as unpost

