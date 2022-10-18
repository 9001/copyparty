### [`plugins/`](plugins/)
* example extensions

### [`copyparty.bat`](copyparty.bat)
* launches copyparty with no arguments (anon read+write within same folder)
* intended for windows machines with no python.exe in PATH
* works on windows, linux and macos
* assumes `copyparty-sfx.py` was renamed to `copyparty.py` in the same folder as `copyparty.bat`

### [`index.html`](index.html)
* drop-in redirect from an httpd to copyparty
* assumes the webserver and copyparty is running on the same server/IP
* modify `10.13.1.1` as necessary if you wish to support browsers without javascript

### [`sharex.sxcu`](sharex.sxcu)
* sharex config file to upload screenshots and grab the URL
* `RequestURL`: full URL to the target folder
* `pw`: password (remove the `pw` line if anon-write)

however if your copyparty is behind a reverse-proxy, you may want to use [`sharex-html.sxcu`](sharex-html.sxcu) instead:
* `RequestURL`: full URL to the target folder
* `URL`: full URL to the root folder (with trailing slash) followed by `$regex:1|1$`
* `pw`: password (remove `Parameters` if anon-write)

### [`media-osd-bgone.ps1`](media-osd-bgone.ps1)
* disables the [windows OSD popup](https://user-images.githubusercontent.com/241032/122821375-0e08df80-d2dd-11eb-9fd9-184e8aacf1d0.png) (the thing on the left) which appears every time you hit media hotkeys to adjust volume or change song while playing music with the copyparty web-ui, or most other audio players really

### [`explorer-nothumbs-nofoldertypes.reg`](explorer-nothumbs-nofoldertypes.reg)
* disables thumbnails and folder-type detection in windows explorer
* makes it way faster (especially for slow/networked locations (such as copyparty-fuse))

### [`webdav-basicauth.reg`](webdav-basicauth.reg)
* enables webdav basic-auth over plaintext http

### [`cfssl.sh`](cfssl.sh)
* creates CA and server certificates using cfssl
* give a 3rd argument to install it to your copyparty config
* systemd service at [`systemd/cfssl.service`](systemd/cfssl.service)

# OS integration
init-scripts to start copyparty as a service
* [`systemd/copyparty.service`](systemd/copyparty.service) runs the sfx normally
* [`rc/copyparty`](rc/copyparty) runs sfx normally on freebsd, create a `copyparty` user
* [`systemd/prisonparty.service`](systemd/prisonparty.service) runs the sfx in a chroot
* [`openrc/copyparty`](openrc/copyparty)

# Reverse-proxy
copyparty has basic support for running behind another webserver
* [`nginx/copyparty.conf`](nginx/copyparty.conf)
