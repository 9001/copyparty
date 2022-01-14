"use strict";

function dbg(msg) {
	ebi('path').innerHTML = msg;
}


// toolbar
ebi('ops').innerHTML = (
	'<a href="#" data-dest="" tt="close submenu">--</a>\n' +
	'<a href="#" data-perm="read" data-dep="idx" data-dest="search" tt="search for files by attributes, path/name, music tags, or any combination of those$N$N&lt;code&gt;foo bar&lt;/code&gt; = must contain both foo and bar,$N&lt;code&gt;foo -bar&lt;/code&gt; = must contain foo but not bar,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = start with yana and be an opus file$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = contain exactly «try unite»">🔎</a>\n' +
	(have_del && have_unpost ? '<a href="#" data-dest="unpost" data-dep="idx" tt="unpost: delete your recent uploads">🧯</a>\n' : '') +
	'<a href="#" data-dest="up2k">🚀</a>\n' +
	'<a href="#" data-perm="write" data-dest="bup" tt="bup: basic uploader, even supports netscape 4.0">🎈</a>\n' +
	'<a href="#" data-perm="write" data-dest="mkdir" tt="mkdir: create a new directory">📂</a>\n' +
	'<a href="#" data-perm="read write" data-dest="new_md" tt="new-md: create a new markdown document">📝</a>\n' +
	'<a href="#" data-perm="write" data-dest="msg" tt="msg: send a message to the server log">📟</a>\n' +
	'<a href="#" data-dest="player" tt="media player options">🎺</a>\n' +
	'<a href="#" data-dest="cfg" tt="configuration options">⚙️</a>\n' +
	'<div id="opdesc"></div>'
);


// media player
ebi('widget').innerHTML = (
	'<div id="wtoggle">' +
	'<span id="wfm"><a' +
	' href="#" id="fren" tt="rename selected item$NHotkey: F2">✎<span>name</span></a><a' +
	' href="#" id="fdel" tt="delete selected items$NHotkey: ctrl-K">⌫<span>del.</span></a><a' +
	' href="#" id="fcut" tt="cut selected items &lt;small&gt;(then paste somewhere else)&lt;/small&gt;$NHotkey: ctrl-X">✂<span>cut</span></a><a' +
	' href="#" id="fpst" tt="paste a previously cut/copied selection$NHotkey: ctrl-V">📋<span>paste</span></a>' +
	'</span><span id="wzip"><a' +
	' href="#" id="selall" tt="select all files$NHotkey: ctrl-A (when file focused)">sel.<br />all</a><a' +
	' href="#" id="selinv" tt="invert selection">sel.<br />inv.</a><a' +
	' href="#" id="selzip" tt="download selection as archive">zip</a>' +
	'</span><span id="wnp"><a' +
	' href="#" id="npirc" tt="copy irc-formatted track info">📋<span>irc</span></a><a' +
	' href="#" id="nptxt" tt="copy plaintext track info">📋<span>txt</span></a>' +
	'</span><a' +
	'	href="#" id="wtgrid" tt="toggle grid/list view$NHotkey: G">田</a><a' +
	'	href="#" id="wtico">♫</a>' +
	'</div>' +
	'<div id="widgeti">' +
	'	<div id="pctl"><a href="#" id="bprev" tt="previous track$NHotkey: J">⏮</a><a href="#" id="bplay" tt="play/pause$NHotkey: P">▶</a><a href="#" id="bnext" tt="next track$NHotkey: L">⏭</a></div>' +
	'	<canvas id="pvol" width="288" height="38"></canvas>' +
	'	<canvas id="barpos"></canvas>' +
	'	<canvas id="barbuf"></canvas>' +
	'</div>'
);


// up2k ui
ebi('op_up2k').innerHTML = (
	'<form id="u2form" method="post" enctype="multipart/form-data" onsubmit="return false;"></form>\n' +

	'<table id="u2conf">\n' +
	'	<tr>\n' +
	'		<td class="c"><br />parallel uploads:</td>\n' +
	'		<td class="c" rowspan="2">\n' +
	'			<input type="checkbox" id="multitask" />\n' +
	'			<label for="multitask" tt="continue hashing other files while uploading">🏃</label>\n' +
	'		</td>\n' +
	'		<td class="c" rowspan="2">\n' +
	'			<input type="checkbox" id="ask_up" />\n' +
	'			<label for="ask_up" tt="ask for confirmation before upload starts">💭</label>\n' +
	'		</td>\n' +
	'		<td class="c" data-perm="read" data-dep="idx" rowspan="2">\n' +
	'			<input type="checkbox" id="fsearch" />\n' +
	'			<label for="fsearch" tt="don\'t actually upload, instead check if the files already $N exist on the server (will scan all folders you can read)">🔎</label>\n' +
	'		</td>\n' +
	'		<td data-perm="read" rowspan="2" id="u2btn_cw"></td>\n' +
	'		<td data-perm="read" rowspan="2" id="u2c3w"></td>\n' +
	'	</tr>\n' +
	'	<tr>\n' +
	'		<td class="c">\n' +
	'			<a href="#" class="b" id="nthread_sub">&ndash;</a><input\n' +
	'				class="txtbox" id="nthread" value="2" tt="pause uploads by setting it to 0"/><a\n' +
	'				href="#" class="b" id="nthread_add">+</a><br />&nbsp;\n' +
	'		</td>\n' +
	'	</tr>\n' +
	'</table>\n' +

	'<div id="u2notbtn"></div>\n' +

	'<div id="u2btn_ct">\n' +
	'	<div id="u2btn">\n' +
	'		<span id="u2bm"></span><br />\n' +
	'		drag/drop files<br />\n' +
	'		and folders here<br />\n' +
	'		(or click me)\n' +
	'	</div>\n' +
	'</div>\n' +

	'<div id="u2c3t">\n' +

	'<div id="u2etaw"><div id="u2etas"><div class="o">\n' +
	'	hash: <span id="u2etah" tt="average &lt;em&gt;hashing&lt;/em&gt; speed, and estimated time until finish">(no uploads are queued yet)</span><br />\n' +
	'	send: <span id="u2etau" tt="average &lt;em&gt;upload&lt;/em&gt; speed and estimated time until finish">(no uploads are queued yet)</span><br />\n' +
	'	</div><span class="o">done: </span><span id="u2etat" tt="average &lt;em&gt;total&lt;/em&gt; speed and estimated time until finish">(no uploads are queued yet)</span>\n' +
	'</div></div>\n' +

	'<div id="u2cards">\n' +
	'	<a href="#" act="ok" tt="completed successfully">ok <span>0</span></a><a\n' +
	'	href="#" act="ng" tt="failed / rejected / not-found">ng <span>0</span></a><a\n' +
	'	href="#" act="done" tt="ok and ng combined">done <span>0</span></a><a\n' +
	'	href="#" act="bz" tt="hashing or uploading" class="act">busy <span>0</span></a><a\n' +
	'	href="#" act="q" tt="idle, pending">que <span>0</span></a>\n' +
	'</div>\n' +

	'</div>\n' +

	'<div id="u2tabw"><table id="u2tab">\n' +
	'	<thead>\n' +
	'		<tr>\n' +
	'			<td>filename</td>\n' +
	'			<td>status</td>\n' +
	'			<td>progress</td>\n' +
	'		</tr>\n' +
	'	</thead>\n' +
	'	<tbody></tbody>\n' +
	'</table></div>\n' +

	'<p id="u2flagblock"><b>the files were added to the queue</b><br />however there is a busy up2k in another browser tab,<br />so waiting for that to finish first</p>\n' +
	'<p id="u2foot"></p>\n' +
	'<p id="u2footfoot" data-perm="write">( you can use the <a href="#" id="u2nope">basic uploader</a> if you don\'t need lastmod timestamps, resumable uploads, or progress bars )</p>'
);


(function () {
	var o = mknod('div');
	o.innerHTML = (
		'<div id="drops">\n' +
		'	<div class="dropdesc" id="up_zd"><div>🚀 Upload<br /><span></span><div>🚀</div><div>🚀</div></div></div>\n' +
		'	<div class="dropdesc" id="srch_zd"><div>🔎 Search<br /><span></span><div>🔎</div><div>🔎</div></div></div>\n' +
		'	<div class="dropzone" id="up_dz" v="up_zd"></div>\n' +
		'	<div class="dropzone" id="srch_dz" v="srch_zd"></div>\n' +
		'</div>'
	);
	document.body.appendChild(o);
})();


// config panel
ebi('op_cfg').innerHTML = (
	'<div>\n' +
	'	<h3>switches</h3>\n' +
	'	<div>\n' +
	'		<a id="tooltips" class="tgl btn" href="#" tt="◔ ◡ ◔">ℹ️ tooltips</a>\n' +
	'		<a id="lightmode" class="tgl btn" href="#">☀️ lightmode</a>\n' +
	'		<a id="griden" class="tgl btn" href="#" tt="toggle icons or list-view$NHotkey: G">田 the grid</a>\n' +
	'		<a id="thumbs" class="tgl btn" href="#" tt="in icon view, toggle icons or thumbnails$NHotkey: T">🖼️ thumbs</a>\n' +
	'		<a id="dotfiles" class="tgl btn" href="#" tt="show hidden files (if server permits)">dotfiles</a>\n' +
	'		<a id="ireadme" class="tgl btn" href="#" tt="show README.md in folder listings">📜 readme</a>\n' +
	'		<a id="spafiles" class="tgl btn" href="#" tt="speedboost when not using the navpane;$Nturn it off if things arent loading somehow">spa</a>\n' +
	'	</div>\n' +
	'</div>\n' +
	(have_zip ? (
		'<div><h3>folder download</h3><div id="arc_fmt"></div></div>\n'
	) : '') +
	'<div>\n' +
	'	<h3>up2k switches</h3>\n' +
	'	<div>\n' +
	'		<a id="u2turbo" class="tgl btn ttb" href="#" tt="the yolo button, you probably DO NOT want to enable this:$N$Nuse this if you were uploading a huge amount of files and had to restart for some reason, and want to continue the upload ASAP$N$Nthis replaces the hash-check with a simple <em>&quot;does this have the same filesize on the server?&quot;</em> so if the file contents are different it will NOT be uploaded$N$Nyou should turn this off when the upload is done, and then &quot;upload&quot; the same files again to let the client verify them">turbo</a>\n' +
	'		<a id="u2tdate" class="tgl btn ttb" href="#" tt="has no effect unless the turbo button is enabled$N$Nreduces the yolo factor by a tiny amount; checks whether the file timestamps on the server matches yours$N$Nshould <em>theoretically</em> catch most unfinished/corrupted uploads, but is not a substitute for doing a verification pass with turbo disabled afterwards">date-chk</a>\n' +
	'		<a id="flag_en" class="tgl btn" href="#" tt="ensure only one tab is uploading at a time $N (other tabs must have this enabled too)">💤</a>\n' +
	'		</td>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div>\n' +
	'	<h3>favicon <span id="ico1">🎉</span></h3>\n' +
	'	<div>\n' +
	'		<input type="text" id="icot" style="width:1.3em" value="" tt="favicon text (blank and refresh to disable)" />' +
	'		<input type="text" id="icof" style="width:2em" value="" tt="foreground color" />' +
	'		<input type="text" id="icob" style="width:2em" value="" tt="background color" />' +
	'		</td>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div><h3>key notation</h3><div id="key_notation"></div></div>\n' +
	'<div class="fill"><h3>hidden columns</h3><div id="hcols"></div></div>'
);


// navpane
ebi('tree').innerHTML = (
	'<div id="treeh">\n' +
	'	<a href="#" id="detree" tt="show breadcrumbs$NHotkey: B">🍞...</a>\n' +
	'	<a href="#" class="btn" step="2" id="twobytwo" tt="Hotkey: D">+</a>\n' +
	'	<a href="#" class="btn" step="-2" id="twig" tt="Hotkey: A">&ndash;</a>\n' +
	'	<a href="#" class="btn" id="visdir" tt="scroll to selected folder">🎯</a>\n' +
	'	<a href="#" class="tgl btn" id="filetree" tt="toggle folder-tree / textfiles$NHotkey: V">📃</a>\n' +
	'	<a href="#" class="tgl btn" id="parpane" tt="show parent folders in a docked pane at the top">📌</a>\n' +
	'	<a href="#" class="tgl btn" id="dyntree" tt="autogrow as tree expands">a</a>\n' +
	'	<a href="#" class="tgl btn" id="wraptree" tt="word wrap">↵</a>\n' +
	'	<a href="#" class="tgl btn" id="hovertree" tt="reveal overflowing lines on hover$N( breaks scrolling unless mouse $N&nbsp; cursor is in the left gutter )">👀</a>\n' +
	'</div>\n' +
	'<ul id="docul"></ul>\n' +
	'<ul class="ntree" id="treepar"></ul>\n' +
	'<ul class="ntree" id="treeul"></ul>\n' +
	'<div id="thx_ff">&nbsp;</div>'
);


(function () {
	var ops = QSA('#ops>a');
	for (var a = 0; a < ops.length; a++) {
		ops[a].onclick = opclick;
		var v = ops[a].getAttribute('data-dest');
		if (v)
			ops[a].href = '#v=' + v;
	}
})();


function opclick(e) {
	var dest = this.getAttribute('data-dest');
	if (QS('#op_' + dest + '.act'))
		dest = '';

	swrite('opmode', dest || null);
	if (ctrl(e))
		return;

	ev(e);
	goto(dest);

	var input = QS('.opview.act input:not([type="hidden"])')
	if (input && !is_touch) {
		tt.skip = true;
		input.focus();
	}
}


function goto(dest) {
	var obj = QSA('.opview.act');
	for (var a = obj.length - 1; a >= 0; a--)
		clmod(obj[a], 'act');

	obj = QSA('#ops>a');
	for (var a = obj.length - 1; a >= 0; a--)
		clmod(obj[a], 'act');

	if (dest) {
		var lnk = QS('#ops>a[data-dest=' + dest + ']'),
			nps = lnk.getAttribute('data-perm');

		nps = nps && nps.length ? nps.split(' ') : [];

		if (perms.length)
			for (var a = 0; a < nps.length; a++)
				if (!has(perms, nps[a]))
					return;

		if (!has(perms, 'read') && !has(perms, 'write') && (dest == 'up2k'))
			return;

		clmod(ebi('op_' + dest), 'act', 1);
		clmod(lnk, 'act', 1);

		var fn = window['goto_' + dest];
		if (fn)
			fn();
	}

	if (window['treectl'])
		treectl.onscroll();
}


var have_webp = sread('have_webp');
(function () {
	if (have_webp !== null)
		return;

	var img = new Image();
	img.onload = function () {
		have_webp = img.width > 0 && img.height > 0;
		swrite('have_webp', 'ya');
	};
	img.onerror = function () {
		have_webp = false;
		swrite('have_webp', '');
	};
	img.src = "data:image/webp;base64,UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA==";
})();


function set_files_html(html) {
	var files = ebi('files');
	try {
		files.innerHTML = html;
		return files;
	}
	catch (e) {
		var par = files.parentNode;
		par.removeChild(files);
		files = mknod('div');
		files.innerHTML = '<table id="files">' + html + '</table>';
		par.insertBefore(files.childNodes[0], ebi('epi'));
		files = ebi('files');
		return files;
	}
}


var ACtx = window.AudioContext || window.webkitAudioContext,
	actx = ACtx && new ACtx(),
	hash0 = location.hash,
	mp;


var mpl = (function () {
	var have_mctl = 'mediaSession' in navigator && window.MediaMetadata;

	ebi('op_player').innerHTML = (
		'<div><h3>switches</h3><div>' +
		'<a href="#" class="tgl btn" id="au_preload" tt="start loading the next song near the end for gapless playback">preload</a>' +
		'<a href="#" class="tgl btn" id="au_fullpre" tt="try to preload the entire song;$N✔️ enable on <b>unreliable</b> connections,$N❌ <b>disable</b> on slow connections probably">full</a>' +
		'<a href="#" class="tgl btn" id="au_npclip" tt="show buttons for clipboarding the currently playing song">/np clip</a>' +
		'<a href="#" class="tgl btn" id="au_os_ctl" tt="os integration (media hotkeys / osd)">os-ctl</a>' +
		'<a href="#" class="tgl btn" id="au_os_seek" tt="allow seeking through os integration">seek</a>' +
		'<a href="#" class="tgl btn" id="au_osd_cv" tt="show album cover in osd">art</a>' +
		'</div></div>' +

		'<div><h3>playback mode</h3><div id="pb_mode">' +
		'<a href="#" class="tgl btn" tt="loop the open folder">🔁 loop</a>' +
		'<a href="#" class="tgl btn" tt="load the next folder and continue">📂 next</a>' +
		'</div></div>' +

		(have_acode ? (
			'<div><h3>transcode</h3><div>' +
			'<a href="#" id="ac_flac" class="tgl btn" tt="convert flac to opus">flac</a>' +
			'<a href="#" id="ac_aac" class="tgl btn" tt="convert aac/m4a to opus">aac</a>' +
			'<a href="#" id="ac_oth" class="tgl btn" tt="convert all others (not mp3) to opus">oth</a>' +
			'</div></div>'
		) : '') +

		'<div><h3>tint</h3><div>' +
		'<input type="text" id="pb_tint" style="width:2.4em" value="0" tt="background level (0-100) on the seekbar$Nto make buffering less distracting" />' +
		'</div></div>' +

		'<div><h3>audio equalizer</h3><div id="audio_eq"></div></div>');

	var r = {
		"pb_mode": (sread('pb_mode') || 'loop').split('-')[0],
		"os_ctl": bcfg_get('au_os_ctl', have_mctl) && have_mctl,
	};
	bcfg_bind(r, 'preload', 'au_preload', true);
	bcfg_bind(r, 'fullpre', 'au_fullpre', false);
	bcfg_bind(r, 'os_seek', 'au_os_seek', !IPHONE, announce);
	bcfg_bind(r, 'osd_cv', 'au_osd_cv', true, announce);
	bcfg_bind(r, 'clip', 'au_npclip', false, function (v) {
		clmod(ebi('wtoggle'), 'np', v && mp.au);
	});
	bcfg_bind(r, 'ac_flac', 'ac_flac', true);
	bcfg_bind(r, 'ac_aac', 'ac_aac', false);
	bcfg_bind(r, 'ac_oth', 'ac_oth', true, reload_mp);
	if (!have_acode)
		r.ac_flac = r.ac_aac = r.ac_oth = false;

	if (IPHONE) {
		ebi('au_fullpre').style.display = 'none';
		r.fullpre = false;
	}

	ebi('au_os_ctl').onclick = function (e) {
		ev(e);
		r.os_ctl = !r.os_ctl && have_mctl;
		bcfg_set('au_os_ctl', r.os_ctl);
		if (!have_mctl)
			toast.err(5, 'need firefox 82+ or chrome 73+ or iOS 15+');
	};

	function draw_pb_mode() {
		var btns = QSA('#pb_mode>a');
		for (var a = 0, aa = btns.length; a < aa; a++) {
			clmod(btns[a], 'on', btns[a].textContent.indexOf(r.pb_mode) != -1);
			btns[a].onclick = set_pb_mode;
		}
	}
	draw_pb_mode();

	function set_pb_mode(e) {
		ev(e);
		r.pb_mode = this.textContent.split(' ').pop();
		swrite('pb_mode', r.pb_mode);
		draw_pb_mode();
	}

	function set_tint() {
		var tint = icfg_get('pb_tint', 0);
		if (!tint)
			ebi('barbuf').style.removeProperty('background');
		else
			ebi('barbuf').style.background = 'rgba(126,163,75,' + (tint / 100.0) + ')';
	}
	ebi('pb_tint').oninput = function (e) {
		swrite('pb_tint', this.value);
		set_tint();
	};
	set_tint();

	r.acode = function (url) {
		var c = true;
		if (!have_acode)
			c = false;
		else if (/\.flac$/i.exec(url))
			c = r.ac_flac;
		else if (/\.(aac|m4a)$/i.exec(url))
			c = r.ac_aac;
		else if (/\.opus$/i.exec(url) && !can_ogg)
			c = true;
		else if (re_au_native.exec(url))
			c = false;

		if (!c)
			return url;

		return url + (url.indexOf('?') < 0 ? '?' : '&') + 'th=' + (can_ogg ? 'opus' : 'caf');
	};

	r.pp = function () {
		if (!r.os_ctl)
			return;

		navigator.mediaSession.playbackState = mp.au && !mp.au.paused ? "playing" : "paused";
	};

	function announce() {
		if (!r.os_ctl)
			return;

		var np = get_np()[0],
			fns = np.file.split(' - '),
			artist = (np.circle && np.circle != np.artist ? np.circle + ' // ' : '') + (np.artist || (fns.length > 1 ? fns[0] : '')),
			tags = {
				title: np.title || fns.pop()
			};

		if (artist)
			tags.artist = artist;

		if (np.album)
			tags.album = np.album;

		if (r.osd_cv) {
			var files = QSA("#files tr>td:nth-child(2)>a[id]"),
				cover = null;

			for (var a = 0, aa = files.length; a < aa; a++) {
				if (/^(cover|folder)\.(jpe?g|png|gif)$/.test(files[a].textContent)) {
					cover = noq_href(files[a]);
					break;
				}
			}

			if (cover) {
				cover += (cover.indexOf('?') === -1 ? '?' : '&') + 'th=j';

				var pwd = get_pwd();
				if (pwd)
					cover += '&pw=' + uricom_enc(pwd);

				tags.artwork = [{ "src": cover, type: "image/jpeg" }];
			}
		}

		navigator.mediaSession.metadata = new MediaMetadata(tags);
		navigator.mediaSession.setActionHandler('play', playpause);
		navigator.mediaSession.setActionHandler('pause', playpause);
		navigator.mediaSession.setActionHandler('seekbackward', r.os_seek ? function () { seek_au_rel(-10); } : null);
		navigator.mediaSession.setActionHandler('seekforward', r.os_seek ? function () { seek_au_rel(10); } : null);
		navigator.mediaSession.setActionHandler('previoustrack', prev_song);
		navigator.mediaSession.setActionHandler('nexttrack', next_song);
		r.pp();
	}
	r.announce = announce;

	r.stop = function () {
		if (!r.os_ctl || !navigator.mediaSession.metadata)
			return;

		navigator.mediaSession.metadata = null;
		navigator.mediaSession.playbackState = "paused";
	};

	r.unbuffer = function (url) {
		if (mp.au2 && (!url || mp.au2.rsrc == url)) {
			mp.au2.src = mp.au2.rsrc = '';
			mp.au2.load();
		}
		if (!url)
			mpl.preload_url = null;
	}

	return r;
})();


var can_ogg = true;
try {
	can_ogg = new Audio().canPlayType('audio/ogg; codecs=opus') === 'probably';

	if (document.documentMode)
		can_ogg = true;  // ie8-11
}
catch (ex) { }


var re_au_native = can_ogg ? /\.(opus|ogg|m4a|aac|mp3|wav|flac)$/i :
	have_acode ? /\.(opus|m4a|aac|mp3|wav|flac)$/i : /\.(m4a|aac|mp3|wav|flac)$/i,
	re_au_all = /\.(aac|m4a|ogg|opus|flac|alac|mp3|mp2|ac3|dts|wma|ra|wav|aif|aiff|au|alaw|ulaw|mulaw|amr|gsm|ape|tak|tta|wv)$/i;


// extract songs + add play column
function MPlayer() {
	var r = this;
	r.id = Date.now();
	r.au = null;
	r.au = null;
	r.au2 = null;
	r.tracks = {};
	r.order = [];

	var re_audio = have_acode && mpl.ac_oth ? re_au_all : re_au_native,
		trs = QSA('#files tbody tr');

	for (var a = 0, aa = trs.length; a < aa; a++) {
		var tds = trs[a].getElementsByTagName('td'),
			link = tds[1].getElementsByTagName('a');

		link = link[link.length - 1];
		var url = noq_href(link),
			m = re_audio.exec(url);

		if (m) {
			var tid = link.getAttribute('id');
			r.order.push(tid);
			r.tracks[tid] = url;
			tds[0].innerHTML = '<a id="a' + tid + '" href="#a' + tid + '" class="play">play</a></td>';
			ebi('a' + tid).onclick = ev_play;
			clmod(trs[a], 'au', 1);
		}
	}

	r.vol = clamp(fcfg_get('vol', IPHONE ? 1 : 0.5), 0, 1);

	r.expvol = function (v) {
		return 0.5 * v + 0.5 * v * v;
	};

	r.setvol = function (vol) {
		r.vol = clamp(vol, 0, 1);
		swrite('vol', vol);
		r.stopfade(true);

		if (r.au)
			r.au.volume = r.expvol(r.vol);
	};

	r.read_order = function () {
		var order = [],
			links = QSA('#files>tbody>tr>td:nth-child(1)>a');

		for (var a = 0, aa = links.length; a < aa; a++) {
			var tid = links[a].getAttribute('id');
			if (!tid || tid.indexOf('af-') !== 0)
				continue;

			order.push(tid.slice(1));
		}
		r.order = order;
	};

	r.fdir = 0;
	r.fvol = -1;
	r.ftid = -1;
	r.ftimer = null;
	r.fade_in = function () {
		r.fvol = 0;
		r.fdir = 0.025;
		if (r.au) {
			r.ftid = r.au.tid;
			r.au.play();
			mpl.pp();
			fader();
		}
	};
	r.fade_out = function () {
		r.fvol = r.vol;
		r.fdir = -0.05;
		r.ftid = r.au.tid;
		fader();
	};
	r.stopfade = function (hard) {
		clearTimeout(r.ftimer);
		if (hard)
			r.ftid = -1;
	}
	function fader() {
		r.stopfade();
		if (!r.au || r.au.tid !== r.ftid)
			return;

		var done = true;
		r.fvol += r.fdir;
		if (r.fvol < 0) {
			r.fvol = 0;
			r.au.pause();
			mpl.pp();
		}
		else if (r.fvol > r.vol)
			r.fvol = r.vol;
		else
			done = false;

		r.au.volume = r.expvol(r.fvol);
		if (!done)
			setTimeout(fader, 10);
	}

	r.preload = function (url, full) {
		url = mpl.acode(url);
		url += (url.indexOf('?') < 0 ? '?' : '&') + 'cache=987';
		mpl.preload_url = full ? url : null;
		var t0 = Date.now();
		if (full)
			return fetch(url).then(function (x) {
				var rd = x.body.getReader(), n = 0;
				function spd() {
					return humansize(n / ((Date.now() + 1 - t0) / 1000)) + '/s';
				}
				function drop(x) {
					if (x && x.done)
						return console.log('xhr-preload finished, ' + spd());

					if (x && x.value && x.value.length)
						n += x.value.length;

					if (mpl.preload_url !== url || n >= 128 * 1024 * 1024) {
						console.log('xhr-preload aborted at ' + Math.floor(n / 1024) + ' KiB, ' + spd() + ' for ' + url);
						return rd.cancel();
					}

					return rd.read().then(drop);
				}
				drop();
			});

		mp.au2.preload = "auto";
		mp.au2.src = mp.au2.rsrc = url;
	};
}


function ft2dict(tr) {
	var th = ebi('files').tHead.rows[0].cells,
		rv = [],
		rh = [],
		ra = [],
		rt = {};

	for (var a = 1, aa = th.length; a < aa; a++) {
		var tv = tr.cells[a].textContent,
			tk = a == 1 ? 'file' : th[a].getAttribute('name').split('/').pop(),
			vis = th[a].className.indexOf('min') === -1;

		if (!tv)
			continue;

		(vis ? rv : rh).push(tk);
		ra.push(tk);
		rt[tk] = tv;
	}
	return [rt, rv, rh, ra];
}


function get_np() {
	var tr = QS('#files tr.play');
	return ft2dict(tr);
};


// toggle player widget
var widget = (function () {
	var r = {},
		widget = ebi('widget'),
		wtico = ebi('wtico'),
		nptxt = ebi('nptxt'),
		npirc = ebi('npirc'),
		touchmode = false,
		was_paused = true;

	r.open = function () {
		return r.set(true);
	};
	r.close = function () {
		return r.set(false);
	};
	r.set = function (is_open) {
		if (r.is_open == is_open)
			return false;

		clmod(document.documentElement, 'np_open', is_open);
		widget.className = is_open ? 'open' : '';
		bcfg_set('au_open', r.is_open = is_open);
		return true;
	};
	r.toggle = function (e) {
		r.open() || r.close();
		ev(e);
		return false;
	};
	r.paused = function (paused) {
		if (was_paused != paused) {
			was_paused = paused;
			ebi('bplay').innerHTML = paused ? '▶' : '⏸';
		}
	};
	wtico.onclick = function (e) {
		if (!touchmode)
			r.toggle(e);

		return false;
	};
	npirc.onclick = nptxt.onclick = function (e) {
		ev(e);
		var irc = this.getAttribute('id') == 'npirc',
			ck = irc ? '06' : '',
			cv = irc ? '07' : '',
			m = ck + 'np: ',
			npr = get_np(),
			npk = npr[1],
			np = npr[0];

		for (var a = 0; a < npk.length; a++)
			m += (npk[a] == 'file' ? '' : npk[a]) + '(' + cv + np[npk[a]] + ck + ') // ';

		m += '[' + cv + s2ms(mp.au.currentTime) + ck + '/' + cv + s2ms(mp.au.duration) + ck + ']';

		var o = mknod('input');
		o.style.cssText = 'position:fixed;top:45%;left:48%;padding:1em;z-index:9';
		o.value = m;
		document.body.appendChild(o);
		o.focus();
		o.select();
		document.execCommand("copy");
		o.value = 'copied to clipboard ';
		setTimeout(function () {
			document.body.removeChild(o);
		}, 500);
	};
	r.set(sread('au_open') == 1);
	setTimeout(function () {
		clmod(ebi('widget'), 'anim', 1);
	}, 10);
	return r;
})();


function canvas_cfg(can) {
	var r = {},
		b = can.getBoundingClientRect(),
		mul = window.devicePixelRatio || 1;

	r.w = b.width;
	r.h = b.height;
	can.width = r.w * mul;
	can.height = r.h * mul;

	r.can = can;
	r.ctx = can.getContext('2d');
	r.ctx.scale(mul, mul);
	return r;
}


function glossy_grad(can, h, s, l) {
	var g = can.ctx.createLinearGradient(0, 0, 0, can.h),
		p = [0, 0.49, 0.50, 1];

	for (var a = 0; a < p.length; a++)
		g.addColorStop(p[a], 'hsl(' + h + ',' + s[a] + '%,' + l[a] + '%)');

	return g;
}


// buffer/position bar
var pbar = (function () {
	var r = {},
		gradh = -1,
		grad;

	r.onresize = function () {
		r.buf = canvas_cfg(ebi('barbuf'));
		r.pos = canvas_cfg(ebi('barpos'));
		r.drawbuf();
		r.drawpos();
	}

	r.drawbuf = function () {
		var bc = r.buf,
			bctx = bc.ctx;

		bctx.clearRect(0, 0, bc.w, bc.h);

		if (!mp || !mp.au)
			return;

		var sm = bc.w * 1.0 / mp.au.duration,
			gk = bc.h + '' + light;

		if (gradh != gk) {
			gradh = gk;
			grad = glossy_grad(bc, 85, [35, 40, 37, 35], light ? [45, 56, 50, 45] : [42, 51, 47, 42]);
		}
		bctx.fillStyle = grad;
		for (var a = 0; a < mp.au.buffered.length; a++) {
			var x1 = sm * mp.au.buffered.start(a),
				x2 = sm * mp.au.buffered.end(a);

			bctx.fillRect(x1, 0, x2 - x1, bc.h);
		}
	};

	r.drawpos = function () {
		var bc = r.buf,
			pc = r.pos,
			pctx = pc.ctx,
			apos, adur;

		pctx.clearRect(0, 0, pc.w, pc.h);

		if (!mp || !mp.au || isNaN(adur = mp.au.duration) || isNaN(apos = mp.au.currentTime) || apos < 0 || adur < apos)
			return;  // not-init || unsupp-codec

		var sm = bc.w * 1.0 / adur;

		pctx.fillStyle = light ? 'rgba(0,64,0,0.15)' : 'rgba(204,255,128,0.15)';
		for (var p = 1, mins = adur / 10; p <= mins; p++)
			pctx.fillRect(Math.floor(sm * p * 10), 0, 2, pc.h);

		pctx.fillStyle = light ? 'rgba(0,64,0,0.5)' : 'rgba(192,255,96,0.5)';
		for (var p = 1, mins = adur / 60; p <= mins; p++)
			pctx.fillRect(Math.floor(sm * p * 60), 0, 2, pc.h);

		pctx.font = '.5em sans-serif';
		pctx.fillStyle = light ? 'rgba(0,64,0,0.9)' : 'rgba(192,255,96,1)';
		for (var p = 1, mins = adur / 60; p <= mins; p++) {
			pctx.fillText(p, Math.floor(sm * p * 60 + 3), pc.h / 3);
		}

		pctx.fillStyle = light ? 'rgba(0,0,0,1)' : 'rgba(255,255,255,1)';
		for (var p = 1, mins = adur / 600; p <= mins; p++)
			pctx.fillRect(Math.floor(sm * p * 600), 0, 2, pc.h);

		var w = 8,
			x = sm * apos;

		pctx.fillStyle = '#573'; pctx.fillRect((x - w / 2) - 1, 0, w + 2, pc.h);
		pctx.fillStyle = '#dfc'; pctx.fillRect((x - w / 2), 0, 8, pc.h);

		pctx.lineWidth = 2.5;
		pctx.fillStyle = '#fff';
		pctx.strokeStyle = 'rgba(24,56,0,0.4)';
		pctx.font = '1em sans-serif';

		var m = pctx.measureText.bind(pctx),
			t1 = s2ms(adur),
			t2 = s2ms(apos),
			yt = pc.h / 3 * 2.1,
			xt1 = pc.w - (m(t1).width + 12),
			xt2 = x < pc.w / 2 ? (x + 12) : (Math.min(pc.w - m(t1 + ":88").width, x - 12) - m(t2).width);

		pctx.strokeText(t1, xt1 + 1, yt + 1);
		pctx.strokeText(t2, xt2 + 1, yt + 1);
		pctx.strokeText(t1, xt1, yt);
		pctx.strokeText(t2, xt2, yt);
		pctx.fillText(t1, xt1, yt);
		pctx.fillText(t2, xt2, yt);
	};

	window.addEventListener('resize', r.onresize);
	r.onresize();
	return r;
})();


// volume bar
var vbar = (function () {
	var r = {},
		gradh = -1,
		can, ctx, w, h, grad1, grad2;

	r.onresize = function () {
		r.can = canvas_cfg(ebi('pvol'));
		can = r.can.can;
		ctx = r.can.ctx;
		w = r.can.w;
		h = r.can.h;
		r.draw();
	}

	r.draw = function () {
		if (!mp)
			return;

		var gh = h + '' + light;
		if (gradh != gh) {
			gradh = gh;
			grad1 = glossy_grad(r.can, 50, light ? [50, 55, 52, 48] : [45, 52, 47, 43], light ? [54, 60, 52, 47] : [42, 51, 47, 42]);
			grad2 = glossy_grad(r.can, 205, [10, 15, 13, 10], [16, 20, 18, 16]);
		}
		ctx.fillStyle = grad2; ctx.fillRect(0, 0, w, h);
		ctx.fillStyle = grad1; ctx.fillRect(0, 0, w * mp.vol, h);
	};
	window.addEventListener('resize', r.onresize);
	r.onresize();

	var rect;
	function mousedown(e) {
		rect = can.getBoundingClientRect();
		mousemove(e);
	}
	function mousemove(e) {
		if (e.changedTouches && e.changedTouches.length > 0) {
			e = e.changedTouches[0];
		}
		else if (e.buttons === 0) {
			can.onmousemove = null;
			return;
		}

		var x = e.clientX - rect.left,
			mul = x * 1.0 / rect.width;

		if (mul > 0.98)
			mul = 1;

		mp.setvol(mul);
		r.draw();
	}
	can.onmousedown = function (e) {
		if (e.button !== 0)
			return;

		can.onmousemove = mousemove;
		mousedown(e);
	};
	can.onmouseup = function (e) {
		if (e.button === 0)
			can.onmousemove = null;
	};
	if (is_touch) {
		can.ontouchstart = mousedown;
		can.ontouchmove = mousemove;
	}
	return r;
})();


function seek_au_mul(mul) {
	if (mp.au)
		seek_au_sec(mp.au.duration * mul);
}

function seek_au_rel(sec) {
	if (mp.au)
		seek_au_sec(mp.au.currentTime + sec);
}

function seek_au_sec(seek) {
	if (!mp.au)
		return;

	console.log('seek: ' + seek);
	if (!isFinite(seek))
		return;

	mp.au.currentTime = seek;

	if (mp.au.paused)
		mp.fade_in();

	mpui.progress_updater();
}


function song_skip(n) {
	var tid = null;
	if (mp.au)
		tid = mp.au.tid;

	if (tid !== null)
		play(mp.order.indexOf(tid) + n);
	else
		play(mp.order[n == -1 ? mp.order.length - 1 : 0]);
}
function next_song(e) {
	ev(e);
	return song_skip(1);
}
function prev_song(e) {
	ev(e);

	if (mp.au && !mp.au.paused && mp.au.currentTime > 3)
		return seek_au_sec(0);

	return song_skip(-1);
}


function playpause(e) {
	// must be event-chain
	ev(e);
	if (mp.au) {
		if (mp.au.paused)
			mp.fade_in();
		else
			mp.fade_out();

		mpui.progress_updater();
	}
	else
		play(0, true);

	mpl.pp();
};


// hook up the widget buttons
(function () {
	ebi('bplay').onclick = playpause;
	ebi('bprev').onclick = prev_song;
	ebi('bnext').onclick = next_song;

	var bar = ebi('barpos');

	bar.onclick = function (e) {
		if (!mp.au) {
			play(0, true);
			return mp.fade_in();
		}

		var rect = pbar.buf.can.getBoundingClientRect(),
			x = e.clientX - rect.left;

		seek_au_mul(x * 1.0 / rect.width);
	};

	if (!is_touch)
		bar.onwheel = function (e) {
			var dist = Math.sign(e.deltaY) * 10;
			if (Math.abs(e.deltaY) < 30 && !e.deltaMode)
				dist = e.deltaY;

			if (!dist || !mp.au)
				return true;

			seek_au_rel(dist);
			ev(e);
		};
})();


// periodic tasks
var mpui = (function () {
	var r = {},
		nth = 0,
		preloaded = null,
		fpreloaded = null;

	r.progress_updater = function () {
		timer.add(updater_impl, true);
	};

	function updater_impl() {
		if (!mp.au) {
			widget.paused(true);
			timer.rm(updater_impl);
			return;
		}

		// indicate playback state in ui
		widget.paused(mp.au.paused);

		if (++nth > 69) {
			// android-chrome breaks aspect ratio with unannounced viewport changes
			nth = 0;
			if (is_touch) {
				nth = 1;
				pbar.onresize();
				vbar.onresize();
			}
		}
		else {
			// draw current position in song
			if (!mp.au.paused)
				pbar.drawpos();

			// occasionally draw buffered regions
			if (++nth % 5 == 0)
				pbar.drawbuf();
		}

		// preload next song
		if (mpl.preload && preloaded != mp.au.rsrc) {
			var pos = mp.au.currentTime,
				len = mp.au.duration,
				rem = pos > 1 ? len - pos : 999,
				full = null;

			if (rem < (mpl.fullpre ? 7 : 20)) {
				preloaded = fpreloaded = mp.au.rsrc;
				full = false;
			}
			else if (rem < 40 && mpl.fullpre && fpreloaded != mp.au.rsrc) {
				fpreloaded = mp.au.rsrc;
				full = true;
			}

			if (full !== null)
				try {
					mp.preload(mp.tracks[mp.order[mp.order.indexOf(mp.au.tid) + 1]], full);
				}
				catch (ex) {
					console.log("preload failed", ex);
				}
		}

		if (mp.au.paused)
			timer.rm(updater_impl);
	}
	return r;
})();


// event from play button next to a file in the list
function ev_play(e) {
	ev(e);

	var fade = !mp.au || mp.au.paused;
	play(this.getAttribute('id').slice(1), true);
	if (fade)
		mp.fade_in();

	return false;
}


var audio_eq = (function () {
	var r = {
		"en": false,
		"bands": [31.25, 62.5, 125, 250, 500, 1000, 2000, 4000, 8000, 16000],
		"gains": [4, 3, 2, 1, 0, 0, 1, 2, 3, 4],
		"filters": [],
		"amp": 0,
		"last_au": null,
		"acst": {}
	};

	if (!actx)
		ebi('audio_eq').parentNode.style.display = 'none';

	// some browsers have insane high-frequency boost
	// (or rather the actual problem is Q but close enough)
	r.cali = (function () {
		try {
			var fi = actx.createBiquadFilter(),
				freqs = new Float32Array(1),
				mag = new Float32Array(1),
				phase = new Float32Array(1);

			freqs[0] = 14000;
			fi.type = 'peaking';
			fi.frequency.value = 18000;
			fi.Q.value = 0.8;
			fi.gain.value = 1;
			fi.getFrequencyResponse(freqs, mag, phase);

			return mag[0];  // 1.0407 good, 1.0563 bad
		}
		catch (ex) {
			return 0;
		}
	})();
	console.log('eq cali: ' + r.cali);

	var e1 = r.cali < 1.05;

	var cfg = [ // hz, q, g
		[31.25 * 0.88, 0, 1.4],  // shelf
		[31.25 * 1.04, 0.7, 0.96],  // peak
		[62.5, 0.7, 1],
		[125, 0.8, 1],
		[250, 0.9, 1.03],
		[500, 0.9, 1.1],
		[1000, 0.9, 1.1],
		[2000, 0.9, 1.105],
		[4000, 0.88, 1.05],
		[8000 * 1.006, 0.73, e1 ? 1.24 : 1.2],
		[16000 * 0.89, 0.7, e1 ? 1.26 : 1.2],  // peak
		[16000 * 1.13, 0.82, e1 ? 1.09 : 0.75],  // peak
		[16000 * 1.205, 0, e1 ? 1.9 : 1.85]  // shelf
	];

	try {
		r.amp = fcfg_get('au_eq_amp', r.amp);
		var gains = jread('au_eq_gain', r.gains);
		if (r.gains.length == gains.length)
			r.gains = gains;
	}
	catch (ex) { }

	r.draw = function () {
		jwrite('au_eq_gain', r.gains);
		swrite('au_eq_amp', r.amp);

		var txt = QSA('input.eq_gain');
		for (var a = 0; a < r.bands.length; a++)
			txt[a].value = r.gains[a];

		QS('input.eq_gain[band="amp"]').value = r.amp;
	};

	r.stop = function () {
		if (r.filters.length)
			for (var a = 0; a < r.filters.length; a++)
				r.filters[a].disconnect();

		r.filters = [];

		if (!mp)
			return;

		if (mp.acs)
			mp.acs.disconnect();

		mp.acs = null;
	};

	r.apply = function () {
		r.draw();

		if (!actx)
			bcfg_set('au_eq', false);

		if (!actx || !mp.au || (!r.en && !mp.acs))
			return;

		r.stop();
		mp.au.id = mp.au.id || Date.now();
		mp.acs = r.acst[mp.au.id] = r.acst[mp.au.id] || actx.createMediaElementSource(mp.au);

		if (!r.en) {
			mp.acs.connect(actx.destination);
			return;
		}

		var min, max;
		min = max = r.gains[0];
		for (var a = 1; a < r.gains.length; a++) {
			min = Math.min(min, r.gains[a]);
			max = Math.max(max, r.gains[a]);
		}

		var gains = [];
		for (var a = 0; a < r.gains.length; a++)
			gains.push(r.gains[a] - max);

		var t = gains[gains.length - 1];
		gains.push(t);
		gains.push(t);
		gains.unshift(gains[0]);

		for (var a = 0; a < cfg.length && min != max; a++) {
			var fi = actx.createBiquadFilter();
			fi.frequency.value = cfg[a][0];
			fi.gain.value = cfg[a][2] * gains[a];
			fi.Q.value = cfg[a][1];
			fi.type = a == 0 ? 'lowshelf' : a == cfg.length - 1 ? 'highshelf' : 'peaking';
			r.filters.push(fi);
		}

		// pregain, keep first in chain
		fi = actx.createGain();
		fi.gain.value = r.amp + 0.94;  // +.137 dB measured; now -.25 dB and almost bitperfect
		r.filters.push(fi);

		for (var a = r.filters.length - 1; a >= 0; a--)
			r.filters[a].connect(a > 0 ? r.filters[a - 1] : actx.destination);

		mp.acs.connect(r.filters[r.filters.length - 1]);
	}

	function eq_step(e) {
		ev(e);
		var band = parseInt(this.getAttribute('band')),
			step = parseFloat(this.getAttribute('step'));

		if (isNaN(band))
			r.amp = Math.round((r.amp + step * 0.2) * 100) / 100;
		else
			r.gains[band] += step;

		r.apply();
	}

	function adj_band(that, step) {
		var err = false;
		try {
			var band = parseInt(that.getAttribute('band')),
				vs = that.value,
				v = parseFloat(vs);

			if (isNaN(v) || v + '' != vs)
				throw new Error('inval band');

			if (isNaN(band))
				r.amp = Math.round((v + step * 0.2) * 100) / 100;
			else
				r.gains[band] = v + step;

			r.apply();
		}
		catch (ex) {
			err = true;
		}
		clmod(that, 'err', err);
	}

	function eq_mod(e) {
		ev(e);
		adj_band(this, 0);
	}

	function eq_keydown(e) {
		var step = e.key == 'ArrowUp' ? 0.25 : e.key == 'ArrowDown' ? -0.25 : 0;
		if (step != 0)
			adj_band(this, step);
	}

	var html = ['<table><tr><td rowspan="4">',
		'<a id="au_eq" class="tgl btn" href="#" tt="enables the equalizer and gain control;$Nboost 0 = unmodified 100% volume$N$Nenabling the equalizer makes gapless albums fully gapless, so leave it on with all the values at zero if you care about that">enable</a></td>'],
		h2 = [], h3 = [], h4 = [];

	var vs = [];
	for (var a = 0; a < r.bands.length; a++) {
		var hz = r.bands[a];
		if (hz >= 1000)
			hz = (hz / 1000) + 'k';

		hz = (hz + '').split('.')[0];
		vs.push([a, hz, r.gains[a]]);
	}
	vs.push(["amp", "boost", r.amp]);

	for (var a = 0; a < vs.length; a++) {
		var b = vs[a][0];
		html.push('<td><a href="#" class="eq_step" step="0.5" band="' + b + '">+</a></td>');
		h2.push('<td>' + vs[a][1] + '</td>');
		h4.push('<td><a href="#" class="eq_step" step="-0.5" band="' + b + '">&ndash;</a></td>');
		h3.push('<td><input type="text" class="eq_gain" band="' + b + '" value="' + vs[a][2] + '" /></td>');
	}
	html = html.join('\n') + '</tr><tr>';
	html += h2.join('\n') + '</tr><tr>';
	html += h3.join('\n') + '</tr><tr>';
	html += h4.join('\n') + '</tr><table>';
	ebi('audio_eq').innerHTML = html;

	var stp = QSA('a.eq_step');
	for (var a = 0, aa = stp.length; a < aa; a++)
		stp[a].onclick = eq_step;

	var txt = QSA('input.eq_gain');
	for (var a = 0; a < txt.length; a++) {
		txt[a].oninput = eq_mod;
		txt[a].onkeydown = eq_keydown;
	}

	bcfg_bind(r, 'en', 'au_eq', false, r.apply);

	r.draw();
	return r;
})();


// plays the tid'th audio file on the page
function play(tid, is_ev, seek, call_depth) {
	if (mp.order.length == 0)
		return console.log('no audio found wait what');

	if (crashed)
		return;

	mpl.preload_url = null;
	mp.stopfade(true);

	var tn = tid;
	if ((tn + '').indexOf('f-') === 0) {
		tn = mp.order.indexOf(tn);
		if (tn < 0)
			return;
	}

	if (tn >= mp.order.length) {
		if (mpl.pb_mode == 'loop') {
			tn = 0;
		}
		else if (mpl.pb_mode == 'next') {
			treectl.ls_cb = next_song;
			return tree_neigh(1);
		}
	}

	if (tn < 0) {
		if (mpl.pb_mode == 'loop') {
			tn = mp.order.length - 1;
		}
		else if (mpl.pb_mode == 'next') {
			treectl.ls_cb = prev_song;
			return tree_neigh(-1);
		}
	}

	tid = mp.order[tn];

	if (mp.au) {
		mp.au.pause();
		clmod(ebi('a' + mp.au.tid), 'act');
	}
	else {
		mp.au = new Audio();
		mp.au2 = new Audio();
		mp.au.onerror = evau_error;
		mp.au.onprogress = pbar.drawpos;
		mp.au.onended = next_song;
		widget.open();
	}

	var url = mpl.acode(mp.tracks[tid]);
	url += (url.indexOf('?') < 0 ? '?' : '&') + 'cache=987';

	if (mp.au.rsrc == url)
		mp.au.currentTime = 0;
	else if (mp.au2.rsrc == url) {
		var t = mp.au;
		mp.au = mp.au2;
		mp.au2 = t;
		t.onerror = t.onprogress = t.onended = null;
		mp.au.onerror = evau_error;
		mp.au.onprogress = pbar.drawpos;
		mp.au.onended = next_song;
	}
	else
		mp.au.src = mp.au.rsrc = url;

	audio_eq.apply();

	setTimeout(function () {
		mpl.unbuffer(url);
	}, 500);

	mp.au.tid = tid;
	mp.au.volume = mp.expvol(mp.vol);
	var trs = QSA('#files tr.play');
	for (var a = 0, aa = trs.length; a < aa; a++)
		clmod(trs[a], 'play');

	var oid = 'a' + tid;
	clmod(ebi(oid), 'act', 1);
	clmod(ebi(oid).closest('tr'), 'play', 1);
	clmod(ebi('wtoggle'), 'np', mpl.clip);
	if (window.thegrid)
		thegrid.loadsel();

	try {
		mp.au.play();
		if (mp.au.paused)
			autoplay_blocked(seek);
		else if (seek) {
			seek_au_sec(seek);
		}

		if (!seek && !ebi('unsearch')) {
			var o = ebi(oid);
			o.setAttribute('id', 'thx_js');
			sethash(oid);
			o.setAttribute('id', oid);
		}

		mpui.progress_updater();
		pbar.onresize();
		vbar.onresize();
		mpl.announce();
		return true;
	}
	catch (ex) {
		toast.err(0, esc('playback failed: ' + basenames(ex)));
	}
	clmod(ebi(oid), 'act');
	setTimeout(next_song, 5000);
}


// event from the audio object if something breaks
function evau_error(e) {
	var err = '',
		eplaya = (e && e.target) || (window.event && window.event.srcElement);

	switch (eplaya.error.code) {
		case eplaya.error.MEDIA_ERR_ABORTED:
			err = "You aborted the playback attempt (how tho)";
			break;
		case eplaya.error.MEDIA_ERR_NETWORK:
			err = "Your internet connection is wonky";
			break;
		case eplaya.error.MEDIA_ERR_DECODE:
			err = "This file is supposedly corrupted??";
			break;
		case eplaya.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
			err = "Your browser does not understand this audio format";
			if (/\.(aac|m4a)(\?|$)/i.exec(eplaya.rsrc) && !mpl.ac_aac) {
				try {
					ebi('ac_aac').click();
					QS('a.play.act').click();
					toast.warn(10, 'your browser cannot play aac/m4a files;\ntranscoding to opus is now enabled');
					return;
				}
				catch (ex) { }
			}
			break;
		default:
			err = 'Unknown Errol';
			break;
	}
	if (eplaya.error.message)
		err += '\n\n' + eplaya.error.message;

	err += '\n\nFile: «' + uricom_dec(eplaya.src.split('/').pop())[0] + '»';

	toast.warn(15, esc(basenames(err)));
}


// show ui to manually start playback of a linked song
function autoplay_blocked(seek) {
	var tid = mp.au.tid,
		fn = mp.tracks[tid].split(/\//).pop();

	fn = uricom_dec(fn.replace(/\+/g, ' '))[0];

	modal.confirm('<h6>play this audio file?</h6>\n«' + esc(fn) + '»', function () {
		// chrome 91 may permanently taint on a failed play()
		// depending on win10 settings or something? idk
		mp.au = null;

		play(tid, true, seek);
		mp.fade_in();
	}, function () {
		sethash('');
		clmod(QS('#files tr.play'), 'play');
		return reload_mp();
	});
}


function eval_hash() {
	var v = hash0;
	hash0 = null;
	if (!v)
		return;

	if (v.indexOf('#af-') === 0) {
		var id = v.slice(2).split('&');
		if (id[0].length < 10)
			return;

		if (id.length == 1)
			return play(id[0]);

		var m = /^[Tt=0]*([0-9]+[Mm:])?0*([0-9]+)[Ss]?$/.exec(id[1]);
		if (!m)
			return play(id[0]);

		return play(id[0], false, parseInt(m[1] || 0) * 60 + parseInt(m[2] || 0));
	}

	if (v.indexOf('#q=') === 0) {
		goto('search');
		var i = ebi('q_raw');
		i.value = uricom_dec(v.slice(3))[0];
		return i.oninput();
	}

	if (v.indexOf('#v=') === 0) {
		goto(v.slice(3));
		return;
	}
}


(function () {
	var d = mknod('div');
	d.setAttribute('id', 'acc_info');
	document.body.insertBefore(d, ebi('ops'));
})();


function sortfiles(nodes) {
	if (!nodes.length)
		return nodes;

	var sopts = jread('fsort', [["href", 1, ""]]);

	try {
		var is_srch = false;
		if (nodes[0]['rp']) {
			is_srch = true;
			for (var b = 0, bb = nodes.length; b < bb; b++)
				nodes[b].ext = nodes[b].rp.split('.').pop();
			for (var b = 0; b < sopts.length; b++)
				if (sopts[b][0] == 'href')
					sopts[b][0] = 'rp';
		}
		for (var a = sopts.length - 1; a >= 0; a--) {
			var name = sopts[a][0], rev = sopts[a][1], typ = sopts[a][2];
			if (!name)
				continue;

			if (name == 'ts')
				typ = 'int';

			if (name.indexOf('tags/') === 0) {
				name = name.slice(5);
				for (var b = 0, bb = nodes.length; b < bb; b++)
					nodes[b]._sv = nodes[b].tags[name];
			}
			else {
				for (var b = 0, bb = nodes.length; b < bb; b++) {
					var v = nodes[b][name];

					if ((v + '').indexOf('<a ') === 0)
						v = v.split('>')[1];
					else if (name == "href" && v) {
						if (v.split('?')[0].slice(-1) == '/')
							v = '\t' + v;

						v = uricom_dec(v)[0];
					}

					nodes[b]._sv = v;
				}
			}

			var onodes = nodes.map(function (x) { return x; });
			nodes.sort(function (n1, n2) {
				var v1 = n1._sv,
					v2 = n2._sv;

				if (v1 === undefined) {
					if (v2 === undefined) {
						return onodes.indexOf(n1) - onodes.indexOf(n2);
					}
					return -1 * rev;
				}
				if (v2 === undefined) return 1 * rev;

				var ret = rev * (typ == 'int' ? (v1 - v2) : (v1.localeCompare(v2)));
				if (ret === 0)
					ret = onodes.indexOf(n1) - onodes.indexOf(n2);

				return ret;
			});
		}
		for (var b = 0, bb = nodes.length; b < bb; b++) {
			delete nodes[b]._sv;
			if (is_srch)
				delete nodes[b].ext;
		}
	}
	catch (ex) {
		console.log("failed to apply sort config: " + ex);
		console.log("resetting fsort " + sread('fsort'))
		localStorage.removeItem('fsort');
	}
	return nodes;
}


function fmt_ren(re, md, fmt) {
	var ptr = 0;
	function dive(stop_ch) {
		var ret = '', ng = 0;
		while (ptr < fmt.length) {
			var dbg = fmt.slice(ptr),
				ch = fmt[ptr++];

			if (ch == '\\') {
				ret += fmt[ptr++];
				continue;
			}

			if (ch == ')' || ch == ']' || ch == stop_ch)
				return [ng, ret];

			if (ch == '[') {
				var r2 = dive();
				if (r2[0] == 0)
					ret += r2[1];
			}
			else if (ch == '(') {
				var end = fmt.indexOf(')', ptr);
				if (end < 0)
					throw 'the ( was never closed: ' + fmt.slice(0, ptr);

				var arg = fmt.slice(ptr, end), v = null;
				ptr = end + 1;

				if (arg != parseInt(arg))
					v = md[arg];
				else {
					arg = parseInt(arg);
					if (arg >= re.length)
						throw 'matching group ' + arg + ' exceeds ' + (re.length - 0);

					v = re[arg];
				}

				if (v !== null && v !== undefined)
					ret += v;
				else
					ng++;
			}
			else if (ch == '$') {
				ch = fmt[ptr++];
				var end = fmt.indexOf('(', ptr);
				if (end < 0)
					throw 'no function name after the $ here: ' + fmt.slice(0, ptr);

				var fun = fmt.slice(ptr - 1, end);
				ptr = end + 1;

				if (fun == "lpad") {
					var str = dive(',')[1];
					var len = dive(',')[1];
					var chr = dive()[1];
					if (!len || !chr)
						throw 'invalid arguments to ' + fun;

					if (!str.length)
						ng += 1;

					while (str.length < len)
						str = chr + str;

					ret += str;
				}
				else if (fun == "rpad") {
					var str = dive(',')[1];
					var len = dive(',')[1];
					var chr = dive()[1];
					if (!len || !chr)
						throw 'invalid arguments to ' + fun;

					if (!str.length)
						ng += 1;

					while (str.length < len)
						str += chr;

					ret += str;
				}
				else throw 'function not implemented: "' + fun + '"';
			}
			else ret += ch;
		}
		return [ng, ret];
	}
	try {
		return [true, dive()[1]];
	}
	catch (ex) {
		return [false, ex];
	}
}


var fileman = (function () {
	var bren = ebi('fren'),
		bdel = ebi('fdel'),
		bcut = ebi('fcut'),
		bpst = ebi('fpst'),
		r = {};

	r.clip = null;
	try {
		r.bus = new BroadcastChannel("fileman_bus");
	}
	catch (ex) { }

	r.render = function () {
		if (r.clip === null)
			r.clip = jread('fman_clip', []).slice(1);

		var nsel = msel.getsel().length;
		clmod(bren, 'en', nsel);
		clmod(bdel, 'en', nsel);
		clmod(bcut, 'en', nsel);
		clmod(bpst, 'en', r.clip && r.clip.length);

		clmod(bren, 'hide', !(have_mv && has(perms, 'write') && has(perms, 'move')));
		clmod(bdel, 'hide', !(have_del && has(perms, 'delete')));
		clmod(bcut, 'hide', !(have_mv && has(perms, 'move')));
		clmod(bpst, 'hide', !(have_mv && has(perms, 'write')));
		clmod(ebi('wfm'), 'act', QS('#wfm a.en:not(.hide)'));

		bpst.setAttribute('tt', 'paste ' + r.clip.length + ' items$NHotkey: ctrl-V');
	};

	r.rename = function (e) {
		ev(e);
		if (clgot(bren, 'hide'))
			return toast.err(3, 'cannot rename:\nyou do not have “move” permission in this folder');

		var sel = msel.getsel();
		if (!sel.length)
			return toast.err(3, 'select at least one item to rename');

		var f = [],
			base = vsplit(sel[0].vp)[0],
			mkeys;

		for (var a = 0; a < sel.length; a++) {
			var vp = sel[a].vp;
			if (vp.endsWith('/'))
				vp = vp.slice(0, -1);

			var vsp = vsplit(vp);
			if (base != vsp[0])
				return toast.err(0, esc('bug:\n' + base + '\n' + vsp[0]));

			var vars = ft2dict(ebi(sel[a].id).closest('tr'));
			mkeys = vars[1].concat(vars[2]);

			var md = vars[0];
			for (var k in md) {
				if (!md.hasOwnProperty(k))
					continue;

				md[k.toLowerCase()] = md[k];
				k = k.toLowerCase();

				if (k.startsWith('.'))
					md[k.slice(1)] = md[k];
			}
			md.t = md.ext;
			md.date = md.ts;
			md.size = md.sz;

			f.push({
				"src": vp,
				"ofn": uricom_dec(vsp[1])[0],
				"md": vars[0],
				"ok": true
			});
		}

		var rui = ebi('rui');
		if (!rui) {
			rui = mknod('div');
			rui.setAttribute('id', 'rui');
			document.body.appendChild(rui);
		}

		var html = sel.length > 1 ? ['<div>'] : [
			'<div>',
			'<button class="rn_dec" n="0" tt="may fix some cases of broken filenames">url-decode</button>',
			'//',
			'<button class="rn_reset" n="0" tt="reset modified filenames back to the original ones">↺ reset</button>'
		];

		html = html.concat([
			'<button id="rn_cancel" tt="abort and close this window">❌ cancel</button>',
			'<button id="rn_apply">✅ APPLY RENAME</button>',
			'<a id="rn_adv" class="tgl btn" href="#" tt="batch / metadata / pattern renaming">advanced</a>',
			'<a id="rn_case" class="tgl btn" href="#" tt="case-sensitive regex">case</a>',
			'</div>',
			'<div id="rn_vadv"><table>',
			'<tr><td>regex</td><td><input type="text" id="rn_re" tt="regex search pattern to apply to original filenames; capturing groups can be referenced in the format field below like &lt;code&gt;(1)&lt;/code&gt; and &lt;code&gt;(2)&lt;/code&gt; and so on" /></td></tr>',
			'<tr><td>format</td><td><input type="text" id="rn_fmt" tt="inspired by foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; is replaced by song title,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; skips the first part if artist is blank$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; pads tracknumber to 2 digits" /></td></tr>',
			'<tr><td>preset</td><td><select id="rn_pre"></select>',
			'<button id="rn_pdel">❌ delete</button>',
			'<button id="rn_pnew">💾 save as</button>',
			'</td></tr>',
			'</table></div>'
		]);

		var cheap = f.length > 500;
		if (sel.length == 1)
			html.push(
				'<div><table id="rn_f">\n' +
				'<tr><td>old:</td><td><input type="text" id="rn_old" n="0" readonly /></td></tr>\n' +
				'<tr><td>new:</td><td><input type="text" id="rn_new" n="0" /></td></tr>');
		else {
			html.push(
				'<div><table id="rn_f" class="m">' +
				'<tr><td></td><td>new name</td><td>old name</td></tr>');
			for (var a = 0; a < f.length; a++)
				html.push(
					'<tr><td>' +
					(cheap ? '</td>' :
						'<button class="rn_dec" n="' + a + '">decode</button>' +
						'<button class="rn_reset" n="' + a + '">↺ reset</button></td>') +
					'<td><input type="text" id="rn_new" n="' + a + '" /></td>' +
					'<td><input type="text" id="rn_old" n="' + a + '" readonly /></td></tr>');
		}
		html.push('</table></div>');

		if (sel.length == 1) {
			html.push('<div><p style="margin:.6em 0">tags for the selected file (read-only, just for reference):</p><table>');
			for (var a = 0; a < mkeys.length; a++)
				html.push('<tr><td>' + esc(mkeys[a]) + '</td><td><input type="text" readonly value="' + esc(f[0].md[mkeys[a]]) + '" /></td></tr>');

			html.push('</table></div>');
		}

		rui.innerHTML = html.join('\n');
		for (var a = 0; a < f.length; a++) {
			var k = '[n="' + a + '"]';
			f[a].iold = QS('#rn_old' + k);
			f[a].inew = QS('#rn_new' + k);
			f[a].inew.value = f[a].iold.value = f[a].ofn;

			if (!cheap)
				(function (a) {
					f[a].inew.onkeydown = function (e) {
						rn_ok(a, true);
						if (e.key == 'Enter')
							return rn_apply();
					};
					QS('.rn_dec' + k).onclick = function (e) {
						ev(e);
						f[a].inew.value = uricom_dec(f[a].inew.value)[0];
					};
					QS('.rn_reset' + k).onclick = function (e) {
						ev(e);
						rn_reset(a);
					};
				})(a);
		}
		rn_reset(0);
		tt.att(rui);

		function sadv() {
			ebi('rn_vadv').style.display = ebi('rn_case').style.display = r.adv ? '' : 'none';
		}
		bcfg_bind(r, 'adv', 'rn_adv', false, sadv);
		bcfg_bind(r, 'cs', 'rn_case', false);
		sadv();

		function rn_ok(n, ok) {
			f[n].ok = ok;
			clmod(f[n].inew.closest('tr'), 'err', !ok);
		}

		function rn_reset(n) {
			f[n].inew.value = f[n].iold.value = f[n].ofn;
			f[n].inew.focus();
			f[n].inew.setSelectionRange(0, f[n].inew.value.lastIndexOf('.'), "forward");
		}
		function rn_cancel(e) {
			ev(e);
			rui.parentNode.removeChild(rui);
		}

		ebi('rn_cancel').onclick = rn_cancel;
		ebi('rn_apply').onclick = rn_apply;

		var ire = ebi('rn_re'),
			ifmt = ebi('rn_fmt'),
			ipre = ebi('rn_pre'),
			idel = ebi('rn_pdel'),
			inew = ebi('rn_pnew'),
			defp = '$lpad((tn),2,0). [(artist) - ](title).(ext)';

		var presets = {};
		presets[defp] = ['', defp];
		presets = jread("rn_pre", presets);

		function spresets() {
			var keys = Object.keys(presets), o;
			keys.sort();
			ipre.innerHTML = '<option value=""></option>';
			for (var a = 0; a < keys.length; a++) {
				o = mknod('option');
				o.setAttribute('value', keys[a]);
				o.textContent = keys[a];
				ipre.appendChild(o);
			}
		}
		inew.onclick = function (e) {
			ev(e);
			modal.prompt('provide a name for your new preset', ifmt.value, function (name) {
				if (!name)
					return toast.warn(3, 'aborted');

				presets[name] = [ire.value, ifmt.value];
				jwrite('rn_pre', presets);
				spresets();
				ipre.value = name;
			});
		};
		idel.onclick = function (e) {
			ev(e);
			delete presets[ipre.value];
			jwrite('rn_pre', presets);
			spresets();
		};
		ipre.oninput = function () {
			var cfg = presets[ipre.value];
			if (cfg) {
				ire.value = cfg[0];
				ifmt.value = cfg[1];
			}
			ifmt.oninput();
		};
		spresets();

		ire.onkeydown = ifmt.onkeydown = function (e) {
			if (e.key == 'Escape')
				return rn_cancel();

			if (e.key == 'Enter')
				return rn_apply();
		};

		ire.oninput = ifmt.oninput = function (e) {
			var ptn = ire.value,
				fmt = ifmt.value,
				re = null;

			if (!fmt)
				return;

			try {
				if (ptn)
					re = new RegExp(ptn, r.cs ? 'i' : '');
			}
			catch (ex) {
				return toast.err(5, esc('invalid regex:\n' + ex));
			}
			toast.hide();

			for (var a = 0; a < f.length; a++) {
				var m = re ? re.exec(f[a].ofn) : null,
					ok, txt = '';

				if (re && !m) {
					txt = 'regex did not match';
					ok = false;
				}
				else {
					var ret = fmt_ren(m, f[a].md, fmt);
					ok = ret[0];
					txt = ret[1];
				}
				rn_ok(a, ok);
				f[a].inew.value = (ok ? '' : 'ERROR: ') + txt;
			}
		};

		function rn_apply(e) {
			ev(e);
			while (f.length && (!f[0].ok || f[0].ofn == f[0].inew.value))
				f.shift();

			if (!f.length) {
				toast.ok(2, 'rename OK');
				treectl.goto(get_evpath());
				return rn_cancel();
			}

			toast.inf(0, esc('renaming ' + f.length + ' items\n\n' + f[0].ofn));
			var dst = base + uricom_enc(f[0].inew.value, false);

			function rename_cb() {
				if (this.readyState != XMLHttpRequest.DONE)
					return;

				if (this.status !== 200) {
					var msg = this.responseText;
					toast.err(9, 'rename failed:\n' + msg);
					return;
				}

				f.shift().inew.value = '( OK )';
				return rn_apply();
			}

			var xhr = new XMLHttpRequest();
			xhr.open('GET', f[0].src + '?move=' + dst, true);
			xhr.onreadystatechange = rename_cb;
			xhr.send();
		}
	};

	r.delete = function (e) {
		ev(e);
		if (clgot(bdel, 'hide'))
			return toast.err(3, 'cannot delete:\nyou do not have “delete” permission in this folder');

		var sel = msel.getsel(),
			vps = [];

		for (var a = 0; a < sel.length; a++)
			vps.push(sel[a].vp);

		if (!sel.length)
			return toast.err(3, 'select at least 1 item to delete');

		function deleter() {
			var xhr = new XMLHttpRequest(),
				vp = vps.shift();

			if (!vp) {
				toast.ok(2, 'delete OK');
				treectl.goto(get_evpath());
				return;
			}
			toast.inf(0, esc('deleting ' + (vps.length + 1) + ' items\n\n' + vp));

			xhr.open('GET', vp + '?delete', true);
			xhr.onreadystatechange = delete_cb;
			xhr.send();
		}
		function delete_cb() {
			if (this.readyState != XMLHttpRequest.DONE)
				return;

			if (this.status !== 200) {
				var msg = this.responseText;
				toast.err(9, 'delete failed:\n' + msg);
				return;
			}
			deleter();
		}

		modal.confirm('<h6 style="color:#900">DANGER</h6>\n<b>DELETE these ' + vps.length + ' items?</b><ul>' + uricom_adec(vps, true).join('') + '</ul>', function () {
			modal.confirm('<b>Last chance!</b> Delete?', deleter, null);
		}, null);
	};

	r.cut = function (e) {
		ev(e);
		if (clgot(bcut, 'hide'))
			return toast.err(3, 'cannot cut:\nyou do not have “move” permission in this folder');

		var sel = msel.getsel(),
			vps = [];

		if (!sel.length)
			toast.err(3, 'select at least 1 item to cut');

		var els = [];
		for (var a = 0; a < sel.length; a++) {
			vps.push(sel[a].vp);
			if (sel.length < 100) {
				els.push(ebi(sel[a].id).closest('tr'));
				clmod(els[a], 'fcut');
			}
		}

		setTimeout(function () {
			for (var a = 0; a < els.length; a++)
				clmod(els[a], 'fcut', 1);
		}, 1);

		try {
			var stamp = Date.now();
			vps = JSON.stringify([stamp].concat(vps));
			if (vps.length > 1024 * 1024)
				throw 'a';

			swrite('fman_clip', vps);
			r.tx(stamp);
			if (sel.length)
				toast.inf(1.5, 'cut ' + sel.length + ' items');
		}
		catch (ex) {
			toast.warn(30, 'cut ' + sel.length + ' items\n\nbut: only <b>this</b> browser-tab can paste them\n(since the selection is so absolutely massive)');
		}
	};

	r.paste = function (e) {
		ev(e);
		if (clgot(bpst, 'hide'))
			return toast.err(3, 'cannot paste:\nyou do not have “write” permission in this folder');

		if (!r.clip.length)
			return toast.err(5, 'first cut some files/folders to paste\n\nnote: you can cut/paste across different browser tabs');

		var req = [],
			exists = [],
			indir = [],
			srcdir = vsplit(r.clip[0])[0],
			links = QSA('#files tbody td:nth-child(2) a');

		for (var a = 0, aa = links.length; a < aa; a++)
			indir.push(vsplit(noq_href(links[a]))[1]);

		for (var a = 0; a < r.clip.length; a++) {
			var found = false;
			for (var b = 0; b < indir.length; b++) {
				if (r.clip[a].endsWith('/' + indir[b])) {
					exists.push(r.clip[a]);
					found = true;
				}
			}
			if (!found)
				req.push(r.clip[a]);
		}

		if (exists.length)
			toast.warn(30, 'these ' + exists.length + ' items cannot be pasted here (names already exist):<ul>' + uricom_adec(exists, true).join('') + '</ul>');

		if (!req.length)
			return;

		function paster() {
			var xhr = new XMLHttpRequest(),
				vp = req.shift();

			if (!vp) {
				toast.ok(2, 'paste OK');
				treectl.goto(get_evpath());
				r.tx(srcdir);
				return;
			}
			toast.inf(0, esc('pasting ' + (req.length + 1) + ' items\n\n' + uricom_dec(vp)[0]));

			var dst = get_evpath() + vp.split('/').pop();

			xhr.open('GET', vp + '?move=' + dst, true);
			xhr.onreadystatechange = paste_cb;
			xhr.send();
		}
		function paste_cb() {
			if (this.readyState != XMLHttpRequest.DONE)
				return;

			if (this.status !== 200) {
				var msg = this.responseText;
				toast.err(9, 'paste failed:\n' + msg);
				return;
			}
			paster();
		}

		modal.confirm('paste these ' + req.length + ' items here?<ul>' + uricom_adec(req, true).join('') + '</ul>', function () {
			paster();
			jwrite('fman_clip', [Date.now()]);
		}, null);
	};

	function onmsg(msg) {
		r.clip = null;
		var n = parseInt('' + msg), tries = 0;
		var fun = function () {
			if (n == msg && n > 1 && r.clip === null) {
				var fc = jread('fman_clip', []);
				if (!fc || !fc.length || fc[0] != n) {
					if (++tries > 10)
						return modal.alert('failed to read clipboard from other browser tab');

					return setTimeout(fun, 100);
				}
			}
			r.render();
			if (msg == get_evpath())
				treectl.goto(msg);
		};
		fun();
	}

	if (r.bus)
		r.bus.onmessage = function (e) {
			onmsg(e ? e.data : 1)
		};

	r.tx = function (msg) {
		if (!r.bus)
			return onmsg(msg);

		r.bus.postMessage(msg);
		r.bus.onmessage();
	};

	bren.onclick = r.rename;
	bdel.onclick = r.delete;
	bcut.onclick = r.cut;
	bpst.onclick = r.paste;

	return r;
})();


var showfile = (function () {
	var r = {};
	r.map = {
		'.ahk': 'autohotkey',
		'.bas': 'basic',
		'.bat': 'batch',
		'.cxx': 'cpp',
		'.h': 'c',
		'.hpp': 'cpp',
		'.htm': 'html',
		'.hxx': 'cpp',
		'.patch': 'diff',
		'.ps1': 'powershell',
		'.psm1': 'powershell',
		'.pl': 'perl',
		'.rs': 'rust',
		'.sh': 'bash',
		'.service': 'systemd',
		'.vb': 'vbnet',
		'.v': 'verilog',
		'.vh': 'verilog',
		'.yml': 'yaml'
	};
	r.nmap = {
		'cmakelists.txt': 'cmake',
		'dockerfile': 'docker'
	};
	var x = txt_ext + ' c cfg conf cpp cs css diff go html ini java js json jsx kt kts less latex lisp lua makefile md py r rss rb ruby sass scss sql svg swift tex toml ts vhdl xml yaml';
	x = x.split(/ +/g);
	for (var a = 0; a < x.length; a++)
		r.map["." + x[a]] = x[a];

	r.sname = function (srch) {
		return srch.split(/[?&]doc=/)[1].split('&')[0];
	};

	window.Prism = { 'manual': true };
	var em = QS('#bdoc>pre');
	if (em)
		em = [r.sname(window.location.search), window.location.hash, em.textContent];

	r.setstyle = function () {
		if (window['no_prism'])
			return;

		qsr('#prism_css');
		var el = mknod('link');
		el.rel = 'stylesheet';
		el.href = '/.cpr/deps/prism' + (light ? '' : 'd') + '.css';
		el.setAttribute('id', 'prism_css');
		document.head.appendChild(el);
	};

	r.active = function () {
		return document.location.search.indexOf('doc=') + 1;
	};

	r.getlang = function (fn) {
		fn = fn.toLowerCase();
		var ext = fn.slice(fn.lastIndexOf('.'));
		return r.map[ext] || r.nmap[fn];
	}

	r.addlinks = function () {
		r.files = [];
		var links = msel.getall();
		for (var a = 0; a < links.length; a++) {
			var link = links[a],
				fn = link.vp.split('/').pop(),
				lang = r.getlang(fn);

			if (!lang)
				continue;

			r.files.push({ 'id': link.id, 'name': fn });

			var td = ebi(link.id).closest('tr').getElementsByTagName('td')[0];

			if (lang == 'md' && td.textContent != '-')
				continue;

			td.innerHTML = '<a href="#" class="doc bri" hl="' + link.id + '">-txt-</a>';
		}
		r.mktree();
		if (em) {
			render(em);
			em = null;
		}
	};

	r.show = function (url, no_push) {
		var xhr = new XMLHttpRequest();
		xhr.url = url;
		xhr.no_push = no_push;
		xhr.ts = Date.now();
		xhr.open('GET', url.split('?')[0] + '?raw', true);
		xhr.onreadystatechange = load_cb;
		xhr.send();
	};

	function load_cb() {
		if (this.readyState != XMLHttpRequest.DONE)
			return;

		if (this.status !== 200) {
			toast.err(0, "recvtree, http " + this.status + ": " + this.responseText);
			return;
		}

		render([this.url, '', this.responseText], this.no_push);
	}

	function render(doc, no_push) {
		r.q = null;
		var url = doc[0],
			lnh = doc[1],
			txt = doc[2],
			name = url.split('/').pop(),
			lang = r.getlang(name),
			is_md = lang == 'md';

		ebi('files').style.display = ebi('gfiles').style.display = ebi('pro').style.display = ebi('epi').style.display = 'none';
		ebi('dldoc').setAttribute('href', url);

		var wr = ebi('bdoc'),
			defer = !Prism.highlightElement;

		var fun = function (el) {
			try {
				if (lnh.slice(0, 5) == '#doc.')
					sethash(lnh.slice(1));

				Prism.highlightElement(el || QS('#doc>code'));
			}
			catch (ex) { }
		}

		if (txt.length > 1024 * 256)
			fun = function (el) { };

		qsr('#doc');
		var el = mknod('pre');
		el.setAttribute('id', 'doc');
		el.setAttribute('tabindex', '0');
		clmod(ebi('wrap'), 'doc', !is_md);
		if (is_md) {
			show_md(txt, name, el);
		}
		else {
			el.textContent = txt;
			el.innerHTML = '<code>' + el.innerHTML + '</code>';
			if (!window['no_prism']) {
				el.setAttribute('class', 'prism linkable-line-numbers line-numbers language-' + lang);
				if (!defer)
					fun(el.firstChild);
				else
					import_js('/.cpr/deps/prism.js', function () { fun(); });
			}
		}

		wr.appendChild(el);
		wr.style.display = '';
		set_tabindex();

		document.documentElement.scrollTop = 0;
		var hfun = no_push ? hist_replace : hist_push;
		hfun(get_evpath() + '?doc=' + url.split('/').pop());

		qsr('#docname');
		el = mknod('span');
		el.textContent = uricom_dec(name)[0];
		el.setAttribute('id', 'docname');
		ebi('path').appendChild(el);

		r.updtree();
		treectl.textmode(true);
		tree_scrollto();
	}

	r.mktree = function () {
		var html = ['<li class="bn">list of textfiles in<br />' + linksplit(get_vpath()).join('') + '</li>'];
		for (var a = 0; a < r.files.length; a++) {
			var file = r.files[a];
			html.push('<li><a href="#" hl="' + file.id +
				'">' + esc(uricom_dec(file.name)[0]) + '</a>');
		}
		ebi('docul').innerHTML = html.join('\n');
	};

	r.updtree = function () {
		var fn = QS('#path span:last-child'),
			lis = QSA('#docul li a'),
			sels = msel.getsel(),
			actsel = false;

		fn = fn ? fn.textContent : '';
		for (var a = 0, aa = lis.length; a < aa; a++) {
			var lin = lis[a].textContent,
				sel = false;

			for (var b = 0; b < sels.length; b++)
				if (vsplit(sels[b].vp)[1] == lin)
					sel = true;

			clmod(lis[a], 'hl', lin == fn);
			clmod(lis[a], 'sel', sel);
			if (lin == fn && sel)
				actsel = true;
		}
		clmod(ebi('seldoc'), 'sel', actsel);
	};

	r.tglsel = function () {
		var fn = ebi('docname').textContent;
		for (var a = 0; a < r.files.length; a++)
			if (r.files[a].name == fn)
				clmod(ebi(r.files[a].id).closest('tr'), 'sel', 't');

		msel.selui();
	};

	var bdoc = ebi('bdoc');
	bdoc.setAttribute('class', 'line-numbers');
	bdoc.innerHTML = (
		'<div id="hdoc" class="ghead">\n' +
		'<a href="#" class="btn" id="xdoc" tt="return to folder view$NHotkey: M">❌ close</a>\n' +
		'<a href="#" class="btn" id="dldoc" tt="download this file">💾 download</a>\n' +
		'<a href="#" class="btn" id="prevdoc" tt="show previous document$NHotkey: i">⬆ prev</a>\n' +
		'<a href="#" class="btn" id="nextdoc" tt="show next document$NHotkey: K">⬇ next</a>\n' +
		'<a href="#" class="btn" id="seldoc" tt="file is selected$NHotkey: S">sel</a>\n' +
		'</div>'
	);
	ebi('xdoc').onclick = function () {
		thegrid.setvis(true);
	};
	ebi('dldoc').setAttribute('download', '');
	ebi('prevdoc').onclick = function () { tree_neigh(-1); };
	ebi('nextdoc').onclick = function () { tree_neigh(1); };
	ebi('seldoc').onclick = r.tglsel;

	return r;
})();


var thegrid = (function () {
	var lfiles = ebi('files'),
		gfiles = mknod('div');

	gfiles.setAttribute('id', 'gfiles');
	gfiles.style.display = 'none';
	gfiles.innerHTML = (
		'<div id="ghead" class="ghead">' +
		'<a href="#" class="tgl btn" id="gridsel" tt="enable file selection; ctrl-click a file to override$N$N&lt;em&gt;when active: doubleclick a file/folder to open it&lt;/em&gt;$N$NHotkey: S">multiselect</a> <span>zoom: ' +
		'<a href="#" class="btn" z="-1.2" tt="Hotkey: shift-A">&ndash;</a> ' +
		'<a href="#" class="btn" z="1.2" tt="Hotkey: shift-D">+</a></span> <span>chop: ' +
		'<a href="#" class="btn" l="-1" tt="truncate filenames more (show less)">&ndash;</a> ' +
		'<a href="#" class="btn" l="1" tt="truncate filenames less (show more)">+</a></span> <span>sort by: ' +
		'<a href="#" s="href">name</a> ' +
		'<a href="#" s="sz">size</a> ' +
		'<a href="#" s="ts">date</a> ' +
		'<a href="#" s="ext">type</a>' +
		'</span></div>' +
		'<div id="ggrid"></div>'
	);
	lfiles.parentNode.insertBefore(gfiles, lfiles);

	var r = {
		'sz': clamp(fcfg_get('gridsz', 10), 4, 40),
		'ln': clamp(icfg_get('gridln', 3), 1, 7),
		'isdirty': true,
		'bbox': null
	};

	var btnclick = function (e) {
		ev(e);
		var s = this.getAttribute('s'),
			z = this.getAttribute('z'),
			l = this.getAttribute('l');

		if (z)
			return setsz(z > 0 ? r.sz * z : r.sz / (-z));

		if (l)
			return setln(parseInt(l));

		var t = lfiles.tHead.rows[0].cells;
		for (var a = 0; a < t.length; a++)
			if (t[a].getAttribute('name') == s) {
				t[a].click();
				break;
			}

		r.setdirty();
	};

	var links = QSA('#ghead a');
	for (var a = 0; a < links.length; a++)
		links[a].onclick = btnclick;

	r.setvis = function (force) {
		if (showfile.active()) {
			if (!force)
				return;

			hist_push(get_evpath());
		}

		var vis = has(perms, "read");
		gfiles.style.display = vis && r.en ? '' : 'none';
		lfiles.style.display = vis && !r.en ? '' : 'none';
		ebi('pro').style.display = ebi('epi').style.display = ebi('treeul').style.display = ebi('treepar').style.display = '';
		ebi('bdoc').style.display = 'none';
		clmod(ebi('wrap'), 'doc');
		qsr('#docname');
		if (window['treectl'])
			treectl.textmode(false);
	};

	r.setdirty = function () {
		r.dirty = true;
		if (r.en) {
			loadgrid();
		}
		r.setvis();
	};

	function setln(v) {
		if (v) {
			r.ln += v;
			if (r.ln < 1) r.ln = 1;
			if (r.ln > 7) r.ln = v < 0 ? 7 : 99;
			swrite('gridln', r.ln);
			setTimeout(r.tippen, 20);
		}
		try {
			document.documentElement.style.setProperty('--grid-ln', r.ln);
		}
		catch (ex) { }
	}
	setln();

	function setsz(v) {
		if (v !== undefined) {
			r.sz = clamp(v, 4, 40);
			swrite('gridsz', r.sz);
			setTimeout(r.tippen, 20);
		}
		try {
			document.documentElement.style.setProperty('--grid-sz', r.sz + 'em');
		}
		catch (ex) { }
	}
	setsz();

	function gclick1(e) {
		if (ctrl(e))
			return true;

		return gclick.bind(this)(e, false);
	}

	function gclick2(e) {
		if (ctrl(e) || !r.sel)
			return true;

		return gclick.bind(this)(e, true);
	}

	function gclick(e, dbl) {
		var oth = ebi(this.getAttribute('ref')),
			href = noq_href(this),
			aplay = ebi('a' + oth.getAttribute('id')),
			is_img = /\.(gif|jpe?g|png|webp|webm|mp4)(\?|$)/i.test(href),
			is_dir = href.endsWith('/'),
			in_tree = is_dir && treectl.find(oth.textContent.slice(0, -1)),
			have_sel = QS('#files tr.sel'),
			td = oth.closest('td').nextSibling,
			tr = td.parentNode;

		if (r.sel && !dbl) {
			td.click();
			clmod(this, 'sel', clgot(tr, 'sel'));
		}
		else if (widget.is_open && aplay)
			aplay.click();

		else if (in_tree && !have_sel)
			in_tree.click();

		else if (is_dir && !have_sel && treectl.spa)
			treectl.reqls(href, true, true);

		else if (!is_img && have_sel)
			window.open(href, '_blank');

		else {
			if (!dbl)
				return true;

			setTimeout(function () {
				r.sel = true;
			}, 1);
			r.sel = false;
			this.click();
		}
		ev(e);
	}

	r.loadsel = function () {
		if (r.dirty)
			return;

		var ths = QSA('#ggrid>a');

		for (var a = 0, aa = ths.length; a < aa; a++) {
			var tr = ebi(ths[a].getAttribute('ref')).closest('tr'),
				cl = tr.getAttribute('class') || '';

			if (noq_href(ths[a]).endsWith('/'))
				cl += ' dir';

			ths[a].setAttribute('class', cl);
		}
		var uns = QS('#ggrid a[ref="unsearch"]');
		if (uns)
			uns.onclick = function (e) {
				ev(e);
				ebi('unsearch').click();
			};
	};

	r.tippen = function () {
		var els = QSA('#ggrid>a>span'),
			aa = els.length;

		if (!aa)
			return;

		var cs = window.getComputedStyle(els[0]),
			fs = parseFloat(cs.lineHeight),
			pad = parseFloat(cs.paddingTop),
			pels = [],
			todo = [];

		for (var a = 0; a < aa; a++) {
			var vis = Math.round((els[a].offsetHeight - pad) / fs),
				all = Math.round((els[a].scrollHeight - pad) / fs),
				par = els[a].parentNode;

			pels.push(par);
			todo.push(vis < all ? par.getAttribute('ttt') : null);
		}

		for (var a = 0; a < todo.length; a++) {
			if (todo[a])
				pels[a].setAttribute('tt', todo[a]);
			else
				pels[a].removeAttribute('tt');
		}

		tt.att(ebi('ggrid'));
	};

	function loadgrid() {
		if (have_webp === null)
			return setTimeout(loadgrid, 50);

		r.setvis();
		if (!r.dirty)
			return r.loadsel();

		var html = [];
		var files = QSA('#files>tbody>tr>td:nth-child(2) a[id]');
		for (var a = 0, aa = files.length; a < aa; a++) {
			var ao = files[a],
				ohref = esc(ao.getAttribute('href')),
				href = ohref.split('?')[0],
				name = uricom_dec(vsplit(href)[1])[0],
				ref = ao.getAttribute('id'),
				isdir = href.endsWith('/'),
				ac = isdir ? ' class="dir"' : '',
				ihref = href;

			if (r.thumbs) {
				ihref += '?th=' + (have_webp ? 'w' : 'j');
				if (href == "#")
					ihref = '/.cpr/ico/⏏️';
			}
			else if (isdir) {
				ihref = '/.cpr/ico/folder';
			}
			else {
				var ar = href.split('.');
				if (ar.length > 1)
					ar = ar.slice(1);

				ihref = '';
				ar.reverse();
				for (var b = 0; b < ar.length; b++) {
					if (ar[b].length > 7)
						break;

					ihref = ar[b] + '.' + ihref;
				}
				if (!ihref) {
					ihref = 'unk.';
				}
				ihref = '/.cpr/ico/' + ihref.slice(0, -1);
			}
			ihref += (ihref.indexOf('?') > 0 ? '&' : '?') + 'cache=i';

			html.push('<a href="' + ohref + '" ref="' + ref +
				'"' + ac + ' ttt="' + esc(name) + '"><img style="height:' +
				(r.sz / 1.25) + 'em" onload="th_onload(this)" src="' +
				ihref + '" /><span' + ac + '>' + ao.innerHTML + '</span></a>');
		}
		ebi('ggrid').innerHTML = html.join('\n');

		var ths = QSA('#ggrid>a');
		for (var a = 0, aa = ths.length; a < aa; a++) {
			ths[a].ondblclick = gclick2;
			ths[a].onclick = gclick1;
		}

		r.dirty = false;
		r.bagit();
		r.loadsel();
		setTimeout(r.tippen, 20);
	}

	r.bagit = function () {
		if (!window.baguetteBox)
			return;

		if (r.bbox)
			baguetteBox.destroy();

		r.bbox = baguetteBox.run('#ggrid', {
			captions: function (g) {
				var idx = -1,
					h = '' + g;

				for (var a = 0; a < r.bbox.length; a++)
					if (r.bbox[a].imageElement == g)
						idx = a;

				return '<a download href="' + h +
					'">' + (idx + 1) + ' / ' + r.bbox.length + ' -- ' +
					esc(uricom_dec(h.split('/').pop())[0]) + '</a>';
			}
		})[0];
	};

	bcfg_bind(r, 'thumbs', 'thumbs', true, r.setdirty);
	bcfg_bind(r, 'sel', 'gridsel', false, r.loadsel);
	bcfg_bind(r, 'en', 'griden', false, function (v) {
		v ? loadgrid() : r.setvis(true);
		pbar.onresize();
		vbar.onresize();
	});
	ebi('wtgrid').onclick = ebi('griden').onclick;

	setTimeout(function () {
		import_js('/.cpr/baguettebox.js', r.bagit);
	}, 1);

	return r;
})();


function th_onload(el) {
	el.style.height = '';
}


function tree_scrollto(e) {
	ev(e);
	tree_scrolltoo('#treeul a.hl');
	tree_scrolltoo('#docul a.hl');
}


function tree_scrolltoo(q) {
	var act = QS(q),
		ul = act ? act.offsetParent : null;

	if (!ul)
		return;

	var ctr = ebi('tree'),
		em = parseFloat(getComputedStyle(act).fontSize),
		top = act.offsetTop + ul.offsetTop,
		min = top - 11 * em,
		max = top - (ctr.offsetHeight - 10 * em);

	if (ctr.scrollTop > min)
		ctr.scrollTop = Math.floor(min);
	else if (ctr.scrollTop < max)
		ctr.scrollTop = Math.floor(max);
}


function tree_neigh(n) {
	var links = QSA(showfile.active() || treectl.texts ? '#docul li>a' : '#treeul li>a+a');
	if (!links.length) {
		treectl.dir_cb = function () {
			tree_neigh(n);
		};
		treectl.entree(null, true);
		return;
	}
	var act = -1;
	for (var a = 0, aa = links.length; a < aa; a++) {
		if (clgot(links[a], 'hl')) {
			act = a;
			break;
		}
	}
	if (act == -1 && !treectl.texts)
		return;

	act += n;
	if (act < 0)
		act = links.length - 1;
	if (act >= links.length)
		act = 0;

	treectl.dir_cb = tree_scrollto;
	links[act].click();
}


function tree_up() {
	if (showfile.active())
		return thegrid.setvis(true);

	var act = QS('#treeul a.hl');
	if (!act) {
		treectl.dir_cb = tree_up;
		treectl.entree(null, true);
		return;
	}
	if (act.previousSibling.textContent == '-')
		return act.previousSibling.click();

	act.parentNode.parentNode.parentNode.getElementsByTagName('a')[1].click();
}


document.onkeydown = function (e) {
	if (e.altKey || e.isComposing)
		return;

	if (QS('#bbox-overlay.visible') || modal.busy)
		return;

	var k = e.code + '', pos = -1, n,
		ae = document.activeElement,
		aet = ae && ae != document.body ? ae.nodeName.toLowerCase() : '';

	if (k == 'Escape') {
		ae && ae.blur();

		if (ebi('rn_cancel'))
			return ebi('rn_cancel').click();

		if (QS('.opview.act'))
			return QS('#ops>a').click();

		if (widget.is_open)
			return widget.close();

		if (showfile.active())
			return thegrid.setvis(true);

		if (!treectl.hidden)
			return treectl.detree();

		if (QS('#unsearch'))
			return QS('#unsearch').click();

		if (thegrid.en)
			return ebi('griden').click();
	}

	if (aet == 'tr' && ae.closest('#files')) {
		var d = '';
		if (k == 'ArrowUp') d = 'previous';
		if (k == 'ArrowDown') d = 'next';
		if (d) {
			var el = ae[d + 'ElementSibling'];
			if (el) {
				el.focus();
				if (ctrl(e))
					document.documentElement.scrollTop += (d == 'next' ? 1 : -1) * el.offsetHeight;

				if (e.shiftKey) {
					clmod(el, 'sel', 't');
					msel.selui();
				}

				return ev(e);
			}
		}
		if (k == 'Space') {
			clmod(ae, 'sel', 't');
			msel.selui();
			return ev(e);
		}
		if (k == 'KeyA' && ctrl(e)) {
			var sel = msel.getsel(),
				all = msel.getall();

			msel.evsel(e, sel.length < all.length);
			return ev(e);
		}
	}

	if (ae.closest('pre')) {
		if (k == 'KeyA' && ctrl(e)) {
			var sel = document.getSelection(),
				ran = document.createRange();

			sel.removeAllRanges();
			ran.selectNode(ae.closest('pre'));
			sel.addRange(ran);
			return ev(e);
		}
	}

	if (aet && aet != 'a' && aet != 'tr' && aet != 'pre')
		return;

	if (ctrl(e)) {
		if (k == 'KeyX')
			return fileman.cut();

		if (k == 'KeyV')
			return fileman.paste();

		if (k == 'KeyK')
			return fileman.delete();

		return;
	}

	if (e.shiftKey && k != 'KeyA' && k != 'KeyD')
		return;

	if (k.indexOf('Digit') === 0)
		pos = parseInt(k.slice(-1)) * 0.1;

	if (pos !== -1)
		return seek_au_mul(pos) || true;

	if (k == 'KeyJ')
		return prev_song() || true;

	if (k == 'KeyL')
		return next_song() || true;

	if (k == 'KeyP')
		return playpause() || true;

	n = k == 'KeyU' ? -10 : k == 'KeyO' ? 10 : 0;
	if (n !== 0)
		return seek_au_rel(n) || true;

	n = k == 'KeyI' ? -1 : k == 'KeyK' ? 1 : 0;
	if (n !== 0)
		return tree_neigh(n);

	if (k == 'KeyM')
		return tree_up();

	if (k == 'KeyB')
		return treectl.hidden ? treectl.entree() : treectl.detree();

	if (k == 'KeyG')
		return ebi('griden').click();

	if (k == 'KeyT')
		return ebi('thumbs').click();

	if (k == 'KeyV')
		return ebi('filetree').click();

	if (k == 'F2')
		return fileman.rename();

	if (!treectl.hidden && (!e.shiftKey || !thegrid.en)) {
		if (k == 'KeyA')
			return QS('#twig').click();

		if (k == 'KeyD')
			return QS('#twobytwo').click();
	}

	if (thegrid.en) {
		if (k == 'KeyS')
			return ebi('gridsel').click();

		if (k == 'KeyA')
			return QSA('#ghead a[z]')[0].click();

		if (k == 'KeyD')
			return QSA('#ghead a[z]')[1].click();
	}

	if (showfile.active()) {
		if (k == 'KeyS')
			showfile.tglsel();
	}
};


// search
(function () {
	var sconf = [
		["size",
			["szl", "sz_min", "minimum MiB", "14"],
			["szu", "sz_max", "maximum MiB", "14"]
		],
		["date",
			["dtl", "dt_min", "min. iso8601", "14"],
			["dtu", "dt_max", "max. iso8601", "14"]
		],
		["path",
			["path", "path", "path contains &nbsp; (space-separated)", "30"]
		],
		["name",
			["name", "name", "name contains &nbsp; (negate with -nope)", "30"]
		]
	];
	var oldcfg = [];

	if (QS('#srch_form.tags')) {
		sconf.push(["tags",
			["tags", "tags", "tags contains &nbsp; (^=start, end=$)", "30"]
		]);
		sconf.push(["adv.",
			["adv", "adv", "key>=1A&nbsp; key<=2B&nbsp; .bpm>165", "30"]
		]);
	}

	var trs = [],
		orig_url = null,
		orig_html = null;

	for (var a = 0; a < sconf.length; a++) {
		var html = ['<tr><td><br />' + sconf[a][0] + '</td>'];
		for (var b = 1; b < 3; b++) {
			var hn = "srch_" + sconf[a][b][0],
				csp = (sconf[a].length == 2) ? 2 : 1;

			html.push(
				'<td colspan="' + csp + '"><input id="' + hn + 'c" type="checkbox">\n' +
				'<label for="' + hn + 'c">' + sconf[a][b][2] + '</label>\n' +
				'<br /><input id="' + hn + 'v" type="text" style="width:' + sconf[a][b][3] +
				'em" name="' + sconf[a][b][1] + '" /></td>');
			if (csp == 2)
				break;
		}
		html.push('</tr>');
		trs.push(html);
	}
	var html = [];
	for (var a = 0; a < trs.length; a += 2) {
		html.push('<table>' + (trs[a].concat(trs[a + 1])).join('\n') + '</table>');
	}
	html.push('<table id="tq_raw"><tr><td>raw</td><td><input id="q_raw" type="text" name="q" /></td></tr></table>');
	ebi('srch_form').innerHTML = html.join('\n');

	var o = QSA('#op_search input');
	for (var a = 0; a < o.length; a++) {
		o[a].oninput = ev_search_input;
	}

	function srch_msg(err, txt) {
		var o = ebi('srch_q');
		o.textContent = txt;
		o.style.color = err ? '#f09' : '#c90';
	}

	var search_timeout,
		defer_timeout,
		search_in_progress = 0;

	function ev_search_input() {
		var v = this.value,
			id = this.getAttribute('id');

		if (id.slice(-1) == 'v') {
			var chk = ebi(id.slice(0, -1) + 'c');
			chk.checked = ((v + '').length > 0);
		}

		if (id != "q_raw")
			encode_query();

		set_vq();

		clearTimeout(defer_timeout);
		defer_timeout = setTimeout(try_search, 2000);
		try_search(v);
	}

	function try_search(v) {
		if (Date.now() - search_in_progress > 30 * 1000) {
			clearTimeout(defer_timeout);
			clearTimeout(search_timeout);
			search_timeout = setTimeout(do_search,
				v && v.length < (is_touch ? 4 : 3) ? 600 : 200);
		}
	}

	function set_vq() {
		if (search_in_progress)
			return;

		var q = ebi('q_raw').value,
			vq = ebi('files').getAttribute('q_raw');

		srch_msg(false, (q == vq) ? '' : 'search results below are from a previous query:\n  ' + (vq ? vq : '(*)'));
	}

	function encode_query() {
		var q = '';
		for (var a = 0; a < sconf.length; a++) {
			for (var b = 1; b < sconf[a].length; b++) {
				var k = sconf[a][b][0],
					chk = 'srch_' + k + 'c',
					vs = ebi('srch_' + k + 'v').value,
					tvs = [];

				if (k == 'name')
					console.log('a');
				while (vs) {
					vs = vs.trim();
					if (!vs)
						break;

					var v = '';
					if (vs.startsWith('"')) {
						var vp = vs.slice(1).split(/"(.*)/);
						v = vp[0];
						vs = vp[1] || '';
						while (v.endsWith('\\')) {
							vp = vs.split(/"(.*)/);
							v = v.slice(0, -1) + '"' + vp[0];
							vs = vp[1] || '';
						}
					}
					else {
						var vp = vs.split(/ +(.*)/);
						v = vp[0].replace(/\\"/g, '"');
						vs = vp[1] || '';
					}
					tvs.push(v);
				}

				if (!ebi(chk).checked)
					continue;

				for (var c = 0; c < tvs.length; c++) {
					var tv = tvs[c];
					if (!tv.length)
						break;

					q += ' and ';

					if (k == 'adv') {
						q += tv.replace(/ +/g, " and ").replace(/([=!><]=?)/, " $1 ");
						continue;
					}

					if (k.length == 3) {
						q += k.replace(/sz/, 'size').replace(/dt/, 'date').replace(/l$/, ' >= ').replace(/u$/, ' <= ') + tv;
						continue;
					}

					if (k == 'path' || k == 'name' || k == 'tags') {
						var not = ' ';
						if (tv.slice(0, 1) == '-') {
							tv = tv.slice(1);
							not = ' not ';
						}

						if (tv.slice(0, 1) == '^') {
							tv = tv.slice(1);
						}
						else {
							tv = '*' + tv;
						}

						if (tv.slice(-1) == '$') {
							tv = tv.slice(0, -1);
						}
						else {
							tv += '*';
						}

						if (tv.indexOf(' ') + 1) {
							tv = '"' + tv + '"';
						}

						q += k + not + 'like ' + tv;
					}
				}
			}
		}
		ebi('q_raw').value = q.slice(5);
	}

	function do_search() {
		search_in_progress = Date.now();
		srch_msg(false, "searching...");
		clearTimeout(search_timeout);

		var xhr = new XMLHttpRequest();
		xhr.open('POST', '/?srch', true);
		xhr.setRequestHeader('Content-Type', 'text/plain');
		xhr.onreadystatechange = xhr_search_results;
		xhr.ts = Date.now();
		xhr.q_raw = ebi('q_raw').value;
		xhr.send(JSON.stringify({ "q": xhr.q_raw }));
	}

	function xhr_search_results() {
		if (this.readyState != XMLHttpRequest.DONE)
			return;

		if (this.status !== 200) {
			var msg = this.responseText;
			if (msg.indexOf('<pre>') === 0)
				msg = msg.slice(5);

			srch_msg(true, "http " + this.status + ": " + msg);
			search_in_progress = 0;
			return;
		}
		search_in_progress = 0;
		srch_msg(false, '');

		var res = JSON.parse(this.responseText),
			tagord = res.tag_order;

		sortfiles(res.hits);

		var ofiles = ebi('files');
		if (ofiles.getAttribute('ts') > this.ts)
			return;

		treectl.hide();

		var html = mk_files_header(tagord), seen = {};
		html.push('<tbody>');
		html.push('<tr><td>-</td><td colspan="42"><a href="#" id="unsearch"><big style="font-weight:bold">[❌] close search results</big></a></td></tr>');
		for (var a = 0; a < res.hits.length; a++) {
			var r = res.hits[a],
				ts = parseInt(r.ts),
				sz = esc(r.sz + ''),
				rp = esc(uricom_dec(r.rp + '')[0]),
				ext = rp.lastIndexOf('.') > 0 ? rp.split('.').pop().split('?')[0] : '%',
				id = 'f-' + ('00000000' + crc32(rp)).slice(-8);

			while (seen[id])
				id += 'a';
			seen[id] = 1;

			if (ext.length > 8)
				ext = '%';

			var links = linksplit(r.rp + '', id).join(''),
				nodes = ['<tr><td>-</td><td><div>' + links + '</div>', sz];

			for (var b = 0; b < tagord.length; b++) {
				var k = tagord[b],
					v = r.tags[k] || "";

				if (k == ".dur") {
					var sv = v ? s2ms(v) : "";
					nodes[nodes.length - 1] += '</td><td sortv="' + v + '">' + sv;
					continue;
				}

				nodes.push(v);
			}

			nodes = nodes.concat([ext, unix2iso(ts)]);
			html.push(nodes.join('</td><td>'));
			html.push('</td></tr>');
		}

		if (!orig_html || orig_url != get_evpath()) {
			orig_html = ebi('files').innerHTML;
			orig_url = get_evpath();
		}

		ofiles = set_files_html(html.join('\n'));
		ofiles.setAttribute("ts", this.ts);
		ofiles.setAttribute("q_raw", this.q_raw);
		set_vq();
		mukey.render();
		reload_browser();
		filecols.set_style(['File Name']);

		sethash('q=' + uricom_enc(this.q_raw));
		ebi('unsearch').onclick = unsearch;
	}

	function unsearch(e) {
		ev(e);
		treectl.show();
		set_files_html(orig_html);
		ebi('files').removeAttribute('q_raw');
		orig_html = null;
		sethash('');
		reload_browser();
	}
})();


var treectl = (function () {
	var r = {
		"hidden": true,
		"ls_cb": null,
		"dir_cb": tree_scrollto,
		"pdir": []
	},
		entreed = false,
		fixedpos = false,
		prev_atop = null,
		prev_winh = null,
		mentered = null,
		treesz = clamp(icfg_get('treesz', 16), 10, 50);

	bcfg_bind(r, 'spa', 'spafiles', true);
	bcfg_bind(r, 'ireadme', 'ireadme', true);
	bcfg_bind(r, 'dyn', 'dyntree', true, onresize);
	bcfg_bind(r, 'dots', 'dotfiles', false, function (v) {
		r.goto(get_evpath());
	});
	setwrap(bcfg_bind(r, 'wtree', 'wraptree', true, setwrap));
	setwrap(bcfg_bind(r, 'parpane', 'parpane', true, onscroll));
	bcfg_bind(r, 'htree', 'hovertree', false, reload_tree);

	function setwrap(v) {
		clmod(ebi('tree'), 'nowrap', !v);
		reload_tree();
	}
	setwrap(r.wtree);

	r.entree = function (e, nostore) {
		ev(e);
		entreed = true;
		if (!nostore)
			swrite('entreed', 'tree');

		get_tree("", get_evpath(), true);
		r.show();
	}

	r.show = function () {
		r.hidden = false;
		if (!entreed) {
			ebi('path').style.display = 'inline-block';
			return;
		}
		ebi('path').style.display = 'none';
		ebi('tree').style.display = 'block';
		window.addEventListener('scroll', onscroll);
		window.addEventListener('resize', onresize);
		onresize();
	};

	r.detree = function (e) {
		ev(e);
		entreed = false;
		swrite('entreed', 'na');

		r.hide();
		ebi('path').style.display = '';
	}

	r.hide = function () {
		r.hidden = true;
		ebi('path').style.display = 'none';
		ebi('tree').style.display = 'none';
		ebi('wrap').style.marginLeft = '';
		window.removeEventListener('resize', onresize);
		window.removeEventListener('scroll', onscroll);
	}

	function unmenter() {
		if (mentered) {
			mentered.style.position = '';
			mentered = null;
		}
	}

	r.textmode = function (ya) {
		var chg = !r.texts != !ya;
		r.texts = ya;
		ebi('docul').style.display = ya ? '' : 'none';
		ebi('treeul').style.display = ebi('treepar').style.display = ya ? 'none' : '';
		clmod(ebi('filetree'), 'on', ya);
		if (chg)
			tree_scrollto();
	};
	ebi('filetree').onclick = function (e) {
		ev(e);
		r.textmode(!r.texts);
	};
	r.textmode(false);

	function onscroll() {
		unmenter();
		onscroll2();
	}

	function onscroll2() {
		if (!entreed || r.hidden || document.visibilityState == 'hidden')
			return;

		var tree = ebi('tree'),
			wrap = ebi('wrap'),
			wraptop = null,
			atop = wrap.getBoundingClientRect().top,
			winh = window.innerHeight,
			parp = ebi('treepar'),
			y = tree.scrollTop,
			w = tree.offsetWidth;

		if (atop !== prev_atop || winh !== prev_winh)
			wraptop = Math.floor(wrap.offsetTop);

		if (r.parpane && r.pdir.length && w != r.pdirw) {
			r.pdirw = w;
			compy();
		}

		if (!r.parpane || !r.pdir.length || y >= r.pdir.slice(-1)[0][0] || y <= r.pdir[0][0]) {
			clmod(parp, 'off', 1);
			r.pdirh = null;
		}
		else {
			var h1 = [], h2 = [], els = [];
			for (var a = 0; a < r.pdir.length; a++) {
				if (r.pdir[a][0] > y)
					break;

				var e2 = r.pdir[a][1], e1 = e2.previousSibling;
				h1.push('<li>' + e1.outerHTML + e2.outerHTML + '<ul>');
				h2.push('</ul></li>');
				els.push([e1, e2]);
			}
			h1 = h1.join('\n') + h2.join('\n');
			if (h1 != r.pdirh) {
				r.pdirh = h1;
				parp.innerHTML = h1;
				clmod(parp, 'off');
				var els = QSA('#treepar a');
				for (var a = 0, aa = els.length; a < aa; a++)
					els[a].onclick = bad_proxy;
			}
			y = ebi('treeh').offsetHeight;
			if (!fixedpos)
				y += tree.offsetTop - document.documentElement.scrollTop;

			y = (y - 3) + 'px';
			if (parp.style.top != y)
				parp.style.top = y;
		}

		if (wraptop === null)
			return;

		prev_atop = atop;
		prev_winh = winh;

		if (fixedpos && atop >= 0) {
			tree.style.position = 'absolute';
			tree.style.bottom = '';
			fixedpos = false;
		}
		else if (!fixedpos && atop < 0) {
			tree.style.position = 'fixed';
			tree.style.height = 'auto';
			fixedpos = true;
		}

		if (fixedpos) {
			tree.style.top = Math.max(0, parseInt(atop)) + 'px';
		}
		else {
			var top = Math.max(0, wraptop),
				treeh = winh - atop;

			tree.style.top = top + 'px';
			tree.style.height = treeh < 10 ? '' : Math.floor(treeh - 2) + 'px';
		}
	}
	timer.add(onscroll2, true);

	function onresize(e) {
		if (!entreed || r.hidden)
			return;

		var q = '#tree',
			nq = -3;

		while (r.dyn) {
			nq++;
			q += '>ul>li';
			if (!QS(q))
				break;
		}
		nq = Math.max(nq, get_evpath().split('/').length - 2);
		var iw = (treesz + Math.max(0, nq)),
			w = iw + 'em',
			w2 = (iw + 2) + 'em';

		try {
			document.documentElement.style.setProperty('--nav-sz', w);
		}
		catch (ex) { }
		ebi('tree').style.width = w;
		ebi('wrap').style.marginLeft = w2;
		onscroll();
	}

	r.find = function (txt) {
		var ta = QSA('#treeul a.hl+ul>li>a+a');
		for (var a = 0, aa = ta.length; a < aa; a++)
			if (ta[a].textContent == txt)
				return ta[a];
	};

	r.goto = function (url, push) {
		get_tree("", url, true);
		r.reqls(url, push, true);
	};

	function get_tree(top, dst, rst) {
		var xhr = new XMLHttpRequest();
		xhr.top = top;
		xhr.dst = dst;
		xhr.rst = rst;
		xhr.ts = Date.now();
		xhr.open('GET', dst + '?tree=' + top + (r.dots ? '&dots' : ''), true);
		xhr.onreadystatechange = recvtree;
		xhr.send();
		enspin('#tree');
	}

	function recvtree() {
		if (this.readyState != XMLHttpRequest.DONE)
			return;

		if (this.status !== 200) {
			toast.err(0, "recvtree, http " + this.status + ": " + this.responseText);
			return;
		}

		var cur = ebi('treeul').getAttribute('ts');
		if (cur && parseInt(cur) > this.ts) {
			console.log("reject tree");
			return;
		}
		ebi('treeul').setAttribute('ts', this.ts);

		var top = this.top == '.' ? this.dst : this.top,
			name = uricom_dec(top.split('/').slice(-2)[0])[0],
			rtop = top.replace(/^\/+/, ""),
			res;

		try {
			res = JSON.parse(this.responseText);
		}
		catch (ex) {
			return;
		}
		var html = parsetree(res, rtop);
		if (!this.top) {
			html = '<li><a href="#">-</a><a href="/">[root]</a>\n<ul>' + html;
			if (this.rst || !ebi('treeul').getElementsByTagName('li').length)
				ebi('treeul').innerHTML = html + '</ul></li>';
		}
		else {
			html = '<a href="#">-</a><a href="' +
				esc(top) + '">' + esc(name) +
				"</a>\n<ul>\n" + html + "</ul>";

			var links = QSA('#treeul a+a');
			for (var a = 0, aa = links.length; a < aa; a++) {
				if (links[a].getAttribute('href') == top) {
					var o = links[a].parentNode;
					if (!o.getElementsByTagName('li').length)
						o.innerHTML = html;
				}
			}
		}
		QS('#treeul>li>a+a').textContent = '[root]';
		despin('#tree');
		reload_tree();
		onresize();

		var fun = r.dir_cb;
		if (fun) {
			r.dir_cb = null;
			try {
				fun();
			}
			catch (ex) {
				console.log("dir_cb failed", ex);
			}
		}
	}

	function reload_tree() {
		var cdir = get_vpath(),
			links = QSA('#treeul a+a'),
			nowrap = QS('#tree.nowrap') && QS('#hovertree.on'),
			act = null;

		for (var a = 0, aa = links.length; a < aa; a++) {
			var href = uricom_dec(links[a].getAttribute('href'))[0],
				cl = '';

			if (href == cdir) {
				act = links[a];
				cl = 'hl';
			}
			else if (cdir.startsWith(href)) {
				cl = 'par';
			}

			links[a].setAttribute('class', cl);
			links[a].onclick = treego;
			links[a].onmouseenter = nowrap ? menter : null;
			links[a].onmouseleave = nowrap ? mleave : null;
		}
		links = QSA('#treeul li>a:first-child');
		for (var a = 0, aa = links.length; a < aa; a++) {
			links[a].setAttribute('dst', links[a].nextSibling.getAttribute('href'));
			links[a].onclick = treegrow;
		}
		ebi('tree').onscroll = nowrap ? unmenter : null;
		r.pdir = [];
		try {
			while (act) {
				r.pdir.unshift([-1, act]);
				act = act.parentNode.parentNode.closest('li').querySelector('a:first-child+a');
			}
		}
		catch (ex) { }
		r.pdir.shift();
		r.pdirw = -1;
	}

	function compy() {
		for (var a = 0; a < r.pdir.length; a++)
			r.pdir[a][0] = r.pdir[a][1].offsetTop;

		var ofs = 0;
		for (var a = 0; a < r.pdir.length - 1; a++) {
			ofs += r.pdir[a][1].offsetHeight + 1;
			r.pdir[a + 1][0] -= ofs;
		}
	}

	function menter(e) {
		var p = this.offsetParent,
			pp = p.offsetParent,
			ppy = pp.offsetTop,
			y = this.offsetTop + p.offsetTop + ppy - p.scrollTop - pp.scrollTop - (ppy ? document.documentElement.scrollTop : 0);

		this.style.top = y + 'px';
		this.style.position = 'fixed';
		mentered = this;
	}

	function mleave(e) {
		this.style.position = '';
		mentered = null;
	}

	function bad_proxy(e) {
		ev(e);
		var dst = this.getAttribute('dst'),
			k = dst ? 'dst' : 'href',
			v = dst ? dst : this.getAttribute('href'),
			els = QSA('#treeul a');

		for (var a = 0, aa = els.length; a < aa; a++)
			if (els[a].getAttribute(k) === v)
				return els[a].click();
	}

	function treego(e) {
		if (ctrl(e))
			return true;

		ev(e);
		if (this.getAttribute('class') == 'hl' &&
			this.previousSibling.textContent == '-') {
			treegrow.call(this.previousSibling, e);
			return;
		}
		r.reqls(this.getAttribute('href'), true);
		r.dir_cb = tree_scrollto;
		thegrid.setvis(true);
	}

	r.reqls = function (url, hpush, no_tree) {
		var xhr = new XMLHttpRequest();
		xhr.top = url;
		xhr.hpush = hpush;
		xhr.ts = Date.now();
		xhr.open('GET', xhr.top + '?ls' + (r.dots ? '&dots' : ''), true);
		xhr.onreadystatechange = recvls;
		xhr.send();
		if (hpush && !no_tree)
			get_tree('.', xhr.top);

		enspin(thegrid.en ? '#gfiles' : '#files');
	}

	function treegrow(e) {
		ev(e);
		if (this.textContent == '-') {
			while (this.nextSibling.nextSibling) {
				var rm = this.nextSibling.nextSibling;
				rm.parentNode.removeChild(rm);
			}
			this.textContent = '+';
			onresize();
			return;
		}
		var dst = this.getAttribute('dst');
		get_tree('.', dst);
	}

	function recvls() {
		if (this.readyState != XMLHttpRequest.DONE)
			return;

		if (this.status !== 200) {
			toast.err(0, "recvls, http " + this.status + ": " + this.responseText);
			return;
		}

		var cur = ebi('files').getAttribute('ts');
		if (cur && parseInt(cur) > this.ts) {
			console.log("reject ls");
			return;
		}
		ebi('files').setAttribute('ts', this.ts);

		try {
			var res = JSON.parse(this.responseText);
		}
		catch (ex) {
			window.location = this.top;
			return;
		}

		ebi('srv_info').innerHTML = '<span>' + res.srvinf + '</span>';

		if (this.hpush && !showfile.active())
			hist_push(this.top);

		r.gentab(this.top, res);
		despin('#files');
		despin('#gfiles');

		ebi('pro').innerHTML = res.logues ? res.logues[0] || "" : "";
		ebi('epi').innerHTML = res.logues ? res.logues[1] || "" : "";

		clmod(ebi('epi'), 'mdo');
		if (res.readme)
			show_readme(res.readme);

		wintitle();
		var fun = r.ls_cb;
		if (fun) {
			r.ls_cb = null;
			fun();
		}
		eval_hash();
	}

	r.gentab = function (top, res) {
		var nodes = res.dirs.concat(res.files),
			html = mk_files_header(res.taglist),
			seen = {};

		showfile.files = [];
		html.push('<tbody>');
		nodes = sortfiles(nodes);
		for (var a = 0; a < nodes.length; a++) {
			var tn = nodes[a],
				bhref = tn.href.split('?')[0],
				fname = uricom_dec(bhref)[0],
				hname = esc(fname),
				sortv = (bhref.slice(-1) == '/' ? '\t' : '') + hname,
				id = 'f-' + ('00000000' + crc32(fname)).slice(-8),
				lang = showfile.getlang(fname);

			while (seen[id])  // ejyefs ev69gg y9j8sg .opus
				id += 'a';
			seen[id] = 1;

			if (lang)
				showfile.files.push({ 'id': id, 'name': fname });

			if (tn.lead == '-')
				tn.lead = '<a href="#" class="doc' + (lang ? ' bri' : '') +
					'" hl="' + id + '" name="' + hname + '">-txt-</a>';

			var ln = ['<tr><td>' + tn.lead + '</td><td sortv="' + sortv +
				'"><a href="' + top + tn.href + '" id="' + id + '">' + hname + '</a>', tn.sz];

			for (var b = 0; b < res.taglist.length; b++) {
				var k = res.taglist[b],
					v = (tn.tags || {})[k] || "";

				if (k == ".dur") {
					var sv = v ? s2ms(v) : "";
					ln[ln.length - 1] += '</td><td sortv="' + v + '">' + sv;
					continue;
				}
				ln.push(v);
			}
			ln = ln.concat([tn.ext, unix2iso(tn.ts)]).join('</td><td>');
			html.push(ln + '</td></tr>');
		}
		html.push('</tbody>');
		html = html.join('\n');
		set_files_html(html);

		filecols.set_style();
		showfile.mktree();
		mukey.render();
		reload_tree();
		reload_browser();
		tree_scrollto();
		if (res.acct) {
			acct = res.acct;
			have_up2k_idx = res.idx;
			apply_perms(res.perms);
			fileman.render();
		}
	}

	r.hydrate = function () {
		if (ls0 === null) {
			var xhr = new XMLHttpRequest();
			xhr.open('GET', '/?am_js', true);
			xhr.send();

			return r.reqls(get_evpath(), false, true);
		}

		r.gentab(get_evpath(), ls0);
		reload_browser();
		pbar.onresize();
		vbar.onresize();
		mukey.render();
		showfile.addlinks();
		thegrid.setdirty();
		setTimeout(eval_hash, 1);
	};

	function parsetree(res, top) {
		var ret = '';
		for (var a = 0; a < res.a.length; a++) {
			if (res.a[a] !== '')
				res['k' + res.a[a]] = 0;
		}
		delete res['a'];
		var keys = Object.keys(res);
		keys.sort(function (a, b) { return a.localeCompare(b); });
		for (var a = 0; a < keys.length; a++) {
			var kk = keys[a],
				ks = kk.slice(1),
				k = uricom_dec(ks),
				hek = esc(k[0]),
				uek = k[1] ? uricom_enc(k[0], true) : k[0],
				url = '/' + (top ? top + uek : uek) + '/',
				sym = res[kk] ? '-' : '+',
				link = '<a href="#">' + sym + '</a><a href="' +
					url + '">' + hek + '</a>';

			if (res[kk]) {
				var subtree = parsetree(res[kk], url.slice(1));
				ret += '<li>' + link + '\n<ul>\n' + subtree + '</ul></li>\n';
			}
			else {
				ret += '<li>' + link + '</li>\n';
			}
		}
		return ret;
	}

	function scaletree(e) {
		ev(e);
		treesz += parseInt(this.getAttribute("step"));
		if (isNaN(treesz))
			treesz = 16;

		treesz = clamp(treesz, 2, 120);
		swrite('treesz', treesz);
		onresize();
	}

	ebi('entree').onclick = r.entree;
	ebi('detree').onclick = r.detree;
	ebi('visdir').onclick = tree_scrollto;
	ebi('twig').onclick = scaletree;
	ebi('twobytwo').onclick = scaletree;

	var cs = sread('entreed'),
		vw = window.innerWidth / parseFloat(getComputedStyle(document.body)['font-size']);

	if (cs == 'tree' || (cs != 'na' && vw >= 60))
		r.entree(null, true);

	window.onpopstate = function (e) {
		console.log("h-pop " + e.state);
		if (!e.state)
			return;

		var url = new URL(e.state, "https://" + document.location.host);
		var hbase = url.pathname;
		var cbase = document.location.pathname;
		if (url.search.indexOf('doc=') + 1 && hbase == cbase)
			return showfile.show(hbase + showfile.sname(url.search), true);

		r.goto(url.pathname);
	};

	hist_replace(get_evpath() + window.location.hash);
	r.onscroll = onscroll;
	return r;
})();


function enspin(sel) {
	despin(sel);
	var d = mknod('div');
	d.setAttribute('class', 'dumb_loader_thing');
	d.innerHTML = '🌲';
	var tgt = QS(sel);
	tgt.insertBefore(d, tgt.childNodes[0]);
}


function despin(sel) {
	var o = QSA(sel + '>.dumb_loader_thing');
	for (var a = o.length - 1; a >= 0; a--)
		o[a].parentNode.removeChild(o[a]);
}


function apply_perms(newperms) {
	perms = newperms || [];

	var a = QS('#ops a[data-dest="up2k"]');
	if (have_up2k_idx) {
		a.removeAttribute('data-perm');
		a.setAttribute('tt', 'up2k: upload files (if you have write-access) or toggle into the search-mode to see if they exist somewhere on the server');
	}
	else {
		a.setAttribute('data-perm', 'write');
		a.setAttribute('tt', 'up2k: upload files with resume support (close your browser and drop the same files in later)');
	}
	tt.att(QS('#ops'));

	var axs = [],
		aclass = '>',
		chk = ['read', 'write', 'move', 'delete', 'get'];

	for (var a = 0; a < chk.length; a++)
		if (has(perms, chk[a]))
			axs.push(chk[a].slice(0, 1).toUpperCase() + chk[a].slice(1));

	axs = axs.join('-');
	if (perms.length == 1) {
		aclass = ' class="warn">';
		axs += '-Only';
	}

	ebi('acc_info').innerHTML = '<span' + aclass + axs + ' access</span>' + (acct != '*' ?
		'<a href="/?pw=x">Logout ' + acct + '</a>' : '<a href="/?h">Login</a>');

	var o = QSA('#ops>a[data-perm], #u2footfoot');
	for (var a = 0; a < o.length; a++) {
		var display = '';
		var needed = o[a].getAttribute('data-perm').split(' ');
		for (var b = 0; b < needed.length; b++) {
			if (!has(perms, needed[b])) {
				display = 'none';
			}
		}
		o[a].style.display = display;
	}

	var o = QSA('#ops>a[data-dep], #u2conf td[data-dep]');
	for (var a = 0; a < o.length; a++)
		o[a].style.display = (
			o[a].getAttribute('data-dep') != 'idx' || have_up2k_idx
		) ? '' : 'none';

	var act = QS('#ops>a.act');
	if (act && act.style.display === 'none')
		goto();

	document.body.setAttribute('perms', perms.join(' '));

	var have_write = has(perms, "write"),
		have_read = has(perms, "read"),
		de = document.documentElement,
		tds = QSA('#u2conf td');

	clmod(de, "read", have_read);
	clmod(de, "write", have_write);
	clmod(de, "nread", !have_read);
	clmod(de, "nwrite", !have_write);

	for (var a = 0; a < tds.length; a++) {
		tds[a].style.display =
			(have_write || tds[a].getAttribute('data-perm') == 'read') ?
				'table-cell' : 'none';
	}

	if (window['up2k'])
		up2k.set_fsearch();

	ebi('widget').style.display = have_read ? '' : 'none';
	thegrid.setvis();
	if (!have_read && have_write)
		goto('up2k');
}


function find_file_col(txt) {
	var i = -1,
		min = false,
		tds = ebi('files').tHead.getElementsByTagName('th');

	for (var a = 0; a < tds.length; a++) {
		var spans = tds[a].getElementsByTagName('span');
		if (spans.length && spans[0].textContent == txt) {
			min = (tds[a].getAttribute('class') || '').indexOf('min') !== -1;
			i = a;
			break;
		}
	}

	if (i == -1)
		return;

	return [i, min];
}


function mk_files_header(taglist) {
	var html = [
		'<thead><tr>',
		'<th name="lead"><span>c</span></th>',
		'<th name="href"><span>File Name</span></th>',
		'<th name="sz" sort="int"><span>Size</span></th>'
	];
	for (var a = 0; a < taglist.length; a++) {
		var tag = taglist[a],
			c1 = tag.slice(0, 1).toUpperCase();

		tag = c1 + tag.slice(1);
		if (c1 == '.')
			tag = '<th name="tags/' + tag + '" sort="int"><span>' + tag.slice(1);
		else
			tag = '<th name="tags/' + tag + '"><span>' + tag;

		html.push(tag + '</span></th>');
	}
	html = html.concat([
		'<th name="ext"><span>T</span></th>',
		'<th name="ts"><span>Date</span></th>',
		'</tr></thead>',
	]);
	return html;
}


var filecols = (function () {
	var hidden = jread('filecols', []),
		tts = {
			"c": "action buttons",
			"dur": "duration",
			"q": "quality / bitrate",
			"Ac": "audio codec",
			"Vc": "video codec",
			"Ahash": "audio checksum",
			"Vhash": "video checksum",
			"Res": "resolution",
			"T": "filetype",
			"aq": "audio quality / bitrate",
			"vq": "video quality / bitrate",
			"pixfmt": "subsampling / pixel structure",
			"resw": "horizontal resolution",
			"resh": "veritcal resolution",
			"chs": "audio channels",
			"hz": "sample rate"
		};

	if (JSON.stringify(def_hcols) != sread('hfilecols')) {
		console.log("applying default hidden-cols");
		jwrite('hfilecols', def_hcols);
		for (var a = 0; a < def_hcols.length; a++) {
			var t = def_hcols[a];
			t = t.slice(0, 1).toUpperCase() + t.slice(1);
			if (t.startsWith("."))
				t = t.slice(1);

			if (hidden.indexOf(t) == -1)
				hidden.push(t);
		}
		jwrite("filecols", hidden);
	}

	var add_btns = function () {
		var ths = QSA('#files th>span');
		for (var a = 0, aa = ths.length; a < aa; a++) {
			var th = ths[a].parentElement,
				ttv = tts[ths[a].textContent];

			th.innerHTML = '<div class="cfg"><a href="#">-</a></div>' + ths[a].outerHTML;
			th.getElementsByTagName('a')[0].onclick = ev_row_tgl;
			if (ttv) {
				th.setAttribute("tt", ttv);
				th.setAttribute("ttd", "u");
				th.setAttribute("ttm", "12");
			}
		}
	};

	function hcols_click(e) {
		ev(e);
		var t = e.target;
		if (t.tagName != 'A')
			return;

		toggle(t.textContent);
	}

	var set_style = function (unhide) {
		hidden.sort();

		if (!unhide)
			unhide = [];

		var html = [],
			hcols = ebi('hcols');

		for (var a = 0; a < hidden.length; a++) {
			var ttv = tts[hidden[a]],
				tta = ttv ? ' tt="' + ttv + '">' : '>';

			html.push('<a href="#" class="btn"' + tta + esc(hidden[a]) + '</a>');
		}
		hcols.previousSibling.style.display = html.length ? 'block' : 'none';
		hcols.innerHTML = html.join('\n');
		hcols.onclick = hcols_click;

		add_btns();

		var ohidden = [],
			ths = QSA('#files th'),
			ncols = ths.length;

		for (var a = 0; a < ncols; a++) {
			var span = ths[a].getElementsByTagName('span');
			if (span.length <= 0)
				continue;

			var name = span[0].textContent,
				cls = false;

			if (has(hidden, name) && !has(unhide, name)) {
				ohidden.push(a);
				cls = true;
			}
			clmod(ths[a], 'min', cls)
		}
		for (var a = 0; a < ncols; a++) {
			var cls = has(ohidden, a) ? 'min' : '',
				tds = QSA('#files>tbody>tr>td:nth-child(' + (a + 1) + ')');

			for (var b = 0, bb = tds.length; b < bb; b++)
				tds[b].setAttribute('class', cls);
		}
		if (window['tt']) {
			tt.att(ebi('hcols'));
			tt.att(QS('#files thead'));
		}
	};
	set_style();

	var toggle = function (name) {
		var ofs = hidden.indexOf(name);
		if (ofs !== -1)
			hidden.splice(ofs, 1);
		else
			hidden.push(name);

		jwrite("filecols", hidden);
		set_style();
	};

	try {
		var ci = find_file_col('dur'),
			i = ci[0],
			rows = ebi('files').tBodies[0].rows;

		for (var a = 0, aa = rows.length; a < aa; a++) {
			var c = rows[a].cells[i];
			if (c && c.textContent)
				c.textContent = s2ms(c.textContent);
		}
	}
	catch (ex) { }

	return {
		"add_btns": add_btns,
		"set_style": set_style,
		"toggle": toggle,
	};
})();


var mukey = (function () {
	var maps = {
		"rekobo_alnum": [
			"1B ", "2B ", "3B ", "4B ", "5B ", "6B ", "7B ", "8B ", "9B ", "10B", "11B", "12B",
			"1A ", "2A ", "3A ", "4A ", "5A ", "6A ", "7A ", "8A ", "9A ", "10A", "11A", "12A"
		],
		"rekobo_classic": [
			"B  ", "F# ", "Db ", "Ab ", "Eb ", "Bb ", "F  ", "C  ", "G  ", "D  ", "A  ", "E  ",
			"Abm", "Ebm", "Bbm", "Fm ", "Cm ", "Gm ", "Dm ", "Am ", "Em ", "Bm ", "F#m", "Dbm"
		],
		"traktor_musical": [
			"B  ", "Gb ", "Db ", "Ab ", "Eb ", "Bb ", "F  ", "C  ", "G  ", "D  ", "A  ", "E  ",
			"Abm", "Ebm", "Bbm", "Fm ", "Cm ", "Gm ", "Dm ", "Am ", "Em ", "Bm ", "Gbm", "Dbm"
		],
		"traktor_sharps": [
			"B  ", "F# ", "C# ", "G# ", "D# ", "A# ", "F  ", "C  ", "G  ", "D  ", "A  ", "E  ",
			"G#m", "D#m", "A#m", "Fm ", "Cm ", "Gm ", "Dm ", "Am ", "Em ", "Bm ", "F#m", "C#m"
		],
		"traktor_open": [
			"6d ", "7d ", "8d ", "9d ", "10d", "11d", "12d", "1d ", "2d ", "3d ", "4d ", "5d ",
			"6m ", "7m ", "8m ", "9m ", "10m", "11m", "12m", "1m ", "2m ", "3m ", "4m ", "5m "
		]
	};
	var map = {},
		html = [];

	for (var k in maps) {
		if (!maps.hasOwnProperty(k))
			continue;

		html.push(
			'<span><input type="radio" name="keytype" value="' + k + '" id="key_' + k + '">' +
			'<label for="key_' + k + '">' + k + '</label></span>');

		for (var a = 0; a < 24; a++)
			maps[k][a] = maps[k][a].trim();
	}
	ebi('key_notation').innerHTML = html.join('\n');

	function set_key_notation(e) {
		ev(e);
		var notation = this.getAttribute('value');
		load_notation(notation);
		try_render();
	}

	function load_notation(notation) {
		swrite("key_notation", notation);
		map = {};
		var dst = maps[notation];
		for (var k in maps)
			if (k != notation && maps.hasOwnProperty(k))
				for (var a = 0; a < 24; a++)
					if (maps[k][a] != dst[a])
						map[maps[k][a]] = dst[a];
	}

	function render() {
		var ci = find_file_col('Key');
		if (!ci)
			return;

		var i = ci[0],
			min = ci[1],
			rows = ebi('files').tBodies[0].rows;

		if (min)
			for (var a = 0, aa = rows.length; a < aa; a++) {
				var c = rows[a].cells[i];
				if (!c)
					continue;

				var v = c.getAttribute('html');
				c.setAttribute('html', map[v] || v);
			}
		else
			for (var a = 0, aa = rows.length; a < aa; a++) {
				var c = rows[a].cells[i];
				if (!c)
					continue;

				var v = c.textContent;
				c.textContent = map[v] || v;
			}
	}

	function try_render() {
		try {
			render();
		}
		catch (ex) {
			console.log("key notation failed: " + ex);
		}
	}

	var notation = sread("key_notation") || "rekobo_alnum";
	ebi('key_' + notation).checked = true;
	load_notation(notation);

	var o = QSA('#key_notation input');
	for (var a = 0; a < o.length; a++) {
		o[a].onchange = set_key_notation;
	}

	return {
		"render": try_render
	};
})();


var light;
(function () {
	function freshen() {
		clmod(document.documentElement, "light", light);
		clmod(document.documentElement, "dark", !light);
		pbar.drawbuf();
		pbar.drawpos();
		vbar.draw();
		showfile.setstyle();
	}

	bcfg_bind(window, 'light', 'lightmode', false, freshen);

	freshen();
})();


var arcfmt = (function () {
	if (!ebi('arc_fmt'))
		return { "render": function () { } };

	var html = [],
		fmts = [
			["tar", "tar", "plain gnutar file"],
			["zip", "zip=utf8", "zip with utf8 filenames (maybe wonky on windows 7 and older)"],
			["zip_dos", "zip", "zip with traditional cp437 filenames, for really old software"],
			["zip_crc", "zip=crc", "cp437 with crc32 computed early,$Nfor MS-DOS PKZIP v2.04g (october 1993)$N(takes longer to process before download can start)"]
		];

	for (var a = 0; a < fmts.length; a++) {
		var k = fmts[a][0];
		html.push(
			'<span><input type="radio" name="arcfmt" value="' + k + '" id="arcfmt_' + k + '" tt="' + fmts[a][2] + '">' +
			'<label for="arcfmt_' + k + '" tt="' + fmts[a][2] + '">' + k + '</label></span>');
	}
	ebi('arc_fmt').innerHTML = html.join('\n');

	var fmt = sread("arc_fmt");
	if (!ebi('arcfmt_' + fmt))
		fmt = "zip";

	ebi('arcfmt_' + fmt).checked = true;

	function render() {
		var arg = null,
			tds = QSA('#files tbody td:first-child a');

		for (var a = 0; a < fmts.length; a++)
			if (fmts[a][0] == fmt)
				arg = fmts[a][1];

		for (var a = 0, aa = tds.length; a < aa; a++) {
			var o = tds[a], txt = o.textContent, href = o.getAttribute('href');
			if (txt != 'tar' && txt != 'zip')
				continue;

			var ofs = href.lastIndexOf('?');
			if (ofs < 0)
				throw new Error('missing arg in url');

			o.setAttribute("href", href.slice(0, ofs + 1) + arg);
			o.textContent = fmt.split('_')[0];
		}
		ebi('selzip').textContent = fmt.split('_')[0];
		ebi('selzip').setAttribute('fmt', arg);
	}

	function try_render() {
		try {
			render();
		}
		catch (ex) {
			console.log("arcfmt failed: " + ex);
		}
	}

	function change_fmt(e) {
		ev(e);
		fmt = this.getAttribute('value');
		swrite("arc_fmt", fmt);
		try_render();
	}

	var o = QSA('#arc_fmt input');
	for (var a = 0; a < o.length; a++) {
		o[a].onchange = change_fmt;
	}

	return {
		"render": try_render
	};
})();


var msel = (function () {
	var r = {};
	r.sel = null;
	r.all = null;

	r.load = function () {
		if (r.sel)
			return;

		r.sel = [];
		if (r.all && r.all.length) {
			for (var a = 0; a < r.all.length; a++) {
				var ao = r.all[a];
				ao.sel = clgot(ebi(ao.id).closest('tr'), 'sel');
				if (ao.sel)
					r.sel.push(ao);
			}
			return;
		}

		r.all = [];
		var links = QSA('#files tbody td:nth-child(2) a:last-child'),
			vbase = get_evpath();

		for (var a = 0, aa = links.length; a < aa; a++) {
			var href = noq_href(links[a]).replace(/\/$/, ""),
				item = {};

			item.id = links[a].getAttribute('id');
			item.sel = clgot(links[a].closest('tr'), 'sel');
			item.vp = href.indexOf('/') !== -1 ? href : vbase + href;

			r.all.push(item);
			if (item.sel)
				r.sel.push(item);

			links[a].closest('tr').setAttribute('tabindex', '0');
		}
	};

	r.getsel = function () {
		r.load();
		return r.sel;
	};
	r.getall = function () {
		r.load();
		return r.all;
	};
	r.selui = function (reset) {
		r.sel = null;
		if (reset)
			r.all = null;

		clmod(ebi('wtoggle'), 'sel', r.getsel().length);
		thegrid.loadsel();
		fileman.render();
		showfile.updtree();
	}
	r.seltgl = function (e) {
		ev(e);
		var tr = this.parentNode;
		clmod(tr, 'sel', 't');
		r.selui();
	}
	r.evsel = function (e, fun) {
		ev(e);
		var trs = QSA('#files tbody tr');
		for (var a = 0, aa = trs.length; a < aa; a++)
			clmod(trs[a], 'sel', fun);
		r.selui();
	}
	ebi('selall').onclick = function (e) {
		r.evsel(e, "add");
	};
	ebi('selinv').onclick = function (e) {
		r.evsel(e, "t");
	};
	ebi('selzip').onclick = function (e) {
		ev(e);
		var sel = r.getsel(),
			arg = ebi('selzip').getAttribute('fmt'),
			frm = mknod('form'),
			txt = [];

		for (var a = 0; a < sel.length; a++)
			txt.push(vsplit(sel[a].vp)[1]);

		txt = txt.join('\n');

		frm.setAttribute('action', '?' + arg);
		frm.setAttribute('method', 'post');
		frm.setAttribute('target', '_blank');
		frm.setAttribute('enctype', 'multipart/form-data');
		frm.innerHTML = '<input name="act" value="zip" />' +
			'<textarea name="files" id="ziptxt"></textarea>';
		frm.style.display = 'none';

		qsr('#widgeti>form');
		ebi('widgeti').appendChild(frm);
		var obj = ebi('ziptxt');
		obj.value = txt;
		console.log(txt);
		frm.submit();
	};
	r.render = function () {
		var tds = QSA('#files tbody td+td+td');
		for (var a = 0, aa = tds.length; a < aa; a++) {
			tds[a].onclick = r.seltgl;
		}
		r.selui(true);
		arcfmt.render();
		fileman.render();
		ebi('selzip').style.display = ebi('unsearch') ? 'none' : '';
	}
	return r;
})();


(function () {
	if (!window.FormData)
		return;

	var form = QS('#op_mkdir>form'),
		tb = QS('#op_mkdir input[name="name"]'),
		sf = mknod('div');

	clmod(sf, 'msg', 1);
	form.parentNode.appendChild(sf);

	form.onsubmit = function (e) {
		ev(e);
		clmod(sf, 'vis', 1);
		sf.textContent = 'creating "' + tb.value + '"...';

		var fd = new FormData();
		fd.append("act", "mkdir");
		fd.append("name", tb.value);

		var xhr = new XMLHttpRequest();
		xhr.vp = get_evpath();
		xhr.dn = tb.value;
		xhr.open('POST', xhr.vp, true);
		xhr.onreadystatechange = cb;
		xhr.responseType = 'text';
		xhr.send(fd);

		return false;
	};

	function cb() {
		if (this.readyState != XMLHttpRequest.DONE)
			return;

		if (this.vp !== get_evpath()) {
			sf.textContent = 'aborted due to location change';
			return;
		}

		if (this.status !== 200) {
			sf.textContent = 'error: ' + this.responseText;
			return;
		}

		tb.value = '';
		clmod(sf, 'vis');
		sf.textContent = '';
		treectl.goto(this.vp + uricom_enc(this.dn) + '/', true);
	}
})();


(function () {
	var form = QS('#op_msg>form'),
		tb = QS('#op_msg input[name="msg"]'),
		sf = mknod('div');

	clmod(sf, 'msg', 1);
	form.parentNode.appendChild(sf);

	form.onsubmit = function (e) {
		ev(e);
		clmod(sf, 'vis', 1);
		sf.textContent = 'sending...';

		var xhr = new XMLHttpRequest(),
			ct = 'application/x-www-form-urlencoded;charset=UTF-8';

		xhr.msg = tb.value;
		xhr.open('POST', get_evpath(), true);
		xhr.responseType = 'text';
		xhr.onreadystatechange = cb;
		xhr.setRequestHeader('Content-Type', ct);
		if (xhr.overrideMimeType)
			xhr.overrideMimeType('Content-Type', ct);

		xhr.send('msg=' + uricom_enc(xhr.msg));
		return false;
	};

	function cb() {
		if (this.readyState != XMLHttpRequest.DONE)
			return;

		if (this.status !== 200) {
			sf.textContent = 'error: ' + this.responseText;
			return;
		}

		tb.value = '';
		clmod(sf, 'vis');
		sf.textContent = 'sent: "' + this.msg + '"';
		setTimeout(function () {
			treectl.goto(get_evpath());
		}, 100);
	}
})();


function show_md(md, name, div, url, depth) {
	var errmsg = 'cannot show ' + name + ':\n\n',
		now = get_evpath();

	url = url || now;
	if (url != now)
		return;

	if (!window['marked']) {
		if (depth)
			return toast.warn(10, errmsg + 'failed to load marked.js')

		return import_js('/.cpr/deps/marked.js', function () {
			show_md(md, name, div, url, 1);
		});
	}

	try {
		clmod(div, 'mdo', 1);
		div.innerHTML = marked.parse(md, {
			headerPrefix: 'md-',
			breaks: true,
			gfm: true
		});
		var els = QSA('#epi a');
		for (var a = 0, aa = els.length; a < aa; a++) {
			var href = els[a].getAttribute('href');
			if (!href.startsWith('#') || href.startsWith('#md-'))
				continue;

			els[a].setAttribute('href', '#md-' + href.slice(1));
		}
		set_tabindex();
	}
	catch (ex) {
		toast.warn(10, errmsg + ex);
	}
}


function set_tabindex() {
	var els = QSA('pre');
	for (var a = 0, aa = els.length; a < aa; a++)
		els[a].setAttribute('tabindex', '0');
}


function show_readme(md) {
	if (!treectl.ireadme)
		return;

	show_md(md, 'README.md', ebi('epi'));
}
if (readme)
	show_readme(readme);


(function () {
	try {
		var tr = ebi('files').tBodies[0].rows;
		for (var a = 0; a < tr.length; a++) {
			var td = tr[a].cells[1],
				ao = td.firstChild,
				href = noq_href(ao),
				isdir = href.endsWith('/'),
				txt = ao.textContent;

			td.setAttribute('sortv', (isdir ? '\t' : '') + txt);
		}
	}
	catch (ex) { }
})();


function ev_row_tgl(e) {
	ev(e);
	filecols.toggle(this.parentElement.parentElement.getElementsByTagName('span')[0].textContent);
}


var unpost = (function () {
	ebi('op_unpost').innerHTML = (
		'you can delete your recent uploads below &ndash; <a id="unpost_refresh" href="#">refresh list</a>' +
		'<p>optional filter:&nbsp; URL must contain <input type="text" id="unpost_filt" size="20" /><a id="unpost_nofilt" href="#">clear filter</a></p>' +
		'<div id="unpost"></div>'
	);

	var r = {},
		ct = ebi('unpost'),
		filt = ebi('unpost_filt');

	r.files = [];
	r.me = null;

	r.load = function () {
		var me = Date.now(),
			html = [];

		function unpost_load_cb() {
			if (this.readyState != XMLHttpRequest.DONE)
				return;

			if (this.status !== 200) {
				var msg = this.responseText;
				toast.err(9, 'unpost-load failed:\n' + msg);
				ebi('op_unpost').innerHTML = html.join('\n');
				return;
			}

			var res = JSON.parse(this.responseText);
			if (res.length) {
				if (res.length == 2000)
					html.push("<p>showing first 2000 files (use the filter)");
				else
					html.push("<p>" + res.length + " uploads can be deleted");

				html.push(" &ndash; sorted by upload time &ndash; most recent first:</p>");
				html.push("<table><thead><tr><td></td><td>time</td><td>size</td><td>file</td></tr></thead><tbody>");
			}
			else
				html.push("<p>sike! no uploads " + (filt.value ? 'matching that filter' : '') + " are sufficiently recent</p>");

			var mods = [1000, 100, 10];
			for (var a = 0; a < res.length; a++) {
				for (var b = 0; b < mods.length; b++)
					if (a % mods[b] == 0 && res.length > a + mods[b] / 10)
						html.push(
							'<tr><td></td><td colspan="3" style="padding:.5em">' +
							'<a me="' + me + '" class="n' + a + '" n2="' + (a + mods[b]) +
							'" href="#">delete the next ' + Math.min(mods[b], res.length - a) + ' files below</a></td></tr>');
				html.push(
					'<tr><td><a me="' + me + '" class="n' + a + '" href="#">delete</a></td>' +
					'<td>' + unix2iso(res[a].at) + '</td>' +
					'<td>' + res[a].sz + '</td>' +
					'<td>' + linksplit(res[a].vp).join(' ') + '</td></tr>');
			}

			html.push("</tbody></table>");
			ct.innerHTML = html.join('\n');
			r.files = res;
			r.me = me;
		}

		var q = '/?ups';
		if (filt.value)
			q += '&filter=' + uricom_enc(filt.value, true);

		var xhr = new XMLHttpRequest();
		xhr.open('GET', q, true);
		xhr.onreadystatechange = unpost_load_cb;
		xhr.send();

		ct.innerHTML = "<p><em>loading your recent uploads...</em></p>";
	};

	function unpost_delete_cb() {
		if (this.readyState != XMLHttpRequest.DONE)
			return;

		if (this.status !== 200) {
			var msg = this.responseText;
			toast.err(9, 'unpost-delete failed:\n' + msg);
			return;
		}

		for (var a = this.n; a < this.n2; a++) {
			var o = QSA('#op_unpost a.n' + a);
			for (var b = 0; b < o.length; b++) {
				var o2 = o[b].closest('tr');
				o2.parentNode.removeChild(o2);
			}
		}
		toast.ok(5, this.responseText);

		if (!QS('#op_unpost a[me]'))
			ebi(goto_unpost());
	}

	ct.onclick = function (e) {
		var tgt = e.target.closest('a[me]');
		if (!tgt)
			return;

		if (!tgt.getAttribute('href'))
			return;

		ev(e);
		var ame = tgt.getAttribute('me');
		if (ame != r.me)
			return toast.err(0, 'something broke, please try a refresh');

		var n = parseInt(tgt.className.slice(1)),
			n2 = parseInt(tgt.getAttribute('n2') || n + 1),
			req = [];

		for (var a = n; a < n2; a++)
			if (QS('#op_unpost a.n' + a))
				req.push(uricom_dec(r.files[a].vp)[0]);

		var links = QSA('#op_unpost a.n' + n);
		for (var a = 0, aa = links.length; a < aa; a++) {
			links[a].removeAttribute('href');
			links[a].innerHTML = '[busy]';
		}

		toast.inf(0, "deleting " + req.length + " files...");

		var xhr = new XMLHttpRequest();
		xhr.n = n;
		xhr.n2 = n2;
		xhr.open('POST', '/?delete', true);
		xhr.onreadystatechange = unpost_delete_cb;
		xhr.send(JSON.stringify(req));
	};

	var tfilt = null;
	filt.oninput = function () {
		clearTimeout(tfilt);
		tfilt = setTimeout(r.load, 250);
	};

	ebi('unpost_nofilt').onclick = function (e) {
		ev(e);
		filt.value = '';
		r.load();
	};

	ebi('unpost_refresh').onclick = function (e) {
		ev(e);
		goto('unpost');
	};

	return r;
})();


function goto_unpost(e) {
	unpost.load();
}


function wintitle(txt) {
	document.title = (txt ? txt : '') + get_vpath().slice(1, -1).split('/').pop();
}


ebi('path').onclick = function (e) {
	var a = e.target.closest('a[href]');
	if (!treectl.spa || !a || !(a = a.getAttribute('href') + '') || !a.endsWith('/'))
		return;

	thegrid.setvis(true);
	treectl.reqls(a, true, true);
	return ev(e);
};


ebi('files').onclick = ebi('docul').onclick = function (e) {
	var tgt = e.target.closest('a[id]');
	if (tgt && tgt.getAttribute('id').indexOf('f-') === 0 && tgt.textContent.endsWith('/')) {
		var el = treectl.find(tgt.textContent.slice(0, -1));
		if (el) {
			el.click();
			return ev(e);
		}
		if (treectl.spa) {
			treectl.reqls(tgt.getAttribute('href'), true, true);
			return ev(e);
		}
		return;
	}

	tgt = e.target.closest('a[hl]');
	if (tgt) {
		showfile.show(noq_href(ebi(tgt.getAttribute('hl'))), tgt.getAttribute('lang'));
		return ev(e);
	}

	tgt = e.target.closest('a');
	if (tgt && tgt.closest('li.bn')) {
		thegrid.setvis(true);
		treectl.goto(tgt.getAttribute('href'), true);
		return ev(e);
	}
};


function reload_mp() {
	if (mp && mp.au) {
		audio_eq.stop();
		mp.au.pause();
		mp.au = null;
		mpl.unbuffer();
	}
	mpl.stop();
	var plays = QSA('tr>td:first-child>a.play');
	for (var a = plays.length - 1; a >= 0; a--)
		plays[a].parentNode.innerHTML = '-';

	mp = new MPlayer();
	audio_eq.acst = {};
	setTimeout(pbar.onresize, 1);
}


function reload_browser() {
	filecols.set_style();

	var parts = get_evpath().split('/'),
		rm = QSA('#path>a+a+a'),
		ftab = ebi('files'),
		link = '/', o;

	for (a = rm.length - 1; a >= 0; a--)
		rm[a].parentNode.removeChild(rm[a]);

	for (var a = 1; a < parts.length - 1; a++) {
		link += parts[a] + '/';
		o = mknod('a');
		o.setAttribute('href', link);
		o.textContent = uricom_dec(parts[a])[0];
		ebi('path').appendChild(o);
	}

	var oo = QSA('#files>tbody>tr>td:nth-child(3)');
	for (var a = 0, aa = oo.length; a < aa; a++) {
		var sz = oo[a].textContent.replace(/ +/g, ""),
			hsz = sz.replace(/\B(?=(\d{3})+(?!\d))/g, " ");

		oo[a].textContent = hsz;
	}

	reload_mp();
	try { showsort(ftab); } catch (ex) { }
	makeSortable(ftab, function () {
		thegrid.setdirty();
		mp.read_order();
	});

	for (var a = 0; a < 2; a++)
		clmod(ebi(a ? 'pro' : 'epi'), 'hidden', ebi('unsearch'));

	if (window['up2k'])
		up2k.set_fsearch();

	thegrid.setdirty();
	msel.render();
}
treectl.hydrate();
