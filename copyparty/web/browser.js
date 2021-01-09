"use strict";

window.onerror = vis_exh;

function dbg(msg) {
	ebi('path').innerHTML = msg;
}

function ev(e) {
	e = e || window.event;

	if (e.preventDefault)
		e.preventDefault()

	if (e.stopPropagation)
		e.stopPropagation();

	e.returnValue = false;
	return e;
}

makeSortable(ebi('files'));


// extract songs + add play column
var mp = (function () {
	var tracks = [];
	var ret = {
		'au': null,
		'au_native': null,
		'au_ogvjs': null,
		'tracks': tracks,
		'cover_url': ''
	};
	var re_audio = /\.(opus|ogg|m4a|aac|mp3|wav|flac)$/i;

	var trs = ebi('files').getElementsByTagName('tbody')[0].getElementsByTagName('tr');
	for (var a = 0, aa = trs.length; a < aa; a++) {
		var tds = trs[a].getElementsByTagName('td');
		var link = tds[1].getElementsByTagName('a')[0];
		var url = link.getAttribute('href');

		var m = re_audio.exec(url);
		if (m) {
			var ntrack = tracks.length;
			tracks.push(url);

			tds[0].innerHTML = '<a id="trk' + ntrack + '" href="#trk' + ntrack + '" class="play">play</a></td>';
		}
	}

	for (var a = 0, aa = tracks.length; a < aa; a++)
		ebi('trk' + a).onclick = ev_play;

	ret.vol = localStorage.getItem('vol');
	if (ret.vol !== null)
		ret.vol = parseFloat(ret.vol);
	else
		ret.vol = 0.5;

	ret.expvol = function () {
		return 0.5 * ret.vol + 0.5 * ret.vol * ret.vol;
	};

	ret.setvol = function (vol) {
		ret.vol = Math.max(Math.min(vol, 1), 0);
		localStorage.setItem('vol', vol);

		if (ret.au)
			ret.au.volume = ret.expvol();
	};

	return ret;
})();


// toggle player widget
var widget = (function () {
	var ret = {};
	var widget = ebi('widget');
	var wtoggle = ebi('wtoggle');
	var touchmode = false;
	var side_open = false;
	var was_paused = true;

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
	var click_handler = function (e) {
		if (!touchmode)
			ret.toggle(e);

		return false;
	};
	if (window.Touch) {
		var touch_handler = function (e) {
			touchmode = true;
			return ret.toggle(e);
		};
		wtoggle.addEventListener('touchstart', touch_handler, false);
	}
	wtoggle.onclick = click_handler;
	return ret;
})();


// buffer/position bar
var pbar = (function () {
	var r = {};
	r.bcan = ebi('barbuf');
	r.pcan = ebi('barpos');
	r.bctx = r.bcan.getContext('2d');
	r.pctx = r.pcan.getContext('2d');

	var bctx = r.bctx;
	var pctx = r.pctx;
	var scale = (window.devicePixelRatio || 1) / (
		bctx.webkitBackingStorePixelRatio ||
		bctx.mozBackingStorePixelRatio ||
		bctx.msBackingStorePixelRatio ||
		bctx.oBackingStorePixelRatio ||
		bctx.BackingStorePixelRatio || 1);

	var gradh = 0;
	var grad = null;

	r.drawbuf = function () {
		var cs = getComputedStyle(r.bcan);
		var sw = parseInt(cs['width']);
		var sh = parseInt(cs['height']);
		var sm = sw * 1.0 / mp.au.duration;

		r.bcan.width = (sw * scale);
		r.bcan.height = (sh * scale);
		bctx.setTransform(scale, 0, 0, scale, 0, 0);

		if (!grad || gradh != sh) {
			grad = bctx.createLinearGradient(0, 0, 0, sh);
			grad.addColorStop(0, 'hsl(85,35%,42%)');
			grad.addColorStop(0.49, 'hsl(85,40%,49%)');
			grad.addColorStop(0.50, 'hsl(85,37%,47%)');
			grad.addColorStop(1, 'hsl(85,35%,42%)');
			gradh = sh;
		}
		bctx.fillStyle = grad;
		bctx.clearRect(0, 0, sw, sh);
		for (var a = 0; a < mp.au.buffered.length; a++) {
			var x1 = sm * mp.au.buffered.start(a);
			var x2 = sm * mp.au.buffered.end(a);
			bctx.fillRect(x1, 0, x2 - x1, sh);
		}
	};
	r.drawpos = function () {
		var cs = getComputedStyle(r.bcan);
		var sw = parseInt(cs['width']);
		var sh = parseInt(cs['height']);
		var sm = sw * 1.0 / mp.au.duration;

		r.pcan.width = (sw * scale);
		r.pcan.height = (sh * scale);
		pctx.setTransform(scale, 0, 0, scale, 0, 0);
		pctx.clearRect(0, 0, sw, sh);

		var w = 8;
		var x = sm * mp.au.currentTime;
		pctx.fillStyle = '#573'; pctx.fillRect((x - w / 2) - 1, 0, w + 2, sh);
		pctx.fillStyle = '#dfc'; pctx.fillRect((x - w / 2), 0, 8, sh);
	};
	return r;
})();


// volume bar
var vbar = (function () {
	var r = {};
	r.can = ebi('pvol');
	r.ctx = r.can.getContext('2d');

	var bctx = r.ctx;
	var scale = (window.devicePixelRatio || 1) / (
		bctx.webkitBackingStorePixelRatio ||
		bctx.mozBackingStorePixelRatio ||
		bctx.msBackingStorePixelRatio ||
		bctx.oBackingStorePixelRatio ||
		bctx.BackingStorePixelRatio || 1);

	var gradh = 0;
	var grad1 = null;
	var grad2 = null;

	r.draw = function () {
		var cs = getComputedStyle(r.can);
		var sw = parseInt(cs['width']);
		var sh = parseInt(cs['height']);

		r.can.width = (sw * scale);
		r.can.height = (sh * scale);
		bctx.setTransform(scale, 0, 0, scale, 0, 0);

		if (!grad1 || gradh != sh) {
			gradh = sh;

			grad1 = bctx.createLinearGradient(0, 0, 0, sh);
			grad1.addColorStop(0, 'hsl(50,45%,42%)');
			grad1.addColorStop(0.49, 'hsl(50,50%,49%)');
			grad1.addColorStop(0.50, 'hsl(50,47%,47%)');
			grad1.addColorStop(1, 'hsl(50,45%,42%)');

			grad2 = bctx.createLinearGradient(0, 0, 0, sh);
			grad2.addColorStop(0, 'hsl(205,10%,16%)');
			grad2.addColorStop(0.49, 'hsl(205,15%,20%)');
			grad2.addColorStop(0.50, 'hsl(205,13%,18%)');
			grad2.addColorStop(1, 'hsl(205,10%,16%)');
		}
		bctx.fillStyle = grad2; bctx.fillRect(0, 0, sw, sh);
		bctx.fillStyle = grad1; bctx.fillRect(0, 0, sw * mp.vol, sh);
	};

	var rect;
	function mousedown(e) {
		rect = r.can.getBoundingClientRect();
		mousemove(e);
	}
	function mousemove(e) {
		if (e.changedTouches && e.changedTouches.length > 0) {
			e = e.changedTouches[0];
		}
		else if (e.buttons === 0) {
			r.can.onmousemove = null;
			return;
		}

		var x = e.clientX - rect.left;
		var mul = x * 1.0 / rect.width;
		if (mul > 0.98)
			mul = 1;

		mp.setvol(mul);
		r.draw();
	}
	r.can.onmousedown = function (e) {
		if (e.button !== 0)
			return;

		r.can.onmousemove = mousemove;
		mousedown(e);
	};
	r.can.onmouseup = function (e) {
		if (e.button === 0)
			r.can.onmousemove = null;
	};
	if (window.Touch) {
		r.can.ontouchstart = mousedown;
		r.can.ontouchmove = mousemove;
	}
	r.draw();
	return r;
})();


// hook up the widget buttons
(function () {
	var bskip = function (n) {
		var tid = null;
		if (mp.au)
			tid = mp.au.tid;

		if (tid !== null)
			play(tid + n);
		else
			play(0);
	};
	ebi('bplay').onclick = function (e) {
		ev(e);
		if (mp.au) {
			if (mp.au.paused)
				mp.au.play();
			else
				mp.au.pause();
		}
		else
			play(0);
	};
	ebi('bprev').onclick = function (e) {
		ev(e);
		bskip(-1);
	};
	ebi('bnext').onclick = function (e) {
		ev(e);
		bskip(1);
	};
	ebi('barpos').onclick = function (e) {
		if (!mp.au) {
			//dbg((new Date()).getTime());
			return play(0);
		}

		var rect = pbar.pcan.getBoundingClientRect();
		var x = e.clientX - rect.left;
		var mul = x * 1.0 / rect.width;
		var seek = mp.au.duration * mul;
		console.log('seek: ' + seek);
		if (!isFinite(seek))
			return;

		mp.au.currentTime = seek;

		if (mp.au === mp.au_native)
			// hack: ogv.js breaks on .play() during playback
			mp.au.play();
	};
})();


// periodic tasks
(function () {
	var nth = 0;
	var last_skip_url = '';
	var progress_updater = function () {
		if (!mp.au) {
			widget.paused(true);
		}
		else {
			// indicate playback state in ui
			widget.paused(mp.au.paused);

			// draw current position in song
			if (!mp.au.paused)
				pbar.drawpos();

			// occasionally draw buffered regions
			if (++nth == 10) {
				pbar.drawbuf();
				nth = 0;
			}

			// switch to next track if approaching the end
			if (last_skip_url != mp.au.src) {
				var pos = mp.au.currentTime;
				var len = mp.au.duration;
				if (pos > 0 && pos > len - 0.1) {
					last_skip_url = mp.au.src;
					play(mp.au.tid + 1);
				}
			}
		}
		setTimeout(progress_updater, 100);
	};
	progress_updater();
})();


// event from play button next to a file in the list
function ev_play(e) {
	ev(e);
	play(parseInt(this.getAttribute('id').substr(3)));
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


// plays the tid'th audio file on the page
function play(tid, call_depth) {
	if (mp.tracks.length == 0)
		return alert('no audio found wait what');

	while (tid >= mp.tracks.length)
		tid -= mp.tracks.length;

	while (tid < 0)
		tid += mp.tracks.length;

	if (mp.au) {
		mp.au.pause();
		setclass('trk' + mp.au.tid, 'play');
	}

	// ogv.js breaks on .play() unless directly user-triggered
	var hack_attempt_play = true;

	var url = mp.tracks[tid];
	if (need_ogv && /\.(ogg|opus)$/i.test(url)) {
		if (mp.au_ogvjs) {
			mp.au = mp.au_ogvjs;
		}
		else if (window['OGVPlayer']) {
			mp.au = mp.au_ogvjs = new OGVPlayer();
			hack_attempt_play = false;
			mp.au.addEventListener('error', evau_error, true);
			mp.au.addEventListener('progress', pbar.drawpos, false);
			widget.open();
		}
		else {
			if (call_depth !== undefined)
				return alert('failed to load ogv.js');

			show_modal('<h1>loading ogv.js</h1><h2>thanks apple</h2>');

			import_js('/.cpr/deps/ogv.js', function () {
				play(tid, 1);
			});

			return;
		}
	}
	else {
		if (!mp.au_native) {
			mp.au = mp.au_native = new Audio();
			mp.au.addEventListener('error', evau_error, true);
			mp.au.addEventListener('progress', pbar.drawpos, false);
			widget.open();
		}
		mp.au = mp.au_native;
	}

	mp.au.tid = tid;
	mp.au.src = url;
	mp.au.volume = mp.expvol();
	var oid = 'trk' + tid;
	setclass(oid, 'play act');

	try {
		if (hack_attempt_play)
			mp.au.play();

		if (mp.au.paused)
			autoplay_blocked();

		var o = ebi(oid);
		o.setAttribute('id', 'thx_js');
		location.hash = oid;
		o.setAttribute('id', oid);

		pbar.drawbuf();
		return true;
	}
	catch (ex) {
		alert('playback failed: ' + ex);
	}
	setclass('trk' + mp.au.tid, 'play');
	setTimeout('play(' + (mp.au.tid + 1) + ');', 500);
}


// event from the audio object if something breaks
function evau_error(e) {
	var err = '';
	var eplaya = (e && e.target) || (window.event && window.event.srcElement);

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

	err += '\n\nFile: «' + decodeURIComponent(eplaya.src.split('/').slice(-1)[0]) + '»';

	alert(err);
}


// show a fullscreen message
function show_modal(html) {
	var body = document.body || document.getElementsByTagName('body')[0];
	var div = document.createElement('div');
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
function autoplay_blocked() {
	show_modal(
		'<div id="blk_play"><a href="#" id="blk_go"></a></div>' +
		'<div id="blk_abrt"><a href="#" id="blk_na">Cancel<br />(show file list)</a></div>');

	var go = ebi('blk_go');
	var na = ebi('blk_na');

	var fn = mp.tracks[mp.au.tid].split(/\//).pop();
	fn = decodeURIComponent(fn.replace(/\+/g, ' '));

	go.textContent = 'Play "' + fn + '"';
	go.onclick = function (e) {
		if (e) e.preventDefault();
		unblocked();
		mp.au.play();
	};
	na.onclick = unblocked;
}


// autoplay linked track
(function () {
	var v = location.hash;
	if (v && v.length > 4 && v.indexOf('#trk') === 0)
		play(parseInt(v.substr(4)));
})();


//widget.open();
