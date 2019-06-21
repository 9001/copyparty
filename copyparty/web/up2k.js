// error handler for mobile devices
function hcroak(msg) {
    document.body.innerHTML = msg;
    window.onerror = undefined;
    throw 'fatal_err';
}
function croak(msg) {
    document.body.textContent = msg;
    window.onerror = undefined;
    throw msg;
}
function esc(txt) {
    return txt.replace(/[&"<>]/g, function (c) {
        return {
            '&': '&amp;',
            '"': '&quot;',
            '<': '&lt;',
            '>': '&gt;'
        }[c];
    });
}
window.onerror = function (msg, url, lineNo, columnNo, error) {
    window.onerror = undefined;
    var html = ['<h1>you hit a bug!</h1><p>please screenshot this error and send me a copy arigathanks gozaimuch (ed/irc.rizon.net or ed#2644)</p><p>',
        esc(String(msg)), '</p><p>', esc(url + ' @' + lineNo + ':' + columnNo), '</p>'];

    if (error) {
        var find = ['desc', 'stack', 'trace'];
        for (var a = 0; a < find.length; a++)
            if (String(error[find[a]]) !== 'undefined')
                html.push('<h2>' + find[a] + '</h2>' +
                    esc(String(error[find[a]])).replace(/\n/g, '<br />\n'));
    }
    document.body.style.fontSize = '0.8em';
    hcroak(html.join('\n'));
};

function ebi(id) {
    return document.getElementById(id);
}

ebi('up2k').style.display = 'block';
ebi('bup').style.display = 'none';

ebi('u2tgl').onclick = function (e) {
    e.preventDefault();
    ebi('u2tgl').style.display = 'none';
    ebi('u2body').style.display = 'block';
}

ebi('u2nope').onclick = function (e) {
    e.preventDefault();
    ebi('up2k').style.display = 'none';
    ebi('bup').style.display = 'block';
}
