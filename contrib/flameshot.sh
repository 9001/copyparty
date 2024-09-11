#!/bin/bash
set -e

# take a screenshot with flameshot and send it to copyparty;
# the image url will be placed on your clipboard

password=wark
url=https://a.ocv.me/up/
filename=$(date +%Y-%m%d-%H%M%S).png

flameshot gui -s -r |
curl -T- $url$filename?pw=$password |
tail -n 1 |
xsel -ib
