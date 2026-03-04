#!/bin/ash
set -e

[ $1 = 1 ] && hub=1

uname -a
apk add alpine-sdk doas wget
echo permit nopass root > /etc/doas.d/u.conf
cp -pv /root/.abuild/*.pub /etc/apk/keys/ || abuild-keygen -ina

##
## yeet h265

mkdir /ffmpeg
cd /ffmpeg
base=https://github.com/alpinelinux/aports/raw/refs/heads/3.23-stable/community/ffmpeg/
wget ${base}APKBUILD
awk <APKBUILD -vb="$base" '/"/{o=0}/^source=/{o=1;next}o{print b $1}' | wget -i-
cp -pv APKBUILD /root/

# grep -E '^extern const.* FF[^ ]+ +ff_(hevc|vvc)_' libavcodec/allcodecs.c libavcodec/hwaccels.h libavcodec/bitstream_filters.c libavcodec/parsers.c libavformat/allformats.c | sed -r 's/.* ff_([^/;]*)_([^/;]*);.*/--disable-\2=\1/' | tr '\n' ' '
sed -ri 's/--enable-libx265/--disable-decoder=hevc --disable-decoder=hevc_qsv --disable-decoder=hevc_rkmpp --disable-encoder=hevc_rkmpp --disable-decoder=hevc_v4l2m2m --disable-decoder=vvc --disable-encoder=hevc_amf --disable-decoder=hevc_amf --disable-decoder=hevc_cuvid --disable-encoder=hevc_d3d12va --disable-decoder=hevc_mediacodec --disable-encoder=hevc_mediacodec --disable-encoder=hevc_mf --disable-encoder=hevc_nvenc --disable-decoder=hevc_oh --disable-encoder=hevc_oh --disable-encoder=hevc_qsv --disable-encoder=hevc_v4l2m2m --disable-encoder=hevc_vaapi --disable-encoder=hevc_videotoolbox --disable-encoder=hevc_vulkan --disable-decoder=vvc_qsv --disable-hwaccel=hevc_d3d11va --disable-hwaccel=hevc_d3d11va2 --disable-hwaccel=hevc_d3d12va --disable-hwaccel=hevc_dxva2 --disable-hwaccel=hevc_nvdec --disable-hwaccel=hevc_vaapi --disable-hwaccel=hevc_vdpau --disable-hwaccel=hevc_videotoolbox --disable-hwaccel=hevc_vulkan --disable-hwaccel=vvc_vaapi --disable-bsf=hevc_metadata --disable-bsf=hevc_mp4toannexb --disable-bsf=vvc_metadata --disable-bsf=vvc_mp4toannexb --disable-parser=hevc --disable-parser=vvc --disable-demuxer=hevc --disable-muxer=hevc --disable-demuxer=vvc --disable-muxer=vvc /;s/\bx265-dev\b//' APKBUILD

##
## yeet aac he/he+/ld (sbr/ps); keep lc only

cat >>APKBUILD <<'EOF'
prepare() {
    default_prepare
    tar -cC/opt/patch/ffmpeg . | tar -x
    patch -p1 <aac-lc-only.patch
}
EOF

##
## shrink-ray

sed -ri 's/--enable-lib(bluray|placebo|rav1e|shaderc)/--disable-lib\1/; s/--enable-(vdpau)/--disable-\1/; s/\b(rav1e|shaderc)-dev//; s/\blib(bluray|placebo|vdpau|xfixes)-dev\b//' APKBUILD
# `- rm placebo+shaderc to drop spirv-tools (1.7 MiB apk)

sed -ri 's/--enable-libxcb/--disable-libxcb --disable-indev=xcbgrab --disable-ffplay --disable-encoder=opus /' APKBUILD
sed -ri 's/\bffplay$//; s/\bsdl2-dev\b//' APKBUILD

##
## golflympics; decode-only, super-specific for copyparty only

[ $hub ] || {
sed -ri 's/--enable-(ladspa|lv2|vaapi|vulkan)/--disable-\1/' APKBUILD
sed -ri 's/--enable-lib(aom|ass|drm|fontconfig|freetype|fribidi|harfbuzz|pulse|rist|srt|ssh|v4l2|vidstab|x264|xvid|zimg|vpl)/--disable-lib\1/' APKBUILD
sed -ri 's/\b(v4l-utils|libvpx)-dev\b//' APKBUILD  # (try to) drop v4l2_m2m, and use builtin vp8/vp9 instead of libvpx for decode
sed -ri 's/(--disable-vulkan)/\1 --disable-devices --disable-hwaccels --disable-encoders --enable-encoder=flac --enable-encoder=libjxl --enable-encoder=libmp3lame --enable-encoder=libopus --enable-encoder=libwebp --enable-encoder=mjpeg --enable-encoder=pcm_s16le --enable-encoder=pcm_s16le_planar --enable-encoder=png --enable-encoder=rawvideo --enable-encoder=vnull --enable-encoder=wrapped_avframe --disable-muxers --enable-muxer=aiff --enable-muxer=apng --enable-muxer=caf --enable-muxer=ffmetadata --enable-muxer=fifo --enable-muxer=flac --enable-muxer=image2 --enable-muxer=image2pipe --enable-muxer=matroska --enable-muxer=matroska_audio --enable-muxer=mjpeg --enable-muxer=mp3 --enable-muxer=null --enable-muxer=opus --enable-muxer=pcm_s16le --enable-muxer=wav --enable-muxer=webm --enable-muxer=webp --enable-muxer=yuv4mpegpipe --disable-filters --enable-filter=anoisesrc --enable-filter=asplit --enable-filter=amerge --enable-filter=amix --enable-filter=aresample --enable-filter=crop --enable-filter=showspectrumpic --enable-filter=showwavespic --enable-filter=convolution --enable-filter=volume --enable-filter=compand --enable-filter=setsar --enable-filter=scale       --disable-decoder=av1 --disable-hwaccel=v4l2_m2m --disable-decoder=h263_v4l2m2m --disable-decoder=h264_v4l2m2m --disable-decoder=mpeg1_v4l2m2m --disable-decoder=mpeg2_v4l2m2m --disable-decoder=mpeg4_v4l2m2m --disable-decoder=vc1_v4l2m2m --disable-decoder=vp8_v4l2m2m --disable-decoder=vp9_v4l2m2m --disable-decoder=subrip --disable-decoder=srt --disable-decoder=pgssub --disable-decoder=cc_dec --disable-decoder=dvdsub --disable-decoder=dvbsub --disable-decoder=ssa --disable-decoder=ass --disable-decoder=opus /' APKBUILD
# `- s/av1/libdav1d/; s/libvorbis/vorbis/; s/opus/libopus/; libvorbis and mpg123 gets pulled in by openmpt 
}

p=/root/packages/$(abuild -A)
rm -rf $p
abuild -FrcK

mkdir $p/ex
mv $p/ffmpeg-d* $p/ex  # dbg,dev,doc
cp -pv src/ffmpeg-*/ffbuild/config.log $p/

[ $hub ] && rm -rf $p.hub && mv $p $p.hub

cp -pv /root/.abuild/*.pub ~/packages/
