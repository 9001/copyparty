"use strict";

var J_SPL = 1;

Ls.eng = {
	"splash": {
		"d2": "shows the state of all active threads",
		"e2": "reload config files (accounts/volumes/volflags),$Nand rescan all e2ds volumes$N$Nnote: any changes to global settings$Nrequire a full restart to take effect",
		"lo2": "ends the session on all browsers",
		"u2": "time since the last server write$N( upload / rename / ... )$N$N17d = 17 days$N1h23 = 1 hour 23 minutes$N4m56 = 4 minutes 56 seconds",
		"v2": "use this server as a local HDD",
		"ta1": "fill in your new password first",
		"ta2": "repeat to confirm new password:",
		"ta3": "found a typo; please try again",
		"nop": "ERROR: Password cannot be blank",
		"nou": "ERROR: Username and/or password cannot be blank",
	}
};

if (window.langmod)
	langmod();

var d = (Ls[lang] || Ls.eng).splash;
if (Ls.eng && d !== Ls.eng.splash)
	for (var k in Ls.eng.splash)
		if (d[k] === undefined)
			d[k] = Ls.eng.splash[k];

d.wb = d.w;

for (var k in (d || {})) {
	var f = k.slice(-1),
		i = k.slice(0, -1),
		o = QSA(i.startsWith('.') ? i : '#' + i);

	for (var a = 0; a < o.length; a++)
		if (f == 1)
			o[a].innerHTML = d[k];
		else if (f == 2)
			o[a].setAttribute("tt", d[k]);
		else if (f == 3)
			o[a].setAttribute("value", d[k]);
		else if (f == 4)
			o[a].setAttribute("placeholder", " " + d[k]);
}
var o1 = ebi('lo'), o2 = ebi('un');
if (o1 && o2 && d.lo3)
	o1.setAttribute("value", d.lo3.format(o2.textContent));

try {
	if (is_idp > 1) {
		var z = ['#l+div', '#l', '#c'];
		for (var a = 0; a < z.length; a++)
			QS(z[a]).style.display = 'none';
	}
}
catch (ex) { }

tt.init();
var o = QS('input[name="uname"]') || QS('input[name="cppwd"]');
if (o && !MOBILE && !ebi('c') && o.offsetTop + o.offsetHeight < window.innerHeight)
	o.focus();

o = ebi('u');
if (o && /[0-9]+$/.exec(o.innerHTML))
	o.innerHTML = shumantime(o.innerHTML);

o = ebi('uhash')
if (o)
	o.value = '' + location.hash;

if (/\&re=/.test('' + location))
	ebi('a').className = 'af g';

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
			return ebi('lm').innerHTML = d.ta1;

		modal.prompt(d.ta2, "y", mok, null, stars);
	};
})();

if (ebi('lf'))
	ebi('lf').onsubmit = function() {
		var un = ebi('lu');
		if (ebi('lp').value && (!un || un.value))
			return true;
		ebi('lm').innerHTML = un ? d.nou : d.nop;
		return false;
	};

if (ebi('lp'))
	ebi('lp').oninput = function() {
		ebi('lm').innerHTML = this.value.length <= 64 ?
			'' : 'ERROR: Password too long (max=64)';
	};

J_SPL = 2;
