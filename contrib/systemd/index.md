this is `/var/lib/copyparty-jail`, the fallback webroot when copyparty has not yet been configured

please edit `/etc/copyparty/copyparty.conf` (if running as a system service)
or `$HOME/.config/copyparty/copyparty.conf` if running as a user service

* a basic example config: https://github.com/9001/copyparty/blob/hovudstraum/contrib/systemd/copyparty.example.conf
* another example with focus on syntax: https://github.com/9001/copyparty/blob/hovudstraum/docs/example.conf
* and CTRL-F "config file example" here: https://github.com/9001/copyparty

the full list of configuration options can be seen at https://copyparty.eu/cli/ 
or by running `copyparty --help`
