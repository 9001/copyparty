var dom_toc = document.getElementById('toc');
var dom_wrap = document.getElementById('mw');
var dom_hbar = document.getElementById('mh');
var dom_nav = document.getElementById('mn');
var dom_pre = document.getElementById('mp');
var dom_src = document.getElementById('mt');
var dom_navtgl = document.getElementById('navtoggle');

function hesc(txt) {
    return txt.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

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

        var dec = hesc(decodeURIComponent(n[a]));

        nav.push('<a href="/' + loc.join('/') + '">' + dec + '</a>');
    }
    dom_nav.innerHTML = nav.join('');
})();

function convert_markdown(md_text) {
    marked.setOptions({
        //headerPrefix: 'h-',
        breaks: true,
        gfm: true
    });
    var html = marked(md_text);
    dom_pre.innerHTML = html;

    // todo-lists (should probably be a marked extension)
    var nodes = dom_pre.getElementsByTagName('input');
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

    var manip_nodes = dom_pre.getElementsByTagName('*');
    for (var a = manip_nodes.length - 1; a >= 0; a--) {
        var el = manip_nodes[a];

        var is_precode =
            el.tagName == 'PRE' &&
            el.childNodes.length === 1 &&
            el.childNodes[0].tagName == 'CODE';

        if (!is_precode)
            continue;

        var nline = parseInt(el.getAttribute('data-ln')) + 1;
        var lines = el.innerHTML.replace(/\r?\n<\/code>$/i, '</code>').split(/\r?\n/g);
        for (var b = 0; b < lines.length - 1; b++)
            lines[b] += '</code>\n<code data-ln="' + (nline + b) + '">';

        el.innerHTML = lines.join('');
    }
}

function init_toc() {
    var loader = document.getElementById('ml');
    loader.parentNode.removeChild(loader);

    var anchors = [];  // list of toc entries, complex objects
    var anchor = null; // current toc node
    var id_seen = {};  // taken IDs
    var html = [];     // generated toc html
    var lv = 0;        // current indentation level in the toc html
    var re = new RegExp('^[Hh]([1-3])');

    var manip_nodes_dyn = dom_pre.getElementsByTagName('*');
    var manip_nodes = [];
    for (var a = 0, aa = manip_nodes_dyn.length; a < aa; a++)
        manip_nodes.push(manip_nodes_dyn[a]);

    for (var a = 0, aa = manip_nodes.length; a < aa; a++) {
        var elm = manip_nodes[a];
        var m = re.exec(elm.tagName);
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

            var orig_id = elm.getAttribute('id');
            var id = orig_id;
            if (id_seen[id]) {
                for (var n = 1; n < 4096; n++) {
                    id = orig_id + '-' + n;
                    if (!id_seen[id])
                        break;
                }
                elm.setAttribute('id', id);
            }
            id_seen[id] = 1;

            var ahref = '<a href="#' + id + '">' +
                elm.innerHTML + '</a>';

            html.push('<li>' + ahref + '</li>');
            elm.innerHTML = ahref;

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
convert_markdown(dom_src.value);
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
    var timeout = null;
    function show_nav(e) {
        if (e && e.target == dom_hbar && e.pageX && e.pageX < dom_hbar.offsetWidth / 2)
            return;

        clearTimeout(timeout);
        dom_nav.style.display = 'block';
    }
    function hide_nav() {
        clearTimeout(timeout);
        timeout = setTimeout(function () {
            dom_nav.style.display = 'none';
        }, 30);
    }
    var hidden = dom_navtgl.innerHTML == 'hide nav';
    dom_navtgl.innerHTML = hidden ? 'show nav' : 'hide nav';
    if (hidden) {
        dom_nav.setAttribute('class', 'undocked');
        dom_nav.style.display = 'none';
        dom_nav.style.top = dom_hbar.offsetHeight + 'px';
        dom_nav.onmouseenter = show_nav;
        dom_nav.onmouseleave = hide_nav;
        dom_hbar.onmouseenter = show_nav;
        dom_hbar.onmouseleave = hide_nav;
    }
    else {
        dom_nav.setAttribute('class', '');
        dom_nav.style.display = 'block';
        dom_nav.style.top = '0';
        dom_nav.onmouseenter = null;
        dom_nav.onmouseleave = null;
        dom_hbar.onmouseenter = null;
        dom_hbar.onmouseleave = null;
    }
    if (window.localStorage)
        localStorage.setItem('hidenav', hidden ? 1 : 0);

    redraw();
};

if (window.localStorage && localStorage.getItem('hidenav') == 1)
    dom_navtgl.onclick();
