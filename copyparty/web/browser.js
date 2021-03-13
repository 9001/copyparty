"use strict";

window.onerror = vis_exh;

function dbg(msg) {
	ebi('path').innerHTML = msg;
}

makeSortable(ebi('files'), reload_mp);


// extract songs + add play column
function init_mp() {
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
		var link = tds[1].getElementsByTagName('a');
		link = link[link.length - 1];
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

	ret.vol = sread('vol');
	if (ret.vol !== null)
		ret.vol = parseFloat(ret.vol);
	else
		ret.vol = 0.5;

	ret.expvol = function () {
		return 0.5 * ret.vol + 0.5 * ret.vol * ret.vol;
	};

	ret.setvol = function (vol) {
		ret.vol = Math.max(Math.min(vol, 1), 0);
		swrite('vol', vol);

		if (ret.au)
			ret.au.volume = ret.expvol();
	};

	return ret;
}
var mp = init_mp();


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
		if (!mp.au)
			return;

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
		if (!mp.au)
			return;

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
	var trs = ebi('files').getElementsByTagName('tbody')[0].getElementsByTagName('tr');
	for (var a = 0, aa = trs.length; a < aa; a++) {
		trs[a].className = trs[a].className.replace(/ *play */, "");
	}
	ebi(oid).parentElement.parentElement.className += ' play';

	try {
		if (hack_attempt_play)
			mp.au.play();

		if (mp.au.paused)
			autoplay_blocked();

		var o = ebi(oid);
		o.setAttribute('id', 'thx_js');
		if (window.history && history.replaceState) {
			hist_replace(document.location.pathname + '#' + oid);
		}
		else {
			document.location.hash = oid;
		}
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

	err += '\n\nFile: «' + uricom_dec(eplaya.src.split('/').slice(-1)[0])[0] + '»';

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
	fn = uricom_dec(fn.replace(/\+/g, ' '))[0];

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

	if (document.querySelector('#srch_form.tags'))
		sconf.push(["tags",
			["tags", "tags", "tags contains &nbsp; (^=start, end=$)", "46"]
		]);

	var html = [];
	var orig_html = null;
	for (var a = 0; a < sconf.length; a++) {
		html.push('<tr><td><br />' + sconf[a][0] + '</td>');
		for (var b = 1; b < 3; b++) {
			var hn = "srch_" + sconf[a][b][0];
			var csp = (sconf[a].length == 2) ? 2 : 1;
			html.push(
				'<td colspan="' + csp + '"><input id="' + hn + 'c" type="checkbox">\n' +
				'<label for="' + hn + 'c">' + sconf[a][b][2] + '</label>\n' +
				'<br /><input id="' + hn + 'v" type="text" size="' + sconf[a][b][3] +
				'" name="' + sconf[a][b][1] + '" /></td>');
			if (csp == 2)
				break;
		}
		html.push('</tr>');
	}
	ebi('srch_form').innerHTML = html.join('\n');

	var o = document.querySelectorAll('#op_search input');
	for (var a = 0; a < o.length; a++) {
		o[a].oninput = ev_search_input;
	}

	var search_timeout;

	function ev_search_input() {
		var v = this.value;
		var id = this.getAttribute('id');
		if (id.slice(-1) == 'v') {
			var chk = ebi(id.slice(0, -1) + 'c');
			chk.checked = ((v + '').length > 0);
		}
		clearTimeout(search_timeout);
		search_timeout = setTimeout(do_search, 100);
	}

	function do_search() {
		clearTimeout(search_timeout);
		var params = {};
		var o = document.querySelectorAll('#op_search input[type="text"]');
		for (var a = 0; a < o.length; a++) {
			var chk = ebi(o[a].getAttribute('id').slice(0, -1) + 'c');
			if (!chk.checked)
				continue;

			params[o[a].getAttribute('name')] = o[a].value;
		}
		// ebi('srch_q').textContent = JSON.stringify(params, null, 4);
		var xhr = new XMLHttpRequest();
		xhr.open('POST', '/?srch', true);
		xhr.onreadystatechange = xhr_search_results;
		xhr.ts = new Date().getTime();
		xhr.send(JSON.stringify(params));
	}

	function xhr_search_results() {
		if (this.readyState != XMLHttpRequest.DONE)
			return;

		if (this.status !== 200) {
			alert("http " + this.status + ": " + this.responseText);
			return;
		}

		var res = JSON.parse(this.responseText),
			tagord = res.tag_order;

		var ofiles = ebi('files');
		if (ofiles.getAttribute('ts') > this.ts)
			return;

		if (!oldcfg.length) {
			oldcfg = [
				ebi('path').style.display,
				ebi('tree').style.display,
				ebi('wrap').style.marginLeft
			];
			ebi('path').style.display = 'none';
			ebi('tree').style.display = 'none';
			ebi('wrap').style.marginLeft = '0';
		}

		var html = mk_files_header(tagord);
		html.push('<tbody>');
		html.push('<tr><td>-</td><td colspan="42"><a href="#" id="unsearch">close search results</a></td></tr>');
		for (var a = 0; a < res.hits.length; a++) {
			var r = res.hits[a],
				ts = parseInt(r.ts),
				sz = esc(r.sz + ''),
				rp = esc(r.rp + ''),
				ext = rp.lastIndexOf('.') > 0 ? rp.split('.').slice(-1)[0] : '%',
				links = linksplit(rp);

			if (ext.length > 8)
				ext = '%';

			links = links.join('');
			var nodes = ['<tr><td>-</td><td><div>' + links + '</div>', sz];
			for (var b = 0; b < tagord.length; b++) {
				var k = tagord[b],
					v = r.tags[k] || "";

				if (k == "dur") {
					var sv = s2ms(v);
					nodes[nodes.length - 1] += '</td><td sortv="' + v + '">' + sv;
					continue;
				}

				nodes.push(v);
			}

			nodes = nodes.concat([ext, unix2iso(ts)]);
			html.push(nodes.join('</td><td>'));
			html.push('</td></tr>');
		}

		if (!orig_html)
			orig_html = ebi('files').innerHTML;

		ofiles.innerHTML = html.join('\n');
		ofiles.setAttribute("ts", this.ts);
		filecols.set_style();
		reload_browser();

		ebi('unsearch').onclick = unsearch;
	}

	function unsearch(e) {
		ev(e);
		ebi('path').style.display = oldcfg[0];
		ebi('tree').style.display = oldcfg[1];
		ebi('wrap').style.marginLeft = oldcfg[2];
		oldcfg = [];
		ebi('files').innerHTML = orig_html;
		orig_html = null;
		reload_browser();
	}
})();


var treectl = (function () {
	var dyn = bcfg_get('dyntree', true);
	var treesz = icfg_get('treesz', 16);
	treesz = Math.min(Math.max(treesz, 4), 50);
	console.log('treesz [' + treesz + ']');
	var entreed = false;

	function entree(e) {
		ev(e);
		entreed = true;
		ebi('path').style.display = 'none';

		var tree = ebi('tree');
		tree.style.display = 'block';

		swrite('entreed', 'tree');
		get_tree("", get_evpath(), true);
		window.addEventListener('scroll', onscroll);
		window.addEventListener('resize', onresize);
		onresize();
	}

	function detree(e) {
		ev(e);
		entreed = false;
		ebi('tree').style.display = 'none';
		ebi('path').style.display = 'inline-block';
		ebi('wrap').style.marginLeft = '0';
		swrite('entreed', 'na');
		window.removeEventListener('resize', onresize);
		window.removeEventListener('scroll', onscroll);
	}

	function onscroll() {
		if (!entreed)
			return;

		var top = ebi('wrap').getBoundingClientRect().top;
		ebi('tree').style.top = Math.max(0, parseInt(top)) + 'px';
	}

	function periodic() {
		onscroll();
		setTimeout(periodic, document.visibilityState ? 200 : 5000);
	}
	periodic();

	function onresize(e) {
		if (!entreed)
			return;

		var q = '#tree';
		var nq = 0;
		while (dyn) {
			nq++;
			q += '>ul>li';
			if (!document.querySelector(q))
				break;
		}
		var w = treesz + nq;
		ebi('tree').style.width = w + 'em';
		ebi('wrap').style.marginLeft = w + 'em';
		onscroll();
	}

	function get_tree(top, dst, rst) {
		var xhr = new XMLHttpRequest();
		xhr.top = top;
		xhr.dst = dst;
		xhr.rst = rst;
		xhr.ts = new Date().getTime();
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
			rtop = top.replace(/^\/+/, "");

		try {
			var res = JSON.parse(this.responseText);
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

			var links = document.querySelectorAll('#treeul a+a');
			for (var a = 0, aa = links.length; a < aa; a++) {
				if (links[a].getAttribute('href') == top) {
					var o = links[a].parentNode;
					if (!o.getElementsByTagName('li').length)
						o.innerHTML = html;
					//else
					//	links[a].previousSibling.textContent = '-';
				}
			}
		}
		document.querySelector('#treeul>li>a+a').textContent = '[root]';
		despin('#tree');
		reload_tree();
		onresize();
	}

	function reload_tree() {
		var cdir = get_evpath();
		var links = document.querySelectorAll('#treeul a+a');
		for (var a = 0, aa = links.length; a < aa; a++) {
			var href = links[a].getAttribute('href');
			links[a].setAttribute('class', href == cdir ? 'hl' : '');
			links[a].onclick = treego;
		}
		links = document.querySelectorAll('#treeul li>a:first-child');
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
		xhr.ts = new Date().getTime();
		xhr.open('GET', xhr.top + '?ls', true);
		xhr.onreadystatechange = recvls;
		xhr.send();
		if (hpush)
			get_tree('.', xhr.top);

		enspin('#files');
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
		var nodes = res.dirs.concat(res.files);
		var top = this.top;
		var html = mk_files_header(res.taglist);
		html.push('<tbody>');
		for (var a = 0; a < nodes.length; a++) {
			var r = nodes[a],
				ln = ['<tr><td>' + r.lead + '</td><td><a href="' +
					top + r.href + '">' + esc(uricom_dec(r.href)[0]) + '</a>', r.sz];

			for (var b = 0; b < res.taglist.length; b++) {
				var k = res.taglist[b],
					v = (r.tags || {})[k] || "";

				if (k[0] == '.')
					k = k.slice(1);

				if (k == "dur") {
					var sv = s2ms(v);
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

		ebi('pro').innerHTML = res.logues ? res.logues[0] || "" : "";
		ebi('epi').innerHTML = res.logues ? res.logues[1] || "" : "";

		filecols.set_style();
		mukey.render();
		reload_tree();
		reload_browser();
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

	ebi('entree').onclick = entree;
	ebi('detree').onclick = detree;
	ebi('dyntree').onclick = dyntree;
	ebi('twig').onclick = scaletree;
	ebi('twobytwo').onclick = scaletree;
	if (sread('entreed') == 'tree')
		entree();

	window.onpopstate = function (e) {
		console.log("h-pop " + e.state);
		if (!e.state)
			return;

		var url = new URL(e.state, "https://" + document.location.host);
		url = url.pathname;
		get_tree("", url, true);
		reqls(url);
	};

	if (window.history && history.pushState) {
		hist_replace(get_evpath() + window.location.hash);
	}

	return {
		"onscroll": onscroll
	}
})();


function enspin(sel) {
	despin(sel);
	var d = document.createElement('div');
	d.setAttribute('class', 'dumb_loader_thing');
	d.innerHTML = '🌲';
	var tgt = document.querySelector(sel);
	tgt.insertBefore(d, tgt.childNodes[0]);
}


function despin(sel) {
	var o = document.querySelectorAll(sel + '>.dumb_loader_thing');
	for (var a = o.length - 1; a >= 0; a--)
		o[a].parentNode.removeChild(o[a]);
}


function apply_perms(perms) {
	perms = perms || [];

	var o = document.querySelectorAll('#ops>a[data-perm]');
	for (var a = 0; a < o.length; a++)
		o[a].style.display = 'none';

	for (var a = 0; a < perms.length; a++) {
		o = document.querySelectorAll('#ops>a[data-perm="' + perms[a] + '"]');
		for (var b = 0; b < o.length; b++)
			o[b].style.display = 'inline';
	}

	var act = document.querySelector('#ops>a.act');
	if (act) {
		var areq = act.getAttribute('data-perm');
		if (areq && !has(perms, areq))
			goto();
	}

	document.body.setAttribute('perms', perms.join(' '));

	var have_write = has(perms, "write");
	var tds = document.querySelectorAll('#u2conf td');
	for (var a = 0; a < tds.length; a++) {
		tds[a].style.display =
			(have_write || tds[a].getAttribute('data-perm') == 'read') ?
				'table-cell' : 'none';
	}

	if (window['up2k'])
		up2k.set_fsearch();
}


function mk_files_header(taglist) {
	var html = [
		'<thead>',
		'<th></th>',
		'<th><span>File Name</span></th>',
		'<th sort="int"><span>Size</span></th>'
	];
	for (var a = 0; a < taglist.length; a++) {
		var tag = taglist[a];
		var c1 = tag.slice(0, 1).toUpperCase();
		tag = c1 + tag.slice(1);
		if (c1 == '.')
			tag = '<th sort="int"><span>' + tag.slice(1);
		else
			tag = '<th><span>' + tag;

		html.push(tag + '</span></th>');
	}
	html = html.concat([
		'<th><span>T</span></th>',
		'<th><span>Date</span></th>',
		'</thead>',
	]);
	return html;
}


var filecols = (function () {
	var hidden = jread('filecols', []);

	var add_btns = function () {
		var ths = document.querySelectorAll('#files th>span');
		for (var a = 0, aa = ths.length; a < aa; a++) {
			var th = ths[a].parentElement;
			var is_hidden = has(hidden, ths[a].textContent);
			th.innerHTML = '<div class="cfg"><a href="#">' +
				(is_hidden ? '+' : '-') + '</a></div>' + ths[a].outerHTML;

			th.getElementsByTagName('a')[0].onclick = ev_row_tgl;
		}
	};

	var set_style = function () {
		add_btns();

		var ohidden = [],
			ths = document.querySelectorAll('#files th'),
			ncols = ths.length;

		for (var a = 0; a < ncols; a++) {
			var span = ths[a].getElementsByTagName('span');
			if (span.length <= 0)
				continue;

			var name = span[0].textContent,
				cls = '';

			if (has(hidden, name)) {
				ohidden.push(a);
				cls = ' min';
			}
			ths[a].className = ths[a].className.replace(/ *min */, " ") + cls;
		}
		for (var a = 0; a < ncols; a++) {
			var cls = has(ohidden, a) ? 'min' : '';
			var tds = document.querySelectorAll('#files>tbody>tr>td:nth-child(' + (a + 1) + ')');
			for (var b = 0, bb = tds.length; b < bb; b++) {
				tds[b].setAttribute('class', cls);
				if (a < 2)
					continue;

				if (cls) {
					if (!tds[b].hasAttribute('html')) {
						tds[b].setAttribute('html', tds[b].innerHTML);
						tds[b].innerHTML = '...';
					}
				}
				else if (tds[b].hasAttribute('html')) {
					tds[b].innerHTML = tds[b].getAttribute('html');
					tds[b].removeAttribute('html');
				}
			}
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
	var map = {};

	var html = [];
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
		render();
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
		var tds = ebi('files').tHead.getElementsByTagName('th');
		var i = -1;
		var min = false;
		for (var a = 0; a < tds.length; a++) {
			var spans = tds[a].getElementsByTagName('span');
			if (spans.length && spans[0].textContent == 'Key') {
				min = tds[a].getAttribute('class').indexOf('min') !== -1;
				i = a;
				break;
			}
		}

		if (i == -1)
			return;

		var rows = ebi('files').tBodies[0].rows;

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

	var o = document.querySelectorAll('#key_notation input');
	for (var a = 0; a < o.length; a++) {
		o[a].onchange = set_key_notation;
	}

	return {
		"render": try_render
	};
})();


(function () {
	function set_tooltip(e) {
		ev(e);
		ebi('opdesc').innerHTML = this.getAttribute('data-desc');
	}
	var btns = document.querySelectorAll('#ops, #ops>a');
	for (var a = 0; a < btns.length; a++) {
		btns[a].onmouseenter = set_tooltip;
	}
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
	mp = init_mp();
}


function reload_browser(not_mp) {
	filecols.set_style();
	makeSortable(ebi('files'), reload_mp);

	var parts = get_evpath().split('/');
	var rm = document.querySelectorAll('#path>a+a+a');
	for (a = rm.length - 1; a >= 0; a--)
		rm[a].parentNode.removeChild(rm[a]);

	var link = '/';
	for (var a = 1; a < parts.length - 1; a++) {
		link += parts[a] + '/';
		var o = document.createElement('a');
		o.setAttribute('href', link);
		o.innerHTML = parts[a];
		ebi('path').appendChild(o);
	}

	var oo = document.querySelectorAll('#files>tbody>tr>td:nth-child(3)');
	for (var a = 0, aa = oo.length; a < aa; a++) {
		var sz = oo[a].textContent.replace(/ /g, ""),
			hsz = sz.replace(/\B(?=(\d{3})+(?!\d))/g, " ");

		oo[a].textContent = hsz;
	}

	if (!not_mp)
		reload_mp();

	if (window['up2k'])
		up2k.set_fsearch();
}
reload_browser(true);
mukey.render();
