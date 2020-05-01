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
            action: (mde) => {
                alert("TODO save (" + (mde.value().length / 1024) + ' kB)');
            }
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
    var loader = document.getElementById('ml');
    loader.parentNode.removeChild(loader);
})();

zsetTimeout(function () { window.location.reload(true); }, 1000);
