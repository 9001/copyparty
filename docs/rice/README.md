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

and because textboxes don't inherit fonts by default, you can force it like this:

```css
input[type=text], input[type=submit], input[type=button] { font-family: var(--font-main) }
```

and if you want to have a monospace font in the fancy markdown editor, do this:

```css
.EasyMDEContainer .CodeMirror { font-family: var(--font-mono) }
```

NB: `<textarea id="mt">` and `<div id="mtr">` in the regular markdown editor must have the same font; none of the suggestions above will cause any issues but keep it in mind if you're getting creative


# `<head>`

to add stuff to the html `<head>`, for example a css `<link>` or `<meta>` tags, use either the global-option `--html-head` or the volflag `html_head`

if you give it the value `@ASDF` it will try to open a file named ASDF and send the text within

if the value starts with `%` it will assume a jinja2 template and expand it; the template has access to the `HttpCli` object through a property named `this` as well as everything in `j2a` and the stuff added by `self.j2s`; see [browser.html](https://github.com/9001/copyparty/blob/hovudstraum/copyparty/web/browser.html) for inspiration or look under the hood in [httpcli.py](https://github.com/9001/copyparty/blob/hovudstraum/copyparty/httpcli.py)


# translations

add your own translations by using the english or norwegian one from `browser.js` as a template

the easy way is to open up and modify `browser.js` in your own installation; depending on how you installed copyparty it might be named `browser.js.gz` instead, in which case just decompress it, restart copyparty, and start editing it anyways

if you're running `copyparty-sfx.py` then you'll find it at `/tmp/pe-copyparty.1000/copyparty/web` (on linux) or `%TEMP%\pe-copyparty\copyparty\web` (on windows)
* make sure to keep backups of your work religiously! since that location is volatile af

if editing `browser.js` is inconvenient in your setup then you can instead do this:
* add your translation to a separate javascript file (`tl.js`) and make it load before `browser.js` with the help of `--html-head='<script src="/tl.js"></script>'`
* as the page loads, `browser.js` will look for a function named `langmod` so define that function and make it insert your translation into the `Ls` and `LANGS` variables so it'll take effect
