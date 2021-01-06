### [`copyparty.bat`](copyparty.bat)
* launches copyparty with no arguments (anon read+write within same folder)
* intended for windows machines with no python.exe in PATH
* works on windows, linux and macos
* assumes `copyparty-sfx.py` was renamed to `copyparty.py` in the same folder as `copyparty.bat`

### [`index.html`](index.html)
* drop-in redirect from an httpd to copyparty
* assumes the webserver and copyparty is running on the same server/IP
* modify `10.13.1.1` as necessary if you wish to support browsers without javascript

### [`explorer-nothumbs-nofoldertypes.reg`](explorer-nothumbs-nofoldertypes.reg)
disables thumbnails and folder-type detection in windows explorer, makes it way faster (especially for slow/networked locations (such as copyparty-fuse))

# OS integration
init-scripts to start copyparty as a service
* [`systemd/copyparty.service`](systemd/copyparty.service)
* [`openrc/copyparty`](openrc/copyparty)

# Reverse-proxy
copyparty has basic support for running behind another webserver
* [`nginx/copyparty.conf`](nginx/copyparty.conf)
