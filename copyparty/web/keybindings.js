const HOTKEY_ACTIONS = {
    ESCAPE: {
        code: "escape",
        tr: L.hotkeys.ESC,
    },
    ENTER: {
        code: "enter",
        tr: L.hotkeys.ENTER,
    },
    HELP: {
        code: "?",
        tr: L.hotkeys.HELP,
    },
    PREV_SONG: {
        code: "prevSong",
        tr: L.hotkeys.PREV_SONG,
    },
    NEXT_SONG: {
        code: "nextSong",
        tr: L.hotkeys.NEXT_SONG,
    },
    TREE_PREV: {
        code: "treePrev",
        tr: L.hotkeys.TREE_PREV,
    },
    TREE_NEXT: {
        code: "treeNext",
        tr: L.hotkeys.TREE_NEXT,
    },
    TREE_UP: {
        code: "treeUp",
        tr: L.hotkeys.TREE_UP,
    },
    PLAY_PAUSE: {
        code: "playPause",
        tr: L.hotkeys.PLAY_PAUSE,
    },
    DOWNLOAD: {
        code: "download",
        tr: L.hotkeys.DOWNLOAD,
    },
    CUT: {
        code: "cut",
        tr: L.hotkeys.CUT,
    },
    COPY: {
        code: "copy",
        tr: L.hotkeys.COPY,
        context: (ctx) => {
            var sel = window.getSelection && window.getSelection() || {};
            sel = sel && !sel.isCollapsed && sel.direction != 'none';
            return !sel;
        },
    },
    PASTE: {
        code: "paste",
        tr: L.hotkeys.PASTE,
    },
    DELETE: {
        code: "delete",
        tr: L.hotkeys.DELETE,
    },
    FAST_FORWARD: {
        code: "fastForward",
        tr: L.hotkeys.FAST_FORWARD,
    },
    REWIND: {
        code: "rewind",
        tr: L.hotkeys.REWIND,
    },
    TOGGLE_BREADCRUMBS: {
        code: "toggleBreadcrumbs",
        tr: L.hotkeys.TOGGLE_BREADCRUMBS,
    },
    TOGGLE_GRID: {
        code: "toggleGrid",
        tr: L.hotkeys.TOGGLE_GRID,
    },
    TOGGLE_THUMBNAILS: {
        code: "toggleThumbnails",
        tr: L.hotkeys.TOGGLE_THUMBNAILS,
    },
    TOGGLE_FOLDER_TREE: {
        code: "toggleFolderTree",
        tr: L.hotkeys.TOGGLE_FOLDER_TREE,
    },
    RENAME: {
        code: "rename",
        tr: L.hotkeys.RENAME,
    },
    NAVPANE_SHRINK: {
        code: "navpaneShrink",
        tr: L.hotkeys.NAVPANE_SHRINK,
        context: (ctx) => {
            return !ctx.treectl.hidden && ctx.gridMode;
        },
        desc: L.hotkeys.NAVPANE_SHRINK_DESC
    },
    NAVPANE_GROW: {
        code: "navpaneGrow",
        tr: L.hotkeys.NAVPANE_GROW,
        context: (ctx) => {
            return !ctx.treectl.hidden && ctx.gridMode;
        },
        desc: L.hotkeys.NAVPANE_GROW_DESC
    },
    SELECT_ALL: {
        code: "selectAll",
        tr: L.hotkeys.SELECT_ALL,
        context: (ctx) => {
            return ctx.activeElement && ctx.activeElement.closest('pre')
        },
    },
    SELECT_SONG: {
        code: "selectSong",
        tr: L.hotkeys.SELECT_SONG,
        context: (ctx) => {
            return ctx.mp && ctx.mp.au && !ctx.mp.au.paused;
        },
        desc: L.hotkeys.SELECT_SONG_DESC
    },
    SELECT_FILE: {
        code: "selectFile",
        tr: L.hotkeys.SELECT_FILE,
        context: (ctx) => {
            return ctx.showfile.active();
        },
        desc: L.hotkeys.SELECT_FILE_DESC
    },
    EDIT_FILE: {
        code: "editFile",
        tr: L.hotkeys.EDIT_FILE,
        context: (ctx) => {
            return ctx.showfile.active();
        },
        desc: L.hotkeys.EDIT_FILE_DESC
    },

    TOGGLE_GRID_MULTISELECT: {
        code: "toggleGridMultiSelect",
        tr: L.hotkeys.TOGGLE_GRID_MULTISELECT,
        context: (ctx) => {
            return ctx.gridMode;
        },
        desc: L.hotkeys.TOGGLE_GRID_MULTISELECT_DESC
    },
    GRID_SHRINK_THUMBNAILS: {
        code: "gridShrinkThumbnails",
        tr: L.hotkeys.GRID_SHRINK_THUMBNAILS,
        context: (ctx) => {
            return ctx.gridMode;
        },
        desc: L.hotkeys.GRID_SHRINK_THUMBNAILS_DESC
    },
    GRID_GROW_THUMBNAILS: {
        code: "gridGrowThumbnails",
        tr: L.hotkeys.GRID_GROW_THUMBNAILS,
        context: (ctx) => {
            return ctx.gridMode;
        },
        desc: L.hotkeys.GRID_GROW_THUMBNAILS_DESC
    },
}

const defaultKeybindings = {
    "escape": HOTKEY_ACTIONS.ESCAPE,
    "enter": HOTKEY_ACTIONS.ENTER,
    "shift+?": HOTKEY_ACTIONS.HELP,
    "?": HOTKEY_ACTIONS.HELP,
    "J": HOTKEY_ACTIONS.PREV_SONG,
    "L": HOTKEY_ACTIONS.NEXT_SONG,
    "K": HOTKEY_ACTIONS.TREE_NEXT,
    "I": HOTKEY_ACTIONS.TREE_PREV,
    "P": HOTKEY_ACTIONS.PLAY_PAUSE,
    "Y": HOTKEY_ACTIONS.DOWNLOAD,
    "ctrl+X": HOTKEY_ACTIONS.CUT,
    "ctrl+C": HOTKEY_ACTIONS.COPY,
    "ctrl+V": HOTKEY_ACTIONS.PASTE,
    "ctrl+K": HOTKEY_ACTIONS.DELETE,
    "meta+X": HOTKEY_ACTIONS.CUT,
    "meta+C": HOTKEY_ACTIONS.COPY,
    "meta+V": HOTKEY_ACTIONS.PASTE,
    "meta+K": HOTKEY_ACTIONS.DELETE,
    "O": HOTKEY_ACTIONS.FAST_FORWARD,
    "U": HOTKEY_ACTIONS.REWIND,
    "M": HOTKEY_ACTIONS.TREE_UP,
    "B": HOTKEY_ACTIONS.TOGGLE_BREADCRUMBS,
    "G": HOTKEY_ACTIONS.TOGGLE_GRID,
    "T": HOTKEY_ACTIONS.TOGGLE_THUMBNAILS,
    "V": HOTKEY_ACTIONS.TOGGLE_FOLDER_TREE,
    "F2": HOTKEY_ACTIONS.RENAME,
    "A": HOTKEY_ACTIONS.NAVPANE_SHRINK,
    "D": HOTKEY_ACTIONS.NAVPANE_GROW,
    "ctrl+A": HOTKEY_ACTIONS.SELECT_ALL,
    "S": HOTKEY_ACTIONS.SELECT_SONG,
    "E": HOTKEY_ACTIONS.EDIT_FILE,
    "S": HOTKEY_ACTIONS.SELECT_FILE,
    "shift+S": HOTKEY_ACTIONS.TOGGLE_GRID_MULTISELECT,
    "shift+A": HOTKEY_ACTIONS.GRID_SHRINK_THUMBNAILS,
    "shift+D": HOTKEY_ACTIONS.GRID_GROW_THUMBNAILS,
};
//TODO bit of a mess
const currentKeybindings = readKeybindings();
const keybindingTree = toTree(currentKeybindings);

/**
 * Reads the keybindings from localStorage
 * @returns {object} Current user Keybidnds 
 */
function readKeybindings() {
    const s = sread("keybindings");
    if (!s) {
        return defaultKeybindings;
    }

    return JSON.parse(s);
}

/**
 * Resets the keybindings to default
 * @returns {object} Default keybindings
 */
function resetKeybindings() {
    srem("keybindings");
    return defaultKeybindings;
}

/**
 * Sets a keybinding for a specific action
 * @param {string} combo Key combination
 * @param {function} callback Callback function
 */
function setKeybinding(event) {
    console.log('Not implemented setKeybinding', event);
    // sset("keybindings", JSON.stringify(keybindings));
}

function getHotkeyEvent(event, context = {}) {
    const hash = event.ctrlKey << 2 | event.metaKey << 1 | event.shiftKey;
    let kkey = (event.key || event.code) + '';
    const matchingHotkeys = keybindingTree[hash][kkey.toLowerCase()] || [];
    console.log('getHotkeyEvent', event, context, hash, matchingHotkeys);
    if (matchingHotkeys.length < 2) {
        return matchingHotkeys[0];
    }

    var validIndex = -1;
    for (var i = 0; i < matchingHotkeys.length; i++) {
        var hotkey = matchingHotkeys[i];
        if (hotkey.context) {
            if (hotkey.context(context)) return hotkey;
        } else {
            validIndex = i;
        }
    }

    console.log('More than 1 matching hotkey without sufficient context check found', event, context, hash, matchingHotkeys);
    return matchingHotkeys[validIndex];
}

/**
 * Convers human readable keybindings into a tree structure for fast lookup
 * @param {object} keybindings 
 * @see getHotkeyEvent for usage
 * @returns {object[]} tree of keybindings for fast lookup
 */
function toTree(keybindings) {
    var tree = [...Array(8)].map(() => ({}));
    
    for (var combo in keybindings) {
        var action = keybindings[combo];

        var parts = combo.split("+").map(function (p) {
            return p.trim().toLowerCase();
        });

        var hash = 0;
        hash += parts.indexOf("shift") !== -1 ? 1 : 0;
        hash += parts.indexOf("ctrl")  !== -1 ? 2 : 0;
        hash += parts.indexOf("meta")  !== -1 ? 4 : 0;
        var key = parts[parts.length - 1];  // last part is the key

        console.log('binding', combo, action, hash, key);
        if (!tree[hash][key]) tree[hash][key] = [];
        tree[hash][key].push(action);
    }

    console.log('Tree', keybindings, '=>', tree);

    return tree;
}