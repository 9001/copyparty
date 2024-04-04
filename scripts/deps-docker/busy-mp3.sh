#!/bin/bash
set -e

cat >/dev/null <<EOF
a frame is 1152 samples
1sec @ 48000 = 41.66 frames
11 frames = 12672 samples = 0.264 sec
22 frames = 25344 samples = 0.528 sec
EOF

fast=1
fast=

echo
cd /dev/shm
rm -f -- a.*.mp3 a.*.mp3.gz
min=99999999

for freq in 425; do  # {400..500}
for vol in 24; do  # {10..30}
for kbps in 32; do
for fdur in 1124; do  # {800..1200}
for fdu2 in 1042; do  # {800..1200}
for ftyp in h; do  # q h t l p
for ofs1 in 801; do  # {0..4096}
for ofs2 in 0; do  # {0..4096}
for ofs3 in 0; do  # {0..4096}
for nores in --nores; do  # '' --nores

f=a.b$kbps$nores-f$freq-v$vol-$ftyp$fdur-$fdu2-o$ofs1-$ofs2-$ofs3
sox -r48000 -Dn -r48000 -b16 -c2 -t raw s1.pcm synth 25344s sin $freq vol 0.$vol fade $ftyp ${fdur}s 25344s ${fdu2}s
sox -r48000 -Dn -r48000 -b16 -c2 -t raw s0.pcm synth 12672s sin $freq vol 0
tail -c +$ofs1 s0.pcm >s0a.pcm
tail -c +$ofs2 s0.pcm >s0b.pcm
tail -c +$ofs3 s0.pcm >s0c.pcm
cat s{0a,1,0,0b,1,0c}.pcm > a.pcm
lame --silent -r -s 48 --bitwidth 16 --signed a.pcm -m j --resample 48 -b $kbps -q 0 $nores $f.mp3
if [ $fast ]
then gzip -c <$f.mp3 >$f.mp3.gz
else pigz -c11 -I1 <$f.mp3 >$f.mp3.gz
fi
sz=$(wc -c <$f.mp3.gz)
printf '\033[A%d %s\033[K\n' $sz $f
[ $sz -le $((min+10)) ] && echo
[ $sz -le $min ] && echo && min=$sz

done;done;done;done;done;done;done;done;done;done
true

f=a.b32--nores-f425-v24-h1124-1042-o801-0-0.mp3
[ $fast ] &&
    pigz -c11 -I1 <$f >busy.mp3.gz ||
    mv $f.gz busy.mp3.gz

sz=$(wc -c <busy.mp3.gz)
[ "$sz" -eq 707 ] &&
    echo busy.mp3 built successfully ||
    echo WARNING: unexpected size of busy.mp3

rm -f a.*.mp3 a.*.mp3.gz
