#!/bin/bash
set -e

# imagemagick png compression is broken, use pillow instead
convert ~/AndroidStudioProjects/PartyUP/metadata/en-US/images/icon.png a.bmp

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

python3 <<'EOF'
from PIL import Image
Image.open('a.png').save('loader.ico',sizes=[(48,48)])
EOF

rm a.{bmp,png}
ls -al
exit 0
