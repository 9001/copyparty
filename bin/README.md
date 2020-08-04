# copyparty-fuse.py
* mount a copyparty server as a local filesystem (read-only)
* **supports Linux** -- expect `117 MiB/s` sequential read over wifi
* **supports Windows!** -- expect `87 MiB/s` sequential read over wifi
* **supports macos** -- expect `17 MiB/s` sequential read over wifi

to run this on windows you
* definitely need `msys2`
* probably need `dokany` or `winfsp`, not sure which #todo
* should do this `/mingw64/bin/python3 ./copyparty-fuse.py n: http://192.168.1.69:3923/`

# copyparty-fuse🅱️.py
* mount a copyparty server as a local filesystem (read-only)
* does the same thing except more correct, `samba` approves
* **supports Linux** -- expect `18 MiB/s` (wait what)
* **supports Macos** -- probably
