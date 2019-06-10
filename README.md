# ⇆🎉 copyparty

* http file sharing hub (py2/py3)
* MIT-Licensed, 2019-05-26, ed @ irc.rizon.net

## summary

turn your phone or raspi into a portable file server with resumable uploads/downloads using IE6 or any other browser

* server runs on anything with `py2.7` or `py3.3+`
* *resumable* uploads need `firefox 12+` / `chrome 6+` / `safari 6+` / `IE 10+`
* code standard: `black`

## status

* [x] sanic multipart parser
* [x] load balancer (multiprocessing)
* [ ] upload (plain multipart, ie6 support)
* [ ] upload (js, resumable, multithreaded)
* [x] download
* [x] browser
* [x] media player
* [ ] thumbnails
* [ ] download as zip
* [x] volumes
* [x] accounts

conclusion: mostly useless

## dependencies

* jinja2
  * markupsafe

## dev env
```
python3 -v venv .env
. .env/bin/activate
pip install jinja2  # dependencies
pip install black bandit pylint flake8  # vscode tooling
```

