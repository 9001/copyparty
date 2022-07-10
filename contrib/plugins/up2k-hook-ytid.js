// way more specific example --
// assumes all files dropped into the uploader have a youtube-id somewhere in the filename,
// locates the youtube-ids and passes them to an API which returns a list of IDS which should be uploaded

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

        if (nothing_to_do)
            return modal.alert('Good news -- turns out we already have all those videos.\n\nBut thank you for checking in!');
        else if (n_skip)
            toast.inf(0, `skipped ${n_skip} files which already exist on the server`);

        [good_files, nil_files, bad_files] = new_lists;
        hooks[0](good_files, nil_files, bad_files, hooks.slice(1));
    };
    xhr.send(Array.from(yt_ids).join('\n'));
}

up2k_hooks.push(function () {
    up2k.gotallfiles.unshift(up2k_namefilter);
});
