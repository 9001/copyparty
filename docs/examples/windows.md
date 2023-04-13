# running copyparty on windows

this is a complete example / quickstart for running copyparty on windows, optionally as a service (autostart on boot)

you will definitely need either [copyparty.exe](https://github.com/9001/copyparty/releases/latest/download/copyparty.exe) (comfy, portable, more features) or [copyparty-sfx.py](https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py) (smaller, safer)

* if you decided to grab `copyparty-sfx.py` instead of the exe you will also need to install the ["Latest Python 3 Release"](https://www.python.org/downloads/windows/)

then you probably want to download [FFmpeg](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip) and put `ffmpeg.exe` and `ffprobe.exe` in your PATH (so for example `C:\Windows\System32\`) -- this enables thumbnails, audio transcoding, and making music metadata searchable


## the config file

open up notepad and save the following as `c:\users\you\documents\party.conf` (for example)

```yaml
[global]
  lo: c:\users\you\logs\cpp-%Y-%m%d.xz  # log to file
  e2dsa, e2ts, no-dedup, z   # sets 4 flags; see expl.
  p: 80, 443  # listen on ports 80 and 443, not 3923
  theme: 2    # default theme: protonmail-monokai
  lang: nor   # default language: viking

[accounts]                  # usernames and passwords
  kevin: shangalabangala    # kevin's password

[/]               # create a volume available at /
  c:\pub          # sharing this filesystem location
  accs:           # and set permissions:
    r: *          # everyone can read/download files,
    rwmd: kevin   # kevin can read/write/move/delete

[/inc]            # create another volume at /inc
  c:\pub\inc      # sharing this filesystem location
  accs:           # permissions:
    w: *          # everyone can upload, but not browse
    rwmd: kevin   # kevin is admin here too

[/music]          # and a third volume at /music
  ~/music         # which shares c:\users\you\music
  accs:
    r: *
    rwmd: kevin
```


### config explained: [global]

the `[global]` section accepts any config parameters you can see when running copyparty (either the exe or the sfx.py) with `--help`, so this is the same as running copyparty with arguments `--lo c:\users\you\logs\copyparty-%Y-%m%d.xz -e2dsa -e2ts --no-dedup -z -p 80,443 --theme 2 --lang nor`
* `lo: c:\users\you\logs\cpp-%Y-%m%d.xz` writes compressed logs (the compression will make them delayed)
  * sorry that `~/logs/` doesn't work currently, good oversight
* `e2dsa` enables the upload deduplicator and file indexer, which enables searching
* `e2ts` enables music metadata indexing, making albums / titles etc. searchable too
* `no-dedup` writes full dupes to disk instead of symlinking, since lots of windows software doesn't handle symlinks well
  * but the improved upload speed from `e2dsa` is not affected
* `z` enables zeroconf, making the server available at `http://HOSTNAME.local/` from any other machine in the LAN
* `p: 80,443` listens on the ports `80` and `443` instead of the default `3923`
* `lang: nor` sets default language to viking


### config explained: [accounts]

the `[accounts]` section defines all the user accounts, which can then be referenced when granting people access to the different volumes


### config explained: volumes

then we create three volumes, one at `/`, one at `/inc`, and one at `/music`
* `/` and `/music` are readable without requiring people to login (`r: *`) but you need to login as kevin to write/move/delete files (`rwmd: kevin`)
* anyone can upload to `/inc` but you must be logged in as kevin to see the files inside


## run copyparty

to test your config it's best to just run copyparty in a console to watch the output:

```batch
copyparty.exe -c party.conf
```

or if you wanna use `copyparty-sfx.py` instead of the exe (understandable),

```batch
%localappdata%\programs\python\python311\python.exe copyparty-sfx.py -c party.conf
```

(please adjust `python311` to match the python version you installed, i'm not good enough at windows to make that bit generic)


## run it as a service

to run this as a service you need [NSSM](https://nssm.cc/ci/nssm-2.24-101-g897c7ad.zip), so put the exe somewhere in your PATH

then either do this for `copyparty.exe`:
```batch
nssm install cpp %homedrive%%homepath%\downloads\copyparty.exe -c %homedrive%%homepath%\documents\party.conf
```

or do this for `copyparty-sfx.py`:
```batch
nssm install cpp %localappdata%\programs\python\python311\python.exe %homedrive%%homepath%\downloads\copyparty-sfx.py -c %homedrive%%homepath%\documents\party.conf
```

then after creating the service, modify it so it runs with your own windows account (so file permissions don't get wonky and paths expand as expected):
```batch
nssm set cpp ObjectName .\yourAccoutName yourWindowsPassword
nssm start cpp
```

and that's it, all good

if it doesn't start, enable stderr logging so you can see what went wrong:
```batch
nssm set cpp AppStderr %homedrive%%homepath%\logs\cppsvc.err
nssm set cpp AppStderrCreationDisposition 2
```
