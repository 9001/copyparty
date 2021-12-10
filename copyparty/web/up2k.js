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
    catch (ex) {
        console.log('up2k init failed:', ex);
        toast.err(10, 'could not initialze up2k\n\n' + basenames(ex));
    }
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

    var markup = {
        '404': '<span class="err">404</span>',
        'ERROR': '<span class="err">ERROR</span>',
        'OS-error': '<span class="err">OS-error</span>',
        'found': '<span class="inf">found</span>',
        'YOLO': '<span class="inf">YOLO</span>',
        'done': '<span class="ok">done</span>',
    };

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
        obj.innerHTML = field == 'ht' ? (markup[html] || html) : html;
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
        var fo = r.tab[nfile], bd = 0;

        for (var a = 0; a < blocktab.length; a++)
            bd += blocktab[a];

        fo.bd = bd;
        fo.bd0 = bd;
        fo.cb = blocktab;
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
            f2f(p[0], 2), p[1], f2f(p[2], 2)
        );
        if (!r.is_act(fo.in))
            return;

        var obj = ebi('f{0}p'.format(fobj.n)),
            o1 = p[0] - 2, o2 = p[0] - 0.1, o3 = p[0];

        obj.innerHTML = fo.hp;
        obj.style.color = '#fff';
        obj.style.background = 'linear-gradient(90deg, #025, #06a ' + o1 + '%, #09d ' + o2 + '%, #222 ' + o3 + '%, #222 99%, #555)';
    };

    r.prog = function (fobj, nchunk, cbd) {
        var fo = r.tab[fobj.n],
            delta = cbd - fo.cb[nchunk];

        fo.cb[nchunk] = cbd;
        fo.bd += delta;

        var p = r.perc(fo.bd, fo.bd0, fo.bt, fobj.t_uploading);
        fo.hp = '{0}%, {1}, {2} MB/s'.format(
            f2f(p[0], 2), p[1], f2f(p[2], 2)
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
        obj.style.background = 'linear-gradient(90deg, #050, #270 ' + o1 + '%, #4b0 ' + o2 + '%, #222 ' + o3 + '%, #222 99%, #555)';
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
                qsr("#f" + nfile);
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
            qsr('#f' + (first++));
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
                td + 't">' + (markup[row.ht] || row.ht) +
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


function Donut(uc, st) {
    var r = this,
        el = null,
        psvg = null,
        o = 20 * 2 * Math.PI,
        optab = QS('#ops a[data-dest="up2k"]');

    optab.setAttribute('ico', optab.textContent);

    function svg(v) {
        var ico = v !== undefined,
            bg = ico ? '#333' : 'transparent',
            fg = '#fff',
            fsz = 52,
            rc = 32;

        if (r.eta && (r.eta > 99 || (uc.fsearch ? st.time.hashing : st.time.uploading) < 20))
            r.eta = null;

        if (r.eta) {
            if (r.eta < 10) {
                fg = '#fa0';
                fsz = 72;
            }
            rc = 8;
        }

        return (
            '<svg version="1.1" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">\n' +
            (ico ? '<rect width="100%" height="100%" rx="' + rc + '" fill="#333" />\n' :
                '<circle stroke="white" stroke-width="6" r="3" cx="32" cy="32" />\n') +
            (r.eta ? (
                '<text x="55%" y="58%" dominant-baseline="middle" text-anchor="middle"' +
                ' font-family="sans-serif" font-weight="bold" font-size="' + fsz + 'px"' +
                ' fill="' + fg + '">' + r.eta + '</text></svg>'
            ) : (
                '<circle class="donut" stroke="white" fill="' + bg +
                '" stroke-dashoffset="' + (ico ? v : o) + '" stroke-dasharray="' + o + ' ' + o +
                '" transform="rotate(270 32 32)" stroke-width="12" r="20" cx="32" cy="32" /></svg>'
            ))
        );
    }

    function pos() {
        return uc.fsearch ? Math.max(st.bytes.hashed, st.bytes.finished) : st.bytes.finished;
    }

    r.on = function (ya) {
        r.fc = r.tc = 99;
        r.eta = null;
        r.base = pos();
        optab.innerHTML = ya ? svg() : optab.getAttribute('ico');
        el = QS('#ops a .donut');
        if (!ya) {
            favico.upd();
            wintitle();
        }
    };
    r.do = function () {
        if (!el)
            return;

        var t = st.bytes.total - r.base,
            v = pos() - r.base,
            ofs = el.style.strokeDashoffset = o - o * v / t;

        if (++r.tc >= 10) {
            wintitle(f2f(v * 100 / t, 1) + '%, ' + r.eta + 's, ', true);
            r.tc = 0;
        }

        if (favico.txt) {
            if (++r.fc < 10 && r.eta && r.eta > 99)
                return;

            var s = svg(ofs);
            if (s == psvg || (r.eta === null && r.fc < 10))
                return;

            favico.upd('', s);
            psvg = s;
            r.fc = 0;
        }
    };
}


function fsearch_explain(n) {
    if (n)
        return toast.inf(60, 'your access to this folder is Read-Only\n\n' + (acct == '*' ? 'you are currently not logged in' : 'you are currently logged in as "' + acct + '"'));

    if (bcfg_get('fsearch', false))
        return toast.inf(60, 'you are currently in file-search mode\n\nswitch to upload-mode by clicking the green magnifying glass (next to the big yellow search button), and try uploading again\n\nsorry');

    return toast.inf(60, 'try again, it should work now');
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

    function got_deps() {
        return subtle || window.asmCrypto || window.hashwasm;
    }

    var loading_deps = false;
    function init_deps() {
        if (!loading_deps && !got_deps()) {
            var fn = 'sha512.' + sha_js + '.js';
            showmodal('<h1>loading ' + fn + '</h1><h2>since ' + shame + '</h2><h4>thanks chrome</h4>');
            import_js('/.cpr/deps/' + fn, unmodal);

            if (is_https)
                ebi('u2foot').innerHTML = shame + ' so <em>this</em> uploader will do like 500 KiB/s at best';
            else
                ebi('u2foot').innerHTML = 'seems like ' + shame + ' so do that if you want more performance <span style="color:#' +
                    (sha_js == 'ac' ? 'c84">(expecting 20' : '8a5">(but dont worry too much, expect 100') + ' MiB/s)</span>';
        }
        loading_deps = true;
    }

    if (perms.length && !has(perms, 'read') && has(perms, 'write'))
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
        uc = {},
        fdom_ctr = 0,
        min_filebuf = 0;

    bcfg_bind(uc, 'multitask', 'multitask', true, null, false);
    bcfg_bind(uc, 'ask_up', 'ask_up', true, null, false);
    bcfg_bind(uc, 'flag_en', 'flag_en', false, apply_flag_cfg);
    bcfg_bind(uc, 'fsearch', 'fsearch', false, set_fsearch, false);
    bcfg_bind(uc, 'turbo', 'u2turbo', false, draw_turbo, false);
    bcfg_bind(uc, 'datechk', 'u2tdate', true, null, false);

    var st = {
        "files": [],
        "seen": {},
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
            "total": 0,
            "hashed": 0,
            "uploaded": 0,
            "finished": 0
        },
        "time": {
            "hashing": 0,
            "uploading": 0,
            "busy": 0
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

    var pvis = new U2pvis("bz", '#u2cards'),
        donut = new Donut(uc, st);

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
    ebi('u2btn').onclick = nav;

    var nenters = 0;
    function ondrag(e) {
        if (++nenters <= 0)
            nenters = 1;

        if (onover.bind(this)(e))
            return true;

        var mup, up = QS('#up_zd');
        var msr, sr = QS('#srch_zd');
        if (!has(perms, 'write'))
            mup = 'you do not have write-access to this folder';
        if (!has(perms, 'read'))
            msr = 'you do not have read-access to this folder';
        if (!have_up2k_idx)
            msr = 'file-search is not enabled in server config';

        up.querySelector('span').textContent = mup || 'drop it here';
        sr.querySelector('span').textContent = msr || 'drop it here';
        clmod(up, 'err', mup);
        clmod(sr, 'err', msr);
        clmod(up, 'ok', !mup);
        clmod(sr, 'ok', !msr);
        ebi('up_dz').setAttribute('err', mup || '');
        ebi('srch_dz').setAttribute('err', msr || '');
    }
    function onoverb(e) {
        // zones are alive; disable cuo2duo branch
        document.body.ondragover = document.body.ondrop = null;
        return onover.bind(this)(e);
    }
    function onover(e) {
        try {
            var ok = false, dt = e.dataTransfer.types;
            for (var a = 0; a < dt.length; a++)
                if (dt[a] == 'Files')
                    ok = true;
                else if (dt[a] == 'text/uri-list')
                    return true;

            if (!ok)
                return true;
        }
        catch (ex) { }

        ev(e);
        e.dataTransfer.dropEffect = 'copy';
        e.dataTransfer.effectAllowed = 'copy';
        clmod(ebi('drops'), 'vis', 1);
        var v = this.getAttribute('v');
        if (v)
            clmod(ebi(v), 'hl', 1);
    }
    function offdrag(e) {
        ev(e);

        var v = this.getAttribute('v');
        if (v)
            clmod(ebi(v), 'hl');

        if (--nenters <= 0) {
            clmod(ebi('drops'), 'vis');
            clmod(ebi('up_dz'), 'hl');
            clmod(ebi('srch_dz'), 'hl');
            // cuo2duo:
            document.body.ondragover = onover;
            document.body.ondrop = gotfile;
        }
    }
    document.body.ondragenter = ondrag;
    document.body.ondragleave = offdrag;
    document.body.ondragover = onover;
    document.body.ondrop = gotfile;

    var drops = [ebi('up_dz'), ebi('srch_dz')];
    for (var a = 0; a < 2; a++) {
        drops[a].ondragenter = ondrag;
        drops[a].ondragover = onoverb;
        drops[a].ondragleave = offdrag;
        drops[a].ondrop = gotfile;
    }
    ebi('drops').onclick = offdrag;  // old ff

    function gotfile(e) {
        ev(e);
        nenters = 0;
        offdrag.bind(this)();
        var dz = this && this.getAttribute('id');
        if (!dz && e && e.clientY)
            // cuo2duo fallback
            dz = e.clientY < window.innerHeight / 2 ? 'up_dz' : 'srch_dz';

        var err = this.getAttribute('err');
        if (err)
            return modal.alert('sorry, ' + err);

        if ((dz == 'up_dz' && uc.fsearch) || (dz == 'srch_dz' && !uc.fsearch))
            tgl_fsearch();

        if (!QS('#op_up2k.act'))
            goto('up2k');

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
            nil_files = [],
            good_files = [],
            dirs = [];

        for (var a = 0; a < files.length; a++) {
            var fobj = files[a],
                dst = good_files;

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
                    dst = nil_files;
            }
            catch (ex) {
                dst = bad_files;
            }
            dst.push([fobj, fobj.name]);
        }
        if (dirs) {
            return read_dirs(null, [], dirs, good_files, nil_files, bad_files);
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
    function read_dirs(rd, pf, dirs, good, nil, bad, spins) {
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
                var msg = ['directory iterator got stuck on the following {0} items; good chance your browser is about to spinlock:<ul>'.format(missing.length)];
                for (var a = 0; a < Math.min(20, missing.length); a++)
                    msg.push('<li>' + esc(missing[a]) + '</li>');

                return modal.alert(msg.join('') + '</ul>', function () {
                    read_dirs(rd, [], [], good, nil, bad, spins);
                });
            }
            spins = 0;
        }

        if (!dirs.length) {
            if (!pf.length)
                return gotallfiles(good, nil, bad);

            console.log("retry pf, " + pf.length);
            setTimeout(function () {
                read_dirs(rd, pf, dirs, good, nil, bad, spins);
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
                        var dst = good;
                        try {
                            if (fobj.size < 1)
                                dst = nil;
                        }
                        catch (ex) {
                            dst = bad;
                        }
                        dst.push([fobj, name]);
                    });
                }
                ngot += 1;
            });
            if (!ngot) {
                dirs.shift();
                rd = null;
            }
            return read_dirs(rd, pf, dirs, good, nil, bad, spins);
        });
    }

    function gotallfiles(good_files, nil_files, bad_files) {
        var ntot = good_files.concat(nil_files, bad_files).length;
        if (bad_files.length) {
            var msg = 'These {0} files (of {1} total) were skipped, possibly due to filesystem permissions:\n'.format(bad_files.length, ntot);
            for (var a = 0, aa = Math.min(20, bad_files.length); a < aa; a++)
                msg += '-- ' + bad_files[a][1] + '\n';

            msg += '\nMaybe it works better if you select just one file';
            return modal.alert(msg, function () {
                gotallfiles(good_files, nil_files, []);
            });
        }

        if (nil_files.length) {
            var msg = 'These {0} files (of {1} total) are blank/empty; upload them anyways?\n'.format(nil_files.length, ntot);
            for (var a = 0, aa = Math.min(20, nil_files.length); a < aa; a++)
                msg += '-- ' + nil_files[a][1] + '\n';

            msg += '\nMaybe it works better if you select just one file';
            return modal.confirm(msg, function () {
                gotallfiles(good_files.concat(nil_files), [], []);
            }, function () {
                gotallfiles(good_files, [], []);
            });
        }

        good_files.sort(function (a, b) {
            a = a[1];
            b = b[1];
            return a < b ? -1 : a > b ? 1 : 0;
        });

        var msg = ['{0} these {1} files?<ul>'.format(uc.fsearch ? 'search' : 'upload', good_files.length)];
        for (var a = 0, aa = Math.min(20, good_files.length); a < aa; a++)
            msg.push('<li>' + esc(good_files[a][1]) + '</li>');

        if (uc.ask_up && !uc.fsearch)
            return modal.confirm(msg.join('') + '</ul>', function () { up_them(good_files); }, null);

        up_them(good_files);
    }

    function up_them(good_files) {
        var evpath = get_evpath(),
            draw_each = good_files.length < 50;

        for (var a = 0; a < good_files.length; a++) {
            var fobj = good_files[a][0],
                name = good_files[a][1],
                fdir = evpath,
                now = Date.now(),
                lmod = fobj.lastModified || now,
                ofs = name.lastIndexOf('/') + 1;

            if (ofs) {
                fdir += url_enc(name.slice(0, ofs));
                name = name.slice(ofs);
            }

            var entry = {
                "n": st.files.length,
                "t0": now,
                "fobj": fobj,
                "name": name,
                "size": fobj.size || 0,
                "lmod": lmod / 1000,
                "purl": fdir,
                "done": false,
                "bytes_uploaded": 0,
                "hash": []
            },
                key = name + '\n' + entry.size + '\n' + lmod + '\n' + uc.fsearch;

            if (uc.fsearch)
                entry.srch = 1;

            try {
                if (st.seen[fdir][key])
                    continue;
            }
            catch (ex) {
                st.seen[fdir] = {};
            }

            st.seen[fdir][key] = 1;

            pvis.addfile([
                uc.fsearch ? esc(entry.name) : linksplit(
                    entry.purl + uricom_enc(entry.name)).join(' '),
                '📐 hash',
                ''
            ], fobj.size, draw_each);

            st.bytes.total += fobj.size;
            st.files.push(entry);
            if (!entry.size)
                push_t(st.todo.handshake, entry);
            else if (uc.turbo)
                push_t(st.todo.head, entry);
            else
                push_t(st.todo.hash, entry);
        }
        if (!draw_each) {
            pvis.drawcard("q");
            pvis.changecard(pvis.act);
        }
    }

    function more_one_file() {
        fdom_ctr++;
        var elm = mknod('div');
        elm.innerHTML = '<input id="file{0}" type="file" name="file{0}[]" multiple="multiple" />'.format(fdom_ctr);
        ebi('u2form').appendChild(elm);
        ebi('file' + fdom_ctr).onchange = gotfile;
    }
    more_one_file();

    var etaref = 0, etaskip = 0, utw_minh = 0;
    function etafun() {
        var nhash = st.busy.head.length + st.busy.hash.length + st.todo.head.length + st.todo.hash.length,
            nsend = st.busy.upload.length + st.todo.upload.length,
            now = Date.now(),
            td = (now - (etaref || now)) / 1000.0;

        etaref = now;
        if (td > 1.2)
            td = 0.05;

        //ebi('acc_info').innerHTML = humantime(st.time.busy) + ' ' + f2f(now / 1000, 1);

        var minh = QS('#op_up2k.act') && st.is_busy ? Math.max(utw_minh, ebi('u2tab').offsetHeight + 32) : 0;
        if (utw_minh < minh || !utw_minh) {
            utw_minh = minh;
            ebi('u2tabw').style.minHeight = utw_minh + 'px';
        }

        if (!nhash)
            ebi('u2etah').innerHTML = 'Done ({0}, {1} files)'.format(humansize(st.bytes.hashed), pvis.ctr["ok"] + pvis.ctr["ng"]);

        if (!nsend && !nhash)
            ebi('u2etau').innerHTML = ebi('u2etat').innerHTML = (
                'Done ({0}, {1} files)'.format(humansize(st.bytes.uploaded), pvis.ctr["ok"] + pvis.ctr["ng"]));

        if (!st.busy.hash.length && !hashing_permitted())
            nhash = 0;

        if (!parallel_uploads || !(nhash + nsend) || (flag && flag.owner && !flag.ours))
            return;

        var t = [];
        if (nhash) {
            st.time.hashing += td;
            t.push(['u2etah', st.bytes.hashed, st.bytes.hashed, st.time.hashing]);
            if (uc.fsearch)
                t.push(['u2etat', st.bytes.hashed, st.bytes.hashed, st.time.hashing]);
        }
        if (nsend) {
            st.time.uploading += td;
            t.push(['u2etau', st.bytes.uploaded, st.bytes.finished, st.time.uploading]);
        }
        if ((nhash || nsend) && !uc.fsearch) {
            if (!st.bytes.finished) {
                ebi('u2etat').innerHTML = '(preparing to upload)';
            }
            else {
                st.time.busy += td;
                t.push(['u2etat', st.bytes.finished, st.bytes.finished, st.time.busy]);
            }
        }
        for (var a = 0; a < t.length; a++) {
            var rem = st.bytes.total - t[a][2],
                bps = t[a][1] / t[a][3],
                eta = Math.floor(rem / bps);

            if (t[a][1] < 1024 || t[a][3] < 0.1) {
                ebi(t[a][0]).innerHTML = '(preparing to upload)';
                continue;
            }

            donut.eta = eta;
            if (etaskip)
                continue;

            ebi(t[a][0]).innerHTML = '{0}, {1}/s, {2}'.format(
                humansize(rem), humansize(bps, 1), humantime(eta));
        }
        if (++etaskip > 2)
            etaskip = 0;
    }

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

        if ((uc.multitask ? 1 : 0) <
            st.todo.upload.length +
            st.busy.upload.length)
            return false;

        return true;
    }

    function hashing_permitted() {
        if (!parallel_uploads)
            return false;

        if (uc.multitask) {
            var ahead = st.bytes.hashed - st.bytes.finished;
            return ahead < 1024 * 1024 * 1024 * 4 &&
                st.todo.handshake.length + st.busy.handshake.length < 16;
        }
        return handshakes_permitted() && 0 ==
            st.todo.handshake.length +
            st.busy.handshake.length +
            st.todo.upload.length +
            st.busy.upload.length;
    }

    var tasker = (function () {
        var running = false,
            was_busy = false;

        function defer() {
            running = false;
        }

        function taskerd() {
            if (running)
                return;

            if (crashed || !got_deps())
                return defer();

            running = true;
            while (true) {
                var now = Date.now(),
                    oldest_active = Math.min(  // gzip take the wheel
                        st.todo.head.length ? st.todo.head[0].n : st.files.length,
                        st.todo.hash.length ? st.todo.hash[0].n : st.files.length,
                        st.todo.upload.length ? st.todo.upload[0].nfile : st.files.length,
                        st.todo.handshake.length ? st.todo.handshake[0].n : st.files.length,
                        st.busy.head.length ? st.busy.head[0].n : st.files.length,
                        st.busy.hash.length ? st.busy.hash[0].n : st.files.length,
                        st.busy.upload.length ? st.busy.upload[0].nfile : st.files.length,
                        st.busy.handshake.length ? st.busy.handshake[0].n : st.files.length),
                    is_busy = oldest_active < st.files.length;

                if (was_busy && !is_busy) {
                    for (var a = 0; a < st.files.length; a++) {
                        var t = st.files[a];
                        if (t.want_recheck) {
                            t.rechecks++;
                            t.want_recheck = false;
                            push_t(st.todo.handshake, t);
                        }
                    }
                    is_busy = st.todo.handshake.length;
                    try {
                        if (!is_busy && !uc.fsearch && !msel.getsel().length && (!mp.au || mp.au.paused))
                            treectl.goto(get_evpath());
                    }
                    catch (ex) { }
                }

                if (was_busy != is_busy) {
                    st.is_busy = was_busy = is_busy;

                    window[(is_busy ? "add" : "remove") +
                        "EventListener"]("beforeunload", warn_uploader_busy);

                    donut.on(is_busy);

                    if (!is_busy) {
                        var k = uc.fsearch ? 'searches' : 'uploads',
                            ks = uc.fsearch ? 'Search' : 'Upload',
                            tok = uc.fsearch ? 'successful (found on server)' : 'completed successfully',
                            tng = uc.fsearch ? 'failed (NOT found on server)' : 'failed, sorry',
                            ok = pvis.ctr["ok"],
                            ng = pvis.ctr["ng"],
                            t = uc.ask_up ? 0 : 10;

                        if (ok && ng)
                            toast.warn(t, 'Finished, but some {0} failed:\n{1} {2},\n{3} {4}'.format(k, ok, tok, ng, tng));
                        else if (ok > 1)
                            toast.ok(t, 'All {1} {0} {2}'.format(k, ok, tok));
                        else if (ok)
                            toast.ok(t, '{0} {1}'.format(ks, tok));
                        else if (ng > 1)
                            toast.err(t, 'All {1} {0} {2}'.format(k, ng, tng));
                        else if (ng)
                            toast.err(t, '{0} {1}'.format(ks, tng));

                        timer.rm(etafun);
                        timer.rm(donut.do);
                        utw_minh = 0;
                    }
                    else {
                        timer.add(donut.do);
                        timer.add(etafun, false);
                        ebi('u2etas').style.textAlign = 'left';
                    }
                    etafun();
                    if (pvis.act == 'bz')
                        pvis.changecard('bz');
                }

                if (flag) {
                    if (is_busy) {
                        flag.take(now);
                        ebi('u2flagblock').style.display = flag.ours ? '' : 'block';
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
                    st.busy.head.length < parallel_uploads &&
                    (!is_busy || st.todo.head[0].n - oldest_active < parallel_uploads * 2)) {
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
        timer.add(taskerd, true);
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
            st.bytes.hashed += cdr - car;

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
                    pvis.seth(t.n, 2, err + ' @ ' + car);
                    console.log('OS-error', reader.error, '@', car);
                    handled = true;
                }

                if (handled) {
                    pvis.move(t.n, 'ng');
                    apop(st.busy.hash, t);
                    st.bytes.finished += t.size;
                    return;
                }

                toast.err(0, 'y o u   b r o k e    i t\nfile: ' + esc(t.name + '') + '\nerror: ' + err);
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
        };
        function orz(e) {
            var ok = false;
            if (xhr.status == 200) {
                var srv_sz = xhr.getResponseHeader('Content-Length'),
                    srv_ts = xhr.getResponseHeader('Last-Modified');

                ok = t.size == srv_sz;
                if (ok && uc.datechk) {
                    srv_ts = new Date(srv_ts) / 1000;
                    ok = Math.abs(srv_ts - t.lmod) < 2;
                }
            }
            apop(st.busy.head, t);
            if (!ok && !t.srch) {
                push_t(st.todo.hash, t);
                tasker();
                return;
            }

            t.done = true;
            t.fobj = null;
            st.bytes.hashed += t.size;
            st.bytes.finished += t.size;
            pvis.move(t.n, 'bz');
            pvis.seth(t.n, 1, ok ? 'YOLO' : '404');
            pvis.seth(t.n, 2, "turbo'd");
            pvis.move(t.n, ok ? 'ok' : 'ng');
            tasker();
        };
        xhr.onload = function (e) {
            try { orz(e); } catch (ex) { vis_exh(ex + '', '', '', '', ex); }
        };

        xhr.open('HEAD', t.purl + uricom_enc(t.name) + '?raw', true);
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
                        var msg = [];
                        for (var a = 0, aa = Math.min(20, response.hits.length); a < aa; a++) {
                            var hit = response.hits[a],
                                tr = unix2iso(hit.ts),
                                tu = unix2iso(t.lmod),
                                diff = parseInt(t.lmod) - parseInt(hit.ts),
                                cdiff = (Math.abs(diff) <= 2) ? '3c0' : 'f0b',
                                sdiff = '<span style="color:#' + cdiff + '">diff ' + diff;

                            msg.push(linksplit(hit.rp).join('') + '<br /><small>' + tr + ' (srv), ' + tu + ' (You), ' + sdiff + '</small></span>');
                        }
                        msg = msg.join('<br />\n');
                    }
                    pvis.seth(t.n, 2, msg);
                    pvis.seth(t.n, 1, smsg);
                    pvis.move(t.n, smsg == '404' ? 'ng' : 'ok');
                    apop(st.busy.handshake, t);
                    st.bytes.finished += t.size;
                    t.done = true;
                    t.fobj = null;
                    tasker();
                    return;
                }

                var rsp_purl = url_enc(response.purl);
                if (rsp_purl !== t.purl || response.name !== t.name) {
                    // server renamed us (file exists / path restrictions)
                    console.log("server-rename [" + t.purl + "] [" + t.name + "] to [" + rsp_purl + "] [" + response.name + "]");
                    t.purl = rsp_purl;
                    t.name = response.name;
                    pvis.seth(t.n, 0, linksplit(t.purl + uricom_enc(t.name)).join(' '));
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
                    msg = 'done';

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
                    t.fobj = null;
                    st.bytes.finished += t.size - t.bytes_uploaded;
                    var spd1 = (t.size / ((t.t_hashed - t.t_hashing) / 1000.)) / (1024 * 1024.),
                        spd2 = (t.size / ((t.t_uploaded - t.t_uploading) / 1000.)) / (1024 * 1024.);

                    pvis.seth(t.n, 2, 'hash {0}, up {1} MB/s'.format(
                        f2f(spd1, 2), isNaN(spd2) ? '--' : f2f(spd2, 2)));

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

                st.bytes.finished += t.size;
                var err_pend = rsp.indexOf('partial upload exists') + 1,
                    err_dupe = rsp.indexOf('file already exists') + 1;

                if (err_pend || err_dupe) {
                    err = rsp;
                    ofs = err.indexOf('\n/');
                    if (ofs !== -1) {
                        err = err.slice(0, ofs + 1) + linksplit(err.slice(ofs + 2).trimEnd()).join(' ');
                    }
                    if (!t.rechecks && err_pend) {
                        t.rechecks = 0;
                        t.want_recheck = true;
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
        if (t.srch)
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
            t = st.files[upt.nfile],
            tries = 0;

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
                st.bytes.finished += cdr - car;
                st.bytes.uploaded += cdr - car;
                t.bytes_uploaded += cdr - car;
            }
            else if (txt.indexOf('already got that') + 1 ||
                txt.indexOf('already being written') + 1) {
                console.log("ignoring dupe-segment error", t);
            }
            else {
                toast.err(0, "server broke; cu-err {0} on file [{1}]:\n".format(
                    xhr.status, t.name) + (txt || "no further information"));
                return;
            }
            orz2(xhr);
        }
        function orz2(xhr) {
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

                if (!toast.visible)
                    toast.warn(9.98, "failed to upload a chunk;\nprobably harmless, continuing\n\n" + t.name);

                console.log('chunkpit onerror,', ++tries, t);
                orz2(xhr);
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
            write = has(perms, 'write'),
            wide = write && wem > 54 ? 'w' : '',
            parent = ebi(wide && write ? 'u2btn_cw' : 'u2btn_ct'),
            btn = ebi('u2btn');

        //console.log([wpx, fpx, wem]);
        if (btn.parentNode !== parent) {
            parent.appendChild(btn);
            ebi('u2conf').setAttribute('class', wide);
            ebi('u2cards').setAttribute('class', wide);
            ebi('u2etaw').setAttribute('class', wide);
        }

        wide = write && wem > 78 ? 'ww' : wide;
        parent = ebi(wide == 'ww' && write ? 'u2c3w' : 'u2c3t');
        var its = [ebi('u2etaw'), ebi('u2cards')];
        if (its[0].parentNode !== parent) {
            ebi('u2conf').setAttribute('class', wide);
            for (var a = 0; a < 2; a++) {
                parent.appendChild(its[a]);
                its[a].setAttribute('class', wide);
            }
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

    var o = QSA('#u2conf .c *[tt]');
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

    function tgl_fsearch() {
        set_fsearch(!uc.fsearch);
    }

    function draw_turbo() {
        var msgu = '<p class="warn">WARNING: turbo enabled, <span>&nbsp;client may not detect and resume incomplete uploads; see turbo-button tooltip</span></p>',
            msgs = '<p class="warn">WARNING: turbo enabled, <span>&nbsp;search results can be incorrect; see turbo-button tooltip</span></p>',
            msg = uc.fsearch ? msgs : msgu,
            omsg = uc.fsearch ? msgu : msgs,
            html = ebi('u2foot').innerHTML,
            ohtml = html;

        if (uc.turbo && html.indexOf(msg) === -1)
            html = html.replace(omsg, '') + msg;
        else if (!uc.turbo)
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
            if (!has(perms, 'read') || !have_up2k_idx) {
                new_state = false;
                fixed = true;
            }
        }

        if (new_state !== undefined) {
            uc.fsearch = new_state;
            bcfg_set('fsearch', uc.fsearch);
        }

        try {
            QS('label[for="fsearch"]').style.display = QS('#fsearch').style.display = fixed ? 'none' : '';
        }
        catch (ex) { }

        try {
            var ico = uc.fsearch ? '🔎' : '🚀',
                desc = uc.fsearch ? 'Search' : 'Upload';

            clmod(ebi('op_up2k'), 'srch', uc.fsearch);
            ebi('u2bm').innerHTML = ico + ' <sup>' + desc + '</sup>';
        }
        catch (ex) { }

        draw_turbo();
        onresize();
    }

    function apply_flag_cfg() {
        if (uc.flag_en && !flag) {
            try {
                flag = up2k_flagbus();
            }
            catch (ex) {
                toast.err(5, "not supported on your browser:\n" + esc(basenames(ex)));
                bcfg_set('flag_en', false);
            }
        }
        else if (!uc.flag_en && flag) {
            if (flag.ours)
                flag.give();

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
    ebi('nthread').oninput = bumpthread;

    ebi('u2etas').onclick = function (e) {
        ev(e);
        clmod(ebi('u2etas'), 'o', 't');
    };

    set_fsearch();
    bumpthread({ "target": 1 });
    if (parallel_uploads < 1)
        bumpthread(1);

    return { "init_deps": init_deps, "set_fsearch": set_fsearch, "ui": pvis, "st": st, "uc": uc }
}


function warn_uploader_busy(e) {
    e.preventDefault();
    e.returnValue = '';
    return "upload in progress, click abort and use the file-tree to navigate instead";
}


tt.init();
favico.init();
ebi('ico1').onclick = function () {
    var a = favico.txt == this.textContent;
    swrite('icot', a ? 'c' : this.textContent);
    swrite('icof', a ? null : '000');
    swrite('icob', a ? null : '');
    favico.init();
};


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
