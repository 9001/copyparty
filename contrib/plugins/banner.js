(function() {

// usage: copy this to '.banner.js' in your webroot,
// and run copyparty with the following arguments:
// --js-browser /.banner.js  --js-other /.banner.js



// had to pick the most chuuni one as the default
var bannertext = '' +
'<h3>You are accessing a U.S. Government (USG) Information System (IS) that is provided for USG-authorized use only.</h3>' +
'<p>By using this IS (which includes any device attached to this IS), you consent to the following conditions:</p>' +
'<ul>' +
'<li>The USG routinely intercepts and monitors communications on this IS for purposes including, but not limited to, penetration testing, COMSEC monitoring, network operations and defense, personnel misconduct (PM), law enforcement (LE), and counterintelligence (CI) investigations.</li>' +
'<li>At any time, the USG may inspect and seize data stored on this IS.</li>' +
'<li>Communications using, or data stored on, this IS are not private, are subject to routine monitoring, interception, and search, and may be disclosed or used for any USG-authorized purpose.</li>' +
'<li>This IS includes security measures (e.g., authentication and access controls) to protect USG interests -- not for your personal benefit or privacy.</li>' +
'<li>Notwithstanding the above, using this IS does not constitute consent to PM, LE or CI investigative searching or monitoring of the content of privileged communications, or work product, related to personal representation or services by attorneys, psychotherapists, or clergy, and their assistants. Such communications and work product are private and confidential. See User Agreement for details.</li>' +
'</ul>';



// fancy div to insert into pages
function bannerdiv(border) {
    var ret = mknod('div', null, bannertext);
    if (border)
        ret.setAttribute("style", "border:1em solid var(--fg); border-width:.3em 0; margin:3em 0");
    return ret;
}



// keep all of these false and then selectively enable them in the if-blocks below
var show_msgbox = false,
    login_top = false,
    top = false,
    bottom = false,
    top_bordered = false,
    bottom_bordered = false;

if (QS("h1#cc") && QS("a#k")) {
    // this is the controlpanel
    // (you probably want to keep just one of these enabled)
    show_msgbox = true;
    login_top = true;
    bottom = true;
}
else if (ebi("swin") && ebi("smac")) {
    // this is the connect-page, same deal here
    show_msgbox = true;
    top_bordered = true;
    bottom_bordered = true;
}
else if (ebi("op_cfg") || ebi("div#mw") ) {
    // we're running in the main filebrowser (op_cfg) or markdown-viewer/editor (div#mw),
    // fragile pages which break if you do something too fancy
    show_msgbox = true;
}



// shows a fullscreen messagebox; works on all pages
if (show_msgbox) {
    var now = Math.floor(Date.now() / 1000),
        last_shown = sread("bannerts") || 0;

    // 60 * 60 * 17 = 17 hour cooldown
    if (now - last_shown > 60 * 60 * 17) {
        swrite("bannerts", now);
        modal.confirm(bannertext, null, function () {
            location = 'https://this-page-intentionally-left-blank.org/';
        });
    }
}

// show a message on the page footer; only works on the connect-page
if (top || top_bordered) {
    var dst = ebi('wrap');
    dst.insertBefore(bannerdiv(top_bordered), dst.firstChild);
}

// show a message on the page footer; only works on the controlpanel and connect-page
if (bottom || bottom_bordered) {
    ebi('wrap').appendChild(bannerdiv(bottom_bordered));
}

// show a message on the top of the page; only works on the controlpanel
if (login_top) {
    var dst = QS('h1');
    dst.parentNode.insertBefore(bannerdiv(false), dst);
}

})();
