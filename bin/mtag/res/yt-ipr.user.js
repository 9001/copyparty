// ==UserScript==
// @name    youtube-playerdata-hub
// @match   https://youtube.com/*
// @match   https://*.youtube.com/*
// @version 1.0
// @grant   GM_addStyle
// ==/UserScript==

function main() {
    var server = 'https://127.0.0.1:3923/ytm?pw=wark',
        interval = 60; // sec

    var sent = {};
    function send(txt, mf_url, desc) {
        if (sent[mf_url])
            return;

        fetch(server + '&_=' + Date.now(), { method: "PUT", body: txt });
        console.log('[yt-pdh] yeet %d bytes, %s', txt.length, desc);
        sent[mf_url] = 1;
    }

    function collect() {
        setTimeout(collect, interval * 1000);
        try {
            var pd = document.querySelector('ytd-watch-flexy');
            if (!pd)
                return console.log('[yt-pdh] no video found');

            pd = pd.playerData;
            var mu = pd.streamingData.dashManifestUrl || pd.streamingData.hlsManifestUrl;
            if (!mu || !mu.length)
                return console.log('[yt-pdh] no manifest found');

            var desc = pd.videoDetails.videoId + ', ' + pd.videoDetails.title;
            send(JSON.stringify(pd), mu, desc);
        }
        catch (ex) {
            console.log("[yt-pdh]", ex);
        }
    }
    collect();
}

var scr = document.createElement('script');
scr.textContent = '(' + main.toString() + ')();';
(document.head || document.getElementsByTagName('head')[0]).appendChild(scr);
console.log('[yt-pdh] a');
