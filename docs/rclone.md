# using rclone to mount a remote copyparty server as a local filesystem

speed estimates with server and client on the same win10 machine:
* `1070 MiB/s` with rclone as both server and client
* `570 MiB/s` with rclone-client and `copyparty -ed -j16` as server
* `220 MiB/s` with rclone-client and `copyparty -ed` as server
* `100 MiB/s` with [../bin/copyparty-fuse.py](../bin/copyparty-fuse.py) as client

when server is on another machine (1gbit LAN),
* `75 MiB/s` with [../bin/copyparty-fuse.py](../bin/copyparty-fuse.py) as client
* `92 MiB/s` with rclone-client and `copyparty -ed` as server
* `103 MiB/s` (connection max) with `copyparty -ed -j16` and all the others


# creating the config file

replace `hunter2` with your password, or remove the `hunter2` lines if you allow anonymous access


### on windows clients:
```
(
echo [cpp-rw]
echo type = webdav
echo vendor = other
echo url = http://127.0.0.1:3923/
echo headers = Cookie,cppwd=hunter2
echo(
echo [cpp-ro]
echo type = http
echo url = http://127.0.0.1:3923/
echo headers = Cookie,cppwd=hunter2
) > %userprofile%\.config\rclone\rclone.conf
```

also install the windows dependencies: [winfsp](https://github.com/billziss-gh/winfsp/releases/latest)


### on unix clients:
```
cat > ~/.config/rclone/rclone.conf <<'EOF'
[cpp-rw]
type = webdav
vendor = other
url = http://127.0.0.1:3923/
headers = Cookie,cppwd=hunter2

[cpp-ro]
type = http
url = http://127.0.0.1:3923/
headers = Cookie,cppwd=hunter2
EOF
```


# mounting the copyparty server locally

connect to `cpp-rw:` for read-write, or `cpp-ro:` for read-only (twice as fast):

```
rclone.exe mount --vfs-cache-mode writes --vfs-cache-max-age 5s --attr-timeout 5s --dir-cache-time 5s cpp-rw: W:
```


# use rclone as server too, replacing copyparty

feels out of place but is too good not to mention

```
rclone.exe serve http --read-only .
rclone.exe serve webdav .
```
