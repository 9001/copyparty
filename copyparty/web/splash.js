var Ls = {
	"nor": {
		"a1": "oppdater",
		"b1": "halloien &nbsp; <small>(du er ikke logget inn)</small>",
		"c1": "logg ut",
		"d1": "tilstand",
		"d2": "vis tilstanden til alle tråder",
		"e1": "last innst.",
		"e2": "leser inn konfigurasjonsfiler på nytt$N(kontoer, volumer, volumbrytere)$Nog kartlegger alle e2ds-volumer$N$Nmerk: endringer i globale parametere$Nkrever en full restart for å ta gjenge",
		"f1": "du kan betrakte:",
		"g1": "du kan laste opp til:",
		"cc1": "brytere og sånt",
		"h1": "skru av k304",
		"i1": "skru på k304",
		"j1": "k304 bryter tilkoplingen for hver HTTP 304. Dette hjelper mot visse mellomtjenere som kan sette seg fast / plutselig slutter å laste sider, men det reduserer også ytelsen betydelig",
		"k1": "nullstill innstillinger",
		"l1": "logg inn:",
		"m1": "velkommen tilbake,",
		"n1": "404: filen finnes ikke &nbsp;┐( ´ -`)┌",
		"o1": 'eller kanskje du ikke har tilgang? prøv et passord eller <a href="' + SR + '/?h">gå hjem</a>',
		"p1": "403: tilgang nektet &nbsp;~┻━┻",
		"q1": 'prøv et passord eller <a href="' + SR + '/?h">gå hjem</a>',
		"r1": "gå hjem",
		".s1": "kartlegg",
		"t1": "handling",
		"u2": "tid siden noen sist skrev til serveren$N( opplastning / navneendring / ... )$N$N17d = 17 dager$N1h23 = 1 time 23 minutter$N4m56 = 4 minuter 56 sekunder",
		"v1": "koble til",
		"v2": "bruk denne serveren som en lokal harddisk$N$NADVARSEL: kommer til å vise passordet ditt!",
		"w1": "bytt til https",
		"x1": "bytt passord",
		"y1": "dine delinger",
		"z1": "lås opp område",
		"ta1": "du må skrive et nytt passord først",
		"ta2": "gjenta for å bekrefte nytt passord:",
		"ta3": "fant en skrivefeil; vennligst prøv igjen",
		"aa1": "innkommende:",
	},
	"eng": {
		"d2": "shows the state of all active threads",
		"e2": "reload config files (accounts/volumes/volflags),$Nand rescan all e2ds volumes$N$Nnote: any changes to global settings$Nrequire a full restart to take effect",
		"u2": "time since the last server write$N( upload / rename / ... )$N$N17d = 17 days$N1h23 = 1 hour 23 minutes$N4m56 = 4 minutes 56 seconds",
		"v2": "use this server as a local HDD$N$NWARNING: this will show your password!",
		"ta1": "fill in your new password first",
		"ta2": "repeat to confirm new password:",
		"ta3": "found a typo; please try again",
	},

	"chi": {
		"a1": "更新",
		"b1": "你好 &nbsp; <small>(你尚未登录)</small>",
		"c1": "登出",
		"d1": "状态",
		"d2": "显示所有活动线程的状态",
		"e1": "重新加载配置",
		"e2": "重新加载配置文件（账户/卷/卷标），$N并重新扫描所有 e2ds 卷$N$N注意：任何全局设置的更改$N都需要完全重启才能生效",
		"f1": "你可以查看：",
		"g1": "你可以上传到：",
		"cc1": "开关等",
		"h1": "关闭 k304",
		"i1": "开启 k304",
		"j1": "k304 会在每个 HTTP 304 时断开连接。这有助于避免某些代理服务器卡住或突然停止加载页面，但也会显著降低性能。",
		"k1": "重置设置",
		"l1": "登录：",
		"m1": "欢迎回来，",
		"n1": "404: 文件不存在 &nbsp;┐( ´ -`)┌",
		"o1": '或者你可能没有权限？尝试输入密码或 <a href="' + SR + '/?h">回家</a>',
		"p1": "403: 访问被拒绝 &nbsp;~┻━┻",
		"q1": '尝试输入密码或 <a href="' + SR + '/?h">回家</a>',
		"r1": "回家",
		".s1": "映射",
		"t1": "操作",
		"u2": "自上次服务器写入的时间$N( 上传 / 重命名 / ... )$N$N17d = 17 天$N1h23 = 1 小时 23 分钟$N4m56 = 4 分钟 56 秒",
		"v1": "连接",
		"v2": "将此服务器用作本地硬盘$N$N警告：这将显示你的密码！",
		"w1": "切换到 https",
		"x1": "更改密码",
		"y1": "你的分享",
		"z1": "解锁区域",
		"ta1": "请先输入新密码",
		"ta2": "重复以确认新密码：",
		"ta3": "发现拼写错误；请重试",
		"aa1": "正在接收的文件：", //m
	}
};

if (window.langmod)
	langmod();

var d = Ls[sread("cpp_lang", Object.keys(Ls)) || lang] ||
			Ls.eng || Ls.nor || Ls.chi;

for (var k in (d || {})) {
	var f = k.slice(-1),
		i = k.slice(0, -1),
		o = QSA(i.startsWith('.') ? i : '#' + i);

	for (var a = 0; a < o.length; a++)
		if (f == 1)
			o[a].innerHTML = d[k];
		else if (f == 2)
			o[a].setAttribute("tt", d[k]);
}

try {
	if (is_idp) {
		var z = ['#l+div', '#l', '#c'];
		for (var a = 0; a < z.length; a++)
			QS(z[a]).style.display = 'none';
	}
}
catch (ex) { }

tt.init();
var o = QS('input[name="cppwd"]');
if (!ebi('c') && o.offsetTop + o.offsetHeight < window.innerHeight)
	o.focus();

o = ebi('u');
if (o && /[0-9]+$/.exec(o.innerHTML))
	o.innerHTML = shumantime(o.innerHTML);

ebi('uhash').value = '' + location.hash;

(function() {
	if (!ebi('x'))
		return;

	var pwi = ebi('lp');

	function redo(msg) {
		modal.alert(msg, function() {
			pwi.value = '';
			pwi.focus();
		});
	}
	function mok(v) {
		if (v !== pwi.value)
			return redo(d.ta3);

		pwi.setAttribute('name', 'pw');
		ebi('la').value = 'chpw';
		ebi('lf').submit();
	}
	function stars() {
		var m = ebi('modali');
		function enstars(n) {
			setTimeout(function() { m.value = ''; }, n);
		}
		m.setAttribute('type', 'password');
		enstars(17);
		enstars(32);
		enstars(69);
	}
	ebi('x').onclick = function (e) {
		ev(e);
		if (!pwi.value)
			return redo(d.ta1);

		modal.prompt(d.ta2, "y", mok, null, stars);
	};
})();
