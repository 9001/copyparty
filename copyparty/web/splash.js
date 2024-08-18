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
		"o1": 'eller kanskje du ikke har tilgang? prøv å logge inn eller <a href="' + SR + '/?h">gå hjem</a>',
		"p1": "403: tilgang nektet &nbsp;~┻━┻",
		"q1": 'du må logge inn eller <a href="' + SR + '/?h">gå hjem</a>',
		"r1": "gå hjem",
		".s1": "kartlegg",
		"t1": "handling",
		"u2": "tid siden noen sist skrev til serveren$N( opplastning / navneendring / ... )$N$N17d = 17 dager$N1h23 = 1 time 23 minutter$N4m56 = 4 minuter 56 sekunder",
		"v1": "koble til",
		"v2": "bruk denne serveren som en lokal harddisk$N$NADVARSEL: kommer til å vise passordet ditt!",
		"w1": "bytt til https",
		"x1": "bytt passord",
		"y1": "dine delinger",
		"ta1": "du må skrive et nytt passord først",
		"ta2": "gjenta for å bekrefte nytt passord:",
		"ta3": "fant en skrivefeil; vennligst prøv igjen",
	},
	"eng": {
		"d2": "shows the state of all active threads",
		"e2": "reload config files (accounts/volumes/volflags),$Nand rescan all e2ds volumes$N$Nnote: any changes to global settings$Nrequire a full restart to take effect",
		"u2": "time since the last server write$N( upload / rename / ... )$N$N17d = 17 days$N1h23 = 1 hour 23 minutes$N4m56 = 4 minutes 56 seconds",
		"v2": "use this server as a local HDD$N$NWARNING: this will show your password!",
		"ta1": "fill in your new password first",
		"ta2": "repeat to confirm new password:",
		"ta3": "found a typo; please try again",
	}
};

var LANGS = ["eng", "nor"];

if (window.langmod)
	langmod();

var d = Ls[sread("cpp_lang", LANGS) || lang] || Ls.eng || Ls.nor;

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
