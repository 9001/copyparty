"use strict";

var dom_wrap = ebi('mw');
var dom_nav = ebi('mn');
var dom_doc = ebi('m');
var dom_md = ebi('mt');

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

var mde = (function () {
    var tbar = [
        {
            name: "light",
            title: "light",
            className: "fa fa-lightbulb",
            action: lightswitch
        }, {
            name: "save",
            title: "save",
            className: "fa fa-save",
            action: save
        }, '|',
        'bold', 'italic', 'strikethrough', 'heading', '|',
        'code', 'quote', 'unordered-list', 'ordered-list', 'clean-block', '|',
        'link', 'image', 'table', 'horizontal-rule', '|',
        'preview', 'side-by-side', 'fullscreen', '|',
        'undo', 'redo'];

    var mde = new EasyMDE({
        autoDownloadFontAwesome: false,
        autofocus: true,
        spellChecker: false,
        renderingConfig: {
            markedOptions: {
                breaks: true,
                gfm: true
            }
        },
        shortcuts: {
            "save": "Ctrl-S"
        },
        insertTexts: ["[](", ")"],
        indentWithTabs: false,
        tabSize: 2,
        toolbar: tbar,
        previewClass: 'mdo',
        onToggleFullScreen: set_jumpto,
    });
    md_changed(mde, true);
    mde.codemirror.on("change", function () {
        md_changed(mde);
    });
    var loader = ebi('ml');
    loader.parentNode.removeChild(loader);
    return mde;
})();

function set_jumpto() {
    document.querySelector('.editor-preview-side').onclick = jumpto;
}

function jumpto(ev) {
    var tgt = ev.target || ev.srcElement;
    var ln = null;
    while (tgt && !ln) {
        ln = tgt.getAttribute('data-ln');
        tgt = tgt.parentElement;
    }
    var ln = parseInt(ln);
    console.log(ln);
    var cm = mde.codemirror;
    var y = cm.heightAtLine(ln - 1, 'local');
    var y2 = cm.heightAtLine(ln, 'local');
    cm.scrollTo(null, y + (y2 - y) - cm.getScrollInfo().clientHeight / 2);
}

function md_changed(mde, on_srv) {
    if (on_srv)
        window.md_saved = mde.value();

    var md_now = mde.value();
    var save_btn = document.querySelector('.editor-toolbar button.save');

    if (md_now == window.md_saved)
        save_btn.classList.add('disabled');
    else
        save_btn.classList.remove('disabled');

    set_jumpto();
}

function save(mde) {
    var save_btn = document.querySelector('.editor-toolbar button.save');
    if (save_btn.classList.contains('disabled')) {
        alert('there is nothing to save');
        return;
    }
    var force = save_btn.classList.contains('force-save');
    if (force && !confirm('confirm that you wish to lose the changes made on the server since you opened this document')) {
        alert('ok, aborted');
        return;
    }

    var txt = mde.value();

    var fd = new FormData();
    fd.append("act", "tput");
    fd.append("lastmod", (force ? -1 : last_modified));
    fd.append("body", txt);

    var url = (document.location + '').split('?')[0];
    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.responseType = 'text';
    xhr.onreadystatechange = save_cb;
    xhr.btn = save_btn;
    xhr.mde = mde;
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
    xhr.mde = this.mde;
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
    md_changed(this.mde, true);

    var ok = document.createElement('div');
    ok.setAttribute('style', 'font-size:6em;font-family:serif;font-weight:bold;color:#cf6;background:#444;border-radius:.3em;padding:.6em 0;position:fixed;top:30%;left:calc(50% - 2em);width:4em;text-align:center;z-index:9001;transition:opacity 0.2s ease-in-out;opacity:1');
    ok.innerHTML = 'OK✔️';
    var parent = ebi('m');
    document.documentElement.appendChild(ok);
    setTimeout(function () {
        ok.style.opacity = 0;
    }, 500);
    setTimeout(function () {
        ok.parentNode.removeChild(ok);
    }, 750);
}
