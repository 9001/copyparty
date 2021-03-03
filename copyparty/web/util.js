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
function vis_exh(msg, url, lineNo, columnNo, error) {
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
    document.body.style.padding = '0 1em 1em 1em';
    hcroak(html.join('\n'));
}


function ebi(id) {
    return document.getElementById(id);
}

function ev(e) {
    e = e || window.event;
    if (!e)
        return;

    if (e.preventDefault)
        e.preventDefault()

    if (e.stopPropagation)
        e.stopPropagation();

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
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = url;

    script.onreadystatechange = cb;
    script.onload = cb;

    head.appendChild(script);
}


function sortTable(table, col) {
    var tb = table.tBodies[0],
        th = table.tHead.rows[0].cells,
        tr = Array.prototype.slice.call(tb.rows, 0),
        i, reverse = th[col].className.indexOf('sort1') !== -1 ? -1 : 1;
    for (var a = 0, thl = th.length; a < thl; a++)
        th[a].className = th[a].className.replace(/ *sort-?1 */, " ");
    th[col].className += ' sort' + reverse;
    var stype = th[col].getAttribute('sort');
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
}
function makeSortable(table) {
    var th = table.tHead, i;
    th && (th = th.rows[0]) && (th = th.cells);
    if (th) i = th.length;
    else return; // if no `<thead>` then do nothing
    while (--i >= 0) (function (i) {
        th[i].onclick = function (e) {
            ev(e);
            sortTable(table, i);
        };
    }(i));
}



(function () {
    var ops = document.querySelectorAll('#ops>a');
    for (var a = 0; a < ops.length; a++) {
        ops[a].onclick = opclick;
    }
})();


function opclick(e) {
    ev(e);

    var dest = this.getAttribute('data-dest');
    goto(dest);

    swrite('opmode', dest || undefined);

    var input = document.querySelector('.opview.act input:not([type="hidden"])')
    if (input)
        input.focus();
}


function goto(dest) {
    var obj = document.querySelectorAll('.opview.act');
    for (var a = obj.length - 1; a >= 0; a--)
        obj[a].classList.remove('act');

    obj = document.querySelectorAll('#ops>a');
    for (var a = obj.length - 1; a >= 0; a--)
        obj[a].classList.remove('act');

    var others = ['path', 'files', 'widget'];
    for (var a = 0; a < others.length; a++)
        ebi(others[a]).classList.remove('hidden');

    if (dest) {
        var ui = ebi('op_' + dest);
        ui.classList.add('act');
        document.querySelector('#ops>a[data-dest=' + dest + ']').classList.add('act');

        var fn = window['goto_' + dest];
        if (fn)
            fn();
    }
}


(function () {
    goto();
    var op = sread('opmode');
    if (op !== null && op !== '.')
        goto(op);
})();


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
        var vlink = link;
        if (link.indexOf('/') !== -1)
            vlink = link.slice(0, -1) + '<span>/</span>';

        ret.push('<a href="' + apath + link + '">' + vlink + '</a>');
        apath += link;
    }
    return ret;
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
    return decodeURIComponent(get_evpath());
}


function unix2iso(ts) {
    return new Date(ts * 1000).toISOString().replace("T", " ").slice(0, -5);
}


function s2ms(s) {
    var m = Math.floor(s / 60);
    return m + ":" + ("0" + (s - m * 60)).slice(-2);
}


function has(haystack, needle) {
    for (var a = 0; a < haystack.length; a++)
        if (haystack[a] == needle)
            return true;

    return false;
}


function sread(key) {
    if (window.localStorage)
        return localStorage.getItem(key);

    return '';
}

function swrite(key, val) {
    if (window.localStorage) {
        if (val === undefined)
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
