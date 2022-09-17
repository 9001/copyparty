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

        var dec = uricom_dec(n[a]).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

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
    qsr('#ml');
    return mde;
})();

function set_jumpto() {
    QS('.editor-preview-side').onclick = jumpto;
}

function jumpto(ev) {
    var tgt = ev.target;
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
    var save_btn = QS('.editor-toolbar button.save');

    clmod(save_btn, 'disabled', md_now == window.md_saved);
    set_jumpto();
}

function save(mde) {
    var save_btn = QS('.editor-toolbar button.save');
    if (clgot(save_btn, 'disabled'))
        return toast.inf(2, 'no changes');

    var force = clgot(save_btn, 'force-save');
    function save2() {
        var txt = mde.value();

        var fd = new FormData();
        fd.append("act", "tput");
        fd.append("lastmod", (force ? -1 : last_modified));
        fd.append("body", txt);

        var url = (document.location + '').split('?')[0];
        var xhr = new XHR();
        xhr.open('POST', url, true);
        xhr.responseType = 'text';
        xhr.onload = xhr.onerror = save_cb;
        xhr.btn = save_btn;
        xhr.mde = mde;
        xhr.txt = txt;
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
        if (!clgot(this.btn, 'force-save')) {
            clmod(this.btn, 'force-save', 1);
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

    clmod(this.btn, 'force-save');
    //alert('save OK -- wrote ' + r.size + ' bytes.\n\nsha512: ' + r.sha512);

    // download the saved doc from the server and compare
    var url = (document.location + '').split('?')[0] + '?raw';
    var xhr = new XHR();
    xhr.open('GET', url, true);
    xhr.responseType = 'text';
    xhr.onload = xhr.onerror = save_chk;
    xhr.btn = this.save_btn;
    xhr.mde = this.mde;
    xhr.txt = this.txt;
    xhr.lastmod = r.lastmod;
    xhr.send();
}

function save_chk() {
    if (this.status !== 200)
        return toast.err(0, 'Error!  The file was NOT saved.\n\n' + this.status + ": " + (this.responseText + '').replace(/^<pre>/, ""));

    var doc1 = this.txt.replace(/\r\n/g, "\n");
    var doc2 = this.responseText.replace(/\r\n/g, "\n");
    if (doc1 != doc2) {
        modal.alert(
            'Error! The document on the server does not appear to have saved correctly (your editor contents and the server copy is not identical). Place the document on your clipboard for now and check the server logs for hints\n\n' +
            'Length: yours=' + doc1.length + ', server=' + doc2.length
        );
        modal.alert('yours, ' + doc1.length + ' byte:\n[' + doc1 + ']');
        modal.alert('server, ' + doc2.length + ' byte:\n[' + doc2 + ']');
        return;
    }

    last_modified = this.lastmod;
    md_changed(this.mde, true);

    toast.ok(2, 'save OK' + (this.ntry ? '\nattempt ' + this.ntry : ''));
}
