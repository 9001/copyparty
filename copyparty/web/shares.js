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
