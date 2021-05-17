"use strict";

window.onerror = vis_exh;


function goto_up2k() {
    if (up2k === false)
        return goto('bup');

    if (!up2k)
        return setTimeout(goto_up2k, 100);

    up2k.init_deps();
}


// chrome requires https to use crypto.subtle,
// usually it's undefined but some chromes throw on invoke
var up2k = null;
try {
    var cf = crypto.subtle || crypto.webkitSubtle;
    cf.digest('SHA-512', new Uint8Array(1)).then(
        function (x) { console.log('sha-ok'); up2k = up2k_init(cf); },
        function (x) { console.log('sha-ng:', x); up2k = up2k_init(false); }
    );
}
catch (ex) {
    console.log('sha-na:', ex);
    try {
        up2k = up2k_init(false);
    }
    catch (ex) { }
}
treectl.onscroll();


function up2k_flagbus() {
    var flag = {
        "id": Math.floor(Math.random() * 1024 * 1024 * 1023 * 2),
        "ch": new BroadcastChannel("up2k_flagbus"),
        "ours": false,
        "owner": null,
        "wants": null,
        "act": false,
        "last_tx": ["x", null]
    };
    var dbg = function (who, msg) {
        console.log('flagbus(' + flag.id + '): [' + who + '] ' + msg);
    };
    flag.ch.onmessage = function (e) {
        var who = e.data[0],
            what = e.data[1];

        if (who == flag.id) {
            dbg(who, 'hi me (??)');
            return;
        }
        flag.act = Date.now();
        if (what == "want") {
            // lowest id wins, don't care if that's us
            if (who < flag.id) {
                dbg(who, 'wants (ack)');
                flag.wants = [who, flag.act];
            }
            else {
                dbg(who, 'wants (ign)');
            }
        }
        else if (what == "have") {
            dbg(who, 'have');
            flag.owner = [who, flag.act];
        }
        else if (what == "give") {
            if (flag.owner && flag.owner[0] == who) {
                flag.owner = null;
                dbg(who, 'give (ok)');
            }
            else {
                dbg(who, 'give, INVALID, ' + flag.owner);
            }
        }
        else if (what == "hi") {
            dbg(who, 'hi');
            flag.ch.postMessage([flag.id, "hey"]);
        }
        else {
            dbg('?', e.data);
        }
    };
    var tx = function (now, msg) {
        var td = now - flag.last_tx[1];
        if (td > 500 || flag.last_tx[0] != msg) {
            dbg('*', 'tx ' + msg);
            flag.ch.postMessage([flag.id, msg]);
            flag.last_tx = [msg, now];
        }
    };
    var do_take = function (now) {
        //dbg('*', 'do_take');
        tx(now, "have");
        flag.owner = [flag.id, now];
        flag.ours = true;
    };
    var do_want = function (now) {
        //dbg('*', 'do_want');
        tx(now, "want");
    };
    flag.take = function (now) {
        if (flag.ours) {
            do_take(now);
            return;
        }
        if (flag.owner && now - flag.owner[1] > 5000) {
            flag.owner = null;
        }
        if (flag.wants && now - flag.wants[1] > 5000) {
            flag.wants = null;
        }
        if (!flag.owner && !flag.wants) {
            do_take(now);
            return;
        }
        do_want(now);
    };
    flag.give = function () {
        dbg('#', 'put give');
        flag.ch.postMessage([flag.id, "give"]);
        flag.owner = null;
        flag.ours = false;
    };
    flag.ch.postMessage([flag.id, 'hi']);
    return flag;
}


function U2pvis(act, btns) {
    this.act = act;
    this.ctr = { "ok": 0, "ng": 0, "bz": 0, "q": 0 };
    this.tab = [];
    this.head = 0;
    this.tail = -1;
    this.wsz = 3;

    this.addfile = function (entry, sz) {
        this.tab.push({
            "hn": entry[0],
            "ht": entry[1],
            "hp": entry[2],
            "in": 'q',
            "nh": 0, //hashed
            "nd": 0, //done
            "cb": [], // bytes done in chunk
            "bt": sz, // bytes total
            "bd": 0,  // bytes done
            "bd0": 0  // upload start
        });
        this.ctr["q"]++;
        this.drawcard("q");
        if (this.act == "q") {
            this.addrow(this.tab.length - 1);
        }
        if (this.act == "bz") {
            this.bzw();
        }
    };

    this.is_act = function (card) {
        if (this.act == "done")
            return card == "ok" || card == "ng";

        return this.act == card;
    }

    this.seth = function (nfile, field, html) {
        var fo = this.tab[nfile];
        field = ['hn', 'ht', 'hp'][field];
        if (fo[field] === html)
            return;

        fo[field] = html;
        if (!this.is_act(fo.in))
            return;

        var obj = ebi('f{0}{1}'.format(nfile, field.slice(1)));
        obj.innerHTML = html;
        if (field == 'hp') {
            obj.style.color = '';
            obj.style.background = '';
        }
    };

    this.setab = function (nfile, nblocks) {
        var t = [];
        for (var a = 0; a < nblocks; a++)
            t.push(0);

        this.tab[nfile].cb = t;
    };

    this.setat = function (nfile, blocktab) {
        this.tab[nfile].cb = blocktab;

        var bd = 0;
        for (var a = 0; a < blocktab.length; a++)
            bd += blocktab[a];

        this.tab[nfile].bd = bd;
        this.tab[nfile].bd0 = bd;
    };

    this.perc = function (bd, bd0, sz, t0) {
        var td = Date.now() - t0,
            p = bd * 100.0 / sz,
            nb = bd - bd0,
            spd = nb / (td / 1000),
            eta = (sz - bd) / spd;

        return [p, s2ms(eta), spd / (1024 * 1024)];
    };

    this.hashed = function (fobj) {
        var fo = this.tab[fobj.n],
            nb = fo.bt * (++fo.nh / fo.cb.length),
            p = this.perc(nb, 0, fobj.size, fobj.t1);

        fo.hp = '{0}%, {1}, {2} MB/s'.format(
            p[0].toFixed(2), p[1], p[2].toFixed(2)
        );
        if (!this.is_act(fo.in))
            return;

        var obj = ebi('f{0}p'.format(fobj.n)),
            o1 = p[0] - 2, o2 = p[0] - 0.1, o3 = p[0];

        obj.innerHTML = fo.hp;
        obj.style.color = '#fff';
        obj.style.background = 'linear-gradient(90deg, #025, #06a ' + o1 + '%, #09d ' + o2 + '%, #333 ' + o3 + '%, #333 99%, #777)';
    };

    this.prog = function (fobj, nchunk, cbd) {
        var fo = this.tab[fobj.n],
            delta = cbd - fo.cb[nchunk];

        fo.cb[nchunk] = cbd;
        fo.bd += delta;

        var p = this.perc(fo.bd, fo.bd0, fo.bt, fobj.t3);
        fo.hp = '{0}%, {1}, {2} MB/s'.format(
            p[0].toFixed(2), p[1], p[2].toFixed(2)
        );

        if (!this.is_act(fo.in))
            return;

        var obj = ebi('f{0}p'.format(fobj.n)),
            o1 = p[0] - 2, o2 = p[0] - 0.1, o3 = p[0];

        obj.innerHTML = fo.hp;
        obj.style.color = '#fff';
        obj.style.background = 'linear-gradient(90deg, #050, #270 ' + o1 + '%, #4b0 ' + o2 + '%, #333 ' + o3 + '%, #333 99%, #777)';
    };

    this.move = function (nfile, newcat) {
        var fo = this.tab[nfile],
            oldcat = fo.in,
            bz_act = this.act == "bz";

        if (oldcat == newcat) {
            throw 42;
        }

        fo.in = newcat;
        this.ctr[oldcat]--;
        this.ctr[newcat]++;
        this.drawcard(oldcat);
        this.drawcard(newcat);
        if (this.is_act(newcat)) {
            this.tail++;
            if (!ebi('f' + nfile))
                this.addrow(nfile);
        }
        else if (this.is_act(oldcat)) {
            this.head++;
            if (!bz_act) {
                var tr = ebi("f" + nfile);
                tr.parentNode.removeChild(tr);
            }
        }
        if (bz_act) {
            this.bzw();
        }
    };

    this.bzw = function () {
        var first = QS('#u2tab>tbody>tr:first-child');
        if (!first)
            return;

        var last = QS('#u2tab>tbody>tr:last-child');
        first = parseInt(first.getAttribute('id').slice(1));
        last = parseInt(last.getAttribute('id').slice(1));

        while (this.head - first > this.wsz) {
            var obj = ebi('f' + (first++));
            obj.parentNode.removeChild(obj);
        }
        while (last - this.tail < this.wsz && last < this.tab.length - 2) {
            var obj = ebi('f' + (++last));
            if (!obj)
                this.addrow(last);
        }
    };

    this.drawcard = function (cat) {
        var cards = QSA('#u2cards>a>span');

        if (cat == "q") {
            cards[4].innerHTML = this.ctr[cat];
            return;
        }
        if (cat == "bz") {
            cards[3].innerHTML = this.ctr[cat];
            return;
        }

        cards[2].innerHTML = this.ctr["ok"] + this.ctr["ng"];

        if (cat == "ng") {
            cards[1].innerHTML = this.ctr[cat];
        }
        if (cat == "ok") {
            cards[0].innerHTML = this.ctr[cat];
        }
    };

    this.changecard = function (card) {
        this.act = card;
        this.head = -1;
        this.tail = -1;
        var html = [];
        for (var a = 0; a < this.tab.length; a++) {
            var rt = this.tab[a].in;
            if (this.is_act(rt)) {
                html.push(this.genrow(a, true));

                this.tail = a;
                if (this.head == -1)
                    this.head = a;
            }
        }
        if (this.head == -1) {
            this.head = this.tab.length;
            this.tail = this.head - 1;
        }
        if (card == "bz") {
            for (var a = this.head - 1; a >= this.head - this.wsz && a >= 0; a--) {
                html.unshift(this.genrow(a, true).replace(/><td>/, "><td>a "));
            }
            for (var a = this.tail + 1; a <= this.tail + this.wsz && a < this.tab.length; a++) {
                html.push(this.genrow(a, true).replace(/><td>/, "><td>b "));
            }
        }
        ebi('u2tab').tBodies[0].innerHTML = html.join('\n');
    };

    this.genrow = function (nfile, as_html) {
        var r = this.tab[nfile],
            td1 = '<td id="f' + nfile,
            td = '</td>' + td1,
            ret = td1 + 'n">' + r.hn +
                td + 't">' + r.ht +
                td + 'p" class="prog">' + r.hp + '</td>';

        if (as_html)
            return '<tr id="f' + nfile + '">' + ret + '</tr>';

        var obj = mknod('tr');
        obj.setAttribute('id', 'f' + nfile);
        obj.innerHTML = ret;
        return obj;
    };

    this.addrow = function (nfile) {
        var tr = this.genrow(nfile);
        ebi('u2tab').tBodies[0].appendChild(tr);
    };

    var that = this;
    btns = QSA(btns + '>a[act]');
    for (var a = 0; a < btns.length; a++) {
        btns[a].onclick = function (e) {
            ev(e);
            var newtab = this.getAttribute('act');
            for (var b = 0; b < btns.length; b++) {
                btns[b].className = (
                    btns[b].getAttribute('act') == newtab) ? 'act' : '';
            }
            that.changecard(newtab);
        };
    }
}


function up2k_init(subtle) {
    // show modal message
    function showmodal(msg) {
        ebi('u2notbtn').innerHTML = msg;
        ebi('u2btn').style.display = 'none';
        ebi('u2notbtn').style.display = 'block';
        ebi('u2conf').style.opacity = '0.5';
    }

    // hide modal message
    function unmodal() {
        ebi('u2notbtn').style.display = 'none';
        ebi('u2btn').style.display = 'block';
        ebi('u2conf').style.opacity = '1';
        ebi('u2notbtn').innerHTML = '';
    }

    var suggest_up2k = 'this is the basic uploader; <a href="#" id="u2yea">up2k</a> is better';

    var shame = 'your browser <a href="https://www.chromium.org/blink/webcrypto">disables sha512</a> unless you <a href="' + (window.location + '').replace(':', 's:') + '">use https</a>',
        is_https = (window.location + '').indexOf('https:') === 0;

    if (is_https)
        // chrome<37 firefox<34 edge<12 opera<24 safari<7
        shame = 'your browser is impressively ancient';

    // upload ui hidden by default, clicking the header shows it
    function init_deps() {
        if (!subtle && !window.asmCrypto) {
            showmodal('<h1>loading sha512.js</h1><h2>since ' + shame + '</h2><h4>thanks chrome</h4>');
            import_js('/.cpr/deps/sha512.js', unmodal);

            if (is_https)
                ebi('u2foot').innerHTML = shame + ' so <em>this</em> uploader will do like 500kB/s at best';
            else
                ebi('u2foot').innerHTML = 'seems like ' + shame + ' so do that if you want more performance';
        }
    }

    // show uploader if the user only has write-access
    var perms = document.body.getAttribute('perms');
    if (perms && !has(perms.split(' '), 'read'))
        goto('up2k');

    // shows or clears a message in the basic uploader ui
    function setmsg(msg, type) {
        if (msg !== undefined) {
            ebi('u2err').setAttribute('class', type);
            ebi('u2err').innerHTML = msg;
        }
        else {
            ebi('u2err').setAttribute('class', '');
            ebi('u2err').innerHTML = '';
        }
        if (msg == suggest_up2k) {
            ebi('u2yea').onclick = function (e) {
                ev(e);
                goto('up2k');
            };
        }
    }

    // switches to the basic uploader with msg as error message
    function un2k(msg) {
        setmsg(msg, 'err');
        return false;
    }

    // handle user intent to use the basic uploader instead
    ebi('u2nope').onclick = function (e) {
        ev(e);
        setmsg(suggest_up2k, 'msg');
        goto('bup');
    };

    setmsg(suggest_up2k, 'msg');

    if (!String.prototype.format) {
        String.prototype.format = function () {
            var args = arguments;
            return this.replace(/{(\d+)}/g, function (match, number) {
                return typeof args[number] != 'undefined' ?
                    args[number] : match;
            });
        };
    }

    var parallel_uploads = icfg_get('nthread'),
        multitask = bcfg_get('multitask', true),
        ask_up = bcfg_get('ask_up', true),
        flag_en = bcfg_get('flag_en', false),
        fsearch = bcfg_get('fsearch', false),
        fdom_ctr = 0,
        min_filebuf = 0;

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
        },
        "bytes": {
            "hashed": 0,
            "uploaded": 0
        }
    };

    var pvis = new U2pvis("bz", '#u2cards');

    var bobslice = null;
    if (window.File)
        bobslice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice;

    if (!bobslice || !window.FileReader || !window.FileList)
        return un2k("this is the basic uploader; up2k needs at least<br />chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1");

    var flag = false;
    apply_flag_cfg();
    set_fsearch();

    function nav() {
        ebi('file' + fdom_ctr).click();
    }
    ebi('u2btn').addEventListener('click', nav, false);

    function ondrag(e) {
        e.stopPropagation();
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        e.dataTransfer.effectAllowed = 'copy';
    }
    ebi('u2btn').addEventListener('dragover', ondrag, false);
    ebi('u2btn').addEventListener('dragenter', ondrag, false);

    function gotfile(e) {
        e.stopPropagation();
        e.preventDefault();

        var files,
            is_itemlist = false;

        if (e.dataTransfer) {
            if (e.dataTransfer.items) {
                files = e.dataTransfer.items; // DataTransferItemList
                is_itemlist = true;
            }
            else files = e.dataTransfer.files; // FileList
        }
        else files = e.target.files;

        if (!files || files.length == 0)
            return alert('no files selected??');

        more_one_file();
        var bad_files = [],
            good_files = [],
            dirs = [];

        for (var a = 0; a < files.length; a++) {
            var fobj = files[a];
            if (is_itemlist) {
                if (fobj.kind !== 'file')
                    continue;

                try {
                    var wi = fobj.webkitGetAsEntry();
                    if (wi.isDirectory) {
                        dirs.push(wi);
                        continue;
                    }
                }
                catch (ex) { }
                fobj = fobj.getAsFile();
            }
            try {
                if (fobj.size < 1)
                    throw 1;
            }
            catch (ex) {
                bad_files.push(fobj.name);
                continue;
            }
            good_files.push([fobj, fobj.name]);
        }
        if (dirs) {
            return read_dirs(null, [], dirs, good_files, bad_files);
        }
    }

    function read_dirs(rd, pf, dirs, good, bad) {
        if (!dirs.length) {
            if (!pf.length)
                return gotallfiles(good, bad);

            console.log("retry pf, " + pf.length);
            setTimeout(function () {
                read_dirs(rd, pf, dirs, good, bad);
            }, 50);
            return;
        }

        if (!rd)
            rd = dirs[0].createReader();

        rd.readEntries(function (ents) {
            var ngot = 0;
            ents.forEach(function (dn) {
                if (dn.isDirectory) {
                    dirs.push(dn);
                }
                else {
                    var name = dn.fullPath;
                    if (name.indexOf('/') === 0)
                        name = name.slice(1);

                    pf.push(name);
                    dn.file(function (fobj) {
                        var idx = pf.indexOf(name);
                        pf.splice(idx, 1);
                        try {
                            if (fobj.size > 0) {
                                good.push([fobj, name]);
                                return;
                            }
                        }
                        catch (ex) { }
                        bad.push(name);
                    });
                }
                ngot += 1;
            });
            // console.log("ngot: " + ngot);
            if (!ngot) {
                dirs.shift();
                rd = null;
            }
            return read_dirs(rd, pf, dirs, good, bad);
        });
    }

    function gotallfiles(good_files, bad_files) {
        if (bad_files.length > 0) {
            var ntot = bad_files.length + good_files.length,
                msg = 'These {0} files (of {1} total) were skipped because they are empty:\n'.format(bad_files.length, ntot);

            for (var a = 0, aa = Math.min(20, bad_files.length); a < aa; a++)
                msg += '-- ' + bad_files[a] + '\n';

            if (good_files.length - bad_files.length <= 1 && ANDROID)
                msg += '\nFirefox-Android has a bug which prevents selecting multiple files. Try selecting one file at a time. For more info, see firefox bug 1456557';

            alert(msg);
        }

        var msg = ['upload these ' + good_files.length + ' files?'];
        for (var a = 0, aa = Math.min(20, good_files.length); a < aa; a++)
            msg.push(good_files[a][1]);

        if (ask_up && !fsearch && !confirm(msg.join('\n')))
            return;

        for (var a = 0; a < good_files.length; a++) {
            var fobj = good_files[a][0],
                now = Date.now(),
                lmod = fobj.lastModified || now;

            var entry = {
                "n": parseInt(st.files.length.toString()),
                "t0": now,
                "fobj": fobj,
                "name": good_files[a][1],
                "size": fobj.size,
                "lmod": lmod / 1000,
                "purl": get_evpath(),
                "done": false,
                "hash": []
            };

            var skip = false;
            for (var b = 0; b < st.files.length; b++)
                if (entry.name == st.files[b].name &&
                    entry.size == st.files[b].size)
                    skip = true;

            if (skip)
                continue;

            pvis.addfile([
                fsearch ? esc(entry.name) : linksplit(
                    esc(uricom_dec(entry.purl)[0] + entry.name)).join(' '),
                '📐 hash',
                ''
            ], fobj.size);
            st.files.push(entry);
            st.todo.hash.push(entry);
        }
    }
    ebi('u2btn').addEventListener('drop', gotfile, false);

    function more_one_file() {
        fdom_ctr++;
        var elm = mknod('div');
        elm.innerHTML = '<input id="file{0}" type="file" name="file{0}[]" multiple="multiple" />'.format(fdom_ctr);
        ebi('u2form').appendChild(elm);
        ebi('file' + fdom_ctr).addEventListener('change', gotfile, false);
    }
    more_one_file();

    function u2cleanup(e) {
        ev(e);
        for (var a = 0; a < st.files.length; a++) {
            var t = st.files[a];
            if (t.done && t.name) {
                var tr = ebi('f' + t.n);
                if (!tr)
                    continue;

                tr.parentNode.removeChild(tr);
                t.name = undefined;
            }
        }
    }
    ebi('u2cleanup').onclick = u2cleanup;

    /////
    ////
    ///   actuator
    //

    function handshakes_permitted() {
        var lim = multitask ? 1 : 0;
        return lim >=
            st.todo.upload.length +
            st.busy.upload.length;
    }

    function hashing_permitted() {
        if (multitask) {
            var ahead = st.bytes.hashed - st.bytes.uploaded;
            return ahead < 1024 * 1024 * 1024 * 4 &&
                st.todo.handshake.length + st.busy.handshake.length < 16;
        }
        return handshakes_permitted() && 0 ==
            st.todo.handshake.length +
            st.busy.handshake.length;
    }

    var tasker = (function () {
        var tto = null,
            running = false,
            was_busy = false;

        function defer() {
            running = false;
            clearTimeout(tto);
            tto = setTimeout(taskerd, 100);
        }

        function taskerd() {
            if (running)
                return;

            clearTimeout(tto);
            running = true;
            while (true) {
                var is_busy = 0 !=
                    st.todo.hash.length +
                    st.todo.handshake.length +
                    st.todo.upload.length +
                    st.busy.hash.length +
                    st.busy.handshake.length +
                    st.busy.upload.length;

                if (was_busy != is_busy) {
                    was_busy = is_busy;

                    window[(is_busy ? "add" : "remove") +
                        "EventListener"]("beforeunload", warn_uploader_busy);
                }

                if (flag) {
                    if (is_busy) {
                        var now = Date.now();
                        flag.take(now);
                        if (!flag.ours)
                            return defer();
                    }
                    else if (flag.ours) {
                        flag.give();
                    }
                }

                var mou_ikkai = false;

                if (st.todo.handshake.length > 0 &&
                    st.busy.handshake.length == 0 && (
                        st.todo.handshake[0].t4 || (
                            handshakes_permitted() &&
                            st.busy.upload.length < parallel_uploads
                        )
                    )
                ) {
                    exec_handshake();
                    mou_ikkai = true;
                }

                if (handshakes_permitted() &&
                    st.todo.handshake.length > 0 &&
                    st.busy.handshake.length == 0 &&
                    st.busy.upload.length < parallel_uploads) {
                    exec_handshake();
                    mou_ikkai = true;
                }

                if (st.todo.upload.length > 0 &&
                    st.busy.upload.length < parallel_uploads) {
                    exec_upload();
                    mou_ikkai = true;
                }

                if (hashing_permitted() &&
                    st.todo.hash.length > 0 &&
                    st.busy.hash.length == 0) {
                    exec_hash();
                    mou_ikkai = true;
                }

                if (!mou_ikkai)
                    return defer();
            }
        }
        taskerd();
        return taskerd;
    })();

    /////
    ////
    ///   hashing
    //

    // https://gist.github.com/jonleighton/958841
    function buf2b64(arrayBuffer) {
        var base64 = '',
            cset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_',
            src = new Uint8Array(arrayBuffer),
            nbytes = src.byteLength,
            byteRem = nbytes % 3,
            mainLen = nbytes - byteRem,
            a, b, c, d, chunk;

        for (var i = 0; i < mainLen; i = i + 3) {
            chunk = (src[i] << 16) | (src[i + 1] << 8) | src[i + 2];
            // create 8*3=24bit segment then split into 6bit segments
            a = (chunk & 16515072) >> 18; // (2^6 - 1) << 18
            b = (chunk & 258048) >> 12; // (2^6 - 1) << 12
            c = (chunk & 4032) >> 6; // (2^6 - 1) << 6
            d = chunk & 63; // 2^6 - 1

            // Convert the raw binary segments to the appropriate ASCII encoding
            base64 += cset[a] + cset[b] + cset[c] + cset[d];
        }

        if (byteRem == 1) {
            chunk = src[mainLen];
            a = (chunk & 252) >> 2; // (2^6 - 1) << 2
            b = (chunk & 3) << 4; // 2^2 - 1  (zero 4 LSB)
            base64 += cset[a] + cset[b];//+ '==';
        }
        else if (byteRem == 2) {
            chunk = (src[mainLen] << 8) | src[mainLen + 1];
            a = (chunk & 64512) >> 10; // (2^6 - 1) << 10
            b = (chunk & 1008) >> 4; // (2^6 - 1) << 4
            c = (chunk & 15) << 2; // 2^4 - 1  (zero 2 LSB)
            base64 += cset[a] + cset[b] + cset[c];//+ '=';
        }

        return base64;
    }

    function get_chunksize(filesize) {
        var chunksize = 1024 * 1024,
            stepsize = 512 * 1024;

        while (true) {
            for (var mul = 1; mul <= 2; mul++) {
                var nchunks = Math.ceil(filesize / chunksize);
                if (nchunks <= 256 || chunksize >= 32 * 1024 * 1024)
                    return chunksize;

                chunksize += stepsize;
                stepsize *= mul;
            }
        }
    }

    function exec_hash() {
        var t = st.todo.hash.shift();
        st.busy.hash.push(t);
        st.bytes.hashed += t.size;
        t.bytes_uploaded = 0;

        var bpend = 0,
            nchunk = 0,
            chunksize = get_chunksize(t.size),
            nchunks = Math.ceil(t.size / chunksize),
            hashtab = {};

        pvis.setab(t.n, nchunks);
        pvis.move(t.n, 'bz');

        var segm_next = function () {
            if (nchunk >= nchunks || (bpend > chunksize && bpend >= min_filebuf))
                return false;

            var reader = new FileReader(),
                nch = nchunk++,
                car = nch * chunksize,
                cdr = car + chunksize,
                t0 = Date.now();

            if (cdr >= t.size)
                cdr = t.size;

            bpend += cdr - car;

            reader.onload = function (e) {
                if (!min_filebuf && nch == 1) {
                    min_filebuf = 1;
                    var td = Date.now() - t0;
                    if (td > 50) {
                        ebi('u2foot').innerHTML += "<p>excessive filereader latency (" + td + " ms), increasing readahead</p>";
                        min_filebuf = 32 * 1024 * 1024;
                    }
                }
                hash_calc(nch, e.target.result);
            };
            reader.onerror = function () {
                alert('y o u   b r o k e    i t\nerror: ' + reader.error);
            };
            reader.readAsArrayBuffer(
                bobslice.call(t.fobj, car, cdr));

            return true;
        };

        var hash_calc = function (nch, buf) {
            while (segm_next());

            var hash_done = function (hashbuf) {
                var hslice = new Uint8Array(hashbuf).subarray(0, 32),
                    b64str = buf2b64(hslice).replace(/=$/, '');

                hashtab[nch] = b64str;
                t.hash.push(nch);
                pvis.hashed(t);

                bpend -= buf.byteLength;
                if (t.hash.length < nchunks) {
                    return segm_next();
                }
                t.hash = [];
                for (var a = 0; a < nchunks; a++) {
                    t.hash.push(hashtab[a]);
                }

                t.t2 = Date.now();
                if (t.n == 0 && window.location.hash == '#dbg') {
                    var spd = (t.size / ((t.t2 - t.t1) / 1000.)) / (1024 * 1024.);
                    alert('{0} ms, {1} MB/s\n'.format(t.t2 - t.t1, spd.toFixed(3)) + t.hash.join('\n'));
                }

                pvis.seth(t.n, 2, 'hashing done');
                pvis.seth(t.n, 1, '📦 wait');
                st.busy.hash.splice(st.busy.hash.indexOf(t), 1);
                st.todo.handshake.push(t);
            };

            if (subtle)
                subtle.digest('SHA-512', buf).then(hash_done);
            else setTimeout(function () {
                var hasher = new asmCrypto.Sha512();
                hasher.process(new Uint8Array(buf));
                hasher.finish();
                hash_done(hasher.result);
            }, 1);
        };

        t.t1 = Date.now();
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
        xhr.onload = function (e) {
            if (xhr.status == 200) {
                var response = JSON.parse(xhr.responseText);

                if (!response.name) {
                    var msg = '',
                        smsg = '';

                    if (!response || !response.hits || !response.hits.length) {
                        msg = 'not found on server';
                        smsg = '404';
                    }
                    else {
                        smsg = 'found';
                        var hit = response.hits[0],
                            msg = linksplit(esc(hit.rp)).join(''),
                            tr = unix2iso(hit.ts),
                            tu = unix2iso(t.lmod),
                            diff = parseInt(t.lmod) - parseInt(hit.ts),
                            cdiff = (Math.abs(diff) <= 2) ? '3c0' : 'f0b',
                            sdiff = '<span style="color:#' + cdiff + '">diff ' + diff;

                        msg += '<br /><small>' + tr + ' (srv), ' + tu + ' (You), ' + sdiff + '</span></span>';
                    }
                    pvis.seth(t.n, 2, msg);
                    pvis.seth(t.n, 1, smsg);
                    pvis.move(t.n, smsg == '404' ? 'ng' : 'ok');
                    st.busy.handshake.splice(st.busy.handshake.indexOf(t), 1);
                    st.bytes.uploaded += t.size;
                    t.done = true;
                    tasker();
                    return;
                }

                if (response.name !== t.name) {
                    // file exists; server renamed us
                    t.name = response.name;
                    pvis.seth(t.n, 0, linksplit(esc(t.purl + t.name)).join(' '));
                }

                var chunksize = get_chunksize(t.size),
                    cdr_idx = Math.ceil(t.size / chunksize) - 1,
                    cdr_sz = (t.size % chunksize) || chunksize,
                    cbd = [];

                for (var a = 0; a <= cdr_idx; a++) {
                    cbd.push(a == cdr_idx ? cdr_sz : chunksize);
                }

                t.postlist = [];
                t.wark = response.wark;
                var missing = response.hash;
                for (var a = 0; a < missing.length; a++) {
                    var idx = t.hash.indexOf(missing[a]);
                    if (idx < 0)
                        return alert('wtf negative index for hash "{0}" in task:\n{1}'.format(
                            missing[a], JSON.stringify(t)));

                    t.postlist.push(idx);
                    cbd[idx] = 0;
                }

                pvis.setat(t.n, cbd);
                pvis.prog(t, 0, cbd[0]);

                var done = true,
                    msg = '&#x1f3b7;&#x1f41b;';

                if (t.postlist.length > 0) {
                    for (var a = 0; a < t.postlist.length; a++)
                        st.todo.upload.push({
                            'nfile': t.n,
                            'npart': t.postlist[a]
                        });

                    msg = 'uploading';
                    done = false;
                }
                pvis.seth(t.n, 1, msg);
                st.busy.handshake.splice(st.busy.handshake.indexOf(t), 1);

                if (done) {
                    t.done = true;
                    st.bytes.uploaded += t.size - t.bytes_uploaded;
                    var spd1 = (t.size / ((t.t2 - t.t1) / 1000.)) / (1024 * 1024.),
                        spd2 = (t.size / ((t.t4 - t.t3) / 1000.)) / (1024 * 1024.);

                    pvis.seth(t.n, 2, 'hash {0}, up {1} MB/s'.format(
                        spd1.toFixed(2), spd2.toFixed(2)));

                    pvis.move(t.n, 'ok');
                }
                else t.t4 = undefined;

                tasker();
            }
            else {
                var err = "",
                    rsp = (xhr.responseText + ''),
                    ofs = rsp.lastIndexOf('\nURL: ');

                if (ofs !== -1)
                    rsp = rsp.slice(0, ofs);

                if (rsp.indexOf('<pre>') === 0)
                    rsp = rsp.slice(5);

                st.bytes.uploaded += t.size;
                if (rsp.indexOf('partial upload exists') !== -1 ||
                    rsp.indexOf('file already exists') !== -1) {
                    err = rsp;
                    ofs = err.indexOf('\n/');
                    if (ofs !== -1) {
                        err = err.slice(0, ofs + 1) + linksplit(err.slice(ofs + 2)).join(' ');
                    }
                }
                if (err != "") {
                    pvis.seth(t.n, 1, "ERROR");
                    pvis.seth(t.n, 2, err);
                    pvis.move(t.n, 'ng');

                    st.busy.handshake.splice(st.busy.handshake.indexOf(t), 1);
                    tasker();
                    return;
                }
                alert("server broke; hs-err {0} on file [{1}]:\n".format(
                    xhr.status, t.name) + (
                        (xhr.response && xhr.response.err) ||
                        (xhr.responseText && xhr.responseText) ||
                        "no further information"));
            }
        };

        var req = {
            "name": t.name,
            "size": t.size,
            "lmod": t.lmod,
            "hash": t.hash
        };
        if (fsearch)
            req.srch = 1;

        xhr.open('POST', t.purl + 'handshake.php', true);
        xhr.responseType = 'text';
        xhr.send(JSON.stringify(req));
    }

    /////
    ////
    ///   upload
    //

    function exec_upload() {
        var upt = st.todo.upload.shift();
        st.busy.upload.push(upt);

        var npart = upt.npart,
            t = st.files[upt.nfile];

        if (!t.t3)
            t.t3 = Date.now();

        pvis.seth(t.n, 1, "🚀 send");

        var chunksize = get_chunksize(t.size),
            car = npart * chunksize,
            cdr = car + chunksize;

        if (cdr >= t.size)
            cdr = t.size;

        var xhr = new XMLHttpRequest();
        xhr.upload.onprogress = function (xev) {
            pvis.prog(t, npart, xev.loaded);
        };
        xhr.onload = function (xev) {
            if (xhr.status == 200) {
                pvis.prog(t, npart, cdr - car);
                st.bytes.uploaded += cdr - car;
                t.bytes_uploaded += cdr - car;
                st.busy.upload.splice(st.busy.upload.indexOf(upt), 1);
                t.postlist.splice(t.postlist.indexOf(npart), 1);
                if (t.postlist.length == 0) {
                    t.t4 = Date.now();
                    pvis.seth(t.n, 1, 'verifying');
                    st.todo.handshake.unshift(t);
                }
                tasker();
            }
            else
                alert("server broke; cu-err {0} on file [{1}]:\n".format(
                    xhr.status, t.name) + (
                        (xhr.response && xhr.response.err) ||
                        (xhr.responseText && xhr.responseText) ||
                        "no further information"));
        };
        xhr.open('POST', t.purl + 'chunkpit.php', true);
        xhr.setRequestHeader("X-Up2k-Hash", t.hash[npart]);
        xhr.setRequestHeader("X-Up2k-Wark", t.wark);
        xhr.setRequestHeader('Content-Type', 'application/octet-stream');
        if (xhr.overrideMimeType)
            xhr.overrideMimeType('Content-Type', 'application/octet-stream');

        xhr.responseType = 'text';
        xhr.send(bobslice.call(t.fobj, car, cdr));
    }

    /////
    ////
    ///   config ui
    //

    function onresize(e) {
        var bar = ebi('ops'),
            wpx = innerWidth,
            fpx = parseInt(getComputedStyle(bar)['font-size']),
            wem = wpx * 1.0 / fpx,
            wide = wem > 54,
            parent = ebi(wide ? 'u2btn_cw' : 'u2btn_ct'),
            btn = ebi('u2btn');

        //console.log([wpx, fpx, wem]);
        if (btn.parentNode !== parent) {
            parent.appendChild(btn);
            ebi('u2conf').setAttribute('class', wide ? 'has_btn' : '');
            ebi('u2cards').setAttribute('class', wide ? 'w' : '');
        }
    }
    window.addEventListener('resize', onresize);
    onresize();

    function desc_show(e) {
        var cfg = sread('tooltips');
        if (cfg !== null && cfg != '1')
            return;

        var msg = this.getAttribute('alt'),
            cdesc = ebi('u2cdesc');

        cdesc.innerHTML = msg.replace(/\$N/g, "<br />");
        cdesc.setAttribute('class', 'show');
    }
    function desc_hide(e) {
        ebi('u2cdesc').setAttribute('class', '');
    }
    var o = QSA('#u2conf *[alt]');
    for (var a = o.length - 1; a >= 0; a--) {
        o[a].parentNode.getElementsByTagName('input')[0].setAttribute('alt', o[a].getAttribute('alt'));
    }
    var o = QSA('#u2conf *[alt]');
    for (var a = 0; a < o.length; a++) {
        o[a].onfocus = desc_show;
        o[a].onblur = desc_hide;
        o[a].onmouseenter = desc_show;
        o[a].onmouseleave = desc_hide;
    }

    function bumpthread(dir) {
        try {
            dir.stopPropagation();
            dir.preventDefault();
        } catch (ex) { }

        var obj = ebi('nthread');
        if (dir.target) {
            clmod(obj, 'err', 1);
            var v = Math.floor(parseInt(obj.value));
            if (v < 1 || v > 8 || v !== v)
                return;

            parallel_uploads = v;
            swrite('nthread', v);
            clmod(obj, 'err');
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

    function tgl_multitask() {
        multitask = !multitask;
        bcfg_set('multitask', multitask);
    }

    function tgl_ask_up() {
        ask_up = !ask_up;
        bcfg_set('ask_up', ask_up);
    }

    function tgl_fsearch() {
        set_fsearch(!fsearch);
    }

    function set_fsearch(new_state) {
        var perms = document.body.getAttribute('perms'),
            fixed = false;

        if (!ebi('fsearch')) {
            new_state = false;
        }
        else if (perms) {
            perms = perms.split(' ');
            if (!has(perms, 'write')) {
                new_state = true;
                fixed = true;
            }
            if (!has(perms, 'read')) {
                new_state = false;
                fixed = true;
            }
        }

        if (new_state !== undefined) {
            fsearch = new_state;
            bcfg_set('fsearch', fsearch);
        }

        try {
            QS('label[for="fsearch"]').style.display = QS('#fsearch').style.display = fixed ? 'none' : '';
        }
        catch (ex) { }

        try {
            var fun = fsearch ? 'add' : 'remove',
                ico = fsearch ? '🔎' : '🚀',
                desc = fsearch ? 'Search' : 'Upload';

            ebi('op_up2k').classList[fun]('srch');
            ebi('u2bm').innerHTML = ico + ' <sup>' + desc + '</sup>';
        }
        catch (ex) { }
    }

    function tgl_flag_en() {
        flag_en = !flag_en;
        bcfg_set('flag_en', flag_en);
        apply_flag_cfg();
    }

    function apply_flag_cfg() {
        if (flag_en && !flag) {
            try {
                flag = up2k_flagbus();
            }
            catch (ex) {
                console.log("flag error: " + ex.toString());
                tgl_flag_en();
            }
        }
        else if (!flag_en && flag) {
            flag.ch.close();
            flag = false;
        }
    }

    function nop(e) {
        ev(e);
        this.click();
    }

    ebi('nthread_add').onclick = function (e) {
        ev(e);
        bumpthread(1);
    };
    ebi('nthread_sub').onclick = function (e) {
        ev(e);
        bumpthread(-1);
    };

    ebi('nthread').addEventListener('input', bumpthread, false);
    ebi('multitask').addEventListener('click', tgl_multitask, false);
    ebi('ask_up').addEventListener('click', tgl_ask_up, false);
    ebi('flag_en').addEventListener('click', tgl_flag_en, false);
    var o = ebi('fsearch');
    if (o)
        o.addEventListener('click', tgl_fsearch, false);

    var nodes = ebi('u2conf').getElementsByTagName('a');
    for (var a = nodes.length - 1; a >= 0; a--)
        nodes[a].addEventListener('touchend', nop, false);

    set_fsearch();
    bumpthread({ "target": 1 })
    return { "init_deps": init_deps, "set_fsearch": set_fsearch }
}


function warn_uploader_busy(e) {
    e.preventDefault();
    e.returnValue = '';
    return "upload in progress, click abort and use the file-tree to navigate instead";
}


if (QS('#op_up2k.act'))
    goto_up2k();
