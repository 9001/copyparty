standalone programs which are executed by copyparty when an event happens (upload, file rename, delete, ...)

these programs either take zero arguments, or a filepath (the affected file), or a json message with filepath + additional info


# after upload
* [notify.py](notify.py) shows a desktop notification
* [discord-announce.py](discord-announce.py) announces new uploads on discord using webhooks
* [reject-mimetype.py](reject-mimetype.py) rejects uploads unless the mimetype is acceptable


# before upload
* [reject-extension.py](reject-extension.py) rejects uploads if they match a list of file extensions


# on message
* [wget.py](wget.py) lets you download files by POSTing URLs to copyparty
