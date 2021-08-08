// ==UserScript==
// @name    youtube-playerdata-hub
// @match   https://youtube.com/*
// @match   https://*.youtube.com/*
// @version 1.0
// @grant   GM_addStyle
// ==/UserScript==

function main() {
    var sent = {};
    function send(txt) {
        if (sent[txt])
            return;

        fetch('https://127.0.0.1:3923/playerdata?_=' + Date.now(), { method: "PUT", body: txt });
        console.log('[yt-ipr] yeet %d bytes', txt.length);
        sent[txt] = 1;
    }

    function collect() {
        setTimeout(collect, 60 * 1000);
        var pd = document.querySelector('ytd-watch-flexy');
        if (pd)
            send(JSON.stringify(pd.playerData));
    }
    setTimeout(collect, 5000);
}

var scr = document.createElement('script');
scr.textContent = '(' + main.toString() + ')();';
(document.head || document.getElementsByTagName('head')[0]).appendChild(scr);
console.log('[yt-ipr] a');
