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
    var tb = table.tBodies[0], // use `<tbody>` to ignore `<thead>` and `<tfoot>` rows
        th = table.tHead.rows[0].cells,
        tr = Array.prototype.slice.call(tb.rows, 0),
        i, reverse = th[col].className == 'sort1' ? -1 : 1;
    for (var a = 0, thl = th.length; a < thl; a++)
        th[a].className = '';
    th[col].className = 'sort' + reverse;
    var stype = th[col].getAttribute('sort');
    tr = tr.sort(function (a, b) {
        if (!a.cells[col])
            return -1;
        if (!b.cells[col])
            return 1;

        var v1 = a.cells[col].textContent.trim();
        var v2 = b.cells[col].textContent.trim();
        if (stype == 'int') {
            v1 = parseInt(v1.replace(/,/g, ''));
            v2 = parseInt(v2.replace(/,/g, ''));
            return reverse * (v1 - v2);
        }
        return reverse * (v1.localeCompare(v2));
    });
    for (i = 0; i < tr.length; ++i) tb.appendChild(tr[i]);
}
function makeSortable(table) {
    var th = table.tHead, i;
    th && (th = th.rows[0]) && (th = th.cells);
    if (th) i = th.length;
    else return; // if no `<thead>` then do nothing
    while (--i >= 0) (function (i) {
        th[i].onclick = function () {
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


function opclick(ev) {
    if (ev) //ie
        ev.preventDefault();

    var dest = this.getAttribute('data-dest');
    goto(dest);

    // writing a blank value makes ie8 segfault w
    if (window.localStorage)
        localStorage.setItem('opmode', dest || '.');

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
    if (window.localStorage) {
        var op = localStorage.getItem('opmode');
        if (op !== null && op !== '.')
            goto(op);
    }
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


function has(haystack, needle) {
    for (var a = 0; a < haystack.length; a++)
        if (haystack[a] == needle)
            return true;

    return false;
}
