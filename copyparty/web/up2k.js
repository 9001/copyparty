"use strict";

// error handler for mobile devices
function hcroak(msg) {
    document.body.innerHTML = msg;
    window.onerror = undefined;
    throw 'fatal_err';
}
function croak(msg) {
    document.body.textContent = msg;
    window.onerror = undefined;
    throw msg;
}
function esc(txt) {
    return txt.replace(/[&"<>]/g, function (c) {
        return {
            '&': '&amp;',
            '"': '&quot;',
            '<': '&lt;',
            '>': '&gt;'
        }[c];
    });
}
window.onerror = function (msg, url, lineNo, columnNo, error) {
    window.onerror = undefined;
    var html = ['<h1>you hit a bug!</h1><p>please screenshot this error and send me a copy arigathanks gozaimuch (ed/irc.rizon.net or ed#2644)</p><p>',
        esc(String(msg)), '</p><p>', esc(url + ' @' + lineNo + ':' + columnNo), '</p>'];

    if (error) {
        var find = ['desc', 'stack', 'trace'];
        for (var a = 0; a < find.length; a++)
            if (String(error[find[a]]) !== 'undefined')
                html.push('<h2>' + find[a] + '</h2>' +
                    esc(String(error[find[a]])).replace(/\n/g, '<br />\n'));
    }
    document.body.style.fontSize = '0.8em';
    hcroak(html.join('\n'));
};

function o(id) {
    return document.getElementById(id);
}

(function () {
    // hide basic uploader
    o('up2k').style.display = 'block';
    o('bup').style.display = 'none';

    // upload ui hidden by default, clicking the header shows it
    o('u2tgl').onclick = function (e) {
        e.preventDefault();
        o('u2tgl').style.display = 'none';
        o('u2body').style.display = 'block';
    };

    // shows or clears an error message in the basic uploader ui
    function setmsg(msg) {
        if (msg !== undefined) {
            o('u2err').setAttribute('class', 'err');
            o('u2err').innerHTML = msg;
        }
        else {
            o('u2err').setAttribute('class', '');
            o('u2err').innerHTML = '';
        }
    }

    // switches to the basic uploader with msg as error message
    function un2k(msg) {
        o('up2k').style.display = 'none';
        o('bup').style.display = 'block';
        setmsg(msg);
    }

    // handle user intent to use the basic uploader instead
    o('u2nope').onclick = function (e) {
        e.preventDefault();
        un2k();
    };

    if (!String.prototype.format) {
        String.prototype.format = function () {
            var args = arguments;
            return this.replace(/{(\d+)}/g, function (match, number) {
                return typeof args[number] != 'undefined' ?
                    args[number] : match;
            });
        };
    }

    function cfg(name) {
        var val = localStorage.getItem(name);
        if (val === null)
            return parseInt(o(name).value);

        o(name).value = val
        return val;
    }

    var parallel_uploads = cfg('nthread');
    var chunksize_mb = cfg('chunksz');
    var chunksize = chunksize_mb * 1024 * 1024;

    var col_hashing = '#0099ff'; //'#d7d7d7';
    //var col_hashed    = '#e8a6df'; //'#decb7f';
    //var col_hashed    = '#0099ff';
    var col_hashed = '#eeeeee';
    var col_uploading = '#ffcc44';
    var col_uploaded = '#00cc00';
    var fdom_ctr = 0;
    var st = {
        "files": [],
        "todo": {
            "hash": [],
            "handshake": [],
            "upload": []
        },
        "busy": {
            "hash": [],
            "handshake": [],
            "upload": []
        }
    };

    var bobslice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice;
    var have_crypto = window.crypto && crypto.subtle && crypto.subtle.digest;

    if (!bobslice || !window.FileReader || !window.FileList || !have_crypto)
        return un2k("this is the basic uploader; the good one needs at least<br />chrome 37 // firefox 34 // edge 12 // opera 24 // safari 7");

    function nav() {
        o('file' + fdom_ctr).click();
    }
    o('u2btn').addEventListener('click', nav, false);

    function ondrag(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        ev.dataTransfer.dropEffect = 'copy';
        ev.dataTransfer.effectAllowed = 'copy';
    }
    o('u2btn').addEventListener('dragover', ondrag, false);
    o('u2btn').addEventListener('dragenter', ondrag, false);

    function gotfile(ev) {
        ev.stopPropagation();
        ev.preventDefault();

        var files = ev.dataTransfer ?
            ev.dataTransfer.files : ev.target.files;

        if (files.length == 0)
            return alert('no files selected??');

        more_one_file();
        for (var a = 0; a < files.length; a++) {
            var fobj = files[a];
            var entry = {
                "n": parseInt(st.files.length.toString()),
                "fobj": fobj,
                "name": fobj.name,
                "size": fobj.size,
                "hash": []
            };

            var skip = false;
            for (var b = 0; b < st.files.length; b++)
                if (entry.name == st.files[b].name &&
                    entry.size == st.files[b].size)
                    skip = true;

            if (skip)
                continue;

            var tr = document.createElement('tr');
            tr.innerHTML = '<td></td><td id="f{0}t">hashing</td><td id="f{0}p" class="prog"></td>'.format(st.files.length);
            tr.getElementsByTagName('td')[0].textContent = entry.name;
            o('u2tab').appendChild(tr);

            st.files.push(entry);
            st.todo.hash.push(entry);
        }
    }
    o('u2btn').addEventListener('drop', gotfile, false);

    function more_one_file() {
        fdom_ctr++;
        var elm = document.createElement('div')
        elm.innerHTML = '<input id="file{0}" type="file" name="file{0}[]" multiple="multiple" />'.format(fdom_ctr);
        o('u2form').appendChild(elm);
        o('file' + fdom_ctr).addEventListener('change', gotfile, false);
    }
    more_one_file();

    /////
    ////
    ///   actuator
    //

    function boss() {
        if (st.todo.hash.length > 0 &&
            st.busy.hash.length == 0)
            exec_hash();

        if (st.todo.handshake.length > 0 &&
            st.busy.handshake.length == 0 &&
            st.busy.upload.length < parallel_uploads)
            exec_handshake();

        if (st.todo.upload.length > 0 &&
            st.busy.upload.length < parallel_uploads)
            exec_upload();

        setTimeout(boss, 100);
    }
    boss();

    /////
    ////
    ///   hashing
    //

    // https://gist.github.com/jonleighton/958841
    function buf2b64_maybe_fucky(buffer) {
        var ret = '';
        var view = new DataView(buffer);
        for (var i = 0; i < view.byteLength; i++) {
            ret += String.fromCharCode(view.getUint8(i));
        }
        return window.btoa(ret).replace(
            /\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }

    // https://gist.github.com/jonleighton/958841
    function buf2b64(arrayBuffer) {
        var base64 = '';
        var encodings = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
        var bytes = new Uint8Array(arrayBuffer);
        var byteLength = bytes.byteLength;
        var byteRemainder = byteLength % 3;
        var mainLength = byteLength - byteRemainder;
        var a, b, c, d;
        var chunk;

        for (var i = 0; i < mainLength; i = i + 3) {
            chunk = (bytes[i] << 16) | (bytes[i + 1] << 8) | bytes[i + 2];
            // create 8*3=24bit segment then split into 6bit segments
            a = (chunk & 16515072) >> 18; // 16515072 = (2^6 - 1) << 18
            b = (chunk & 258048) >> 12; // 258048   = (2^6 - 1) << 12
            c = (chunk & 4032) >> 6; // 4032     = (2^6 - 1) << 6
            d = chunk & 63;               // 63       = 2^6 - 1

            // Convert the raw binary segments to the appropriate ASCII encoding
            base64 += encodings[a] + encodings[b] + encodings[c] + encodings[d];
        }

        if (byteRemainder == 1) {
            chunk = bytes[mainLength];
            a = (chunk & 252) >> 2; // 252 = (2^6 - 1) << 2
            b = (chunk & 3) << 4; // 3   = 2^2 - 1  (zero 4 LSB)
            base64 += encodings[a] + encodings[b];//+ '==';
        }
        else if (byteRemainder == 2) {
            chunk = (bytes[mainLength] << 8) | bytes[mainLength + 1];
            a = (chunk & 64512) >> 10; // 64512 = (2^6 - 1) << 10
            b = (chunk & 1008) >> 4; // 1008  = (2^6 - 1) << 4
            c = (chunk & 15) << 2; // 15    = 2^4 - 1  (zero 2 LSB)
            base64 += encodings[a] + encodings[b] + encodings[c];//+ '=';
        }

        return base64;
    }

    // https://developer.mozilla.org/en-US/docs/Web/API/SubtleCrypto/digest
    function buf2hex(buffer) {
        var hexCodes = [];
        var view = new DataView(buffer);
        for (var i = 0; i < view.byteLength; i += 4) {
            var value = view.getUint32(i) // 4 bytes per iter
            var stringValue = value.toString(16) // doesn't pad
            var padding = '00000000'
            var paddedValue = (padding + stringValue).slice(-padding.length)
            hexCodes.push(paddedValue);
        }
        return hexCodes.join("");
    }

    function exec_hash() {
        var t = st.todo.hash.shift();
        st.busy.hash.push(t);

        var nchunks = Math.ceil(t.size / chunksize);
        var nchunk = 0;

        var pb_html = '';
        var pb_perc = 99.9 / nchunks;
        for (var a = 0; a < nchunks; a++)
            pb_html += '<div id="f{0}p{1}" style="width:{2}%"><div></div></div>'.format(
                t.n, a, pb_perc);

        o('f{0}p'.format(t.n)).innerHTML = pb_html;

        var segm_next = function () {
            var reader = new FileReader();
            reader.onload = segm_load;
            reader.onerror = segm_err;

            var car = nchunk * chunksize;
            var cdr = car + chunksize;
            if (cdr >= t.size)
                cdr = t.size;

            reader.readAsArrayBuffer(
                bobslice.call(t.fobj, car, cdr));

            prog(t.n, nchunk, col_hashing);
        };

        var segm_load = async function (ev) {
            const hashbuf = await crypto.subtle.digest('SHA-256', ev.target.result);
            t.hash.push(buf2b64(hashbuf));

            prog(t.n, nchunk, col_hashed);
            if (++nchunk < nchunks) {
                prog(t.n, nchunk, col_hashing);
                return segm_next();
            }

            o('f{0}t'.format(t.n)).innerHTML = 'connecting';
            st.busy.hash.splice(st.busy.hash.indexOf(t), 1);
            st.todo.handshake.push(t);
        };

        var segm_err = function () {
            alert('y o u   b r o k e    i t\n\n(was that a folder? just files please)');
        };

        segm_next();
    }

    /////
    ////
    ///   handshake
    //

    function exec_handshake() {
        var t = st.todo.handshake.shift();
        st.busy.handshake.push(t);

        var xhr = new XMLHttpRequest();
        xhr.onload = function (ev) {
            if (xhr.status == 200) {
                t.postlist = [];
                t.wark = xhr.response.wark;
                var missing = xhr.response.hash;
                for (var a = 0; a < missing.length; a++) {
                    var idx = t.hash.indexOf(missing[a]);
                    if (idx < 0)
                        return alert('wtf negative index for hash "{0}" in task:\n{1}'.format(
                            missing[a], JSON.stringify(t)));

                    t.postlist.push(idx);
                }
                for (var a = 0; a < t.hash.length; a++)
                    prog(t.n, a, (t.postlist.indexOf(a) == -1)
                        ? col_uploaded : col_hashed);

                var msg = 'completed';
                if (t.postlist.length > 0) {
                    for (var a = 0; a < t.postlist.length; a++)
                        st.todo.upload.push({
                            'nfile': t.n,
                            'npart': t.postlist[a]
                        });

                    msg = 'uploading';
                }
                o('f{0}t'.format(t.n)).innerHTML = msg;
                st.busy.handshake.splice(st.busy.handshake.indexOf(t), 1);
            }
            else
                alert("server broke (error {0}):\n\"{1}\"\n".format(
                    xhr.status, (xhr.response && xhr.response.err) ||
                    "no further information"));
        };
        xhr.open('POST', 'handshake.php', true);
        xhr.responseType = 'json';
        xhr.send(JSON.stringify({
            "name": t.name,
            "size": t.size,
            "hash": t.hash
        }));
    }

    /////
    ////
    ///   upload
    //

    function exec_upload() {
        var upt = st.todo.upload.shift();
        st.busy.upload.push(upt);

        var npart = upt.npart;
        var t = st.files[upt.nfile];

        prog(t.n, npart, col_uploading);

        var car = npart * chunksize;
        var cdr = car + chunksize;
        if (cdr >= t.size)
            cdr = t.size;

        var reader = new FileReader();

        reader.onerror = function () {
            alert('y o u   b r o k e    i t\n\n(was that a folder? just files please)');
        };

        reader.onload = function (ev) {
            var xhr = new XMLHttpRequest();
            xhr.upload.onprogress = function (xev) {
                var perc = xev.loaded / (cdr - car) * 100;
                prog(t.n, npart, '', perc);
            };
            xhr.onload = function (xev) {
                if (xhr.status == 200) {
                    prog(t.n, npart, col_uploaded);
                    st.busy.upload.splice(st.busy.upload.indexOf(upt), 1);
                    t.postlist.splice(t.postlist.indexOf(npart), 1);
                    if (t.postlist.length == 0) {
                        o('f{0}t'.format(t.n)).innerHTML = 'verifying';
                        st.todo.handshake.push(t);
                    }
                }
                else
                    alert("server broke (error {0}):\n\"{1}\"\n".format(
                        xhr.status, (xhr.response && xhr.response.err) ||
                        "no further information"));
            };
            xhr.open('POST', 'chunkpit.php', true);
            //xhr.setRequestHeader("X-Up2k-Hash", t.hash[npart].substr(1) + "x");
            xhr.setRequestHeader("X-Up2k-Hash", t.hash[npart]);
            xhr.setRequestHeader("X-Up2k-Wark", t.wark);
            xhr.setRequestHeader('Content-Type', 'application/octet-stream');
            xhr.overrideMimeType('Content-Type', 'application/octet-stream');
            xhr.responseType = 'json';
            xhr.send(ev.target.result);
        };

        reader.readAsArrayBuffer(bobslice.call(t.fobj, car, cdr));
    }

    /////
    ////
    ///   progress bar
    //

    function prog(nfile, nchunk, color, percent) {
        var n1 = o('f{0}p{1}'.format(nfile, nchunk));
        var n2 = n1.getElementsByTagName('div')[0];
        if (percent === undefined) {
            n1.style.background = color;
            n2.style.display = 'none';
        }
        else {
            n2.style.width = percent + '%';
            n2.style.display = 'block';
        }
    }

    /////
    ////
    ///   config ui
    //

    function bumpchunk(dir) {
        try {
            dir.stopPropagation();
            dir.preventDefault();
        } catch (ex) { }

        if (st.files.length > 0)
            return alert('only possible before you start uploading\n\n(refresh and try again)')

        var obj = o('chunksz');
        if (dir.target) {
            obj.style.background = '#922';
            var v = Math.floor(parseInt(obj.value));
            if (v < 1 || v > 1024 || v !== v)
                return;

            chunksize_mb = v;
            chunksize = chunksize_mb * 1024 * 1024;
            localStorage.setItem('chunksz', v);
            obj.style.background = '#444';
            return;
        }

        chunksize_mb = Math.floor(chunksize_mb * dir);

        if (chunksize_mb < 1)
            chunksize_mb = 1;

        if (chunksize_mb > 1024)
            chunksize_mb = 1024;

        obj.value = chunksize_mb;
        bumpchunk({ "target": 1 })
    }

    function bumpthread(dir) {
        try {
            dir.stopPropagation();
            dir.preventDefault();
        } catch (ex) { }

        var obj = o('nthread');
        if (dir.target) {
            obj.style.background = '#922';
            var v = Math.floor(parseInt(obj.value));
            if (v < 1 || v > 8 || v !== v)
                return;

            parallel_uploads = v;
            localStorage.setItem('nthread', v);
            obj.style.background = '#444';
            return;
        }

        parallel_uploads += dir;

        if (parallel_uploads < 1)
            parallel_uploads = 1;

        if (parallel_uploads > 8)
            parallel_uploads = 8;

        obj.value = parallel_uploads;
        bumpthread({ "target": 1 })
    }

    function nop(ev) {
        ev.preventDefault();
        this.click();
    }

    o('chunksz_add').onclick = function (ev) {
        ev.preventDefault();
        bumpchunk(2);
    };
    o('chunksz_sub').onclick = function (ev) {
        ev.preventDefault();
        bumpchunk(0.5);
    };
    o('nthread_add').onclick = function (ev) {
        ev.preventDefault();
        bumpthread(1);
    };
    o('nthread_sub').onclick = function (ev) {
        ev.preventDefault();
        bumpthread(-1);
    };

    o('chunksz').addEventListener('input', bumpchunk, false);
    o('nthread').addEventListener('input', bumpthread, false);

    var nodes = o('u2conf').getElementsByTagName('a');
    for (var a = nodes.length - 1; a >= 0; a--)
        nodes[a].addEventListener('touchend', nop, false);

    bumpchunk({ "target": 1 })
    bumpthread({ "target": 1 })
})();
