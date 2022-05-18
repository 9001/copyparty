var Ls = {
	"nor": {
		"a1": "oppdater",
		"b1": "halloien &nbsp; <small>(du er ikke logget inn)</small>",
		"c1": "logg ut",
		"d1": "tilstand",
		"d2": "vis tilstanden til alle tråder",
		"e1": "last innst.",
		"e2": "leser inn konfigurasjonsfiler på nytt$N(kontoer, volumer, volumbrytere)$Nog kartlegger alle e2ds-volumer",
		"f1": "du kan betrakte:",
		"g1": "du kan laste opp til:",
		"cc1": "klient-konfigurasjon",
		"h1": "skru av k304",
		"i1": "skru på k304",
		"j1": "k304 bryter tilkoplingen for hver HTTP 304. Dette hjelper visse mellomtjenere som kan sette seg fast / plutselig slutter å laste sider, men det reduserer også ytelsen betydelig",
		"k1": "nullstill innstillinger",
		"l1": "logg inn:",
		"m1": "velkommen tilbake,",
		"n1": "404: filen finnes ikke &nbsp;┐( ´ -`)┌",
		"o1": 'eller kanskje du ikke har tilgang? prøv å logge inn eller <a href="/?h">gå hjem</a>',
		"p1": "403: tilgang nektet &nbsp;~┻━┻",
		"q1": 'du må logge inn eller <a href="/?h">gå hjem</a>',
		"r1": "gå hjem",
		".s1": "kartlegg",
		"t1": "handling",
	}
},
	d = Ls[sread("lang") || lang];

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

tt.init();
if (!ebi('c'))
	QS('input[name="cppwd"]').focus();
