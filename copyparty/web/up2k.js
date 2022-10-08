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
    up2k_hooks = [],
    hws = [],
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


function U2pvis(act, btns, uc, st) {
    var r = this;
    r.act = act;
    r.ctr = { "ok": 0, "ng": 0, "bz": 0, "q": 0 };
    r.tab = [];
    r.hq = {};
    r.head = 0;
    r.tail = -1;
    r.wsz = 3;
    r.npotato = 99;
    r.modn = 0;
    r.modv = 0;
    r.mod0 = null;

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
        if (uc.potato && !uc.fsearch)
            return false;

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

        var k = 'f' + nfile + '' + field.slice(1),
            obj = ebi(k);

        obj.innerHTML = field == 'ht' ? (markup[html] || html) : html;
        if (field == 'hp') {
            obj.style.color = '';
            obj.style.background = '';
            delete r.hq[nfile];
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

        fo.hp = f2f(p[0], 2) + '%, ' + p[1] + ', ' + f2f(p[2], 2) + ' MB/s';
        if (!r.is_act(fo.in))
            return;

        var o1 = p[0] - 2, o2 = p[0] - 0.1, o3 = p[0];

        r.hq[fobj.n] = [fo.hp, '#fff', 'linear-gradient(90deg, #025, #06a ' + o1 + '%, #09d ' + o2 + '%, #222 ' + o3 + '%, #222 99%, #555)'];
    };

    r.prog = function (fobj, nchunk, cbd) {
        var fo = r.tab[fobj.n],
            delta = cbd - fo.cb[nchunk];

        fo.cb[nchunk] = cbd;
        fo.bd += delta;

        if (!fo.bd)
            return;

        var p = r.perc(fo.bd, fo.bd0, fo.bt, fobj.t_uploading);
        fo.hp = f2f(p[0], 2) + '%, ' + p[1] + ', ' + f2f(p[2], 2) + ' MB/s';

        if (!r.is_act(fo.in))
            return;

        var obj = ebi('f' + fobj.n + 'p'),
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

        r.hq[fobj.n] = [fo.hp, '#fff', 'linear-gradient(90deg, #050, #270 ' + o1 + '%, #4b0 ' + o2 + '%, #222 ' + o3 + '%, #222 99%, #555)'];
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

        while (st.car < r.tab.length && has(['ok', 'ng'], r.tab[st.car].in))
            st.car++;

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
        var mod = 0,
            t0 = Date.now(),
            first = QS('#u2tab>tbody>tr:first-child');

        if (!first)
            return;

        var last = QS('#u2tab>tbody>tr:last-child');
        first = parseInt(first.getAttribute('id').slice(1));
        last = parseInt(last.getAttribute('id').slice(1));

        while (r.head - first > r.wsz) {
            qsr('#f' + (first++));
            mod++;
        }
        while (last - r.tail < r.wsz && last < r.tab.length - 1) {
            var obj = ebi('f' + (++last));
            if (!obj) {
                r.addrow(last);
                mod++;
            }
        }
        if (mod && r.modn < 200 && ebi('repl').offsetTop) {
            if (++r.modn >= 10) {
                if (r.modn == 10)
                    r.mod0 = Date.now();

                r.modv += Date.now() - t0;
            }

            if (r.modn >= 200) {
                var n = r.modn - 10,
                    ipu = r.modv / n,
                    spu = (Date.now() - r.mod0) / n,
                    ir = spu / ipu;

                console.log('bzw:', f2f(ipu, 2), ' spu:', f2f(spu, 2), ' ir:', f2f(ir, 2), ' tab:', r.tab.length);
                // efficiency estimates;
                // ir: 5=16% 4=50%,30% 27=100%
                // ipu: 2.7=16% 2=30% 1.6=50% 1.8=100% (ng for big files)
                if (ipu >= 1.5 && ir <= 9 && r.tab.length >= 1000 && r.tab[Math.floor(r.tab.length / 3)].bt <= 1024 * 1024 * 4)
                    r.go_potato();
            }
        }
    };

    r.potatolabels = function () {
        var ode = ebi('u2depotato'),
            oen = ebi('u2enpotato');

        if (!ode)
            return;

        ode.style.display = uc.potato ? '' : 'none';
        oen.style.display = uc.potato ? 'none' : '';
    }

    r.potato = function () {
        ebi('u2tabw').style.minHeight = '';
        QS('#u2cards a[act="bz"]').click();
        timer[uc.potato ? "add" : "rm"](draw_potato);
        timer[uc.potato ? "rm" : "add"](apply_html);
        r.potatolabels();
    };

    r.go_potato = function () {
        r.go_potato = noop;
        var ode = mknod('div', 'u2depotato'),
            oen = mknod('div', 'u2enpotato'),
            u2f = ebi('u2foot'),
            btn = ebi('potato');

        ode.innerHTML = L.u_depot;
        oen.innerHTML = L.u_enpot;

        if (sread('potato') === null) {
            btn.click();
            toast.inf(30, L.u_gotpot);
            localStorage.removeItem('potato');
        }

        u2f.appendChild(ode);
        u2f.appendChild(oen);
        ode.onclick = oen.onclick = btn.onclick;
        r.potatolabels();
    };

    function draw_potato() {
        if (++r.npotato < 2)
            return;

        r.npotato = 0;
        var html = [
            "<p>files: &nbsp; <b>{0}</b> finished, &nbsp; <b>{1}</b> failed, &nbsp; <b>{2}</b> busy, &nbsp; <b>{3}</b> queued</p>".format(
                r.ctr.ok, r.ctr.ng, r.ctr.bz, r.ctr.q)];

        while (r.head < r.tab.length && has(["ok", "ng"], r.tab[r.head].in))
            r.head++;

        var act = null;
        if (r.head < r.tab.length)
            act = r.tab[r.head];

        if (act)
            html.push("<p>file {0} of {1} : &nbsp; {2} &nbsp; <code>{3}</code></p>\n<div>{4}</div>".format(
                r.head + 1, r.tab.length, act.ht, act.hp, act.hn));

        html = html.join('\n');
        if (r.hpotato == html)
            return;

        r.hpotato = html;
        ebi('u2mu').innerHTML = html;
    }

    function apply_html() {
        var oq = {}, n = 0;
        for (var k in r.hq) {
            var o = ebi('f' + k + 'p');
            if (!o)
                continue;

            oq[k] = o;
            n++;
        }
        if (!n)
            return;

        for (var k in oq) {
            var o = oq[k],
                v = r.hq[k];

            o.innerHTML = v[0];
            o.style.color = v[1];
            o.style.background = v[2];
        }
        r.hq = {};
    }

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
        var el = ebi('u2tab');
        el.tBodies[0].innerHTML = html.join('\n');
        el.className = (uc.fsearch ? 'srch ' : 'up ') + r.act;
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

        var obj = mknod('tr', 'f' + nfile);
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
    r.potato();
}


function Donut(uc, st) {
    var r = this,
        el = null,
        psvg = null,
        tenstrobe = null,
        tstrober = null,
        strobes = [],
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
        r.fc = r.tc = r.dc = 99;
        r.eta = null;
        r.base = pos();
        optab.innerHTML = ya ? svg() : optab.getAttribute('ico');
        el = QS('#ops a .donut');
        clearTimeout(tenstrobe);
        if (!ya) {
            favico.upd();
            wintitle();
            if (document.visibilityState == 'hidden')
                tenstrobe = setTimeout(enstrobe, 500); //debounce
        }
    };

    r.do = function () {
        if (!el)
            return;

        var t = st.bytes.total - r.base,
            v = pos() - r.base,
            ofs = o - o * v / t;

        if (!uc.potato || ++r.dc >= 4) {
            el.style.strokeDashoffset = ofs;
            r.dc = 0;
        }

        if (++r.tc >= 10) {
            wintitle("{0}%, {1}, #{2}, ".format(
                f2f(v * 100 / t, 1), shumantime(r.eta), st.files.length - st.nfile.upload), true);
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

    function enstrobe() {
        strobes = ['████████████████', '________________', '████████████████'];
        tstrober = setInterval(strobe, 300);

        if (uc.upsfx && actx && actx.state != 'suspended')
            sfx();

        // firefox may forget that filedrops are user-gestures so it can skip this:
        if (uc.upnag && window.Notification && Notification.permission == 'granted')
            new Notification(uc.nagtxt);
    }

    function strobe() {
        var txt = strobes.pop();
        wintitle(txt);
        if (!txt)
            clearInterval(tstrober);
    }

    function sfx() {
        var osc = actx.createOscillator(),
            gain = actx.createGain(),
            gg = gain.gain,
            ft = [660, 880, 440, 660, 880],
            ofs = 0;

        osc.connect(gain);
        gain.connect(actx.destination);
        var ct = actx.currentTime + 0.03;

        osc.type = 'triangle';
        while (ft.length)
            osc.frequency.setTargetAtTime(
                ft.shift(), ct + (ofs += 0.05), 0.001);

        gg.value = 0.15;
        gg.setTargetAtTime(0.8, ct, 0.01);
        gg.setTargetAtTime(0.3, ct + 0.13, 0.01);
        gg.setTargetAtTime(0, ct + ofs + 0.05, 0.02);

        osc.start();
        setTimeout(function () {
            osc.stop();
            osc.disconnect();
            gain.disconnect();
        }, 500);
    }
}


function fsearch_explain(n) {
    if (n)
        return toast.inf(60, L.ue_ro + (acct == '*' ? L.ue_nl : L.ue_la).format(acct));

    if (bcfg_get('fsearch', false))
        return toast.inf(60, L.ue_sr);

    return toast.inf(60, L.ue_ta);
}


function up2k_init(subtle) {
    var r = {
        "init_deps": init_deps,
        "set_fsearch": set_fsearch,
        "gotallfiles": [gotallfiles]  // hooks
    };

    setTimeout(function () {
        if (window.WebAssembly && !hws.length)
            fetch('/.cpr/w.hash.js' + CB);
    }, 1000);

    function showmodal(msg) {
        ebi('u2notbtn').innerHTML = msg;
        ebi('u2btn').style.display = 'none';
        ebi('u2notbtn').style.display = 'block';
        ebi('u2conf').style.opacity = '0.5';
    }

    function unmodal() {
        ebi('u2notbtn').style.display = 'none';
        ebi('u2conf').style.opacity = '1';
        ebi('u2btn').style.display = '';
        ebi('u2notbtn').innerHTML = '';
    }

    var suggest_up2k = L.u_su2k;

    function got_deps() {
        return subtle || window.asmCrypto || window.hashwasm;
    }

    var loading_deps = false;
    function init_deps() {
        if (!loading_deps && !got_deps()) {
            var fn = 'sha512.' + sha_js + '.js',
                m = L.u_https1 + ' <a href="' + (window.location + '').replace(':', 's:') + '">' + L.u_https2 + '</a> ' + L.u_https3;

            showmodal('<h1>loading ' + fn + '</h1>');
            import_js('/.cpr/deps/' + fn, unmodal);

            if (HTTPS) {
                // chrome<37 firefox<34 edge<12 opera<24 safari<7
                m = L.u_ancient;
                setmsg('');
            }
            qsr('#u2depmsg');
            var o = mknod('div', 'u2depmsg');
            o.innerHTML = m;
            ebi('u2foot').appendChild(o);
        }
        loading_deps = true;
    }

    if (perms.length && !has(perms, 'read') && has(perms, 'write'))
        goto('up2k');

    function setmsg(msg, type) {
        if (msg !== undefined) {
            ebi('u2err').className = type;
            ebi('u2err').innerHTML = msg;
        }
        else {
            ebi('u2err').className = '';
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

    setmsg(suggest_up2k, 'msg');

    var parallel_uploads = icfg_get('nthread'),
        uc = {},
        fdom_ctr = 0,
        biggest_file = 0;

    bcfg_bind(uc, 'multitask', 'multitask', true, null, false);
    bcfg_bind(uc, 'potato', 'potato', false, set_potato, false);
    bcfg_bind(uc, 'ask_up', 'ask_up', true, null, false);
    bcfg_bind(uc, 'fsearch', 'fsearch', false, set_fsearch, false);

    bcfg_bind(uc, 'flag_en', 'flag_en', false, apply_flag_cfg);
    bcfg_bind(uc, 'turbo', 'u2turbo', turbolvl > 1, draw_turbo);
    bcfg_bind(uc, 'datechk', 'u2tdate', turbolvl < 3, null);
    bcfg_bind(uc, 'az', 'u2sort', u2sort.indexOf('n') + 1, set_u2sort);
    bcfg_bind(uc, 'hashw', 'hashw', !!window.WebAssembly && (!subtle || !CHROME || MOBILE), set_hashw);
    bcfg_bind(uc, 'upnag', 'upnag', false, set_upnag);
    bcfg_bind(uc, 'upsfx', 'upsfx', false);

    var st = {
        "files": [],
        "nfile": {
            "hash": 0,
            "upload": 0
        },
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
        },
        "eta": {
            "h": "",
            "u": "",
            "t": ""
        },
        "car": 0,
        "slow_io": null,
        "oserr": false,
        "modn": 0,
        "modv": 0,
        "mod0": null
    };

    function push_t(arr, t) {
        var sort = arr.length && arr[arr.length - 1].n > t.n;
        arr.push(t);
        if (sort)
            arr.sort(function (a, b) {
                return a.n < b.n ? -1 : 1;
            });
    }

    var pvis = new U2pvis("bz", '#u2cards', uc, st),
        donut = new Donut(uc, st);

    r.ui = pvis;
    r.st = st;
    r.uc = uc;

    if (!window.File || !window.FileReader || !window.FileList || !File.prototype || !File.prototype.slice)
        return un2k(L.u_ever);

    var flag = false;
    apply_flag_cfg();
    set_fsearch();

    function nav() {
        start_actx();

        var uf = function () { ebi('file' + fdom_ctr).click(); },
            ud = function () { ebi('dir' + fdom_ctr).click(); };

        // too buggy on chrome <= 72
        var m = / Chrome\/([0-9]+)\./.exec(navigator.userAgent);
        if (m && parseInt(m[1]) < 73)
            return uf();

        // phones dont support folder upload
        if (MOBILE)
            return uf();

        modal.confirm(L.u_nav_m, uf, ud, null, L.u_nav_b);
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
            mup = L.u_ewrite;
        if (!has(perms, 'read'))
            msr = L.u_eread;
        if (!have_up2k_idx)
            msr = L.u_enoi;

        up.querySelector('span').textContent = mup || L.udt_drop;
        sr.querySelector('span').textContent = msr || L.udt_drop;
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
        try {
            e.dataTransfer.dropEffect = 'copy';
            e.dataTransfer.effectAllowed = 'copy';
        }
        catch (ex) {
            document.body.ondragenter = document.body.ondragleave = document.body.ondragover = null;
            return modal.alert('your browser does not support drag-and-drop uploading');
        }
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

    function gotdir(e) {
        ev(e);
        var good_files = [],
            nil_files = [],
            bad_files = [];

        for (var a = 0, aa = e.target.files.length; a < aa; a++) {
            var fobj = e.target.files[a],
                name = fobj.webkitRelativePath,
                dst = good_files;

            try {
                if (!name)
                    throw 1;

                if (fobj.size < 1)
                    dst = nil_files;
            }
            catch (ex) {
                dst = bad_files;
            }
            dst.push([fobj, name]);
        }

        if (!good_files.length && bad_files.length)
            return toast.err(30, "that's not a folder!\n\nyour browser is too old,\nplease try dragdrop instead");

        return read_dirs(null, [], [], good_files, nil_files, bad_files);
    }

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

        toast.inf(0, 'Scanning files...');

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
        start_actx();  // good enough for chrome; not firefox
        return read_dirs(null, [], dirs, good_files, nil_files, bad_files);
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
                // call first hook, pass list of remaining hooks to call
                return r.gotallfiles[0](good, nil, bad, r.gotallfiles.slice(1));

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
        if (toast.txt == 'Scanning files...')
            toast.hide();

        if (uc.fsearch && !uc.turbo)
            nil_files = [];

        var ntot = good_files.concat(nil_files, bad_files).length;
        if (bad_files.length) {
            var msg = L.u_badf.format(bad_files.length, ntot);
            for (var a = 0, aa = Math.min(20, bad_files.length); a < aa; a++)
                msg += '-- ' + bad_files[a][1] + '\n';

            msg += L.u_just1;
            return modal.alert(msg, function () {
                start_actx();
                gotallfiles(good_files, nil_files, []);
            });
        }

        if (nil_files.length) {
            var msg = L.u_blankf.format(nil_files.length, ntot);
            for (var a = 0, aa = Math.min(20, nil_files.length); a < aa; a++)
                msg += '-- ' + nil_files[a][1] + '\n';

            msg += L.u_just1;
            return modal.confirm(msg, function () {
                start_actx();
                gotallfiles(good_files.concat(nil_files), [], []);
            }, function () {
                start_actx();
                gotallfiles(good_files, [], []);
            });
        }

        good_files.sort(function (a, b) {
            a = a[1];
            b = b[1];
            return a < b ? -1 : a > b ? 1 : 0;
        });

        var msg = [];

        if (lifetime)
            msg.push('<b>' + L.u_up_life.format(lhumantime(st.lifetime || lifetime)) + '</b>\n\n');

        if (FIREFOX && good_files.length > 3000)
            msg.push(L.u_ff_many + "\n\n");

        msg.push(L.u_asku.format(good_files.length, esc(get_vpath())) + '<ul>');
        for (var a = 0, aa = Math.min(20, good_files.length); a < aa; a++)
            msg.push('<li>' + esc(good_files[a][1]) + '</li>');

        if (uc.ask_up && !uc.fsearch)
            return modal.confirm(msg.join('') + '</ul>', function () {
                start_actx();
                up_them(good_files);
                toast.inf(15, L.u_unpt, L.u_unpt);
            }, null);

        up_them(good_files);
    }

    function up_them(good_files) {
        start_actx();
        var evpath = get_evpath(),
            draw_each = good_files.length < 50;

        if (window.WebAssembly && !hws.length) {
            for (var a = 0; a < Math.min(navigator.hardwareConcurrency || 4, 16); a++)
                hws.push(new Worker('/.cpr/w.hash.js' + CB));

            console.log(hws.length + " hashers");
        }

        if (!uc.az)
            good_files.sort(function (a, b) {
                a = a[0].size;
                b = b[0].size;
                return a < b ? -1 : a > b ? 1 : 0;
            });

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

            if (biggest_file < entry.size)
                biggest_file = entry.size;

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
                '📐 ' + L.u_hashing,
                ''
            ], entry.size, draw_each);

            st.bytes.total += entry.size;
            st.files.push(entry);
            if (uc.turbo)
                push_t(st.todo.head, entry);
            else
                push_t(st.todo.hash, entry);
        }
        if (!draw_each) {
            pvis.drawcard("q");
            pvis.changecard(pvis.act);
        }
        ebi('u2tabw').className = 'ye';

        setTimeout(function () {
            if (!actx || actx.state != 'suspended' || toast.tag == L.u_unpt)
                return;

            toast.warn(30, "<div onclick=\"start_actx();toast.inf(3,'thanks!')\">please click this text to<br />unlock full upload speed</div>");
        }, 500);
    }

    function more_one_file() {
        fdom_ctr++;
        var elm = mknod('div');
        elm.innerHTML = (
            '<input id="file{0}" type="file" name="file{0}[]" multiple="multiple" tabindex="-1" />' +
            '<input id="dir{0}" type="file" name="dir{0}[]" multiple="multiple" tabindex="-1" webkitdirectory />'
        ).format(fdom_ctr);
        ebi('u2form').appendChild(elm);
        ebi('file' + fdom_ctr).onchange = gotfile;
        ebi('dir' + fdom_ctr).onchange = gotdir;
    }
    more_one_file();

    var etaref = 0, etaskip = 0, utw_minh = 0, utw_read = 0;
    function etafun() {
        var nhash = st.busy.head.length + st.busy.hash.length + st.todo.head.length + st.todo.hash.length,
            nsend = st.busy.upload.length + st.todo.upload.length,
            now = Date.now(),
            td = (now - (etaref || now)) / 1000.0;

        etaref = now;
        if (td > 1.2)
            td = 0.05;

        //ebi('acc_info').innerHTML = humantime(st.time.busy) + ' ' + f2f(now / 1000, 1);

        if (++utw_read >= 20) {
            utw_read = 0;
            utw_minh = parseInt(ebi('u2tabw').style.minHeight || '0');
        }

        var minh = QS('#op_up2k.act') && st.is_busy ? Math.max(utw_minh, ebi('u2tab').offsetHeight + 32) : 0;
        if (utw_minh < minh || !utw_minh) {
            utw_minh = minh;
            ebi('u2tabw').style.minHeight = utw_minh + 'px';
        }

        if (!nhash) {
            var h = L.u_etadone.format(humansize(st.bytes.hashed), pvis.ctr.ok + pvis.ctr.ng);
            if (st.eta.h !== h) {
                st.eta.h = ebi('u2etah').innerHTML = h;
                console.log('{0} hash, {1} up, {2} busy'.format(
                    f2f(st.time.hashing, 1),
                    f2f(st.time.uploading, 1),
                    f2f(st.time.busy, 1)));
            }
        }

        if (!nsend && !nhash) {
            var h = L.u_etadone.format(humansize(st.bytes.uploaded), pvis.ctr.ok + pvis.ctr.ng);

            if (st.eta.u !== h)
                st.eta.u = ebi('u2etau').innerHTML = h;

            if (st.eta.t !== h)
                st.eta.t = ebi('u2etat').innerHTML = h;
        }

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
                ebi('u2etat').innerHTML = L.u_etaprep;
            }
            else {
                st.time.busy += td;
                t.push(['u2etat', st.bytes.finished, st.bytes.finished, st.time.busy]);
            }
        }
        for (var a = 0; a < t.length; a++) {
            var rem = st.bytes.total - t[a][2],
                bps = t[a][1] / t[a][3],
                hid = t[a][0],
                eid = hid.slice(-1),
                eta = Math.floor(rem / bps);

            if (t[a][1] < 1024 || t[a][3] < 0.1) {
                ebi(hid).innerHTML = L.u_etaprep;
                continue;
            }

            donut.eta = eta;
            st.eta[eid] = '{0}, {1}/s, {2}'.format(
                humansize(rem), humansize(bps, 1), humantime(eta));

            if (!etaskip)
                ebi(hid).innerHTML = st.eta[eid];
        }
        if (++etaskip > 2)
            etaskip = 0;
    }

    function got_oserr() {
        if (!hws.length || !uc.hashw || st.oserr)
            return;

        st.oserr = true;
        var msg = HTTPS ? L.u_emtleak3 : L.u_emtleak2.format((window.location + '').replace(':', 's:'));
        modal.alert(L.u_emtleak1 + msg + L.u_emtleak4 + (CHROME ? L.u_emtleakc : FIREFOX ? L.u_emtleakf : ''));
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

        if (cd && cd > Date.now())
            return false;

        // keepalive or verify
        if (t.keepalive ||
            t.t_uploaded)
            return true;

        if (parallel_uploads <
            st.busy.handshake.length)
            return false;

        if (t.n - st.car > 8)
            // prevent runahead from a stuck upload (slow server hdd)
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
            if (!uc.az)
                return st.todo.handshake.length + st.busy.handshake.length < 2;

            var ahead = st.bytes.hashed - st.bytes.finished,
                nmax = ahead < biggest_file / 8 ? 32 : 16;

            return ahead < biggest_file &&
                st.todo.handshake.length + st.busy.handshake.length < nmax;
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
                    is_busy = st.car < st.files.length;

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
                        uptoast();
                        //throw console.hist.join('\n');
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
                    (!is_busy || st.todo.head[0].n - st.car < parallel_uploads * 2)) {
                    exec_head();
                    mou_ikkai = true;
                }

                if (handshakes_permitted() &&
                    st.todo.handshake.length) {
                    exec_handshake();
                    mou_ikkai = true;
                }

                if (st.todo.upload.length &&
                    st.busy.upload.length < parallel_uploads &&
                    can_upload_next()) {
                    exec_upload();
                    mou_ikkai = true;
                }

                if (hashing_permitted() &&
                    st.todo.hash.length &&
                    !st.busy.hash.length) {
                    exec_hash();
                    mou_ikkai = true;
                }

                if (is_busy && st.modn < 100) {
                    var t0 = Date.now() + (ebi('repl').offsetTop ? 0 : 0);

                    if (++st.modn >= 10) {
                        if (st.modn == 10)
                            st.mod0 = Date.now();

                        st.modv += Date.now() - t0;
                    }

                    if (st.modn >= 100) {
                        var n = st.modn - 10,
                            ipu = st.modv / n,
                            spu = (Date.now() - st.mod0) / n,
                            ir = spu / ipu;

                        console.log('tsk:', f2f(ipu, 2), ' spu:', f2f(spu, 2), ' ir:', f2f(ir, 2));
                        // efficiency estimates;
                        // ir: 8=16% 11=60% 16=90% 24=100%
                        // ipu: 1=40% .8=60% .3=100%
                        if (ipu >= 0.5 && ir <= 15)
                            pvis.go_potato();
                    }
                }

                if (!mou_ikkai || crashed)
                    return defer();
            }
        }
        timer.add(taskerd, true);
        return taskerd;
    })();

    function uptoast() {
        var sr = uc.fsearch,
            ok = pvis.ctr.ok,
            ng = pvis.ctr.ng,
            t = uc.ask_up ? 0 : 10;

        console.log('toast', ok, ng);

        if (ok && ng)
            toast.warn(t, uc.nagtxt = (sr ? L.ur_sm : L.ur_um).format(ok, ng));
        else if (ok > 1)
            toast.ok(t, uc.nagtxt = (sr ? L.ur_aso : L.ur_auo).format(ok));
        else if (ok)
            toast.ok(t, uc.nagtxt = sr ? L.ur_1so : L.ur_1uo);
        else if (ng > 1)
            toast.err(t, uc.nagtxt = (sr ? L.ur_asn : L.ur_aun).format(ng));
        else if (ng)
            toast.err(t, uc.nagtxt = sr ? L.ur_1sn : L.ur_1un);

        timer.rm(etafun);
        timer.rm(donut.do);
        utw_minh = 0;
    }

    function chill(t) {
        var now = Date.now();
        if ((t.coolmul || 0) < 2 || now - t.cooldown < t.coolmul * 700)
            t.coolmul = Math.min((t.coolmul || 0.5) * 2, 32);

        t.cooldown = Math.max(t.cooldown || 1, Date.now() + t.coolmul * 1000);
    }

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
        if (!t.size)
            return st.todo.handshake.push(t);

        st.busy.hash.push(t);
        st.nfile.hash = t.n;
        t.t_hashing = Date.now();

        var bpend = 0,
            nchunk = 0,
            chunksize = get_chunksize(t.size),
            nchunks = Math.ceil(t.size / chunksize),
            hashtab = {};

        pvis.setab(t.n, nchunks);
        pvis.move(t.n, 'bz');

        if (hws.length && uc.hashw && (nchunks > 1 || document.visibilityState == 'hidden'))
            // resolving subtle.digest w/o worker takes 1sec on blur if the actx hack breaks
            return wexec_hash(t, chunksize, nchunks);

        var segm_next = function () {
            if (nchunk >= nchunks || bpend)
                return false;

            var reader = new FileReader(),
                nch = nchunk++,
                car = nch * chunksize,
                cdr = Math.min(chunksize + car, t.size);

            st.bytes.hashed += cdr - car;

            function orz(e) {
                bpend--;
                segm_next();
                hash_calc(nch, e.target.result);
            }
            reader.onload = function (e) {
                try { orz(e); } catch (ex) { vis_exh(ex + '', 'up2k.js', '', '', ex); }
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
                    got_oserr();
                }

                if (handled) {
                    pvis.move(t.n, 'ng');
                    apop(st.busy.hash, t);
                    st.bytes.finished += t.size;
                    return;
                }

                toast.err(0, 'y o u   b r o k e    i t\nfile: ' + esc(t.name + '') + '\nerror: ' + err);
            };
            bpend++;
            reader.readAsArrayBuffer(t.fobj.slice(car, cdr));

            return true;
        };

        var hash_calc = function (nch, buf) {
            var orz = function (hashbuf) {
                var hslice = new Uint8Array(hashbuf).subarray(0, 33),
                    b64str = buf2b64(hslice);

                hashtab[nch] = b64str;
                t.hash.push(nch);
                pvis.hashed(t);
                if (t.hash.length < nchunks)
                    return segm_next();

                t.hash = [];
                for (var a = 0; a < nchunks; a++)
                    t.hash.push(hashtab[a]);

                t.t_hashed = Date.now();

                pvis.seth(t.n, 2, L.u_hashdone);
                pvis.seth(t.n, 1, '📦 wait');
                apop(st.busy.hash, t);
                st.todo.handshake.push(t);
                tasker();
            };

            var hash_done = function (hashbuf) {
                try { orz(hashbuf); } catch (ex) { vis_exh(ex + '', 'up2k.js', '', '', ex); }
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
        segm_next();
    }

    function wexec_hash(t, chunksize, nchunks) {
        var nchunk = 0,
            reading = 0,
            max_readers = 1,
            opt_readers = 2,
            free = [],
            busy = {},
            nbusy = 0,
            hashtab = {},
            mem = (MOBILE ? 128 : 256) * 1024 * 1024;

        for (var a = 0; a < hws.length; a++) {
            var w = hws[a];
            free.push(w);
            w.onmessage = onmsg;
            mem -= chunksize;
            if (mem <= 0)
                break;
        }

        function go_next() {
            if (st.slow_io && uc.multitask)
                // android-chrome filereader latency is ridiculous but scales linearly
                // (unlike every other platform which instead suffers on parallel reads...)
                max_readers = opt_readers = free.length;

            if (reading >= max_readers || !free.length || nchunk >= nchunks)
                return;

            var w = free.pop(),
                car = nchunk * chunksize,
                cdr = Math.min(chunksize + car, t.size);

            //console.log('[P ] %d read bgin (%d reading, %d busy)', nchunk, reading + 1, nbusy + 1);
            w.postMessage([nchunk, t.fobj, car, cdr]);
            busy[nchunk] = w;
            nbusy++;
            reading++;
            nchunk++;
        }

        function onmsg(d) {
            d = d.data;
            var k = d[0];

            if (k == "panic")
                return vis_exh(d[1], 'up2k.js', '', '', d[1]);

            if (k == "fail") {
                pvis.seth(t.n, 1, d[1]);
                pvis.seth(t.n, 2, d[2]);
                console.log(d[1], d[2]);
                if (d[1] == 'OS-error')
                    got_oserr();

                pvis.move(t.n, 'ng');
                apop(st.busy.hash, t);
                st.bytes.finished += t.size;
                return;
            }

            if (k == "ferr")
                return toast.err(0, 'y o u   b r o k e    i t\nfile: ' + esc(t.name + '') + '\nerror: ' + d[1]);

            if (k == "read") {
                reading--;
                if (MOBILE && CHROME && st.slow_io === null && d[1] == 1 && d[2] > 1024 * 512) {
                    var spd = Math.floor(d[2] / d[3]);
                    st.slow_io = spd < 40 * 1024;
                    console.log('spd {0}, slow: {1}'.format(spd, st.slow_io));
                }
                //console.log('[P ] %d read DONE (%d reading, %d busy)', d[1], reading, nbusy);
                return go_next();
            }

            if (k == "done") {
                var nchunk = d[1],
                    hslice = d[2],
                    sz = d[3];

                free.push(busy[nchunk]);
                delete busy[nchunk];
                nbusy--;

                //console.log('[P ] %d HASH DONE (%d reading, %d busy)', nchunk, reading, nbusy);

                hashtab[nchunk] = buf2b64(hslice);
                st.bytes.hashed += sz;
                t.hash.push(nchunk);
                pvis.hashed(t);

                if (t.hash.length < nchunks)
                    return nbusy < opt_readers && go_next();

                t.hash = [];
                for (var a = 0; a < nchunks; a++)
                    t.hash.push(hashtab[a]);

                t.t_hashed = Date.now();

                pvis.seth(t.n, 2, L.u_hashdone);
                pvis.seth(t.n, 1, '📦 wait');
                apop(st.busy.hash, t);
                st.todo.handshake.push(t);
                tasker();
            }
        }
        go_next();
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
            console.log('head onerror, retrying', t.name, t);
            if (!toast.visible)
                toast.warn(9.98, L.u_enethd + "\n\nfile: " + t.name, t);

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
            try { orz(e); } catch (ex) { vis_exh(ex + '', 'up2k.js', '', '', ex); }
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
            console.log("sending keepalive handshake", t.name, t);

        var xhr = new XMLHttpRequest();
        xhr.onerror = function () {
            if (t.t_busied != me) {
                console.log('zombie handshake onerror,', t.name, t);
                return;
            }
            if (!toast.visible)
                toast.warn(9.98, L.u_eneths + "\n\nfile: " + t.name, t);

            console.log('handshake onerror, retrying', t.name, t);
            apop(st.busy.handshake, t);
            st.todo.handshake.unshift(t);
            t.keepalive = keepalive;
        };
        function orz(e) {
            if (t.t_busied != me) {
                console.log('zombie handshake onload,', t.name, t);
                return;
            }
            if (xhr.status == 200) {
                t.t_handshake = Date.now();
                if (keepalive) {
                    apop(st.busy.handshake, t);
                    return;
                }

                if (toast.tag === t)
                    toast.ok(5, L.u_fixed);

                var response = JSON.parse(xhr.responseText);
                if (!response.name) {
                    var msg = '',
                        smsg = '';

                    if (!response || !response.hits || !response.hits.length) {
                        smsg = '404';
                        msg = (L.u_s404 + ' <a href="#" onclick="fsearch_explain(' +
                            (has(perms, 'write') ? '0' : '1') + ')" class="fsearch_explain">(' + L.u_expl + ')</a>');
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

                t.sprs = response.sprs;

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

                    msg = null;
                    done = false;

                    if (sort)
                        arr.sort(function (a, b) {
                            return a.nfile < b.nfile ? -1 :
                            /*  */ a.nfile > b.nfile ? 1 :
                                    a.npart < b.npart ? -1 : 1;
                        });
                }

                if (msg)
                    pvis.seth(t.n, 1, msg);

                apop(st.busy.handshake, t);

                if (done) {
                    t.done = true;
                    t.fobj = null;
                    st.bytes.finished += t.size - t.bytes_uploaded;
                    var spd1 = (t.size / ((t.t_hashed - t.t_hashing) / 1000.)) / (1024 * 1024.),
                        spd2 = (t.size / ((t.t_uploaded - t.t_uploading) / 1000.)) / (1024 * 1024.);

                    pvis.seth(t.n, 2, 'hash {0}, up {1} MB/s'.format(
                        f2f(spd1, 2), !isNum(spd2) ? '--' : f2f(spd2, 2)));

                    pvis.move(t.n, 'ok');
                    if (!pvis.ctr.bz && !pvis.ctr.q)
                        uptoast();
                }
                else {
                    if (t.t_uploaded)
                        chill(t);

                    t.t_uploaded = undefined;
                }
                tasker();
            }
            else {
                pvis.seth(t.n, 1, "ERROR");
                pvis.seth(t.n, 2, L.u_ehstmp, t);

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
                if (rsp.indexOf('server HDD is full') + 1)
                    return toast.err(0, L.u_ehsdf + "\n\n" + rsp.replace(/.*; /, ''));

                if (err != "") {
                    if (!t.t_uploading)
                        st.bytes.finished += t.size;

                    pvis.seth(t.n, 1, "ERROR");
                    pvis.seth(t.n, 2, err);
                    pvis.move(t.n, 'ng');

                    apop(st.busy.handshake, t);
                    tasker();
                    return;
                }
                err = t.t_uploading ? L.u_ehsfin : t.srch ? L.u_ehssrch : L.u_ehsinit;
                xhrchk(xhr, err + "\n\nfile: " + t.name + "\n\nerror ", "404, target folder not found", "warn", t);
            }
        }
        xhr.onload = function (e) {
            try { orz(e); } catch (ex) { vis_exh(ex + '', 'up2k.js', '', '', ex); }
        };

        var req = {
            "name": t.name,
            "size": t.size,
            "lmod": t.lmod,
            "life": st.lifetime,
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

    function can_upload_next() {
        var upt = st.todo.upload[0],
            upf = st.files[upt.nfile],
            now = Date.now();

        for (var a = 0, aa = st.busy.handshake.length; a < aa; a++) {
            var hs = st.busy.handshake[a];
            if (hs.n < upt.nfile && hs.t_busied > now - 10 * 1000 && !st.files[hs.n].bytes_uploaded)
                return false;  // handshake race; wait for lexically first
        }

        if (upf.sprs)
            return true;

        for (var a = 0, aa = st.busy.upload.length; a < aa; a++)
            if (st.busy.upload[a].nfile == upt.nfile)
                return false;

        return true;
    }

    function exec_upload() {
        var upt = st.todo.upload.shift();
        st.busy.upload.push(upt);
        st.nfile.upload = upt.nfile;

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
                console.log("ignoring dupe-segment error", t.name, t);
            }
            else {
                xhrchk(xhr, L.u_cuerr2.format(npart, Math.ceil(t.size / chunksize), t.name), "404, target folder not found (???)", "warn", t);

                chill(t);
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
            var xhr = new XMLHttpRequest(),
                bfin = Math.floor(st.bytes.finished / 1024 / 1024),
                btot = Math.floor(st.bytes.total / 1024 / 1024);

            xhr.upload.onprogress = function (xev) {
                pvis.prog(t, npart, xev.loaded);
            };
            xhr.onload = function (xev) {
                try { orz(xhr); } catch (ex) { vis_exh(ex + '', 'up2k.js', '', '', ex); }
            };
            xhr.onerror = function (xev) {
                if (crashed)
                    return;

                if (!toast.visible)
                    toast.warn(9.98, L.u_cuerr.format(npart, Math.ceil(t.size / chunksize), t.name), t);

                console.log('chunkpit onerror,', ++tries, t.name, t);
                orz2(xhr);
            };
            xhr.open('POST', t.purl, true);
            xhr.setRequestHeader("X-Up2k-Hash", t.hash[npart]);
            xhr.setRequestHeader("X-Up2k-Wark", t.wark);
            xhr.setRequestHeader("X-Up2k-Stat", "{0}/{1}/{2}/{3} {4}/{5} {6}".format(
                pvis.ctr.ok, pvis.ctr.ng, pvis.ctr.bz, pvis.ctr.q, btot, btot - bfin,
                st.eta.t.split(' ').pop()));
            xhr.setRequestHeader('Content-Type', 'application/octet-stream');
            if (xhr.overrideMimeType)
                xhr.overrideMimeType('Content-Type', 'application/octet-stream');

            xhr.responseType = 'text';
            xhr.send(t.fobj.slice(car, cdr));
        }
        do_send();
    }

    /////
    ////
    ///   config ui
    //

    function onresize(e) {
        // 10x faster than matchMedia('(min-width
        var bar = ebi('ops'),
            wpx = window.innerWidth,
            fpx = parseInt(getComputedStyle(bar)['font-size']),
            wem = wpx * 1.0 / fpx,
            wide = wem > 54 ? 'w' : '',
            parent = ebi(wide ? 'u2btn_cw' : 'u2btn_ct'),
            btn = ebi('u2btn');

        if (btn.parentNode !== parent) {
            parent.appendChild(btn);
            ebi('u2conf').className = ebi('u2cards').className = ebi('u2etaw').className = wide;
        }

        wide = wem > 82 ? 'ww' : wide;
        parent = ebi(wide == 'ww' ? 'u2c3w' : 'u2c3t');
        var its = [ebi('u2etaw'), ebi('u2cards')];
        if (its[0].parentNode !== parent) {
            ebi('u2conf').className = wide;
            for (var a = 0; a < 2; a++) {
                parent.appendChild(its[a]);
                its[a].className = wide;
            }
        }
    }
    window.addEventListener('resize', onresize);
    onresize();

    if (MOBILE) {
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
        if (anymod(e))
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
        var msg = (turbolvl || !uc.turbo) ? null : uc.fsearch ? L.u_ts : L.u_tu,
            html = ebi('u2foot').innerHTML;

        if (msg && html.indexOf(msg) + 1)
            return;

        qsr('#u2turbomsg');
        if (!msg)
            return;

        var o = mknod('div', 'u2turbomsg');
        o.innerHTML = msg;
        ebi('u2foot').appendChild(o);
    }
    draw_turbo();

    function draw_life() {
        var el = ebi('u2life');
        if (!lifetime) {
            el.style.display = 'none';
            el.innerHTML = '';
            st.lifetime = 0;
            return;
        }
        el.style.display = uc.fsearch ? 'none' : '';
        el.innerHTML = '<div>' + L.u_life_cfg + '</div><div>' + L.u_life_est + '</div><div id="undor"></div>';
        set_life(Math.min(lifetime, icfg_get('lifetime', lifetime)));
        ebi('lifem').oninput = ebi('lifeh').oninput = mod_life;
        ebi('lifem').onkeydown = ebi('lifeh').onkeydown = kd_life;
        tt.att(ebi('u2life'));
    }
    draw_life();

    function mod_life(e) {
        var el = e.target,
            pow = parseInt(el.getAttribute('p')),
            v = parseInt(el.value);

        if (!isNum(v))
            return;

        if (toast.tag == mod_life)
            toast.hide();

        v *= pow;
        if (v > lifetime) {
            v = lifetime;
            toast.warn(20, L.u_life_max.format(lhumantime(lifetime)), mod_life);
        }

        swrite('lifetime', v);
        set_life(v);
    }

    function kd_life(e) {
        var el = e.target,
            d = e.code == 'ArrowUp' ? 1 : e.code == 'ArrowDown' ? -1 : 0;

        if (anymod(e) || !d)
            return;

        el.value = parseInt(el.value) + d;
        mod_life(e);
    }

    function set_life(v) {
        //ebi('lifes').value = v;
        ebi('lifem').value = parseInt(v / 60);
        ebi('lifeh').value = parseInt(v / 3600);

        var undo = have_unpost - (v ? lifetime - v : 0);
        ebi('undor').innerHTML = undo <= 0 ?
            L.u_unp_ng : L.u_unp_ok.format(lhumantime(undo));

        st.lifetime = v;
        rel_life();
    }

    function rel_life() {
        if (!lifetime)
            return;

        try {
            ebi('lifew').innerHTML = unix2iso((st.lifetime || lifetime) +
                Date.now() / 1000 - new Date().getTimezoneOffset() * 60
            ).replace(' ', ', ').slice(0, -3);
        }
        catch (ex) { }
    }
    setInterval(rel_life, 9000);

    function set_potato() {
        pvis.potato();
        set_fsearch();
    }

    function set_fsearch(new_state) {
        var fixed = false,
            can_write = false;

        if (!ebi('fsearch')) {
            new_state = false;
        }
        else if (perms.length) {
            if (!(can_write = has(perms, 'write'))) {
                new_state = true;
                fixed = true;
            }
            if (!has(perms, 'read') || !have_up2k_idx) {
                new_state = false;
                fixed = true;
            }
        }

        if (new_state !== undefined)
            bcfg_set('fsearch', uc.fsearch = new_state);

        try {
            clmod(ebi('u2c3w'), 's', !can_write);
            QS('label[for="fsearch"]').style.display = QS('#fsearch').style.display = fixed ? 'none' : '';
        }
        catch (ex) { }

        try {
            var ico = uc.fsearch ? '🔎' : '🚀',
                desc = uc.fsearch ? L.ul_btns : L.ul_btnu;

            clmod(ebi('op_up2k'), 'srch', uc.fsearch);
            ebi('u2bm').innerHTML = ico + '&nbsp; <sup>' + desc + '</sup>';
        }
        catch (ex) { }

        ebi('u2tab').className = (uc.fsearch ? 'srch ' : 'up ') + pvis.act;

        var potato = uc.potato && !uc.fsearch;
        ebi('u2cards').style.display = ebi('u2tab').style.display = potato ? 'none' : '';
        ebi('u2mu').style.display = potato ? '' : 'none';

        draw_turbo();
        draw_life();
        onresize();
    }

    function apply_flag_cfg() {
        if (uc.flag_en && !flag) {
            try {
                flag = up2k_flagbus();
            }
            catch (ex) {
                toast.err(5, "not supported on your browser:\n" + esc(basenames(ex)));
                bcfg_set('flag_en', uc.flag_en = false);
            }
        }
        else if (!uc.flag_en && flag) {
            if (flag.ours)
                flag.give();

            flag.ch.close();
            flag = false;
        }
    }

    function set_u2sort() {
        if (u2sort.indexOf('f') < 0)
            return;

        bcfg_set('u2sort', uc.az = u2sort.indexOf('n') + 1);
        localStorage.removeItem('u2sort');
    }

    function set_hashw() {
        if (!window.WebAssembly) {
            bcfg_set('hashw', uc.hashw = false);
            toast.err(10, L.u_nowork);
        }
    }

    function set_upnag(en) {
        function nopenag() {
            bcfg_set('upnag', uc.upnag = false);
            toast.err(10, "https only");
        }

        function chknag() {
            if (Notification.permission != 'granted')
                nopenag();
        }

        if (!window.Notification || !HTTPS)
            return nopenag();

        if (en && Notification.permission == 'default')
            Notification.requestPermission().then(chknag, chknag);
    }

    if (uc.upnag && (!window.Notification || Notification.permission != 'granted'))
        bcfg_set('upnag', uc.upnag = false);

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

    setTimeout(function () {
        for (var a = 0; a < up2k_hooks.length; a++)
            up2k_hooks[a]();
    }, 1);

    return r;
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
    swrite('icof', a ? 'fc5' : '000');
    swrite('icob', a ? '222' : '');
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
