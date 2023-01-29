standalone programs which are executed by copyparty when an event happens (upload, file rename, delete, ...)

these programs either take zero arguments, or a filepath (the affected file), or a json message with filepath + additional info

> **note:** in addition to event hooks (the stuff described here), copyparty has another api to run your programs/scripts while providing way more information such as audio tags / video codecs / etc and optionally daisychaining data between scripts in a processing pipeline; if that's what you want then see [mtp plugins](../mtag/) instead


# after upload
* [notify.py](notify.py) shows a desktop notification ([example](https://user-images.githubusercontent.com/241032/215335767-9c91ed24-d36e-4b6b-9766-fb95d12d163f.png))
* [discord-announce.py](discord-announce.py) announces new uploads on discord using webhooks ([example](https://user-images.githubusercontent.com/241032/215304439-1c1cb3c8-ec6f-4c17-9f27-81f969b1811a.png))
* [reject-mimetype.py](reject-mimetype.py) rejects uploads unless the mimetype is acceptable


# before upload
* [reject-extension.py](reject-extension.py) rejects uploads if they match a list of file extensions


# on message
* [wget.py](wget.py) lets you download files by POSTing URLs to copyparty
