#!/usr/bin/env python3

import os
import sys

"""
generates a "tl.js" which can be used to prototype a new translation
without having to run from source, or tamper with the files that are
extracted from the sfx

to generate a tl.js for the language you are translating to,
run the following command:  python tl.py fra Français
("fra" being the three-letter language code of your language, and
 "Français" the native name of the language)

then copy tl.js into the webroot and run copyparty with the following:
  on Linux:    --html-head='<script src="/tl.js"></script>'
  on Windows:  "--html-head=<script src='/tl.js'></script>"

or in a copyparty config file:
[global]
  html-head: <script src="/tl.js"></script>

after editing tl.js, reload your webbrowser by pressing ctrl-shift-r
"""


#######################################################################
#######################################################################


def generate_javascript(lang3, native_name, tl_browser):
    note1 = ""
    note2 = ""
    if lang3 == "hmn":
        note1 = ';\n// please adjust this (and the "Ls.hmn" further down)'
        note2 = """
// the three-letter language-code "hmn" and language-name "Hymmnos"
// is used as an example; please replace these with your language
//"""

    return f""""use strict";


// the three-letter name of the language you're translating to{note1}
var my_lang = "{lang3}";


////////////////////////////////////////////////////////////////////////
// please ignore the next 5 lines:
var Ls={{}}, SR='', wah='';
function langmod() {{
	if (window.LANGN)
		LANGN.push([my_lang, Ls[my_lang].tt]);
}}


////////////////////////////////////////////////////////////////////////
// alright,
// below this point is where the actual translation happens;
// here is the pairs of "text-identifier": "text-to-translate"
//{note2}
// you do not need to translate the TLNotes, those are just for you :-)
//
// when you are happy with this translation and want to submit it,
// copy the text below into a new file in the translations folder;
// https://github.com/9001/copyparty/tree/hovudstraum/copyparty/web/tl


Ls.{lang3} = {{
	"tt": "{native_name}",
{tl_browser}

	"splash": {{
		"a1": "refresh",
		"b1": "howdy stranger &nbsp; <small>(you're not logged in)</small>",
		"c1": "logout",
		"d1": "dump stack",  // TLNote: "d2" is the tooltip for this button
		"d2": "shows the state of all active threads",
		"e1": "reload cfg",
		"e2": "reload config files (accounts/volumes/volflags),$Nand rescan all e2ds volumes$N$Nnote: any changes to global settings$Nrequire a full restart to take effect",
		"f1": "you can browse:",
		"g1": "you can upload to:",
		"cc1": "other stuff:",
		"h1": "disable k304",  // TLNote: "j1" explains what k304 is
		"i1": "enable k304",
		"j1": "enabling k304 will disconnect your client on every HTTP 304, which can prevent some buggy proxies from getting stuck (suddenly not loading pages), <em>but</em> it will also make things slower in general",
		"k1": "reset client settings",
		"l1": "login for more:",
		"m1": "welcome back,",  // TLNote: "welcome back, USERNAME"
		"n1": "404 not found &nbsp;┐( ´ -`)┌",
		"o1": 'or maybe you don\\'t have access -- try a password or <a href="' + SR + '/?h">go home</a>',
		"p1": "403 forbiddena &nbsp;~┻━┻",
		"q1": 'use a password or <a href="' + SR + '/?h">go home</a>',
		"r1": "go home",
		".s1": "rescan",
		"t1": "action",  // TLNote: this is the header above the "rescan" buttons
		"u2": "time since the last server write$N( upload / rename / ... )$N$N17d = 17 days$N1h23 = 1 hour 23 minutes$N4m56 = 4 minutes 56 seconds",
		"v1": "connect",
		"v2": "use this server as a local HDD",
		"w1": "switch to https",
		"x1": "change password",
		"y1": "edit shares",  // TLNote: shows the list of folders that the user has decided to share
		"z1": "unlock this share:",  // TLNote: the password prompt to see a hidden share
		"ta1": "fill in your new password first",
		"ta2": "repeat to confirm new password:",
		"ta3": "found a typo; please try again",
		"nop": "ERROR: Password cannot be blank",
		"nou": "ERROR: Username and/or password cannot be blank",
		"aa1": "incoming files:",
		"ab1": "disable no304",
		"ac1": "enable no304",
		"ad1": "enabling no304 will disable all caching; try this if k304 wasn't enough. This will waste a huge amount of network traffic!",
		"ae1": "active downloads:",
		"af1": "show recent uploads",
		"ag1": "view idp cache",  // TLNote: is a link to a page where IdP users can be managed
	}}
}};
"""


#######################################################################
#######################################################################


def die(*a):
    print(*a)
    sys.exit(1)


def main():
    webdir = "../copyparty/web/splash.js"

    while webdir and not os.path.exists(webdir):
        webdir = webdir.split("/", 1)[1]

    if not webdir:
        t = "could not find the copyparty/web/*.js files!\nplease cd into the copyparty repo before running this script"
        die(t)

    webdir = webdir.rsplit("/", 1)[0] if "/" in webdir else "."

    with open(os.path.join(webdir, "browser.js"), "rb") as f:
        browserjs = f.read().decode("utf-8")

    _, browserjs = browserjs.split('\n\t\t"tt": "English",\n', 1)
    browserjs, _ = browserjs.split("\n}", 1)
    browserjs = browserjs.replace("\n\t", "\n")

    try:
        lang3 = sys.argv[1]
    except:
        t = "you need to provide one more argument: the three-letter language code for the language you are translating to, for example: ger"
        die(t)

    try:
        native_name = sys.argv[2]
    except:
        t = "you need to provide one more argument: the native name of the language you are translating to, for example: Deutsch"
        die(t)

    ret = generate_javascript(lang3, native_name, browserjs)

    outpath = os.path.abspath("tl.js")
    if os.path.exists(outpath):
        t = "the output file already exists! if you really want to overwrite it, then delete the following file and try again:"
        die(t, outpath)

    with open(outpath, "wb") as f:
        f.write(ret.encode("utf-8"))

    print("successfully created", outpath)


if __name__ == "__main__":
    main()
