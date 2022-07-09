// hooks into up2k

function up2k_namefilter(good_files, nil_files, bad_files, hooks) {
    // is called when stuff is dropped into the browser,
    // after iterating through the directory tree and discovering all files,
    // before the upload confirmation dialogue is shown

    // good_files will successfully upload
    // nil_files are empty files and will show an alert in the final hook
    // bad_files are unreadable and cannot be uploaded
    var file_lists = [good_files, nil_files, bad_files];

    // build a list of filenames
    var filenames = [];
    for (var lst of file_lists)
        for (var ent of lst)
            filenames.push(ent[1]);

    toast.inf(5, "running database query...");

    // simulate delay while passing the list to some api for checking
    setTimeout(function () {

        // only keep webm files as an example
        var new_lists = [];
        for (var lst of file_lists) {
            var keep = [];
            new_lists.push(keep);

            for (var ent of lst)
                if (/\.webm$/.test(ent[1]))
                    keep.push(ent);
        }

        // finally, call the next hook in the chain
        [good_files, nil_files, bad_files] = new_lists;
        hooks[0](good_files, nil_files, bad_files, hooks.slice(1));

    }, 1000);
}

// register
up2k_hooks.push(function () {
    up2k.gotallfiles.unshift(up2k_namefilter);
});
