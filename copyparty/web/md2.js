"use strict";


// server state
var server_md = dom_src.value;


// the non-ascii whitelist
var esc_uni_whitelist = '\\n\\t\\x20-\\x7eÆØÅæøå';
var js_uni_whitelist = eval('\'' + esc_uni_whitelist + '\'');


// dom nodes
var dom_swrap = ebi('mtw');
var dom_sbs = ebi('sbs');
var dom_nsbs = ebi('nsbs');
var dom_tbox = ebi('toolsbox');
var dom_ref = (function () {
    var d = mknod('div');
    d.setAttribute('id', 'mtr');
    dom_swrap.appendChild(d);
    d = ebi('mtr');
    // hide behind the textarea (offsetTop is not computed if display:none)
    dom_src.style.zIndex = '4';
    d.style.zIndex = '3';
    return d;
})();


// line->scrollpos maps
function genmapq(dom, query) {
    var ret = [];
    var last_y = -1;
    var parent_y = 0;
    var parent_n = null;
    var nodes = dom.querySelectorAll(query);
    for (var a = 0; a < nodes.length; a++) {
        var n = nodes[a];
        var ln = parseInt(n.getAttribute('data-ln'));
        if (ln in ret)
            continue;

        var y = 0;
        var par = n.offsetParent;
        if (par && par != parent_n) {
            while (par && par != dom) {
                y += par.offsetTop;
                par = par.offsetParent;
            }
            if (par != dom)
                continue;

            parent_y = y;
            parent_n = n.offsetParent;
        }
        while (ln > ret.length)
            ret.push(null);

        y = parent_y + n.offsetTop;
        if (y <= last_y)
            //console.log('awawa');
            continue;

        //console.log('%d  %d  (%d+%d)', a, y, parent_y, n.offsetTop);
        ret.push(y);
        last_y = y;
    }
    return ret;
}
var map_src = [];
var map_pre = [];
function genmap(dom, oldmap) {
    var find = nlines;
    while (oldmap && find-- > 0) {
        var tmap = genmapq(dom, '*[data-ln="' + find + '"]');
        if (!tmap || !tmap.length)
            continue;

        var cy = tmap[find];
        var oy = parseInt(oldmap[find]);
        if (cy + 24 > oy && cy - 24 < oy)
            return oldmap;

        console.log('map regen', dom.getAttribute('id'), find, oy, cy, oy - cy);
        break;
    }
    return genmapq(dom, '*[data-ln]');
}


// input handler
var action_stack = null;
var nlines = 0;
var draw_md = (function () {
    var delay = 1;
    function draw_md() {
        var t0 = Date.now();
        var src = dom_src.value;
        convert_markdown(src, dom_pre);

        var lines = hesc(src).replace(/\r/g, "").split('\n');
        nlines = lines.length;
        var html = [];
        for (var a = 0; a < lines.length; a++)
            html.push('<span data-ln="' + (a + 1) + '">' + lines[a] + "</span>");

        dom_ref.innerHTML = html.join('\n');
        map_src = genmap(dom_ref, map_src);
        map_pre = genmap(dom_pre, map_pre);

        cls(ebi('save'), 'disabled', src == server_md);

        var t1 = Date.now();
        delay = t1 - t0 > 100 ? 25 : 1;
    }

    var timeout = null;
    dom_src.oninput = function (e) {
        clearTimeout(timeout);
        timeout = setTimeout(draw_md, delay);
        if (action_stack)
            action_stack.push();
    };

    draw_md();
    return draw_md;
})();


// resize handler
redraw = (function () {
    function onresize() {
        var y = (dom_hbar.offsetTop + dom_hbar.offsetHeight) + 'px';
        dom_wrap.style.top = y;
        dom_swrap.style.top = y;
        dom_ref.style.width = getComputedStyle(dom_src).offsetWidth + 'px';
        map_src = genmap(dom_ref, map_src);
        map_pre = genmap(dom_pre, map_pre);
        dbg(document.body.clientWidth + 'x' + document.body.clientHeight);
    }
    function setsbs() {
        dom_wrap.setAttribute('class', '');
        dom_swrap.setAttribute('class', '');
        onresize();
    }
    function modetoggle() {
        var mode = dom_nsbs.innerHTML;
        dom_nsbs.innerHTML = mode == 'editor' ? 'preview' : 'editor';
        mode += ' single';
        dom_wrap.setAttribute('class', mode);
        dom_swrap.setAttribute('class', mode);
        onresize();
    }

    window.onresize = onresize;
    window.onscroll = null;
    dom_wrap.onscroll = null;
    dom_sbs.onclick = setsbs;
    dom_nsbs.onclick = modetoggle;

    onresize();
    return onresize;
})();


// scroll handlers
(function () {
    var skip_src = false, skip_pre = false;

    function scroll(src, srcmap, dst, dstmap) {
        var y = src.scrollTop;
        if (y < 8) {
            dst.scrollTop = 0;
            return;
        }
        if (y + 48 + src.clientHeight > src.scrollHeight) {
            dst.scrollTop = dst.scrollHeight - dst.clientHeight;
            return;
        }
        y += src.clientHeight / 2;
        var sy1 = -1, sy2 = -1, dy1 = -1, dy2 = -1;
        for (var a = 1; a < nlines + 1; a++) {
            if (srcmap[a] == null || dstmap[a] == null)
                continue;

            if (srcmap[a] > y) {
                sy2 = srcmap[a];
                dy2 = dstmap[a];
                break;
            }
            sy1 = srcmap[a];
            dy1 = dstmap[a];
        }
        if (sy1 == -1)
            return;

        var dy = dy1;
        if (sy2 != -1 && dy2 != -1) {
            var mul = (y - sy1) / (sy2 - sy1);
            dy = dy1 + (dy2 - dy1) * mul;
        }
        dst.scrollTop = dy - dst.clientHeight / 2;
    }

    dom_src.onscroll = function () {
        //dbg: dom_ref.scrollTop = dom_src.scrollTop;
        if (skip_src) {
            skip_src = false;
            return;
        }
        skip_pre = true;
        scroll(dom_src, map_src, dom_wrap, map_pre);
    };

    dom_wrap.onscroll = function () {
        if (skip_pre) {
            skip_pre = false;
            return;
        }
        skip_src = true;
        scroll(dom_wrap, map_pre, dom_src, map_src);
    };
})();


// modification checker
function Modpoll() {
    this.skip_one = true;
    this.disabled = false;

    this.periodic = function () {
        var that = this;
        setTimeout(function () {
            that.periodic();
        }, 1000 * md_opt.modpoll_freq);

        var skip = null;

        if (toast.visible)
            skip = 'toast';

        else if (this.skip_one)
            skip = 'saved';

        else if (this.disabled)
            skip = 'disabled';

        if (skip) {
            console.log('modpoll skip, ' + skip);
            this.skip_one = false;
            return;
        }

        console.log('modpoll...');
        var url = (document.location + '').split('?')[0] + '?raw&_=' + Date.now();
        var xhr = new XMLHttpRequest();
        xhr.modpoll = this;
        xhr.open('GET', url, true);
        xhr.responseType = 'text';
        xhr.onreadystatechange = this.cb;
        xhr.send();
    }

    this.cb = function () {
        if (this.modpoll.disabled || this.modpoll.skip_one) {
            console.log('modpoll abort');
            return;
        }

        if (this.readyState != XMLHttpRequest.DONE)
            return;

        if (this.status !== 200) {
            console.log('modpoll err ' + this.status + ": " + this.responseText);
            return;
        }

        if (!this.responseText)
            return;

        var server_ref = server_md.replace(/\r/g, '');
        var server_now = this.responseText.replace(/\r/g, '');

        if (server_ref != server_now) {
            console.log("modpoll diff |" + server_ref.length + "|, |" + server_now.length + "|");
            this.modpoll.disabled = true;
            var msg = [
                "The document has changed on the server.",
                "The changes will NOT be loaded into your editor automatically.",
                "",
                "Press F5 or CTRL-R to refresh the page,",
                "replacing your document with the server copy.",
                "",
                "You can close this message to ignore and contnue."
            ];
            return toast.warn(0, msg.join('\n'));
        }

        console.log('modpoll eq');
    }

    if (md_opt.modpoll_freq > 0)
        this.periodic();

    return this;
}
var modpoll = new Modpoll();


window.onbeforeunload = function (e) {
    if ((ebi("save").getAttribute('class') + '').indexOf('disabled') >= 0)
        return; //nice (todo)

    e.preventDefault(); //ff
    e.returnValue = ''; //chrome
};


// save handler
function save(e) {
    if (e) e.preventDefault();
    var save_btn = ebi("save"),
        save_cls = save_btn.getAttribute('class') + '';

    if (save_cls.indexOf('disabled') >= 0)
        return toast.inf(2, "no changes");

    var force = (save_cls.indexOf('force-save') >= 0);
    function save2() {
        var txt = dom_src.value,
            fd = new FormData();

        fd.append("act", "tput");
        fd.append("lastmod", (force ? -1 : last_modified));
        fd.append("body", txt);

        var url = (document.location + '').split('?')[0];
        var xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);
        xhr.responseType = 'text';
        xhr.onreadystatechange = save_cb;
        xhr.btn = save_btn;
        xhr.txt = txt;

        modpoll.skip_one = true;  // skip one iteration while we save
        xhr.send(fd);
    }

    if (!force)
        save2();
    else
        modal.confirm('confirm that you wish to lose the changes made on the server since you opened this document', save2, function () {
            toast.inf(3, 'aborted');
        });
}

function save_cb() {
    if (this.readyState != XMLHttpRequest.DONE)
        return;

    if (this.status !== 200)
        return toast.err(0, 'Error!  The file was NOT saved.\n\n' + this.status + ": " + (this.responseText + '').replace(/^<pre>/, ""));

    var r;
    try {
        r = JSON.parse(this.responseText);
    }
    catch (ex) {
        return toast.err(0, 'Failed to parse reply from server:\n\n' + this.responseText);
    }

    if (!r.ok) {
        if (!this.btn.classList.contains('force-save')) {
            this.btn.classList.add('force-save');
            var msg = [
                'This file has been modified since you started editing it!\n',
                'if you really want to overwrite, press save again.\n',
                'modified ' + ((r.now - r.lastmod) / 1000) + ' seconds ago,',
                ((r.lastmod - last_modified) / 1000) + ' sec after you opened it\n',
                last_modified + ' lastmod when you opened it,',
                r.lastmod + ' lastmod on the server now,',
                r.now + ' server time now,\n',
            ];
            return toast.err(0, msg.join('\n'));
        }
        else
            return toast.err(0, 'Error! Save failed.  Maybe this JSON explains why:\n\n' + this.responseText);
    }

    this.btn.classList.remove('force-save');
    //alert('save OK -- wrote ' + r.size + ' bytes.\n\nsha512: ' + r.sha512);

    run_savechk(r.lastmod, this.txt, this.btn, 0);
}

function run_savechk(lastmod, txt, btn, ntry) {
    // download the saved doc from the server and compare
    var url = (document.location + '').split('?')[0] + '?raw&_=' + Date.now();
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'text';
    xhr.onreadystatechange = savechk_cb;
    xhr.lastmod = lastmod;
    xhr.txt = txt;
    xhr.btn = btn;
    xhr.ntry = ntry;
    xhr.send();
}

function savechk_cb() {
    if (this.readyState != XMLHttpRequest.DONE)
        return;

    if (this.status !== 200)
        return toast.err(0, 'Error!  The file was NOT saved.\n\n' + this.status + ": " + (this.responseText + '').replace(/^<pre>/, ""));

    var doc1 = this.txt.replace(/\r\n/g, "\n");
    var doc2 = this.responseText.replace(/\r\n/g, "\n");
    if (doc1 != doc2) {
        var that = this;
        if (that.ntry < 10) {
            // qnap funny, try a few more times
            setTimeout(function () {
                run_savechk(that.lastmod, that.txt, that.btn, that.ntry + 1)
            }, 100);
            return;
        }
        modal.alert(
            'Error! The document on the server does not appear to have saved correctly (your editor contents and the server copy is not identical). Place the document on your clipboard for now and check the server logs for hints\n\n' +
            'Length: yours=' + doc1.length + ', server=' + doc2.length
        );
        modal.alert('yours, ' + doc1.length + ' byte:\n[' + doc1 + ']');
        modal.alert('server, ' + doc2.length + ' byte:\n[' + doc2 + ']');
        return;
    }

    last_modified = this.lastmod;
    server_md = this.txt;
    draw_md();
    toast.ok(2, 'save OK' + (this.ntry ? '\nattempt ' + this.ntry : ''));
    modpoll.disabled = false;
}


// firefox bug: initial selection offset isn't cleared properly through js
var ff_clearsel = (function () {
    if (navigator.userAgent.indexOf(') Gecko/') === -1)
        return function () { }

    return function () {
        var txt = dom_src.value;
        var y = dom_src.scrollTop;
        dom_src.value = '';
        dom_src.value = txt;
        dom_src.scrollTop = y;
    };
})();


// returns car/cdr (selection bounds) and n1/n2 (grown to full lines)
function linebounds(just_car, greedy_growth) {
    var car = dom_src.selectionStart,
        cdr = dom_src.selectionEnd;

    if (just_car)
        cdr = car;

    var md = dom_src.value,
        n1 = Math.max(car, 0),
        n2 = Math.min(cdr, md.length - 1);

    if (greedy_growth !== true) {
        if (n1 < n2 && md[n1] == '\n')
            n1++;

        if (n1 < n2 && md[n2 - 1] == '\n')
            n2 -= 2;
    }

    n1 = md.lastIndexOf('\n', n1 - 1) + 1;
    n2 = md.indexOf('\n', n2);
    if (n2 < n1)
        n2 = md.length;

    return {
        "car": car,
        "cdr": cdr,
        "n1": n1,
        "n2": n2,
        "md": md
    }
}


// linebounds + the three textranges
function getsel() {
    var s = linebounds(false);
    s.pre = s.md.substring(0, s.n1);
    s.sel = s.md.substring(s.n1, s.n2);
    s.post = s.md.substring(s.n2);
    return s;
}


// place modified getsel into markdown
function setsel(s) {
    if (s.car != s.cdr) {
        s.car = s.pre.length;
        s.cdr = s.pre.length + s.sel.length;
    }
    dom_src.value = [s.pre, s.sel, s.post].join('');
    dom_src.setSelectionRange(s.car, s.cdr, dom_src.selectionDirection);
    dom_src.oninput();
    // support chrome:
    dom_src.blur();
    dom_src.focus();
}


// indent/dedent
function md_indent(dedent) {
    var s = getsel(),
        sel0 = s.sel;

    if (dedent)
        s.sel = s.sel.replace(/^  /, "").replace(/\n  /g, "\n");
    else
        s.sel = '  ' + s.sel.replace(/\n/g, '\n  ');

    if (s.car == s.cdr)
        s.car = s.cdr += s.sel.length - sel0.length;

    setsel(s);
}


// header
function md_header(dedent) {
    var s = getsel(),
        sel0 = s.sel;

    if (dedent)
        s.sel = s.sel.replace(/^#/, "").replace(/^ +/, "");
    else
        s.sel = s.sel.replace(/^(#*) ?/, "#$1 ");

    if (s.car == s.cdr)
        s.car = s.cdr += s.sel.length - sel0.length;

    setsel(s);
}


// smart-home
function md_home(shift) {
    var s = linebounds(false, true),
        ln = s.md.substring(s.n1, s.n2),
        dir = dom_src.selectionDirection,
        rev = dir === 'backward',
        p1 = rev ? s.car : s.cdr,
        p2 = rev ? s.cdr : s.car,
        home = 0,
        lf = ln.lastIndexOf('\n') + 1,
        re = /^[ \t#>+-]*(\* )?([0-9]+\. +)?/;

    if (rev)
        home = s.n1 + re.exec(ln)[0].length;
    else
        home = s.n1 + lf + re.exec(ln.substring(lf))[0].length;

    p1 = (p1 !== home) ? home : (rev ? s.n1 : s.n1 + lf);
    if (!shift)
        p2 = p1;

    if (rev !== p1 < p2)
        dir = rev ? 'forward' : 'backward';

    if (!shift)
        ff_clearsel();

    dom_src.setSelectionRange(Math.min(p1, p2), Math.max(p1, p2), dir);
}


// autoindent
function md_newline() {
    var s = linebounds(true),
        ln = s.md.substring(s.n1, s.n2),
        m1 = /^( *)([0-9]+)(\. +)/.exec(ln),
        m2 = /^[ \t>+-]*(\* )?/.exec(ln),
        drop = dom_src.selectionEnd - dom_src.selectionStart;

    var pre = m2[0];
    if (m1 !== null)
        pre = m1[1] + (parseInt(m1[2]) + 1) + m1[3];

    if (pre.length > s.car - s.n1)
        // in gutter, do nothing
        return true;

    s.pre = s.md.substring(0, s.car) + '\n' + pre;
    s.sel = '';
    s.post = s.md.substring(s.car + drop);
    s.car = s.cdr = s.pre.length;
    setsel(s);
    return false;
}


// backspace
function md_backspace() {
    var s = linebounds(true),
        o0 = dom_src.selectionStart,
        left = s.md.slice(s.n1, o0),
        m = /^[ \t>+-]*(\* )?([0-9]+\. +)?/.exec(left);

    // if car is in whitespace area, do nothing
    if (/^\s*$/.test(left))
        return true;

    // same if selection
    if (o0 != dom_src.selectionEnd)
        return true;

    // same if line is all-whitespace or non-markup
    var v = m[0].replace(/[^ ]/g, " ");
    if (v === m[0] || v.length !== left.length)
        return true;

    s.pre = s.md.substring(0, s.n1) + v;
    s.sel = '';
    s.post = s.md.substring(s.car);
    s.car = s.cdr = s.pre.length;
    setsel(s);
    return false;
}


// paragraph jump
function md_p_jump(down) {
    var txt = dom_src.value,
        ofs = dom_src.selectionStart;

    if (down) {
        while (txt[ofs] == '\n' && --ofs > 0);
        ofs = txt.indexOf("\n\n", ofs);
        if (ofs < 0)
            ofs = txt.length - 1;

        while (txt[ofs] == '\n' && ++ofs < txt.length - 1);
    }
    else {
        txt += '\n\n';
        while (ofs > 1 && txt[ofs - 1] == '\n') ofs--;
        ofs = Math.max(0, txt.lastIndexOf("\n\n", ofs - 1));
        while (txt[ofs] == '\n' && ++ofs < txt.length - 1);
    }

    dom_src.setSelectionRange(ofs, ofs, "none");
}


function reLastIndexOf(txt, ptn, end) {
    var ofs = (typeof end !== 'undefined') ? end : txt.length;
    end = ofs;
    while (ofs >= 0) {
        var sub = txt.slice(ofs, end);
        if (ptn.test(sub))
            return ofs;

        ofs--;
    }
    return -1;
}


// table formatter
function fmt_table(e) {
    if (e) e.preventDefault();
    //dom_tbox.setAttribute('class', '');

    var txt = dom_src.value,
        ofs = dom_src.selectionStart,
        //o0 = txt.lastIndexOf('\n\n', ofs),
        //o1 = txt.indexOf('\n\n', ofs);
        o0 = reLastIndexOf(txt, /\n\s*\n/m, ofs),
        o1 = txt.slice(ofs).search(/\n\s*\n|\n\s*$/m);
    // note \s contains \n but its fine

    if (o0 < 0)
        o0 = 0;
    else {
        // seek past the hit
        var m = /\n\s*\n/m.exec(txt.slice(o0));
        o0 += m[0].length;
    }

    o1 = o1 < 0 ? txt.length : o1 + ofs;

    var err = 'cannot format table due to ',
        tab = txt.slice(o0, o1).split(/\s*\n/),
        re_ind = /^\s*/,
        ind = tab[1].match(re_ind)[0],
        r0_ind = tab[0].slice(0, ind.length),
        lpipe = tab[1].indexOf('|') < tab[1].indexOf('-'),
        rpipe = tab[1].lastIndexOf('|') > tab[1].lastIndexOf('-'),
        re_lpipe = lpipe ? /^\s*\|\s*/ : /^\s*/,
        re_rpipe = rpipe ? /\s*\|\s*$/ : /\s*$/,
        ncols;

    // the second row defines the table,
    // need to process that first
    var tmp = tab[0];
    tab[0] = tab[1];
    tab[1] = tmp;

    for (var a = 0; a < tab.length; a++) {
        var row_name = (a == 1) ? 'header' : 'row#' + (a + 1);

        var ind2 = tab[a].match(re_ind)[0];
        if (ind != ind2 && a != 1)  // the table can be a list entry or something, ignore [0]
            return toast.err(7, err + 'indentation mismatch on row#2 and ' + row_name + ',\n' + tab[a]);

        var t = tab[a].slice(ind.length);
        t = t.replace(re_lpipe, "");
        t = t.replace(re_rpipe, "");
        tab[a] = t.split(/\s*\|\s*/g);

        if (a == 0)
            ncols = tab[a].length;
        else if (ncols < tab[a].length)
            return toast.err(7, err + 'num.columns(' + row_name + ') exceeding row#2;  ' + ncols + ' < ' + tab[a].length);

        // if row has less columns than row2, fill them in
        while (tab[a].length < ncols)
            tab[a].push('');
    }

    // aight now swap em back
    tmp = tab[0];
    tab[0] = tab[1];
    tab[1] = tmp;

    var re_align = /^ *(:?)-+(:?) *$/;
    var align = [];
    for (var col = 0; col < tab[1].length; col++) {
        var m = tab[1][col].match(re_align);
        if (!m)
            return toast.err(7, err + 'invalid column specification, row#2, col ' + (col + 1) + ', [' + tab[1][col] + ']');

        if (m[2]) {
            if (m[1])
                align.push('c');
            else
                align.push('r');
        }
        else
            align.push('l');
    }

    var pad = [];
    var tmax = 0;
    for (var col = 0; col < ncols; col++) {
        var max = 0;
        for (var row = 0; row < tab.length; row++)
            if (row != 1)
                max = Math.max(max, tab[row][col].length);

        var s = '';
        for (var n = 0; n < max; n++)
            s += ' ';

        pad.push(s);
        tmax = Math.max(max, tmax);
    }

    var dashes = '';
    for (var a = 0; a < tmax; a++)
        dashes += '-';

    var ret = [];
    for (var row = 0; row < tab.length; row++) {
        var ln = [];
        for (var col = 0; col < tab[row].length; col++) {
            var p = pad[col];
            var s = tab[row][col];

            if (align[col] == 'l') {
                s = (s + p).slice(0, p.length);
            }
            else if (align[col] == 'r') {
                s = (p + s).slice(-p.length);
            }
            else {
                var pt = p.length - s.length;
                var pl = p.slice(0, Math.floor(pt / 2));
                var pr = p.slice(0, pt - pl.length);
                s = pl + s + pr;
            }

            if (row == 1) {
                if (align[col] == 'l')
                    s = dashes.slice(0, p.length);
                else if (align[col] == 'r')
                    s = dashes.slice(0, p.length - 1) + ':';
                else
                    s = ':' + dashes.slice(0, p.length - 2) + ':';
            }
            ln.push(s);
        }
        ret.push(ind + '| ' + ln.join(' | ') + ' |');
    }

    // restore any markup in the row0 gutter
    ret[0] = r0_ind + ret[0].slice(ind.length);

    ret = {
        "pre": txt.slice(0, o0),
        "sel": ret.join('\n'),
        "post": txt.slice(o1),
        "car": o0,
        "cdr": o0
    };
    setsel(ret);
}


// show unicode
function mark_uni(e) {
    if (e) e.preventDefault();
    dom_tbox.setAttribute('class', '');

    var txt = dom_src.value,
        ptn = new RegExp('([^' + js_uni_whitelist + ']+)', 'g'),
        mod = txt.replace(/\r/g, "").replace(ptn, "\u2588\u2770$1\u2771");

    if (txt == mod)
        return toast.inf(5, 'no results;  no modifications were made');

    dom_src.value = mod;
}


// iterate unicode
function iter_uni(e) {
    if (e) e.preventDefault();

    var txt = dom_src.value,
        ofs = dom_src.selectionDirection == "forward" ? dom_src.selectionEnd : dom_src.selectionStart,
        re = new RegExp('([^' + js_uni_whitelist + ']+)'),
        m = re.exec(txt.slice(ofs));

    if (!m)
        return toast.inf(5, 'no more hits from cursor onwards');

    ofs += m.index;

    dom_src.setSelectionRange(ofs, ofs + m[0].length, "forward");
    dom_src.oninput();
    // support chrome:
    dom_src.blur();
    dom_src.focus();
}


// configure whitelist
function cfg_uni(e) {
    if (e) e.preventDefault();

    modal.prompt("unicode whitelist", esc_uni_whitelist, function (reply) {
        esc_uni_whitelist = reply;
        js_uni_whitelist = eval('\'' + esc_uni_whitelist + '\'');
    }, null);
}


// hotkeys / toolbar
(function () {
    function keydown(ev) {
        ev = ev || window.event;
        var kc = ev.code || ev.keyCode || ev.which;
        //console.log(ev.key, ev.code, ev.keyCode, ev.which);
        if (ctrl(ev) && (ev.code == "KeyS" || kc == 83)) {
            save();
            return false;
        }
        if (ev.code == "Escape" || kc == 27) {
            var d = ebi('helpclose');
            if (d)
                d.click();
        }
        if (document.activeElement != dom_src)
            return true;

        if (ctrl(ev)) {
            if (ev.code == "KeyH" || kc == 72) {
                md_header(ev.shiftKey);
                return false;
            }
            if (ev.code == "KeyZ" || kc == 90) {
                if (ev.shiftKey)
                    action_stack.redo();
                else
                    action_stack.undo();

                return false;
            }
            if (ev.code == "KeyY" || kc == 89) {
                action_stack.redo();
                return false;
            }
            if (ev.code == "KeyK") {
                fmt_table();
                return false;
            }
            if (ev.code == "KeyU") {
                iter_uni();
                return false;
            }
            if (ev.code == "KeyE") {
                dom_nsbs.click();
                return false;
            }
            var up = ev.code == "ArrowUp" || kc == 38;
            var dn = ev.code == "ArrowDown" || kc == 40;
            if (up || dn) {
                md_p_jump(dn);
                return false;
            }
        }
        else {
            if (ev.code == "Tab" || kc == 9) {
                md_indent(ev.shiftKey);
                return false;
            }
            if (ev.code == "Home" || kc == 36) {
                md_home(ev.shiftKey);
                return false;
            }
            if (!ev.shiftKey && (ev.code == "Enter" || kc == 13)) {
                return md_newline();
            }
            if (!ev.shiftKey && kc == 8) {
                return md_backspace();
            }
        }
    }
    document.onkeydown = keydown;
    ebi('save').onclick = save;
})();


ebi('tools').onclick = function (e) {
    if (e) e.preventDefault();
    var is_open = dom_tbox.getAttribute('class') != 'open';
    dom_tbox.setAttribute('class', is_open ? 'open' : '');
};


ebi('help').onclick = function (e) {
    if (e) e.preventDefault();
    dom_tbox.setAttribute('class', '');

    var dom = ebi('helpbox');
    var dtxt = dom.getElementsByTagName('textarea');
    if (dtxt.length > 0) {
        convert_markdown(dtxt[0].value, dom);
        dom.innerHTML = '<a href="#" id="helpclose">close</a>' + dom.innerHTML;
    }

    dom.style.display = 'block';
    ebi('helpclose').onclick = function () {
        dom.style.display = 'none';
    };
};


ebi('fmt_table').onclick = fmt_table;
ebi('mark_uni').onclick = mark_uni;
ebi('iter_uni').onclick = iter_uni;
ebi('cfg_uni').onclick = cfg_uni;


// blame steen
action_stack = (function () {
    var hist = {
        un: [],
        re: []
    };
    var sched_cpos = 0;
    var sched_timer = null;
    var ignore = false;
    var ref = dom_src.value;

    function diff(from, to, cpos) {
        if (from === to)
            return null;

        var car = 0,
            max = Math.max(from.length, to.length);

        for (; car < max; car++)
            if (from[car] != to[car])
                break;

        var p1 = from.length,
            p2 = to.length;

        while (p1-- > 0 && p2-- > 0)
            if (from[p1] != to[p2])
                break;

        if (car > ++p1) {
            car = p1;
        }

        var txt = from.substring(car, p1)
        return {
            car: car,
            cdr: ++p2,
            txt: txt,
            cpos: cpos
        };
    }

    function undiff(from, change) {
        return {
            txt: from.substring(0, change.car) + change.txt + from.substring(change.cdr),
            cpos: change.cpos
        };
    }

    function apply(src, dst) {
        dbg('undos(%d) redos(%d)', hist.un.length, hist.re.length);

        if (src.length === 0)
            return false;

        var patch = src.pop(),
            applied = undiff(ref, patch),
            cpos = patch.cpos - (patch.cdr - patch.car) + patch.txt.length,
            reverse = diff(ref, applied.txt, cpos);

        if (reverse === null)
            return false;

        dst.push(reverse);
        ref = applied.txt;
        ignore = true; // just some browsers
        dom_src.value = ref;
        dom_src.setSelectionRange(cpos, cpos);
        ignore = true; // all browsers
        dom_src.oninput();
        return true;
    }

    function schedule_push() {
        if (ignore) {
            ignore = false;
            return;
        }
        hist.re = [];
        clearTimeout(sched_timer);
        sched_cpos = dom_src.selectionEnd;
        sched_timer = setTimeout(push, 500);
    }

    function undo() {
        if (hist.re.length == 0) {
            clearTimeout(sched_timer);
            push();
        }
        return apply(hist.un, hist.re);
    }

    function redo() {
        return apply(hist.re, hist.un);
    }

    function push() {
        var newtxt = dom_src.value;
        var change = diff(ref, newtxt, sched_cpos);
        if (change !== null)
            hist.un.push(change);

        ref = newtxt;
        dbg('undos(%d) redos(%d)', hist.un.length, hist.re.length);
        if (hist.un.length > 0)
            dbg(statify(hist.un.slice(-1)[0]));
        if (hist.re.length > 0)
            dbg(statify(hist.re.slice(-1)[0]));
    }

    return {
        undo: undo,
        redo: redo,
        push: schedule_push,
        _hist: hist,
        _ref: ref
    }
})();
