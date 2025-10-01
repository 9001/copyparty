"use strict";


// USAGE:
//   place this file somewhere in the webroot, 
//   for example in a folder named ".res" to hide it, and then
//   python3 copyparty-sfx.py -v .::A --js-browser /.res/quickmove.js
//
// DESCRIPTION:
//   the command above launches copyparty with one single volume;
//   ".::A" = current folder as webroot, and everyone has Admin
//
//   the plugin adds hotkey "W" which moves all selected files
//   into a subfolder named "foobar" inside the current folder


(function() {

    var action_to_perform = ask_for_confirmation_and_then_move;
    // this decides what the new hotkey should do;
    //  ask_for_confirmation_and_then_move  =  show a yes/no box,
    //  move_selected_files  =  just move the files immediately

    var move_destination = "foobar";
    // this is the target folder to move files to;
    // by default it is a subfolder of the current folder,
    // but it can also be an absolute path like "/foo/bar"

    // ===
    // ===   END OF CONFIG
    // ===

    var main_hotkey_handler,  // copyparty's original hotkey handler
        plugin_enabler,  // timer to engage this plugin when safe
        files_to_move;  // list of files to move

    function ask_for_confirmation_and_then_move() {
        var num_files = msel.getsel().length,
            msg = "move the selected " + num_files + " files?";

        if (!num_files)
            return toast.warn(2, 'no files were selected to be moved');

        modal.confirm(msg, move_selected_files, null);
    }

    function move_selected_files() {
        var selection = msel.getsel();

        if (!selection.length)
            return toast.warn(2, 'no files were selected to be moved');

        if (thegrid.bbox) {
            // close image/video viewer
            thegrid.bbox = null;
            baguetteBox.destroy();
        }

        files_to_move = [];
        for (var a = 0; a < selection.length; a++)
            files_to_move.push(selection[a].vp);

        move_next_file();
    }

    function move_next_file() {
        var num_files = files_to_move.length,
            filepath = files_to_move.pop(),
            filename = vsplit(filepath)[1];

        toast.inf(10, "moving " + num_files + " files...\n\n" + filename);

        var dst = move_destination;

        if (!dst.endsWith('/'))
            // must have a trailing slash, so add it
            dst += '/';

        if (!dst.startsWith('/'))
            // destination is a relative path, so prefix current folder path
            dst = get_evpath() + dst;

        // and finally append the filename
        dst += '/' + filename;

        // prepare the move-request to be sent
        var xhr = new XHR();
        xhr.onload = xhr.onerror = function() {
            if (this.status !== 201)
                return toast.err(30, 'move failed: ' + esc(this.responseText));

            if (files_to_move.length)
                return move_next_file();  // still more files to go

            toast.ok(1, 'move OK');
            treectl.goto(); // reload the folder contents
        };
        xhr.open('POST', filepath + '?move=' + dst);
        xhr.send();
    }

    function our_hotkey_handler(e) {
        // bail if either ALT, CTRL, or SHIFT is pressed
        if (anymod(e))
            return main_hotkey_handler(e);  // let copyparty handle this keystroke

        var keycode = (e.key || e.code) + '',
    		ae = document.activeElement,
		    aet = ae && ae != document.body ? ae.nodeName.toLowerCase() : '';

        // check the current aet (active element type),
        // only continue if one of the following currently has input focus:
        //   nothing | link | button | table-row | table-cell | div | text
        if (aet && !/^(a|button|tr|td|div|pre)$/.test(aet))
            return main_hotkey_handler(e);  // let copyparty handle this keystroke

        if (keycode == 'w' || keycode == 'KeyW') {
            // okay, this one's for us... do the thing
            action_to_perform();
            return ev(e);
        }

        return main_hotkey_handler(e);  // let copyparty handle this keystroke
    }

    function enable_plugin() {
        if (!window.hotkeys_attached)
            return console.log('quickmove is waiting for the page to finish loading');

        clearInterval(plugin_enabler);
        main_hotkey_handler = document.onkeydown;
        document.onkeydown = our_hotkey_handler;
        console.log('quickmove is now enabled');
    }

    // copyparty doesn't enable its hotkeys until the page
    // has finished loading, so we'll wait for that too
    plugin_enabler = setInterval(enable_plugin, 100);

})();
