// ==UserScript==
// @name    youtube-playerdata-hub
// @match   https://youtube.com/*
// @match   https://*.youtube.com/*
// @version 1.0
// @grant   GM_addStyle
// ==/UserScript==

function main() {
    var server = 'https://127.0.0.1:3923/ytm',
        interval = 60; // sec

    var sent = {};
    function send(txt, mf_url, desc) {
        if (sent[mf_url])
            return;

        fetch(server + '?_=' + Date.now(), { method: "PUT", body: txt });
        console.log('[yt-ipr] yeet %d bytes, %s', txt.length, desc);
        sent[mf_url] = 1;
    }

    function collect() {
        setTimeout(collect, interval * 1000);
        try {
            var pd = document.querySelector('ytd-watch-flexy').playerData,
                mu = pd.streamingData.dashManifestUrl || pd.streamingData.hlsManifestUrl,
                desc = pd.videoDetails.videoId + ', ' + pd.videoDetails.title;

            if (mu.length)
                send(JSON.stringify(pd), mu, desc);
        }
        catch (ex) {
            console.log("[yt-ipr]", ex);
        }
    }
    collect();
}

var scr = document.createElement('script');
scr.textContent = '(' + main.toString() + ')();';
(document.head || document.getElementsByTagName('head')[0]).appendChild(scr);
console.log('[yt-ipr] a');
