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
* the `act:bput` thing is optional since copyparty v1.9.29
* using an older sharex version, maybe sharex v12.1.1 for example? dw fam i got your back 👉😎👉 [`sharex12.sxcu`](sharex12.sxcu)

### [`flameshot.sh`](flameshot.sh)
* takes a screenshot with [flameshot](https://flameshot.org/) on Linux, uploads it, and writes the URL to clipboard

### [`send-to-cpp.contextlet.json`](send-to-cpp.contextlet.json)
* browser integration, kind of? custom rightclick actions and stuff
* rightclick a pic and send it to copyparty straight from your browser
* for the [contextlet](https://addons.mozilla.org/en-US/firefox/addon/contextlets/) firefox extension

### [`media-osd-bgone.ps1`](media-osd-bgone.ps1)
* disables the [windows OSD popup](https://user-images.githubusercontent.com/241032/122821375-0e08df80-d2dd-11eb-9fd9-184e8aacf1d0.png) (the thing on the left) which appears every time you hit media hotkeys to adjust volume or change song while playing music with the copyparty web-ui, or most other audio players really

### [`explorer-nothumbs-nofoldertypes.reg`](explorer-nothumbs-nofoldertypes.reg)
* disables thumbnails and folder-type detection in windows explorer
* makes it way faster (especially for slow/networked locations (such as partyfuse))

### [`webdav-cfg.reg`](webdav-cfg.bat)
* improves the native webdav support in windows;
  * removes the 47.6 MiB filesize limit when downloading from webdav
  * optionally enables webdav basic-auth over plaintext http
  * optionally helps disable wpad, removing the 10sec latency

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
