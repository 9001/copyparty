function QSA(x) {
    return document.querySelectorAll(x);
}
var LINUX = /Linux/.test(navigator.userAgent),
    MACOS = /[^a-z]mac ?os/i.test(navigator.userAgent),
    WINDOWS = /Windows/.test(navigator.userAgent);


var oa = QSA('pre');
for (var a = 0; a < oa.length; a++) {
    var html = oa[a].innerHTML,
        nd = /^ +/.exec(html)[0].length,
        rd = new RegExp('(^|\r?\n) {' + nd + '}', 'g');

    oa[a].innerHTML = html.replace(rd, '$1').replace(/[ \r\n]+$/, '').replace(/\r?\n/g, '<br />');
}


oa = QSA('.ossel a');
for (var a = 0; a < oa.length; a++)
    oa[a].onclick = esetos;

function esetos(e) {
    ev(e);
    setos(((e && e.target) || (window.event && window.event.srcElement)).id.slice(1));
}

function setos(os) {
    var oa = QSA('.os');
    for (var a = 0; a < oa.length; a++)
        oa[a].style.display = 'none';

    var oa = QSA('.' + os);
    for (var a = 0; a < oa.length; a++)
        oa[a].style.display = '';

    oa = QSA('.ossel a');
    for (var a = 0; a < oa.length; a++)
        clmod(oa[a], 'g', oa[a].id.slice(1) == os);
}

setos(WINDOWS ? 'win' : LINUX ? 'lin' : MACOS ? 'mac' : 'idk');
