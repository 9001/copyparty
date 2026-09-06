this is `/var/lib/copyparty-jail/srv/`, the fallback webroot when copyparty has not yet been configured

please edit the config-file and restart copyparty;
* if running as a system service: `vim /etc/copyparty.conf`
* if running as a user service: `vim $HOME/.config/copyparty/copyparty.conf`

some inspiration:
* a basic example config: https://github.com/9001/copyparty/blob/hovudstraum/contrib/systemd/copyparty.example.conf
* another example with focus on syntax: https://github.com/9001/copyparty/blob/hovudstraum/docs/example.conf
* and CTRL-F `config file example` here: https://github.com/9001/copyparty

the full list of configuration options can be seen at https://copyparty.eu/cli/ 
or by running `copyparty --help`
