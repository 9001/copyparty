this file accidentally got committed at some point, so let's put it to use

# trivia / lore

copyparty started as [three separate php projects](https://a.ocv.me/pub/stuff/old-php-projects/); an nginx custom directory listing (which became a php script), and a php music/picture viewer, and an additional php project for resumable uploads:

* findex -- directory browser / gallery with thumbnails and a music player which sometime back in 2009 had a canvas visualizer grabbing fft data from a flash audio player
* findex.mini -- plain-listing fork of findex with streaming zip-download of folders (the js and design should look familiar)
* upper and up2k -- up2k being the star of the show and where copyparty's chunked resumable uploads came from

the first link has screenshots but if that doesn't work there's also a [tar here](https://ocv.me/dev/old-php-projects.tgz)

----

below this point is misc useless scribbles

# up2k.js

## potato detection

* tsk 0.25/8.4/31.5 bzw 1.27/22.9/18 = 77% (38.4s, 49.7s)
  * 4c locale #1313, ff-102,deb-11 @ ryzen4500u wifi -> win10
  * profiling shows 2sec heavy gc every 2sec

* tsk 0.41/4.1/10 bzw 1.41/9.9/7 = 73% (13.3s, 18.2s)
  * 4c locale #1313, ch-103,deb-11 @ ryzen4500u wifi -> win10
