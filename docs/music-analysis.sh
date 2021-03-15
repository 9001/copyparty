#!/bin/bash
echo please dont actually run this as a scriopt
exit 1


# dependency-heavy, not particularly good fit
pacman -S llvm10
python3 -m pip install --user librosa
git clone https://github.com/librosa/librosa.git


# afun host, collects/grades the results
runfun() { cores=8; touch run; rm -f /dev/shm/mres.*; t00=$(date +%s); tbc() { bc | sed -r 's/(\.[0-9]{2}).*/\1/'; }; for ((core=0; core<$cores; core++)); do sqlite3 /mnt/Users/ed/Music/.hist/up2k.db 'select dur.w, dur.v, bpm.v from mt bpm join mt dur on bpm.w = dur.w where bpm.k = ".bpm" and dur.k = ".dur" order by dur.w' | uniq -w16 | while IFS=\| read w dur bpm; do sqlite3 /mnt/Users/ed/Music/.hist/up2k.db "select rd, fn from up where substr(w,1,16) = '$w'" | sed -r "s/^/$bpm /"; done | grep mir/cr | tr \| / | while read bpm fn; do [ -e run ] || break; n=$((n+1)); ncore=$((n%cores)); [ $ncore -eq $core ] || continue; t0=$(date +%s.%N); (afun || exit 1; t=$(date +%s.%N); td=$(echo "scale=3; $t - $t0" | tbc); bd=$(echo "scale=3; $bpm / $py" | tbc); printf '%4s sec, %4s orig, %6s py, %4s div, %s\n' $td $bpm $py $bd "$fn") | tee -a /dev/shm/mres.$ncore; rv=${PIPESTATUS[0]}; [ $rv -eq 0 ] || { echo "FAULT($rv): $fn"; }; done & done; wait 2>/dev/null; cat /dev/shm/mres.* | awk '$8!="div,"{next} $5!~/^[0-9\.]+/{next} 1;{meta=$3;det=$5;div=meta/det} div<0.7{det/=2} div>1.3{det*=2} {idet=sprintf("%.0f",det)} {idiff=idet-meta} meta>idet{idiff=meta-idet} idiff==0{n0++;next} idiff==1{n1++;next} idiff>10{nx++;next} {n10++} END {printf "ok: %d   1off: %d   10off: %d   fail: %d\n",n0,n1,n10,nx}'; te=$(date +%s); echo $((te-t00)) sec spent; }


# ok:   4   1off: 59   10off: 65   fail: 53   # 105 sec,  librosa @ 8c archvm on 3700x w10
afun() { ffmpeg -hide_banner -v fatal -nostdin -ss $((dur/3)) -y -i /mnt/Users/ed/Music/"$fn" -t 60 /dev/shm/$core.wav || return 1; py="$(/home/ed/src/librosa/examples/beat_tracker.py /dev/shm/$core.wav x 2>&1 | awk 'BEGIN {v=1} /^Estimated tempo: /{v=$3} END {print v}')"; }


# ok: 109   1off:  4   10off:  9   fail: 59   # 51 sec,  vamp-example-fixedtempo
afun() { ffmpeg -hide_banner -v fatal -nostdin -ss $((dur/3)) -y -i /mnt/Users/ed/Music/"$fn" -ac 1 -ar 22050 -f f32le /dev/shm/$core.pcm || return 1; py="$(python3 -c 'import vamp; import numpy as np; f = open("/dev/shm/'$core'.pcm", "rb"); d = np.fromfile(f, dtype=np.float32); c = vamp.collect(d, 22050, "vamp-example-plugins:fixedtempo", parameters={"maxdflen":40}); print(c["list"][0]["label"].split(" ")[0])')"; }


# ok:  80   1off: 48   10off: 11   fail: 42   # 61 sec,  vamp-qm-tempotracker
afun() { ffmpeg -hide_banner -v fatal -nostdin -ss $((dur/3)) -y -i /mnt/Users/ed/Music/"$fn" -ac 1 -ar 22050 -f f32le /dev/shm/$core.pcm || return 1; py="$(python3 -c 'import vamp; import numpy as np; f = open("/dev/shm/'$core'.pcm", "rb"); d = np.fromfile(f, dtype=np.float32); c = vamp.collect(d, 22050, "qm-vamp-plugins:qm-tempotracker", parameters={"inputtempo":150}); v = [float(x["label"].split(" ")[0]) for x in c["list"] if x["label"]]; v = list(sorted(v))[len(v)//4:-len(v)//4]; print(round(sum(v) / len(v), 1))')"; }


# ok: 101   1off: 22   10off: 16   fail: 39   # 51 sec,  vamp-beatroot
# note: some tracks fully fail to analyze (unlike the others which always provide a guess)
afun() { ffmpeg -hide_banner -v fatal -nostdin -ss $((dur/3)) -y -i /mnt/Users/ed/Music/"$fn" -ac 1 -ar 22050 -f f32le /dev/shm/$core.pcm || return 1; py="$(python3 -c 'import vamp; import numpy as np; f = open("/dev/shm/'$core'.pcm", "rb"); d = np.fromfile(f, dtype=np.float32); c = vamp.collect(d, 22050, "beatroot-vamp:beatroot"); cl=c["list"]; print(round(60*((len(cl)-1)/(float(cl[-1]["timestamp"]-cl[1]["timestamp"]))), 2))')"; }



########################################################################
##
##  key detectyion
##
########################################################################



# console scriptlet reusing keytabs from browser.js
var m=''; for (var a=0; a<24; a++) m += 's/\\|(' + maps["traktor_sharps"][a].trim() + "|" + maps["rekobo_classic"][a].trim() + "|" + maps["traktor_musical"][a].trim() + "|" + maps["traktor_open"][a].trim() + ')$/|' + maps["rekobo_alnum"][a].trim() + '/;'; console.log(m);


# translate to camelot
re='s/\|(B|B|B|6d)$/|1B/;s/\|(F#|F#|Gb|7d)$/|2B/;s/\|(C#|Db|Db|8d)$/|3B/;s/\|(G#|Ab|Ab|9d)$/|4B/;s/\|(D#|Eb|Eb|10d)$/|5B/;s/\|(A#|Bb|Bb|11d)$/|6B/;s/\|(F|F|F|12d)$/|7B/;s/\|(C|C|C|1d)$/|8B/;s/\|(G|G|G|2d)$/|9B/;s/\|(D|D|D|3d)$/|10B/;s/\|(A|A|A|4d)$/|11B/;s/\|(E|E|E|5d)$/|12B/;s/\|(G#m|Abm|Abm|6m)$/|1A/;s/\|(D#m|Ebm|Ebm|7m)$/|2A/;s/\|(A#m|Bbm|Bbm|8m)$/|3A/;s/\|(Fm|Fm|Fm|9m)$/|4A/;s/\|(Cm|Cm|Cm|10m)$/|5A/;s/\|(Gm|Gm|Gm|11m)$/|6A/;s/\|(Dm|Dm|Dm|12m)$/|7A/;s/\|(Am|Am|Am|1m)$/|8A/;s/\|(Em|Em|Em|2m)$/|9A/;s/\|(Bm|Bm|Bm|3m)$/|10A/;s/\|(F#m|F#m|Gbm|4m)$/|11A/;s/\|(C#m|Dbm|Dbm|5m)$/|12A/;'


# ok: 26   1off: 10   2off: 1   fail: 3   #  15 sec, keyfinder
cores=8; touch run; tbc() { bc | sed -r 's/(\.[0-9]{2}).*/\1/'; }; for ((core=0; core<$cores; core++)); do sqlite3 /mnt/Users/ed/Music/.hist/up2k.db 'select dur.w, dur.v, key.v from mt key join mt dur on key.w = dur.w where key.k = "key" and dur.k = ".dur" order by dur.w' | uniq -w16 | grep -vE '(Off-Key|None)$' | sed -r "s/ //g;$re" | uniq -w16 | while IFS=\| read w dur bpm; do sqlite3 /mnt/Users/ed/Music/.hist/up2k.db "select rd, fn from up where substr(w,1,16) = '$w'" | sed -r "s/^/$bpm /"; done| grep mir/cr | tr \| / | while read key fn; do [ -e run ] || break; n=$((n+1)); ncore=$((n%cores)); [ $ncore -eq $core ] || continue; ffmpeg -hide_banner -v fatal -nostdin -ss $((dur/3)) -y -i /mnt/Users/ed/Music/"$fn" -ac 1 -ar 44100 -t 60 /dev/shm/$core.wav || break; t0=$(date +%s.%N); py="$(python3 -c 'import sys; import keyfinder; print(keyfinder.key(sys.argv[1]).camelot())' "/dev/shm/$core.wav")"; t=$(date +%s.%N); td=$(echo "scale=3; $t - $t0" | tbc); [ "$key" = "$py" ] && c=2 || c=5; printf '%4s sec, %4s orig, \033[3%dm%4s py,\033[0m %s\n' $td "$key" $c "$py" "$fn"; done & done; time wait 2>/dev/null



########################################################################
##
##  misc
##
########################################################################



python3 -m pip install --user vamp

import librosa
d, r = librosa.load('/dev/shm/0.wav')
d.dtype
# dtype('float32')
d.shape
# (1323000,)
d
# array([-1.9614939e-08,  1.8037968e-08, -1.4106059e-08, ...,
#         1.2024145e-01,  2.7462116e-01,  1.6202132e-01], dtype=float32)



import vamp
c = vamp.collect(d, r, "vamp-example-plugins:fixedtempo")
c
# {'list': [{'timestamp':  0.005804988, 'duration':  9.999092971, 'label': '110.0 bpm', 'values': array([109.98116], dtype=float32)}]}



ffmpeg -ss 48 -i /mnt/Users/ed/Music/mir/cr-a/'I Beg You(ths Bootleg).wav' -ac 1 -ar 22050 -f f32le -t 60 /dev/shm/f32.pcm

import numpy as np
f = open('/dev/shm/f32.pcm', 'rb')
d = np.fromfile(f, dtype=np.float32)
d
array([-0.17803933, -0.27206388, -0.41586545, ..., -0.04940119,
       -0.0267825 , -0.03564296], dtype=float32)

d = np.reshape(d, [1, -1])
d
array([[-0.17803933, -0.27206388, -0.41586545, ..., -0.04940119,
        -0.0267825 , -0.03564296]], dtype=float32)



import vampyhost
print("\n".join(vampyhost.list_plugins()))

mvamp:marsyas_bextract_centroid
mvamp:marsyas_bextract_lpcc
mvamp:marsyas_bextract_lsp
mvamp:marsyas_bextract_mfcc
mvamp:marsyas_bextract_rolloff
mvamp:marsyas_bextract_scf
mvamp:marsyas_bextract_sfm
mvamp:marsyas_bextract_zero_crossings
mvamp:marsyas_ibt
mvamp:zerocrossing
qm-vamp-plugins:qm-adaptivespectrogram
qm-vamp-plugins:qm-barbeattracker
qm-vamp-plugins:qm-chromagram
qm-vamp-plugins:qm-constantq
qm-vamp-plugins:qm-dwt
qm-vamp-plugins:qm-keydetector
qm-vamp-plugins:qm-mfcc
qm-vamp-plugins:qm-onsetdetector
qm-vamp-plugins:qm-segmenter
qm-vamp-plugins:qm-similarity
qm-vamp-plugins:qm-tempotracker
qm-vamp-plugins:qm-tonalchange
qm-vamp-plugins:qm-transcription
vamp-aubio:aubiomelenergy
vamp-aubio:aubiomfcc
vamp-aubio:aubionotes
vamp-aubio:aubioonset
vamp-aubio:aubiopitch
vamp-aubio:aubiosilence
vamp-aubio:aubiospecdesc
vamp-aubio:aubiotempo
vamp-example-plugins:amplitudefollower
vamp-example-plugins:fixedtempo
vamp-example-plugins:percussiononsets
vamp-example-plugins:powerspectrum
vamp-example-plugins:spectralcentroid
vamp-example-plugins:zerocrossing
vamp-rubberband:rubberband



plug = vampyhost.load_plugin("vamp-example-plugins:fixedtempo", 22050, 0)
plug.info
{'apiVersion': 2, 'pluginVersion': 1, 'identifier': 'fixedtempo', 'name': 'Simple Fixed Tempo Estimator', 'description': 'Study a short section of audio and estimate its tempo, assuming the tempo is constant', 'maker': 'Vamp SDK Example Plugins', 'copyright': 'Code copyright 2008 Queen Mary, University of London.  Freely redistributable (BSD license)'}
plug = vampyhost.load_plugin("qm-vamp-plugins:qm-tempotracker", 22050, 0)
from pprint import pprint; pprint(plug.parameters)



for c in plug.parameters: print("{} \033[36m{}  [\033[33m{}\033[36m] = {}\033[0m".format(c["identifier"], c["name"], "\033[36m, \033[33m".join(c["valueNames"]), c["valueNames"][int(c["defaultValue"])])) if "valueNames" in c else print("{} \033[36m{}  [\033[33m{}..{}\033[36m] = {}\033[0m".format(c["identifier"], c["name"], c["minValue"], c["maxValue"], c["defaultValue"]))



beatroot-vamp:beatroot
cl=c["list"]; 60*((len(cl)-1)/(float(cl[-1]["timestamp"]-cl[1]["timestamp"])))



ffmpeg -ss 48 -i /mnt/Users/ed/Music/mir/cr-a/'I Beg You(ths Bootleg).wav' -ac 1 -ar 22050 -f f32le -t 60 /dev/shm/f32.pcm
# 128 bpm, key 5A Cm

import vamp
import numpy as np
f = open('/dev/shm/f32.pcm', 'rb')
d = np.fromfile(f, dtype=np.float32)
c = vamp.collect(d, 22050, "vamp-example-plugins:fixedtempo", parameters={"maxdflen":40})
c["list"][0]["label"]
# 127.6 bpm

c = vamp.collect(d, 22050, "qm-vamp-plugins:qm-tempotracker", parameters={"inputtempo":150})
print("\n".join([v["label"] for v in c["list"] if v["label"]]))
v = [float(x["label"].split(' ')[0]) for x in c["list"] if x["label"]]
v = list(sorted(v))[len(v)//4:-len(v)//4]
v = sum(v) / len(v)
# 128.1 bpm

