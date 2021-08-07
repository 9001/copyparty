"use strict";


function goto_up2k() {
    if (up2k === false)
        return goto('bup');

    if (!up2k)
        return setTimeout(goto_up2k, 100);

    up2k.init_deps();
}


// chrome requires https to use crypto.subtle,
// usually it's undefined but some chromes throw on invoke
var up2k = null,
    sha_js = window.WebAssembly ? 'hw' : 'ac',  // ff53,c57,sa11
    m = 'will use ' + sha_js + ' instead of native sha512 due to';

try {
    var cf = crypto.subtle || crypto.webkitSubtle;
    cf.digest('SHA-512', new Uint8Array(1)).then(
        function (x) { console.log('sha-ok'); up2k = up2k_init(cf); },
        function (x) { console.log(m, x); up2k = up2k_init(false); }
    );
}
catch (ex) {
    console.log(m, ex);
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
        tx(now, "have");
        flag.owner = [flag.id, now];
        flag.ours = true;
    };
    var do_want = function (now) {
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
    var r = this;
    r.act = act;
    r.ctr = { "ok": 0, "ng": 0, "bz": 0, "q": 0 };
    r.tab = [];
    r.head = 0;
    r.tail = -1;
    r.wsz = 3;

    r.addfile = function (entry, sz, draw) {
        r.tab.push({
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
        r.ctr["q"]++;
        if (!draw)
            return;

        r.drawcard("q");
        if (r.act == "q") {
            r.addrow(r.tab.length - 1);
        }
        if (r.act == "bz") {
            r.bzw();
        }
    };

    r.is_act = function (card) {
        if (r.act == "done")
            return card == "ok" || card == "ng";

        return r.act == card;
    }

    r.seth = function (nfile, field, html) {
        var fo = r.tab[nfile];
        field = ['hn', 'ht', 'hp'][field];
        if (fo[field] === html)
            return;

        fo[field] = html;
        if (!r.is_act(fo.in))
            return;

        var obj = ebi('f{0}{1}'.format(nfile, field.slice(1)));
        obj.innerHTML = html;
        if (field == 'hp') {
            obj.style.color = '';
            obj.style.background = '';
        }
    };

    r.setab = function (nfile, nblocks) {
        var t = [];
        for (var a = 0; a < nblocks; a++)
            t.push(0);

        r.tab[nfile].cb = t;
    };

    r.setat = function (nfile, blocktab) {
        r.tab[nfile].cb = blocktab;

        var bd = 0;
        for (var a = 0; a < blocktab.length; a++)
            bd += blocktab[a];

        r.tab[nfile].bd = bd;
        r.tab[nfile].bd0 = bd;
    };

    r.perc = function (bd, bd0, sz, t0) {
        var td = Date.now() - t0,
            p = bd * 100.0 / sz,
            nb = bd - bd0,
            spd = nb / (td / 1000),
            eta = (sz - bd) / spd;

        return [p, s2ms(eta), spd / (1024 * 1024)];
    };

    r.hashed = function (fobj) {
        var fo = r.tab[fobj.n],
            nb = fo.bt * (++fo.nh / fo.cb.length),
            p = r.perc(nb, 0, fobj.size, fobj.t_hashing);

        fo.hp = '{0}%, {1}, {2} MB/s'.format(
            p[0].toFixed(2), p[1], p[2].toFixed(2)
        );
        if (!r.is_act(fo.in))
            return;

        var obj = ebi('f{0}p'.format(fobj.n)),
            o1 = p[0] - 2, o2 = p[0] - 0.1, o3 = p[0];

        obj.innerHTML = fo.hp;
        obj.style.color = '#fff';
        obj.style.background = 'linear-gradient(90deg, #025, #06a ' + o1 + '%, #09d ' + o2 + '%, #333 ' + o3 + '%, #333 99%, #777)';
    };

    r.prog = function (fobj, nchunk, cbd) {
        var fo = r.tab[fobj.n],
            delta = cbd - fo.cb[nchunk];

        fo.cb[nchunk] = cbd;
        fo.bd += delta;

        var p = r.perc(fo.bd, fo.bd0, fo.bt, fobj.t_uploading);
        fo.hp = '{0}%, {1}, {2} MB/s'.format(
            p[0].toFixed(2), p[1], p[2].toFixed(2)
        );

        if (!r.is_act(fo.in))
            return;

        var obj = ebi('f{0}p'.format(fobj.n)),
            o1 = p[0] - 2, o2 = p[0] - 0.1, o3 = p[0];

        if (!obj) {
            var msg = [
                "act", r.act,
                "in", fo.in,
                "is_act", r.is_act(fo.in),
                "head", r.head,
                "tail", r.tail,
                "nfile", fobj.n,
                "name", fobj.name,
                "sz", fobj.size,
                "bytesDelta", delta,
                "bytesDone", fo.bd,
            ],
                m2 = '',
                ds = QSA("#u2tab>tbody>tr>td:first-child>a:last-child");

            for (var a = 0; a < msg.length; a += 2)
                m2 += msg[a] + '=' + msg[a + 1] + ', ';

            console.log(m2);

            for (var a = 0, aa = ds.length; a < aa; a++) {
                var id = ds[a].parentNode.getAttribute('id').slice(1, -1);
                console.log("dom %d/%d = [%s] in(%s) is_act(%s) %s",
                    a, aa, id, r.tab[id].in, r.is_act(fo.in), ds[a].textContent);
            }

            for (var a = 0, aa = r.tab.length; a < aa; a++)
                if (r.is_act(r.tab[a].in))
                    console.log("tab %d/%d = sz %s", a, aa, r.tab[a].bt);

            throw new Error('see console');
        }

        obj.innerHTML = fo.hp;
        obj.style.color = '#fff';
        obj.style.background = 'linear-gradient(90deg, #050, #270 ' + o1 + '%, #4b0 ' + o2 + '%, #333 ' + o3 + '%, #333 99%, #777)';
    };

    r.move = function (nfile, newcat) {
        var fo = r.tab[nfile],
            oldcat = fo.in,
            bz_act = r.act == "bz";

        if (oldcat == newcat)
            return;

        fo.in = newcat;
        r.ctr[oldcat]--;
        r.ctr[newcat]++;
        r.drawcard(oldcat);
        r.drawcard(newcat);
        if (r.is_act(newcat)) {
            r.tail = Math.max(r.tail, nfile + 1);
            if (!ebi('f' + nfile))
                r.addrow(nfile);
        }
        else if (r.is_act(oldcat)) {
            while (r.head < Math.min(r.tab.length, r.tail) && r.precard[r.tab[r.head].in])
                r.head++;

            if (!bz_act) {
                var tr = ebi("f" + nfile);
                tr.parentNode.removeChild(tr);
            }
        }
        else return;

        if (bz_act)
            r.bzw();
    };

    r.bzw = function () {
        var first = QS('#u2tab>tbody>tr:first-child');
        if (!first)
            return;

        var last = QS('#u2tab>tbody>tr:last-child');
        first = parseInt(first.getAttribute('id').slice(1));
        last = parseInt(last.getAttribute('id').slice(1));

        while (r.head - first > r.wsz) {
            var obj = ebi('f' + (first++));
            if (obj)
                obj.parentNode.removeChild(obj);
        }
        while (last - r.tail < r.wsz && last < r.tab.length - 2) {
            var obj = ebi('f' + (++last));
            if (!obj)
                r.addrow(last);
        }
    };

    r.drawcard = function (cat) {
        var cards = QSA('#u2cards>a>span');

        if (cat == "q") {
            cards[4].innerHTML = r.ctr[cat];
            return;
        }
        if (cat == "bz") {
            cards[3].innerHTML = r.ctr[cat];
            return;
        }

        cards[2].innerHTML = r.ctr["ok"] + r.ctr["ng"];

        if (cat == "ng") {
            cards[1].innerHTML = r.ctr[cat];
        }
        if (cat == "ok") {
            cards[0].innerHTML = r.ctr[cat];
        }
    };

    r.changecard = function (card) {
        r.act = card;
        r.precard = has(["ok", "ng", "done"], r.act) ? {} : r.act == "bz" ? { "ok": 1, "ng": 1 } : { "ok": 1, "ng": 1, "bz": 1 };
        r.postcard = has(["ok", "ng", "done"], r.act) ? { "bz": 1, "q": 1 } : r.act == "bz" ? { "q": 1 } : {};
        r.head = -1;
        r.tail = -1;
        var html = [];
        for (var a = 0; a < r.tab.length; a++) {
            var rt = r.tab[a].in;
            if (r.is_act(rt)) {
                html.push(r.genrow(a, true));

                r.tail = a;
                if (r.head == -1)
                    r.head = a;
            }
        }
        if (r.head == -1) {
            for (var a = 0; a < r.tab.length; a++) {
                var rt = r.tab[a].in;
                if (r.precard[rt]) {
                    r.head = a + 1;
                    r.tail = a;
                }
                else if (r.postcard[rt]) {
                    r.head = a;
                    r.tail = a - 1;
                    break;
                }
            }
        }

        if (r.head < 0)
            r.head = 0;

        if (card == "bz") {
            for (var a = r.head - 1; a >= r.head - r.wsz && a >= 0; a--) {
                html.unshift(r.genrow(a, true).replace(/><td>/, "><td>a "));
            }
            for (var a = r.tail + 1; a <= r.tail + r.wsz && a < r.tab.length; a++) {
                html.push(r.genrow(a, true).replace(/><td>/, "><td>b "));
            }
        }
        ebi('u2tab').tBodies[0].innerHTML = html.join('\n');
    };

    r.genrow = function (nfile, as_html) {
        var row = r.tab[nfile],
            td1 = '<td id="f' + nfile,
            td = '</td>' + td1,
            ret = td1 + 'n">' + row.hn +
                td + 't">' + row.ht +
                td + 'p" class="prog">' + row.hp + '</td>';

        if (as_html)
            return '<tr id="f' + nfile + '">' + ret + '</tr>';

        var obj = mknod('tr');
        obj.setAttribute('id', 'f' + nfile);
        obj.innerHTML = ret;
        return obj;
    };

    r.addrow = function (nfile) {
        var tr = r.genrow(nfile);
        ebi('u2tab').tBodies[0].appendChild(tr);
    };

    btns = QSA(btns + '>a[act]');
    for (var a = 0; a < btns.length; a++) {
        btns[a].onclick = function (e) {
            ev(e);
            var newtab = this.getAttribute('act');
            function go() {
                for (var b = 0; b < btns.length; b++) {
                    btns[b].className = (
                        btns[b].getAttribute('act') == newtab) ? 'act' : '';
                }
                r.changecard(newtab);
            }
            var nf = r.ctr[newtab];
            if (nf === undefined)
                nf = r.ctr["ok"] + r.ctr["ng"];

            if (nf < 9000)
                return go();

            modal.confirm('about to show ' + nf + ' files\n\nthis may crash your browser, are you sure?', go, null);
        };
    }

    r.changecard(r.act);
}


function fsearch_explain(n) {
    if (n)
        return toast.inf(60, 'your access to this folder is Read-Only\n\n' + (acct == '*' ? 'you are currently not logged in' : 'you are currently logged in as "' + acct + '"'));

    if (bcfg_get('fsearch', false))
        return toast.inf(60, 'you are currently in file-search mode\n\nswitch to upload-mode by clicking the green magnifying glass (next to the big yellow search button), and then refresh\n\nsorry');

    return toast.inf(60, 'refresh the page and try again, it should work now');
}


function up2k_init(subtle) {
    function showmodal(msg) {
        ebi('u2notbtn').innerHTML = msg;
        ebi('u2btn').style.display = 'none';
        ebi('u2notbtn').style.display = 'block';
        ebi('u2conf').style.opacity = '0.5';
    }

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

    var got_deps = false;
    function init_deps() {
        if (!got_deps && !subtle && !window.asmCrypto) {
            var fn = 'sha512.' + sha_js + '.js';
            showmodal('<h1>loading ' + fn + '</h1><h2>since ' + shame + '</h2><h4>thanks chrome</h4>');
            import_js('/.cpr/deps/' + fn, unmodal);

            if (is_https)
                ebi('u2foot').innerHTML = shame + ' so <em>this</em> uploader will do like 500kB/s at best';
            else
                ebi('u2foot').innerHTML = 'seems like ' + shame + ' so do that if you want more performance <span style="color:#' +
                    (sha_js == 'ac' ? 'c84">(expecting 20' : '8a5">(but dont worry too much, expect 100') + ' MiB/s)</span>';
        }
        got_deps = true;
    }

    if (perms.length && !has(perms, 'read'))
        goto('up2k');

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

    function un2k(msg) {
        setmsg(msg, 'err');
        return false;
    }

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
        turbo = bcfg_get('u2turbo', false),
        datechk = bcfg_get('u2tdate', true),
        fdom_ctr = 0,
        min_filebuf = 0;

    var st = {
        "files": [],
        "todo": {
            "head": [],
            "hash": [],
            "handshake": [],
            "upload": []
        },
        "busy": {
            "head": [],
            "hash": [],
            "handshake": [],
            "upload": []
        },
        "bytes": {
            "hashed": 0,
            "uploaded": 0
        }
    };

    function push_t(arr, t) {
        var sort = arr.length && arr[arr.length - 1].n > t.n;
        arr.push(t);
        if (sort)
            arr.sort(function (a, b) {
                return a.n < b.n ? -1 : 1;
            });
    }

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

        if (!files || !files.length)
            return toast.err(0, 'no files selected??');

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

    function rd_flatten(pf, dirs) {
        var ret = jcp(pf);
        for (var a = 0; a < dirs.length; a++)
            ret.push(dirs.fullPath || '');

        ret.sort();
        return ret;
    }

    var rd_missing_ref = [];
    function read_dirs(rd, pf, dirs, good, bad, spins) {
        spins = spins || 0;
        if (++spins == 5)
            rd_missing_ref = rd_flatten(pf, dirs);

        if (spins == 200) {
            var missing = rd_flatten(pf, dirs),
                match = rd_missing_ref.length == missing.length,
                aa = match ? missing.length : 0;

            missing.sort();
            for (var a = 0; a < aa; a++)
                if (rd_missing_ref[a] != missing[a])
                    match = false;

            if (match) {
                var msg = ['directory iterator got stuck on the following {0} items; good chance your browser is about to spinlock:'.format(missing.length)];
                for (var a = 0; a < Math.min(20, missing.length); a++)
                    msg.push(missing[a]);

                return modal.alert(msg.join('\n-- '), function () {
                    read_dirs(rd, [], [], good, bad, spins);
                });
            }
            spins = 0;
        }

        if (!dirs.length) {
            if (!pf.length)
                return gotallfiles(good, bad);

            console.log("retry pf, " + pf.length);
            setTimeout(function () {
                read_dirs(rd, pf, dirs, good, bad, spins);
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
                        apop(pf, name);
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
            if (!ngot) {
                dirs.shift();
                rd = null;
            }
            return read_dirs(rd, pf, dirs, good, bad, spins);
        });
    }

    function gotallfiles(good_files, bad_files) {
        if (bad_files.length) {
            var ntot = bad_files.length + good_files.length,
                msg = 'These {0} files (of {1} total) were skipped because they are empty:\n'.format(bad_files.length, ntot);

            for (var a = 0, aa = Math.min(20, bad_files.length); a < aa; a++)
                msg += '-- ' + bad_files[a] + '\n';

            if (good_files.length - bad_files.length <= 1 && ANDROID)
                msg += '\nFirefox-Android has a bug which prevents selecting multiple files. Try selecting one file at a time. For more info, see firefox bug 1456557';

            return modal.alert(msg, function () {
                gotallfiles(good_files, []);
            });
        }

        var msg = ['upload these ' + good_files.length + ' files?'];
        for (var a = 0, aa = Math.min(20, good_files.length); a < aa; a++)
            msg.push(good_files[a][1]);

        if (ask_up && !fsearch)
            return modal.confirm(msg.join('\n'), function () { up_them(good_files); }, null);

        up_them(good_files);
    }

    function up_them(good_files) {
        var seen = {},
            evpath = get_evpath(),
            draw_each = good_files.length < 50;

        for (var a = 0; a < st.files.length; a++)
            seen[st.files[a].name + '\n' + st.files[a].size] = 1;

        for (var a = 0; a < good_files.length; a++) {
            var fobj = good_files[a][0],
                name = good_files[a][1],
                fdir = '',
                now = Date.now(),
                lmod = fobj.lastModified || now,
                ofs = name.lastIndexOf('/') + 1;

            if (ofs) {
                fdir = name.slice(0, ofs);
                name = name.slice(ofs);
            }

            var entry = {
                "n": st.files.length,
                "t0": now,
                "fobj": fobj,
                "name": name,
                "size": fobj.size,
                "lmod": lmod / 1000,
                "purl": fdir,
                "done": false,
                "hash": []
            },
                key = entry.name + '\n' + entry.size;

            if (seen[key])
                continue;

            seen[key] = 1;

            pvis.addfile([
                fsearch ? esc(entry.name) : linksplit(
                    uricom_dec(entry.purl)[0] + entry.name).join(' '),
                '📐 hash',
                ''
            ], fobj.size, draw_each);

            st.files.push(entry);
            if (turbo)
                push_t(st.todo.head, entry);
            else
                push_t(st.todo.hash, entry);
        }
        if (!draw_each) {
            pvis.drawcard("q");
            pvis.changecard(pvis.act);
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
        if (!st.todo.handshake.length)
            return true;

        var t = st.todo.handshake[0],
            cd = t.cooldown;

        if (cd && cd - Date.now() > 0)
            return false;

        // keepalive or verify
        if (t.keepalive ||
            t.t_uploaded)
            return true;

        if (parallel_uploads <
            st.busy.handshake.length)
            return false;

        if (st.busy.handshake.length)
            for (var n = t.n - 1; n >= t.n - parallel_uploads && n >= 0; n--)
                if (st.files[n].t_uploading)
                    return false;

        if ((multitask ? 1 : 0) <
            st.todo.upload.length +
            st.busy.upload.length)
            return false;

        return true;
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
            if (crashed)
                return defer();

            running = true;
            while (true) {
                var now = Date.now(),
                    is_busy = 0 !=
                        st.todo.head.length +
                        st.todo.hash.length +
                        st.todo.handshake.length +
                        st.todo.upload.length +
                        st.busy.head.length +
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
                        flag.take(now);
                        if (!flag.ours)
                            return defer();
                    }
                    else if (flag.ours) {
                        flag.give();
                    }
                }

                var mou_ikkai = false;

                if (st.busy.handshake.length &&
                    st.busy.handshake[0].t_busied < now - 30 * 1000
                ) {
                    console.log("retrying stuck handshake");
                    var t = st.busy.handshake.shift();
                    st.todo.handshake.unshift(t);
                }

                var nprev = -1;
                for (var a = 0; a < st.todo.upload.length; a++) {
                    var nf = st.todo.upload[a].nfile;
                    if (nprev == nf)
                        continue;

                    nprev = nf;
                    var t = st.files[nf];
                    if (now - t.t_busied > 1000 * 30 &&
                        now - t.t_handshake > 1000 * (21600 - 1800)
                    ) {
                        apop(st.todo.handshake, t);
                        st.todo.handshake.unshift(t);
                        t.keepalive = true;
                    }
                }

                if (st.todo.head.length &&
                    st.busy.head.length < parallel_uploads) {
                    exec_head();
                    mou_ikkai = true;
                }

                if (handshakes_permitted() &&
                    st.todo.handshake.length) {
                    exec_handshake();
                    mou_ikkai = true;
                }

                if (st.todo.upload.length &&
                    st.busy.upload.length < parallel_uploads) {
                    exec_upload();
                    mou_ikkai = true;
                }

                if (hashing_permitted() &&
                    st.todo.hash.length &&
                    !st.busy.hash.length) {
                    exec_hash();
                    mou_ikkai = true;
                }

                if (!mou_ikkai || crashed)
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

    function hex2u8(txt) {
        return new Uint8Array(txt.match(/.{2}/g).map(function (b) { return parseInt(b, 16); }));
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

            function orz(e) {
                if (!min_filebuf && nch == 1) {
                    min_filebuf = 1;
                    var td = Date.now() - t0;
                    if (td > 50) {
                        ebi('u2foot').innerHTML += "<p>excessive filereader latency (" + td + " ms), increasing readahead</p>";
                        min_filebuf = 32 * 1024 * 1024;
                    }
                }
                hash_calc(nch, e.target.result);
            }
            reader.onload = function (e) {
                try { orz(e); } catch (ex) { vis_exh(ex + '', '', '', '', ex); }
            };
            reader.onerror = function () {
                var err = reader.error + '';
                var handled = false;

                if (err.indexOf('NotReadableError') !== -1 || // win10-chrome defender
                    err.indexOf('NotFoundError') !== -1  // macos-firefox permissions
                ) {
                    pvis.seth(t.n, 1, 'OS-error');
                    pvis.seth(t.n, 2, err);
                    handled = true;
                }

                if (handled) {
                    pvis.move(t.n, 'ng');
                    apop(st.busy.hash, t);
                    st.bytes.uploaded += t.size;
                    return tasker();
                }

                toast.err(0, 'y o u   b r o k e    i t\nfile: ' + t.name + '\nerror: ' + err);
            };
            reader.readAsArrayBuffer(
                bobslice.call(t.fobj, car, cdr));

            return true;
        };

        var hash_calc = function (nch, buf) {
            while (segm_next());

            var hash_done = function (hashbuf) {
                var hslice = new Uint8Array(hashbuf).subarray(0, 33),
                    b64str = buf2b64(hslice);

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

                t.t_hashed = Date.now();

                pvis.seth(t.n, 2, 'hashing done');
                pvis.seth(t.n, 1, '📦 wait');
                apop(st.busy.hash, t);
                st.todo.handshake.push(t);
                tasker();
            };

            if (subtle)
                subtle.digest('SHA-512', buf).then(hash_done);
            else setTimeout(function () {
                var u8buf = new Uint8Array(buf);
                if (sha_js == 'hw') {
                    hashwasm.sha512(u8buf).then(function (v) {
                        hash_done(hex2u8(v))
                    });
                }
                else {
                    var hasher = new asmCrypto.Sha512();
                    hasher.process(u8buf);
                    hasher.finish();
                    hash_done(hasher.result);
                }
            }, 1);
        };

        t.t_hashing = Date.now();
        segm_next();
    }

    /////
    ////
    ///   head
    //

    function exec_head() {
        var t = st.todo.head.shift();
        st.busy.head.push(t);

        var xhr = new XMLHttpRequest();
        xhr.onerror = function () {
            console.log('head onerror, retrying', t);
            apop(st.busy.head, t);
            st.todo.head.unshift(t);
            tasker();
        };
        function orz(e) {
            var ok = false;
            if (xhr.status == 200) {
                var srv_sz = xhr.getResponseHeader('Content-Length'),
                    srv_ts = xhr.getResponseHeader('Last-Modified');

                ok = t.size == srv_sz;
                if (ok && datechk) {
                    srv_ts = new Date(srv_ts) / 1000;
                    ok = Math.abs(srv_ts - t.lmod) < 2;
                }
            }
            apop(st.busy.head, t);
            if (!ok)
                return push_t(st.todo.hash, t);

            t.done = true;
            st.bytes.hashed += t.size;
            st.bytes.uploaded += t.size;
            pvis.seth(t.n, 1, 'YOLO');
            pvis.seth(t.n, 2, "turbo'd");
            pvis.move(t.n, 'ok');
        };
        xhr.onload = function (e) {
            try { orz(e); } catch (ex) { vis_exh(ex + '', '', '', '', ex); }
        };

        xhr.open('HEAD', t.purl + t.name, true);
        xhr.send();
    }

    /////
    ////
    ///   handshake
    //

    function exec_handshake() {
        var t = st.todo.handshake.shift(),
            keepalive = t.keepalive,
            me = Date.now();

        st.busy.handshake.push(t);
        t.keepalive = undefined;
        t.t_busied = me;

        if (keepalive)
            console.log("sending keepalive handshake", t);

        var xhr = new XMLHttpRequest();
        xhr.onerror = function () {
            if (t.t_busied != me) {
                console.log('zombie handshake onerror,', t);
                return;
            }
            console.log('handshake onerror, retrying', t);
            apop(st.busy.handshake, t);
            st.todo.handshake.unshift(t);
            t.keepalive = keepalive;
            tasker();
        };
        function orz(e) {
            if (t.t_busied != me) {
                console.log('zombie handshake onload,', t);
                return;
            }
            if (xhr.status == 200) {
                t.t_handshake = Date.now();
                if (keepalive) {
                    apop(st.busy.handshake, t);
                    return;
                }

                var response = JSON.parse(xhr.responseText);
                if (!response.name) {
                    var msg = '',
                        smsg = '';

                    if (!response || !response.hits || !response.hits.length) {
                        smsg = '404';
                        msg = ('not found on server <a href="#" onclick="fsearch_explain(' +
                            (has(perms, 'write') ? '0' : '1') + ')" class="fsearch_explain">(explain)</a>');
                    }
                    else {
                        smsg = 'found';
                        var hit = response.hits[0],
                            msg = linksplit(hit.rp).join(''),
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
                    apop(st.busy.handshake, t);
                    st.bytes.uploaded += t.size;
                    t.done = true;
                    tasker();
                    return;
                }

                if (response.purl !== t.purl || response.name !== t.name) {
                    // server renamed us (file exists / path restrictions)
                    console.log("server-rename [" + t.purl + "] [" + t.name + "] to [" + response.purl + "] [" + response.name + "]");
                    t.purl = response.purl;
                    t.name = response.name;
                    pvis.seth(t.n, 0, linksplit(t.purl + t.name).join(' '));
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
                        return modal.alert('wtf negative index for hash "{0}" in task:\n{1}'.format(
                            missing[a], JSON.stringify(t)));

                    t.postlist.push(idx);
                    cbd[idx] = 0;
                }

                pvis.setat(t.n, cbd);
                pvis.prog(t, 0, cbd[0]);

                var done = true,
                    msg = '&#x1f3b7;&#x1f41b;';

                if (t.postlist.length) {
                    var arr = st.todo.upload,
                        sort = arr.length && arr[arr.length - 1].nfile > t.n;

                    for (var a = 0; a < t.postlist.length; a++)
                        arr.push({
                            'nfile': t.n,
                            'npart': t.postlist[a]
                        });

                    msg = 'uploading';
                    done = false;

                    if (sort)
                        arr.sort(function (a, b) {
                            return a.nfile < b.nfile ? -1 :
                            /*  */ a.nfile > b.nfile ? 1 :
                                    a.npart < b.npart ? -1 : 1;
                        });
                }
                pvis.seth(t.n, 1, msg);
                apop(st.busy.handshake, t);

                if (done) {
                    t.done = true;
                    st.bytes.uploaded += t.size - t.bytes_uploaded;
                    var spd1 = (t.size / ((t.t_hashed - t.t_hashing) / 1000.)) / (1024 * 1024.),
                        spd2 = (t.size / ((t.t_uploaded - t.t_uploading) / 1000.)) / (1024 * 1024.);

                    pvis.seth(t.n, 2, 'hash {0}, up {1} MB/s'.format(
                        spd1.toFixed(2), spd2.toFixed(2)));

                    pvis.move(t.n, 'ok');
                }
                else t.t_uploaded = undefined;

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

                if (rsp.indexOf('rate-limit ') !== -1) {
                    var penalty = rsp.replace(/.*rate-limit /, "").split(' ')[0];
                    console.log("rate-limit: " + penalty);
                    t.cooldown = Date.now() + parseFloat(penalty) * 1000;
                    apop(st.busy.handshake, t);
                    st.todo.handshake.unshift(t);
                    return;
                }

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

                    apop(st.busy.handshake, t);
                    tasker();
                    return;
                }
                toast.err(0, "server broke; hs-err {0} on file [{1}]:\n".format(
                    xhr.status, t.name) + (
                        (xhr.response && xhr.response.err) ||
                        (xhr.responseText && xhr.responseText) ||
                        "no further information"));
            }
        }
        xhr.onload = function (e) {
            try { orz(e); } catch (ex) { vis_exh(ex + '', '', '', '', ex); }
        };

        var req = {
            "name": t.name,
            "size": t.size,
            "lmod": t.lmod,
            "hash": t.hash
        };
        if (fsearch)
            req.srch = 1;

        xhr.open('POST', t.purl, true);
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

        if (!t.t_uploading)
            t.t_uploading = Date.now();

        pvis.seth(t.n, 1, "🚀 send");

        var chunksize = get_chunksize(t.size),
            car = npart * chunksize,
            cdr = car + chunksize;

        if (cdr >= t.size)
            cdr = t.size;

        function orz(xhr) {
            var txt = ((xhr.response && xhr.response.err) || xhr.responseText) + '';
            if (xhr.status == 200) {
                pvis.prog(t, npart, cdr - car);
                st.bytes.uploaded += cdr - car;
                t.bytes_uploaded += cdr - car;
            }
            else if (txt.indexOf('already got that') !== -1) {
                console.log("ignoring dupe-segment error", t);
            }
            else {
                toast.err(0, "server broke; cu-err {0} on file [{1}]:\n".format(
                    xhr.status, t.name) + (txt || "no further information"));
                return;
            }
            apop(st.busy.upload, upt);
            apop(t.postlist, npart);
            if (!t.postlist.length) {
                t.t_uploaded = Date.now();
                pvis.seth(t.n, 1, 'verifying');
                st.todo.handshake.unshift(t);
            }
            tasker();
        }
        function do_send() {
            var xhr = new XMLHttpRequest();
            xhr.upload.onprogress = function (xev) {
                pvis.prog(t, npart, xev.loaded);
            };
            xhr.onload = function (xev) {
                try { orz(xhr); } catch (ex) { vis_exh(ex + '', '', '', '', ex); }
            };
            xhr.onerror = function (xev) {
                if (crashed)
                    return;

                console.log('chunkpit onerror, retrying', t);
                do_send();
            };
            xhr.open('POST', t.purl, true);
            xhr.setRequestHeader("X-Up2k-Hash", t.hash[npart]);
            xhr.setRequestHeader("X-Up2k-Wark", t.wark);
            xhr.setRequestHeader('Content-Type', 'application/octet-stream');
            if (xhr.overrideMimeType)
                xhr.overrideMimeType('Content-Type', 'application/octet-stream');

            xhr.responseType = 'text';
            xhr.send(bobslice.call(t.fobj, car, cdr));
        }
        do_send();
    }

    /////
    ////
    ///   config ui
    //

    function onresize(e) {
        var bar = ebi('ops'),
            wpx = window.innerWidth,
            fpx = parseInt(getComputedStyle(bar)['font-size']),
            wem = wpx * 1.0 / fpx,
            wide = wem > 54,
            parent = ebi(wide && has(perms, 'write') ? 'u2btn_cw' : 'u2btn_ct'),
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

    if (is_touch) {
        // android-chrome wobbles for a bit; firefox / iOS-safari are OK
        setTimeout(onresize, 20);
        setTimeout(onresize, 100);
        setTimeout(onresize, 500);
    }

    var o = QSA('#u2conf *[tt]');
    for (var a = o.length - 1; a >= 0; a--) {
        o[a].parentNode.getElementsByTagName('input')[0].setAttribute('tt', o[a].getAttribute('tt'));
    }
    tt.att(QS('#u2conf'));

    function bumpthread2(e) {
        if (e.ctrlKey || e.altKey || e.metaKey || e.isComposing)
            return;

        if (e.code == 'ArrowUp')
            bumpthread(1);

        if (e.code == 'ArrowDown')
            bumpthread(-1);
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
            if (v < 0 || v > 64 || v !== v)
                return;

            parallel_uploads = v;
            swrite('nthread', v);
            clmod(obj, 'err');
            return;
        }

        parallel_uploads += dir;

        if (parallel_uploads < 0)
            parallel_uploads = 0;

        if (parallel_uploads > 16)
            parallel_uploads = 16;

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

    function tgl_turbo() {
        turbo = !turbo;
        bcfg_set('u2turbo', turbo);
        draw_turbo();
    }

    function tgl_datechk() {
        datechk = !datechk;
        bcfg_set('u2tdate', datechk);
    }

    function draw_turbo() {
        var msgu = '<p class="warn">WARNING: turbo enabled, <span>&nbsp;client may not detect and resume incomplete uploads; see turbo-button tooltip</span></p>',
            msgs = '<p class="warn">WARNING: turbo enabled, <span>&nbsp;search may give false-positives; see turbo-button tooltip</span></p>',
            msg = fsearch ? msgs : msgu,
            omsg = fsearch ? msgu : msgs,
            html = ebi('u2foot').innerHTML,
            ohtml = html;

        if (turbo && html.indexOf(msg) === -1)
            html = html.replace(omsg, '') + msg;
        else if (!turbo)
            html = html.replace(msgu, '').replace(msgs, '');

        if (html !== ohtml)
            ebi('u2foot').innerHTML = html;
    }
    draw_turbo();

    function set_fsearch(new_state) {
        var fixed = false;

        if (!ebi('fsearch')) {
            new_state = false;
        }
        else if (perms.length) {
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

        draw_turbo();
        onresize();
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

    ebi('nthread').onkeydown = bumpthread2;
    ebi('nthread').addEventListener('input', bumpthread, false);
    ebi('multitask').addEventListener('click', tgl_multitask, false);
    ebi('ask_up').addEventListener('click', tgl_ask_up, false);
    ebi('flag_en').addEventListener('click', tgl_flag_en, false);
    ebi('u2turbo').addEventListener('click', tgl_turbo, false);
    ebi('u2tdate').addEventListener('click', tgl_datechk, false);
    var o = ebi('fsearch');
    if (o)
        o.addEventListener('click', tgl_fsearch, false);

    var nodes = ebi('u2conf').getElementsByTagName('a');
    for (var a = nodes.length - 1; a >= 0; a--)
        nodes[a].addEventListener('touchend', nop, false);

    set_fsearch();
    bumpthread({ "target": 1 });
    if (parallel_uploads < 1)
        bumpthread(1);

    return { "init_deps": init_deps, "set_fsearch": set_fsearch }
}


function warn_uploader_busy(e) {
    e.preventDefault();
    e.returnValue = '';
    return "upload in progress, click abort and use the file-tree to navigate instead";
}


tt.init();

if (QS('#op_up2k.act'))
    goto_up2k();

apply_perms(perms);


(function () {
    goto();
    var op = sread('opmode');
    if (op !== null && op !== '.')
        try {
            goto(op);
        }
        catch (ex) { }
})();
