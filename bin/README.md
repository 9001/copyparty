# [`copyparty-fuse.py`](copyparty-fuse.py)
* mount a copyparty server as a local filesystem (read-only)
* **supports Windows!** -- expect `194 MiB/s` sequential read
* **supports Linux** -- expect `117 MiB/s` sequential read
* **supports macos** -- expect `85 MiB/s` sequential read

filecache is default-on for windows and macos;
* macos readsize is 64kB, so speed ~32 MiB/s without the cache
* windows readsize varies by software; explorer=1M, pv=32k

note that copyparty should run with `-ed` to enable dotfiles (hidden otherwise)

also consider using [../docs/rclone.md](../docs/rclone.md) instead for 5x performance


## to run this on windows:
* install [winfsp](https://github.com/billziss-gh/winfsp/releases/latest) and [python 3](https://www.python.org/downloads/)
  * [x] add python 3.x to PATH (it asks during install)
* `python -m pip install --user fusepy`
* `python ./copyparty-fuse.py n: http://192.168.1.69:3923/`

10% faster in [msys2](https://www.msys2.org/), 700% faster if debug prints are enabled:
* `pacman -S mingw64/mingw-w64-x86_64-python{,-pip}`
* `/mingw64/bin/python3 -m pip install --user fusepy`
* `/mingw64/bin/python3 ./copyparty-fuse.py [...]`

you could replace winfsp with [dokan](https://github.com/dokan-dev/dokany/releases/latest), let me know if you [figure out how](https://github.com/dokan-dev/dokany/wiki/FUSE)  
(winfsp's sshfs leaks, doesn't look like winfsp itself does, should be fine)



# [`copyparty-fuse🅱️.py`](copyparty-fuseb.py)
* mount a copyparty server as a local filesystem (read-only)
* does the same thing except more correct, `samba` approves
* **supports Linux** -- expect `18 MiB/s` (wait what)
* **supports Macos** -- probably



# [`copyparty-fuse-streaming.py`](copyparty-fuse-streaming.py)
* pretend this doesn't exist



# [`mtag/`](mtag/)
* standalone programs which perform misc. file analysis
* copyparty can soon Popen programs like these during file indexing to collect additional metadata
