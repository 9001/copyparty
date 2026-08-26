/* ============================================================
   Feather icons for copyparty — Paper & Vibrant themes
   Replaces emoji with Feather SVG icons when the f/g themes
   (Paper / Vibrant) are active — everywhere in the UI, including
   dynamically-injected panels (up2k, player, menus, toasts).

   Notes:
   * only the copyparty UI is rewritten; user content such as
     file listings, the navpane and rendered markdown/readmes is
     left untouched
   * user-added emojis (potato mode, konami spinner) are kept
   ============================================================ */

var feather = (function () {
	var r = {};
	var icons = {
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>',
    "trash": '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
    "file-plus": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>',
    "folder": '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
    "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>',
    "message-square": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "music": '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    "share": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>',
    "coffee": '<path d="M18 8h1a4 4 0 0 1 0 8h-1"/><path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"/><line x1="6" y1="1" x2="6" y2="4"/><line x1="10" y1="1" x2="10" y2="4"/><line x1="14" y1="1" x2="14" y2="4"/>',
    "clipboard": '<rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="10" y="9" width="4" height="4" rx="1" ry="1"/>',
    "package": '<line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>',
    "play": '<polygon points="5 3 19 12 5 21 5 3"/>',
    "pause": '<rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>',
    "skip-back": '<polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5"/>',
    "skip-forward": '<polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/>',
    "flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/>',
    "bell": '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
    "volume-2": '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>',
    "volume-x": '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>',
    "award": '<circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>',
    "align-left": '<line x1="17" y1="10" x2="3" y2="10"/><line x1="21" y1="6" x2="3" y2="6"/><line x1="21" y1="14" x2="3" y2="14"/><line x1="17" y1="18" x2="3" y2="18"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "eye": '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
    "repeat": '<polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/>',
    "shuffle": '<polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="15" y1="15" x2="21" y2="21"/><line x1="4" y1="4" x2="9" y2="9"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "save": '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "terminal": '<polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/>',
    "headphones": '<path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>',
    "thumbs-up": '<path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>',
    "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>',
    "radio": '<circle cx="12" cy="12" r="2"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M7.76 16.24a6 6 0 0 1 0-8.49"/><path d="M4.93 19.07a10 10 0 0 1 0-14.14"/>',
    "plus": '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    "x": '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "list": '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
    "grid": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>',
    "pin": '<line x1="12" y1="17" x2="12" y2="3"/><circle cx="12" cy="20" r="1"/>',
    "corner-down-left": '<polyline points="9 10 4 15 9 20"/><path d="M20 4v7a4 4 0 0 1-4 4H4"/>',
    "git-branch": '<line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
    "arrow-up": '<line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>',
    "arrow-down": '<line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/>',
    "chevron-down": '<polyline points="6 9 12 15 18 9"/>',
    "chevron-up": '<polyline points="18 15 12 9 6 15"/>',
    "rotate-ccw": '<polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>',
    "rotate-cw": '<polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>',
    "maximize": '<path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>',
    "refresh-cw": '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    "help-circle": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "edit-2": '<path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>',
    "edit-3": '<path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>',
    "delete": '<path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z"/><line x1="18" y1="9" x2="12" y2="15"/><line x1="12" y1="9" x2="18" y2="15"/>',
    "scissors": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><line x1="20" y1="4" x2="8.12" y2="15.88"/><line x1="14.47" y1="14.48" x2="20" y2="20"/><line x1="8.12" y1="8.12" x2="12" y2="12"/>',
    "anchor": '<circle cx="12" cy="5" r="3"/><line x1="12" y1="22" x2="12" y2="8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "loader": '<line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/>',
	};
	// Map emoji → icon name
	var emojiMap = {
		'\uD83D\uDD0E': 'search', // 🔎
		'\uD83E\uDDEF': 'trash', // 🧯
		'\uD83D\uDE80': 'upload', // 🚀
		'\uD83C\uDF88': 'file-plus', // 🎈
		'\uD83D\uDCC2': 'folder', // 📂
		'\uD83D\uDCC1': 'folder', // 📁
		'\uD83D\uDCDD': 'file-text', // 📝
		'\uD83D\uDCDF': 'message-square', // 📟
		'\uD83C\uDFBA': 'music', // 🎺
		'\u2699': 'settings', // ⚙
		'\u2699\uFE0F': 'settings', // ⚙️
		'\uD83D\uDCE8': 'share', // 📨
		'\uD83D\uDCCB': 'clipboard', // 📋
		'\uD83D\uDCE6': 'package', // 📦
		'\u25B6': 'play', // ▶
		'\u23F8': 'pause', // ⏸
		'\u23EE': 'skip-back', // ⏮
		'\u23ED': 'skip-forward', // ⏭
		'\uD83D\uDCA4': 'flag', // 💤
		'\uD83D\uDD14': 'bell', // 🔔
		'\uD83D\uDD0A': 'volume-2', // 🔊
		'\uD83D\uDD07': 'volume-x', // 🔇
		'\uD83C\uDF89': 'award', // 🎉
		'\uD83C\uDF5E': 'align-left', // 🍞
		'\uD83C\uDFAF': 'target', // 🎯
		'\uD83D\uDC40': 'eye', // 👀
		'\uD83D\uDD01': 'repeat', // 🔁
		'\uD83D\uDD00': 'shuffle', // 🔀
		'\uD83C\uDFC3': 'zap', // 🏃
		'\uD83D\uDEE1': 'shield', // 🛡
		'\uD83D\uDEE1\uFE0F': 'shield', // 🛡️
		'\uD83D\uDCBE': 'save', // 💾
		'\uD83D\uDCE1': 'activity', // 📡
		'\uD83C\uDF08': 'terminal', // 🌈
		'\uD83C\uDFA7': 'headphones', // 🎧
		'\uD83D\uDC4D': 'thumbs-up', // 👍
		'\uD83D\uDCDC': 'file-text', // 📜
		'\uD83D\uDCC3': 'file-text', // 📃
		'\uD83D\uDCC4': 'file', // 📄
		'\uD83D\uDCCC': 'pin', // 📌
		'\u2693': 'anchor', // ⚓
		'\u2702': 'scissors', // ✂
		'\u270E': 'edit-3', // ✎
		'\u270F': 'edit-2', // ✏
		'\u232B': 'delete', // ⌫
		'\u274C': 'x', // ❌
		'\u2705': 'check', // ✅
		'\u21B5': 'corner-down-left', // ↵
		'\u21BA': 'rotate-ccw', // ↺
		'\u2B06': 'arrow-up', // ⬆
		'\u2B07': 'arrow-down', // ⬇
		'\u2BAF': 'chevron-down', // ⮯
		'\uD83D\uDCC5': 'calendar', // 📅
		'\uD83D\uDCAD': 'help-circle', // 💭
		'\uD83D\uDDBC': 'image', // 🖼
		'\uD83D\uDDBC\uFE0F': 'image', // 🖼️
		'\uD83C\uDFB2': 'shuffle', // 🎲
		'\u2615': 'coffee', // ☕
		'\u2615\uFE0F': 'coffee', // ☕️
		'\uD83D\uDD52': 'clock', // 🕒
		'\u267B': 'refresh-cw', // ♻
		'\u267B\uFE0F': 'refresh-cw', // ♻️
		'\uD83D\uDCD0': 'loader', // 📐
		'\u266B': 'music', // ♫
		'\u266B\uFE0F': 'music', // ♫️
		'\u03C0': 'terminal', // π
		'\u2795': 'plus', // ➕
		'\u2715': 'x', // ✕
		'\u2713': 'check', // ✓
		'\uD83D\uDCFB': 'radio', // 📻
		'\u7530': 'grid', // 田
		'\uD83C\uDF32': 'git-branch', // 🌲
		'\u21B6': 'rotate-ccw', // ↶
		'\u21B7': 'rotate-cw', // ↷
		'\u26F6': 'maximize', // ⛶
		'\u21C4': 'repeat', // ⇄
		'\u2BBA': 'refresh-cw', // ⮺
		'\u26A1': 'zap', // ⚡
	};

	// SVG factory: 1em sized, currentColor stroke, no fill.
	// The original emoji is stored in data-emoji so revert() can
	// restore it when switching back to a non-feather theme.
	function svg(paths, emoji) {
		var el = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
		el.setAttribute('viewBox', '0 0 24 24');
		el.setAttribute('width', '1em');
		el.setAttribute('height', '1em');
		el.setAttribute('fill', 'none');
		el.setAttribute('stroke', 'currentColor');
		el.setAttribute('stroke-width', '2');
		el.setAttribute('stroke-linecap', 'round');
		el.setAttribute('stroke-linejoin', 'round');
		el.setAttribute('class', 'cpr-ico');
		el.setAttribute('aria-hidden', 'true');
		if (emoji) el.setAttribute('data-emoji', emoji);
		el.innerHTML = paths;
		return el;
	}

	// Escape regex special chars
	function escRE(s) {
		return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
	}

	var RE_EMOJI = null;
	function buildRe() {
		// longest keys first: "☕️" must win over "☕" so the
		// variation-selector is consumed in the same match
		var keys = Object.keys(emojiMap).sort(function (a, b) {
			return b.length - a.length;
		});
		RE_EMOJI = new RegExp(keys.map(escRE).join('|'), 'g');
	}

	// Replace emoji in a text node with feather SVG; returns the
	// new content (array of nodes/strings) or null if unchanged.
	function replaceEmoji(txt) {
		if (!RE_EMOJI) buildRe();
		RE_EMOJI.lastIndex = 0;
		if (!RE_EMOJI.test(txt)) {
			// drop stray variation-selectors / ZWJ residues
			if (/[\uFE0F\u200D]/.test(txt))
				return txt.replace(/[\uFE0F\u200D]/g, '');
			return null;
		}
		RE_EMOJI.lastIndex = 0;
		var parts = [], lastIdx = 0, match;
		while ((match = RE_EMOJI.exec(txt)) !== null) {
			if (match.index > lastIdx)
				parts.push(txt.slice(lastIdx, match.index));
			var iconName = emojiMap[match[0]];
			if (icons[iconName]) parts.push(svg(icons[iconName], match[0]));
			else parts.push(match[0]);
			lastIdx = RE_EMOJI.lastIndex;
		}
		if (lastIdx < txt.length) parts.push(txt.slice(lastIdx));
		return parts;
	}

	var SKIP = '#files, #pro, #epi, #docul, ul.ntree, pre, code';

	// Recursively replace emojis in a subtree, skipping user content
	function walkStats(root, stats) {
		if (!root || !root.nodeType) return;
		if (root.nodeType == 3) {
			var par = root.parentNode;
			if (par && par.closest && par.closest(SKIP)) return;
			var old = root.nodeValue;
			var parts = replaceEmoji(old);
			if (parts === null) return;
			if (typeof parts == 'string') {
				root.nodeValue = parts;
				stats.n++;
				return;
			}
			if (parts.length == 1 && parts[0] === old) return;
			var frag = document.createDocumentFragment();
			for (var i = 0; i < parts.length; i++)
				frag.appendChild(
					typeof parts[i] == 'string' ? document.createTextNode(parts[i]) : parts[i]
				);
			root.parentNode.replaceChild(frag, root);
			stats.n++;
			return;
		}
		if (root.nodeType != 1) return;
		var tn = root.nodeName;
		if (tn == 'SVG' || tn == 'PRE' || tn == 'CODE') return;
		if (root.closest && root.closest(SKIP)) return;
		var kids = root.childNodes;
		for (var i = 0; i < kids.length; i++) walkStats(kids[i], stats);
	}

	r.walk = function (root) {
		var stats = { n: 0 };
		try { walkStats(root || document.body, stats); } catch (ex) { }
		return stats.n;
	};

	// Restore original emojis by replacing every injected svg.cpr-ico
	// back with the text node it replaced (stored in data-emoji).
	// Called when the user switches to a non-feather theme at runtime.
	r.revert = function (root) {
		var els = (root || document.body).querySelectorAll('svg.cpr-ico[data-emoji]');
		for (var i = 0; i < els.length; i++) {
			var el = els[i];
			var par = el.parentNode;
			if (!par) continue;
			var emoji = el.getAttribute('data-emoji') || '';
			par.replaceChild(document.createTextNode(emoji), el);
			if (par.normalize) par.normalize();
		}
	};

	// monitor dynamically-injected UI (up2k panel, player, context
	// menus, toasts, h-repl toolbar rebuilds, ...)
	var watcher = null;
	function observe() {
		if (watcher || !window.MutationObserver) return;
		watcher = true;
		var observer = new MutationObserver(function (muts) {
			if (!themeOn()) return;
			var roots = [];
			for (var i = 0; i < muts.length; i++) {
				var mu = muts[i];
				if (mu.type == 'childList') {
					for (var j = 0; j < mu.addedNodes.length; j++) {
						var n = mu.addedNodes[j];
						if (n.nodeType == 1 || n.nodeType == 3) roots.push(n);
					}
				} else if (mu.type == 'characterData' && mu.target.nodeType == 3)
					roots.push(mu.target);
			}
			if (roots.length) r.walk(roots.length == 1 ? roots[0] : document.body);
		});
		observer.observe(document.body, {
			childList: true, subtree: true, characterData: true,
		});
		r._obs = observer;
	}

	// is the active theme one of the feather themes?
	function themeOn() {
		var cl = document.documentElement.className || '';
		// letter form  (fz / fy / gz / gy / hz / hy / iz / iy / jz / jy)
		if (/(^|\s)[fghij][yz](\s|$)/.test(cl)) return true;
		// server default form (paper=10/11, vibrant=12/13)
		if (/(^|\s)(1[0-3])(\s|$)/.test(cl)) return true;
		return false;
	}

	// self-start when the theme is loaded as f/g
	(function () {
		if (document.body && themeOn()) {
			r.walk(document.body);
			observe();
		}
	})();

	// react to theme switches at runtime
	if (window.MutationObserver) {
		var tm = new MutationObserver(function () {
			if (themeOn()) {
				r.walk(document.body);
				observe();
			} else {
				r.revert(document.body);
			}
		});
		tm.observe(document.documentElement, {
			attributes: true, attributeFilter: ['class'],
		});
		r._tm = tm;
	}

	return r;
})();