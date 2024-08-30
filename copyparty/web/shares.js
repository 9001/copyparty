var t = QSA('a[k]');
for (var a = 0; a < t.length; a++)
    t[a].onclick = rm;

function rm() {
    var u = SR + shr + uricom_enc(this.getAttribute('k')) + '?eshare=rm',
        xhr = new XHR();

    xhr.open('POST', u, true);
    xhr.onload = xhr.onerror = cb;
    xhr.send();
}

function bump() {
    var k = this.closest('tr').getElementsByTagName('a')[0].getAttribute('k'),
        u = SR + shr + uricom_enc(k) + '?eshare=' + this.value,
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

    for (var a = 0; a < tr.length; a++)
        tr[a].cells[11].innerHTML =
            '<button value="1">1min</button> ' +
            '<button value="60">1h</button>';
    
    var btns = QSA('td button'), aa = btns.length;
    for (var a = 0; a < aa; a++)
        btns[a].onclick = bump;
})();
