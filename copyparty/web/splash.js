// please add translations in alphabetic order, but keep "nor" and "eng" first
// (lines ending with //m are machine translations)
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
		"cc1": "brytere og sånt:",
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
		"v2": "bruk denne serveren som en lokal harddisk",
		"w1": "bytt til https",
		"x1": "bytt passord",
		"y1": "dine delinger",
		"z1": "lås opp område:",
		"ta1": "du må skrive et nytt passord først",
		"ta2": "gjenta for å bekrefte nytt passord:",
		"ta3": "fant en skrivefeil; vennligst prøv igjen",
		"aa1": "innkommende:",
		"ab1": "skru av no304",
		"ac1": "skru på no304",
		"ad1": "no304 stopper all bruk av cache. Hvis ikke k304 var nok, prøv denne. Vil mangedoble dataforbruk!",
		"ae1": "utgående:",
		"af1": "vis nylig opplastede filer",
		"ag1": "vis kjente IdP-brukere",
	},
	"eng": {
		"d2": "shows the state of all active threads",
		"e2": "reload config files (accounts/volumes/volflags),$Nand rescan all e2ds volumes$N$Nnote: any changes to global settings$Nrequire a full restart to take effect",
		"u2": "time since the last server write$N( upload / rename / ... )$N$N17d = 17 days$N1h23 = 1 hour 23 minutes$N4m56 = 4 minutes 56 seconds",
		"v2": "use this server as a local HDD",
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
		"v2": "将此服务器用作本地硬盘",
		"w1": "切换到 https",
		"x1": "更改密码",
		"y1": "你的分享",
		"z1": "解锁区域",
		"ta1": "请先输入新密码",
		"ta2": "重复以确认新密码：",
		"ta3": "发现拼写错误；请重试",
		"aa1": "正在接收的文件：", //m
		"ab1": "关闭 k304",
		"ac1": "开启 k304",
		"ad1": "启用 no304 将禁用所有缓存；如果 k304 不够，可以尝试此选项。这将消耗大量的网络流量！", //m
		"ae1": "正在下载：", //m
		"af1": "显示最近上传的文件", //m
		"ag1": "查看已知 IdP 用户", //m
	},
	"cze": {
		"a1": "obnovit",
		"b1": "ahoj cizinče &nbsp; <small>(nejsi přihlášen)</small>",
		"c1": "odhlásit se",
		"d1": "vypsat zásobníku",  // TLNote: "d2" is the tooltip for this button
		"d2": "zobrazit stav všech aktivních vláken",
		"e1": "znovu načíst konfiguraci",
		"e2": "znovu načíst konfigurační soubory (accounts/volumes/volflags),$Na prohledat všechny e2ds úložiště$N$Npoznámka: všechny změny globálních nastavení$Nvyžadují úplné restartování, aby se projevily",
		"f1": "můžeš procházet:",
		"g1": "můžeš nahrávat do:",
		"cc1": "další věci:",
		"h1": "zakázat k304",  // TLNote: "j1" explains what k304 is
		"i1": "povolit k304",
		"j1": "povolení k304 odpojí vašeho klienta při každém HTTP 304, což může zabránit některým chybovým proxy serverům, aby se zasekly (náhle nenačítaly stránky), <em>ale</em> také to obecně zpomalí věci",
		"k1": "resetovat nastavení klienta",
		"l1": "přihlaste se pro více:",
		"m1": "vítej zpět,",  // TLNote: "welcome back, USERNAME"
		"n1": "404 nenalezeno &nbsp;┐( ´ -`)┌",
		"o1": 'nebo možná nemáš přístup -- zkus heslo nebo <a href="' + SR + '/?h">jdi domů</a>',
		"p1": "403 zakázáno &nbsp;~┻━┻",
		"q1": 'použij heslo nebo <a href="' + SR + '/?h">jdi domů</a>',
		"r1": "jdi domů",
		".s1": "znovu prohledat",
		"t1": "akce",  // TLNote: this is the header above the "rescan" buttons
		"u2": "čas od posledního zápisu na server$N( upload / rename / ... )$N$N17d = 17 dní$N1h23 = 1 hodina 23 minut$N4m56 = 4 minuty 56 sekund",
		"v1": "připojit",
		"v2": "použít tento server jako místní HDD",
		"w1": "přepnout na https",
		"x1": "změnit heslo",
		"y1": "upravit sdílení",  // TLNote: shows the list of folders that the user has decided to share
		"z1": "odblokovat toto sdílení:",  // TLNote: the password prompt to see a hidden share
		"ta1": "nejprve vyplňte své nové heslo",
		"ta2": "zopakujte pro potvrzení nového hesla:",
		"ta3": "nalezen překlep; zkuste to prosím znovu",
		"aa1": "příchozí soubory:",
		"ab1": "deaktivovat no304",
		"ac1": "povolit no304",
		"ad1": "povolení no304 deaktivuje veškeré mezipaměti; zkuste to, pokud k304 nestačilo. To ovšem zapříčíní obrovské množství síťového provozu!",
		"ae1": "aktivní stahování:",
		"af1": "zobrazit nedávné nahrávání",
	},
	"deu": {
		"a1": "Neu laden",
		"b1": "Tach, wie geht's? &nbsp; <small>(Du bist nicht angemeldet)</small>",
		"c1": "Abmelden",
		"d1": "Zustand",
		"d2": "Zeigt den Zustand aller aktiven Threads",
		"e1": "Config neu laden",
		"e2": "Konfigurationsdatei neu laden (Accounts/Volumes/VolFlags)$Nund scannt alle e2ds-Volumes$N$NBeachte: Jegliche Änderung an globalen Einstellungen$Nbenötigt einen Neustart zum Anwenden",
		"f1": "Du kannst lesen:",
		"g1": "Du kannst hochladen nach:",
		"cc1": "Andere Dinge:",
		"h1": "k304 deaktivieren",
		"i1": "k304 aktivieren",
		"j1": "k304 trennt die Clientverbindung bei jedem HTTP 304, was Bugs mit problematischen Proxies vorbeugen kann (z.B. nicht ladenden Seiten), macht Dinge aber generell langsamer",
		"k1": "Client-Einstellungen zurücksetzen",
		"l1": "Melde dich an für mehr:",
		"m1": "Willkommen zurück,",
		"n1": "404 Nicht gefunden &nbsp;┐( ´ -`)┌",
		"o1": 'or maybe you don\'t have access -- try a password or <a href="' + SR + '/?h">go home</a>',
		"p1": "403 Verboten &nbsp;~┻━┻",
		"q1": 'Benutze ein Passwort oder <a href="' + SR + '/?h">gehe zur Homepage</a>',
		"r1": "Gehe zur Homepage",
		".s1": "Neu scannen",
		"t1": "Aktion",
		"u2": "time since the last server write$N( upload / rename / ... )$N$N17d = 17 days$N1h23 = 1 hour 23 minutes$N4m56 = 4 minutes 56 seconds",
		"v1": "Verbinden",
		"v2": "Benutze diesen Server als lokale Festplatte",
		"w1": "Zu HTTPS wechseln",
		"x1": "Passwort ändern",
		"y1": "Shares bearbeiten",
		"z1": "Share entsperren:",
		"ta1": "Trage zuerst dein Passwort ein",
		"ta2": "Wiederhole dein Passwort zur Bestätigung:",
		"ta3": "Da stimmt etwas nicht; probier's nochmal",
		"aa1": "Eingehende Dateien:",
		"ab1": "no304 deaktivieren",
		"ac1": "no304 aktivieren",
		"ad1": "Das Aktivieren von no304 deaktiviert jegliche Form von Caching; probier dies, wenn k304 nicht genug war. Dies verschwendet eine grosse Menge Netzwerk-Traffic!",
		"ae1": "Aktive Downloads:",
		"af1": "Zeige neue Uploads",
	},
	"fin": {
		"a1": "päivitä",
		"b1": "hei sie muukalainen &nbsp; <small>(et ole kirjautunut sisään)</small>",
		"c1": "kirjaudu ulos",
		"d1": "tulosta pinojälki",
		"d2": "näytä kaikkien aktiivisten säikeiden tila",
		"e1": "päivitä konffit",
		"e2": "lataa konfiguraatiotiedostot uudelleen (käyttäjätilit/asemat/asemaflagit),$Nja skannaa kaikki e2ds asemat uudelleen$N$Nhuom: kaikki global-asetuksiin$Ntehdyt muutokset vaativat täyden$Nuudelleenkäynnistyksen",
		"f1": "voit selata näitä:",
		"g1": "voit ladata näihin:",
		"cc1": "muuta:",
		"h1": "poista k304 käytöstä",
		"i1": "ota k304 käyttöön",
		"j1": "k304 katkaisee yhteytesi jokaisella HTTP 304:llä, mikä voi estää joitain bugisia välityspalvelimia jumittumasta/lopettamasta sivujen lataamista, <em>mutta</em> se myös vähentää suorituskykyä",
		"k1": "nollaa asetukset",
		"l1": "kirjaudu sisään:",
		"m1": "tervetuloa takaisin,",
		"n1": "404: ei löytynyt mitään &nbsp;┐( ´ -`)┌",
		"o1": 'tai ehkä sinulla ei vain ole käyttöoikeuksia? kokeile salasanaa tai <a href="' + SR + '/?h">mene kotiin</a>',
		"p1": "403: pääsy kielletty &nbsp;~┻━┻",
		"q1": 'kokeile salasanaa tai <a href="' + SR + '/?h">mene kotiin</a>',
		"r1": "mene kotiin",
		".s1": "uudelleenkartoita",
		"t1": "toiminto",
		"u2": "aika viimeisestä palvelimen kirjoituksesta$N( lataus / uudelleennimeäminen / tms. )$N$N17d = 17 päivää$N1h23 = 1 tunti 23 minuuttia$N4m56 = 4 minuuttia 56 sekuntia",
		"v1": "yhdistä",
		"v2": "käytä tätä palvelinta paikallisena kiintolevynä",
		"w1": "vaihda https:ään",
		"x1": "vaihda salasana",
		"y1": "muokkaa jakoja",
		"z1": "avaa tämä jako:",
		"ta1": "täytä ensin uusi salasana",
		"ta2": "toista vahvistaaksesi uuden salasanan:",
		"ta3": "löytyi kirjoitusvirhe; yritä uudelleen",
		"aa1": "saapuvat:",
		"ab1": "poista no304 käytöstä",
		"ac1": "ota no304 käyttöön",
		"ad1": "no304:n lopettaa välimuistin käytön kokonaan; kokeile tätä jos k304 ei riittänyt. Tuhlaa valtavan määrän verkkoliikennettä!",
		"ae1": "lähtevät:",
		"af1": "näytä viimeaikaiset lataukset",
		"ag1": "näytä tunnetut IdP-käyttäjät",
	},
	"grc": {
		"a1": "ανανέωση",
		"b1": "γεια σου ξένε! &nbsp; <small>(δεν είσαι συνδεδεμένος)</small>",
		"c1": "αποσύνδεση",
		"d1": "σωρός απορριμμάτων",
		"d2": "εμφανίζει την κατάσταση όλων των ενεργών διεργασιών",
		"e1": "επαναφόρτωση του cfg",
		"e2": "φορτώνει ξανά τα αρχεία ρυθμίσεων (λογαριασμοί/τόμοι/volflags),$Nκαι κάνει επανεξέταση όλων των τόμων e2ds$N$Nσημείωση: οποιαδήποτε αλλαγή στις καθολικές ρυθμίσεις$Nαπαιτεί πλήρη επανεκκίνηση για να εφαρμοστεί",
		"f1": "μπορείς να περιηγηθείς:",
		"g1": "μπορείς να εκτελέσεις μεταφόρτωση σε:",
		"cc1": "άλλα πράγματα:",
		"h1": "απενεργοποίση k304",
		"i1": "ενεργοποίηση k304",
		"j1": "η ενεργοποίηση του k304 θα αποσυνδέσει το πρόγραμμα πελάτη σου σε κάθε HTTP 304, κάτι που μπορεί να αποτρέψει κάποια προβληματικά proxies από το να κολλάνε (να μην φορτώνουν ξαφνικά σελίδες), <em>αλλά</em> θα κάνει τα πράγματα, γενικά πιο αργά",
		"k1": "επαναφορά ρυθμίσεων στο πρόγραμμα πελάτη",
		"l1": "συνδέσου για περισσότερα:",
		"m1": "καλώς ήρθες,",
		"n1": "404 δεν βρέθηκε &nbsp;┐( ´ -`)┌",
		"o1": '´η μήπως δεν έχεις πρόσβαση -- δοκίμασε έναν κωδικό <a href="' + SR + '/?h">πήγαινε στην αρχική</a>',
		"p1": "403 απαγορευμένο &nbsp;~┻━┻",
		"q1": 'δοκίμασε έναν κωδικό <a href="' + SR + '/?h">πήγαινε στην αρχική</a>',
		"r1": "πίσω στην αρχική",
		".s1": "επανάληψη σάρωσης",
		"t1": "ενέργεια",
		"u2": "χρόνος από την τελευταία εγγραφή του διακομιστή$N( μεταφόρτωση / μετονομασία / ... )$N$N17d = 17 days$N1ω23 = 1 ώρα 23 λεπτά$N4λ56 = 4 λεπτά 56 δευτερόλεπτα",
		"v1": "σύνδεση",
		"v2": "χρησιμοποίησε αυτόν το διακομιστή σαν τοπικό δίσκο",
		"w1": "εναλλαγή σε https",
		"x1": "αλλαγή κωδικού",
		"y1": "επεξεργασία κοινόχρηστων φακέλων",
		"z1": "ξεκλείδωμα αυτού του κοινόχρηστου φακέλου:",
		"ta1": "συμπλήρωσε πρώτα το νέο σου κωδικό",
		"ta2": "επανέλαβε για να επιβεβαιώσεις το νέο κωδικό:",
		"ta3": "βρέθηκε τυπογραφικό λάθος· δοκίμασε ξανά",
		"aa1": "εισερχόμενα αρχεία:",
		"ab1": "απενεργοποίηση no304",
		"ac1": "ενεργοποίηση no304",
		"ad1": "η ενεργοποίηση του no304 θα απενεργοποιήσει όλη την προσωρινή αποθήκευση· δοκίμασέ το αν το k304 δεν ήταν αρκετό. Προσοχή, θα σπαταλήσει τεράστιο όγκο δικτυακής κίνησης!",
		"ae1": "ενεργές μεταφορτώσεις:",
		"af1": "προβολή πρόσφατων μεταφορτώσεων",
	},
	"ita": {
		"a1": "aggiorna",
		"b1": "ciao &nbsp; <small>(non sei connesso)</small>",
		"c1": "disconnetti",
		"d1": "stato",
		"d2": "mostra lo stato di tutti i thread attivi",
		"e1": "ricarica configurazione",
		"e2": "ricarica i file di configurazione (account/volumi/flag dei volumi),\n e riesegue la scansione di tutti i volumi e2ds.\n\nNota: qualsiasi modifica alle impostazioni globali richiede un riavvio completo per avere effetto",
		"f1": "puoi visualizzare:",
		"g1": "puoi caricare su:",
		"cc1": "altro:",
		"h1": "disattiva k304",
		"i1": "attiva k304",
		"j1": "k304 interrompe la connessione per ogni HTTP 304. Questo aiuta contro alcuni proxy difettosi che possono bloccarsi o smettere improvvisamente di caricare pagine, ma riduce notevolmente le prestazioni",
		"k1": "resetta impostazioni",
		"l1": "accedi:",
		"m1": "bentornato,",
		"n1": "404: file non trovato &nbsp;┐( ´ -`)┌",
		"o1": "oppure forse non hai accesso? prova una password o <a href=\"SR/?h\">torna alla home</a>",
		"p1": "403: accesso negato &nbsp;~┻━┻",
		"q1": "prova una password o <a href=\"SR/?h\">torna alla home</a>",
		"r1": "torna alla home",
		".s1": "mappa",
		"t1": "azione",
		"u2": "tempo dall'ultima scrittura sul server\n (caricamento / rinomina / ...)\n\n17d = 17 giorni\n1h23 = 1 ora 23 minuti\n4m56 = 4 minuti 56 secondi",
		"v1": "connetti",
		"v2": "usa questo server come un disco locale",
		"w1": "passa a https",
		"x1": "cambia password",
		"y1": "le tue condivisioni",
		"z1": "sblocca area:",
		"ta1": "devi prima inserire una nuova password",
		"ta2": "ripeti per confermare la nuova password:",
		"ta3": "errore di digitazione; riprova",
		"aa1": "in arrivo:",
		"ab1": "disattiva no304",
		"ac1": "attiva no304",
		"ad1": "no304 disabilita completamente la cache. Se k304 non è sufficiente, prova questa opzione. Aumenterà notevolmente il consumo di dati!",
		"ae1": "in uscita:",
		"af1": "mostra i file caricati di recente",
		"ag1": "mostra utenti IdP conosciuti"
	},
	"nld": {
		"a1": "Update",
		"b1": "Hallo, hoe gaat het met jou? &nbsp; <small>(Je bent niet ingelogd)</small>",
		"c1": "Uitloggen",
		"d1": "Voorwaarde",
		"d2": "Toont de status van alle actieve threads",
		"e1": "Configuratie opnieuw laden.",
		"e2": "Leest configuratiebestanden opnieuw in$N(accounts, volumes, volumeschakelaars)$Nen brengt alle e2ds-volumes in kaart$N$Nopmerking: veranderingen in globale parameters$Nvereist een volledige herstart van de server",
		"f1": "Je kan het volgende lezen:",
		"g1": "Je kan naar het volgende uploaden:",
		"cc1": "Schakelaars en dergelijke:",
		"h1": "k304 uitschakelen",
		"i1": "k304 inschakelen",
		"j1": "k304 verbreekt de verbinding voor elke HTTP 304. Dit helpt tegen bepaalde proxy servers die kunnen vastlopen/plotseling stoppen met het laden van pagina's, maar het vermindert ook de prestaties aanzienlijk",
		"k1": "Instellingen resetten",
		"l1": "Inloggen:",
		"m1": "Welkom terug,",
		"n1": "404: bestand bestaat niet &nbsp;┐( ´ -`)┌",
		"o1": 'of misschien heb je geen toegang? probeer een wachtwoord of <a href="' + SR + '/?h">ga naar startscherm</a>',
		"p1": "403: toegang geweigerd &nbsp;~┻━┻",
		"q1": 'Probeer een wachtwoord of <a href="' + SR + '/?h">ga naar startscherm</a>',
		"r1": "Ga naar startscherm",
		".s1": "Kaart",
		"t1": "Actie",
		"u2": "Tijd sinds iemand voor het laatst naar de server schreef$N( upload / naamswijziging / ... )$N$N17d = 17 dagen$N1h23 = 1 uur 23 minuten$N4m56 = 4 minuten 56 secondes",
		"v1": "Verbinden",
		"v2": "Gebruik deze server als een lokale harde schijf",
		"w1": "Overschakelen naar https",
		"x1": "Wachtwoord wijzigen",
		"y1": "Jou gedeelde items",
		"z1": "Ontgrendel gebied:",
		"ta1": "Je moet eerst een nieuw wachtwoord invoeren",
		"ta2": "Herhaal om nieuw wachtwoord te bevestigen:",
		"ta3": "Typefout gevonden; probeer het opnieuw",
		"aa1": "Inkomend:",
		"ab1": "Schakel nr. 304 uit",
		"ac1": "Schakel nr. 304 in",
		"ad1": "Nr. 304 stopt al het cachegebruik. Als k304 niet voldoende was, probeer dan deze. Vermenigvuldigt het dataverbruik.!",
		"ae1": "Uitgaand:",
		"af1": "Recent geüploade bestanden weergeven",
		"ag1": "Bekende IdP-gebruikers weergeven",
	},
	"spa": {
		"a1": "actualizar",
		"b1": "hola &nbsp; <small>(no has iniciado sesión)</small>",
		"c1": "cerrar sesión",
		"d1": "volcar estado de la pila",
		"d2": "muestra el estado de todos los hilos activos",
		"e1": "recargar configuración",
		"e2": "recargar archivos de configuración (cuentas/volúmenes/indicadores de vol.),$Ny reescanear todos los volúmenes e2ds$N$Nnota: cualquier cambio en la configuración global$Nrequiere un reinicio completo para surtir efecto",
		"f1": "puedes explorar:",
		"g1": "puedes subir a:",
		"cc1": "otras cosas:",
		"h1": "desactivar k304",
		"i1": "activar k304",
		"j1": "activar k304 desconectará tu cliente en cada HTTP 304, lo que puede evitar que algunos proxies con errores se atasquen (dejando de cargar páginas de repente), <em>pero</em> también ralentizará las cosas en general",
		"k1": "restablecer config. de cliente",
		"l1": "inicia sesión para más:",
		"m1": "bienvenido de nuevo,",
		"n1": "404 no encontrado &nbsp;┐( ´ -`)┌",
		"o1": '¿o quizás no tienes acceso? -- prueba con una contraseña o <a href=\"' + SR + '/?h\">vuelve al inicio</a>',
		"p1": "403 prohibido &nbsp;~┻━┻",
		"q1": 'usa una contraseña o <a href=\"' + SR + '/?h\">vuelve al inicio</a>',
		"r1": "ir al inicio",
		".s1": "reescanear",
		"t1": "acción",
		"u2": "tiempo desde la última escritura en el servidor$N( subida / renombrar / ... )$N$N17d = 17 días$N1h23 = 1 hora 23 minutos$N4m56 = 4 minutos 56 segundos",
		"v1": "conectar",
		"v2": "usar este servidor como un disco duro local",
		"w1": "cambiar a https",
		"x1": "cambiar contraseña",
		"y1": "editar recursos compartidos",
		"z1": "desbloquear este recurso compartido:",
		"ta1": "primero escribe tu nueva contraseña",
		"ta2": "repite para confirmar la nueva contraseña:",
		"ta3": "hay un error; por favor, inténtalo de nuevo",
		"aa1": "archivos entrantes:",
		"ab1": "desactivar no304",
		"ac1": "activar no304",
		"ad1": "activar no304 desactivará todo el almacenamiento en caché; prueba esto si k304 no fue suficiente. ¡Esto desperdiciará una gran cantidad de tráfico de red!",
		"ae1": "descargas activas:",
		"af1": "mostrar subidas recientes",
		"ag1": "mostrar usuarios IdP conocidos"
	},
	"rus": {
		"a1": "обновить",
		"b1": "приветик, незнакомец &nbsp; <small>(вы не авторизованы)</small>",
		"c1": "выйти",
		"d1": "трассировка стека",
		"d2": "показывает состояние всех активных потоков",
		"e1": "перезагрузить конфиг",
		"e2": "перезагрузить файлы конфига (аккаунты/хранилища/флаги),$Nи пересканировать все хранилища с флагом e2ds$N$Nвнимание: изменения глобальных настроек$Nтребуют полного перезапуска сервера",
		"f1": "вы можете видеть:",
		"g1": "вы можете загружать файлы в:",
		"cc1": "всякая всячина:",
		"h1": "отключить k304",
		"i1": "включить k304",
		"j1": "включённый k304 будет отключать вас при получении HTTP 304, что может помочь при работе с некоторыми глючными прокси (перестают загружаться страницы), <em>но</em> это также сделает работу клиента медленнее",
		"k1": "сбросить локальные настройки",
		"l1": "авторизуйтесь для других опций:",
		"m1": "с возвращением,",
		"n1": "404 не найдено &nbsp;┐( ´ -`)┌",
		"o1": 'или у вас нет доступа -- попробуйте авторизоваться или <a href="' + SR + '/?h">вернуться на главную</a>',
		"p1": "403 доступ запрещён &nbsp;~┻━┻",
		"q1": 'авторизуйтесь или <a href="' + SR + '/?h">вернитесь на главную</a>',
		"r1": "вернуться на главную",
		".s1": "пересканировать",
		"t1": "действия",
		"u2": "время с последней записи на сервер$N( загрузка / переименование / ... )$N$N17d = 17 дней$N1h23 = 1 час 23 минут$N4m56 = 4 минут 56 секунд",
		"v1": "подключить",
		"v2": "использовать сервер как локальный диск",
		"w1": "перейти на https",
		"x1": "поменять пароль",
		"y1": "управление доступом",
		"z1": "разблокировать:",
		"ta1": "сначала введите свой новый пароль",
		"ta2": "повторите новый пароль:",
		"ta3": "опечатка; попробуйте снова",
		"aa1": "входящие файлы:",
		"ab1": "отключить no304",
		"ac1": "включить no304",
		"ad1": "включённый no304 полностью отключит хеширование; используйте, если k304 не помог. Сильно увеличит объём трафика!",
		"ae1": "активные скачивания:",
		"af1": "показать недавние загрузки",
		"ag1": "показать известных IdP-пользователей",
	},
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
var o = QS('input[name="uname"]') || QS('input[name="cppwd"]');
if (!ebi('c') && o.offsetTop + o.offsetHeight < window.innerHeight)
	o.focus();

o = ebi('u');
if (o && /[0-9]+$/.exec(o.innerHTML))
	o.innerHTML = shumantime(o.innerHTML);

ebi('uhash').value = '' + location.hash;

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
			return redo(d.ta1);

		modal.prompt(d.ta2, "y", mok, null, stars);
	};
})();
