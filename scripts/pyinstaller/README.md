builds a fully standalone copyparty.exe compatible with 32bit win7-sp1 and later

requires a win7 vm which has never been connected to the internet and a host-only network with the linux host at 192.168.123.1

first-time setup steps in notes.txt

run build.sh in the vm to fetch src + compile + push a new exe to the linux host for manual publishing


## ffmpeg

built with [ffmpeg-windows-build-helpers](https://github.com/rdp/ffmpeg-windows-build-helpers) and [this patch](./ffmpeg.patch) using [these steps](./ffmpeg.txt)
