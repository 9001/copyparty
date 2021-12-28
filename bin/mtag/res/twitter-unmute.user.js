// ==UserScript==
// @name         twitter-unmute
// @namespace    http://ocv.me/
// @version      0.1
// @description  memes
// @author       ed <irc.rizon.net>
// @match        https://twitter.com/*
// @icon         https://www.google.com/s2/favicons?domain=twitter.com
// @grant        GM_addStyle
// ==/UserScript==

function grunnur() {
    setInterval(function () {
        //document.querySelector('div[aria-label="Unmute"]').click();
        document.querySelector('video').muted = false;
    }, 200);
}

var scr = document.createElement('script');
scr.textContent = '(' + grunnur.toString() + ')();';
(document.head || document.getElementsByTagName('head')[0]).appendChild(scr);
