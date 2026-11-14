"use strict";

// fork-only: the "grant" button beside "share" in the file browser; see FORK.md.
// Loaded with --js-browser /.cpr/w/grantbtn.js so upstream's browser.js stays as it is.
// Shown for the current folder, or for exactly one selected folder, when grants are on.

(function () {
    var bshr = ebi('fshr');
    if (!bshr || !window.fileman || acct == '*')
        return;

    var top = null,  // the grants folder; null until ?grants=rcpts says grants are on
        btn = mknod('a', 'fgrant');

    btn.href = '#';
    btn.setAttribute('tt', 'grant this folder to another account; they find it in their own file tree');
    btn.innerHTML = '🤝<span>grant</span>';
    btn.className = 'hide';
    bshr.parentNode.insertBefore(btn, bshr.nextSibling);
    btn.onclick = function (e) {
        ev(e);
        var vp = src_folder();
        if (vp !== null)
            rcpts(function (jo) { dialog(vp, jo); });
    };

    // the folder the button acts on: the selected one, or the current one;
    // null if a file or several things are selected. Without the reverse
    // proxy's prefix (SR), as the server and the recipient see the path
    function src_folder() {
        var sel = msel.getsel();
        if (sel.length > 1)
            return null;
        var vp = sel.length ? noq_href(ebi(sel[0].id)) : get_evpath();
        vp = uricom_dec(vp);
        if (!vp.endsWith('/'))
            return null;
        return SR && vp.indexOf(SR + '/') === 0 ? vp.slice(SR.length) : vp;
    }

    // the text of an error reply: the server html-escapes it inside <pre>
    function errtxt(txt) {
        txt = hunpre(txt).replace(/\s*URL:[^\n]*\s*$/, '');
        try {
            return new DOMParser().parseFromString(txt, 'text/html').documentElement.textContent;
        }
        catch (ex) {
            return txt;
        }
    }


    function update() {
        var vp = src_folder(),
            hide = top === null || in_shr || vp === null ||
                !has(perms, 'read') || (src_folder() || '').indexOf('/' + top + '/') === 0;

        clmod(btn, 'en', !hide);
        clmod(btn, 'hide', hide);
        clmod(ebi('wfm'), 'act', QS('#wfm a.en:not(.hide)'));
    }

    var render = fileman.render;
    fileman.render = function () {
        var ret = render.apply(this, arguments);
        update();
        return ret;
    };

    function rcpts(cb) {
        var xhr = new XHR();
        xhr.open('GET', SR + '/?grants=rcpts', true);
        xhr.onload = xhr.onerror = function () {
            if (this.status !== 200)
                return cb(null, this);
            try {
                cb(JSON.parse(this.responseText));
            }
            catch (ex) {
                cb(null, this);
            }
        };
        xhr.send();
    }

    // 400 "grants are disabled" (or any other error) leaves the button hidden
    rcpts(function (jo) {
        if (!jo)
            return;
        top = jo.top;
        update();
    });

    function opts(names) {
        var ret = [];
        for (var a = 0; a < names.length; a++)
            ret.push('<option value="' + esc(names[a]) + '">' + esc(names[a]) + '</option>');
        return ret.join('');
    }

    function dialog(vp, jo) {
        if (!jo)
            return modal.alert('<h6>could not load the recipient list</h6>');

        if (!jo.accounts.length && !jo.groups.length)
            return modal.alert('there is nobody to grant this folder to; ask the admin to add accounts or groups');

        var shui = ebi('shui');
        if (!shui) {
            shui = mknod('div', 'shui');
            document.body.appendChild(shui);
        }
        shui.style.display = 'block';

        var name = vp.replace(/\/+$/, '').split('/').pop(),  // "" at /
            pick = '';

        if (jo.accounts.length)
            pick += '<optgroup label="accounts">' + opts(jo.accounts) + '</optgroup>';
        if (jo.groups.length)
            pick += '<optgroup label="groups">' + opts(jo.groups) + '</optgroup>';

        shui.innerHTML = [
            '<div>',
            '<table>',
            '<tr><td colspan="2">',
            '<button id="gr_abrt">cancel</button>',
            '<button id="gr_apply">create grant</button>',
            '</td></tr>',
            '<tr><td>folder</td><td><input type="text" id="gr_vp" ' + NOAC + ' readonly /></td></tr>',
            '<tr><td>recipient</td><td><select id="gr_rcpt">' + pick + '</select></td></tr>',
            '<tr><td>rights</td><td><select id="gr_pr">',
            '<option value="r">read-only</option>',
            '<option value="rw">read + upload</option>',
            '</select></td></tr>',
            '<tr><td>appears as</td><td><input type="text" id="gr_name" ' + NOAC + ' placeholder="a folder name" tt="the folder name the recipient sees, under /' + esc(jo.top) + '/' + esc(acct) + '/" /></td></tr>',
            '<tr><td>expires</td><td class="exs">',
            '<input type="text" id="gr_exp" ' + NOAC + ' placeholder="never" /> ',
            '<select id="gr_exu">',
            '<option value="60">hours</option>',
            '<option value="1440" selected>days</option>',
            '<option value="10080">weeks</option>',
            '</select>',
            '</td></tr>',
            '</table></div>'
        ].join('\n');

        var gr_vp = ebi('gr_vp'),
            gr_name = ebi('gr_name'),
            gr_exp = ebi('gr_exp'),
            gr_apply = ebi('gr_apply');

        gr_vp.value = vp;
        gr_name.value = name;
        tt.att(shui);

        function close() {
            if (shui.parentNode)
                shui.parentNode.removeChild(shui);
        }
        ebi('gr_abrt').onclick = close;

        gr_name.onkeydown = gr_exp.onkeydown = function (e) {
            var kc = (e.key || e.code) + '';
            if (kc.endsWith('Enter'))
                gr_apply.click();
        };

        gr_apply.onclick = function () {
            var exp = gr_exp.value.trim();
            if (exp && !/^[0-9]+(\.[0-9]+)?$/.test(exp))
                return toast.err(9, 'the expiry is a number, or empty for never');

            var mins = exp ? Math.round(parseFloat(exp) * parseInt(ebi('gr_exu').value)) : 0;
            if (exp && !mins)
                return toast.err(9, 'that expiry is too short; leave it empty for never');

            var body = {
                "vp": gr_vp.value,
                "rcpt": ebi('gr_rcpt').value,
                "name": gr_name.value,
                "perms": ebi('gr_pr').value == 'rw' ? ['read', 'write'] : ['read'],
                "exp": mins
            };

            shui.style.display = 'none';
            toast.inf(30, 'creating grant...');

            var xhr = new XHR();
            xhr.open('POST', SR + '/?grant', true);
            xhr.setRequestHeader('Content-Type', 'text/plain');
            xhr.onload = xhr.onerror = function () {
                toast.hide();
                if (this.status !== 201) {
                    // the server's refusal, word for word, minus the URL line every error ends with
                    shui.style.display = 'block';
                    return modal.alert('<h6>grant refused</h6>' + esc(errtxt(this.responseText || 'no reply from the server')));
                }
                var jr;
                try {
                    jr = JSON.parse(this.responseText);
                }
                catch (ex) {
                    jr = {"vp": '/' + top + '/' + acct + '/' + body.name + '/'};
                }
                close();
                modal.alert(
                    'granted <code>' + esc(vp) + '</code> to <b>' + esc(body.rcpt) + '</b> (' +
                    (body.perms.length > 1 ? 'read + upload' : 'read-only') + ', expires ' +
                    (mins ? unix2ui(Date.now() / 1000 + mins * 60) : 'never') + ')<br />' +
                    'they find it at <code>' + esc(jr.vp) + '</code><br /><br />' +
                    '<a href="' + SR + '/?grants">manage your grants</a>');
            };
            xhr.send(JSON.stringify(body));
        };

        setTimeout(ebi('gr_rcpt').focus.bind(ebi('gr_rcpt')), 1);
    }
})();
