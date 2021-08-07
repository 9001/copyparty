"use strict";

var dom_toc = ebi('toc');
var dom_wrap = ebi('mw');
var dom_hbar = ebi('mh');
var dom_nav = ebi('mn');
var dom_pre = ebi('mp');
var dom_src = ebi('mt');
var dom_navtgl = ebi('navtoggle');


// chrome 49 needs this
var chromedbg = function () { console.log(arguments); }

// null-logger
var dbg = function () { };

// replace dbg with the real deal here or in the console:
// dbg = chromedbg
// dbg = console.log


// plugins
var md_plug = {};


function hesc(txt) {
    return txt.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}


function cls(dom, name, add) {
    var re = new RegExp('(^| )' + name + '( |$)');
    var lst = (dom.getAttribute('class') + '').replace(re, "$1$2").replace(/  /, "");
    dom.setAttribute('class', lst + (add ? ' ' + name : ''));
}


function statify(obj) {
    return JSON.parse(JSON.stringify(obj));
}


// dodge browser issues
(function () {
    var ua = navigator.userAgent;
    if (ua.indexOf(') Gecko/') !== -1 && /Linux| Mac /.exec(ua)) {
        // necessary on ff-68.7 at least
        var s = mknod('style');
        s.innerHTML = '@page { margin: .5in .6in .8in .6in; }';
        console.log(s.innerHTML);
        document.head.appendChild(s);
    }
})();


// add navbar
(function () {
    var n = document.location + '';
    n = n.substr(n.indexOf('//') + 2).split('?')[0].split('/');
    n[0] = 'top';
    var loc = [];
    var nav = [];
    for (var a = 0; a < n.length; a++) {
        if (a > 0)
            loc.push(n[a]);

        var dec = hesc(uricom_dec(n[a])[0]);

        nav.push('<a href="/' + loc.join('/') + '">' + dec + '</a>');
    }
    dom_nav.innerHTML = nav.join('');
})();


// faster than replacing the entire html (chrome 1.8x, firefox 1.6x)
function copydom(src, dst, lv) {
    var sc = src.childNodes,
        dc = dst.childNodes;

    if (sc.length !== dc.length) {
        dbg("replace L%d (%d/%d) |%d|",
            lv, sc.length, dc.length, src.innerHTML.length);

        dst.innerHTML = src.innerHTML;
        return;
    }

    var rpl = [];
    for (var a = sc.length - 1; a >= 0; a--) {
        var st = sc[a].tagName,
            dt = dc[a].tagName;

        if (st !== dt) {
            dbg("replace L%d (%d/%d) type %s/%s", lv, a, sc.length, st, dt);
            rpl.push(a);
            continue;
        }

        var sa = sc[a].attributes || [],
            da = dc[a].attributes || [];

        if (sa.length !== da.length) {
            dbg("replace L%d (%d/%d) attr# %d/%d",
                lv, a, sc.length, sa.length, da.length);

            rpl.push(a);
            continue;
        }

        var dirty = false;
        for (var b = sa.length - 1; b >= 0; b--) {
            var name = sa[b].name,
                sv = sa[b].value,
                dv = dc[a].getAttribute(name);

            if (name == "data-ln" && sv !== dv) {
                dc[a].setAttribute(name, sv);
                continue;
            }

            if (sv !== dv) {
                dbg("replace L%d (%d/%d) attr %s [%s] [%s]",
                    lv, a, sc.length, name, sv, dv);

                dirty = true;
                break;
            }
        }
        if (dirty)
            rpl.push(a);
    }

    // TODO pure guessing
    if (rpl.length > sc.length / 3) {
        dbg("replace L%d fully, %s (%d/%d) |%d|",
            lv, rpl.length, sc.length, src.innerHTML.length);

        dst.innerHTML = src.innerHTML;
        return;
    }

    // repl is reversed; build top-down
    var nbytes = 0;
    for (var a = rpl.length - 1; a >= 0; a--) {
        var html = sc[rpl[a]].outerHTML;
        dc[rpl[a]].outerHTML = html;
        nbytes += html.length;
    }
    if (nbytes > 0)
        dbg("replaced %d bytes L%d", nbytes, lv);

    for (var a = 0; a < sc.length; a++)
        copydom(sc[a], dc[a], lv + 1);

    if (src.innerHTML !== dst.innerHTML) {
        dbg("setting %d bytes L%d", src.innerHTML.length, lv);
        dst.innerHTML = src.innerHTML;
    }
}


function md_plug_err(ex, js) {
    var errbox = ebi('md_errbox');
    if (errbox)
        errbox.parentNode.removeChild(errbox);

    if (!ex)
        return;

    var msg = (ex + '').split('\n')[0];
    var ln = ex.lineNumber;
    var o = null;
    if (ln) {
        msg = "Line " + ln + ", " + msg;
        var lns = js.split('\n');
        if (ln < lns.length) {
            o = mknod('span');
            o.style.cssText = "color:#ac2;font-size:.9em;font-family:'scp',monospace,monospace;display:block";
            o.textContent = lns[ln - 1];
        }
    }
    errbox = mknod('div');
    errbox.setAttribute('id', 'md_errbox');
    errbox.style.cssText = 'position:absolute;top:0;left:0;padding:1em .5em;background:#2b2b2b;color:#fc5'
    errbox.textContent = msg;
    errbox.onclick = function () {
        modal.alert('<pre>' + ex.stack + '</pre>');
    };
    if (o) {
        errbox.appendChild(o);
        errbox.style.padding = '.25em .5em';
    }
    dom_nav.appendChild(errbox);

    try {
        console.trace();
    }
    catch (ex2) { }
}


function load_plug(md_text, plug_type) {
    if (!md_opt.allow_plugins)
        return md_text;

    var find = '\n```copyparty_' + plug_type + '\n';
    var ofs = md_text.indexOf(find);
    if (ofs === -1)
        return md_text;

    var ofs2 = md_text.indexOf('\n```', ofs + 1);
    if (ofs2 == -1)
        return md_text;

    var js = md_text.slice(ofs + find.length, ofs2 + 1);
    var md = md_text.slice(0, ofs + 1) + md_text.slice(ofs2 + 4);

    var old_plug = md_plug[plug_type];
    if (!old_plug || old_plug[1] != js) {
        js = 'const x = { ' + js + ' }; x;';
        try {
            var x = eval(js);
        }
        catch (ex) {
            md_plug[plug_type] = null;
            md_plug_err(ex, js);
            return md;
        }
        if (x['ctor']) {
            x['ctor']();
            delete x['ctor'];
        }
        md_plug[plug_type] = [x, js];
    }

    return md;
}


function convert_markdown(md_text, dest_dom) {
    md_text = md_text.replace(/\r/g, '');

    md_plug_err(null);
    md_text = load_plug(md_text, 'pre');
    md_text = load_plug(md_text, 'post');

    var marked_opts = {
        //headerPrefix: 'h-',
        breaks: true,
        gfm: true
    };

    var ext = md_plug['pre'];
    if (ext)
        Object.assign(marked_opts, ext[0]);

    try {
        var md_html = marked(md_text, marked_opts);
    }
    catch (ex) {
        if (ext)
            md_plug_err(ex, ext[1]);

        throw ex;
    }
    var md_dom = new DOMParser().parseFromString(md_html, "text/html").body;

    var nodes = md_dom.getElementsByTagName('a');
    for (var a = nodes.length - 1; a >= 0; a--) {
        var href = nodes[a].getAttribute('href');
        var txt = nodes[a].textContent;

        if (!txt)
            nodes[a].textContent = href;
        else if (href !== txt)
            nodes[a].setAttribute('class', 'vis');
    }

    // todo-lists (should probably be a marked extension)
    nodes = md_dom.getElementsByTagName('input');
    for (var a = nodes.length - 1; a >= 0; a--) {
        var dom_box = nodes[a];
        if (dom_box.getAttribute('type') !== 'checkbox')
            continue;

        var dom_li = dom_box.parentNode;
        var done = dom_box.getAttribute('checked');
        done = done !== null;
        var clas = done ? 'done' : 'pend';
        var char = done ? 'Y' : 'N';

        dom_li.setAttribute('class', 'task-list-item');
        dom_li.style.listStyleType = 'none';
        var html = dom_li.innerHTML;
        dom_li.innerHTML =
            '<span class="todo_' + clas + '">' + char + '</span>' +
            html.substr(html.indexOf('>') + 1);
    }

    // separate <code> for each line in <pre>
    nodes = md_dom.getElementsByTagName('pre');
    for (var a = nodes.length - 1; a >= 0; a--) {
        var el = nodes[a];

        var is_precode =
            el.tagName == 'PRE' &&
            el.childNodes.length === 1 &&
            el.childNodes[0].tagName == 'CODE';

        if (!is_precode)
            continue;

        var nline = parseInt(el.getAttribute('data-ln')) + 1;
        var lines = el.innerHTML.replace(/\n<\/code>$/i, '</code>').split(/\n/g);
        for (var b = 0; b < lines.length - 1; b++)
            lines[b] += '</code>\n<code data-ln="' + (nline + b) + '">';

        el.innerHTML = lines.join('');
    }

    // self-link headers
    var id_seen = {},
        dyn = md_dom.getElementsByTagName('*');

    nodes = [];
    for (var a = 0, aa = dyn.length; a < aa; a++)
        if (/^[Hh]([1-6])/.exec(dyn[a].tagName) !== null)
            nodes.push(dyn[a]);

    for (var a = 0; a < nodes.length; a++) {
        el = nodes[a];
        var id = el.getAttribute('id'),
            orig_id = id;

        if (id_seen[id]) {
            for (var n = 1; n < 4096; n++) {
                id = orig_id + '-' + n;
                if (!id_seen[id])
                    break;
            }
            el.setAttribute('id', id);
        }
        id_seen[id] = 1;
        el.innerHTML = '<a href="#' + id + '">' + el.innerHTML + '</a>';
    }

    ext = md_plug['post'];
    if (ext && ext[0].render)
        try {
            ext[0].render(md_dom);
        }
        catch (ex) {
            md_plug_err(ex, ext[1]);
        }

    copydom(md_dom, dest_dom, 0);

    if (ext && ext[0].render2)
        try {
            ext[0].render2(dest_dom);
        }
        catch (ex) {
            md_plug_err(ex, ext[1]);
        }
}


function init_toc() {
    var loader = ebi('ml');
    loader.parentNode.removeChild(loader);

    var anchors = [];  // list of toc entries, complex objects
    var anchor = null; // current toc node
    var html = [];     // generated toc html
    var lv = 0;        // current indentation level in the toc html
    var ctr = [0, 0, 0, 0, 0, 0];

    var manip_nodes_dyn = dom_pre.getElementsByTagName('*');
    var manip_nodes = [];
    for (var a = 0, aa = manip_nodes_dyn.length; a < aa; a++)
        manip_nodes.push(manip_nodes_dyn[a]);

    for (var a = 0, aa = manip_nodes.length; a < aa; a++) {
        var elm = manip_nodes[a];
        var m = /^[Hh]([1-6])/.exec(elm.tagName);
        var is_header = m !== null;
        if (is_header) {
            var nlv = m[1];
            while (lv < nlv) {
                html.push('<ul>');
                lv++;
            }
            while (lv > nlv) {
                html.push('</ul>');
                lv--;
            }
            ctr[lv - 1]++;
            for (var b = lv; b < 6; b++)
                ctr[b] = 0;

            elm.childNodes[0].setAttribute('ctr', ctr.slice(0, lv).join('.'));

            var elm2 = elm.cloneNode(true);
            elm2.childNodes[0].textContent = elm.textContent;
            while (elm2.childNodes.length > 1)
                elm2.removeChild(elm2.childNodes[1]);

            html.push('<li>' + elm2.innerHTML + '</li>');

            if (anchor != null)
                anchors.push(anchor);

            anchor = {
                elm: elm,
                kids: [],
                y: null
            };
        }
        if (!is_header && anchor)
            anchor.kids.push(elm);
    }
    dom_toc.innerHTML = html.join('\n');
    if (anchor != null)
        anchors.push(anchor);

    // copy toc links into the toc list
    var atoc = dom_toc.getElementsByTagName('a');
    for (var a = 0, aa = anchors.length; a < aa; a++)
        anchors[a].lnk = atoc[a];

    // collect vertical position of all toc items (headers in document)
    function freshen_offsets() {
        var top = window.pageYOffset || document.documentElement.scrollTop;
        for (var a = anchors.length - 1; a >= 0; a--) {
            var y = top + anchors[a].elm.getBoundingClientRect().top;
            y = Math.round(y * 10.0) / 10;
            if (anchors[a].y === y)
                break;

            anchors[a].y = y;
        }
    }

    // hilight the correct toc items + scroll into view
    function freshen_toclist() {
        if (anchors.length == 0)
            return;

        var ptop = window.pageYOffset || document.documentElement.scrollTop;
        var hit = anchors.length - 1;
        for (var a = 0; a < anchors.length; a++) {
            if (anchors[a].y >= ptop - 8) {  //???
                hit = a;
                break;
            }
        }

        var links = dom_toc.getElementsByTagName('a');
        if (!anchors[hit].active) {
            for (var a = 0; a < anchors.length; a++) {
                if (anchors[a].active) {
                    anchors[a].active = false;
                    links[a].setAttribute('class', '');
                }
            }
            anchors[hit].active = true;
            links[hit].setAttribute('class', 'act');
        }

        var pane_height = parseInt(getComputedStyle(dom_toc).height);
        var link_bounds = links[hit].getBoundingClientRect();
        var top = link_bounds.top - (pane_height / 6);
        var btm = link_bounds.bottom + (pane_height / 6);
        if (top < 0)
            dom_toc.scrollTop -= -top;
        else if (btm > pane_height)
            dom_toc.scrollTop += btm - pane_height;
    }

    function refresh() {
        freshen_offsets();
        freshen_toclist();
    }

    return { "refresh": refresh }
}


// "main" :p
convert_markdown(dom_src.value, dom_pre);
var toc = init_toc();


// scroll handler
var redraw = (function () {
    var sbs = false;
    function onresize() {
        sbs = window.matchMedia('(min-width: 64em)').matches;
        var y = (dom_hbar.offsetTop + dom_hbar.offsetHeight) + 'px';
        if (sbs) {
            dom_toc.style.top = y;
            dom_wrap.style.top = y;
            dom_toc.style.marginTop = '0';
        }
        onscroll();
    }

    function onscroll() {
        toc.refresh();
    }

    window.onresize = onresize;
    window.onscroll = onscroll;
    dom_wrap.onscroll = onscroll;

    onresize();
    return onresize;
})();


dom_navtgl.onclick = function () {
    var hidden = dom_navtgl.innerHTML == 'hide nav';
    dom_navtgl.innerHTML = hidden ? 'show nav' : 'hide nav';
    dom_nav.style.display = hidden ? 'none' : 'block';

    swrite('hidenav', hidden ? 1 : 0);
    redraw();
};

if (sread('hidenav') == 1)
    dom_navtgl.onclick();

if (window['tt'])
    tt.init();
