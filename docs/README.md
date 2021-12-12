**NOTE:** there's more stuff (sharex config, service scripts, nginx configs, ...) in [`/contrib/`](/contrib/)



# example resource files

can be provided to copyparty to tweak things



## example `.epilogue.html`
save one of these as `.epilogue.html` inside a folder to customize it:

* [`minimal-up2k.html`](minimal-up2k.html) will [simplify the upload ui](https://user-images.githubusercontent.com/241032/118311195-dd6ca380-b4ef-11eb-86f3-75a3ff2e1332.png)



## example browser-css
point `--css-browser` to one of these by URL:

* [`browser.css`](browser.css) changes the background
* [`browser-icons.css`](browser-icons.css) adds filetype icons



# utilities

## [`multisearch.html`](multisearch.html)
* takes a list of filenames of youtube rips, grabs the youtube-id of each file, and does a search on the server for those
* use it by putting it somewhere on the server and opening it as an html page
* also serves as an extendable template for other specific search behaviors



# other stuff

## [`rclone.md`](rclone.md)
* notes on using rclone as a fuse client/server

## [`example.conf`](example.conf)
* example config file for `-c`



# junk

alphabetical list of the remaining files

| what | why |
| -- | -- |
| [biquad.html](biquad.html) | bruteforce calibrator for the audio equalizer since im not that good at maths |
| [design.txt](design.txt) | initial brainstorming of the copyparty design, unmaintained, incorrect, sentimental value only |
| [hls.html](hls.html) | experimenting with hls playback using `hls.js`, works p well, almost became a thing |
| [music-analysis.sh](music-analysis.sh) | testing various bpm/key detection libraries before settling on the ones used in [`/bin/mtag/`](/bin/mtag/) |
| [notes.sh](notes.sh) | notepad, just scraps really |
| [nuitka.txt](nuitka.txt) | how to build a copyparty exe using nuitka (not maintained) |
| [pretend-youre-qnap.patch](pretend-youre-qnap.patch) | simulate a NAS which keeps returning old cached data even though you just modified the file yourself |
| [tcp-debug.sh](tcp-debug.sh) | looks like this was to debug stuck tcp connections? |
| [unirange.py](unirange.py) | uhh |
| [up2k.txt](up2k.txt) | initial ideas for how up2k should work, another unmaintained sentimental-value-only thing |
