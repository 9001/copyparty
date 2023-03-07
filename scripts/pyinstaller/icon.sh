#!/bin/bash
set -e

genico() {

# imagemagick png compression is broken, use pillow instead
convert $1 a.bmp

#convert a.bmp -trim -resize '48x48!' -strip a.png
python3 <<'EOF'
from PIL import Image
i = Image.open('a.bmp')
i = i.crop(i.getbbox())
i = i.resize((48,48), Image.BICUBIC)
i = Image.alpha_composite(i,i)
i.save('a.png')
EOF

pngquant --strip --quality 30 a.png
mv a-*.png a.png

python3 <<EOF
from PIL import Image
Image.open('a.png').save('$2',sizes=[(48,48)])
EOF

rm a.{bmp,png}
}


genico ~/AndroidStudioProjects/PartyUP/metadata/en-US/images/icon.png loader.ico
genico https://raw.githubusercontent.com/googlefonts/noto-emoji/main/png/512/emoji_u1f680.png up2k.ico
ls -al
