this is `/var/lib/copyparty-jail`, the fallback webroot when copyparty has not yet been configured

please edit `/etc/copyparty/copyparty.conf` (if running as a system service)
or `$HOME/.config/copyparty/copyparty.conf` if running as a user service

a basic configuration example is available at https://github.com/9001/copyparty/blob/hovudstraum/contrib/systemd/copyparty.example.conf
a configuration example that explains most flags is available at https://github.com/9001/copyparty/blob/hovudstraum/docs/chungus.conf

the full list of configuration options can be seen at https://ocv.me/copyparty/helptext.html 
or by running `copyparty --help`
