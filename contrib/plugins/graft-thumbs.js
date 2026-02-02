// USAGE:
//   place this file somewhere in the webroot and then
//   python3 -m copyparty --js-browser /.res/graft-thumbs.js
//
// DESCRIPTION:
//   this is a gridview plugin which, for each file in a folder,
//   looks for another file with the same filename (but with a
//   different file extension)
//
//   if one of those files is an image and the other is not,
//   then this plugin assumes the image is a "sidecar thumbnail"
//   for the other file, and it will graft the image thumbnail
//   onto the non-image file (for example an mp3)
//
//   optional feature 1, default-enabled:
//   the image-file is then hidden from the directory listing
//
//   optional feature 2, default-enabled:
//   when clicking the audio file, the image will also open


(function() {

	// `graft_thumbs` assumes the gridview has just been rendered;
	// it looks for sidecars, and transplants those thumbnails onto
	// the other file with the same basename (filename sans extension)

	var graft_thumbs = function () {
		if (!thegrid.en)
			return;  // not in grid mode

		var files = msel.getall(),
			pairs = {};

		console.log(files);

		for (var a = 0; a < files.length; a++) {
			var file = files[a],
				is_pic = /\.(jpe?g|png|gif|webp|jxl)$/i.exec(file.vp),
				is_audio = re_au_all.exec(file.vp),
				basename = file.vp.replace(/\.[^\.]+$/, ""),
				entry = pairs[basename];

			if (!entry)
				// first time seeing this basename; create a new entry in pairs
				entry = pairs[basename] = {};

			if (is_pic)
				entry.thumb = file;
			else if (is_audio)
				entry.audio = file;
		}

		var basenames = Object.keys(pairs);
		for (var a = 0; a < basenames.length; a++)
			(function(a) {
				var pair = pairs[basenames[a]];

				if (!pair.thumb || !pair.audio)
					return;  // not a matching pair of files

				var img_thumb = QS('#ggrid a[ref="' + pair.thumb.id + '"] img[onload]'),
					img_audio = QS('#ggrid a[ref="' + pair.audio.id + '"] img[onload]');

				if (!img_thumb || !img_audio)
					return;  // something's wrong... let's bail

				// alright, graft the thumb...
				img_audio.src = img_thumb.src;

				// ...and hide the sidecar
				img_thumb.closest('a').style.display = 'none';

				// ...and add another onclick-handler to the audio,
				// so it also opens the pic while playing the song
				img_audio.addEventListener('click', function() {
					img_thumb.click();
					return false;  // let it bubble to the next listener
				});

			})(a);
	};

	// ...and then the trick! near the end of loadgrid,
	// thegrid.bagit is called to initialize the baguettebox
	// (image/video gallery); this is the perfect function to
	// "hook" (hijack) so we can run our code :^)

	// need to grab a backup of the original function first,
	var orig_func = thegrid.bagit;

	// and then replace it with our own:
	thegrid.bagit = function (isrc) {

		if (isrc !== '#ggrid')
			// we only want to modify the grid, so
			// let the original function handle this one
			return orig_func(isrc);

		graft_thumbs();

		// when changing directories, the grid is
		// rendered before msel returns the correct
		// filenames, so schedule another run:
		setTimeout(graft_thumbs, 1);

		// and finally, call the original thegrid.bagit function
		return orig_func(isrc);
	};

	if (ls0) {
		// the server included an initial listing json (ls0),
		// so the grid has already been rendered without our hook
		graft_thumbs();
	}

})();
