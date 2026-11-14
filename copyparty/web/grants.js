"use strict";

// fork-only: the grants page (?grants); see FORK.md

var J_GR = 1;

function egrant(tr, act) {
    var u = SR + '/?egrant=' + act + '&gid=' + tr.getAttribute('gid'),
        xhr = new XHR();

    xhr.open('POST', u, true);
    xhr.onload = xhr.onerror = cb;
    xhr.send();
}

function cb() {
    if (this.status !== 200)
        return modal.alert('<h6>server error</h6>' + esc(unpre(this.responseText)));

    location = '?grants';
}

(function () {
    var t = QSA('a.rm');
    for (var a = 0; a < t.length; a++)
        t[a].onclick = function (e) {
            ev(e);
            var tr = this.closest('tr');
            modal.confirm('revoke this grant?', function () {
                egrant(tr, 'rm');
            }, null);
        };

    t = QSA('td.ext button');
    for (var a = 0; a < t.length; a++)
        t[a].onclick = function () {
            egrant(this.closest('tr'), this.value);
        };

    t = QSA('span[t1]');
    for (var a = 0; a < t.length; a++)
        t[a].textContent = unix2ui(parseInt(t[a].getAttribute('t1')));
})();

J_GR = 2;
