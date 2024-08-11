# example resource files

can be provided to copyparty to tweak things



## example `.epilogue.html`
save one of these as `.epilogue.html` inside a folder to customize it:

* [`minimal-up2k.html`](minimal-up2k.html) will [simplify the upload ui](https://user-images.githubusercontent.com/241032/118311195-dd6ca380-b4ef-11eb-86f3-75a3ff2e1332.png)



## example browser-js
point `--js-browser` to one of these by URL:

* [`minimal-up2k.js`](minimal-up2k.js) is similar to the above `minimal-up2k.html` except it applies globally to all write-only folders
* [`up2k-hooks.js`](up2k-hooks.js) lets you specify a ruleset for files to skip uploading
  * [`up2k-hook-ytid.js`](up2k-hook-ytid.js) is a more specific example checking youtube-IDs against some API



## example any-js
point `--js-browser` and/or `--js-other` to one of these by URL:

* [`banner.js`](banner.js) shows a very enterprise [legal-banner](https://github.com/user-attachments/assets/8ae8e087-b209-449c-b08d-74e040f0284b)



## example browser-css
point `--css-browser` to one of these by URL:

* [`browser-icons.css`](browser-icons.css) adds filetype icons



## meadup.js

* turns copyparty into chromecast just more flexible (and probably way more buggy)
* usage: put the js somewhere in the webroot and `--js-browser /memes/meadup.js`
