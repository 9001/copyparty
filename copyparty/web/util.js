"use strict";

if (!window['console'])
    window['console'] = {
        "log": function (msg) { }
    };


var is_touch = 'ontouchstart' in window,
    ANDROID = /(android)/i.test(navigator.userAgent);


// error handler for mobile devices
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
function vis_exh(msg, url, lineNo, columnNo, error) {
    if (!window.onerror)
        return;

    window.onerror = undefined;
    window['vis_exh'] = null;
    var html = ['<h1>you hit a bug!</h1><p>please send me a screenshot arigathanks gozaimuch: <code>ed/irc.rizon.net</code> or <code>ed#2644</code><br />&nbsp; (and if you can, press F12 and include the "Console" tab in the screenshot too)</p><p>',
        esc(String(msg)), '</p><p>', esc(url + ' @' + lineNo + ':' + columnNo), '</p>'];

    if (error) {
        var find = ['desc', 'stack', 'trace'];
        for (var a = 0; a < find.length; a++)
            if (String(error[find[a]]) !== 'undefined')
                html.push('<h2>' + find[a] + '</h2>' +
                    esc(String(error[find[a]])).replace(/\n/g, '<br />\n'));
    }
    html.push('<p style="border-top:1px solid #999;margin-top:1.5em;font-size:1.4em">if you are stuck here, try to <a href="#" onclick="localStorage.clear();location.reload();">reset copyparty settings</a></p>');
    document.body.innerHTML = html.join('\n');

    var s = mknod('style');
    s.innerHTML = 'body{background:#333;color:#ddd;font-family:sans-serif;font-size:0.8em;padding:0 1em 1em 1em} code{color:#bf7;background:#222;padding:.1em;margin:.2em;font-size:1.1em;font-family:monospace,monospace} *{line-height:1.5em}';
    document.head.appendChild(s);

    throw 'fatal_err';
}


var ebi = document.getElementById.bind(document),
    QS = document.querySelector.bind(document),
    QSA = document.querySelectorAll.bind(document),
    mknod = document.createElement.bind(document);


function ev(e) {
    e = e || window.event;
    if (!e)
        return;

    if (e.preventDefault)
        e.preventDefault()

    if (e.stopPropagation)
        e.stopPropagation();

    if (e.stopImmediatePropagation)
        e.stopImmediatePropagation();

    e.returnValue = false;
    return e;
}


// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/endsWith
if (!String.prototype.endsWith) {
    String.prototype.endsWith = function (search, this_len) {
        if (this_len === undefined || this_len > this.length) {
            this_len = this.length;
        }
        return this.substring(this_len - search.length, this_len) === search;
    };
}
if (!String.startsWith) {
    String.prototype.startsWith = function (s, i) {
        i = i > 0 ? i | 0 : 0;
        return this.substring(i, i + s.length) === s;
    };
}


// https://stackoverflow.com/a/950146
function import_js(url, cb) {
    var head = document.head || document.getElementsByTagName('head')[0];
    var script = mknod('script');
    script.type = 'text/javascript';
    script.src = url;

    script.onreadystatechange = cb;
    script.onload = cb;

    head.appendChild(script);
}


var crctab = (function () {
    var c, tab = [];
    for (var n = 0; n < 256; n++) {
        c = n;
        for (var k = 0; k < 8; k++) {
            c = ((c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1));
        }
        tab[n] = c;
    }
    return tab;
})();


function crc32(str) {
    var crc = 0 ^ (-1);
    for (var i = 0; i < str.length; i++) {
        crc = (crc >>> 8) ^ crctab[(crc ^ str.charCodeAt(i)) & 0xFF];
    }
    return ((crc ^ (-1)) >>> 0).toString(16);
}


function clmod(obj, cls, add) {
    var re = new RegExp('\\s*\\b' + cls + '\\s*\\b', 'g');
    if (add == 't')
        add = !re.test(obj.className);

    obj.className = obj.className.replace(re, ' ') + (add ? ' ' + cls : '');
}


function sortfiles(nodes) {
    var sopts = jread('fsort', [["href", 1, ""]]);

    try {
        var is_srch = false;
        if (nodes[0]['rp']) {
            is_srch = true;
            for (var b = 0, bb = nodes.length; b < bb; b++)
                nodes[b].ext = nodes[b].rp.split('.').pop();
            for (var b = 0; b < sopts.length; b++)
                if (sopts[b][0] == 'href')
                    sopts[b][0] = 'rp';
        }
        for (var a = sopts.length - 1; a >= 0; a--) {
            var name = sopts[a][0], rev = sopts[a][1], typ = sopts[a][2];
            if (!name)
                continue;

            if (name == 'ts')
                typ = 'int';

            if (name.indexOf('tags/') === 0) {
                name = name.slice(5);
                for (var b = 0, bb = nodes.length; b < bb; b++)
                    nodes[b]._sv = nodes[b].tags[name];
            }
            else {
                for (var b = 0, bb = nodes.length; b < bb; b++) {
                    var v = nodes[b][name];

                    if ((v + '').indexOf('<a ') === 0)
                        v = v.split('>')[1];
                    else if (name == "href" && v) {
                        if (v.slice(-1) == '/')
                            v = '\t' + v;

                        v = uricom_dec(v)[0]
                    }

                    nodes[b]._sv = v;
                }
            }

            var onodes = nodes.map(function (x) { return x; });
            nodes.sort(function (n1, n2) {
                var v1 = n1._sv,
                    v2 = n2._sv;

                if (v1 === undefined) {
                    if (v2 === undefined) {
                        return onodes.indexOf(n1) - onodes.indexOf(n2);
                    }
                    return -1 * rev;
                }
                if (v2 === undefined) return 1 * rev;

                var ret = rev * (typ == 'int' ? (v1 - v2) : (v1.localeCompare(v2)));
                if (ret === 0)
                    ret = onodes.indexOf(n1) - onodes.indexOf(n2);

                return ret;
            });
        }
        for (var b = 0, bb = nodes.length; b < bb; b++) {
            delete nodes[b]._sv;
            if (is_srch)
                delete nodes[b].ext;
        }
    }
    catch (ex) {
        console.log("failed to apply sort config: " + ex);
        console.log("resetting fsort " + sread('fsort'))
        localStorage.removeItem('fsort');
    }
    return nodes;
}


function sortTable(table, col, cb) {
    var tb = table.tBodies[0],
        th = table.tHead.rows[0].cells,
        tr = Array.prototype.slice.call(tb.rows, 0),
        i, reverse = th[col].className.indexOf('sort1') !== -1 ? -1 : 1;
    for (var a = 0, thl = th.length; a < thl; a++)
        th[a].className = th[a].className.replace(/ *sort-?1 */, " ");
    th[col].className += ' sort' + reverse;
    var stype = th[col].getAttribute('sort');
    try {
        var nrules = [], rules = jread("fsort", []);
        rules.unshift([th[col].getAttribute('name'), reverse, stype || '']);
        for (var a = 0; a < rules.length; a++) {
            var add = true;
            for (var b = 0; b < a; b++)
                if (rules[a][0] == rules[b][0])
                    add = false;

            if (add)
                nrules.push(rules[a]);

            if (nrules.length >= 10)
                break;
        }
        jwrite("fsort", nrules);
    }
    catch (ex) {
        console.log("failed to persist sort rules, resetting: " + ex);
        jwrite("fsort", null);
    }
    var vl = [];
    for (var a = 0; a < tr.length; a++) {
        var cell = tr[a].cells[col];
        if (!cell) {
            vl.push([null, a]);
            continue;
        }
        var v = cell.getAttribute('sortv') || cell.textContent.trim();
        if (stype == 'int') {
            v = parseInt(v.replace(/[, ]/g, '')) || 0;
        }
        vl.push([v, a]);
    }
    vl.sort(function (a, b) {
        a = a[0];
        b = b[0];
        if (a === null)
            return -1;
        if (b === null)
            return 1;

        if (stype == 'int') {
            return reverse * (a - b);
        }
        return reverse * (a.localeCompare(b));
    });
    for (i = 0; i < tr.length; ++i) tb.appendChild(tr[vl[i][1]]);
    if (cb) cb();
}
function makeSortable(table, cb) {
    var th = table.tHead, i;
    th && (th = th.rows[0]) && (th = th.cells);
    if (th) i = th.length;
    else return; // if no `<thead>` then do nothing
    while (--i >= 0) (function (i) {
        th[i].onclick = function (e) {
            ev(e);
            sortTable(table, i, cb);
        };
    }(i));
}


function linksplit(rp) {
    var ret = [];
    var apath = '/';
    if (rp && rp.charAt(0) == '/')
        rp = rp.slice(1);

    while (rp) {
        var link = rp;
        var ofs = rp.indexOf('/');
        if (ofs === -1) {
            rp = null;
        }
        else {
            link = rp.slice(0, ofs + 1);
            rp = rp.slice(ofs + 1);
        }
        var vlink = esc(link),
            elink = uricom_enc(link);

        if (link.indexOf('/') !== -1) {
            vlink = vlink.slice(0, -1) + '<span>/</span>';
            elink = elink.slice(0, -3) + '/';
        }

        ret.push('<a href="' + apath + elink + '">' + vlink + '</a>');
        apath += elink;
    }
    return ret;
}


function uricom_enc(txt, do_fb_enc) {
    try {
        return encodeURIComponent(txt);
    }
    catch (ex) {
        console.log("uce-err [" + txt + "]");
        if (do_fb_enc)
            return esc(txt);

        return txt;
    }
}


function uricom_dec(txt) {
    try {
        return [decodeURIComponent(txt), true];
    }
    catch (ex) {
        console.log("ucd-err [" + txt + "]");
        return [txt, false];
    }
}


function get_evpath() {
    var ret = document.location.pathname;

    if (ret.indexOf('/') !== 0)
        ret = '/' + ret;

    if (ret.lastIndexOf('/') !== ret.length - 1)
        ret += '/';

    return ret;
}


function get_vpath() {
    return uricom_dec(get_evpath())[0];
}


function get_pwd() {
    var pwd = ('; ' + document.cookie).split('; cppwd=');
    if (pwd.length < 2)
        return null;

    return pwd[1].split(';')[0];
}


function unix2iso(ts) {
    return new Date(ts * 1000).toISOString().replace("T", " ").slice(0, -5);
}


function s2ms(s) {
    s = Math.floor(s);
    var m = Math.floor(s / 60);
    return m + ":" + ("0" + (s - m * 60)).slice(-2);
}


function has(haystack, needle) {
    for (var a = 0; a < haystack.length; a++)
        if (haystack[a] == needle)
            return true;

    return false;
}


function apop(arr, v) {
    var ofs = arr.indexOf(v);
    if (ofs !== -1)
        arr.splice(ofs, 1);
}


function jcp(obj) {
    return JSON.parse(JSON.stringify(obj));
}


function sread(key) {
    if (window.localStorage)
        return localStorage.getItem(key);

    return null;
}

function swrite(key, val) {
    if (window.localStorage) {
        if (val === undefined || val === null)
            localStorage.removeItem(key);
        else
            localStorage.setItem(key, val);
    }
}

function jread(key, fb) {
    var str = sread(key);
    if (!str)
        return fb;

    return JSON.parse(str);
}

function jwrite(key, val) {
    if (!val)
        swrite(key);
    else
        swrite(key, JSON.stringify(val));
}

function icfg_get(name, defval) {
    return parseInt(fcfg_get(name, defval));
}

function fcfg_get(name, defval) {
    var o = ebi(name);

    var val = parseFloat(sread(name));
    if (isNaN(val))
        return parseFloat(o ? o.value : defval);

    if (o)
        o.value = val;

    return val;
}

function bcfg_get(name, defval) {
    var o = ebi(name);
    if (!o)
        return defval;

    var val = sread(name);
    if (val === null)
        val = defval;
    else
        val = (val == '1');

    bcfg_upd_ui(name, val);
    return val;
}

function bcfg_set(name, val) {
    swrite(name, val ? '1' : '0');
    bcfg_upd_ui(name, val);
    return val;
}

function bcfg_upd_ui(name, val) {
    var o = ebi(name);
    if (!o)
        return;

    if (o.getAttribute('type') == 'checkbox')
        o.checked = val;
    else if (o) {
        clmod(o, 'on', val);
    }
}


function hist_push(url) {
    console.log("h-push " + url);
    history.pushState(url, url, url);
}

function hist_replace(url) {
    console.log("h-repl " + url);
    history.replaceState(url, url, url);
}


var tt = (function () {
    var r = {
        "tt": mknod("div"),
        "en": true
    };

    r.tt.setAttribute('id', 'tt');
    document.body.appendChild(r.tt);

    function show() {
        var cfg = sread('tooltips');
        if (cfg !== null && cfg != '1')
            return;

        var msg = this.getAttribute('tt');
        if (!msg)
            return;

        var pos = this.getBoundingClientRect(),
            left = pos.left < window.innerWidth / 2,
            top = pos.top < window.innerHeight / 2,
            big = this.className.indexOf(' ttb') !== -1;

        clmod(r.tt, 'b', big);
        r.tt.style.top = top ? pos.bottom + 'px' : 'auto';
        r.tt.style.bottom = top ? 'auto' : (window.innerHeight - pos.top) + 'px';
        r.tt.style.left = left ? pos.left + 'px' : 'auto';
        r.tt.style.right = left ? 'auto' : (window.innerWidth - pos.right) + 'px';

        r.tt.innerHTML = msg.replace(/\$N/g, "<br />");
        clmod(r.tt, 'show', 1);
    }

    function hide() {
        clmod(r.tt, 'show');
    }

    r.init = function () {
        var ttb = ebi('tooltips');
        if (ttb) {
            ttb.onclick = function (e) {
                ev(e);
                r.en = !r.en;
                bcfg_set('tooltips', r.en);
                r.init();
            };
            r.en = bcfg_get('tooltips', true)
        }

        var _show = r.en ? show : null,
            _hide = r.en ? hide : null;

        var o = QSA('*[tt]');
        for (var a = o.length - 1; a >= 0; a--) {
            o[a].onfocus = _show;
            o[a].onblur = _hide;
            o[a].onmouseenter = _show;
            o[a].onmouseleave = _hide;
        }
        hide();
    };

    return r;
})();
