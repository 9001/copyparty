var t = QSA('a[k]');
for (var a = 0; a < t.length; a++)
    t[a].onclick = rm;

function rm() {
    var u = SR + shr + uricom_enc(this.getAttribute('k')) + '?unshare',
        xhr = new XHR();

    xhr.open('POST', u, true);
    xhr.onload = xhr.onerror = cb;
    xhr.send();
}

function cb() {
    if (this.status !== 200)
        return modal.alert('<h6>server error</h6>' + esc(unpre(this.responseText)));

    document.location = '?shares';
}

(function() {
    var tab = ebi('tab').tBodies[0],
        tr = Array.prototype.slice.call(tab.rows, 0);

    var buf = [];
    for (var a = 0; a < tr.length; a++)
        for (var b = 7; b < 9; b++)
            buf.push(parseInt(tr[a].cells[b].innerHTML));

    var ibuf = 0;
    for (var a = 0; a < tr.length; a++)
        for (var b = 7; b < 9; b++) {
            var v = buf[ibuf++];
            tr[a].cells[b].innerHTML =
                v ? unix2iso(v).replace(' ', ',&nbsp;') : 'never';
        }
})();
