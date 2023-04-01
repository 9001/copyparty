# using rclone to mount a remote copyparty server as a local filesystem

speed estimates with server and client on the same win10 machine:
* `1070 MiB/s` with rclone as both server and client
* `570 MiB/s` with rclone-client and `copyparty -ed -j16` as server
* `220 MiB/s` with rclone-client and `copyparty -ed` as server
* `100 MiB/s` with [../bin/partyfuse.py](../bin/partyfuse.py) as client

when server is on another machine (1gbit LAN),
* `75 MiB/s` with [../bin/partyfuse.py](../bin/partyfuse.py) as client
* `92 MiB/s` with rclone-client and `copyparty -ed` as server
* `103 MiB/s` (connection max) with `copyparty -ed -j16` and all the others


# creating the config file

the copyparty "connect" page at `/?hc` (so for example http://127.0.0.1:3923/?hc) will generate commands to autoconfigure rclone for your server

**if you prefer to configure rclone manually, continue reading:**

replace `hunter2` with your password, or remove the `hunter2` lines if you allow anonymous access


### on windows clients:
```
(
echo [cpp-rw]
echo type = webdav
echo vendor = owncloud
echo url = http://127.0.0.1:3923/
echo headers = Cookie,cppwd=hunter2
echo pacer_min_sleep = 0.01ms
echo(
echo [cpp-ro]
echo type = http
echo url = http://127.0.0.1:3923/
echo headers = Cookie,cppwd=hunter2
echo pacer_min_sleep = 0.01ms
) > %userprofile%\.config\rclone\rclone.conf
```

also install the windows dependencies: [winfsp](https://github.com/billziss-gh/winfsp/releases/latest)


### on unix clients:
```
cat > ~/.config/rclone/rclone.conf <<'EOF'
[cpp-rw]
type = webdav
vendor = owncloud
url = http://127.0.0.1:3923/
headers = Cookie,cppwd=hunter2
pacer_min_sleep = 0.01ms

[cpp-ro]
type = http
url = http://127.0.0.1:3923/
headers = Cookie,cppwd=hunter2
pacer_min_sleep = 0.01ms
EOF
```


# mounting the copyparty server locally

connect to `cpp-rw:` for read-write, or `cpp-ro:` for read-only (twice as fast):

```
rclone.exe mount --vfs-cache-mode writes --vfs-cache-max-age 5s --attr-timeout 5s --dir-cache-time 5s cpp-rw: W:
```


# sync folders to/from copyparty

note that the up2k client [up2k.py](https://github.com/9001/copyparty/tree/hovudstraum/bin#up2kpy) (available on the "connect" page of your copyparty server) does uploads much faster and safer, but rclone is bidirectional and more ubiquitous

```
rclone sync /usr/share/icons/ cpp-rw:fds/
```


# use rclone as server too, replacing copyparty

feels out of place but is too good not to mention

```
rclone.exe serve http --read-only .
rclone.exe serve webdav .
```


# devnotes

copyparty supports and expects [the following](https://github.com/rclone/rclone/blob/46484022b08f8756050aa45505ea0db23e62df8b/backend/webdav/webdav.go#L575-L578) from rclone,

```go
case "owncloud":
    f.canStream = true
    f.precision = time.Second
    f.useOCMtime = true
    f.hasOCMD5 = true
    f.hasOCSHA1 = true
```

notably,
* `useOCMtime` enables the `x-oc-mtime` header to retain mtime of uploads from rclone
* `canStream` is supported but not required by us
* `hasOCMD5` / `hasOCSHA1` is conveniently dontcare on both ends

there's a scary comment mentioning PROPSET of lastmodified which is not something we wish to support

and if `vendor=owncloud` ever stops working, try `vendor=fastmail` instead
