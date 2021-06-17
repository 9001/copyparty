"use strict";

window.onerror = vis_exh;

function dbg(msg) {
	ebi('path').innerHTML = msg;
}


// add widget buttons
ebi('widget').innerHTML = (
	'<div id="wtoggle">' +
	'<span id="wzip"><a' +
	' href="#" id="selall" tt="select all files">sel.<br />all</a><a' +
	' href="#" id="selinv" tt="invert selection">sel.<br />inv.</a><a' +
	' href="#" id="selzip" tt="download selection as archive">zip</a>' +
	'</span><span id="wnp"><a' +
	' href="#" id="npirc" tt="copy irc-formatted track info">📋irc</a><a' +
	' href="#" id="nptxt" tt="copy plaintext track info">📋txt</a>' +
	'</span><a' +
	'	href="#" id="wtico">♫</a>' +
	'</div>' +
	'<div id="widgeti">' +
	'	<div id="pctl"><a href="#" id="bprev" tt="previous track$NHotkey: J">⏮</a><a href="#" id="bplay" tt="play/pause$NHotkey: P">▶</a><a href="#" id="bnext" tt="next track$NHotkey: L">⏭</a></div>' +
	'	<canvas id="pvol" width="288" height="38"></canvas>' +
	'	<canvas id="barpos"></canvas>' +
	'	<canvas id="barbuf"></canvas>' +
	'</div>'
);


var have_webp = null;
(function () {
	var img = new Image();
	img.onload = function () {
		have_webp = img.width > 0 && img.height > 0;
	};
	img.onerror = function () {
		have_webp = false;
	};
	img.src = "data:image/webp;base64,UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA==";
})();


var mpl = (function () {
	ebi('op_player').innerHTML = (
		'<div><h3>switches</h3><div>' +
		'<a href="#" class="tgl btn" id="au_preload" tt="start loading the next song near the end for gapless playback">preload</a>' +
		'<a href="#" class="tgl btn" id="au_npclip" tt="show buttons for clipboarding the currently playing song">/np clip</a>' +
		'</div></div>' +

		'<div><h3>playback mode</h3><div id="pb_mode">' +
		'<a href="#" class="tgl btn" tt="loop the open folder">🔁 loop-folder</a>' +
		'<a href="#" class="tgl btn" tt="load the next folder and continue">📂 next-folder</a>' +
		'</div></div>' +

		'<div><h3>audio equalizer</h3><div id="audio_eq"></div></div>');

	var r = {
		"pb_mode": sread('pb_mode') || 'loop-folder',
		"preload": bcfg_get('au_preload', true),
		"clip": bcfg_get('au_npclip', false)
	};

	ebi('au_preload').onclick = function (e) {
		ev(e);
		r.preload = !r.preload;
		bcfg_set('au_preload', r.preload);
	};

	ebi('au_npclip').onclick = function (e) {
		ev(e);
		r.clip = !r.clip;
		bcfg_set('au_npclip', r.clip);
		clmod(ebi('wtoggle'), 'np', r.clip && mp.au);
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
		r.pb_mode = this.textContent.split(' ').slice(-1)[0];
		swrite('pb_mode', r.pb_mode);
		draw_pb_mode();
	}

	return r;
})();


// extract songs + add play column
function MPlayer() {
	this.id = Date.now();
	this.au = null;
	this.au_native = null;
	this.au_native2 = null;
	this.au_ogvjs = null;
	this.au_ogvjs2 = null;
	this.tracks = {};
	this.order = [];

	var re_audio = /\.(opus|ogg|m4a|aac|mp3|wav|flac)$/i,
		trs = QSA('#files tbody tr');

	for (var a = 0, aa = trs.length; a < aa; a++) {
		var tds = trs[a].getElementsByTagName('td'),
			link = tds[1].getElementsByTagName('a');

		link = link[link.length - 1];
		var url = link.getAttribute('href'),
			m = re_audio.exec(url);

		if (m) {
			var tid = link.getAttribute('id');
			this.order.push(tid);
			this.tracks[tid] = url;
			tds[0].innerHTML = '<a id="a' + tid + '" href="#a' + tid + '" class="play">play</a></td>';
			ebi('a' + tid).onclick = ev_play;
		}
	}

	this.vol = sread('vol');
	if (this.vol !== null)
		this.vol = parseFloat(this.vol);
	else
		this.vol = 0.5;

	this.expvol = function () {
		return 0.5 * this.vol + 0.5 * this.vol * this.vol;
	};

	this.setvol = function (vol) {
		this.vol = Math.max(Math.min(vol, 1), 0);
		swrite('vol', vol);

		if (this.au)
			this.au.volume = this.expvol();
	};

	this.read_order = function () {
		var order = [],
			links = QSA('#files>tbody>tr>td:nth-child(1)>a');

		for (var a = 0, aa = links.length; a < aa; a++) {
			var tid = links[a].getAttribute('id');
			if (!tid || tid.indexOf('af-') !== 0)
				continue;

			order.push(tid.slice(1));
		}
		this.order = order;
	};

	this.preload = function (url) {
		var au = null;
		if (need_ogv_for(url)) {
			au = mp.au_ogvjs2;
			if (!au && window['OGVPlayer']) {
				au = new OGVPlayer();
				au.preload = "auto";
				this.au_ogvjs2 = au;
			}
		} else {
			au = mp.au_native2;
			if (!au) {
				au = new Audio();
				au.preload = "auto";
				this.au_native2 = au;
			}
		}
		if (au) {
			au.src = url + (url.indexOf('?') < 0 ? '?cache' : '&cache');
		}
	};
}

addcrc();
var mp = new MPlayer();
makeSortable(ebi('files'), mp.read_order.bind(mp));


// toggle player widget
var widget = (function () {
	var ret = {},
		widget = ebi('widget'),
		wtico = ebi('wtico'),
		nptxt = ebi('nptxt'),
		npirc = ebi('npirc'),
		touchmode = false,
		side_open = false,
		was_paused = true;

	ret.open = function () {
		if (side_open)
			return false;

		widget.className = 'open';
		side_open = true;
		return true;
	};
	ret.close = function () {
		if (!side_open)
			return false;

		widget.className = '';
		side_open = false;
		return true;
	};
	ret.toggle = function (e) {
		ret.open() || ret.close();
		ev(e);
		return false;
	};
	ret.paused = function (paused) {
		if (was_paused != paused) {
			was_paused = paused;
			ebi('bplay').innerHTML = paused ? '▶' : '⏸';
		}
	};
	wtico.onclick = function (e) {
		if (!touchmode)
			ret.toggle(e);

		return false;
	};
	npirc.onclick = nptxt.onclick = function (e) {
		ev(e);
		var th = ebi('files').tHead.rows[0].cells,
			tr = QS('#files tr.play').cells,
			irc = this.getAttribute('id') == 'npirc',
			ck = irc ? '06' : '',
			cv = irc ? '07' : '',
			m = ck + 'np: ';

		for (var a = 1, aa = th.length; a < aa; a++) {
			var tv = tr[a].textContent,
				tk = a == 1 ? '' : th[a].getAttribute('name').split('/').slice(-1)[0];

			m += tk + '(' + cv + tv + ck + ') // ';
		}

		m += '[' + cv + s2ms(mp.au.currentTime) + ck + '/' + cv + s2ms(mp.au.duration) + ck + ']';

		var o = document.createElement('input');
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
	return ret;
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

	function onresize() {
		r.buf = canvas_cfg(ebi('barbuf'));
		r.pos = canvas_cfg(ebi('barpos'));
		r.drawbuf();
		r.drawpos();
	}

	r.drawbuf = function () {
		if (!mp.au)
			return;

		var bc = r.buf,
			bctx = bc.ctx,
			sm = bc.w * 1.0 / mp.au.duration,
			gk = bc.h + '' + light;

		if (gradh != gk) {
			gradh = gk;
			grad = glossy_grad(bc, 85, [35, 40, 37, 35], light ? [45, 56, 50, 45] : [42, 51, 47, 42]);
		}
		bctx.fillStyle = grad;
		bctx.clearRect(0, 0, bc.w, bc.h);
		for (var a = 0; a < mp.au.buffered.length; a++) {
			var x1 = sm * mp.au.buffered.start(a),
				x2 = sm * mp.au.buffered.end(a);

			bctx.fillRect(x1, 0, x2 - x1, bc.h);
		}
	};

	r.drawpos = function () {
		if (!mp.au || isNaN(mp.au.duration) || isNaN(mp.au.currentTime))
			return;  // not-init || unsupp-codec

		var bc = r.buf,
			pc = r.pos,
			pctx = pc.ctx,
			sm = bc.w * 1.0 / mp.au.duration;

		pctx.clearRect(0, 0, pc.w, pc.h);
		pctx.fillStyle = light ? 'rgba(0,64,0,0.15)' : 'rgba(204,255,128,0.15)';
		for (var p = 1, mins = mp.au.duration / 10; p <= mins; p++)
			pctx.fillRect(Math.floor(sm * p * 10), 0, 2, pc.h);

		pctx.fillStyle = light ? 'rgba(0,64,0,0.5)' : 'rgba(192,255,96,0.5)';
		for (var p = 1, mins = mp.au.duration / 60; p <= mins; p++)
			pctx.fillRect(Math.floor(sm * p * 60), 0, 2, pc.h);

		var w = 8,
			x = sm * mp.au.currentTime;

		pctx.fillStyle = '#573'; pctx.fillRect((x - w / 2) - 1, 0, w + 2, pc.h);
		pctx.fillStyle = '#dfc'; pctx.fillRect((x - w / 2), 0, 8, pc.h);

		pctx.fillStyle = '#fff';
		pctx.font = '1em sans-serif';
		var txt = s2ms(mp.au.duration),
			tw = pctx.measureText(txt).width;

		pctx.fillText(txt, pc.w - (tw + 8), pc.h / 3 * 2);

		txt = s2ms(mp.au.currentTime);
		tw = pctx.measureText(txt).width;
		var gw = pctx.measureText("88:88::").width,
			xt = x < pc.w / 2 ? (x + 8) : (Math.min(pc.w - gw, x - 8) - tw);

		pctx.fillText(txt, xt, pc.h / 3 * 2);
	};

	window.addEventListener('resize', onresize);
	onresize();
	return r;
})();


// volume bar
var vbar = (function () {
	var r = {},
		gradh = -1,
		can, ctx, w, h, grad1, grad2;

	function onresize() {
		r.can = canvas_cfg(ebi('pvol'));
		can = r.can.can;
		ctx = r.can.ctx;
		w = r.can.w;
		h = r.can.h;
		r.draw();
	}

	r.draw = function () {
		var gh = h + '' + light;
		if (gradh != gh) {
			gradh = gh;
			grad1 = glossy_grad(r.can, 50, light ? [50, 55, 52, 48] : [45, 52, 47, 43], light ? [54, 60, 52, 47] : [42, 51, 47, 42]);
			grad2 = glossy_grad(r.can, 205, [10, 15, 13, 10], [16, 20, 18, 16]);
		}
		ctx.fillStyle = grad2; ctx.fillRect(0, 0, w, h);
		ctx.fillStyle = grad1; ctx.fillRect(0, 0, w * mp.vol, h);
	};
	window.addEventListener('resize', onresize);
	onresize();

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
	if (window.Touch) {
		can.ontouchstart = mousedown;
		can.ontouchmove = mousemove;
	}
	return r;
})();


function seek_au_mul(mul) {
	if (mp.au)
		seek_au_sec(mp.au.duration * mul);
}

function seek_au_sec(seek) {
	if (!mp.au)
		return;

	console.log('seek: ' + seek);
	if (!isFinite(seek))
		return;

	mp.au.currentTime = seek;

	// ogv.js breaks on .play() during playback
	if (mp.au === mp.au_native)
		mp.au.play();

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
	return song_skip(-1);
}


function playpause(e) {
	ev(e);
	if (mp.au) {
		if (mp.au.paused)
			mp.au.play();
		else
			mp.au.pause();

		mpui.progress_updater();
	}
	else
		play(0);
};


// hook up the widget buttons
(function () {
	ebi('bplay').onclick = playpause;
	ebi('bprev').onclick = prev_song;
	ebi('bnext').onclick = next_song;
	ebi('barpos').onclick = function (e) {
		if (!mp.au) {
			return play(0);
		}

		var rect = pbar.buf.can.getBoundingClientRect(),
			x = e.clientX - rect.left;

		seek_au_mul(x * 1.0 / rect.width);
	};
})();


// periodic tasks
var mpui = (function () {
	var r = {},
		nth = 0,
		timeout = null,
		preloaded = null;

	r.progress_updater = function () {
		clearTimeout(timeout);

		if (!mp.au) {
			widget.paused(true);
			return;
		}

		// indicate playback state in ui
		widget.paused(mp.au.paused);

		// draw current position in song
		if (!mp.au.paused)
			pbar.drawpos();

		// occasionally draw buffered regions
		if (++nth == 5) {
			pbar.drawbuf();
			nth = 0;
		}

		// preload next song
		if (mpl.preload && preloaded != mp.au.src) {
			var pos = mp.au.currentTime,
				len = mp.au.duration;

			if (pos > 0 && pos > len - 10) {
				preloaded = mp.au.src;
				try {
					mp.preload(ebi(mp.order[mp.order.indexOf(mp.au.tid) + 1]).href);
				}
				catch (ex) {
					console.log("preload failed", ex);
				}
			}
		}

		if (!mp.au.paused)
			timeout = setTimeout(r.progress_updater, 100);
	};
	r.progress_updater();
	return r;
})();


// event from play button next to a file in the list
function ev_play(e) {
	ev(e);
	play(this.getAttribute('id').slice(1));
	return false;
}


function setclass(id, clas) {
	ebi(id).setAttribute('class', clas);
}


var need_ogv = true;
try {
	need_ogv = new Audio().canPlayType('audio/ogg; codecs=opus') !== 'probably';

	if (/ Edge\//.exec(navigator.userAgent + ''))
		need_ogv = true;
}
catch (ex) { }


function need_ogv_for(url) {
	return need_ogv && /\.(ogg|opus)$/i.test(url);
}


var audio_eq = (function () {
	var r = {
		"en": false,
		"bands": [31.25, 62.5, 125, 250, 500, 1000, 2000, 4000, 8000, 16000],
		"gains": [4, 3, 2, 1, 0, 0, 1, 2, 3, 4],
		"filters": [],
		"amp": 0,
		"last_au": null
	};

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
		[8000 * 1.006, 0.73, 1.24],
		[16000 * 0.89, 0.7, 1.26],  // peak
		[16000 * 1.13, 0.82, 1.09],  // peak
		[16000 * 1.205, 0, 1.9]  // shelf
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

	r.apply = function () {
		r.draw();

		var Ctx = window.AudioContext || window.webkitAudioContext;
		if (!Ctx)
			bcfg_set('au_eq', false);

		if (!Ctx || !mp.au)
			return;

		if (!r.en && !mp.ac)
			return;

		if (mp.ac) {
			for (var a = 0; a < r.filters.length; a++)
				r.filters[a].disconnect();

			mp.acs.disconnect();
		}

		if (!mp.ac || mp.au != r.last_au) {
			if (mp.ac)
				mp.ac.close();

			r.last_au = mp.au;
			mp.ac = new Ctx();
			mp.acs = mp.ac.createMediaElementSource(mp.au);
		}

		r.filters = [];

		if (!r.en) {
			mp.acs.connect(mp.ac.destination);
			return;
		}

		var max = 0;
		for (var a = 0; a < r.gains.length; a++)
			if (max < r.gains[a])
				max = r.gains[a];

		var gains = []
		for (var a = 0; a < r.gains.length; a++)
			gains.push(r.gains[a] - max);

		var t = gains[gains.length - 1];
		gains.push(t);
		gains.push(t);
		gains.unshift(gains[0]);

		for (var a = 0; a < cfg.length; a++) {
			var fi = mp.ac.createBiquadFilter();
			fi.frequency.value = cfg[a][0];
			fi.gain.value = cfg[a][2] * gains[a];
			fi.Q.value = cfg[a][1];
			fi.type = a == 0 ? 'lowshelf' : a == cfg.length - 1 ? 'highshelf' : 'peaking';
			r.filters.push(fi);
		}

		// pregain, keep first in chain
		fi = mp.ac.createGain();
		fi.gain.value = r.amp + 0.94;  // +.137 dB measured; now -.25 dB and almost bitperfect
		r.filters.push(fi);

		for (var a = r.filters.length - 1; a >= 0; a--)
			r.filters[a].connect(a > 0 ? r.filters[a - 1] : mp.ac.destination);

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
				throw 42;

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
		'<a id="au_eq" class="tgl btn" href="#" tt="enables the equalizer and gain control">enable</a></td>'],
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

	r.en = bcfg_get('au_eq', false);
	ebi('au_eq').onclick = function (e) {
		ev(e);
		r.en = !r.en;
		bcfg_set('au_eq', r.en);
		r.apply();
	};

	r.draw();
	return r;
})();


// plays the tid'th audio file on the page
function play(tid, seek, call_depth) {
	if (mp.order.length == 0)
		return alert('no audio found wait what');

	var tn = tid;
	if ((tn + '').indexOf('f-') === 0)
		tn = mp.order.indexOf(tn);

	if (tn >= mp.order.length) {
		if (mpl.pb_mode == 'loop-folder') {
			tn = 0;
		}
		else if (mpl.pb_mode == 'next-folder') {
			treectl.ls_cb = next_song;
			return tree_neigh(1);
		}
	}

	if (tn < 0) {
		if (mpl.pb_mode == 'loop-folder') {
			tn = mp.order.length - 1;
		}
		else if (mpl.pb_mode == 'next-folder') {
			treectl.ls_cb = prev_song;
			return tree_neigh(-1);
		}
	}

	tid = mp.order[tn];

	if (mp.au) {
		mp.au.pause();
		setclass('a' + mp.au.tid, 'play');
	}

	// ogv.js breaks on .play() unless directly user-triggered
	var attempt_play = true;

	var url = mp.tracks[tid];
	if (need_ogv_for(url)) {
		if (mp.au_ogvjs) {
			mp.au = mp.au_ogvjs;
		}
		else if (window['OGVPlayer']) {
			mp.au = mp.au_ogvjs = new OGVPlayer();
			attempt_play = false;
			mp.au.addEventListener('error', evau_error, true);
			mp.au.addEventListener('progress', pbar.drawpos);
			mp.au.addEventListener('ended', next_song);
			widget.open();
		}
		else {
			if (call_depth !== undefined)
				return alert('failed to load ogv.js');

			show_modal('<h1>loading ogv.js</h1><h2>thanks apple</h2>');

			import_js('/.cpr/deps/ogv.js', function () {
				play(tid, seek, 1);
			});

			return;
		}
	}
	else {
		if (!mp.au_native) {
			mp.au = mp.au_native = new Audio();
			mp.au.addEventListener('error', evau_error, true);
			mp.au.addEventListener('progress', pbar.drawpos);
			mp.au.addEventListener('ended', next_song);
			widget.open();
		}
		mp.au = mp.au_native;
	}

	audio_eq.apply();

	mp.au.tid = tid;
	mp.au.src = url + (url.indexOf('?') < 0 ? '?cache' : '&cache');
	mp.au.volume = mp.expvol();
	var oid = 'a' + tid;
	setclass(oid, 'play act');
	var trs = ebi('files').getElementsByTagName('tbody')[0].getElementsByTagName('tr');
	for (var a = 0, aa = trs.length; a < aa; a++) {
		clmod(trs[a], 'play');
	}
	ebi(oid).parentElement.parentElement.className += ' play';
	clmod(ebi('wtoggle'), 'np', mpl.clip);
	if (window.thegrid)
		thegrid.loadsel();

	try {
		if (attempt_play)
			mp.au.play();

		if (mp.au.paused)
			autoplay_blocked(seek);
		else if (seek) {
			seek_au_sec(seek);
		}

		if (!seek) {
			var o = ebi(oid);
			o.setAttribute('id', 'thx_js');
			if (window.history && history.replaceState) {
				hist_replace(document.location.pathname + '#' + oid);
			}
			else {
				document.location.hash = oid;
			}
			o.setAttribute('id', oid);
		}

		mpui.progress_updater();
		pbar.drawbuf();
		return true;
	}
	catch (ex) {
		alert('playback failed: ' + ex);
	}
	setclass(oid, 'play');
	setTimeout(next_song, 500);
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
			break;
		default:
			err = 'Unknown Errol';
			break;
	}
	if (eplaya.error.message)
		err += '\n\n' + eplaya.error.message;

	err += '\n\nFile: «' + uricom_dec(eplaya.src.split('/').slice(-1)[0])[0] + '»';

	alert(err);
}


// show a fullscreen message
function show_modal(html) {
	var body = document.body || document.getElementsByTagName('body')[0],
		div = mknod('div');

	div.setAttribute('id', 'blocked');
	div.innerHTML = html;
	unblocked();
	body.appendChild(div);
}


// hide fullscreen message
function unblocked() {
	var dom = ebi('blocked');
	if (dom)
		dom.parentNode.removeChild(dom);
}


// show ui to manually start playback of a linked song
function autoplay_blocked(seek) {
	show_modal(
		'<div id="blk_play"><a href="#" id="blk_go"></a></div>' +
		'<div id="blk_abrt"><a href="#" id="blk_na">Cancel<br />(show file list)</a></div>');

	var go = ebi('blk_go'),
		na = ebi('blk_na'),
		fn = mp.tracks[mp.au.tid].split(/\//).pop();

	fn = uricom_dec(fn.replace(/\+/g, ' '))[0];

	go.textContent = 'Play "' + fn + '"';
	go.onclick = function (e) {
		if (e) e.preventDefault();
		unblocked();
		mp.au.play();
		if (seek)
			seek_au_sec(seek);
		else
			mpui.progress_updater();
	};
	na.onclick = unblocked;
}


// autoplay linked track
(function () {
	var v = location.hash;
	if (v && v.indexOf('#af-') === 0) {
		var id = v.slice(2).split('&');
		if (id[0].length != 10)
			return;

		if (id.length == 1)
			return play(id[0]);

		var m = /^[Tt=0]*([0-9]+[Mm:])?0*([0-9]+)[Ss]?$/.exec(id[1]);
		if (!m)
			return play(id[0]);

		return play(id[0], parseInt(m[1] || 0) * 60 + parseInt(m[2] || 0));
	}
})();


var thegrid = (function () {
	var lfiles = ebi('files'),
		gfiles = document.createElement('div');

	gfiles.setAttribute('id', 'gfiles');
	gfiles.style.display = 'none';
	gfiles.innerHTML = (
		'<div id="ghead">' +
		'<a href="#" class="tgl btn" id="gridsel" tt="enable file selection; ctrl-click a file to override$NHotkey: S">multiselect</a> &nbsp; zoom ' +
		'<a href="#" class="btn" z="-1.2" tt="Hotkey: A">&ndash;</a> ' +
		'<a href="#" class="btn" z="1.2" tt="Hotkey: D">+</a> &nbsp; sort by: ' +
		'<a href="#" s="href">name</a>, ' +
		'<a href="#" s="sz">size</a>, ' +
		'<a href="#" s="ts">date</a>, ' +
		'<a href="#" s="ext">type</a>' +
		'</div>' +
		'<div id="ggrid"></div>'
	);
	lfiles.parentNode.insertBefore(gfiles, lfiles);

	var r = {
		'thumbs': bcfg_get('thumbs', true),
		'en': bcfg_get('griden', false),
		'sel': bcfg_get('gridsel', false),
		'sz': fcfg_get('gridsz', 10),
		'isdirty': true,
		'bbox': null
	};

	ebi('thumbs').onclick = function (e) {
		ev(e);
		r.thumbs = !r.thumbs;
		bcfg_set('thumbs', r.thumbs);
		r.setdirty();
	};

	ebi('griden').onclick = function (e) {
		ev(e);
		r.en = !r.en;
		bcfg_set('griden', r.en);
		if (r.en) {
			loadgrid();
		}
		else {
			lfiles.style.display = '';
			gfiles.style.display = 'none';
		}
	};

	var btnclick = function (e) {
		ev(e);
		var s = this.getAttribute('s'),
			z = this.getAttribute('z');

		if (z)
			return setsz(z > 0 ? r.sz * z : r.sz / (-z));

		var t = lfiles.tHead.rows[0].cells;
		for (var a = 0; a < t.length; a++)
			if (t[a].getAttribute('name') == s) {
				t[a].click();
				break;
			}

		r.setdirty();
	};

	var links = QSA('#ghead>a');
	for (var a = 0; a < links.length; a++)
		links[a].onclick = btnclick;

	ebi('gridsel').onclick = function (e) {
		ev(e);
		r.sel = !r.sel;
		bcfg_set('gridsel', r.sel);
		r.loadsel();
	};

	r.setvis = function (vis) {
		(r.en ? gfiles : lfiles).style.display = vis ? '' : 'none';
	}

	r.setdirty = function () {
		r.dirty = true;
		if (r.en) {
			loadgrid();
		}
	}

	function setsz(v) {
		if (v !== undefined) {
			r.sz = v;
			swrite('gridsz', r.sz);
		}
		try {
			document.documentElement.style.setProperty('--grid-sz', r.sz + 'em');
		}
		catch (ex) { }
	}
	setsz();

	function seltgl(e) {
		if (e && e.ctrlKey)
			return true;

		ev(e);
		var oth = ebi(this.getAttribute('ref')),
			td = oth.parentNode.nextSibling,
			tr = td.parentNode;

		td.click();
		this.setAttribute('class', tr.getAttribute('class'));
	}

	function bgopen(e) {
		ev(e);
		var url = this.getAttribute('href');
		window.open(url, '_blank');
	}

	r.loadsel = function () {
		if (r.dirty)
			return;

		var ths = QSA('#ggrid>a'),
			have_sel = !!QS('#files tr.sel');

		for (var a = 0, aa = ths.length; a < aa; a++) {
			ths[a].onclick = r.sel ? seltgl : have_sel ? bgopen : null;
			ths[a].setAttribute('class', ebi(ths[a].getAttribute('ref')).parentNode.parentNode.getAttribute('class'));
		}
		var uns = QS('#ggrid a[ref="unsearch"]');
		if (uns)
			uns.onclick = function () {
				ebi('unsearch').click();
			};
	}

	function loadgrid() {
		if (have_webp === null)
			return setTimeout(loadgrid, 50);

		lfiles.style.display = 'none';
		gfiles.style.display = 'block';

		if (!r.dirty)
			return r.loadsel();

		var html = [];
		var files = QSA('#files>tbody>tr>td:nth-child(2) a[id]');
		for (var a = 0, aa = files.length; a < aa; a++) {
			var ao = files[a],
				href = esc(ao.getAttribute('href')),
				ref = ao.getAttribute('id'),
				isdir = href.split('?')[0].slice(-1)[0] == '/',
				ac = isdir ? ' class="dir"' : '',
				ihref = href;

			if (r.thumbs) {
				ihref += (ihref.indexOf('?') === -1 ? '?' : '&') + 'th=' + (have_webp ? 'w' : 'j');
			}
			else if (isdir) {
				ihref = '/.cpr/ico/folder';
			}
			else {
				var ar = href.split('?')[0].split('.');
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

			html.push('<a href="' + href + '" ref="' + ref + '"><img src="' +
				ihref + '" /><span' + ac + '>' + ao.innerHTML + '</span></a>');
		}
		ebi('ggrid').innerHTML = html.join('\n');
		r.dirty = false;
		r.bagit();
		r.loadsel();
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
					esc(uricom_dec(h.split('/').slice(-1)[0])[0]) + '</a>';
			}
		})[0];
	};

	setTimeout(function () {
		import_js('/.cpr/baguettebox.js', r.bagit);
	}, 1);

	if (r.en) {
		loadgrid();
	}

	return r;
})();


function tree_neigh(n) {
	var links = QSA('#treeul li>a+a');
	if (!links.length) {
		treectl.dir_cb = function () {
			tree_neigh(n);
		};
		treectl.entree();
		return;
	}
	var act = -1;
	for (var a = 0, aa = links.length; a < aa; a++) {
		if (links[a].getAttribute('class') == 'hl') {
			act = a;
			break;
		}
	}
	if (act == -1)
		return;

	act += n;
	if (act < 0)
		act = links.length - 1;
	if (act >= links.length)
		act = 0;

	links[act].click();
}


function tree_up() {
	var act = QS('#treeul a.hl');
	if (!act) {
		treectl.dir_cb = tree_up;
		treectl.entree();
		return;
	}
	if (act.previousSibling.textContent == '-')
		return act.previousSibling.click();

	act.parentNode.parentNode.parentNode.getElementsByTagName('a')[1].click();
}


document.onkeydown = function (e) {
	if (!document.activeElement || document.activeElement != document.body && document.activeElement.nodeName.toLowerCase() != 'a')
		return;

	if (e.ctrlKey || e.altKey || e.shiftKey || e.metaKey || e.isComposing)
		return;

	var k = (e.code + ''), pos = -1;
	if (k.indexOf('Digit') === 0)
		pos = parseInt(k.slice(-1)) * 0.1;

	if (pos !== -1)
		return seek_au_mul(pos);

	var n = k == 'KeyJ' ? -1 : k == 'KeyL' ? 1 : 0;
	if (n !== 0)
		return song_skip(n);

	if (k == 'KeyP')
		return playpause();

	n = k == 'KeyU' ? -10 : k == 'KeyO' ? 10 : 0;
	if (n !== 0)
		return mp.au ? seek_au_sec(mp.au.currentTime + n) : true;

	n = k == 'KeyI' ? -1 : k == 'KeyK' ? 1 : 0;
	if (n !== 0)
		return tree_neigh(n);

	if (k == 'KeyM')
		return tree_up();

	if (k == 'KeyB')
		//return treectl.hidden ? treectl.show() : treectl.hide();
		return treectl.hidden ? treectl.entree() : treectl.detree();

	if (k == 'KeyG')
		return ebi('griden').click();

	if (k == 'KeyT')
		return ebi('thumbs').click();

	if (thegrid.en) {
		if (k == 'KeyS')
			return ebi('gridsel').click();

		if (k == 'KeyA')
			return QSA('#ghead>a[z]')[0].click();

		if (k == 'KeyD')
			return QSA('#ghead>a[z]')[1].click();
	}
};


// search
(function () {
	var sconf = [
		["size",
			["szl", "sz_min", "minimum MiB", ""],
			["szu", "sz_max", "maximum MiB", ""]
		],
		["date",
			["dtl", "dt_min", "min. iso8601", ""],
			["dtu", "dt_max", "max. iso8601", ""]
		],
		["path",
			["path", "path", "path contains &nbsp; (space-separated)", "46"]
		],
		["name",
			["name", "name", "name contains &nbsp; (negate with -nope)", "46"]
		]
	];
	var oldcfg = [];

	if (QS('#srch_form.tags')) {
		sconf.push(["tags",
			["tags", "tags", "tags contains &nbsp; (^=start, end=$)", "46"]
		]);
		sconf.push(["adv.",
			["adv", "adv", "key>=1A&nbsp; key<=2B&nbsp; .bpm>165", "46"]
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
				'<br /><input id="' + hn + 'v" type="text" size="' + sconf[a][b][3] +
				'" name="' + sconf[a][b][1] + '" /></td>');
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

		clearTimeout(search_timeout);
		if (Date.now() - search_in_progress > 30 * 1000)
			search_timeout = setTimeout(do_search, 200);
	}

	function encode_query() {
		var q = '';
		for (var a = 0; a < sconf.length; a++) {
			for (var b = 1; b < sconf[a].length; b++) {
				var k = sconf[a][b][0],
					chk = 'srch_' + k + 'c',
					tvs = ebi('srch_' + k + 'v').value.split(/ /g);

				if (!ebi(chk).checked)
					continue;

				for (var c = 0; c < tvs.length; c++) {
					var tv = tvs[c];
					if (!tv.length)
						break;

					q += ' and ';

					if (k == 'adv') {
						q += tv.replace(/ /g, " and ").replace(/([=!><]=?)/, " $1 ");
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
		xhr.send(JSON.stringify({ "q": ebi('q_raw').value }));
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

		var html = mk_files_header(tagord);
		html.push('<tbody>');
		html.push('<tr><td>-</td><td colspan="42"><a href="#" id="unsearch">! close search results</a></td></tr>');
		for (var a = 0; a < res.hits.length; a++) {
			var r = res.hits[a],
				ts = parseInt(r.ts),
				sz = esc(r.sz + ''),
				rp = esc(r.rp + ''),
				ext = rp.lastIndexOf('.') > 0 ? rp.split('.').slice(-1)[0] : '%',
				links = linksplit(r.rp + '');

			if (ext.length > 8)
				ext = '%';

			links = links.join('');
			var nodes = ['<tr><td>-</td><td><div>' + links + '</div>', sz];
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

		ofiles.innerHTML = html.join('\n');
		ofiles.setAttribute("ts", this.ts);
		mukey.render();
		reload_browser();
		filecols.set_style(['File Name']);

		ebi('unsearch').onclick = unsearch;
	}

	function unsearch(e) {
		ev(e);
		treectl.show();
		ebi('files').innerHTML = orig_html;
		orig_html = null;
		msel.render();
		reload_browser();
	}
})();


var treectl = (function () {
	var treectl = {
		"hidden": true,
		"ls_cb": null,
		"dir_cb": null
	},
		entreed = false,
		fixedpos = false,
		prev_atop = null,
		prev_winh = null,
		dyn = bcfg_get('dyntree', true),
		treesz = icfg_get('treesz', 16);

	treesz = Math.min(Math.max(treesz, 4), 50);

	treectl.entree = function (e) {
		ev(e);
		entreed = true;
		swrite('entreed', 'tree');

		get_tree("", get_evpath(), true);
		treectl.show();
	}

	treectl.show = function () {
		treectl.hidden = false;
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

	treectl.detree = function (e) {
		ev(e);
		entreed = false;
		swrite('entreed', 'na');

		treectl.hide();
		ebi('path').style.display = 'inline-block';
	}

	treectl.hide = function () {
		treectl.hidden = true;
		ebi('path').style.display = 'none';
		ebi('tree').style.display = 'none';
		ebi('wrap').style.marginLeft = '0';
		window.removeEventListener('resize', onresize);
		window.removeEventListener('scroll', onscroll);
	}

	function onscroll() {
		if (!entreed || treectl.hidden)
			return;

		var tree = ebi('tree'),
			wrap = ebi('wrap'),
			atop = wrap.getBoundingClientRect().top,
			winh = window.innerHeight;

		if (atop === prev_atop && winh === prev_winh)
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
			var top = Math.max(0, parseInt(wrap.offsetTop)),
				treeh = winh - atop;

			tree.style.top = top + 'px';
			tree.style.height = treeh < 10 ? '' : treeh + 'px';
		}
	}

	function periodic() {
		onscroll();
		setTimeout(periodic, document.visibilityState ? 100 : 5000);
	}
	periodic();

	function onresize(e) {
		if (!entreed || treectl.hidden)
			return;

		var q = '#tree',
			nq = 0;

		while (dyn) {
			nq++;
			q += '>ul>li';
			if (!QS(q))
				break;
		}
		var w = treesz + nq;
		ebi('tree').style.width = w + 'em';
		ebi('wrap').style.marginLeft = w + 'em';
		onscroll();
	}

	treectl.goto = function (url, push) {
		get_tree("", url, true);
		reqls(url, push);
	}

	function get_tree(top, dst, rst) {
		var xhr = new XMLHttpRequest();
		xhr.top = top;
		xhr.dst = dst;
		xhr.rst = rst;
		xhr.ts = Date.now();
		xhr.open('GET', dst + '?tree=' + top, true);
		xhr.onreadystatechange = recvtree;
		xhr.send();
		enspin('#tree');
	}

	function recvtree() {
		if (this.readyState != XMLHttpRequest.DONE)
			return;

		if (this.status !== 200) {
			alert("http " + this.status + ": " + this.responseText);
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

		var fun = treectl.dir_cb;
		if (fun) {
			treectl.dir_cb = null;
			fun();
		}
	}

	function reload_tree() {
		var cdir = get_evpath(),
			links = QSA('#treeul a+a');

		for (var a = 0, aa = links.length; a < aa; a++) {
			var href = links[a].getAttribute('href');
			links[a].setAttribute('class', href == cdir ? 'hl' : '');
			links[a].onclick = treego;
		}
		links = QSA('#treeul li>a:first-child');
		for (var a = 0, aa = links.length; a < aa; a++) {
			links[a].setAttribute('dst', links[a].nextSibling.getAttribute('href'));
			links[a].onclick = treegrow;
		}
	}

	function treego(e) {
		ev(e);
		if (this.getAttribute('class') == 'hl' &&
			this.previousSibling.textContent == '-') {
			treegrow.call(this.previousSibling, e);
			return;
		}
		reqls(this.getAttribute('href'), true);
	}

	function reqls(url, hpush) {
		var xhr = new XMLHttpRequest();
		xhr.top = url;
		xhr.hpush = hpush;
		xhr.ts = Date.now();
		xhr.open('GET', xhr.top + '?ls', true);
		xhr.onreadystatechange = recvls;
		xhr.send();
		if (hpush)
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
			alert("http " + this.status + ": " + this.responseText);
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

		var top = this.top,
			nodes = res.dirs.concat(res.files),
			html = mk_files_header(res.taglist);

		html.push('<tbody>');
		nodes = sortfiles(nodes);
		for (var a = 0; a < nodes.length; a++) {
			var r = nodes[a],
				hname = esc(uricom_dec(r.href)[0]),
				sortv = (r.href.slice(-1) == '/' ? '\t' : '') + hname,
				ln = ['<tr><td>' + r.lead + '</td><td sortv="' + sortv +
					'"><a href="' + top + r.href + '">' + hname + '</a>', r.sz];

			for (var b = 0; b < res.taglist.length; b++) {
				var k = res.taglist[b],
					v = (r.tags || {})[k] || "";

				if (k == ".dur") {
					var sv = v ? s2ms(v) : "";
					ln[ln.length - 1] += '</td><td sortv="' + v + '">' + sv;
					continue;
				}
				ln.push(v);
			}
			ln = ln.concat([r.ext, unix2iso(r.ts)]).join('</td><td>');
			html.push(ln + '</td></tr>');
		}
		html.push('</tbody>');
		html = html.join('\n');
		ebi('files').innerHTML = html;

		if (this.hpush)
			hist_push(this.top);

		apply_perms(res.perms);
		despin('#files');
		despin('#gfiles');

		ebi('pro').innerHTML = res.logues ? res.logues[0] || "" : "";
		ebi('epi').innerHTML = res.logues ? res.logues[1] || "" : "";

		document.title = '⇆🎉 ' + uricom_dec(document.location.pathname.slice(1, -1))[0];

		filecols.set_style();
		mukey.render();
		msel.render();
		reload_tree();
		reload_browser();

		var fun = treectl.ls_cb;
		if (fun) {
			treectl.ls_cb = null;
			fun();
		}
	}

	function parsetree(res, top) {
		var ret = '';
		for (var a = 0; a < res.a.length; a++) {
			if (res.a[a] !== '')
				res['k' + res.a[a]] = 0;
		}
		delete res['a'];
		var keys = Object.keys(res);
		keys.sort();
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

	function dyntree(e) {
		ev(e);
		dyn = !dyn;
		bcfg_set('dyntree', dyn);
		onresize();
	}

	function scaletree(e) {
		ev(e);
		treesz += parseInt(this.getAttribute("step"));
		if (isNaN(treesz))
			treesz = 16;

		swrite('treesz', treesz);
		onresize();
	}

	ebi('entree').onclick = treectl.entree;
	ebi('detree').onclick = treectl.detree;
	ebi('dyntree').onclick = dyntree;
	ebi('twig').onclick = scaletree;
	ebi('twobytwo').onclick = scaletree;
	if (sread('entreed') == 'tree')
		treectl.entree();

	window.onpopstate = function (e) {
		console.log("h-pop " + e.state);
		if (!e.state)
			return;

		var url = new URL(e.state, "https://" + document.location.host);
		treectl.goto(url.pathname);
	};

	if (window.history && history.pushState) {
		hist_replace(get_evpath() + window.location.hash);
	}

	treectl.onscroll = onscroll;
	return treectl;
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


function apply_perms(perms) {
	perms = perms || [];

	var o = QSA('#ops>a[data-perm], #u2footfoot');
	for (var a = 0; a < o.length; a++) {
		var display = 'inline';
		var needed = o[a].getAttribute('data-perm').split(' ');
		for (var b = 0; b < needed.length; b++) {
			if (!has(perms, needed[b])) {
				display = 'none';
			}
		}
		o[a].style.display = display;
	}

	var act = QS('#ops>a.act');
	if (act && act.style.display === 'none')
		goto();

	document.body.setAttribute('perms', perms.join(' '));

	var have_write = has(perms, "write"),
		have_read = has(perms, "read"),
		tds = QSA('#u2conf td');

	for (var a = 0; a < tds.length; a++) {
		tds[a].style.display =
			(have_write || tds[a].getAttribute('data-perm') == 'read') ?
				'table-cell' : 'none';
	}

	if (window['up2k'])
		up2k.set_fsearch();

	ebi('widget').style.display = have_read ? '' : 'none';
	thegrid.setvis(have_read);
	if (!have_read)
		goto('up2k');
}


function find_file_col(txt) {
	var i = -1,
		min = false,
		tds = ebi('files').tHead.getElementsByTagName('th');

	for (var a = 0; a < tds.length; a++) {
		var spans = tds[a].getElementsByTagName('span');
		if (spans.length && spans[0].textContent == txt) {
			min = tds[a].getAttribute('class').indexOf('min') !== -1;
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
	var hidden = jread('filecols', []);

	var add_btns = function () {
		var ths = QSA('#files th>span');
		for (var a = 0, aa = ths.length; a < aa; a++) {
			var th = ths[a].parentElement;
			th.innerHTML = '<div class="cfg"><a href="#">-</a></div>' + ths[a].outerHTML;
			th.getElementsByTagName('a')[0].onclick = ev_row_tgl;
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
			html.push('<a href="#" class="btn">' + esc(hidden[a]) + '</a>');
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


function addcrc() {
	var links = QSA(
		'#files>tbody>tr>td:first-child+td>' + (
			ebi('unsearch') ? 'div>a:last-child' : 'a'));

	for (var a = 0, aa = links.length; a < aa; a++)
		if (!links[a].getAttribute('id')) {
			var crc = crc32(links[a].textContent || links[a].innerText);
			crc = ('00000000' + crc).slice(-8);
			links[a].setAttribute('id', 'f-' + crc);
		}
}


var light;
(function () {
	light = bcfg_get('lightmode', false);

	function freshen() {
		document.documentElement.setAttribute("class", light ? "light" : "");
		pbar.drawbuf();
		pbar.drawpos();
		vbar.draw();
	}

	ebi('lightmode').onclick = function (e) {
		ev(e);
		light = !light;
		bcfg_set('lightmode', light);
		freshen();
	};

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
			["zip_crc", "zip=crc", "cp437 with crc32 computed early for truly ancient software$N(takes longer to process before download can start)"]
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
				throw 'missing arg in url';

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
	function getsel() {
		var names = [],
			links = QSA('#files tbody tr.sel td:nth-child(2) a');

		for (var a = 0, aa = links.length; a < aa; a++)
			names.push(links[a].getAttribute('href').replace(/\/$/, "").split('/').slice(-1));

		return names;
	}
	function selui() {
		clmod(ebi('wtoggle'), 'sel', getsel().length);
		thegrid.loadsel();
	}
	function seltgl(e) {
		ev(e);
		var tr = this.parentNode;
		clmod(tr, 'sel', 't');
		selui();
	}
	function evsel(e, fun) {
		ev(e);
		var trs = QSA('#files tbody tr');
		for (var a = 0, aa = trs.length; a < aa; a++)
			clmod(trs[a], 'sel', fun);
		selui();
	}
	ebi('selall').onclick = function (e) {
		evsel(e, "add");
	};
	ebi('selinv').onclick = function (e) {
		evsel(e, "t");
	};
	ebi('selzip').onclick = function (e) {
		ev(e);
		var names = getsel(),
			arg = ebi('selzip').getAttribute('fmt'),
			txt = names.join('\n'),
			frm = mknod('form');

		frm.setAttribute('action', '?' + arg);
		frm.setAttribute('method', 'post');
		frm.setAttribute('target', '_blank');
		frm.setAttribute('enctype', 'multipart/form-data');
		frm.innerHTML = '<input name="act" value="zip" />' +
			'<textarea name="files" id="ziptxt"></textarea>';
		frm.style.display = 'none';

		var oldform = QS('#widgeti>form');
		if (oldform)
			oldform.parentNode.removeChild(oldform);

		ebi('widgeti').appendChild(frm);
		var obj = ebi('ziptxt');
		obj.value = txt;
		console.log(txt);
		frm.submit();
	};
	function render() {
		var tds = QSA('#files tbody td+td+td');
		for (var a = 0, aa = tds.length; a < aa; a++) {
			tds[a].onclick = seltgl;
		}
		arcfmt.render();
	}
	return {
		"render": render
	};
})();


(function () {
	try {
		var tr = ebi('files').tBodies[0].rows;
		for (var a = 0; a < tr.length; a++) {
			var td = tr[a].cells[1],
				ao = td.firstChild,
				href = ao.getAttribute('href'),
				isdir = href.split('?')[0].slice(-1)[0] == '/',
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


function reload_mp() {
	if (mp && mp.au) {
		mp.au.pause();
		mp.au = null;
	}
	widget.close();
	mp = new MPlayer();
}


function reload_browser(not_mp) {
	filecols.set_style();

	var parts = get_evpath().split('/'),
		rm = QSA('#path>a+a+a');

	for (a = rm.length - 1; a >= 0; a--)
		rm[a].parentNode.removeChild(rm[a]);

	var link = '/';
	for (var a = 1; a < parts.length - 1; a++) {
		link += parts[a] + '/';
		var o = mknod('a');
		o.setAttribute('href', link);
		o.textContent = uricom_dec(parts[a])[0];
		ebi('path').appendChild(o);
	}

	var oo = QSA('#files>tbody>tr>td:nth-child(3)');
	for (var a = 0, aa = oo.length; a < aa; a++) {
		var sz = oo[a].textContent.replace(/ /g, ""),
			hsz = sz.replace(/\B(?=(\d{3})+(?!\d))/g, " ");

		oo[a].textContent = hsz;
	}

	if (!not_mp) {
		addcrc();
		reload_mp();
		makeSortable(ebi('files'), mp.read_order.bind(mp));
	}

	if (window['up2k'])
		up2k.set_fsearch();

	thegrid.setdirty();
}
reload_browser(true);
mukey.render();
msel.render();
