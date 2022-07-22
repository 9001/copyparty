// way more specific example --
// assumes all files dropped into the uploader have a youtube-id somewhere in the filename,
// locates the youtube-ids and passes them to an API which returns a list of IDs which should be uploaded
//
// assumes copyparty is behind nginx as /ytq is a standalone service which must be rproxied in place

function up2k_namefilter(good_files, nil_files, bad_files, hooks) {
    var filenames = [],
        file_lists = [good_files, nil_files, bad_files];

    for (var lst of file_lists)
        for (var ent of lst)
            filenames.push(ent[1]);

    var yt_ids = new Set();
    for (var lst of file_lists)
        for (var ent of lst) {
            var m, name = ent[1];
            while (true) {
                // some ytdl fork did %(title)-%(id).%(ext) ...
                m = /(?:^|[^\w])([\w-]{11})(?:$|[^\w-])/.exec(name);
                if (!m)
                    break;

                yt_ids.add(m[1]);
                name = name.replace(m[1], '');
            }
        }

    toast.inf(5, `running query for ${yt_ids.size} videos...`);

    var xhr = new XHR();
    xhr.open('POST', '/ytq', true);
    xhr.setRequestHeader('Content-Type', 'text/plain');
    xhr.onload = xhr.onerror = function () {
        if (this.status != 200)
            return toast.err(0, `sorry, database query failed ;_;\n\nplease let us know so we can look at it, thx!!\n\nerror ${this.status}: ${(this.response && this.response.err) || this.responseText}`);

        var new_lists = [],
            ptn = new RegExp(this.responseText.trim().split('\n').join('|') || '\n'),
            nothing_to_do = true,
            n_skip = 0;

        for (var lst of file_lists) {
            var keep = [];
            new_lists.push(keep);

            for (var ent of lst)
                if (ptn.exec(ent[1]))
                    keep.push(ent);
                else
                    n_skip++;

            if (keep.length)
                nothing_to_do = false;
        }

        function upload_filtered() {
            if (nothing_to_do)
                return modal.alert('Good news -- turns out we already have all those.\n\nBut thank you for checking in!');

            [good_files, nil_files, bad_files] = new_lists;
            hooks[0](good_files, nil_files, bad_files, hooks.slice(1));
        }

        function upload_all() {
            hooks[0](good_files, nil_files, bad_files, hooks.slice(1));
        }

        var msg = `you added ${good_files.length} files; ${n_skip} of them were skipped --\neither because we already have them,\nor because there is no youtube-ID in your filename.\n\n<code>OK</code> / <code>Enter</code> = continue uploading the ${new_lists[0].length} files we definitely need\n\n<code>Cancel</code> / <code>ESC</code> = override the filter; upload ALL the files you added`;

        if (!n_skip)
            upload_filtered();
        else
            modal.confirm(msg, upload_filtered, upload_all);

    };
    xhr.send(Array.from(yt_ids).join('\n'));
}

up2k_hooks.push(function () {
    up2k.gotallfiles.unshift(up2k_namefilter);
});
