## chattyparty

this file, combined with the [msg-log](https://github.com/9001/copyparty/blob/hovudstraum/bin/hooks/msg-log.py) hook, turns copyparty into a makeshift instant-messaging / chat service

name this file `README.md` and run copyparty as such:
```bash
python copyparty-sfx.py -emp --xm j,bin/hooks/msg-log.py
```

only the stuff below is important; delete everything from this line up

```copyparty_post
render2(dom) {
 if (/[?&]edit/.test(location)) return;
 setTimeout(function() { treectl.goto(); }, 1000);
 // if you wanna go to another folder: treectl.goto('foo <bar> baz/', true);
}
```
