// way more specific example --
// assumes all files dropped into the uploader have a youtube-id somewhere in the filename,
// locates the youtube-ids and passes them to an API which returns a list of IDs which should be uploaded
//
// also tries to find the youtube-id in the embedded metadata
//
// assumes copyparty is behind nginx as /ytq is a standalone service which must be rproxied in place

function up2k_namefilter(good_files, nil_files, bad_files, hooks) {
    var passthru = up2k.uc.fsearch;
    if (passthru)
        return hooks[0](good_files, nil_files, bad_files, hooks.slice(1));

    a_up2k_namefilter(good_files, nil_files, bad_files, hooks).then(() => { });
}

// ebi('op_up2k').appendChild(mknod('input','unick'));

function bstrpos(buf, ptn) {
    var ofs = 0,
        ch0 = ptn[0],
        sz = buf.byteLength;

    while (true) {
        ofs = buf.indexOf(ch0, ofs);
        if (ofs < 0 || ofs >= sz)
            return -1;

        for (var a = 1; a < ptn.length; a++)
            if (buf[ofs + a] !== ptn[a])
                break;

        if (a === ptn.length)
            return ofs;

        ++ofs;
    }
}

async function a_up2k_namefilter(good_files, nil_files, bad_files, hooks) {
    var t0 = Date.now(),
        yt_ids = new Set(),
        textdec = new TextDecoder('latin1'),
        md_ptn = new TextEncoder().encode('youtube.com/watch?v='),
        file_ids = [],  // all IDs found for each good_files
        md_only = [],  // `${id} ${fn}` where ID was only found in metadata
        mofs = 0,
        mnchk = 0,
        mfile = '',
        myid = localStorage.getItem('ytid_t0');

    if (!myid)
        localStorage.setItem('ytid_t0', myid = Date.now());

    for (var a = 0; a < good_files.length; a++) {
        var [fobj, name] = good_files[a],
            cname = name,  // will clobber
            sz = fobj.size,
            ids = [],
            fn_ids = [],
            md_ids = [],
            id_ok = false,
            m;

        // all IDs found in this file
        file_ids.push(ids);

        // look for ID in filename; reduce the
        // metadata-scan intensity if the id looks safe
        m = /[\[(-]([\w-]{11})[\])]?\.(?:mp4|webm|mkv|flv|opus|ogg|mp3|m4a|aac)$/i.exec(name);
        id_ok = !!m;

        while (true) {
            // fuzzy catch-all;
            // some ytdl fork did %(title)-%(id).%(ext) ...
            m = /(?:^|[^\w])([\w-]{11})(?:$|[^\w-])/.exec(cname);
            if (!m)
                break;

            cname = cname.replace(m[1], '');
            yt_ids.add(m[1]);
            fn_ids.unshift(m[1]);
        }

        // look for IDs in video metadata,
        if (/\.(mp4|webm|mkv|flv|opus|ogg|mp3|m4a|aac)$/i.exec(name)) {
            toast.show('inf r', 0, `analyzing file ${a + 1} / ${good_files.length} :\n${name}\n\nhave analysed ${++mnchk} files in ${(Date.now() - t0) / 1000} seconds, ${humantime((good_files.length - (a + 1)) * (((Date.now() - t0) / 1000) / mnchk))} remaining,\n\nbiggest offset so far is ${mofs}, in this file:\n\n${mfile}`);

            // check first and last 128 MiB;
            // pWxOroN5WCo.mkv @  6edb98 (6.92M)
            // Nf-nN1wF5Xo.mp4 @ 4a98034 (74.6M)
            var chunksz = 1024 * 1024 * 2,  // byte
                aspan = id_ok ? 128 : 512;  // MiB

            aspan = parseInt(Math.min(sz / 2, aspan * 1024 * 1024) / chunksz) * chunksz;
            if (!aspan)
                aspan = Math.min(sz, chunksz);

            for (var side = 0; side < 2; side++) {
                var ofs = side ? Math.max(0, sz - aspan) : 0,
                    nchunks = aspan / chunksz;

                for (var chunk = 0; chunk < nchunks; chunk++) {
                    var bchunk = await fobj.slice(ofs, ofs + chunksz + 16).arrayBuffer(),
                        uchunk = new Uint8Array(bchunk, 0, bchunk.byteLength),
                        bofs = bstrpos(uchunk, md_ptn),
                        absofs = Math.min(ofs + bofs, (sz - ofs) + bofs),
                        txt = bofs < 0 ? '' : textdec.decode(uchunk.subarray(bofs)),
                        m;

                    //console.log(`side ${ side }, chunk ${ chunk }, ofs ${ ofs }, bchunk ${ bchunk.byteLength }, txt ${ txt.length }`);
                    while (true) {
                        // mkv/webm have [a-z] immediately after url
                        m = /(youtube\.com\/watch\?v=[\w-]{11})/.exec(txt);
                        if (!m)
                            break;

                        txt = txt.replace(m[1], '');
                        m = m[1].slice(-11);

                        console.log(`found ${m} @${bofs}, ${name} `);
                        yt_ids.add(m);
                        if (!has(fn_ids, m) && !has(md_ids, m)) {
                            md_ids.push(m);
                            md_only.push(`${m} ${name}`);
                        }
                        else
                            // id appears several times; make it preferred
                            md_ids.unshift(m);

                        // bail after next iteration
                        chunk = nchunks - 1;
                        side = 9;

                        if (mofs < absofs) {
                            mofs = absofs;
                            mfile = name;
                        }
                    }
                    ofs += chunksz;
                    if (ofs >= sz)
                        break;
                }
            }
        }

        for (var yi of md_ids)
            ids.push(yi);

        for (var yi of fn_ids)
            if (!has(ids, yi))
                ids.push(yi);
    }

    if (md_only.length)
        console.log('recovered the following youtube-IDs by inspecting metadata:\n\n' + md_only.join('\n'));
    else if (yt_ids.size)
        console.log('did not discover any additional youtube-IDs by inspecting metadata; all the IDs also existed in the filenames');
    else
        console.log('failed to find any youtube-IDs at all, sorry');

    if (false) {
        var msg = `finished analysing ${mnchk} files in ${(Date.now() - t0) / 1000} seconds,\n\nbiggest offset was ${mofs} in this file:\n\n${mfile}`,
            mfun = function () { toast.ok(0, msg); };

        mfun();
        setTimeout(mfun, 200);

        return hooks[0]([], [], [], hooks.slice(1));
    }

    var el = ebi('unick'), unick = el ? el.value : '';
    if (unick) {
        console.log(`sending uploader nickname [${unick}]`);
        fetch(document.location, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8' },
            body: 'msg=' + encodeURIComponent(unick)
        });
    }

    toast.inf(5, `running query for ${yt_ids.size} youtube-IDs...`);

    var xhr = new XHR();
    xhr.open('POST', '/ytq', true);
    xhr.setRequestHeader('Content-Type', 'text/plain');
    xhr.onload = xhr.onerror = function () {
        if (this.status != 200)
            return toast.err(0, `sorry, database query failed ;_;\n\nplease let us know so we can look at it, thx!!\n\nerror ${this.status}: ${(this.response && this.response.err) || this.responseText}`);

        process_id_list(this.responseText);
    };
    xhr.send(Array.from(yt_ids).join('\n'));

    function process_id_list(txt) {
        var wanted_ids = new Set(txt.trim().split('\n')),
            name_id = {},
            wanted_names = new Set(),  // basenames with a wanted ID -- not including relpath
            wanted_names_scoped = {},  // basenames with a wanted ID -> list of dirs to search under
            wanted_files = new Set();  // filedrops

        for (var a = 0; a < good_files.length; a++) {
            var name = good_files[a][1];
            for (var b = 0; b < file_ids[a].length; b++)
                if (wanted_ids.has(file_ids[a][b])) {
                    // let the next stage handle this to prevent dupes
                    //wanted_files.add(good_files[a]);

                    var m = /(.*)\.(mp4|webm|mkv|flv|opus|ogg|mp3|m4a|aac)$/i.exec(name);
                    if (!m)
                        continue;

                    var [rd, fn] = vsplit(m[1]);

                    if (fn in wanted_names_scoped)
                        wanted_names_scoped[fn].push(rd);
                    else
                        wanted_names_scoped[fn] = [rd];

                    wanted_names.add(fn);
                    name_id[m[1]] = file_ids[a][b];

                    break;
                }
        }

        // add all files with the same basename as each explicitly wanted file
        // (infojson/chatlog/etc when ID was discovered from metadata)
        for (var a = 0; a < good_files.length; a++) {
            var [rd, name] = vsplit(good_files[a][1]);
            for (var b = 0; b < 3; b++) {
                name = name.replace(/\.[^\.]+$/, '');
                if (!wanted_names.has(name))
                    continue;

                var vid_fp = false;
                for (var c of wanted_names_scoped[name])
                    if (rd.startsWith(c))
                        vid_fp = c + name;

                if (!vid_fp)
                    continue;

                var subdir = name_id[vid_fp];
                subdir = `v${subdir.slice(0, 1)}/${subdir}-${myid}`;
                var newpath = subdir + '/' + good_files[a][1].split(/\//g).pop();

                // check if this file is a dupe
                for (var c of good_files)
                    if (c[1] == newpath)
                        newpath = null;

                if (!newpath)
                    break;

                good_files[a][1] = newpath;
                wanted_files.add(good_files[a]);
                break;
            }
        }

        function upload_filtered() {
            if (!wanted_files.size)
                return modal.alert('Good news -- turns out we already have all those.\n\nBut thank you for checking in!');

            hooks[0](Array.from(wanted_files), nil_files, bad_files, hooks.slice(1));
        }

        function upload_all() {
            hooks[0](good_files, nil_files, bad_files, hooks.slice(1));
        }

        var n_skip = good_files.length - wanted_files.size,
            msg = `you added ${good_files.length} files; ${good_files.length == n_skip ? 'all' : n_skip} of them were skipped --\neither because we already have them,\nor because there is no youtube-ID in your filenames.\n\n<code>OK</code> / <code>Enter</code> = continue uploading just the ${wanted_files.size} files we definitely need\n\n<code>Cancel</code> / <code>ESC</code> = override the filter; upload ALL the files you added`;

        if (!n_skip)
            upload_filtered();
        else
            modal.confirm(msg, upload_filtered, upload_all);
    };
}

up2k_hooks.push(function () {
    up2k.gotallfiles.unshift(up2k_namefilter);
});

// persist/restore nickname field if present
setInterval(function () {
    var o = ebi('unick');
    if (!o || document.activeElement == o)
        return;

    o.oninput = function () {
        localStorage.setItem('unick', o.value);
    };
    o.value = localStorage.getItem('unick') || '';
}, 1000);
