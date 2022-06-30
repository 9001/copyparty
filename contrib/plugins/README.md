# example resource files

can be provided to copyparty to tweak things



## example `.epilogue.html`
save one of these as `.epilogue.html` inside a folder to customize it:

* [`minimal-up2k.html`](minimal-up2k.html) will [simplify the upload ui](https://user-images.githubusercontent.com/241032/118311195-dd6ca380-b4ef-11eb-86f3-75a3ff2e1332.png)



## example browser-js
point `--js-browser` to one of these by URL:

* [`minimal-up2k.js`](minimal-up2k.js) is similar to the above `minimal-up2k.html` except it applies globally to all write-only folders



## example browser-css
point `--css-browser` to one of these by URL:

* [`browser-icons.css`](browser-icons.css) adds filetype icons



## meadup.js

* turns copyparty into chromecast just more flexible (and probably way more buggy)
* usage: put the js somewhere in the webroot and `--js-browser /memes/meadup.js`
