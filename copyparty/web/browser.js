"use strict";

var XHR = XMLHttpRequest;
var Ls = {
	"eng": {
		"tt": "English",

		"cols": {
			"c": "action buttons",
			"dur": "duration",
			"q": "quality / bitrate",
			"Ac": "audio codec",
			"Vc": "video codec",
			"Fmt": "format / container",
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
		},

		"hks": [
			[
				"misc",
				["ESC", "close various things"],

				"file-manager",
				["G", "toggle list / grid view"],
				["T", "toggle thumbnails / icons"],
				["🡅 A/D", "thumbnail size"],
				["ctrl-K", "delete selected"],
				["ctrl-X", "cut selected"],
				["ctrl-V", "paste into folder"],
				["Y", "download selected"],
				["F2", "rename selected"],

				"file-list-sel",
				["space", "toggle file selection"],
				["🡑/🡓", "move selection cursor"],
				["ctrl 🡑/🡓", "move cursor and viewport"],
				["🡅 🡑/🡓", "select prev/next file"],
				["ctrl-A", "select all files / folders"],
			], [
				"navigation",
				["B", "toggle breadcrumbs / navpane"],
				["I/K", "prev/next folder"],
				["M", "parent folder (or unexpand current)"],
				["V", "toggle folders / textfiles in navpane"],
				["A/D", "navpane size"],
			], [
				"audio-player",
				["J/L", "prev/next song"],
				["U/O", "skip 10sec back/fwd"],
				["0..9", "jump to 0%..90%"],
				["P", "play/pause (also initiates)"],
				["Y", "download song"],
			], [
				"image-viewer",
				["J/L, ←/→", "prev/next pic"],
				["Home/End", "first/last pic"],
				["F", "fullscreen"],
				["R", "rotate clockwise"],
				["🡅 R", "rotate ccw"],
				["Y", "download pic"],
			], [
				"video-player",
				["U/O", "skip 10sec back/fwd"],
				["P/K/Space", "play/pause"],
				["C", "continue playing next"],
				["V", "loop"],
				["M", "mute"],
				["[ and ]", "set loop interval"],
			], [
				"textfile-viewer",
				["I/K", "prev/next file"],
				["M", "close textfile"],
				["S", "select file (for cut/rename)"],
			]
		],

		"m_ok": "OK",
		"m_ng": "Cancel",

		"ht_s": "second!s",
		"ht_m": "minute!s",
		"ht_h": "hour!s",
		"ht_d": "day!s",
		"ht_and": " and ",

		"goh": "control-panel",
		"gop": 'previous sibling">prev',
		"gou": 'parent folder">up',
		"gon": 'next folder">next',
		"logout": "Logout ",
		"access": " access",
		"ot_close": "close submenu",
		"ot_search": "search for files by attributes, path / name, music tags, or any combination of those$N$N&lt;code&gt;foo bar&lt;/code&gt; = must contain both «foo» and «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = must contain «foo» but not «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = start with «yana» and be an «opus» file$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = contain exactly «try unite»$N$Nthe date format is iso-8601, like$N&lt;code&gt;2009-12-31&lt;/code&gt; or &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: delete your recent uploads",
		"ot_bup": "bup: basic uploader, even supports netscape 4.0",
		"ot_mkdir": "mkdir: create a new directory",
		"ot_md": "new-md: create a new markdown document",
		"ot_msg": "msg: send a message to the server log",
		"ot_mp": "media player options",
		"ot_cfg": "configuration options",
		"ot_u2i": 'up2k: upload files (if you have write-access) or toggle into the search-mode to see if they exist somewhere on the server$N$Nuploads are resumable, multithreaded, and file timestamps are preserved, but it uses more CPU than the basic uploader<br /><br />during uploads, this icon becomes a progress indicator!',
		"ot_u2w": 'up2k: upload files with resume support (close your browser and drop the same files in later)$N$Nmultithreaded, and file timestamps are preserved, but it uses more CPU than the basic uploader<br /><br />during uploads, this icon becomes a progress indicator!',

		"ab_mkdir": "make directory",
		"ab_mkdoc": "new markdown doc",
		"ab_msg": "send msg to srv log",

		"ay_path": "skip to folders",
		"ay_files": "skip to files",

		"wt_ren": "rename selected items$NHotkey: F2",
		"wt_del": "delete selected items$NHotkey: ctrl-K",
		"wt_cut": "cut selected items &lt;small&gt;(then paste somewhere else)&lt;/small&gt;$NHotkey: ctrl-X",
		"wt_pst": "paste a previously cut / copied selection$NHotkey: ctrl-V",
		"wt_selall": "select all files$NHotkey: ctrl-A (when file focused)",
		"wt_selinv": "invert selection",
		"wt_selzip": "download selection as archive",
		"wt_seldl": "download selection as separate files$NHotkey: Y",
		"wt_npirc": "copy irc-formatted track info",
		"wt_nptxt": "copy plaintext track info",
		"wt_grid": "toggle grid / list view$NHotkey: G",
		"wt_prev": "previous track$NHotkey: J",
		"wt_play": "play / pause$NHotkey: P",
		"wt_next": "next track$NHotkey: L",

		"ul_par": "parallel uploads:",
		"ut_mt": "continue hashing other files while uploading$N$Nmaybe disable if your CPU or HDD is a bottleneck",
		"ut_ask": "ask for confirmation before upload starts",
		"ut_pot": "improve upload speed on slow devices$Nby making the UI less complex",
		"ut_srch": "don't actually upload, instead check if the files already $N exist on the server (will scan all folders you can read)",
		"ut_par": "pause uploads by setting it to 0$N$Nincrease if your connection is slow / high latency$N$Nkeep it 1 on LAN or if the server HDD is a bottleneck",
		"ul_btn": "drop files / folders<br>here (or click me)",
		"ul_btnu": "U P L O A D",
		"ul_btns": "S E A R C H",

		"ul_hash": "hash",
		"ul_send": "send",
		"ul_done": "done",
		"ul_idle1": "no uploads are queued yet",
		"ut_etah": "average &lt;em&gt;hashing&lt;/em&gt; speed, and estimated time until finish",
		"ut_etau": "average &lt;em&gt;upload&lt;/em&gt; speed and estimated time until finish",
		"ut_etat": "average &lt;em&gt;total&lt;/em&gt; speed and estimated time until finish",

		"uct_ok": "completed successfully",
		"uct_ng": "no-good: failed / rejected / not-found",
		"uct_done": "ok and ng combined",
		"uct_bz": "hashing or uploading",
		"uct_q": "idle, pending",

		"utl_name": "filename",
		"utl_stat": "status",
		"utl_prog": "progress",

		"ul_flagblk": "the files were added to the queue</b><br>however there is a busy up2k in another browser tab,<br>so waiting for that to finish first",

		"udt_up": "Upload",
		"udt_srch": "Search",
		"udt_drop": "drop it here",

		"u_nav_m": '<h6>aight, what do you have?</h6><code>Enter</code> = Files (one or more)\n<code>ESC</code> = One folder (including subfolders)',
		"u_nav_b": '<a href="#" id="modal-ok">Files</a><a href="#" id="modal-ng">One folder</a>',

		"cl_opts": "switches",
		"cl_themes": "theme",
		"cl_langs": "language",
		"cl_ziptype": "folder download",
		"cl_uopts": "up2k switches",
		"cl_favico": "favicon",
		"cl_bigdir": "big dirs",
		"cl_keytype": "key notation",
		"cl_hiddenc": "hidden columns",
		"cl_hidec": "hide",
		"cl_reset": "reset",
		"cl_hpick": "click one column header to hide in the table below",
		"cl_hcancel": "column hiding aborted",

		"ct_thumb": "in icon view, toggle icons or thumbnails$NHotkey: T",
		"ct_dots": "show hidden files (if server permits)",
		"ct_dir1st": "sort folders before files",
		"ct_readme": "show README.md in folder listings",
		"ct_sbars": "show scrollbars",

		"cut_turbo": "the yolo button, you probably DO NOT want to enable this:$N$Nuse this if you were uploading a huge amount of files and had to restart for some reason, and want to continue the upload ASAP$N$Nthis replaces the hash-check with a simple <em>&quot;does this have the same filesize on the server?&quot;</em> so if the file contents are different it will NOT be uploaded$N$Nyou should turn this off when the upload is done, and then &quot;upload&quot; the same files again to let the client verify them",

		"cut_datechk": "has no effect unless the turbo button is enabled$N$Nreduces the yolo factor by a tiny amount; checks whether the file timestamps on the server matches yours$N$Nshould <em>theoretically</em> catch most unfinished / corrupted uploads, but is not a substitute for doing a verification pass with turbo disabled afterwards",

		"cut_flag": "ensure only one tab is uploading at a time $N -- other tabs must have this enabled too $N -- only affects tabs on the same domain",

		"cut_az": "upload files in alphabetical order, rather than smallest-file-first$N$Nalphabetical order can make it easier to eyeball if something went wrong on the server, but it makes uploading slightly slower on fiber / LAN",

		"cut_nag": "OS notification when upload completes$N(only if the browser or tab is not active)",
		"cut_sfx": "audible alert when upload completes$N(only if the browser or tab is not active)",

		"cut_mt": "use multithreading to accelerate file hashing$N$Nthis uses web-workers and requires$Nmore RAM (up to 512 MiB extra)$N$N30% faster https, 4.5x faster http,$Nand 5.3x faster on android phones",

		"cft_text": "favicon text (blank and refresh to disable)",
		"cft_fg": "foreground color",
		"cft_bg": "background color",

		"cdt_lim": "max number of files to show in a folder",
		"cdt_ask": "when scrolling to the bottom,$Ninstead of loading more files,$Nask what to do",

		"tt_entree": "show navpane (directory tree sidebar)$NHotkey: B",
		"tt_detree": "show breadcrumbs$NHotkey: B",
		"tt_visdir": "scroll to selected folder",
		"tt_ftree": "toggle folder-tree / textfiles$NHotkey: V",
		"tt_pdock": "show parent folders in a docked pane at the top",
		"tt_dynt": "autogrow as tree expands",
		"tt_wrap": "word wrap",
		"tt_hover": "reveal overflowing lines on hover$N( breaks scrolling unless mouse $N&nbsp; cursor is in the left gutter )",

		"ml_pmode": "playback mode",
		"ml_tcode": "transcode",
		"ml_tint": "tint",
		"ml_eq": "audio equalizer",

		"mt_preload": "start loading the next song near the end for gapless playback\">preload",
		"mt_fullpre": "try to preload the entire song;$N✅ enable on <b>unreliable</b> connections,$N❌ <b>disable</b> on slow connections probably\">full",
		"mt_waves": "waveform seekbar:$Nshow audio amplitude in the scrubber\">~s",
		"mt_npclip": "show buttons for clipboarding the currently playing song\">/np",
		"mt_octl": "os integration (media hotkeys / osd)\">os-ctl",
		"mt_oseek": "allow seeking through os integration\">seek",
		"mt_oscv": "show album cover in osd\">art",
		"mt_follow": "keep the playing track scrolled into view\">🎯",
		"mt_compact": "compact controls\">⟎",
		"mt_mloop": "loop the open folder\">🔁 loop",
		"mt_mnext": "load the next folder and continue\">📂 next",
		"mt_cflac": "convert flac / wav to opus\">flac",
		"mt_caac": "convert aac / m4a to opus\">aac",
		"mt_coth": "convert all others (not mp3) to opus\">oth",
		"mt_tint": "background level (0-100) on the seekbar$Nto make buffering less distracting",
		"mt_eq": "enables the equalizer and gain control;$N$Nboost &lt;code&gt;0&lt;/code&gt; = standard 100% volume (unmodified)$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = standard stereo (unmodified)$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% left-right crossfeed$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = vocal removal :^)$N$Nenabling the equalizer makes gapless albums fully gapless, so leave it on with all the values at zero (except width = 1) if you care about that",

		"mb_play": "play",
		"mm_hashplay": "play this audio file?",
		"mp_breq": "need firefox 82+ or chrome 73+ or iOS 15+",
		"mm_opusen": "your browser cannot play aac / m4a files;\ntranscoding to opus is now enabled",
		"mm_playerr": "playback failed: ",
		"mm_eabrt": "The playback attempt was cancelled",
		"mm_enet": "Your internet connection is wonky",
		"mm_edec": "This file is supposedly corrupted??",
		"mm_esupp": "Your browser does not understand this audio format",
		"mm_eunk": "Unknown Errol",
		"mm_e404": "Could not play audio; error 404: File not found.",
		"mm_e403": "Could not play audio; error 403: Access denied.\n\nTry pressing F5 to reload, maybe you got logged out",
		"mm_e5xx": "Could not play audio; server error ",

		"f_chide": 'this will hide the column «{0}»\n\nyou can unhide columns in the settings tab',
		"f_bigtxt": "this file is {0} MiB large -- really view as text?",
		"fbd_more": '<div id="blazy">showing <code>{0}</code> of <code>{1}</code> files; <a href="#" id="bd_more">show {2}</a> or <a href="#" id="bd_all">show all</a></div>',
		"fbd_all": '<div id="blazy">showing <code>{0}</code> of <code>{1}</code> files; <a href="#" id="bd_all">show all</a></div>',

		"f_dls": 'the file links in the current folder have\nbeen changed into download links',

		"ft_paste": "paste {0} items$NHotkey: ctrl-V",
		"fr_eperm": 'cannot rename:\nyou do not have “move” permission in this folder',
		"fd_eperm": 'cannot delete:\nyou do not have “delete” permission in this folder',
		"fc_eperm": 'cannot cut:\nyou do not have “move” permission in this folder',
		"fp_eperm": 'cannot paste:\nyou do not have “write” permission in this folder',
		"fr_emore": "select at least one item to rename",
		"fd_emore": "select at least one item to delete",
		"fc_emore": "select at least one item to cut",

		"frt_dec": "may fix some cases of broken filenames\">url-decode",
		"frt_rst": "reset modified filenames back to the original ones\">↺ reset",
		"frt_abrt": "abort and close this window\">❌ cancel",
		"frb_apply": "APPLY RENAME",
		"fr_adv": "batch / metadata / pattern renaming\">advanced",
		"fr_case": "case-sensitive regex\">case",
		"fr_pdel": "delete",
		"fr_pnew": "save as",
		"fr_pname": "provide a name for your new preset",
		"fr_aborted": "aborted",
		"fr_lold": "old name",
		"fr_lnew": "new name",
		"fr_tags": "tags for the selected files (read-only, just for reference):",
		"fr_busy": "renaming {0} items...\n\n{1}",
		"fr_efail": "rename failed:\n",

		"fd_ok": "delete OK",
		"fd_err": "delete failed:\n",
		"fd_busy": "deleting {0} items...\n\n{1}",
		"fd_warn1": "DELETE these {0} items?",
		"fd_warn2": "<b>Last chance!</b> No way to undo. Delete?",

		"fc_ok": "cut {0} items",
		"fc_warn": 'cut {0} items\n\nbut: only <b>this</b> browser-tab can paste them\n(since the selection is so absolutely massive)',

		"fp_ecut": "first cut some files / folders to paste / move\n\nnote: you can cut / paste across different browser tabs",
		"fp_ename": "these {0} items cannot be moved here (names already exist):",
		"fp_ok": "move OK",
		"fp_busy": "moving {0} items...\n\n{1}",
		"fp_err": "move failed:\n",
		"fp_confirm": "move these {0} items here?",
		"fp_etab": 'failed to read clipboard from other browser tab',

		"tv_load": "Loading text document:\n\n{0}\n\n{1}% ({2} of {3} MiB loaded)",
		"tv_xe1": "could not load textfile:\n\nerror ",
		"tv_xe2": "404, file not found",
		"tv_lst": "list of textfiles in",
		"tvt_close": "return to folder view$NHotkey: M\">❌ close",
		"tvt_dl": "download this file\">💾 download",
		"tvt_prev": "show previous document$NHotkey: i\">⬆ prev",
		"tvt_next": "show next document$NHotkey: K\">⬇ next",
		"tvt_sel": "select file &nbsp; ( for cut / delete / ... )$NHotkey: S\">sel",

		"gt_msel": "enable file selection; ctrl-click a file to override$N$N&lt;em&gt;when active: doubleclick a file / folder to open it&lt;/em&gt;$N$NHotkey: S\">multiselect",
		"gt_zoom": "zoom",
		"gt_chop": "chop",
		"gt_sort": "sort by",
		"gt_name": "name",
		"gt_sz": "size",
		"gt_ts": "date",
		"gt_ext": "type",
		"gt_c1": "truncate filenames more (show less)",
		"gt_c2": "truncate filenames less (show more)",

		"sm_prev": "search results below are from a previous query:\n  ",
		"sl_close": "close search results",
		"sl_hits": "showing {0} hits",
		"sl_moar": "load more",

		"s_sz": "size",
		"s_dt": "date",
		"s_rd": "path",
		"s_fn": "name",
		"s_ta": "tags",
		"s_ad": "adv.",
		"s_s1": "minimum MiB",
		"s_s2": "maximum MiB",
		"s_d1": "min. iso8601",
		"s_d2": "max. iso8601",
		"s_r1": "path contains &nbsp; (space-separated)",
		"s_f1": "name contains &nbsp; (negate with -nope)",
		"s_t1": "tags contains &nbsp; (^=start, end=$)",
		"s_a1": "specific metadata properties",

		"md_eshow": "cannot show ",

		"xhr403": "403: Access denied\n\ntry pressing F5, maybe you got logged out",
		"cf_ok": "sorry about that -- DD" + wah + "oS protection kicked in\n\nthings should resume in about 30 sec\n\nif nothing happens, hit F5 to reload the page",
		"tl_xe1": "could not list subfolders:\n\nerror ",
		"tl_xe2": "404: Folder not found",
		"fl_xe1": "could not list files in folder:\n\nerror ",
		"fl_xe2": "404: Folder not found",
		"fd_xe1": "could not create subfolder:\n\nerror ",
		"fd_xe2": "404: Parent folder not found",
		"fsm_xe1": "could not send message:\n\nerror ",
		"fsm_xe2": "404: Parent folder not found",
		"fu_xe1": "failed to load unpost list from server:\n\nerror ",
		"fu_xe2": "404: File not found??",

		"fz_tar": "plain gnutar file (linux / mac)",
		"fz_zip8": "zip with utf8 filenames (maybe wonky on windows 7 and older)",
		"fz_zipd": "zip with traditional cp437 filenames, for really old software",
		"fz_zipc": "cp437 with crc32 computed early,$Nfor MS-DOS PKZIP v2.04g (october 1993)$N(takes longer to process before download can start)",

		"un_m1": "you can delete your recent uploads below",
		"un_upd": "refresh list",
		"un_flt": "optional filter:&nbsp; URL must contain",
		"un_fclr": "clear filter",
		"un_derr": 'unpost-delete failed:\n',
		"un_f5": 'something broke, please try a refresh or hit F5',
		"un_max": "showing first 2000 files (use the filter)",
		"un_avail": "{0} uploads can be deleted",
		"un_m2": "sorted by upload time &ndash; most recent first:",
		"un_no1": "sike! no uploads are sufficiently recent",
		"un_no2": "sike! no uploads matching that filter are sufficiently recent",
		"un_next": "delete the next {0} files below",
		"un_del": "delete",
		"un_m3": "loading your recent uploads...",
		"un_busy": "deleting {0} files...",

		"u_https1": "you should",
		"u_https2": "switch to https",
		"u_https3": "for better performance",
		"u_ancient": 'your browser is impressively ancient -- maybe you should <a href="#" onclick="goto(\'bup\')">use bup instead</a>',
		"u_nowork": "need firefox 53+ or chrome 57+ or iOS 11+",
		"u_enpot": 'switch to <a href="#">potato UI</a> (may improve upload speed)',
		"u_depot": 'switch to <a href="#">fancy UI</a> (may reduce upload speed)',
		"u_gotpot": 'switching to the potato UI for improved upload speed,\n\nfeel free to disagree and switch back!',
		"u_ever": "this is the basic uploader; up2k needs at least<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'this is the basic uploader; <a href="#" id="u2yea">up2k</a> is better',
		"u_ewrite": 'you do not have write-access to this folder',
		"u_eread": 'you do not have read-access to this folder',
		"u_enoi": 'file-search is not enabled in server config',
		"u_badf": 'These {0} files (of {1} total) were skipped, possibly due to filesystem permissions:\n\n',
		"u_blankf": 'These {0} files (of {1} total) are blank / empty; upload them anyways?\n\n',
		"u_just1": '\nMaybe it works better if you select just one file',
		"u_ff_many": "This amount of files <em>may</em> cause Firefox to skip some files, or crash.\nPlease try again with fewer files (or use Chrome) if that happens.",
		"u_up_life": "This upload will be deleted from the server\n{0} after it completes",
		"u_asku": 'upload these {0} files to <code>{1}</code>',
		"u_unpt": "you can undo / delete this upload using the top-left 🧯",
		"u_etadone": 'Done ({0}, {1} files)',
		"u_etaprep": '(preparing to upload)',
		"u_hashdone": 'hashing done',
		"u_hashing": 'hash',
		"u_fixed": "OK!&nbsp; Fixed it 👍",
		"u_cuerr": "failed to upload chunk {0} of {1};\nprobably harmless, continuing\n\nfile: {2}",
		"u_cuerr2": "server rejected upload (chunk {0} of {1});\nwill retry later\n\nfile: {2}\n\nerror ",
		"u_ehstmp": "will retry; see bottom-right",
		"u_ehsfin": "server rejected the request to finalize upload; retrying...",
		"u_ehssrch": "server rejected the request to perform search; retrying...",
		"u_ehsinit": "server rejected the request to initiate upload; retrying...",
		"u_eneths": "network error while performing upload handshake; retrying...",
		"u_enethd": "network error while testing target existence; retrying...",
		"u_ehsdf": "server ran out of disk space!\n\nwill keep retrying, in case someone\nfrees up enough space to continue",
		"u_emtleak1": "it looks like your webbrowser may have a memory leak;\nplease",
		"u_emtleak2": ' <a href="{0}">switch to https (recommended)</a> or ',
		"u_emtleak3": ' ',
		"u_emtleakc": 'try the following:\n<ul><li>hit <code>F5</code> to refresh the page</li><li>then disable the &nbsp;<code>mt</code>&nbsp; button in the &nbsp;<code>⚙️ settings</code></li><li>and try that upload again</li></ul>Uploads will be a bit slower, but oh well.\nSorry for the trouble !\n\nPS: chrome v107 <a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816">has a bugfix</a> for this',
		"u_emtleakf": 'try the following:\n<ul><li>hit <code>F5</code> to refresh the page</li><li>then enable <code>🥔</code> (potato) in the upload UI<li>and try that upload again</li></ul>\nPS: firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500">will hopefully have a bugfix</a> at some point',
		"u_s404": "not found on server",
		"u_expl": "explain",
		"u_tu": '<p class="warn">WARNING: turbo enabled, <span>&nbsp;client may not detect and resume incomplete uploads; see turbo-button tooltip</span></p>',
		"u_ts": '<p class="warn">WARNING: turbo enabled, <span>&nbsp;search results can be incorrect; see turbo-button tooltip</span></p>',
		"u_life_cfg": 'autodelete after <input id="lifem" p="60" /> min (or <input id="lifeh" p="3600" /> hours)',
		"u_life_est": 'upload will be deleted <span id="lifew" tt="local time">---</span>',
		"u_life_max": 'this folder enforces a\nmax lifetime of {0}',
		"u_unp_ok": 'unpost is allowed for {0}',
		"u_unp_ng": 'unpost will NOT be allowed',
		"ue_ro": 'your access to this folder is Read-Only\n\n',
		"ue_nl": 'you are currently not logged in',
		"ue_la": 'you are currently logged in as "{0}"',
		"ue_sr": 'you are currently in file-search mode\n\nswitch to upload-mode by clicking the magnifying glass 🔎 (next to the big SEARCH button), and try uploading again\n\nsorry',
		"ue_ta": 'try uploading again, it should work now',
		"ur_1uo": "OK: File uploaded successfully",
		"ur_auo": "OK: All {0} files uploaded successfully",
		"ur_1so": "OK: File found on server",
		"ur_aso": "OK: All {0} files found on server",
		"ur_1un": "Upload failed, sorry",
		"ur_aun": "All {0} uploads failed, sorry",
		"ur_1sn": "File was NOT found on server",
		"ur_asn": "The {0} files were NOT found on server",
		"ur_um": "Finished;\n{0} uplads OK,\n{1} uploads failed, sorry",
		"ur_sm": "Finished;\n{0} files found on server,\n{1} files NOT found on server",

		"lang_set": "refresh to make the change take effect?",
	},
	"nor": {
		"tt": "Norsk",

		"cols": {
			"c": "handlingsknapper",
			"dur": "varighet",
			"q": "kvalitet / bitrate",
			"Ac": "lyd-format",
			"Vc": "video-format",
			"Fmt": "format / innpakning",
			"Ahash": "lyd-kontrollsum",
			"Vhash": "video-kontrollsum",
			"Res": "oppløsning",
			"T": "filtype",
			"aq": "lydkvalitet / bitrate",
			"vq": "videokvalitet / bitrate",
			"pixfmt": "fargekoding / detaljenivå",
			"resw": "horisontal oppløsning",
			"resh": "vertikal oppløsning",
			"chs": "lydkanaler",
			"hz": "lyd-oppløsning"
		},

		"hks": [
			[
				"ymse",
				["ESC", "lukk saker og ting"],

				"filbehandler",
				["G", "listevisning eller ikoner"],
				["T", "miniatyrbilder på/av"],
				["🡅 A/D", "ikonstørrelse"],
				["ctrl-K", "slett valgte"],
				["ctrl-X", "klipp ut"],
				["ctrl-V", "lim inn"],
				["Y", "last ned valgte"],
				["F2", "endre navn på valgte"],

				"filmarkering",
				["space", "marker fil"],
				["🡑/🡓", "flytt markør"],
				["ctrl 🡑/🡓", "flytt markør og scroll"],
				["🡅 🡑/🡓", "velg forr./neste fil"],
				["ctrl-A", "velg alle filer / mapper"],
			], [
				"navigering",
				["B", "mappehierarki eller filsti"],
				["I/K", "forr./neste mappe"],
				["M", "ett nivå opp (eller lukk)"],
				["V", "vis mapper eller tekstfiler"],
				["A/D", "panelstørrelse"],
			], [
				"musikkspiller",
				["J/L", "forr./neste sang"],
				["U/O", "hopp 10sek bak/frem"],
				["0..9", "hopp til 0%..90%"],
				["P", "pause, eller start / fortsett"],
				["Y", "last ned sang"],
			], [
				"bildeviser",
				["J/L, ←/→", "forr./neste bilde"],
				["Home/End", "første/siste bilde"],
				["F", "fullskjermvisning"],
				["R", "rotere mot høyre"],
				["🡅 R", "rotere mot venstre"],
				["Y", "last ned bilde"],
			], [
				"videospiller",
				["U/O", "hopp 10sek bak/frem"],
				["P/K/Space", "pause / fortsett"],
				["C", "fortsett til neste fil"],
				["V", "gjenta avspilling"],
				["M", "lyd av/på"],
				["[ og ]", "gjentaksintervall"],
			], [
				"dokumentviser",
				["I/K", "forr./neste fil"],
				["M", "lukk tekstdokument"],
				["S", "velg fil (for F2/ctrl-x/...)"]
			]
		],

		"m_ok": "OK",
		"m_ng": "Avbryt",

		"ht_s": "sekund!er",
		"ht_m": "minutt!er",
		"ht_h": "time!r",
		"ht_d": "dag!er",
		"ht_and": " og ",

		"goh": "kontrollpanel",
		"gop": 'naviger til mappen før denne">forr.',
		"gou": 'naviger ett nivå opp">opp',
		"gon": 'naviger til mappen etter denne">neste',
		"logout": "Logg ut ",
		"access": " tilgang",
		"ot_close": "lukk verktøy",
		"ot_search": "søk etter filer ved å angi filnavn, mappenavn, tid, størrelse, eller metadata som sangtittel / artist / osv.$N$N&lt;code&gt;foo bar&lt;/code&gt; = inneholder både «foo» og «bar»,$N&lt;code&gt;foo -bar&lt;/code&gt; = inneholder «foo» men ikke «bar»,$N&lt;code&gt;^yana .opus$&lt;/code&gt; = starter med «yana», filtype «opus»$N&lt;code&gt;&quot;try unite&quot;&lt;/code&gt; = «try unite» eksakt$N$Ndatoformat er iso-8601, så f.eks.$N&lt;code&gt;2009-12-31&lt;/code&gt; eller &lt;code&gt;2020-09-12 23:30:00&lt;/code&gt;",
		"ot_unpost": "unpost: slett filer som du nylig har lastet opp; «angre-knappen»",
		"ot_bup": "bup: tradisjonell / primitiv filopplastning,$N$Nfungerer i omtrent samtlige nettlesere",
		"ot_mkdir": "mkdir: lag en ny mappe",
		"ot_md": "new-md: lag et nytt markdown-dokument",
		"ot_msg": "msg: send en beskjed til serverloggen",
		"ot_mp": "musikkspiller-instillinger",
		"ot_cfg": "andre innstillinger",
		"ot_u2i": 'up2k: last opp filer (hvis du har skrivetilgang) eller bytt til søkemodus for å sjekke om filene finnes et-eller-annet sted på serveren$N$Nopplastninger kan gjenopptas etter avbrudd, skjer stykkevis for potensielt høyere ytelse, og ivaretar datostempling -- men bruker litt mer prosessorkraft enn den primitive opplasteren bup<br /><br />mens opplastninger foregår så vises fremdriften her oppe!',
		"ot_u2w": 'up2k: filopplastning med støtte for å gjenoppta avbrutte opplastninger -- steng ned nettleseren og dra de samme filene inn i nettleseren igjen for å plukke opp igjen der du slapp$N$Nopplastninger skjer stykkevis for potensielt høyere ytelse, og ivaretar datostempling -- men bruker litt mer prosessorkraft enn den primitive opplasteren "bup"<br /><br />mens opplastninger foregår så vises fremdriften her oppe!',

		"ab_mkdir": "lag mappe",
		"ab_mkdoc": "nytt dokument",
		"ab_msg": "send melding",

		"ay_path": "gå videre til mapper",
		"ay_files": "gå videre til filer",

		"wt_ren": "gi nye navn til de valgte filene$NSnarvei: F2",
		"wt_del": "slett de valgte filene$NSnarvei: ctrl-K",
		"wt_cut": "klipp ut de valgte filene &lt;small&gt;(for å lime inn et annet sted)&lt;/small&gt;$NSnarvei: ctrl-X",
		"wt_pst": "lim inn filer (som tidligere ble klippet ut et annet sted)$NSnarvei: ctrl-V",
		"wt_selall": "velg alle filer$NSnarvei: ctrl-A (mens fokus er på en fil)",
		"wt_selinv": "inverter utvalg",
		"wt_selzip": "last ned de valgte filene som et arkiv",
		"wt_seldl": "last ned de valgte filene$NSnarvei: Y",
		"wt_npirc": "kopier sang-info (irc-formattert)",
		"wt_nptxt": "kopier sang-info",
		"wt_grid": "bytt mellom ikoner og listevisning$NSnarvei: G",
		"wt_prev": "forrige sang$NSnarvei: J",
		"wt_play": "play / pause$NSnarvei: P",
		"wt_next": "neste sang$NSnarvei: L",

		"ul_par": "samtidige handl.:",
		"ut_mt": "fortsett å befare køen mens opplastning foregår$N$Nskru denne av dersom du har en$Ntreg prosessor eller harddisk",
		"ut_ask": "bekreft filutvalg før opplastning starter",
		"ut_pot": "forbedre ytelsen på trege enheter ved å$Nforenkle brukergrensesnittet",
		"ut_srch": "utfør søk istedenfor å laste opp --$Nleter igjennom alle mappene du har lov til å se",
		"ut_par": "sett til 0 for å midlertidig stanse opplastning$N$Nhøye verdier (4 eller 8) kan gi bedre ytelse,$Nspesielt på trege internettlinjer$N$Nbør ikke være høyere enn 1 på LAN$Neller hvis serveren sin harddisk er treg",
		"ul_btn": "slipp filer / mapper<br>her (eller klikk meg)",
		"ul_btnu": "L A S T &nbsp; O P P",
		"ul_btns": "F I L S Ø K",

		"ul_hash": "befar",
		"ul_send": "&nbsp;send",
		"ul_done": "total",
		"ul_idle1": "ingen handlinger i køen",
		"ut_etah": "snitthastighet for &lt;em&gt;befaring&lt;/em&gt; samt gjenstående tid",
		"ut_etau": "snitthastighet for &lt;em&gt;opplastning&lt;/em&gt; samt gjenstående tid",
		"ut_etat": "&lt;em&gt;total&lt;/em&gt; snitthastighet og gjenstående tid",

		"uct_ok": "fullført uten problemer",
		"uct_ng": "fullført under tvil (duplikat, ikke funnet, ...)",
		"uct_done": "fullført (enten &lt;em&gt;ok&lt;/em&gt; eller &lt;em&gt;ng&lt;/em&gt;)",
		"uct_bz": "aktive handlinger (befaring / opplastning)",
		"uct_q": "køen",

		"utl_name": "filnavn",
		"utl_stat": "status",
		"utl_prog": "fremdrift",

		"ul_flagblk": "filene har blitt lagt i køen</b><br>men det er en annen nettleserfane som holder på med befaring eller opplastning akkurat nå,<br>så venter til den er ferdig først",

		"udt_up": "Last opp",
		"udt_srch": "Søk",
		"udt_drop": "Slipp filene her",

		"u_nav_m": '<h6>hva har du?</h6><code>Enter</code> = Filer (én eller flere)\n<code>ESC</code> = Én mappe (inkludert undermapper)',
		"u_nav_b": '<a href="#" id="modal-ok">Filer</a><a href="#" id="modal-ng">Én mappe</a>',

		"cl_opts": "brytere",
		"cl_themes": "utseende",
		"cl_langs": "språk",
		"cl_ziptype": "nedlastning av mapper",
		"cl_uopts": "up2k-brytere",
		"cl_favico": "favicon",
		"cl_bigdir": "store mapper",
		"cl_keytype": "notasjon for musikalsk dur",
		"cl_hiddenc": "skjulte kolonner",
		"cl_hidec": "skjul",
		"cl_reset": "nullstill",
		"cl_hpick": "klikk overskriften til kolonnen du ønsker å skjule i tabellen nedenfor",
		"cl_hcancel": "kolonne-skjuling avbrutt",

		"ct_thumb": "vis miniatyrbilder istedenfor ikoner$NSnarvei: T",
		"ct_dots": "vis skjulte filer (gitt at serveren tillater det)",
		"ct_dir1st": "sorter slik at mapper kommer foran filer",
		"ct_readme": "vis README.md nedenfor filene",
		"ct_sbars": "vis rullgardiner / skrollefelt",

		"cut_turbo": "forenklet befaring ved opplastning; bør sannsynlig <em>ikke</em> skrus på:$N$Nnyttig dersom du var midt i en svær opplastning som måtte restartes av en eller annen grunn, og du vil komme igang igjen så raskt som overhodet mulig.$N$Nnår denne er skrudd på så forenkles befaringen kraftig; istedenfor å utføre en trygg sjekk på om filene finnes på serveren i god stand, så sjekkes kun om <em>filstørrelsen</em> stemmer. Så dersom en korrupt fil skulle befinne seg på serveren allerede, på samme sted med samme størrelse og navn, så blir det <em>ikke oppdaget</em>.$N$Ndet anbefales å kun benytte denne funksjonen for å komme seg raskt igjennom selve opplastningen, for så å skru den av, og til slutt &quot;laste opp&quot; de samme filene én gang til -- slik at integriteten kan verifiseres",

		"cut_datechk": "har ingen effekt dersom turbo er avslått$N$Ngjør turbo bittelitt tryggere ved å sjekke datostemplingen på filene (i tillegg til filstørrelse)$N$N<em>burde</em> oppdage og gjenoppta de fleste ufullstendige opplastninger, men er <em>ikke</em> en fullverdig erstatning for å deaktivere turbo og gjøre en skikkelig sjekk",

		"cut_flag": "samkjører nettleserfaner slik at bare én $N kan holde på med befaring / opplastning $N -- andre faner må også ha denne skrudd på $N -- fungerer kun innenfor samme domene",

		"cut_az": "last opp filer i alfabetisk rekkefølge, istedenfor minste-fil-først$N$Nalfabetisk kan gjøre det lettere å anslå om alt gikk bra, men er bittelitt tregere på fiber / LAN",

		"cut_nag": "meldingsvarsel når opplastning er ferdig$N(kun on nettleserfanen ikke er synlig)",
		"cut_sfx": "lydvarsel når opplastning er ferdig$N(kun on nettleserfanen ikke er synlig)",

		"cut_mt": "raskere befaring ved å bruke hele CPU'en$N$Ndenne funksjonen anvender web-workers$Nog krever mer RAM (opptil 512 MiB ekstra)$N$N30% raskere https, 4.5x raskere http,$Nog 5.3x raskere på android-telefoner",

		"cft_text": "ikontekst (blank ut og last siden på nytt for å deaktivere)",
		"cft_fg": "farge",
		"cft_bg": "bakgrunnsfarge",

		"cdt_lim": "maks antall filer å vise per mappe",
		"cdt_ask": "vis knapper for å laste flere filer nederst på siden istedenfor å gradvis laste mer av mappen når man scroller ned",

		"tt_entree": "bytt til mappehierarki$NSnarvei: B",
		"tt_detree": "bytt til tradisjonell sti-visning$NSnarvei: B",
		"tt_visdir": "bla ned til den åpne mappen",
		"tt_ftree": "bytt mellom filstruktur og tekstfiler$NSnarvei: V",
		"tt_pdock": "vis de overordnede mappene i et panel",
		"tt_dynt": "øk bredden på panelet ettersom treet utvider seg",
		"tt_wrap": "linjebryting",
		"tt_hover": "vis hele mappenavnet når musepekeren treffer mappen$N( gjør dessverre at scrollhjulet fusker dersom musepekeren ikke befinner seg i grøfta )",

		"ml_pmode": "spillemodus",
		"ml_tcode": "konvertering",
		"ml_tint": "tint",
		"ml_eq": "audio equalizer (tonejustering)",

		"mt_preload": "hent ned litt av neste sang i forkant,$Nslik at pausen i overgangen blir mindre\">forles",
		"mt_fullpre": "hent ned hele neste sang, ikke bare litt:$N✅ skru på hvis nettet ditt er <b>ustabilt</b>,$N❌ skru av hvis nettet ditt er <b>tregt</b>\">full",
		"mt_waves": "waveform seekbar:$Nvis volumkurve i avspillingsfeltet\">~s",
		"mt_npclip": "vis knapper for å kopiere info om sangen du hører på\">/np",
		"mt_octl": "integrering med operativsystemet (fjernkontroll, info-skjerm)\">os-ctl",
		"mt_oseek": "tillat spoling med fjernkontroll\">spoling",
		"mt_oscv": "vis album-cover på infoskjermen\">bilde",
		"mt_follow": "bla slik at sangen som spilles alltid er synlig\">🎯",
		"mt_compact": "tettpakket avspillerpanel\">⟎",
		"mt_mloop": "repeter hele mappen\">🔁 gjenta",
		"mt_mnext": "hopp til neste mappe og fortsett\">📂 neste",
		"mt_cflac": "konverter flac / wav-filer til opus\">flac",
		"mt_caac": "konverter aac / m4a-filer til to opus\">aac",
		"mt_coth": "konverter alt annet (men ikke mp3) til opus\">andre",
		"mt_tint": "nivå av bakgrunnsfarge på søkestripa (0-100),$Ngjør oppdateringer mindre distraherende",
		"mt_eq": "aktiver tonekontroll og forsterker;$N$Nboost &lt;code&gt;0&lt;/code&gt; = normal volumskala$N$Nwidth &lt;code&gt;1 &nbsp;&lt;/code&gt; = normal stereo$Nwidth &lt;code&gt;0.5&lt;/code&gt; = 50% blanding venstre-høyre$Nwidth &lt;code&gt;0 &nbsp;&lt;/code&gt; = mono$N$Nboost &lt;code&gt;-0.8&lt;/code&gt; &amp; width &lt;code&gt;10&lt;/code&gt; = instrumental :^)$N$Nreduserer også dødtid imellom sangfiler",

		"mb_play": "lytt",
		"mm_hashplay": "spill denne sangen?",
		"mp_breq": "krever firefox 82+, chrome 73+, eller iOS 15+",
		"mm_opusen": "nettleseren din forstår ikke aac / m4a;\nkonvertering til opus er nå aktivert",
		"mm_playerr": "avspilling feilet: ",
		"mm_eabrt": "Avspillingsforespørselen ble avbrutt",
		"mm_enet": "Nettet ditt er ustabilt",
		"mm_edec": "Noe er galt med musikkfilen",
		"mm_esupp": "Nettleseren din forstår ikke filtypen",
		"mm_eunk": "Ukjent feil",
		"mm_e404": "Avspilling feilet: Fil ikke funnet.",
		"mm_e403": "Avspilling feilet: Tilgang nektet.\n\nKanskje du ble logget ut?\nPrøv å trykk F5 for å laste siden på nytt.",
		"mm_e5xx": "Avspilling feilet: ",

		"f_chide": 'dette vil skjule kolonnen «{0}»\n\nfanen for "andre innstillinger" lar deg vise kolonnen igjen',
		"f_bigtxt": "denne filen er hele {0} MiB -- vis som tekst?",
		"fbd_more": '<div id="blazy">viser <code>{0}</code> av <code>{1}</code> filer; <a href="#" id="bd_more">vis {2}</a> eller <a href="#" id="bd_all">vis alle</a></div>',
		"fbd_all": '<div id="blazy">viser <code>{0}</code> av <code>{1}</code> filer; <a href="#" id="bd_all">vis alle</a></div>',

		"f_dls": 'linkene i denne mappen er nå\nomgjort til nedlastningsknapper',

		"ft_paste": "Lim inn {0} filer$NSnarvei: ctrl-V",
		"fr_eperm": 'kan ikke endre navn:\ndu har ikke “move”-rettigheten i denne mappen',
		"fd_eperm": 'kan ikke slette:\ndu har ikke “delete”-rettigheten i denne mappen',
		"fc_eperm": 'kan ikke klippe ut:\ndu har ikke “move”-rettigheten i denne mappen',
		"fp_eperm": 'kan ikke lime inn:\ndu har ikke "write"-rettigheten i denne mappen',
		"fr_emore": "velg minst én fil som skal få nytt navn",
		"fd_emore": "velg minst én fil som skal slettes",
		"fc_emore": "velg minst én fil som skal klippes ut",

		"frt_dec": "kan korrigere visse ødelagte filnavn\">url-decode",
		"frt_rst": "nullstiller endringer (tilbake til de originale filnavnene)\">↺ reset",
		"frt_abrt": "avbryt og lukk dette vinduet\">❌ avbryt",
		"frb_apply": "IVERKSETT",
		"fr_adv": "automasjon basert på metadata<br>og / eller mønster (regulære uttrykk)\">avansert",
		"fr_case": "versalfølsomme uttrykk\">Aa",
		"fr_pdel": "slett",
		"fr_pnew": "lagre som",
		"fr_pname": "gi innstillingene dine et navn",
		"fr_aborted": "avbrutt",
		"fr_lold": "gammelt navn",
		"fr_lnew": "nytt navn",
		"fr_tags": "metadata for de valgte filene (kun for referanse):",
		"fr_busy": "endrer navn på {0} filer...\n\n{1}",
		"fr_efail": "endring av navn feilet:\n",

		"fd_ok": "sletting OK",
		"fd_err": "sletting feilet:\n",
		"fd_busy": "sletter {0} filer...\n\n{1}",
		"fd_warn1": "SLETT disse {0} filene?",
		"fd_warn2": "<b>Siste sjanse!</b> Dette kan ikke angres. Slett?",

		"fc_ok": "klippet ut {0} filer",
		"fc_warn": 'klippet ut {0} filer\n\nmen: kun <b>denne</b> nettleserfanen har mulighet til å lime dem inn et annet sted, siden antallet filer er helt hinsides',

		"fp_ecut": "du må klippe ut noen filer / mapper først\n\nmerk: du kan gjerne jobbe på kryss av nettleserfaner; klippe ut i én fane, lime inn i en annen",
		"fp_ename": "disse {0} filene kan ikke flyttes til målmappen fordi det allerede finnes filer med samme navn:",
		"fp_ok": "flytting OK",
		"fp_busy": "flytter {0} filer...\n\n{1}",
		"fp_err": "flytting feilet:\n",
		"fp_confirm": "flytt disse {0} filene hit?",
		"fp_etab": 'kunne ikke lese listen med filer ifra den andre nettleserfanen',

		"tv_load": "Laster inn tekstfil:\n\n{0}\n\n{1}% ({2} av {3} MiB lastet ned)",
		"tv_xe1": "kunne ikke laste tekstfil:\n\nfeil ",
		"tv_xe2": "404, Fil ikke funnet",
		"tv_lst": "tekstfiler i mappen",
		"tvt_close": "gå tilbake til mappen$NSnarvei: M\">❌ close",
		"tvt_dl": "last ned denne filen\">💾 last ned",
		"tvt_prev": "vis forrige dokument$NSnarvei: i\">⬆ prev",
		"tvt_next": "vis neste dokument$NSnarvei: K\">⬇ next",
		"tvt_sel": "markér filen &nbsp; ( for utklipp / sletting / ... )$NSnarvei: S\">sel",

		"gt_msel": "markér filer istedenfor å åpne dem; ctrl-klikk filer for å overstyre$N$N&lt;em&gt;når aktiv: dobbelklikk en fil / mappe for å åpne&lt;/em&gt;$N$NSnarvei: S\">markering",
		"gt_zoom": "zoom",
		"gt_chop": "trim",
		"gt_sort": "sorter",
		"gt_name": "navn",
		"gt_sz": "størr.",
		"gt_ts": "dato",
		"gt_ext": "type",
		"gt_c1": "reduser maks-lengde på filnavn",
		"gt_c2": "øk maks-lengde på filnavn",

		"sm_prev": "søkeresultatene er fra et tidligere søk:\n  ",
		"sl_close": "lukk søkeresultater",
		"sl_hits": "viser {0} treff",
		"sl_moar": "hent flere",

		"s_sz": "størr.",
		"s_dt": "dato",
		"s_rd": "sti",
		"s_fn": "navn",
		"s_ta": "meta",
		"s_ad": "avns.",
		"s_s1": "større enn ↓ MiB",
		"s_s2": "mindre enn ↓ MiB",
		"s_d1": "nyere enn &lt;dato&gt;",
		"s_d2": "eldre enn",
		"s_r1": "mappenavn inneholder",
		"s_f1": "filnavn inneholder",
		"s_t1": "sang-info inneholder",
		"s_a1": "konkrete egenskaper",

		"md_eshow": "kan ikke vise ",

		"xhr403": "403: Tilgang nektet\n\nkanskje du ble logget ut? prøv å trykk F5",
		"cf_ok": "beklager -- liten tilfeldig kontroll, alt OK\n\nting skal fortsette om ca. 30 sekunder\n\nhvis ikkeno skjer, trykk F5 for å laste siden på nytt",
		"tl_xe1": "kunne ikke hente undermapper:\n\nfeil ",
		"tl_xe2": "404: Mappen finnes ikke",
		"fl_xe1": "kunne ikke hente filer i mappen:\n\nfeil ",
		"fl_xe2": "404: Mappen finnes ikke",
		"fd_xe1": "kan ikke opprette ny mappe:\n\nfeil ",
		"fd_xe2": "404: Den overordnede mappen finnes ikke",
		"fsm_xe1": "kunne ikke sende melding:\n\nfeil ",
		"fsm_xe2": "404: Den overordnede mappen finnes ikke",
		"fu_xe1": "kunne ikke hente listen med nylig opplastede filer ifra serveren:\n\nfeil ",
		"fu_xe2": "404: Filen finnes ikke??",

		"fz_tar": "ukomprimert gnu-tar arkiv, for linux og mac",
		"fz_zip8": "zip med filnavn i utf8 (noe problematisk på windows 7 og eldre)",
		"fz_zipd": "zip med filnavn i cp437, for høggamle maskiner",
		"fz_zipc": "cp437 med tidlig crc32,$Nfor MS-DOS PKZIP v2.04g (oktober 1993)$N(øker behandlingstid på server)",

		"un_m1": "nedenfor kan du angre / slette filer som du nylig har lastet opp",
		"un_upd": "oppdater listen",
		"un_flt": "valgfritt filter:&nbsp; filnavn / filsti må inneholde",
		"un_fclr": "nullstill filter",
		"un_derr": 'unpost-sletting feilet:\n',
		"un_f5": 'noe gikk galt, prøv å oppdatere listen eller trykk F5',
		"un_max": "viser de første 2000 filene (bruk filteret for å innsnevre)",
		"un_avail": "{0} filer kan slettes",
		"un_m2": "sortert etter opplastningstid &ndash; nyeste først:",
		"un_no1": "men nei, her var det jaggu ikkeno som slettes kan",
		"un_no2": "men nei, her var det jaggu ingenting som passet overens med filteret",
		"un_next": "slett de neste {0} filene nedenfor",
		"un_del": "slett",
		"un_m3": "henter listen med nylig opplastede filer...",
		"un_busy": "sletter {0} filer...",

		"u_https1": "du burde",
		"u_https2": "bytte til https",
		"u_https3": "for høyere hastighet",
		"u_ancient": 'nettleseren din er prehistorisk -- mulig du burde <a href="#" onclick="goto(\'bup\')">bruke bup istedenfor</a>',
		"u_nowork": "krever firefox 53+, chrome 57+, eller iOS 11+",
		"u_enpot": 'bytt til <a href="#">enkelt UI</a> (gir sannsynlig raskere opplastning)',
		"u_depot": 'bytt til <a href="#">snæsent UI</a> (gir sannsynlig tregere opplastning)',
		"u_gotpot": 'byttet til et enklere UI for å laste opp raskere,\n\ndu kan gjerne bytte tilbake altså!',
		"u_ever": "dette er den primitive opplasteren; up2k krever minst:<br>chrome 21 // firefox 13 // edge 12 // opera 12 // safari 5.1",
		"u_su2k": 'dette er den primitive opplasteren; <a href="#" id="u2yea">up2k</a> er bedre',
		"u_ewrite": 'du har ikke skrivetilgang i denne mappen',
		"u_eread": 'du har ikke lesetilgang i denne mappen',
		"u_enoi": 'filsøk er deaktivert i serverkonfigurasjonen',
		"u_badf": 'Disse {0} filene (av totalt {1}) kan ikke leses, kanskje pga rettighetsproblemer i filsystemet på datamaskinen din:\n\n',
		"u_blankf": 'Disse {0} filene (av totalt {1}) er blanke / uten innhold; ønsker du å laste dem opp uansett?\n\n',
		"u_just1": '\nFunker kanskje bedre hvis du bare tar én fil om gangen',
		"u_ff_many": "Det var mange filer! Mulig at Firefox kommer til å krasje, eller\nhoppe over et par av dem. Smart å ha Chrome på lur i tilfelle.",
		"u_up_life": "Filene slettes fra serveren {0}\netter at opplastningen er fullført",
		"u_asku": 'Laste opp disse {0} filene til <code>{1}</code>',
		"u_unpt": "Du kan angre / slette opplastningen med 🧯 oppe til venstre",
		"u_etadone": 'Ferdig ({0}, {1} filer)',
		"u_etaprep": '(forbereder opplastning)',
		"u_hashdone": 'befaring ferdig',
		"u_hashing": 'les',
		"u_fixed": "OK!&nbsp; Løste seg 👍",
		"u_cuerr": "kunne ikke laste opp del {0} av {1};\nsikkert greit, fortsetter\n\nfil: {2}",
		"u_cuerr2": "server nektet opplastningen (del {0} av {1});\nprøver igjen senere\n\nfil: {2}\n\nerror ",
		"u_ehstmp": "prøver igjen; se mld nederst",
		"u_ehsfin": "server nektet forespørselen om å ferdigstille filen; prøver igjen...",
		"u_ehssrch": "server nektet forespørselen om å utføre søk; prøver igjen...",
		"u_ehsinit": "server nektet forespørselen om å begynne en ny opplastning; prøver igjen...",
		"u_eneths": "et problem med nettverket gjorde at avtale om opplastning ikke kunne inngås; prøver igjen...",
		"u_enethd": "et problem med nettverket gjorde at filsjekk ikke kunne utføres; prøver igjen...",
		"u_ehsdf": "serveren er full!\n\nprøver igjen regelmessig,\ni tilfelle noen rydder litt...",
		"u_emtleak1": "uff, det er mulig at nettleseren din har en minnelekkasje...\nForeslår",
		"u_emtleak2": ' helst at du <a href="{0}">bytter til https</a>, eller ',
		"u_emtleak3": ' at du ',
		"u_emtleakc": 'prøver følgende:\n<ul><li>trykk F5 for å laste siden på nytt</li><li>så skru av &nbsp;<code>mt</code>&nbsp; bryteren under &nbsp;<code>⚙️ innstillinger</code></li><li>og forsøk den samme opplastningen igjen</li></ul>Opplastning vil gå litt tregere, men det får så være.\nBeklager bryderiet !\n\nPS: feilen <a href="<a href="https://bugs.chromium.org/p/chromium/issues/detail?id=1354816">skal være fikset</a> i chrome v107',
		"u_emtleakf": 'prøver følgende:\n<ul><li>trykk F5 for å laste siden på nytt</li><li>så skru på <code>🥔</code> ("enkelt UI") i opplasteren</li><li>og forsøk den samme opplastningen igjen</li></ul>\nPS: Firefox <a href="https://bugzilla.mozilla.org/show_bug.cgi?id=1790500">fikser forhåpentligvis feilen</a> en eller annen gang',
		"u_s404": "ikke funnet på serveren",
		"u_expl": "forklar",
		"u_tu": '<p class="warn">ADVARSEL: turbo er på, <span>&nbsp;avbrutte opplastninger vil muligens ikke oppdages og gjenopptas; hold musepekeren over turbo-knappen for mer info</span></p>',
		"u_ts": '<p class="warn">ADVARSEL: turbo er på, <span>&nbsp;søkeresultater kan være feil; hold musepekeren over turbo-knappen for mer info</span></p>',
		"u_life_cfg": 'slett opplastning etter <input id="lifem" p="60" /> min (eller <input id="lifeh" p="3600" /> timer)',
		"u_life_est": 'opplastningen slettes <span id="lifew" tt="lokal tid">---</span>',
		"u_life_max": 'denne mappen tillater ikke å \noppbevare filer i mer enn {0}',
		"u_unp_ok": 'opplastning kan angres i {0}',
		"u_unp_ng": 'opplastning kan IKKE angres',
		"ue_ro": 'du har ikke skrivetilgang i denne mappen\n\n',
		"ue_nl": 'du er ikke logget inn',
		"ue_la": 'du er logget inn som "{0}"',
		"ue_sr": 'du er i filsøk-modus\n\nbytt til opplastning ved å klikke på forstørrelsesglasset 🔎 (ved siden av den store FILSØK-knappen) og prøv igjen\n\nsorry',
		"ue_ta": 'prøv å laste opp igjen, det burde funke nå',
		"ur_1uo": "OK: Filen ble lastet opp",
		"ur_auo": "OK: Alle {0} filene ble lastet opp",
		"ur_1so": "OK: Filen ble funnet på serveren",
		"ur_aso": "OK: Alle {0} filene ble funnet på serveren",
		"ur_1un": "Opplastning feilet!",
		"ur_aun": "Alle {0} opplastningene gikk feil!",
		"ur_1sn": "Filen finnes IKKE på serveren",
		"ur_asn": "Fant INGEN av de {0} filene på serveren",
		"ur_um": "Ferdig;\n{0} opplastninger gikk bra,\n{1} opplastninger gikk feil",
		"ur_sm": "Ferdig;\n{0} filer ble funnet,\n{1} filer finnes IKKE på serveren",

		"lang_set": "passer det å laste siden på nytt?",
	},
};
var L = Ls[sread("lang") || lang];
if (Ls.eng && L != Ls.eng) {
	for (var k in Ls.eng)
		if (!L[k])
			L[k] = Ls.eng[k];
}
modal.load();


// toolbar
ebi('ops').innerHTML = (
	'<a href="#" data-dest="" tt="' + L.ot_close + '">--</a>' +
	'<a href="#" data-perm="read" data-dep="idx" data-dest="search" tt="' + L.ot_search + '">🔎</a>' +
	(have_del && have_unpost ? '<a href="#" data-dest="unpost" data-dep="idx" tt="' + L.ot_unpost + '">🧯</a>' : '') +
	'<a href="#" data-dest="up2k">🚀</a>' +
	'<a href="#" data-perm="write" data-dest="bup" tt="' + L.ot_bup + '">🎈</a>' +
	'<a href="#" data-perm="write" data-dest="mkdir" tt="' + L.ot_mkdir + '">📂</a>' +
	'<a href="#" data-perm="read write" data-dest="new_md" tt="' + L.ot_md + '">📝</a>' +
	'<a href="#" data-perm="write" data-dest="msg" tt="' + L.ot_msg + '">📟</a>' +
	'<a href="#" data-dest="player" tt="' + L.ot_mp + '">🎺</a>' +
	'<a href="#" data-dest="cfg" tt="' + L.ot_cfg + '">⚙️</a>' +
	'<div id="opdesc"></div>'
);


// media player
ebi('widget').innerHTML = (
	'<div id="wtoggle">' +
	'<span id="wfm"><a' +
	' href="#" id="fren" tt="' + L.wt_ren + '">✎<span>name</span></a><a' +
	' href="#" id="fdel" tt="' + L.wt_del + '">⌫<span>del.</span></a><a' +
	' href="#" id="fcut" tt="' + L.wt_cut + '">✂<span>cut</span></a><a' +
	' href="#" id="fpst" tt="' + L.wt_pst + '">📋<span>paste</span></a>' +
	'</span><span id="wzip"><a' +
	' href="#" id="selall" tt="' + L.wt_selall + '">sel.<br />all</a><a' +
	' href="#" id="selinv" tt="' + L.wt_selinv + '">sel.<br />inv.</a><a' +
	' href="#" id="selzip" class="l1" tt="' + L.wt_selzip + '">zip</a><a' +
	' href="#" id="seldl" class="l1" tt="' + L.wt_seldl + '">dl</a>' +
	'</span><span id="wnp"><a' +
	' href="#" id="npirc" tt="' + L.wt_npirc + '">📋<span>irc</span></a><a' +
	' href="#" id="nptxt" tt="' + L.wt_nptxt + '">📋<span>txt</span></a>' +
	'</span><a' +
	'	href="#" id="wtgrid" tt="' + L.wt_grid + '">田</a><a' +
	'	href="#" id="wtico">♫</a>' +
	'</div>' +
	'<div id="widgeti">' +
	'	<div id="pctl"><a href="#" id="bprev" tt="' + L.wt_prev + '">⏮</a><a href="#" id="bplay" tt="' + L.wt_play + '">▶</a><a href="#" id="bnext" tt="' + L.wt_next + '">⏭</a></div>' +
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
	'		<td class="c" data-perm="read"><br />' + L.ul_par + '</td>\n' +
	'		<td class="c" rowspan="2">\n' +
	'			<input type="checkbox" id="multitask" />\n' +
	'			<label for="multitask" tt="' + L.ut_mt + '">🏃</label>\n' +
	'		</td>\n' +
	'		<td class="c" rowspan="2">\n' +
	'			<input type="checkbox" id="potato" />\n' +
	'			<label for="potato" tt="' + L.ut_pot + '">🥔</label>\n' +
	'		</td>\n' +
	'		<td class="c" rowspan="2">\n' +
	'			<input type="checkbox" id="ask_up" />\n' +
	'			<label for="ask_up" tt="' + L.ut_ask + '">💭</label>\n' +
	'		</td>\n' +
	'		<td class="c" data-perm="read" data-dep="idx" rowspan="2">\n' +
	'			<input type="checkbox" id="fsearch" />\n' +
	'			<label for="fsearch" tt="' + L.ut_srch + '">🔎</label>\n' +
	'		</td>\n' +
	'		<td data-perm="read" rowspan="2" id="u2btn_cw"></td>\n' +
	'		<td data-perm="read" rowspan="2" id="u2c3w"></td>\n' +
	'	</tr>\n' +
	'	<tr>\n' +
	'		<td class="c" data-perm="read">\n' +
	'			<a href="#" class="b" id="nthread_sub">&ndash;</a><input\n' +
	'				class="txtbox" id="nthread" value="2" tt="' + L.ut_par + '"/><a\n' +
	'				href="#" class="b" id="nthread_add">+</a><br />&nbsp;\n' +
	'		</td>\n' +
	'	</tr>\n' +
	'</table>\n' +

	'<div id="u2notbtn"></div>\n' +

	'<div id="u2btn_ct">\n' +
	'	<div id="u2btn" tabindex="0">\n' +
	'		<span id="u2bm"></span>\n' + L.ul_btn +
	'	</div>\n' +
	'</div>\n' +

	'<div id="u2c3t">\n' +

	'<div id="u2etaw"><div id="u2etas"><div class="o">\n' +
	L.ul_hash + ': <span id="u2etah" tt="' + L.ut_etah + '">(' + L.ul_idle1 + ')</span><br />\n' +
	L.ul_send + ': <span id="u2etau" tt="' + L.ut_etau + '">(' + L.ul_idle1 + ')</span><br />\n' +
	'	</div><span class="o">' +
	L.ul_done + ': </span><span id="u2etat" tt="' + L.ut_etat + '">(' + L.ul_idle1 + ')</span>\n' +
	'</div></div>\n' +

	'<div id="u2cards">\n' +
	'	<a href="#" act="ok" tt="' + L.uct_ok + '">ok <span>0</span></a><a\n' +
	'	href="#" act="ng" tt="' + L.uct_ng + '">ng <span>0</span></a><a\n' +
	'	href="#" act="done" tt="' + L.uct_done + '">done <span>0</span></a><a\n' +
	'	href="#" act="bz" tt="' + L.uct_bz + '" class="act">busy <span>0</span></a><a\n' +
	'	href="#" act="q" tt="' + L.uct_q + '">que <span>0</span></a>\n' +
	'</div>\n' +

	'</div>\n' +

	'<div id="u2tabw" class="na"><table id="u2tab">\n' +
	'	<thead>\n' +
	'		<tr>\n' +
	'			<td>' + L.utl_name + '</td>\n' +
	'			<td>' + L.utl_stat + '</td>\n' +
	'			<td>' + L.utl_prog + '</td>\n' +
	'		</tr>\n' +
	'	</thead>\n' +
	'	<tbody></tbody>\n' +
	'</table><div id="u2mu"></div></div>\n' +

	'<p id="u2flagblock"><b>' + L.ul_flagblk + '</p>\n' +
	'<div id="u2life"></div>' +
	'<div id="u2foot"></div>'
);


ebi('wrap').insertBefore(mknod('div', 'lazy'), ebi('epi'));


(function () {
	var o = mknod('div');
	o.innerHTML = (
		'<div id="drops">\n' +
		'	<div class="dropdesc" id="up_zd"><div>🚀 ' + L.udt_up + '<br /><span></span><div>🚀<b>' + L.udt_up + '</b></div><div><b>' + L.udt_up + '</b>🚀</div></div></div>\n' +
		'	<div class="dropdesc" id="srch_zd"><div>🔎 ' + L.udt_srch + '<br /><span></span><div>🔎<b>' + L.udt_srch + '</b></div><div><b>' + L.udt_srch + '</b>🔎</div></div></div>\n' +
		'	<div class="dropzone" id="up_dz" v="up_zd"></div>\n' +
		'	<div class="dropzone" id="srch_dz" v="srch_zd"></div>\n' +
		'</div>'
	);
	document.body.appendChild(o);
})();


// config panel
ebi('op_cfg').innerHTML = (
	'<div>\n' +
	'	<h3>' + L.cl_opts + '</h3>\n' +
	'	<div>\n' +
	'		<a id="tooltips" class="tgl btn" href="#" tt="◔ ◡ ◔">ℹ️ tooltips</a>\n' +
	'		<a id="griden" class="tgl btn" href="#" tt="' + L.wt_grid + '">田 the grid</a>\n' +
	'		<a id="thumbs" class="tgl btn" href="#" tt="' + L.ct_thumb + '">🖼️ thumbs</a>\n' +
	'		<a id="dotfiles" class="tgl btn" href="#" tt="' + L.ct_dots + '">dotfiles</a>\n' +
	'		<a id="dir1st" class="tgl btn" href="#" tt="' + L.ct_dir1st + '">📁 first</a>\n' +
	'		<a id="ireadme" class="tgl btn" href="#" tt="' + L.ct_readme + '">📜 readme</a>\n' +
	'		<a id="sbars" class="tgl btn" href="#" tt="' + L.ct_sbars + '">⟊</a>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div>\n' +
	'	<h3>' + L.cl_themes + '</h3>\n' +
	'	<div id="themes">\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div>\n' +
	'	<h3>' + L.cl_langs + '</h3>\n' +
	'	<div id="langs">\n' +
	'	</div>\n' +
	'</div>\n' +
	(have_zip ? (
		'<div><h3>' + L.cl_ziptype + '</h3><div id="arc_fmt"></div></div>\n'
	) : '') +
	'<div>\n' +
	'	<h3>' + L.cl_uopts + '</h3>\n' +
	'	<div>\n' +
	'		<a id="hashw" class="tgl btn" href="#" tt="' + L.cut_mt + '">mt</a>\n' +
	'		<a id="u2turbo" class="tgl btn ttb" href="#" tt="' + L.cut_turbo + '">turbo</a>\n' +
	'		<a id="u2tdate" class="tgl btn ttb" href="#" tt="' + L.cut_datechk + '">date-chk</a>\n' +
	'		<a id="flag_en" class="tgl btn" href="#" tt="' + L.cut_flag + '">💤</a>\n' +
	'		<a id="u2sort" class="tgl btn" href="#" tt="' + L.cut_az + '">az</a>\n' +
	'		<a id="upnag" class="tgl btn" href="#" tt="' + L.cut_nag + '">🔔</a>\n' +
	'		<a id="upsfx" class="tgl btn" href="#" tt="' + L.cut_sfx + '">🔊</a>\n' +
	'		</td>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div>\n' +
	'	<h3>' + L.cl_favico + ' <span id="ico1">🎉</span></h3>\n' +
	'	<div>\n' +
	'		<input type="text" id="icot" style="width:1.3em" value="" tt="' + L.cft_text + '" />' +
	'		<input type="text" id="icof" style="width:2em" value="" tt="' + L.cft_fg + '" />' +
	'		<input type="text" id="icob" style="width:2em" value="" tt="' + L.cft_bg + '" />' +
	'		</td>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div>\n' +
	'	<h3>' + L.cl_bigdir + '</h3>\n' +
	'	<div>\n' +
	'		<input type="text" id="bd_lim" value="250" style="width:4em" tt="' + L.cdt_lim + '" />' +
	'		<a id="bd_ask" class="tgl btn" href="#" tt="' + L.cdt_ask + '">ask</a>\n' +
	'		</td>\n' +
	'	</div>\n' +
	'</div>\n' +
	'<div><h3>' + L.cl_keytype + '</h3><div id="key_notation"></div></div>\n' +
	'<div><h3>' + L.cl_hiddenc + ' &nbsp;' + (MOBILE ? '<a href="#" id="hcolsh">' + L.cl_hidec + '</a> / ' : '') + '<a href="#" id="hcolsr">' + L.cl_reset + '</a></h3><div id="hcols"></div></div>'
);


// navpane
ebi('tree').innerHTML = (
	'<div id="treeh">\n' +
	'	<a href="#" id="detree" tt="' + L.tt_detree + '">🍞...</a>\n' +
	'	<a href="#" class="btn" step="2" id="twobytwo" tt="Hotkey: D">+</a>\n' +
	'	<a href="#" class="btn" step="-2" id="twig" tt="Hotkey: A">&ndash;</a>\n' +
	'	<a href="#" class="btn" id="visdir" tt="' + L.tt_visdir + '">🎯</a>\n' +
	'	<a href="#" class="tgl btn" id="filetree" tt="' + L.tt_ftree + '">📃</a>\n' +
	'	<a href="#" class="tgl btn" id="parpane" tt="' + L.tt_pdock + '">📌</a>\n' +
	'	<a href="#" class="tgl btn" id="dyntree" tt="' + L.tt_dynt + '">a</a>\n' +
	'	<a href="#" class="tgl btn" id="wraptree" tt="' + L.tt_wrap + '">↵</a>\n' +
	'	<a href="#" class="tgl btn" id="hovertree" tt="' + L.tt_hover + '">👀</a>\n' +
	'</div>\n' +
	'<ul id="docul"></ul>\n' +
	'<ul class="ntree" id="treepar"></ul>\n' +
	'<ul class="ntree" id="treeul"></ul>\n' +
	'<div id="thx_ff">&nbsp;</div>'
);
clmod(ebi('tree'), 'sbar', 1);
ebi('entree').setAttribute('tt', L.tt_entree);
ebi('goh').textContent = L.goh;
QS('#op_mkdir input[type="submit"]').value = L.ab_mkdir;
QS('#op_new_md input[type="submit"]').value = L.ab_mkdoc;
QS('#op_msg input[type="submit"]').value = L.ab_msg;


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
	if (input && !TOUCH) {
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

	clmod(document.documentElement, 'op_open', dest);

	if (treectl)
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
		par.insertBefore(files.childNodes[0], ebi('lazy'));
		files = ebi('files');
		return files;
	}
}


var ACtx = window.AudioContext || window.webkitAudioContext,
	hash0 = location.hash,
	mp;


var mpl = (function () {
	var have_mctl = 'mediaSession' in navigator && window.MediaMetadata;

	ebi('op_player').innerHTML = (
		'<div><h3>' + L.cl_opts + '</h3><div>' +
		'<a href="#" class="tgl btn" id="au_preload" tt="' + L.mt_preload + '</a>' +
		'<a href="#" class="tgl btn" id="au_fullpre" tt="' + L.mt_fullpre + '</a>' +
		'<a href="#" class="tgl btn" id="au_waves" tt="' + L.mt_waves + '</a>' +
		'<a href="#" class="tgl btn" id="au_npclip" tt="' + L.mt_npclip + '</a>' +
		'<a href="#" class="tgl btn" id="au_os_ctl" tt="' + L.mt_octl + '</a>' +
		'<a href="#" class="tgl btn" id="au_os_seek" tt="' + L.mt_oseek + '</a>' +
		'<a href="#" class="tgl btn" id="au_osd_cv" tt="' + L.mt_oscv + '</a>' +
		'<a href="#" class="tgl btn" id="au_follow" tt="' + L.mt_follow + '</a>' +
		'<a href="#" class="tgl btn" id="au_compact" tt="' + L.mt_compact + '</a>' +
		'</div></div>' +

		'<div><h3>' + L.ml_pmode + '</h3><div id="pb_mode">' +
		'<a href="#" class="tgl btn" m="loop" tt="' + L.mt_mloop + '</a>' +
		'<a href="#" class="tgl btn" m="next" tt="' + L.mt_mnext + '</a>' +
		'</div></div>' +

		(have_acode ? (
			'<div><h3>' + L.ml_tcode + '</h3><div>' +
			'<a href="#" id="ac_flac" class="tgl btn" tt="' + L.mt_cflac + '</a>' +
			'<a href="#" id="ac_aac" class="tgl btn" tt="' + L.mt_caac + '</a>' +
			'<a href="#" id="ac_oth" class="tgl btn" tt="' + L.mt_coth + '</a>' +
			'</div></div>'
		) : '') +

		'<div><h3>' + L.ml_tint + '</h3><div>' +
		'<input type="text" id="pb_tint" style="width:2.4em" value="0" tt="' + L.mt_tint + '" />' +
		'</div></div>' +

		'<div><h3>' + L.ml_eq + '</h3><div id="audio_eq"></div></div>');

	var r = {
		"pb_mode": (sread('pb_mode') || 'next').split('-')[0],
		"os_ctl": bcfg_get('au_os_ctl', have_mctl) && have_mctl,
	};
	bcfg_bind(r, 'preload', 'au_preload', true);
	bcfg_bind(r, 'fullpre', 'au_fullpre', false);
	bcfg_bind(r, 'waves', 'au_waves', true, function (v) {
		if (!v) pbar.unwave();
	});
	bcfg_bind(r, 'os_seek', 'au_os_seek', !IPHONE, announce);
	bcfg_bind(r, 'osd_cv', 'au_osd_cv', true, announce);
	bcfg_bind(r, 'clip', 'au_npclip', false, function (v) {
		clmod(ebi('wtoggle'), 'np', v && mp.au);
	});
	bcfg_bind(r, 'follow', 'au_follow', false, setaufollow);
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
			toast.err(5, L.mp_breq);
	};

	function draw_pb_mode() {
		var btns = QSA('#pb_mode>a');
		for (var a = 0, aa = btns.length; a < aa; a++) {
			clmod(btns[a], 'on', btns[a].getAttribute("m") == r.pb_mode);
			btns[a].onclick = set_pb_mode;
		}
	}
	draw_pb_mode();

	function set_pb_mode(e) {
		ev(e);
		r.pb_mode = this.getAttribute('m');
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
		else if (/\.(wav|flac)$/i.exec(url))
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

	function setaufollow() {
		window[(r.follow ? "add" : "remove") + "EventListener"]("resize", scroll2playing);
	}
	setaufollow();

	function announce() {
		if (!r.os_ctl || !mp.au)
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
				if (/^(cover|folder)\.(jpe?g|png|gif)$/i.test(files[a].textContent)) {
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
	re_au_all = /\.(aac|m4a|ogg|opus|flac|alac|mp3|mp2|ac3|dts|wma|ra|wav|aif|aiff|au|alaw|ulaw|mulaw|amr|gsm|ape|tak|tta|wv|mpc)$/i;


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
			tds[0].innerHTML = '<a id="a' + tid + '" href="#a' + tid + '" class="play">' + L.mb_play + '</a></td>';
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
		r.fdir = 0.025 * r.vol * (CHROME ? 1.5 : 1);
		if (r.au) {
			r.ftid = r.au.tid;
			r.au.play();
			mpl.pp();
			fader();
		}
	};
	r.fade_out = function () {
		r.fvol = r.vol;
		r.fdir = -0.05 * r.vol * (CHROME ? 2 : 1);
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
		r.fvol += r.fdir / (r.fdir < 0 && r.fvol < r.vol / 4 ? 2 : 1);
		if (r.fvol < 0) {
			r.fvol = 0;
			r.au.pause();
			mpl.pp();

			var t = mp.au.currentTime - 0.8;
			if (isNum(t))
				mp.au.currentTime = Math.max(t, 0);
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

		if (mpl.waves)
			fetch(url + '&th=p').then(function (x) {
				x.body.getReader().read();
			});

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
			tk = a == 1 ? 'file' : th[a].getAttribute('name').split('/').pop().toLowerCase(),
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
		clmod(widget, 'open', is_open);
		bcfg_set('au_open', r.is_open = is_open);
		if (vbar) {
			pbar.onresize();
			vbar.onresize();
		}
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

		var cln = function () {
			o.value = 'copied to clipboard ';
			setTimeout(function () {
				document.body.removeChild(o);
			}, 500);
		};
		var fb = function () {
			console.log('fb');
			o.focus();
			o.select();
			document.execCommand("copy");
			cln();
		};
		try {
			// https only
			navigator.clipboard.writeText(m).then(cln, fb);
		}
		catch (ex) { fb(); }
	};
	r.set(sread('au_open') == 1);
	setTimeout(function () {
		clmod(widget, 'anim', 1);
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
		bau = null,
		lastmove = 0,
		mousepos = 0,
		gradh = -1,
		grad;

	r.onresize = function () {
		if (!widget.is_open && r.buf)
			return;

		r.buf = canvas_cfg(ebi('barbuf'));
		r.pos = canvas_cfg(ebi('barpos'));
		r.buf.ctx.font = '.5em sans-serif';
		r.pos.ctx.font = '1em sans-serif';
		r.pos.ctx.strokeStyle = 'rgba(24,56,0,0.4)';
		r.drawbuf();
		r.drawpos();
		if (!r.pos.can.onmouseleave)
			mleave();
	};

	r.loadwaves = function (url) {
		r.wurl = url;
		var img = new Image();
		img.onload = function () {
			r.wimg = img;
			r.onresize();
		};
		img.src = url;
	};

	r.unwave = function () {
		r.wurl = r.wimg = null;
	}

	function mmove(e) {
		var adur;
		if (e.buttons || !mp || !mp.au || !isNum(adur = mp.au.duration))
			return;

		var rect = r.pos.can.getBoundingClientRect(),
			x = e.clientX - rect.left,
			mul = x * 1.0 / rect.width;

		mousepos = adur * mul;
		lastmove = Date.now();
		r.drawpos();
	}
	function menter() {
		r.pos.can.onmousemove = mmove;
		r.pos.can.onmouseleave = mleave;
	}
	function mleave() {
		r.pos.can.onmousemove = null;
		r.pos.can.onmouseleave = null;
		r.pos.can.onmouseenter = menter;
		if (lastmove) {
			lastmove = 0;
			r.drawpos();
		}
	}

	r.drawbuf = function () {
		var bc = r.buf,
			pc = r.pos,
			bctx = bc.ctx,
			apos, adur;

		bctx.clearRect(0, 0, bc.w, bc.h);

		if (!mp || !mp.au || !isNum(adur = mp.au.duration) || !isNum(apos = mp.au.currentTime) || apos < 0 || adur < apos)
			return;  // not-init || unsupp-codec

		bau = mp.au;

		var sm = bc.w * 1.0 / mp.au.duration,
			gk = bc.h + '/' + themen,
			dz = themen == 'dz',
			dy = themen == 'dy';

		if (gradh != gk) {
			gradh = gk;
			grad = glossy_grad(bc, dz ? 120 : 85,
				dy ? [0, 0, 0, 0] : [35, 40, 37, 35],
				dy ? [20, 24, 22, 20] : light ? [45, 56, 50, 45] : [42, 51, 47, 42]);
		}
		bctx.fillStyle = grad;
		for (var a = 0; a < mp.au.buffered.length; a++) {
			var x1 = sm * mp.au.buffered.start(a),
				x2 = sm * mp.au.buffered.end(a);

			bctx.fillRect(x1, 0, x2 - x1, bc.h);
		}
		if (r.wimg) {
			bctx.globalAlpha = 0.6;
			bctx.filter = light ? '' : 'invert(1)';
			bctx.drawImage(r.wimg, 0, 0, bc.w, bc.h);
			bctx.filter = 'invert(0)';
			bctx.globalAlpha = 1;
		}

		var step = sm > 1 ? 1 : sm > 0.4 ? 3 : sm > 0.05 ? 30 : 720;
		bctx.fillStyle = light && !dy ? 'rgba(0,64,0,0.15)' : 'rgba(204,255,128,0.15)';
		for (var p = step, mins = adur / 10; p <= mins; p += step)
			bctx.fillRect(Math.floor(sm * p * 10), 0, 2, pc.h);

		step = sm > 0.15 ? 1 : sm > 0.05 ? 10 : 360;
		bctx.fillStyle = light && !dy ? 'rgba(0,64,0,0.5)' : 'rgba(192,255,96,0.5)';
		for (var p = step, mins = adur / 60; p <= mins; p += step)
			bctx.fillRect(Math.floor(sm * p * 60), 0, 2, pc.h);

		step = sm > 0.33 ? 1 : sm > 0.15 ? 5 : sm > 0.05 ? 10 : sm > 0.01 ? 60 : 720;
		bctx.fillStyle = dz ? '#0f0' : dy ? '#999' : light ? 'rgba(0,64,0,0.9)' : 'rgba(192,255,96,1)';
		for (var p = step, mins = adur / 60; p <= mins; p += step) {
			bctx.fillText(p, Math.floor(sm * p * 60 + 3), pc.h / 3);
		}

		step = sm > 0.2 ? 10 : sm > 0.1 ? 30 : sm > 0.01 ? 60 : sm > 0.005 ? 720 : 1440;
		bctx.fillStyle = light ? 'rgba(0,0,0,1)' : 'rgba(255,255,255,1)';
		for (var p = step, mins = adur / 60; p <= mins; p += step)
			bctx.fillRect(Math.floor(sm * p * 60), 0, 2, pc.h);
	};

	r.drawpos = function () {
		var bc = r.buf,
			pc = r.pos,
			pctx = pc.ctx,
			w = 8,
			apos, adur;

		pctx.clearRect(0, 0, pc.w, pc.h);

		if (!mp || !mp.au || !isNum(adur = mp.au.duration) || !isNum(apos = mp.au.currentTime) || apos < 0 || adur < apos)
			return;  // not-init || unsupp-codec

		if (bau != mp.au)
			r.drawbuf();

		if (Date.now() - lastmove < 400) {
			apos = mousepos;
			w = 0;
		}

		var sm = bc.w * 1.0 / adur,
			x = sm * apos;

		pctx.fillStyle = '#573'; pctx.fillRect((x - w / 2) - 1, 0, w + 2, pc.h);
		pctx.fillStyle = '#dfc'; pctx.fillRect((x - w / 2), 0, w, pc.h);

		pctx.lineWidth = 2.5;
		pctx.fillStyle = '#fff';

		var t1 = s2ms(adur),
			t2 = s2ms(apos),
			m1 = pctx.measureText(t1),
			m1b = pctx.measureText(t1 + ":88"),
			m2 = pctx.measureText(t2),
			yt = pc.h / 3 * 2.1,
			xt1 = pc.w - (m1.width + 12),
			xt2 = x < m1.width * 1.4 ? (x + 12) : (Math.min(pc.w - m1b.width, x - 12) - m2.width);

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
		lastv = -1,
		untext = -1,
		can, ctx, w, h, grad1, grad2;

	r.onresize = function () {
		if (!widget.is_open && r.can)
			return;

		r.can = canvas_cfg(ebi('pvol'));
		can = r.can.can;
		ctx = r.can.ctx;
		ctx.font = '.7em sans-serif';
		w = r.can.w;
		h = r.can.h;
		r.draw();
	}

	r.draw = function () {
		if (!mp)
			return;

		var gh = h + '' + light,
			dz = themen == 'dz',
			dy = themen == 'dy';

		if (gradh != gh) {
			gradh = gh;
			grad1 = glossy_grad(r.can, dz ? 120 : 50,
				dy ? [0, 0, 0, 0] : light ? [50, 55, 52, 48] : [45, 52, 47, 43],
				dy ? [20, 24, 22, 20] : light ? [54, 60, 52, 47] : [42, 51, 47, 42]);
			grad2 = glossy_grad(r.can, dz ? 120 : 205,
				dz ? [100, 100, 100, 100] : dy ? [0, 0, 0, 0] : [10, 15, 13, 10],
				dz ? [10, 14, 12, 10] : dy ? [90, 90, 90, 90] : [16, 20, 18, 16]);
		}
		ctx.fillStyle = grad2; ctx.fillRect(0, 0, w, h);
		ctx.fillStyle = grad1; ctx.fillRect(0, 0, w * mp.vol, h);

		if (Date.now() - lastv > 1000)
			return;

		var vt = Math.floor(mp.vol * 100),
			tw = ctx.measureText(vt).width;

		var li = dy;
		if (mp.vol < 0.05)
			li = !li;

		ctx.fillStyle = li ? '#fff' : '#210';
		ctx.fillText(vt, Math.max(4, w * mp.vol - tw - 8), h / 3 * 2);

		clearTimeout(untext);
		untext = setTimeout(r.draw, 1000);
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

		lastv = Date.now();
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
	if (TOUCH) {
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
	if (!isNum(seek))
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
function dl_song() {
	if (!mp || !mp.au) {
		var o = QSA('#files a[id]');
		for (var a = 0; a < o.length; a++)
			o[a].setAttribute('download', '');

		return toast.inf(10, L.f_dls);
	}

	var url = mp.tracks[mp.au.tid];
	url += (url.indexOf('?') < 0 ? '?' : '&') + 'cache=987';
	dl_file(url);
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

	if (!TOUCH)
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
		//console.trace();
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
			if (MOBILE) {
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


var actx = null;

function start_actx() {
	// bonus: speedhack for unfocused file hashing (removes 1sec delay on subtle.digest resolves)
	if (!actx) {
		if (!ACtx)
			return;

		actx = new ACtx();
		console.log('actx created');
	}
	try {
		if (actx.state == 'suspended') {
			actx.resume();
			setTimeout(function () {
				console.log('actx is ' + actx.state);
			}, 500);
		}
	}
	catch (ex) {
		console.log('actx start failed; ' + ex);
	}
}

var audio_eq = (function () {
	var r = {
		"en": false,
		"bands": [31.25, 62.5, 125, 250, 500, 1000, 2000, 4000, 8000, 16000],
		"gains": [4, 3, 2, 1, 0, 0, 1, 2, 3, 4],
		"filters": [],
		"amp": 0,
		"chw": 1,
		"last_au": null,
		"acst": {}
	};

	if (!ACtx)
		ebi('audio_eq').parentNode.style.display = 'none';

	r.init = function () {
		start_actx();
		if (r.cfg)
			return;

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

		r.cfg = [ // hz, q, g
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
	};

	try {
		r.amp = fcfg_get('au_eq_amp', r.amp);
		r.chw = fcfg_get('au_eq_chw', r.chw);
		var gains = jread('au_eq_gain', r.gains);
		if (r.gains.length == gains.length)
			r.gains = gains;
	}
	catch (ex) { }

	r.draw = function () {
		jwrite('au_eq_gain', r.gains);
		swrite('au_eq_amp', r.amp);
		swrite('au_eq_chw', r.chw);

		var txt = QSA('input.eq_gain');
		for (var a = 0; a < r.bands.length; a++)
			txt[a].value = r.gains[a];

		QS('input.eq_gain[band="amp"]').value = r.amp;
		QS('input.eq_gain[band="chw"]').value = r.chw;
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
		r.init();
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

		for (var a = 0; a < r.cfg.length && min != max; a++) {
			var fi = actx.createBiquadFilter(), c = r.cfg[a];
			fi.frequency.value = c[0];
			fi.gain.value = c[2] * gains[a];
			fi.Q.value = c[1];
			fi.type = a == 0 ? 'lowshelf' : a == r.cfg.length - 1 ? 'highshelf' : 'peaking';
			r.filters.push(fi);
		}

		// pregain, keep first in chain
		fi = actx.createGain();
		fi.gain.value = r.amp + 0.94;  // +.137 dB measured; now -.25 dB and almost bitperfect
		r.filters.push(fi);

		for (var a = r.filters.length - 1; a >= 0; a--)
			r.filters[a].connect(a > 0 ? r.filters[a - 1] : actx.destination);

		if (Math.round(r.chw * 25) != 25) {
			var split = actx.createChannelSplitter(2),
				merge = actx.createChannelMerger(2),
				lg1 = actx.createGain(),
				lg2 = actx.createGain(),
				rg1 = actx.createGain(),
				rg2 = actx.createGain(),
				vg1 = 1 - (1 - r.chw) / 2,
				vg2 = 1 - vg1;

			console.log('chw', vg1, vg2);

			merge.connect(r.filters[r.filters.length - 1]);
			lg1.gain.value = rg2.gain.value = vg1;
			lg2.gain.value = rg1.gain.value = vg2;
			lg1.connect(merge, 0, 0);
			rg1.connect(merge, 0, 0);
			lg2.connect(merge, 0, 1);
			rg2.connect(merge, 0, 1);

			split.connect(lg1, 0);
			split.connect(lg2, 0);
			split.connect(rg1, 1);
			split.connect(rg2, 1);
			r.filters.push(split);
			mp.acs.channelCountMode = 'explicit';
		}

		mp.acs.connect(r.filters[r.filters.length - 1]);
	}

	function eq_step(e) {
		ev(e);
		var sb = this.getAttribute('band'),
			band = parseInt(sb),
			step = parseFloat(this.getAttribute('step'));

		if (sb == 'amp')
			r.amp = Math.round((r.amp + step * 0.2) * 100) / 100;
		else if (sb == 'chw')
			r.chw = Math.round((r.chw + step * 0.2) * 100) / 100;
		else
			r.gains[band] += step;

		r.apply();
	}

	function adj_band(that, step) {
		var err = false;
		try {
			var sb = that.getAttribute('band'),
				band = parseInt(sb),
				vs = that.value,
				v = parseFloat(vs);

			if (!isNum(v) || v + '' != vs)
				throw new Error('inval band');

			if (sb == 'amp')
				r.amp = Math.round((v + step * 0.2) * 100) / 100;
			else if (sb == 'chw')
				r.chw = Math.round((v + step * 0.2) * 100) / 100;
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
		'<a id="au_eq" class="tgl btn" href="#" tt="' + L.mt_eq + '">enable</a></td>'],
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
	vs.push(["chw", "width", r.chw]);

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
function play(tid, is_ev, seek) {
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
		if (mpl.pb_mode == 'loop' || ebi('unsearch')) {
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
		mp.au.onplaying = mpui.progress_updater;
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
		mp.au.onplaying = mpui.progress_updater;
		mp.au.onended = next_song;
		t = mp.au.currentTime;
		if (isNum(t) && t > 0.1)
			mp.au.currentTime = 0;
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
	if (thegrid)
		thegrid.loadsel();

	if (mpl.follow)
		scroll2playing();

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

		pbar.unwave();
		if (mpl.waves)
			pbar.loadwaves(url + '&th=p');

		mpui.progress_updater();
		pbar.onresize();
		vbar.onresize();
		mpl.announce();
		return true;
	}
	catch (ex) {
		toast.err(0, esc(L.mm_playerr + basenames(ex)));
	}
	clmod(ebi(oid), 'act');
	setTimeout(next_song, 5000);
}


function scroll2playing() {
	try {
		QS((!thegrid || !thegrid.en) ?
			'tr.play' : '#ggrid a.play').scrollIntoView();
	}
	catch (ex) { }
}


// event from the audio object if something breaks
function evau_error(e) {
	var err = '',
		eplaya = (e && e.target) || (window.event && window.event.srcElement);

	switch (eplaya.error.code) {
		case eplaya.error.MEDIA_ERR_ABORTED:
			err = L.mm_eabrt;
			break;
		case eplaya.error.MEDIA_ERR_NETWORK:
			err = L.mm_enet;
			break;
		case eplaya.error.MEDIA_ERR_DECODE:
			err = L.mm_edec;
			break;
		case eplaya.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
			err = L.mm_esupp;
			if (/\.(aac|m4a)(\?|$)/i.exec(eplaya.rsrc) && !mpl.ac_aac) {
				try {
					ebi('ac_aac').click();
					QS('a.play.act').click();
					toast.warn(10, L.mm_opusen);
					return;
				}
				catch (ex) { }
			}
			break;
		default:
			err = L.mm_eunk;
			break;
	}
	var em = '' + eplaya.error.message,
		mfile = '\n\nFile: «' + uricom_dec(eplaya.src.split('/').pop()) + '»',
		e404 = L.mm_e404,
		e403 = L.mm_e403;

	if (em)
		err += '\n\n' + em;

	if (em.startsWith('403: '))
		err = e403;

	if (em.startsWith('404: '))
		err = e404;

	toast.warn(15, esc(basenames(err + mfile)));

	if (em.startsWith('MEDIA_ELEMENT_ERROR:')) {
		// chromish for 40x
		var xhr = new XHR();
		xhr.open('HEAD', eplaya.src, true);
		xhr.onload = xhr.onerror = function () {
			if (this.status < 400)
				return;

			err = this.status == 403 ? e403 : this.status == 404 ? e404 :
				L.mm_e5xx + this.status;

			toast.warn(15, esc(basenames(err + mfile)));
		};
		xhr.send();
	}
}


// show ui to manually start playback of a linked song
function autoplay_blocked(seek) {
	var tid = mp.au.tid,
		fn = mp.tracks[tid].split(/\//).pop();

	fn = uricom_dec(fn.replace(/\+/g, ' '));

	modal.confirm('<h6>' + L.mm_hashplay + '</h6>\n«' + esc(fn) + '»', function () {
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


function scan_hash(v) {
	if (!v)
		return null;

	var m = /^#([ag])(f-[0-9a-f]{8,16})(&.+)?/.exec(v + '');
	if (!m)
		return null;

	var mtype = m[1],
		id = m[2],
		ts = null;

	if (m.length > 3) {
		var tm = /^&[Tt=0]*([0-9]+[Mm:])?0*([0-9\.]+)[Ss]?$/.exec(m[3]);
		if (tm) {
			ts = parseInt(tm[1] || 0) * 60 + parseFloat(tm[2] || 0);
		}
		tm = /^&[Tt=0]*([0-9\.]+)-([0-9\.]+)$/.exec(m[3]);
		if (tm) {
			ts = '' + tm[1] + '-' + tm[2];
		}
	}

	return [mtype, id, ts];
}


function eval_hash() {
	var v = hash0;
	hash0 = null;
	if (!v)
		return;

	var media = scan_hash(v);
	if (media) {
		var mtype = media[0],
			id = media[1],
			ts = media[2];

		if (mtype == 'a') {
			if (!ts)
				return play(id);

			return play(id, false, ts);
		}

		if (mtype == 'g') {
			if (!thegrid.en)
				ebi('griden').click();

			var t = setInterval(function () {
				if (!thegrid.bbox)
					return;

				clearInterval(t);
				baguetteBox.urltime(ts);
				var im = QS('#ggrid a[ref="' + id + '"]');
				im.click();
				im.scrollIntoView();
			}, 50);
		}
	}

	if (v.indexOf('#q=') === 0) {
		goto('search');
		var i = ebi('q_raw');
		i.value = uricom_dec(v.slice(3));
		return i.oninput();
	}

	if (v.indexOf('#v=') === 0) {
		goto(v.slice(3));
		return;
	}
}


(function () {
	var props = {};

	// a11y jump-to-content
	for (var a = 0; a < 2; a++)
		(function (a) {
			var d = mknod('a');
			d.setAttribute('href', '#');
			d.setAttribute('class', 'ayjump');
			d.innerHTML = a ? L.ay_path : L.ay_files;
			document.body.insertBefore(d, ebi('ops'));
			d.onclick = function (e) {
				ev(e);
				if (a)
					QS(treectl.hidden ? '#path a:nth-last-child(2)' : '#treeul a.hl').focus();
				else
					QS(thegrid.en ? '#ggrid a' : '#files tbody tr[tabindex]').focus();
			};
		})(a);

	// account-info label
	var d = mknod('div', 'acc_info');
	document.body.insertBefore(d, ebi('ops'));

	// folder nav
	ebi('goh').parentElement.appendChild(mknod('span', null,
		'<a href="#" id="gop" tt="' + L.gop + '</a>/<a href="#" id="gou" tt="' + L.gou + '</a>/<a href="#" id="gon" tt="' + L.gon + '</a>'));
	ebi('gop').onclick = function () { tree_neigh(-1); }
	ebi('gon').onclick = function () { tree_neigh(1); }
	ebi('gou').onclick = function () { tree_up(true); }

	// show/hide scrollbars
	function setsb() {
		clmod(document.documentElement, 'noscroll', !props.sbars);
	}
	bcfg_bind(props, 'sbars', 'sbars', true, setsb);
	setsb();

	// compact media player
	function setacmp() {
		clmod(ebi('widget'), 'cmp', props.mcmp);
	}
	bcfg_bind(props, 'mcmp', 'au_compact', false, setacmp);
	setacmp();
})();


function sortfiles(nodes) {
	if (!nodes.length)
		return nodes;

	var sopts = jread('fsort', [["href", 1, ""]]),
		dir1st = sread('dir1st') !== '0';

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
					else if (name == "href" && v)
						v = uricom_dec(v);

					nodes[b]._sv = v
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
		if (dir1st) {
			var r1 = [], r2 = [];
			for (var b = 0, bb = nodes.length; b < bb; b++)
				(nodes[b].href.split('?')[0].slice(-1) == '/' ? r1 : r2).push(nodes[b]);

			nodes = r1.concat(r2);
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

		bpst.setAttribute('tt', L.ft_paste.format(r.clip.length));
	};

	r.rename = function (e) {
		ev(e);
		if (clgot(bren, 'hide'))
			return toast.err(3, L.fr_eperm);

		var sel = msel.getsel();
		if (!sel.length)
			return toast.err(3, L.fr_emore);

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

				md[k] = (md[k] + '').replace(/[\/\\]/g, '-');

				if (k.startsWith('.'))
					md[k.slice(1)] = md[k];
			}
			md.t = md.ext;
			md.date = md.ts;
			md.size = md.sz;

			f.push({
				"src": vp,
				"ofn": uricom_dec(vsp[1]),
				"md": vars[0],
				"ok": true
			});
		}

		var rui = ebi('rui');
		if (!rui) {
			rui = mknod('div', 'rui');
			document.body.appendChild(rui);
		}

		var html = sel.length > 1 ? ['<div>'] : [
			'<div>',
			'<button class="rn_dec" n="0" tt="' + L.frt_dec + '</button>',
			'//',
			'<button class="rn_reset" n="0" tt="' + L.frt_rst + '</button>'
		];

		html = html.concat([
			'<button id="rn_cancel" tt="' + L.frt_abrt + '</button>',
			'<button id="rn_apply">✅ ' + L.frb_apply + '</button>',
			'<a id="rn_adv" class="tgl btn" href="#" tt="' + L.fr_adv + '</a>',
			'<a id="rn_case" class="tgl btn" href="#" tt="' + L.fr_case + '</a>',
			'</div>',
			'<div id="rn_vadv"><table>',
			'<tr><td>regex</td><td><input type="text" id="rn_re" tt="regex search pattern to apply to original filenames; capturing groups can be referenced in the format field below like &lt;code&gt;(1)&lt;/code&gt; and &lt;code&gt;(2)&lt;/code&gt; and so on" placeholder="^[0-9]+[\\. ]+(.*) - (.*)" /></td></tr>',
			'<tr><td>format</td><td><input type="text" id="rn_fmt" tt="inspired by foobar2000:$N&lt;code&gt;(title)&lt;/code&gt; is replaced by song title,$N&lt;code&gt;[(artist) - ](title)&lt;/code&gt; skips the first part if artist is blank$N&lt;code&gt;$lpad((tn),2,0)&lt;/code&gt; pads tracknumber to 2 digits" placeholder="[(artist) - ](title).(ext)" /></td></tr>',
			'<tr><td>preset</td><td><select id="rn_pre"></select>',
			'<button id="rn_pdel">❌ ' + L.fr_pdel + '</button>',
			'<button id="rn_pnew">💾 ' + L.fr_pnew + '</button>',
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
				'<tr><td></td><td>' + L.fr_lnew + '</td><td>' + L.fr_lold + '</td></tr>');
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
			html.push('<div><p style="margin:.6em 0">' + L.fr_tags + '</p><table>');
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
						f[a].inew.value = uricom_dec(f[a].inew.value);
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
			modal.prompt(L.fr_pname, ifmt.value, function (name) {
				if (!name)
					return toast.warn(3, L.fr_aborted);

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

			toast.show('inf r', 0, esc(L.fr_busy.format(f.length, f[0].ofn)));
			var dst = base + uricom_enc(f[0].inew.value, false);

			function rename_cb() {
				if (this.status !== 201) {
					var msg = this.responseText;
					toast.err(9, L.fr_efail + msg);
					return;
				}

				f.shift().inew.value = '( OK )';
				return rn_apply();
			}

			var xhr = new XHR();
			xhr.open('POST', f[0].src + '?move=' + dst, true);
			xhr.onload = xhr.onerror = rename_cb;
			xhr.send();
		}
	};

	r.delete = function (e) {
		ev(e);
		if (clgot(bdel, 'hide'))
			return toast.err(3, L.fd_eperm);

		var sel = msel.getsel(),
			vps = [];

		for (var a = 0; a < sel.length; a++)
			vps.push(sel[a].vp);

		if (!sel.length)
			return toast.err(3, L.fd_emore);

		function deleter() {
			var xhr = new XHR(),
				vp = vps.shift();

			if (!vp) {
				toast.ok(2, L.fd_ok);
				treectl.goto(get_evpath());
				return;
			}
			toast.show('inf r', 0, esc(L.fd_busy.format(vps.length + 1, vp)), 'r');

			xhr.open('POST', vp + '?delete', true);
			xhr.onload = xhr.onerror = delete_cb;
			xhr.send();
		}
		function delete_cb() {
			if (this.status !== 200) {
				var msg = this.responseText;
				toast.err(9, L.fd_err + msg);
				return;
			}
			deleter();
		}

		modal.confirm('<h6 style="color:#900">DANGER</h6>\n<b>' + L.fd_warn1.format(vps.length) + '</b><ul>' + uricom_adec(vps, true).join('') + '</ul>', function () {
			modal.confirm(L.fd_warn2, deleter, null);
		}, null);
	};

	r.cut = function (e) {
		ev(e);
		if (clgot(bcut, 'hide'))
			return toast.err(3, L.fc_eperm);

		var sel = msel.getsel(),
			vps = [];

		if (!sel.length)
			toast.err(3, L.fc_emore);

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
				toast.inf(1.5, L.fc_ok.format(sel.length));
		}
		catch (ex) {
			toast.warn(30, L.fc_warn.format(sel.length));
		}
	};

	r.paste = function (e) {
		ev(e);
		if (clgot(bpst, 'hide'))
			return toast.err(3, L.fp_eperm);

		if (!r.clip.length)
			return toast.err(5, L.fp_ecut);

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
			toast.warn(30, L.fp_ename.format(exists.length) + '<ul>' + uricom_adec(exists, true).join('') + '</ul>');

		if (!req.length)
			return;

		function paster() {
			var xhr = new XHR(),
				vp = req.shift();

			if (!vp) {
				toast.ok(2, L.fp_ok);
				treectl.goto(get_evpath());
				r.tx(srcdir);
				return;
			}
			toast.show('inf r', 0, esc(L.fp_busy.format(req.length + 1, uricom_dec(vp))));

			var dst = get_evpath() + vp.split('/').pop();

			xhr.open('POST', vp + '?move=' + dst, true);
			xhr.onload = xhr.onerror = paste_cb;
			xhr.send();
		}
		function paste_cb() {
			if (this.status !== 201) {
				var msg = this.responseText;
				toast.err(9, L.fp_err + msg);
				return;
			}
			paster();
		}

		modal.confirm(L.fp_confirm.format(req.length) + '<ul>' + uricom_adec(req, true).join('') + '</ul>', function () {
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
						return modal.alert(L.fp_etab);

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
		'.diz': 'ans',
		'.ex': 'elixir',
		'.exs': 'elixir',
		'.frag': 'glsl',
		'.h': 'c',
		'.hpp': 'cpp',
		'.htm': 'html',
		'.hxx': 'cpp',
		'.log': 'ans',
		'.m': 'matlab',
		'.moon': 'moonscript',
		'.patch': 'diff',
		'.ps1': 'powershell',
		'.psm1': 'powershell',
		'.pl': 'perl',
		'.rs': 'rust',
		'.sh': 'bash',
		'.service': 'systemd',
		'.vb': 'vbnet',
		'.v': 'verilog',
		'.vert': 'glsl',
		'.vh': 'verilog',
		'.yml': 'yaml'
	};
	r.nmap = {
		'cmakelists.txt': 'cmake',
		'dockerfile': 'docker'
	};
	var x = txt_ext + ' ans c cfg conf cpp cs css diff glsl go html ini java js json jsx kt kts latex less lisp lua makefile md nim py r rss rb ruby sass scss sql svg swift tex toml ts vhdl xml yaml zig';
	x = x.split(/ +/g);
	for (var a = 0; a < x.length; a++)
		r.map["." + x[a]] = x[a];

	r.sname = function (srch) {
		return srch.split(/[?&]doc=/)[1].split('&')[0];
	};

	window.Prism = { 'manual': true };
	var em = QS('#bdoc>pre');
	if (em)
		em = [r.sname(window.location.search), location.hash, em.textContent];
	else {
		var m = /[?&]doc=([^&]+)/.exec(window.location.search);
		if (m) {
			setTimeout(function () {
				r.show(uricom_dec(m[1]), true);
			}, 1);
		}
	}

	r.setstyle = function () {
		if (window.no_prism)
			return;

		qsr('#prism_css');
		var el = mknod('link', 'prism_css');
		el.rel = 'stylesheet';
		el.href = SR + '/.cpr/deps/prism' + (light ? '' : 'd') + '.css';
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
			td.getElementsByTagName('a')[0].setAttribute('href', '?doc=' + fn);
		}
		r.mktree();
		if (em) {
			render(em);
			em = null;
		}
	};

	r.show = function (url, no_push) {
		var xhr = new XHR();
		xhr.url = url;
		xhr.fname = uricom_dec(url.split('/').pop());
		xhr.no_push = no_push;
		xhr.ts = Date.now();
		xhr.open('GET', url.split('?')[0], true);
		xhr.onprogress = loading;
		xhr.onload = xhr.onerror = load_cb;
		xhr.send();
	};

	function loading(e) {
		if (e.total < 1024 * 256)
			return;

		var m = L.tv_load.format(
			esc(this.fname),
			f2f(e.loaded * 100 / e.total, 1),
			f2f(e.loaded / 1024 / 1024, 1),
			f2f(e.total / 1024 / 1024, 1))

		if (!this.toasted) {
			this.toasted = 1;
			return toast.inf(573, m);
		}
		ebi('toastb').innerHTML = lf2br(m);
	}

	function load_cb(e) {
		if (this.toasted)
			toast.hide();

		if (!xhrchk(this, L.tv_xe1, L.tv_xe2))
			return;

		render([this.url, '', this.responseText], this.no_push);
	}

	function render(doc, no_push) {
		r.q = null;
		var url = doc[0],
			lnh = doc[1],
			txt = doc[2],
			name = url.split('/').pop(),
			tname = uricom_dec(name),
			lang = r.getlang(name),
			is_md = lang == 'md';

		ebi('files').style.display = ebi('gfiles').style.display = ebi('lazy').style.display = ebi('pro').style.display = ebi('epi').style.display = 'none';
		ebi('dldoc').setAttribute('href', url);

		var wr = ebi('bdoc'),
			defer = !Prism.highlightElement;

		var fun = function (el) {
			try {
				if (lnh.slice(0, 5) == '#doc.')
					sethash(lnh.slice(1));

				el = el || QS('#doc>code');
				Prism.highlightElement(el);
				if (el.className == 'language-ans')
					r.ansify(el);
			}
			catch (ex) { }
		}

		if (txt.length > 1024 * 256)
			fun = function (el) { };

		qsr('#doc');
		var el = mknod('pre', 'doc');
		el.setAttribute('tabindex', '0');
		clmod(ebi('wrap'), 'doc', !is_md);
		if (is_md) {
			show_md(txt, name, el);
		}
		else {
			el.textContent = txt;
			el.innerHTML = '<code>' + el.innerHTML + '</code>';
			if (!window.no_prism) {
				el.className = 'prism linkable-line-numbers line-numbers language-' + lang;
				if (!defer)
					fun(el.firstChild);
				else
					import_js(SR + '/.cpr/deps/prism.js', function () { fun(); });
			}
		}

		wr.appendChild(el);
		wr.style.display = '';
		set_tabindex();

		wintitle(tname + ' \u2014 ');
		document.documentElement.scrollTop = 0;
		var hfun = no_push ? hist_replace : hist_push;
		hfun(get_evpath() + '?doc=' + url.split('/').pop());

		qsr('#docname');
		el = mknod('span', 'docname');
		el.textContent = tname;
		ebi('path').appendChild(el);

		r.updtree();
		treectl.textmode(true);
		tree_scrollto();
	}

	r.ansify = function (el) {
		var ctab = (light ?
			'bfbfbf d30253 497600 b96900 006fbb a50097 288276 2d2d2d 9f9f9f 943b55 3a5600 7f4f00 00507d 683794 004343 000000' :
			'404040 f03669 b8e346 ffa402 02a2ff f65be3 3da698 d2d2d2 606060 c75b79 c8e37e ffbe4a 71cbff b67fe3 9cf0ed ffffff').split(/ /g),
			src = el.innerHTML.split(/\x1b\[/g),
			out = ['<span>'], fg = 7, bg = null, bfg = 0, bbg = 0, inv = 0, bold = 0;

		for (var a = 0; a < src.length; a++) {
			var m = /^([0-9;]+)m/.exec(src[a]);
			if (!m) {
				if (a)
					out.push('\x1b[');

				out.push(src[a]);
				continue;
			}

			var cs = m[1].split(/;/g),
				txt = src[a].slice(m[1].length + 1);

			for (var b = 0; b < cs.length; b++) {
				var c = parseInt(cs[b]);
				if (c == 0) {
					fg = 7;
					bg = null;
					bfg = bbg = bold = inv = 0;
				}
				if (c == 1) bfg = bold = 1;
				if (c == 7) inv = 1;
				if (c == 22) bfg = bold = 0;
				if (c == 27) inv = 0;
				if (c >= 30 && c <= 37) fg = c - 30;
				if (c >= 40 && c <= 47) bg = c - 40;
				if (c >= 90 && c <= 97) {
					fg = c - 90;
					bfg = 1;
				}
				if (c >= 100 && c <= 107) {
					bg = c - 100;
					bbg = 1;
				}
			}

			var cfg = fg, cbg = bg;
			if (inv) {
				cbg = fg;
				cfg = bg || 0;
			}

			var s = '</span><span style="color:#' + ctab[cfg + bfg * 8];
			if (cbg !== null)
				s += ';background:#' + ctab[cbg + bbg * 8];
			if (bold)
				s += ';font-weight:bold';

			out.push(s + '">' + txt);
		}
		el.innerHTML = out.join('');
	};

	r.mktree = function () {
		var html = ['<li class="bn">' + L.tv_lst + '<br />' + linksplit(get_vpath()).join('') + '</li>'];
		for (var a = 0; a < r.files.length; a++) {
			var file = r.files[a];
			html.push('<li><a href="?doc=' + file.name + '" hl="' + file.id +
				'">' + esc(uricom_dec(file.name)) + '</a>');
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
	bdoc.className = 'line-numbers';
	bdoc.innerHTML = (
		'<div id="hdoc" class="ghead">\n' +
		'<a href="#" class="btn" id="xdoc" tt="' + L.tvt_close + '</a>\n' +
		'<a href="#" class="btn" id="dldoc" tt="' + L.tvt_dl + '</a>\n' +
		'<a href="#" class="btn" id="prevdoc" tt="' + L.tvt_prev + '</a>\n' +
		'<a href="#" class="btn" id="nextdoc" tt="' + L.tvt_next + '</a>\n' +
		'<a href="#" class="btn" id="seldoc" tt="' + L.tvt_sel + '</a>\n' +
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
		gfiles = mknod('div', 'gfiles');

	gfiles.style.display = 'none';
	gfiles.innerHTML = (
		'<div id="ghead" class="ghead">' +
		'<a href="#" class="tgl btn" id="gridsel" tt="' + L.gt_msel + '</a> <span>' + L.gt_zoom + ': ' +
		'<a href="#" class="btn" z="-1.2" tt="Hotkey: shift-A">&ndash;</a> ' +
		'<a href="#" class="btn" z="1.2" tt="Hotkey: shift-D">+</a></span> <span>' + L.gt_chop + ': ' +
		'<a href="#" class="btn" l="-1" tt="' + L.gt_c1 + '">&ndash;</a> ' +
		'<a href="#" class="btn" l="1" tt="' + L.gt_c2 + '">+</a></span> <span>' + L.gt_sort + ': ' +
		'<a href="#" s="href">' + L.gt_name + '</a> ' +
		'<a href="#" s="sz">' + L.gt_sz + '</a> ' +
		'<a href="#" s="ts">' + L.gt_ts + '</a> ' +
		'<a href="#" s="ext">' + L.gt_ext + '</a>' +
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

		var t = ebi('files').tHead.rows[0].cells;
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
			wintitle();
		}

		lfiles = ebi('files');
		gfiles = ebi('gfiles');

		var vis = has(perms, "read");
		gfiles.style.display = vis && r.en ? '' : 'none';
		lfiles.style.display = vis && !r.en ? '' : 'none';
		ebi('pro').style.display = ebi('epi').style.display = ebi('lazy').style.display = ebi('treeul').style.display = ebi('treepar').style.display = '';
		ebi('bdoc').style.display = 'none';
		clmod(ebi('wrap'), 'doc');
		qsr('#docname');
		if (treectl)
			treectl.textmode(false);

		if (filecols)
			filecols.uivis();

		aligngriditems();
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
			is_img = /\.(a?png|avif|bmp|gif|heif|jpe?g|jfif|svg|webp|webm|mkv|mp4)(\?|$)/i.test(href),
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

		else if (is_dir && !have_sel)
			treectl.reqls(href, true);

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
				cl = tr.className || '';

			if (noq_href(ths[a]).endsWith('/'))
				cl += ' dir';

			ths[a].className = cl;
		}

		var sp = ['unsearch', 'moar'];
		for (var a = 0; a < sp.length; a++)
			(function (a) {
				var o = QS('#ggrid a[ref="' + sp[a] + '"]');
				if (o)
					o.onclick = function (e) {
						ev(e);
						ebi(sp[a]).click();
					};
			})(a);
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

		var html = [],
			svgs = new Set(),
			max_svgs = CHROME ? 500 : 5000,
			files = QSA('#files>tbody>tr>td:nth-child(2) a[id]');

		for (var a = 0, aa = files.length; a < aa; a++) {
			var ao = files[a],
				ohref = esc(ao.getAttribute('href')),
				href = ohref.split('?')[0],
				name = uricom_dec(vsplit(href)[1]),
				ref = ao.getAttribute('id'),
				isdir = href.endsWith('/'),
				ac = isdir ? ' class="dir"' : '',
				ihref = href;

			if (r.thumbs) {
				ihref += '?th=' + (have_webp ? 'w' : 'j');
				if (href == "#")
					ihref = SR + '/.cpr/ico/⏏️';
			}
			else if (isdir) {
				ihref = SR + '/.cpr/ico/folder';
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
				var ext = ihref.slice(0, -1);
				if (!svgs.has(ext)) {
					if (svgs.size < max_svgs)
						svgs.add(ext);
					else
						ext = "unk";
				}
				ihref = SR + '/.cpr/ico/' + ext;
			}
			ihref += (ihref.indexOf('?') > 0 ? '&' : '?') + 'cache=i';

			html.push('<a href="' + ohref + '" ref="' + ref +
				'"' + ac + ' ttt="' + esc(name) + '"><img style="height:' +
				(r.sz / 1.25) + 'em" onload="th_onload(this)" src="' +
				ihref + '" /><span' + ac + '>' + ao.innerHTML + '</span></a>');
		}
		ebi('ggrid').innerHTML = html.join('\n');

		var srch = ebi('unsearch'),
			gsel = ebi('gridsel');

		gsel.style.display = srch ? 'none' : '';
		if (srch && r.sel)
			gsel.click();

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
					esc(uricom_dec(h.split('/').pop())) + '</a>';
			},
			onChange: function (i) {
				sethash('g' + r.bbox[i].imageElement.getAttribute('ref'));
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
			treectl.detree();
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
	links[act].focus();
}


function tree_up(justgo) {
	if (showfile.active())
		return thegrid.setvis(true);

	var act = QS('#treeul a.hl');
	if (!act) {
		treectl.dir_cb = function () {
			tree_up(justgo);
			treectl.detree();
		};
		treectl.entree(null, true);
		return;
	}
	if (act.previousSibling.textContent == '-') {
		act.previousSibling.click();
		if (!justgo)
			return;
	}
	act.parentNode.parentNode.parentNode.getElementsByTagName('a')[1].click();
}


function hkhelp() {
	var html = [];
	for (var ic = 0; ic < L.hks.length; ic++) {
		var c = L.hks[ic];
		html.push('<table>');
		for (var a = 0; a < c.length; a++)
			try {
				if (c[a].length != 2)
					html.push('<tr><th colspan="2">' + esc(c[a]) + '</th></tr>');
				else
					html.push('<tr><td>{0}</td><td>{1}</td></tr>'.format(c[a][0], c[a][1]));
			}
			catch (ex) {
				html.push(">>> " + c[a]);
			}

		html.push('</table>');
	}
	qsr('#hkhelp');
	var o = mknod('div', 'hkhelp');
	o.innerHTML = html.join('\n');
	document.body.appendChild(o);
}


document.onkeydown = function (e) {
	if (e.altKey || e.isComposing)
		return;

	if (QS('#bbox-overlay.visible') || modal.busy)
		return;

	var k = e.code + '', pos = -1, n,
		ae = document.activeElement,
		aet = ae && ae != document.body ? ae.nodeName.toLowerCase() : '';

	if (e.key == '?')
		return hkhelp();

	if (k == 'Escape') {
		ae && ae.blur();
		tt.hide();

		if (ebi('hkhelp'))
			return qsr('#hkhelp');

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

	if (ae && ae.closest('pre')) {
		if (k == 'KeyA' && ctrl(e)) {
			var sel = document.getSelection(),
				ran = document.createRange();

			sel.removeAllRanges();
			ran.selectNode(ae.closest('pre'));
			sel.addRange(ran);
			return ev(e);
		}
	}

	if (k == 'Enter' && ae && (ae.onclick || ae.hasAttribute('tabIndex')))
		return ev(e) && ae.click() || true;

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

	if (k == 'KeyY')
		return msel.getsel().length ? ebi('seldl').click() : dl_song();

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
		[
			L.s_sz,
			["szl", "sz_min", L.s_s1, "14", ""],
			["szu", "sz_max", L.s_s2, "14", ""]
		],
		[
			L.s_dt,
			["dtl", "dt_min", L.s_d1, "14", "1997-08-15, 01:00"],
			["dtu", "dt_max", L.s_d2, "14", "2020"]
		],
		[
			L.s_rd,
			["path", "path", L.s_r1, "30", "windows  -system32"]
		],
		[
			L.s_fn,
			["name", "name", L.s_f1, "30", ".exe$"]
		],
		[
			L.s_ta,
			["tags", "tags", L.s_t1, "30", "^irui$"]
		],
		[
			L.s_ad,
			["adv", "adv", L.s_a1, "30", "key>=1A  key<=2B  .bpm>165"]
		]
	];

	var trs = [],
		orig_url = null,
		orig_html = null,
		cap = 125;

	for (var a = 0; a < sconf.length; a++) {
		var html = ['<tr id="tsrch_' + sconf[a][1][0] + '"><td><br />' + sconf[a][0] + '</td>'];
		for (var b = 1; b < 3; b++) {
			var hn = "srch_" + sconf[a][b][0],
				csp = (sconf[a].length == 2) ? 2 : 1;

			html.push(
				'<td colspan="' + csp + '"><input id="' + hn + 'c" type="checkbox">\n' +
				'<label for="' + hn + 'c">' + sconf[a][b][2] + '</label>\n' +
				'<br /><input id="' + hn + 'v" type="text" style="width:' + sconf[a][b][3] +
				'em" name="' + sconf[a][b][1] + '" placeholder="' + sconf[a][b][4] + '" /></td>');
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
	html.push('<table id="tq_raw"><tr><td>raw</td><td><input id="q_raw" type="text" name="q" placeholder="( tags like *nhato* or tags like *taishi* ) and ( not tags like *nhato* or not tags like *taishi* )" /></td></tr></table>');
	ebi('srch_form').innerHTML = html.join('\n');

	var o = QSA('#op_search input');
	for (var a = 0; a < o.length; a++) {
		o[a].oninput = ev_search_input;
		o[a].onkeydown = ev_search_keydown;
	}

	function srch_msg(err, txt) {
		var o = ebi('srch_q');
		o.textContent = txt;
		clmod(o, 'err', err);
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
		cap = 125;

		clearTimeout(defer_timeout);
		defer_timeout = setTimeout(try_search, 2000);
		try_search(v);
	}

	function ev_search_keydown(e) {
		if (e.key == 'Enter')
			do_search();
	}

	function try_search(v) {
		if (Date.now() - search_in_progress > 30 * 1000) {
			clearTimeout(defer_timeout);
			clearTimeout(search_timeout);
			search_timeout = setTimeout(do_search,
				v && v.length < (MOBILE ? 4 : 3) ? 1000 : 500);
		}
	}

	function set_vq() {
		if (search_in_progress)
			return;

		var q = ebi('q_raw').value,
			vq = ebi('files').getAttribute('q_raw');

		srch_msg(false, (q == vq) ? '' : L.sm_prev + (vq ? vq : '(*)'));
	}

	function encode_query() {
		var q = '';
		for (var a = 0; a < sconf.length; a++) {
			for (var b = 1; b < sconf[a].length; b++) {
				var k = sconf[a][b][0],
					chk = 'srch_' + k + 'c',
					vs = ebi('srch_' + k + 'v').value,
					tvs = [];

				if (a == 1)
					vs = vs.trim().replace(/ +/, 'T');

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
						var not = '';
						if (tv.slice(0, 1) == '-') {
							tv = tv.slice(1);
							not = 'not ';
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

						q += not + k + ' like ' + tv;
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

		var xhr = new XHR();
		xhr.open('POST', SR + '/?srch', true);
		xhr.setRequestHeader('Content-Type', 'text/plain');
		xhr.onload = xhr.onerror = xhr_search_results;
		xhr.ts = Date.now();
		xhr.q_raw = ebi('q_raw').value;
		xhr.send(JSON.stringify({ "q": xhr.q_raw, "n": cap }));
	}

	function xhr_search_results() {
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
		thegrid.setvis(true);

		var html = mk_files_header(tagord), seen = {};
		html.push('<tbody>');
		html.push('<tr class="srch_hdr"><td>-</td><td><a href="#" id="unsearch"><big style="font-weight:bold">[❌] ' + L.sl_close + '</big></a> -- ' + L.sl_hits.format(res.hits.length) + (res.hits.length == cap ? ' -- <a href="#" id="moar">' + L.sl_moar + '</a>' : '') + '</td></tr>');

		for (var a = 0; a < res.hits.length; a++) {
			var r = res.hits[a],
				ts = parseInt(r.ts),
				sz = esc(r.sz + ''),
				rp = esc(uricom_dec(r.rp + '')),
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
		var m = ebi('moar');
		if (m)
			m.onclick = moar;
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

	function moar(e) {
		ev(e);
		cap *= 2;
		do_search();
	}
})();

function aligngriditems() {
	if (!treectl)
		return;

	var em2px = parseFloat(getComputedStyle(ebi('ggrid')).fontSize);
	var gridsz = 10;
	try {
		gridsz = cprop('--grid-sz').slice(0, -2);
	}
	catch (ex) { }
	var gridwidth = ebi('ggrid').clientWidth;
	var griditemcount = ebi('ggrid').children.length;
	var totalgapwidth = em2px * griditemcount;
	if (/b/.test(themen + ''))
		totalgapwidth *= 2.8;

	if (((griditemcount * em2px) * gridsz) + totalgapwidth < gridwidth) {
		ebi('ggrid').style.justifyContent = 'left';
	} else {
		ebi('ggrid').style.justifyContent = treectl.hidden ? 'center' : 'space-between';
	}
}
window.addEventListener('resize', aligngriditems);

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

	bcfg_bind(r, 'ireadme', 'ireadme', true);
	bcfg_bind(r, 'dyn', 'dyntree', true, onresize);
	bcfg_bind(r, 'dots', 'dotfiles', false, function (v) {
		r.goto(get_evpath());
	});
	bcfg_bind(r, 'dir1st', 'dir1st', true, function (v) {
		treectl.gentab(get_evpath(), treectl.lsc);
	});
	setwrap(bcfg_bind(r, 'wtree', 'wraptree', true, setwrap));
	setwrap(bcfg_bind(r, 'parpane', 'parpane', true, onscroll));
	bcfg_bind(r, 'htree', 'hovertree', false, reload_tree);
	bcfg_bind(r, 'ask', 'bd_ask', MOBILE && FIREFOX);
	ebi('bd_lim').value = r.lim = icfg_get('bd_lim');
	ebi('bd_lim').oninput = function (e) {
		var n = parseInt(this.value);
		swrite('bd_lim', r.lim = (isNum(n) ? n : 0) || 1000);
	};
	r.nvis = r.lim;

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
		aligngriditems();
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
		aligngriditems();
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
				y += tree.offsetTop - yscroll();

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
			tree.style.height = treeh < 10 ? '' : Math.floor(treeh) + 'px';
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

	r.goto = function (url, push, back) {
		get_tree("", url, true);
		r.reqls(url, push, back);
	};

	function get_tree(top, dst, rst) {
		var xhr = new XHR();
		xhr.top = top;
		xhr.dst = dst;
		xhr.rst = rst;
		xhr.ts = Date.now();
		xhr.open('GET', dst + '?tree=' + top + (r.dots ? '&dots' : ''), true);
		xhr.onload = xhr.onerror = recvtree;
		xhr.send();
		enspin('#tree');
	}

	function recvtree() {
		if (!xhrchk(this, L.tl_xe1, L.tl_xe2))
			return;

		try {
			var res = JSON.parse(this.responseText);
		}
		catch (ex) {
			return;
		}
		rendertree(res, this.ts, this.top, this.dst, this.rst);
	}

	function rendertree(res, ts, top0, dst, rst) {
		var cur = ebi('treeul').getAttribute('ts');
		if (cur && parseInt(cur) > ts + 20 && QS('#treeul>li>a+a')) {
			console.log("reject tree; " + cur + " / " + (ts - cur));
			return;
		}
		ebi('treeul').setAttribute('ts', ts);

		var top = top0 == '.' ? dst : top0,
			name = uricom_dec(top.split('/').slice(-2)[0]),
			rtop = top.replace(/^\/+/, ""),
			html = parsetree(res, rtop);

		if (!top0) {
			html = '<li><a href="#">-</a><a href="/">[root]</a>\n<ul>' + html;
			if (rst || !ebi('treeul').getElementsByTagName('li').length)
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
		despin('#tree');

		try {
			QS('#treeul>li>a+a').textContent = '[root]';
		}
		catch (ex) {
			console.log('got no root yet');
			r.dir_cb = null;
			return;
		}

		reload_tree();
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
		var cdir = r.nextdir || get_vpath(),
			links = QSA('#treeul a+a'),
			nowrap = QS('#tree.nowrap') && QS('#hovertree.on'),
			act = null;

		for (var a = 0, aa = links.length; a < aa; a++) {
			var href = uricom_dec(links[a].getAttribute('href')),
				cl = '';

			if (href == cdir) {
				act = links[a];
				cl = 'hl';
			}
			else if (cdir.startsWith(href)) {
				cl = 'par';
			}

			links[a].className = cl;
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
		onresize();
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
		if (this.className == 'hl' &&
			this.previousSibling.textContent == '-') {
			treegrow.call(this.previousSibling, e);
			return;
		}
		var href = this.getAttribute('href');
		if (R && !href.startsWith(SR)) {
			window.location = href;
			return;
		}
		r.reqls(href, true);
		r.dir_cb = tree_scrollto;
		thegrid.setvis(true);
	}

	r.reqls = function (url, hpush, back) {
		var xhr = new XHR();
		xhr.top = url.split('?')[0];
		xhr.back = back
		xhr.hpush = hpush;
		xhr.ts = Date.now();
		xhr.open('GET', xhr.top + '?ls' + (r.dots ? '&dots' : ''), true);
		xhr.onload = xhr.onerror = recvls;
		xhr.send();

		r.nvis = r.lim;
		r.nextdir = xhr.top;
		enspin('#tree');
		enspin(thegrid.en ? '#gfiles' : '#files');
		window.removeEventListener('scroll', r.tscroll);
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
		if (!xhrchk(this, L.fl_xe1, L.fl_xe2))
			return;

		r.nextdir = null;
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

		for (var a = 0; a < res.files.length; a++)
			if (res.files[a].tags === undefined)
				res.files[a].tags = {};

		srvinf = res.srvinf;
		try {
			ebi('srv_info').innerHTML = ebi('srv_info2').innerHTML = '<span>' + res.srvinf + '</span>';
		}
		catch (ex) { }

		if (this.hpush && !showfile.active())
			hist_push(this.top);

		if (!this.back) {
			var dirs = [];
			for (var a = 0; a < res.dirs.length; a++)
				dirs.push(res.dirs[a].href.split('/')[0].split('?')[0]);

			rendertree({ "a": dirs }, this.ts, ".", get_evpath());
		}

		r.gentab(this.top, res);
		despin('#tree');
		despin('#files');
		despin('#gfiles');

		sandbox(ebi('pro'), sb_lg, '', res.logues ? res.logues[0] || "" : "");
		sandbox(ebi('epi'), sb_lg, '', res.logues ? res.logues[1] || "" : "");

		clmod(ebi('epi'), 'mdo');
		if (res.readme)
			show_readme(res.readme);

		if (this.hpush && !this.back) {
			var ofs = ebi('wrap').offsetTop;
			if (document.documentElement.scrollTop > ofs)
				document.documentElement.scrollTop = ofs;
		}

		wintitle();
		var fun = r.ls_cb;
		if (fun) {
			r.ls_cb = null;
			fun();
		}
	}

	r.gentab = function (top, res) {
		var nodes = res.dirs.concat(res.files),
			html = mk_files_header(res.taglist),
			sel = r.lsc === res ? msel.getsel() : [],
			plain = [],
			seen = {};

		r.lsc = res;
		nodes = sortfiles(nodes);
		window.removeEventListener('scroll', r.tscroll);
		r.trunc = nodes.length > r.nvis && location.hash.length < 2;
		if (r.trunc) {
			for (var a = r.lim; a < nodes.length; a++) {
				var tn = nodes[a],
					tns = Object.keys(tn.tags || {});

				plain.push(uricom_dec(tn.href.split('?')[0]));

				for (var b = 0; b < tns.length; b++)
					if (has(res.taglist, tns[b]))
						plain.push(tn.tags[tns[b]]);
			}
			nodes = nodes.slice(0, r.nvis);
		}

		showfile.files = [];
		html.push('<tbody>');
		for (var a = 0; a < nodes.length; a++) {
			var tn = nodes[a],
				bhref = tn.href.split('?')[0],
				fname = uricom_dec(bhref),
				hname = esc(fname),
				id = 'f-' + ('00000000' + crc32(fname)).slice(-8),
				lang = showfile.getlang(fname);

			while (seen[id])  // ejyefs ev69gg y9j8sg .opus
				id += 'a';
			seen[id] = 1;

			if (lang) {
				showfile.files.push({ 'id': id, 'name': fname });
				if (lang == 'md')
					tn.href += tn.href.indexOf('?') < 0 ? '?v' : '&v';
			}

			if (tn.lead == '-')
				tn.lead = '<a href="?doc=' + tn.href + '" class="doc' + (lang ? ' bri' : '') +
					'" hl="' + id + '" name="' + hname + '">-txt-</a>';

			var ln = ['<tr><td>' + tn.lead + '</td><td><a href="' +
				top + tn.href + '" id="' + id + '">' + hname + '</a>', tn.sz];

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
		if (r.trunc) {
			r.setlazy(plain);
			if (!r.ask) {
				window.addEventListener('scroll', r.tscroll);
				setTimeout(r.tscroll, 100);
			}
		}

		function asdf() {
			showfile.mktree();
			mukey.render();
			reload_tree();
			reload_browser();
			tree_scrollto();
			if (res.acct) {
				acct = res.acct;
				have_up2k_idx = res.idx;
				have_tags_idx = res.itag;
				lifetime = res.lifetime;
				apply_perms(res.perms);
				fileman.render();
			}
			if (sel.length)
				msel.loadsel(sel);

			setTimeout(eval_hash, 1);
		}

		var m = scan_hash(hash0),
			url = null;

		if (m) {
			url = ebi(m[1]);
			if (url) {
				url = url.href;
				var mt = m[0] == 'a' ? 'audio' : /\.(webm|mkv)($|\?)/i.exec(url) ? 'video' : 'image'
				if (mt == 'image') {
					url += url.indexOf('?') < 0 ? '?cache' : '&cache';
					console.log(url);
					new Image().src = url;
				}
			}
		}

		if (url) setTimeout(asdf, 1); else asdf();
	}

	r.hydrate = function () {
		qsr('#bbsw');
		if (ls0 === null) {
			var xhr = new XHR();
			xhr.open('GET', SR + '/?am_js', true);
			xhr.send();

			r.ls_cb = showfile.addlinks;
			return r.reqls(get_evpath(), false);
		}

		r.gentab(get_evpath(), ls0);
		pbar.onresize();
		vbar.onresize();
		showfile.addlinks();
		setTimeout(eval_hash, 1);
	};

	r.setlazy = function (plain) {
		var html = ['<div id="plazy">', esc(plain.join(' ')), '</div>'],
			all = r.lsc.files.length + r.lsc.dirs.length,
			nxt = r.nvis * 4;

		if (r.ask)
			html.push((nxt >= all ? L.fbd_all : L.fbd_more).format(r.nvis, all, nxt));

		ebi('lazy').innerHTML = html.join('\n');

		try {
			ebi('bd_all').onclick = function (e) {
				ev(e);
				r.showmore(all);
			};
			ebi('bd_more').onclick = function (e) {
				ev(e);
				r.showmore(nxt);
			};
		}
		catch (ex) { }
	};

	r.showmore = function (n) {
		window.removeEventListener('scroll', r.tscroll);
		console.log('nvis {0} -> {1}'.format(r.nvis, n));
		r.nvis = n;
		ebi('lazy').innerHTML = '';
		ebi('wrap').style.opacity = 0.4;
		document.documentElement.scrollLeft = 0;
		setTimeout(function () {
			r.gentab(get_evpath(), r.lsc);
			ebi('wrap').style.opacity = 'unset';
		}, 1);
	};

	r.tscroll = function () {
		var el = r.trunc ? ebi('plazy') : null;
		if (!el || ebi('lazy').style.display || ebi('unsearch'))
			return;

		var sy = yscroll() + window.innerHeight,
			ty = el.offsetTop;

		if (sy <= ty)
			return;

		window.removeEventListener('scroll', r.tscroll);

		var all = r.lsc.files.length + r.lsc.dirs.length;
		if (r.nvis * 16 <= all) {
			console.log("{0} ({1} * 16) <= {2}".format(r.nvis * 16, r.nvis, all));
			r.showmore(r.nvis * 4);
		}
		else {
			console.log("{0} ({1} * 16) > {2}".format(r.nvis * 16, r.nvis, all));
			r.showmore(all);
		}
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
				k = uricom_sdec(ks),
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
		if (!isNum(treesz))
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

		r.goto(url.pathname, false, true);
	};

	hist_replace(get_evpath() + location.hash);
	r.onscroll = onscroll;
	return r;
})();


function enspin(sel) {
	despin(sel);
	var d = mknod('div');
	d.className = 'dumb_loader_thing';
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
		a.setAttribute('tt', L.ot_u2i);
	}
	else {
		a.setAttribute('data-perm', 'write');
		a.setAttribute('tt', L.ot_u2w);
	}
	clmod(ebi('srch_form'), 'tags', have_tags_idx);

	a.style.display = '';
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

	ebi('acc_info').innerHTML = '<span id="srv_info2"><span>' + srvinf +
		'</span></span><span' + aclass + axs + L.access + '</span>' + (acct != '*' ?
			'<a href="' + SR + '/?pw=x">' + L.logout + acct + '</a>' :
			'<a href="' + SR + '/?h">Login</a>');

	var o = QSA('#ops>a[data-perm]');
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

	if (up2k)
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
			min = (tds[a].className || '').indexOf('min') !== -1;
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
	var r = { 'picking': false };
	var hidden = jread('filecols', []);

	r.add_btns = function () {
		var ths = QSA('#files>thead th>span');
		for (var a = 0, aa = ths.length; a < aa; a++) {
			var th = ths[a].parentElement,
				ttv = L.cols[ths[a].textContent];

			if (!MOBILE) {
				th.innerHTML = '<div class="cfg"><a href="#">-</a></div>' + ths[a].outerHTML;
				th.getElementsByTagName('a')[0].onclick = ev_row_tgl;
			}
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

		r.toggle(t.textContent);
	}

	r.uivis = function () {
		var hcols = ebi('hcols');
		hcols.previousSibling.style.display = hcols.style.display = ((!thegrid || !thegrid.en) && (hidden.length || MOBILE)) ? 'block' : 'none';
	};

	r.set_style = function (unhide) {
		hidden.sort();

		if (!unhide)
			unhide = [];

		var html = [],
			hcols = ebi('hcols');

		for (var a = 0; a < hidden.length; a++) {
			var ttv = L.cols[hidden[a]],
				tta = ttv ? ' tt="' + ttv + '">' : '>';

			html.push('<a href="#" class="btn"' + tta + esc(hidden[a]) + '</a>');
		}
		hcols.innerHTML = html.join('\n');
		hcols.onclick = hcols_click;
		r.uivis();
		r.add_btns();

		var ohidden = [],
			ths = QSA('#files>thead th'),
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
				tds[b].className = cls;
		}
		if (tt) {
			tt.att(ebi('hcols'));
			tt.att(QS('#files>thead'));
		}
	};

	r.setvis = function (name, vis) {
		var ofs = hidden.indexOf(name);
		if (ofs !== -1 && vis != 0)
			hidden.splice(ofs, 1);
		else if (vis != 1) {
			if (!sread("chide_ok")) {
				return modal.confirm(L.f_chide.format(name), function () {
					swrite("chide_ok", 1);
					r.toggle(name);
				}, null);
			}
			hidden.push(name);
		}
		jwrite("filecols", hidden);
		r.set_style();
	};
	r.show = function (name) { r.setvis(name, 1); };
	r.hide = function (name) { r.setvis(name, 0); };
	r.toggle = function (name) { r.setvis(name, -1); };

	ebi('hcolsr').onclick = function (e) {
		ev(e);
		r.reset(true);
	};

	if (MOBILE)
		ebi('hcolsh').onclick = function (e) {
			ev(e);
			if (r.picking)
				return r.unpick(false);

			var lbs = QSA('#files>thead th>span');
			for (var a = 0; a < lbs.length; a++) {
				lbs[a].onclick = function (e) {
					ev(e);
					if (toast.tag == 'pickhide')
						toast.hide();

					r.hide(e.target.textContent);
					r.unpick(true);
				};
			};
			r.picking = true;
			toast.inf(0, L.cl_hpick, 'pickhide');
		};

	r.unpick = function (picked) {
		r.picking = false;
		if (!picked)
			toast.inf(5, L.cl_hcancel);

		var lbs = QSA('#files>thead th>span');
		for (var a = 0; a < lbs.length; a++)
			lbs[a].onclick = null;
	};

	r.reset = function (force) {
		if (force || JSON.stringify(def_hcols) != sread('hfilecols')) {
			console.log("applying default hidden-cols");
			hidden = [];
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
		r.set_style();
	}
	r.reset();

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

	return r;
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


var light, theme, themen;
var settheme = (function () {
	var ax = 'abcdefghijklmnopqrstuvwx';

	theme = sread('theme') || 'a';
	if (!/^[a-x][yz]/.exec(theme))
		theme = dtheme;

	themen = theme.split(/ /)[0];
	light = !!(theme.indexOf('y') + 1);

	function freshen() {
		var cl = document.documentElement.className;
		cl = cl.replace(/\b(light|dark|[a-z]{1,2})\b/g, '').replace(/ +/g, ' ');
		document.documentElement.className = cl + ' ' + theme + ' ';

		pbar.drawbuf();
		pbar.drawpos();
		vbar.draw();
		showfile.setstyle();
		bchrome();

		var html = [], itheme = ax.indexOf(theme[0]) * 2 + (light ? 1 : 0),
			names = ['classic dark', 'classic light', 'pm-monokai', 'flat light', 'vice', 'hotdog stand', 'hacker', 'hi-con'];

		for (var a = 0; a < themes; a++)
			html.push('<a href="#" class="btn tgl' + (a == itheme ? ' on' : '') +
				'" tt="' + (names[a] || 'custom') + '">' + a + '</a>');

		ebi('themes').innerHTML = html.join('');
		var btns = QSA('#themes a');
		for (var a = 0; a < themes; a++)
			btns[a].onclick = settheme;

		bcfg_set('light', light);
		tt.att(ebi('themes'));
	}

	function settheme(e) {
		var i = e;
		try { ev(e); i = e.target.textContent; } catch (ex) { }
		light = i % 2 == 1;
		var c = ax[Math.floor(i / 2)],
			l = light ? 'y' : 'z';
		theme = c + l + ' ' + c + ' ' + l;
		themen = c + l;
		swrite('theme', theme);
		freshen();
	}

	freshen();
	return settheme;
})();


(function () {
	function freshen() {
		lang = sread("lang") || lang;
		var html = [];
		for (var k in Ls)
			if (Ls.hasOwnProperty(k))
				html.push('<a href="#" class="btn tgl' + (k == lang ? ' on' : '') +
					'" tt="' + Ls[k].tt + '">' + k + '</a>');

		ebi('langs').innerHTML = html.join('');
		var btns = QSA('#langs a');
		for (var a = 0, aa = btns.length; a < aa; a++)
			btns[a].onclick = setlang;
	}

	function setlang(e) {
		ev(e);
		L = Ls[this.textContent];
		swrite("lang", this.textContent);
		freshen();
		modal.confirm(Ls.eng.lang_set + "\n\n" + Ls.nor.lang_set, location.reload.bind(location), null);
	};

	freshen();
})();


var arcfmt = (function () {
	if (!ebi('arc_fmt'))
		return { "render": function () { } };

	var html = [],
		fmts = [
			["tar", "tar", L.fz_tar],
			["zip", "zip=utf8", L.fz_zip8],
			["zip_dos", "zip", L.fz_zipd],
			["zip_crc", "zip=crc", L.fz_zipc]
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
			is_srch = !!ebi('unsearch'),
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

			if (!is_srch)
				links[a].closest('tr').setAttribute('tabindex', '0');
		}
	};

	r.loadsel = function (sel) {
		r.sel = [];
		r.load();

		var vsel = new Set();
		for (var a = 0; a < sel.length; a++)
			vsel.add(sel[a].vp);

		for (var a = 0; a < r.all.length; a++)
			if (vsel.has(r.all[a].vp))
				clmod(ebi(r.all[a].id).closest('tr'), 'sel', 1);

		r.selui();
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
	ebi('seldl').onclick = function (e) {
		ev(e);
		var sel = r.getsel();
		for (var a = 0; a < sel.length; a++)
			dl_file(sel[a].vp);
	};
	r.render = function () {
		var tds = QSA('#files tbody td+td+td'),
			is_srch = !!ebi('unsearch');

		if (!is_srch)
			for (var a = 0, aa = tds.length; a < aa; a++)
				tds[a].onclick = r.seltgl;

		r.selui(true);
		arcfmt.render();
		fileman.render();
		ebi('selzip').style.display = is_srch ? 'none' : '';
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

		var xhr = new XHR();
		xhr.vp = get_evpath();
		xhr.dn = tb.value;
		xhr.open('POST', xhr.vp, true);
		xhr.onload = xhr.onerror = cb;
		xhr.responseType = 'text';
		xhr.send(fd);

		return false;
	};

	function cb() {
		if (this.vp !== get_evpath()) {
			sf.textContent = 'aborted due to location change';
			return;
		}

		xhrchk(this, L.fd_xe1, L.fd_xe2);

		if (this.status !== 201) {
			sf.textContent = 'error: ' + this.responseText;
			return;
		}

		tb.value = '';
		clmod(sf, 'vis');
		sf.textContent = '';

		var dn = this.getResponseHeader('X-New-Dir');
		dn = dn || uricom_enc(this.dn);
		treectl.goto(this.vp + dn + '/', true);
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

		var xhr = new XHR(),
			ct = 'application/x-www-form-urlencoded;charset=UTF-8';

		xhr.msg = tb.value;
		xhr.open('POST', get_evpath(), true);
		xhr.responseType = 'text';
		xhr.onload = xhr.onerror = cb;
		xhr.setRequestHeader('Content-Type', ct);
		if (xhr.overrideMimeType)
			xhr.overrideMimeType('Content-Type', ct);

		xhr.send('msg=' + uricom_enc(xhr.msg));
		return false;
	};

	function cb() {
		xhrchk(this, L.fsm_xe1, L.fsm_xe2);

		if (this.status < 200 || this.status > 201) {
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


var globalcss = (function () {
	var ret = '';
	return function () {
		if (ret)
			return ret;

		var dcs = document.styleSheets;
		for (var a = 0; a < dcs.length; a++) {
			var base = dcs[a].href,
				ds = dcs[a].cssRules;

			if (!base)
				continue;

			base = base.replace(/[^/]+$/, '');
			for (var b = 0; b < ds.length; b++) {
				var css = ds[b].cssText.split(/\burl\(/g);
				ret += css[0];
				for (var c = 1; c < css.length; c++) {
					var delim = (/^["']/.exec(css[c])) ? css[c].slice(0, 1) : '';
					ret += 'url(' + delim + ((css[c].slice(0, 8).indexOf('://') + 1 || css[c].startsWith('/')) ? '' : base) +
						css[c].slice(delim ? 1 : 0);
				}
				ret += '\n';
			}
		}
		return ret;
	};
})();


function show_md(md, name, div, url, depth) {
	var errmsg = L.md_eshow + name + ':\n\n',
		now = get_evpath();

	url = url || now;
	if (url != now)
		return;

	if (!marked) {
		if (depth)
			return toast.warn(10, errmsg + 'failed to load marked.js')

		return import_js(SR + '/.cpr/deps/marked.js', function () {
			show_md(md, name, div, url, 1);
		});
	}

	md_plug = {}
	md = load_md_plug(md, 'pre');
	md = load_md_plug(md, 'post', sb_md);

	var marked_opts = {
		headerPrefix: 'md-',
		breaks: true,
		gfm: true
	};
	var ext = md_plug.pre;
	if (ext)
		Object.assign(marked_opts, ext[0]);

	try {
		clmod(div, 'mdo', 1);
		if (sandbox(div, sb_md, 'mdo', marked.parse(md, marked_opts)))
			return;

		ext = md_plug.post;
		ext = ext ? [ext[0].render, ext[0].render2] : [];
		for (var a = 0; a < ext.length; a++)
			if (ext[a])
				try {
					ext[a](div);
				}
				catch (ex) {
					console.log(ex);
				}

		var els = QSA('#epi a');
		for (var a = 0, aa = els.length; a < aa; a++) {
			var href = els[a].getAttribute('href');
			if (!href.startsWith('#') || href.startsWith('#md-'))
				continue;

			els[a].setAttribute('href', '#md-' + href.slice(1));
		}
		set_tabindex();
		var hash = location.hash;
		if (hash.startsWith('#md-'))
			setTimeout(function () {
				try {
					QS(hash).scrollIntoView();
				}
				catch (ex) { }
			}, 1);
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


function sandbox(tgt, rules, cls, html) {
	if (!rules || (html || '').indexOf('<') == -1) {
		tgt.innerHTML = html;
		clmod(tgt, 'sb');
		return false;
	}
	clmod(tgt, 'sb', 1);
	var tid = tgt.getAttribute('id'),
		hash = location.hash,
		want = '';

	if (hash.startsWith('#md-'))
		want = hash.slice(1);

	var env = '', tags = QSA('script');
	for (var a = 0; a < tags.length; a++) {
		var js = tags[a].innerHTML;
		if (js && js.indexOf('have_up2k_idx') + 1)
			env = js.split(/\blogues *=/)[0] + 'a;';
	}

	html = '<html class="iframe ' + document.documentElement.className + '"><head><style>' + globalcss() +
		'</style><base target="_parent"></head><body id="b" class="logue ' + cls + '">' + html +
		'<script>' + env + '</script>' +
		'<script src="' + SR + '/.cpr/util.js?_={{ ts }}"></script>' +
		'<script>var ebi=document.getElementById.bind(document),d=document.documentElement,' +
		'loc=new URL("' + location.href.split('?')[0] + '");' +
		'function say(m){window.parent.postMessage(m,"*")};' +
		'setTimeout(function(){var its=0,pih=-1,f=function(){' +
		'var ih=2+Math.min(parseInt(getComputedStyle(d).height),d.scrollHeight);' +
		'if(ih!=pih){pih=ih;say("iheight #' + tid + ' "+ih,"*")}' +
		'if(++its<20)return setTimeout(f,20);if(its==20)setInterval(f,200)' +
		'};f();' +
		'window.onfocus=function(){say("igot #' + tid + '")};' +
		'window.onblur=function(){say("ilost #' + tid + '")};' +
		'var el="' + want + '"&&ebi("' + want + '");' +
		'if(el)say("iscroll #' + tid + ' "+el.offsetTop);' +
		(cls == 'mdo' && md_plug.post ?
			'const x={' + md_plug.post + '};' +
			'if(x.render)x.render(ebi("b"));' +
			'if(x.render2)x.render2(ebi("b"));' : '') +
		'},1)</script></body></html>';

	var fr = mknod('iframe');
	fr.setAttribute('sandbox', rules ? 'allow-' + rules.replace(/ /g, ' allow-') : '');
	fr.setAttribute('srcdoc', html);
	tgt.innerHTML = '';
	tgt.appendChild(fr);
	return true;
}
window.addEventListener("message", function (e) {
	try {
		console.log('msg:' + e.data);
		var t = e.data.split(/ /g);
		if (t[0] == 'iheight') {
			var el = QS(t[1] + '>iframe');
			el.style.height = t[2] + 'px';
			el.style.visibility = 'unset';
		}
		else if (t[0] == 'iscroll') {
			var y1 = QS(t[1]).offsetTop,
				y2 = parseInt(t[2]);
			console.log(y1, y2);
			document.documentElement.scrollTop = y1 + y2;
		}
		else if (t[0] == 'igot' || t[0] == 'ilost') {
			clmod(QS(t[1] + '>iframe'), 'focus', t[0] == 'igot');
		}
	} catch (ex) {
		console.log('msg-err: ' + ex);
	}
}, false);


if (sb_lg && logues.length) {
	sandbox(ebi('pro'), sb_lg, '', logues[0]);
	sandbox(ebi('epi'), sb_lg, '', logues[1]);
}


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
		L.un_m1 + ' &ndash; <a id="unpost_refresh" href="#">' + L.un_upd + '</a>' +
		'<p>' + L.un_flt + ' <input type="text" id="unpost_filt" size="20" placeholder="documents/passwords" /><a id="unpost_nofilt" href="#">' + L.un_fclr + '</a></p>' +
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
			if (!xhrchk(this, L.fu_xe1, L.fu_xe2))
				return ebi('op_unpost').innerHTML = L.fu_xe1;

			var res = JSON.parse(this.responseText);
			if (res.length) {
				if (res.length == 2000)
					html.push("<p>" + L.un_max);
				else
					html.push("<p>" + L.un_avail.format(res.length));

				html.push(" &ndash; " + L.un_m2 + "</p>");
				html.push("<table><thead><tr><td></td><td>time</td><td>size</td><td>file</td></tr></thead><tbody>");
			}
			else
				html.push('-- <em>' + (filt.value ? L.un_no2 : L.un_no1) + '</em>');

			var mods = [10, 100, 1000];
			for (var a = 0; a < res.length; a++) {
				for (var b = 0; b < mods.length; b++)
					if (a % mods[b] == 0 && res.length > a + mods[b] / 10)
						html.push(
							'<tr><td></td><td colspan="3" style="padding:.5em">' +
							'<a me="' + me + '" class="n' + a + '" n2="' + (a + mods[b]) +
							'" href="#">' + L.un_next.format(Math.min(mods[b], res.length - a)) + '</a></td></tr>');
				html.push(
					'<tr><td><a me="' + me + '" class="n' + a + '" href="#">' + L.un_del + '</a></td>' +
					'<td>' + unix2iso(res[a].at) + '</td>' +
					'<td>' + res[a].sz + '</td>' +
					'<td>' + linksplit(res[a].vp).join(' ') + '</td></tr>');
			}

			html.push("</tbody></table>");
			ct.innerHTML = html.join('\n');
			r.files = res;
			r.me = me;
		}

		var q = SR + '/?ups';
		if (filt.value)
			q += '&filter=' + uricom_enc(filt.value, true);

		var xhr = new XHR();
		xhr.open('GET', q, true);
		xhr.onload = xhr.onerror = unpost_load_cb;
		xhr.send();

		ct.innerHTML = "<p><em>" + L.un_m3 + "</em></p>";
	};

	function unpost_delete_cb() {
		if (this.status !== 200) {
			var msg = this.responseText;
			toast.err(9, L.un_derr + msg);
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
			return toast.err(0, L.un_f5);

		var n = parseInt(tgt.className.slice(1)),
			n2 = parseInt(tgt.getAttribute('n2') || n + 1),
			req = [];

		for (var a = n; a < n2; a++) {
			var links = QSA('#op_unpost a.n' + a);
			if (!links.length)
				continue;

			req.push(uricom_dec(r.files[a].vp.split('?')[0]));
			for (var b = 0; b < links.length; b++) {
				links[b].removeAttribute('href');
				links[b].innerHTML = '[busy]';
			}
		}

		toast.show('inf r', 0, L.un_busy.format(req.length));

		var xhr = new XHR();
		xhr.n = n;
		xhr.n2 = n2;
		xhr.open('POST', SR + '/?delete&lim=' + req.length, true);
		xhr.onload = xhr.onerror = unpost_delete_cb;
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
	if (ctrl(e))
		return true;

	var a = e.target.closest('a[href]');
	if (!a || !(a = a.getAttribute('href') + '') || !a.endsWith('/'))
		return;

	thegrid.setvis(true);
	treectl.reqls(a, true);
	return ev(e);
};


ebi('files').onclick = ebi('docul').onclick = function (e) {
	if (ctrl(e))
		return true;

	var tgt = e.target.closest('a[id]');
	if (tgt && tgt.getAttribute('id').indexOf('f-') === 0 && tgt.textContent.endsWith('/')) {
		var el = treectl.find(tgt.textContent.slice(0, -1));
		if (el) {
			el.click();
			return ev(e);
		}
		treectl.reqls(tgt.getAttribute('href'), true);
		return ev(e);
	}

	tgt = e.target.closest('a[hl]');
	if (tgt) {
		var a = ebi(tgt.getAttribute('hl')),
			fun = function () {
				showfile.show(noq_href(a), tgt.getAttribute('lang'));
			},
			szs = ft2dict(a.closest('tr'))[0].sz,
			sz = parseInt(szs.replace(/[, ]/g, ''));

		if (sz < 1024 * 1024)
			fun();
		else
			modal.confirm(L.f_bigtxt.format(f2f(sz / 1024 / 1024, 1)), fun, null);

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
		if (audio_eq)
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
	if (audio_eq)
		audio_eq.acst = {};

	setTimeout(pbar.onresize, 1);
}


function reload_browser() {
	filecols.set_style();

	var parts = get_evpath().split('/'),
		rm = ebi('entree'),
		ftab = ebi('files'),
		link = '', o;

	while (rm.nextSibling)
		rm.parentNode.removeChild(rm.nextSibling);

	for (var a = 0; a < parts.length - 1; a++) {
		link += parts[a] + '/';
		o = mknod('a');
		o.setAttribute('href', link);
		o.textContent = uricom_dec(parts[a]) || '/';
		ebi('path').appendChild(mknod('i'));
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

	var ns = ['pro', 'epi', 'lazy']
	for (var a = 0; a < ns.length; a++)
		clmod(ebi(ns[a]), 'hidden', ebi('unsearch'));

	if (up2k)
		up2k.set_fsearch();

	thegrid.setdirty();
	msel.render();
}
treectl.hydrate();
