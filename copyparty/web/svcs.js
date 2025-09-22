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


var un, un0, pw, pw0, unpw, up0;
function setpw(e) {
    ev(e);
    if (!ebi('un0'))
        return askpw();

    modal.prompt('username:', '', function (v) {
        if (!v)
            return;

        un = v;
        un0 = ebi('un0').innerHTML;
        var oa = QSA('b');

        for (var a = 0; a < oa.length; a++)
            if (oa[a].innerHTML == un0)
                oa[a].textContent = un;
        
        askpw();
    });
}
function askpw() {
    modal.prompt('password:', '', function (v) {
        if (!v)
            return;

        pw = v;
        pw0 = ebi('pw0').innerHTML;
        var oa = QSA('b');

        for (var a = 0; a < oa.length; a++)
            if (oa[a].innerHTML == pw0)
                oa[a].textContent = pw;

        if (un) {
            unpw = un ? (un+':'+pw) : pw;
            up0 = ebi('up0').innerHTML;
            for (var a = 0; a < oa.length; a++)
                if (oa[a].innerHTML == up0)
                    oa[a].textContent = unpw;
        }
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
