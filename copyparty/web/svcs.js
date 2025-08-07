var oa = QSA('pre');
for (var a = 0; a < oa.length; a++) {
    var html = oa[a].innerHTML,
        nd = /^ +/.exec(html)[0].length,
        rd = new RegExp('(^|\r?\n) {' + nd + '}', 'g');

    oa[a].innerHTML = html.replace(rd, '$1').replace(/[ \r\n]+$/, '').replace(/\r?\n/g, '<br />');
}

function add_dls() {
    oa = QSA('pre.dl');
    for (var a = 0; a < oa.length; a++) {
        var an = 'ta' + a,
            o = ebi(an) || mknod('a', an, 'download');

        oa[a].setAttribute('id', 'tx' + a);
        oa[a].parentNode.insertBefore(o, oa[a]);
        o.setAttribute('download', oa[a].getAttribute('name'));
        o.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(oa[a].innerText));
        clmod(o, 'txa', 1);
    }
}
add_dls();


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


var pw = '';
function setpw(e) {
    ev(e);
    modal.prompt('password:', '', function (v) {
        if (!v)
            return;

        pw = v;
        var pw0 = ebi('pw0').innerHTML,
            oa = QSA('b');
    
        for (var a = 0; a < oa.length; a++)
            if (oa[a].innerHTML == pw0)
                oa[a].textContent = v;

        add_dls();
    });
}
if (ebi('setpw'))
    ebi('setpw').onclick = setpw;


ebi('qr').onclick = function () {
    var url = ('' + location).split('?')[0];
    if (pw)
        url += '?pw=' + pw;
    var txt = esc(url) + '<img class="b64" width="100" height="100" src="' + addq(url, 'qr') + '" />';
    modal.alert(txt);
};
