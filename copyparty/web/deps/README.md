this folder *mostly* contains third-party dependencies; run `make -C scripts/deps-docker` to build the following files and have them appear here:

* `easymde.css.gz` and `easymde.js.gz` is the fancy markdown editor, [EasyMDE](https://github.com/Ionaru/easy-markdown-editor)
* `marked.js.gz` is the markdown rendering library [Marked](https://github.com/markedjs/marked)
* `mini-fa.css.gz` and `mini-fa.woff` is a small subset of [fontawesome](https://github.com/FortAwesome/Font-Awesome)
* `prism.css.gz` and `prism.js.gz` is the syntax highlighter [PrismJS](https://prismjs.com/)
* `scp.woff2` is a subset of the monospace font [Source Code Pro](https://github.com/adobe-fonts/source-code-pro)
* `sha512.hw.js.gz` is the Wasm sha512 library [hash-wasm](https://github.com/Daninet/hash-wasm)

additionally, the following files are vendored into the copyparty git repository, but do NOT originate from the copyparty project (as mentioned in `--license`):

* `sha512.ac.js.gz` is a compiled and slightly golfed/modified [asmcrypto.js](https://github.com/asmcrypto/asmcrypto.js), © 2013 Artem S Vybornov (MIT-Licensed)
  * vendored because it no longer builds with modern versions of NodeJS/npm
  * is only loaded by *really old* webbrowsers (ie11, firefox 51, chrome 56)

finally, there is also the following files which *does* originate from the copyparty project, yet appear here for technical reasons:

* `busy.mp3.gz` is a short mp3-file to make iphones stop glitching out
