* do something cool

really tho, send a PR or an issue or whatever, all appreciated, anything goes, just behave aight 👍👍

but to be more specific,


# contribution ideas


## documentation

I think we can agree that the documentation leaves a LOT to be desired. I've realized I'm not exactly qualified for this 😅 but maybe the [soon-to-come setup GUI](https://github.com/9001/copyparty/issues/57) will make this more manageable. The best documentation is the one that never had to be written, right? :> so I suppose we can give this a wait-and-see approach for a bit longer.


## crazy ideas & features

assuming they won't cause too much problems or side-effects :> 

i think someone was working on a way to list directories over DNS for example...

if you wanna have a go at coding it up yourself then maybe mention the idea on discord before you get too far, otherwise just go nuts 👍


## others

aside from documentation and ideas, some other things that would be cool to have some help with is:

* **translations** -- the copyparty web-UI has translations for english and norwegian at the top of [browser.js](https://github.com/9001/copyparty/blob/hovudstraum/copyparty/web/browser.js); if you'd like to add a translation for another language then that'd be welcome! and if that language has a grammar that doesn't fit into the way the strings are assembled, then we'll fix that as we go :>

* **UI ideas** -- at some point I was thinking of rewriting the UI in react/preact/something-not-vanilla-javascript, but I'll admit the comfiness of not having any build stage combined with raw performance has kinda convinced me otherwise :p but I'd be very open to ideas on how the UI could be improved, or be more intuitive.

* **docker improvements** -- I don't really know what I'm doing when it comes to containers, so I'm sure there's a *huge* room for improvement here, mainly regarding how you're supposed to use the container with kubernetes / docker-compose / any of the other popular ways to do things. At some point I swear I'll start learning about docker so I can pick up clach04's [docker-compose draft](https://github.com/9001/copyparty/issues/38) and learn how that stuff ticks, unless someone beats me to it!

* **packaging** for various linux distributions -- this could either be as simple as just plopping the sfx.py in the right place and calling that from systemd (the archlinux package [originally did this](https://github.com/9001/copyparty/pull/18)); maybe with a small config-file which would cause copyparty to load settings from `/etc/copyparty.d` (like the [archlinux package](https://github.com/9001/copyparty/tree/hovudstraum/contrib/package/arch) does with `copyparty.conf`), or it could be a proper installation of the copyparty python package into /usr/lib or similar (the archlinux package [eventually went for this approach](https://github.com/9001/copyparty/pull/26))

  * [fpm](https://github.com/jordansissel/fpm) can probably help with the technical part of it, but someone needs to handle distro relations :-)

* **software integration** -- I'm sure there's a lot of usecases where copyparty could complement something else, or the other way around, so any ideas or any work in this regard would be dope. This doesn't necessarily have to be code inside copyparty itself;

  * [hooks](https://github.com/9001/copyparty/tree/hovudstraum/bin/hooks) -- these are small programs which are called by copyparty when certain things happen (files are uploaded, someone hits a 404, etc.), and could be a fun way to add support for more usecases

  * [parser plugins](https://github.com/9001/copyparty/tree/hovudstraum/bin/mtag) -- if you want to have copyparty analyze and index metadata for some oddball file-formats, then additional plugins would be neat :>
