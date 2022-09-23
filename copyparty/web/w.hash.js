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
    gc1, gc2, gc3,
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
            // chrome gc forgets the filereader output; remind it
            // (for some chromes, also necessary for subtle)
            gc1 = e.target.result;
            gc2 = new Uint8Array(gc1, 0, 1);
            gc3 = new Uint8Array(gc1, gc1.byteLength - 1);

            //console.log('[ w] %d HASH bgin', nchunk);
            postMessage(["read", nchunk, cdr - car, Date.now() - t0]);
            hash_calc(gc1);
        }
        catch (ex) {
            busy = false;
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
    reader.readAsArrayBuffer(fobj.slice(car, cdr));


    var hash_calc = function (buf) {
        var hash_done = function (hashbuf) {
            // stop gc from attempting to free early
            if (!gc1 || !gc2 || !gc3)
                return console.log('torch went out');

            gc1 = gc2 = gc3 = null;
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

        // stop gc from attempting to free early
        if (!gc1 || !gc2 || !gc3)
            console.log('torch went out');

        if (subtle)
            subtle.digest('SHA-512', buf).then(hash_done);
        else {
            // note: lifting u8buf counterproductive for the chrome gc bug
            var u8buf = new Uint8Array(buf);
            hashwasm.sha512(u8buf).then(function (v) {
                hash_done(hex2u8(v))
            });
        }
    };
}
