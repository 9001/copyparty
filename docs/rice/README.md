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
