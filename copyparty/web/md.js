/*var conv = new showdown.Converter();
conv.setFlavor('github');
conv.setOption('tasklists', 0);
var mhtml = conv.makeHtml(dom_md.value);
*/

var dom_toc = document.getElementById('toc');
var dom_wrap = document.getElementById('mw');
var dom_head = document.getElementById('mh');
var dom_nav = document.getElementById('mn');
var dom_doc = document.getElementById('m');
var dom_md = document.getElementById('mt');

// add toolbar buttons
(function () {
    var n = document.location + '';
    n = n.substr(n.indexOf('//') + 2).split('?')[0].split('/');
    n[0] = 'top';
    var loc = [];
    var nav = [];
    for (var a = 0; a < n.length; a++) {
        if (a > 0)
            loc.push(n[a]);

        var dec = decodeURIComponent(n[a]).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

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
    dom_doc.innerHTML = html;

    var loader = document.getElementById('ml');
    loader.parentNode.removeChild(loader);

    // todo-lists (should probably be a marked extension)
    var nodes = dom_doc.getElementsByTagName('input');
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
}

function init_toc() {
    var anchors = [];  // list of toc entries, complex objects
    var anchor = null; // current toc node
    var id_seen = {};  // taken IDs
    var html = [];     // generated toc html
    var lv = 0;        // current indentation level in the toc html
    var re = new RegExp('^[Hh]([1-3])');

    var manip_nodes_dyn = dom_doc.getElementsByTagName('*');
    var manip_nodes = [];
    for (var a = 0, aa = manip_nodes_dyn.length; a < aa; a++)
        manip_nodes.push(manip_nodes_dyn[a]);

    for (var a = 0, aa = manip_nodes.length; a < aa; a++) {
        var elm = manip_nodes[a];
        var m = re.exec(elm.tagName);

        var is_header =
            m !== null;

        var is_precode =
            !is_header &&
            elm.tagName == 'PRE' &&
            elm.childNodes.length === 1 &&
            elm.childNodes[0].tagName == 'CODE';

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
        else if (is_precode) {
            // not actually toc-related (sorry),
            // split <pre><code /></pre> into one <code> per line
            var nline = parseInt(elm.getAttribute('data-ln')) + 1;
            var lines = elm.innerHTML.replace(/\r?\n<\/code>$/i, '</code>').split(/\r?\n/g);
            for (var b = 0; b < lines.length - 1; b++)
                lines[b] += '</code>\n<code data-ln="' + (nline + b) + '">';

            elm.innerHTML = lines.join('');
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
convert_markdown(dom_md.value);
var toc = init_toc();


// scroll handler
(function () {
    var timer_active = false;
    var final = null;

    function onscroll() {
        clearTimeout(final);
        timer_active = false;
        toc.refresh();

        var y = 0;
        if (window.matchMedia('(min-width: 64em)').matches)
            y = parseInt(dom_nav.offsetHeight) - window.scrollY;

        dom_toc.style.marginTop = y < 0 ? 0 : y + "px";
    }
    onscroll();

    function ev_onscroll() {
        // long timeout: scroll ended
        clearTimeout(final);
        final = setTimeout(onscroll, 100);

        // short timeout: continuous updates
        if (timer_active)
            return;

        timer_active = true;
        setTimeout(onscroll, 10);
    };

    window.onscroll = ev_onscroll;
    window.onresize = ev_onscroll;
})();
