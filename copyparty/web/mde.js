var dom_wrap = document.getElementById('mw');
var dom_nav = document.getElementById('mn');
var dom_doc = document.getElementById('m');
var dom_md = document.getElementById('mt');

(function () {
    var n = document.location + '';
    n = n.substr(n.indexOf('//') + 2).split('?')[0].split('/');
    n[0] = 'top';
    var loc = [];
    var nav = [];
    for (var a = 0; a < n.length; a++) {
        if (a > 0)
            loc.push(n[a]);

        nav.push('<a href="/' + loc.join('/') + '">' + n[a] + '</a>');
    }
    dom_nav.innerHTML = nav.join('');
})();

(function () {
    var tbar = [
        {
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
        insertTexts: ["[](", ")"],
        renderingConfig: {
            markedOptions: {
                breaks: true,
                gfm: true
            }
        },
        spellChecker: false,
        tabSize: 4,
        toolbar: tbar
    });
    md_changed(mde, true);
    mde.codemirror.on("change", function () {
        md_changed(mde);
    });
    var loader = document.getElementById('ml');
    loader.parentNode.removeChild(loader);
})();

function md_changed(mde, on_srv) {
    if (on_srv)
        window.md_saved = mde.value();

    var md_now = mde.value();
    var save_btn = document.querySelector('.editor-toolbar button.save');

    if (md_now == window.md_saved)
        save_btn.classList.add('disabled');
    else
        save_btn.classList.remove('disabled');
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

    var fd = new FormData();
    fd.append("act", "tput");
    fd.append("lastmod", (force ? -1 : last_modified));
    fd.append("body", mde.value());

    var url = (document.location + '').split('?')[0] + '?raw';
    var xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.responseType = 'text';
    xhr.onreadystatechange = save_cb;
    xhr.btn = save_btn;
    xhr.mde = mde;
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
    catch {
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

    last_modified = r.lastmod;
    this.btn.classList.remove('force-save');
    alert('save OK -- wrote ' + r.size + ' bytes.\n\nsha512: ' + r.sha512);
    md_changed(this.mde, true);
}
