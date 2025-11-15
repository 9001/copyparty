# hide ui-elements

useful for simplifying the UI in a write-only folder for uploads, or to embed copyparty into another website in an `<iframe>` or similar

| url-param | volflag | what it hides |
| --------- | ------- | ------------- |
| [nombar](https://a.ocv.me/pub/demo/?nombar) | ui_nombar | the menu-bar at the top |
| [noacci](https://a.ocv.me/pub/demo/?noacci) | ui_noacci | permissions-list and logout-button |
| [nosrvi](https://a.ocv.me/pub/demo/?nosrvi) | ui_nosrvi | server-info (name, disk usage) |
| [notree](https://a.ocv.me/pub/demo/?notree) | ui_notree | the navpane sidebar |
| [nonav](https://a.ocv.me/pub/demo/?nonav)   | ui_nonav  | `notree` + breadcrumbs |
| [nocpla](https://a.ocv.me/pub/demo/?nocpla) | ui_nocpla | link to controlpanel |
| [nolbar](https://a.ocv.me/pub/demo/?nolbar) | ui_nolbar | `nocpla` + "prev/up/next" |
| [noctxb](https://a.ocv.me/pub/demo/?noctxb) | ui_noctxb | tray-toggle / context-buttons |
| [norepl](https://a.ocv.me/pub/demo/?norepl) | ui_norepl | the `π` repl button |

can be combined; https://a.ocv.me/pub/demo/?nombar&noacci&nosrvi&nonav&nolbar&noctxb&norepl

all options can be overruled with url-param `fullui`; https://a.ocv.me/pub/demo/?fullui


# custom fonts

to change the fonts in the web-UI,  first save the following text (the default font-config) to a new css file, for example named `customfonts.css` in your webroot:

```css
:root {
	--font-main: sans-serif;
	--font-serif: serif;
	--font-mono: 'scp';
}
```

add this to your copyparty config so the css file gets loaded: `--html-head='<link rel="stylesheet" href="/customfonts.css">'`

alternatively, if you are using a config file instead of commandline args:

```yaml
[global]
  html-head: <link rel="stylesheet" href="/customfonts.css">
```

restart copyparty for the config change to take effect

edit the css file you made and press `ctrl`-`shift`-`R` in the browser to see the changes as you go (no need to restart copyparty for each change)

if you are introducing a new ttf/woff font, don't forget to declare the font itself in the css file; here's one of the default fonts from `ui.css`:

```css
@font-face {
	font-family: 'scp';
	font-display: swap;
	src: local('Source Code Pro Regular'), local('SourceCodePro-Regular'), url(deps/scp.woff2) format('woff2');
}
```

and if you want to have a monospace font in the fancy markdown editor, do this:

```css
.EasyMDEContainer .CodeMirror { font-family: var(--font-mono) }
```

NB: `<textarea id="mt">` and `<div id="mtr">` in the regular markdown editor must have the same font; none of the suggestions above will cause any issues but keep it in mind if you're getting creative


# boring loader spinner

replace the 🌲 with a spinning circle using commandline args:

`--spinner ',padding:0;border-radius:9em;border:.2em solid #444;border-top:.2em solid #fc0'`

or config file example:

```yaml
[global]
  spinner: ,padding:0;border-radius:9em;border:.2em solid #444;border-top:.2em solid #fc0
```


# `<head>`

to add stuff to the html `<head>`, for example a css `<link>` or `<meta>` tags, use either the global-option `--html-head` or the volflag `html_head`

if you give it the value `@ASDF` it will try to open a file named ASDF and send the text within

if the value starts with `%` it will assume a jinja2 template and expand it; the template has access to the `HttpCli` object through a property named `this` as well as everything in `j2a` and the stuff added by `self.j2s`; see [browser.html](https://github.com/9001/copyparty/blob/hovudstraum/copyparty/web/browser.html) for inspiration or look under the hood in [httpcli.py](https://github.com/9001/copyparty/blob/hovudstraum/copyparty/httpcli.py)

there is also `--html-head-s` and volflag `html_head_s` to add a plain static bit of text, possibly in addition to `--html-head`


# translations

add your own translations by using [tl.js](https://github.com/9001/copyparty/blob/hovudstraum/scripts/tl.js) as a base, and add a new file in [copyparty/web/tl](https://github.com/9001/copyparty/tree/hovudstraum/copyparty/web/tl) when you're happy with it

> ⚠ Please do not contribute translations to [RTL (Right-to-Left) languages](https://en.wikipedia.org/wiki/Right-to-left_script) for now; the javascript is [not ready](https://github.com/9001/copyparty/blob/hovudstraum/docs/rice/rtl.patch) to deal with it

you will be delighted to see inline html in the translation strings; to help prevent syntax errors, there is [a very jank linux script](https://github.com/9001/copyparty/blob/hovudstraum/scripts/tlcheck.sh) which is slightly better than nothing -- just beware the false-positives, so even if it complains it's not necessarily wrong/bad

to see your translation taking shape in the copyparty ui as you work on it:
* put your `tl.js` inside a folder that is being shared by your copyparty, preferably the webroot
* run copyparty with the argument `--html-head='<script src="/tl.js"></script>'`
  * if you placed `tl.js` in the webroot then you're all good, but if you put it somewhere else then change `/tl.js` accordingly
  * if you are running copyparty with config files, you can do this:
    ```yaml
	[global]
	  html-head: <script src="/tl.js"></script>
	```

you can now edit `tl.js` and press CTRL-SHIFT-R in the browser to see your changes take effect as you go

if you want to contribute your translation back to the project (please do!) then grab most of the text inside your `tl.js` , starting from the line that starts with `Ls.` and put it into a new file inside [the translations folder](https://github.com/9001/copyparty/tree/hovudstraum/copyparty/web/tl)
