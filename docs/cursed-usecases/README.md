insane ways to use copyparty


## wireless keyboard

problem: you wanna control mpv or whatever software from the couch but you don't have a wireless keyboard

"solution": load some custom javascript which renders a virtual keyboard on the upload UI and each keystroke is actually an upload which gets picked up by a dummy metadata parser which forwards the keystrokes into xdotool

[no joke, this actually exists and it wasn't even my idea or handiwork (thx steen)](https://github.com/9001/copyparty/blob/hovudstraum/contrib/plugins/meadup.js)


## appxsvc tarpit

problem: `svchost.exe` is using 100% of a cpu core, and upon further inspection (`procmon`) it is `wsappx` desperately trying to install something, repeatedly reading a file named `AppxManifest.xml` and messing with an sqlite3 database

"solution": create a virtual filesystem which is intentionally slow and trick windows into reading it from there instead

* create a file called `AppxManifest.xml` and put something dumb in it
* serve the file from a copyparty instance with `--rsp-slp=1` so every request will hang for 1 sec
* `net use m: http://127.0.0.1:3993/`  (mount copyparty using the windows-native webdav client)
* `mklink /d c:\windows\systemapps\microsoftwindows.client.cbs_cw5n1h2txyewy\AppxManifest.xml m:\AppxManifest.xml`
