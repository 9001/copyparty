standalone programs which take an audio file as argument

some of these rely on libraries which are not MIT-compatible

* [audio-bpm.py](./audio-bpm.py) detects the BPM of music using the BeatRoot Vamp Plugin; imports GPL2
* [audio-key.py](./audio-key.py) detects the melodic key of music using the Mixxx fork of keyfinder; imports GPL3


# dependencies

run [`install-deps.sh`](install-deps.sh) to build/install most dependencies required by these programs (supports windows/linux/macos)

*alternatively* (or preferably) use packages from your distro instead, then you'll need at least these:

* from distro: `numpy vamp-plugin-sdk beatroot-vamp mixxx-keyfinder ffmpeg`
* from pypy: `keyfinder vamp`


# usage from copyparty

`copyparty -e2dsa -e2ts -mtp key=f,audio-key.py -mtp .bpm=f,audio-bpm.py`

* `f,` makes the detected value replace any existing values
* the `.` in `.bpm` indicates numeric value
* assumes the python files are in the folder you're launching copyparty from, replace the filename with a relative/absolute path if that's not the case
* `mtp` modules will not run if a file has existing tags in the db, so clear out the tags with `-e2tsr` the first time you launch with new `mtp` options


## usage with volume-flags

instead of affecting all volumes, you can set the options for just one volume like so:
```
copyparty -v /mnt/nas/music:/music:r:cmtp=key=f,audio-key.py:cmtp=.bpm=f,audio-bpm.py:ce2dsa:ce2ts
```
