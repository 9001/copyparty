// server state
var server_md = dom_src.value;


// dom nodes
var dom_swrap = document.getElementById('mtw');
var dom_ref = (function () {
    var d = document.createElement('div');
    d.setAttribute('id', 'mtr');
    dom_swrap.appendChild(d);
    d = document.getElementById('mtr');
    // hide behind the textarea (offsetTop is not computed if display:none)
    dom_src.style.zIndex = '4';
    d.style.zIndex = '3';
    return d;
})();


// line->scrollpos maps
var map_src = [];
var map_pre = [];
function genmap(dom) {
    var ret = [];
    var parent_y = 0;
    var parent_n = null;
    var nodes = dom.querySelectorAll('*[data-ln]');
    for (var a = 0; a < nodes.length; a++) {
        var n = nodes[a];
        var ln = parseInt(n.getAttribute('data-ln'));
        if (ln in ret)
            continue;

        var y = 0;
        var par = n.offsetParent;
        if (par != parent_n) {
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

        ret.push(parent_y + n.offsetTop);
    }
    return ret;
}


// input handler
var nlines = 0;
(function () {
    dom_src.oninput = function (e) {
        var src = dom_src.value;
        convert_markdown(src);

        var lines = hesc(src).replace(/\r/g, "").split('\n');
        nlines = lines.length;
        var html = [];
        for (var a = 0; a < lines.length; a++)
            html.push('<span data-ln="' + (a + 1) + '">' + lines[a] + "</span>");

        dom_ref.innerHTML = html.join('\n');
        map_src = genmap(dom_ref);
        map_pre = genmap(dom_pre);

        var sb = document.getElementById('save');
        var cl = (sb.getAttribute('class') + '').replace(/ disabled/, "");
        if (src == server_md)
            cl += ' disabled';

        sb.setAttribute('class', cl);
    }
    dom_src.oninput();
})();


// resize handler
redraw = (function () {
    function onresize() {
        var y = (dom_hbar.offsetTop + dom_hbar.offsetHeight) + 'px';
        dom_wrap.style.top = y;
        dom_swrap.style.top = y;
        dom_ref.style.width = (dom_src.offsetWidth - 4) + 'px';
        map_src = genmap(dom_ref);
        map_pre = genmap(dom_pre);
        console.log(document.body.clientWidth + 'x' + document.body.clientHeight);
    };

    window.onresize = onresize;
    window.onscroll = null;
    dom_wrap.onscroll = null;

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
        if (y + 8 + src.clientHeight > src.scrollHeight) {
            dst.scrollTop = dst.scrollHeight - dst.clientHeight;
            return;
        }
        y += src.clientHeight / 2;
        var sy1 = -1, sy2 = -1, dy1 = -1, dy2 = -1;
        for (var a = 1; a < nlines + 1; a++) {
            if (srcmap[a] === null || dstmap[a] === null)
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


// save handler
function save(e) {
    if (e) e.preventDefault();
    var save_btn = document.getElementById("save"),
        save_cls = save_btn.getAttribute('class') + '';

    if (save_cls.indexOf('disabled') >= 0) {
        alert('there is nothing to save');
        return;
    }

    var force = (save_cls.indexOf('force-save') >= 0);
    if (force && !confirm('confirm that you wish to lose the changes made on the server since you opened this document')) {
        alert('ok, aborted');
        return;
    }

    var txt = dom_src.value;

    var fd = new FormData();
    fd.append("act", "tput");
    fd.append("lastmod", (force ? -1 : last_modified));
    fd.append("body", txt);

    var url = (document.location + '').split('?')[0] + '?raw';
    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.responseType = 'text';
    xhr.onreadystatechange = save_cb;
    xhr.btn = save_btn;
    xhr.txt = txt;
    xhr.send(fd);
}

function save_cb() {
    if (this.readyState != XMLHttpRequest.DONE)
        return;

    if (this.status !== 200) {
        alert('Error!  The file was NOT saved.\n\n' + this.status + ": " + (this.responseText + '').replace(/^<pre>/, ""));
        return;
    }

    var r;
    try {
        r = JSON.parse(this.responseText);
    }
    catch (ex) {
        alert('Failed to parse reply from server:\n\n' + this.responseText);
        return;
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
            alert(msg.join('\n'));
        }
        else {
            alert('Error! Save failed.  Maybe this JSON explains why:\n\n' + this.responseText);
        }
        return;
    }

    this.btn.classList.remove('force-save');
    //alert('save OK -- wrote ' + r.size + ' bytes.\n\nsha512: ' + r.sha512);

    // download the saved doc from the server and compare
    var url = (document.location + '').split('?')[0] + '?raw';
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'text';
    xhr.onreadystatechange = save_chk;
    xhr.btn = this.save_btn;
    xhr.txt = this.txt;
    xhr.lastmod = r.lastmod;
    xhr.send();
}

function save_chk() {
    if (this.readyState != XMLHttpRequest.DONE)
        return;

    if (this.status !== 200) {
        alert('Error!  The file was NOT saved.\n\n' + this.status + ": " + (this.responseText + '').replace(/^<pre>/, ""));
        return;
    }

    var doc1 = this.txt.replace(/\r\n/g, "\n");
    var doc2 = this.responseText.replace(/\r\n/g, "\n");
    if (doc1 != doc2) {
        alert(
            'Error! The document on the server does not appear to have saved correctly (your editor contents and the server copy is not identical). Place the document on your clipboard for now and check the server logs for hints\n\n' +
            'Length: yours=' + doc1.length + ', server=' + doc2.length
        );
        alert('yours, ' + doc1.length + ' byte:\n[' + doc1 + ']');
        alert('server, ' + doc2.length + ' byte:\n[' + doc2 + ']');
        return;
    }

    last_modified = this.lastmod;
    server_md = this.txt;
    dom_src.oninput();

    var ok = document.createElement('div');
    ok.setAttribute('style', 'font-size:6em;font-family:serif;font-weight:bold;color:#cf6;background:#444;border-radius:.3em;padding:.6em 0;position:fixed;top:30%;left:calc(50% - 2em);width:4em;text-align:center;z-index:9001;transition:opacity 0.2s ease-in-out;opacity:1');
    ok.innerHTML = 'OK✔️';
    var parent = document.getElementById('m');
    document.documentElement.appendChild(ok);
    setTimeout(function () {
        ok.style.opacity = 0;
    }, 500);
    setTimeout(function () {
        ok.parentNode.removeChild(ok);
    }, 750);
}


// returns [before,selection,after]
function getsel() {
    var car = dom_src.selectionStart;
    var cdr = dom_src.selectionEnd;
    console.log(car, cdr);

    var txt = dom_src.value;
    car = Math.max(car, 0);
    cdr = Math.min(cdr, txt.length - 1);

    if (car < cdr && txt[car] == '\n')
        car++;

    if (car < cdr && txt[cdr - 1] == '\n')
        cdr -= 2;

    car = txt.lastIndexOf('\n', car - 1) + 1;
    cdr = txt.indexOf('\n', cdr);
    if (cdr < car)
        cdr = txt.length;

    return [
        txt.substring(0, car),
        txt.substring(car, cdr),
        txt.substring(cdr)
    ];
}


// place modified getsel into markdown
function setsel(a, b, c) {
    dom_src.value = [a, b, c].join('');
    dom_src.setSelectionRange(a.length, a.length + b.length);
    dom_src.oninput();
}


// indent/dedent
function md_indent(dedent) {
    var r = getsel(),
        pre = r[0],
        sel = r[1],
        post = r[2];

    if (dedent)
        sel = sel.replace(/^  /, "").replace(/\n  /g, "\n");
    else
        sel = '  ' + sel.replace(/\n/g, '\n  ');

    setsel(pre, sel, post);
}


// header
function md_header(dedent) {
    var r = getsel(),
        pre = r[0],
        sel = r[1],
        post = r[2];

    if (dedent)
        sel = sel.replace(/^#/, "").replace(/^ +/, "");
    else
        sel = sel.replace(/^(#*) ?/, "#$1 ");

    setsel(pre, sel, post);
}


// hotkeys / toolbar
(function () {
    function keydown(ev) {
        ev = ev || window.event;
        var kc = ev.keyCode || ev.which;
        var ctrl = ev.ctrlKey || ev.metaKey;
        //console.log(ev.code, kc);
        if (ctrl && (ev.code == "KeyS" || kc == 83)) {
            save();
            return false;
        }
        if (document.activeElement == dom_src) {
            if (ev.code == "Tab" || kc == 9) {
                md_indent(ev.shiftKey);
                return false;
            }
            if (ctrl && (ev.code == "KeyH" || kc == 72)) {
                md_header(ev.shiftKey);
                return false;
            }
        }
    }
    document.onkeydown = keydown;
    document.getElementById('save').onclick = save;
})();


document.getElementById('help').onclick = function (e) {
    if (e) e.preventDefault();
    var dom = document.getElementById('helpbox');
    var dtxt = dom.getElementsByTagName('textarea');
    if (dtxt.length > 0)
        dom.innerHTML = '<a href="#" id="helpclose">close</a>' + marked(dtxt[0].value);

    dom.style.display = 'block';
    document.getElementById('helpclose').onclick = function () {
        dom.style.display = 'none';
    };
};
