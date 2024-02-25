# custom fonts

to change the fonts in the web-UI,  first create a css file with your customizations, for example `customfonts.css`, for example in your webroot

add this to your copyparty config so the css file gets loaded: `--html-head='<link rel="stylesheet" href="/customfonts.css">'`

alternatively, if you are using a config file instead of commandline args:

```yaml
[global]
  html-head: <link rel="stylesheet" href="/customfonts.css">
```

make your changes in the css file; this is the default values to get you started:

```css
:root {
	--font-main: sans-serif;
	--font-serif: serif;
	--font-mono: 'scp';
}
```

if you are introducing a new ttf/woff font, don't forget to declare the font itself in the css file; here's one of the default fonts from `ui.css`:

```css
@font-face {
	font-family: 'scp';
	font-display: swap;
	src: local('Source Code Pro Regular'), local('SourceCodePro-Regular'), url(deps/scp.woff2) format('woff2');
}
```
