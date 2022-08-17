"use strict";


function hex2u8(txt) {
    return new Uint8Array(txt.match(/.{2}/g).map(function (b) { return parseInt(b, 16); }));
}


var subtle = null;
try {
    subtle = crypto.subtle;
    subtle.digest('SHA-512', new Uint8Array(1)).then(
        function (x) { },
        function (x) { load_fb(); }
    );
}
catch (ex) {
    load_fb();
}
function load_fb() {
    subtle = null;
    importScripts('/.cpr/deps/sha512.hw.js');
}


var reader = null,
    busy = false;


onmessage = (d) => {
    if (busy)
        return postMessage(["panic", 'worker got another task while busy']);

    if (!reader)
        reader = new FileReader();

    var [nchunk, fobj, car, cdr] = d.data,
        t0 = Date.now();

    reader.onload = function (e) {
        try {
            //console.log('[ w] %d HASH bgin', nchunk);
            postMessage(["read", nchunk, cdr - car, Date.now() - t0]);
            hash_calc(e.target.result);
        }
        catch (ex) {
            postMessage(["panic", ex + '']);
        }
    };
    reader.onerror = function () {
        busy = false;
        var err = reader.error + '';

        if (err.indexOf('NotReadableError') !== -1 || // win10-chrome defender
            err.indexOf('NotFoundError') !== -1  // macos-firefox permissions
        )
            return postMessage(["fail", 'OS-error', err + ' @ ' + car]);

        postMessage(["ferr", err]);
    };
    //console.log('[ w] %d read bgin', nchunk);
    busy = true;
    reader.readAsArrayBuffer(
        File.prototype.slice.call(fobj, car, cdr));


    var hash_calc = function (buf) {
        var hash_done = function (hashbuf) {
            busy = false;
            try {
                var hslice = new Uint8Array(hashbuf).subarray(0, 33);
                //console.log('[ w] %d HASH DONE', nchunk);
                postMessage(["done", nchunk, hslice, cdr - car]);
            }
            catch (ex) {
                postMessage(["panic", ex + '']);
            }
        };

        if (subtle)
            subtle.digest('SHA-512', buf).then(hash_done);
        else {
            var u8buf = new Uint8Array(buf);
            hashwasm.sha512(u8buf).then(function (v) {
                hash_done(hex2u8(v))
            });
        }
    };
}
