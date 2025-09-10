#!/bin/bash
#
# this script will install copyparty onto an iOS device (iPhone/iPad)
#
# step 1: install a-Shell:
#   https://apps.apple.com/us/app/a-shell/id1473805438
#
# step 2: copypaste the following command into a-Shell:
#   curl https://github.com/9001/copyparty/raw/refs/heads/hovudstraum/contrib/setup-ashell.sh
#
# step 3: launch copyparty with this command: cpp
#
# if you ever want to upgrade copyparty, just repeat step 2



cd "$HOME/Documents"
curl -Locopyparty https://github.com/9001/copyparty/releases/latest/download/copyparty-sfx.py



# create the config file? (cannot use heredoc because body too large)
[ -e cpc ] || {
echo '[global]' >cpc
echo '  p: 80, 443, 3923  # enable http and https on these ports' >>cpc
echo '  e2dsa      # enable file indexing and filesystem scanning' >>cpc
echo '  e2ts       # and enable multimedia indexing' >>cpc
echo '  ver        # show copyparty version in the controlpanel' >>cpc
echo '  qrz: 2     # enable qr-code and make it big' >>cpc
echo '  qrp: 1     # reduce qr-code padding' >>cpc
echo '  qr-fg: -1  # optimize for basic/simple terminals' >>cpc
echo '  qr-wait: 0.3  # less chance of getting scrolled away' >>cpc
echo '' >>cpc
echo '  # enable these by uncommenting them:' >>cpc
echo '  # ftp: 21    # enable ftp server on port 21' >>cpc
echo '  # tftp: 69   # enable tftp server on port 69' >>cpc
echo '' >>cpc
echo '[/]' >>cpc
echo '  ~/Documents' >>cpc
echo '  accs:' >>cpc
echo '    A: *' >>cpc
}



# create the launcher?
[ -e cpp ] || {
echo '#!/bin/sh' >cpp
echo '' >>cpp
echo '# change the font so the qr-code draws correctly:' >>cpp
echo 'config -n "Menlo"  # name' >>cpp
echo 'config -s 8  # size' >>cpp
echo '' >>cpp
echo '# launch copyparty' >>cpp
echo 'exec copyparty -c cpc "$@"' >>cpp
}



chmod 755 copyparty cpp
echo
echo =================================
echo
echo 'okay, all done!'
echo
echo 'you can edit your config'
echo 'with this command: vim cpc'
echo
echo 'you can run copyparty'
echo 'with this command: cpp'
echo
