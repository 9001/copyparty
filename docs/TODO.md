a living list of upcoming features / fixes / changes, very roughly in order of priority

* ensure continuous music playback on android w/ unreliable network
  * playback stops if preload doesn't finish before end of current track, but suspiciously resumes when phone is unsuspended and browser gets focus... preloading earlier is a band-aid; some filler / comfortnoise probably better, but the browser probably requires the play-action to be chained from an end-of-track event... maybe make two audio objects (wn1/wn2) with ≈2sec audio and eot-hop between them until au2 is ready, maybe assembled at runtime by repeating an mp3 frame (b64 is a bit sus)

* download accelerator
  * definitely download chunks in parallel
  * maybe resumable downloads (chrome-only, jank api)
  * maybe checksum validation (return sha512 of requested range in responses, and probably also warks)

* [github issue #64](https://github.com/9001/copyparty/issues/64) - dirkeys 2nd season
  * popular feature request, finally time to refactor browser.js i suppose...

* [github issue #37](https://github.com/9001/copyparty/issues/37) - upload PWA
  * or [maybe not](https://arstechnica.com/tech-policy/2024/02/apple-under-fire-for-disabling-iphone-web-apps-eu-asks-developers-to-weigh-in/), or [maybe](https://arstechnica.com/gadgets/2024/03/apple-changes-course-will-keep-iphone-eu-web-apps-how-they-are-in-ios-17-4/)

* [github issue #57](https://github.com/9001/copyparty/issues/57) - config GUI
  * configs given to -c can be ordered with numerical prefix
  * autorevert settings if it fails to apply
  * countdown until session invalidates in settings gui, with refresh-button

