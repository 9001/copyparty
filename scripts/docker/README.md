copyparty is availabe in these repos:
* https://hub.docker.com/u/copyparty
* https://github.com/9001?tab=packages&repo_name=copyparty


# getting started

run this command to grab the latest copyparty image and start it:
```bash
docker run --rm -it -u 1000 -p 3923:3923 -v /mnt/nas:/w -v $PWD/cfgdir:/cfg copyparty/ac
```

* `/w` is the path inside the container that gets shared by default, so mount one or more folders to share below there
* `/cfg` is an optional folder with zero or more config files (*.conf) to load
* `copyparty/ac` is the recommended [image edition](#editions)
* you can download the image from github instead by replacing `copyparty/ac` with `ghcr.io/9001/copyparty-ac`
* if you are using rootless podman, remove `-u 1000`

i'm unfamiliar with docker-compose and alternatives so let me know if this section could be better 🙏


## configuration

the container has the same default config as the sfx and the pypi module, meaning it will listen on port 3923 and share the "current folder" (`/w` inside the container) as read-write for anyone

the recommended way to configure copyparty inside a container is to mount a folder which has one or more [config files](https://github.com/9001/copyparty/blob/hovudstraum/docs/example.conf) inside; `-v /your/config/folder:/cfg`

* but you can also provide arguments to the docker command if you prefer that
* config files must be named `something.conf` to get picked up


## editions

with image size after installation and when gzipped

* [`min`](https://hub.docker.com/r/copyparty/min) (57 MiB, 20 gz) is just copyparty itself
* [`im`](https://hub.docker.com/r/copyparty/im) (70 MiB, 25 gz) can thumbnail images with pillow, parse media files with mutagen
* [`ac` (163 MiB, 56 gz)](https://hub.docker.com/r/copyparty/ac) is `im` plus ffmpeg for video/audio thumbs + audio transcoding + better tags
* [`iv`](https://hub.docker.com/r/copyparty/iv) (211 MiB, 73 gz) is `ac` plus vips for faster heif / avic / jxl thumbnails
* [`dj`](https://hub.docker.com/r/copyparty/dj) (309 MiB, 104 gz) is `iv` plus beatroot/keyfinder to detect musical keys and bpm

[`ac` is recommended](https://hub.docker.com/r/copyparty/ac) since the additional features available in `iv` and `dj` are rarely useful

most editions support `x86`, `x86_64`, `armhf`, `aarch64`, `ppc64le`, `s390x`
* `dj` doesn't run on `ppc64le`, `s390x`, `armhf`
* `iv` doesn't run on `ppc64le`, `s390x`


## detecting bpm and musical key

the `dj` edition comes with `keyfinder` and `beatroot` which can be used to detect music bpm and musical keys

enable them globally in a config file:
```yaml
[global]
e2dsa, e2ts  # enable filesystem indexing and multimedia indexing
mtp: .bpm=f,t30,/mtag/audio-bpm.py  # should take ~10sec
mtp: key=f,t190,/mtag/audio-key.py  # should take ~50sec
```

or enable them for just one volume,
```yaml
[/music]  # share name / URL
  music   # filesystem path inside the docker volume `/w`
  flags:
    e2dsa, e2ts
    mtp: .bpm=f,t30,/mtag/audio-bpm.py
    mtp: key=f,t190,/mtag/audio-key.py
```

or using commandline arguments,
```
-e2dsa -e2ts -mtp .bpm=f,t30,/mtag/audio-bpm.py -mtp key=f,t190,/mtag/audio-key.py
```


# build the images yourself

basically `./make.sh hclean pull img push` but see [devnotes.md](./devnotes.md)


# notes

* currently unable to play [tracker music](https://en.wikipedia.org/wiki/Module_file) (mod/s3m/xm/it/...) -- will be fixed in june 2023 (Alpine 3.18)
