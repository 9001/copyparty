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
    var k = this.closest('tr').getElementsByTagName('a')[2].getAttribute('k'),
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

function qr(e) {
    ev(e);
    var href = this.href,
        pw = this.closest('tr').cells[2].textContent;

    if (pw.indexOf('yes') < 0)
        return showqr(href);

    modal.prompt("if you want to bypass the password protection by\nembedding the password into the qr-code, then\ntype the password now, otherwise leave this empty", "", function (v) {
        if (v)
            href += "&pw=" + v;
        showqr(href);
    });
}

function showqr(href) {
    var vhref = href.replace('?qr&', '?').replace('?qr', '');
    modal.alert(esc(vhref) + '<img class="b64" src="' + href + '" />');
}

(function() {
    var tab = ebi('tab').tBodies[0],
        tr = Array.prototype.slice.call(tab.rows, 0);

    var buf = [];
    for (var a = 0; a < tr.length; a++) {
        tr[a].cells[0].getElementsByTagName('a')[0].onclick = qr;
        for (var b = 7; b < 9; b++)
            buf.push(parseInt(tr[a].cells[b].innerHTML));
    }

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
