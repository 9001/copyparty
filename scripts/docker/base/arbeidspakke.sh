#!/bin/ash
set -e

AVER=3.24

[ $1 = 1 ] && hub=1
ls -al arbeidspakke.sh
stamp=$(date -u +%Y-%m-%d)-$(md5sum <arbeidspakke.sh | cut -c-16)-$1-$(date +%s)

uname -a
apk update
apk upgrade -al
apk add alpine-sdk doas wget
echo permit nopass root > /etc/doas.d/u.conf
cp -pv /root/.abuild/*.pub /etc/apk/keys/ || abuild-keygen -ina

##
## yeet h265

mkdir /ffmpeg
cd /ffmpeg
base=https://github.com/alpinelinux/aports/raw/refs/heads/$AVER-stable/community/ffmpeg/
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

    awk >t <libavcodec/aac/aacdec_tab.c '/^[^ \t]/{o=0} /^(static|const).*( sbr_|_hcod)/{o=1} !o{print;next} {gsub(/\{ *-?[0-9]+, *-?[0-9]+ *\}/, "{ 1, 1 }")}1'
    mv t libavcodec/aac/aacdec_tab.c

    # invent the missing disable-option for this crap
    sed -ri 's/(^v4l2_m2m_deps=")/\1videotoolbox /' configure

    awk >t <configure '!o&&/FFMPEG_CONFIGURATION=/{o=1;print"FFMPEG_CONFIGURATION='thecfgstr'";next}1'
    cat t >configure; rm t
}
EOF
sed -ri "s/thecfgstr/arbeidspakke-$stamp/" APKBUILD

##
## shrink-ray

sed -ri 's/--enable-lib(bluray|dvdnav|dvdread|placebo|rav1e|shaderc)/--disable-lib\1/; s/--enable-(vdpau)/--disable-\1/; s/\b(rav1e|shaderc)-dev//; s/\blib(bluray|placebo|vdpau|xfixes)-dev\b//' APKBUILD
# `- rm placebo+shaderc to drop spirv-tools (1.7 MiB apk)

sed -ri 's/--enable-libxcb/--disable-libxcb --disable-indev=xcbgrab --disable-ffplay --disable-encoder=opus --disable-decoder=metasound --disable-decoder=twinvq/' APKBUILD
# `- metasound+twinvq = +450 KiB apk
sed -ri 's/\bffplay$//; s/\bsdl2-dev\b//' APKBUILD

##
## golflympics; decode-only, super-specific for copyparty only

[ $hub ] || {
sed -ri 's/--enable-(ladspa|lv2|vaapi|vulkan)/--disable-\1/' APKBUILD
sed -ri 's/--enable-lib(aom|ass|drm|fontconfig|freetype|fribidi|harfbuzz|pulse|rist|srt|ssh|v4l2|vidstab|x264|xvid|zimg|vpl)/--disable-lib\1/' APKBUILD
sed -ri 's/\b(v4l-utils|libvpx)-dev\b//' APKBUILD  # (try to) drop v4l2_m2m, and use builtin vp8/vp9 instead of libvpx for decode
sed -ri 's/(--disable-vulkan)/\1 --disable-devices --disable-hwaccels --disable-encoders --enable-encoder=flac --enable-encoder=libjxl --enable-encoder=libmp3lame --enable-encoder=libopus --enable-encoder=libwebp --enable-encoder=mjpeg --enable-encoder=pcm_f32le --enable-encoder=pcm_s16le --enable-encoder=pcm_s16le_planar --enable-encoder=png --enable-encoder=rawvideo --enable-encoder=vnull --enable-encoder=wrapped_avframe --disable-muxers --enable-muxer=aiff --enable-muxer=apng --enable-muxer=caf --enable-muxer=ffmetadata --enable-muxer=fifo --enable-muxer=flac --enable-muxer=image2 --enable-muxer=image2pipe --enable-muxer=matroska --enable-muxer=matroska_audio --enable-muxer=mjpeg --enable-muxer=mp3 --enable-muxer=null --enable-muxer=opus --enable-muxer=pcm_f32le --enable-muxer=pcm_s16le --enable-muxer=wav --enable-muxer=webm --enable-muxer=webp --enable-muxer=yuv4mpegpipe --disable-filters --enable-filter=anoisesrc --enable-filter=asplit --enable-filter=amerge --enable-filter=amix --enable-filter=aresample --enable-filter=crop --enable-filter=showspectrumpic --enable-filter=showwavespic --enable-filter=convolution --enable-filter=volume --enable-filter=compand --enable-filter=setsar --enable-filter=scale       --disable-decoder=av1 --disable-hwaccel=v4l2_m2m --disable-decoder=h263_v4l2m2m --disable-decoder=h264_v4l2m2m --disable-decoder=mpeg1_v4l2m2m --disable-decoder=mpeg2_v4l2m2m --disable-decoder=mpeg4_v4l2m2m --disable-decoder=vc1_v4l2m2m --disable-decoder=vp8_v4l2m2m --disable-decoder=vp9_v4l2m2m --disable-decoder=subrip --disable-decoder=srt --disable-decoder=pgssub --disable-decoder=cc_dec --disable-decoder=dvdsub --disable-decoder=dvbsub --disable-decoder=ssa --disable-decoder=ass --disable-decoder=opus /' APKBUILD
# `- s/av1/libdav1d/; s/libvorbis/vorbis/; s/opus/libopus/; libvorbis and mpg123 gets pulled in by openmpt 

# grep -E '^extern const.* FF[^ ]+ +ff_.*_(encoder|decoder|hwaccel|bsf|parser|demuxer|muxer);$' libavcodec/allcodecs.c libavcodec/hwaccels.h libavcodec/bitstream_filters.c libavcodec/parsers.c libavformat/allformats.c | sed -r 's/.* ff_([^/;]*)_([^/;]*);.*/\2 \1/' | sort > names
# xsel -o | tr ' ' '\n' | tr . % | grep -E .. | while read x; do grep -qE "^decoder $x$" names || echo "? $x"; done

sed -ri 's/(--disable-vulkan)/\1 '"$(printf '--disable-decoder=%s ' aasc alias_pix anm ansi arbc argo avrn avs bethsoftvid bfi bintext bmv_video brender_pix c93 cdgraphics cdtoons cdxl cljr cllc cpia cscd cyuv dfa dsicinvideo eacmv eamad eatgq eatgv eatqi escape124 escape130 fic fmvc frwu gdv gem hnm4_video idcin idf iff_ilbm imm4 interplay_video ipu jv kgv1 kmvc lead lscr m101 magicyuv mdec media100 mimic mmvideo motionpixels msa1 mscc msp2 mszh mts2 mv30 mvc1 mvc2 mvdv mvha mwsc mxpeg notchlc nuv paf_video pdv photocd pictor ptx qdraw qpeg rasc rl2 rtv1 sanm scpr sga sgirle simbiosis_imx smacker smc smvjpeg snow sp5x srgc tdsc thp tiertexseqvideo tmv truemotion2rt txd ulti vb vble vbn vcr1 vmdvideo vmix vmnc vqa vqc wcmv wnv1 xan_wc3 xan_wc4 xbin xface xl ylc yop zerocodec )/" APKBUILD
# `- codecs: very obscure video

sed -ri 's/(--disable-vulkan)/\1 '"$(printf '--disable-decoder=%s ' acelp_kelvin adpcm_agm adpcm_argo adpcm_ct adpcm_dtk adpcm_ea adpcm_ea_maxis_xa adpcm_ea_r1 adpcm_ea_r2 adpcm_ea_r3 adpcm_ea_xas adpcm_ima_acorn adpcm_ima_alp adpcm_ima_apc adpcm_ima_apm adpcm_ima_cunning adpcm_ima_dat4 adpcm_ima_ea_eacs adpcm_ima_ea_sead adpcm_ima_escape adpcm_ima_hvqm2 adpcm_ima_hvqm4 adpcm_ima_iss adpcm_ima_magix adpcm_ima_mtf adpcm_ima_pda adpcm_ima_rad adpcm_ima_ssi adpcm_mtaf adpcm_vima adpcm_xmd adpcm_zork bmv_audio bonk cbd2_dpcm comfortnoise derf_dpcm dolby_e dsicinaudio dss_sp evrc fastaudio ftr gremlin_dpcm hcom iac interplay_acm interplay_dpcm metasound misc4 mlp osq paf_audio rka roq_dpcm sdx2_dpcm sol_dpcm sonic vmdaudio wady_dpcm wavarc ws_snd1 xan_dpcm )/" APKBUILD
# `- codecs: very obscure audio

sed -ri 's/(--disable-vulkan)/\1 '"$(printf '--disable-decoder=%s ' agm aic amv apv asv1 asv2 aura aura2 avrp avs avui bink bitpacked cavs cfhd cinepak clearvideo cri dirac dxa eightbps flashsv flashsv2 flic fourxm g2m h261 hap hq_hqa hqx indeo2 indeo3 indeo4 indeo5 jpeg2000 jpegls lagarith loco mjpegb mobiclip mss1 mss2 msvideo1 pgx pixlet prosumer qtrle r10k r210 roq roq_dpcm rpza rscc screenpresso sgi sheervideo speedhq sunrast svq1 svq3 truemotion1 truemotion2 truemotion2rt tscc tscc2 vc1image vp3 vp4 vp5 vp6 vp6a vp6f wbmp zero12v )/" APKBUILD
# `- codecs: obscure video

sed -ri 's/(--disable-vulkan)/\1 '"$(printf '--disable-decoder=%s ' adpcm_ima_amv adpcm_ima_dk3 adpcm_ima_dk4 adpcm_ima_moflex adpcm_ima_oki adpcm_ima_smjpeg ahx apac cook dsd_lsbf dsd_lsbf_planar dsd_msbf dsd_msbf_planar eightsvx_exp eightsvx_fib hca ilbc imc mace3 mace6 msnsiren nellymoser pcm_lxf pcm_s24daud pcm_sga pcm_vidc qdm2 qdmc s302m sbc shorten siren truespeech twinvq wmavoice xma1 xma2 )/" APKBUILD
# `- codecs: obscure audio

sed -ri 's/(--disable-vulkan)/\1 '"$(printf '--disable-decoder=%s ' dvvideo dxtory fits fraps pam pfm phm prores prores_raw psd v210 v210x v308 v408 xwd y41p zlib )/" APKBUILD
# `- codecs: not-quite-obscure-but-still-meh video

sed -ri 's/(--disable-vulkan)/\1 '"$(printf '--disable-decoder=%s ' aptx aptx_hd binkaudio_dct binkaudio_rdft )/" APKBUILD
# `- codecs: not-quite-obscure-but-still-meh audio

sed -ri 's/(--disable-vulkan)/\1 '"$(printf '--disable-decoder=%s ' ccaption jacosub microdvd movtext mpl2 pjs realtext sami stl subviewer subviewer1 text vplayer webvtt xsub )/" APKBUILD
# `- oops! all subtitles

sed -ri 's/(--disable-vulkan)/\1 '"$(printf '--disable-demuxer=%s ' aa aax ace acm act adf adp ads adx aea afc aix alp anm apac apc apm aptx aptx_hd apv aqtitle argo_asf argo_brp argo_cvg ass ast avr avs avs2 avs3 bethsoftvid bfi bink binka bintext bit bitpacked bmv boa bonk c93 caf cavsvideo cdg cdxl cine concat dash data daud dcstr derf dfa dhav dirac dsf dsicin dss dv dvbsub dvbtxt dxa ea ea_cdata epaf evc filmstrip fits flic fourxm frm fsb fsb fwse gdv genh gxf hca hcom hls hnm iamf idcin idf ifv ilbc image2_alias_pix image_bmp_pipe image2_brender_pix image_cri_pipe image_dds_pipe image_dpx_pipe image_exr_pipe image_gem_pipe image_hdr_pipe image_j2k_pipe image_jpegls_pipe image_jpegxl_pipe image_jpegxs_pipe image_pam_pipe image_pbm_pipe image_pcx_pipe image_pfm_pipe image_pgm_pipe image_pgmyuv_pipe image_pgx_pipe image_phm_pipe image_photocd_pipe image_pictor_pipe image_ppm_pipe image_psd_pipe image_qdraw_pipe image_qoi_pipe image_sgi_pipe image_sunrast_pipe image_svg_pipe image_tiff_pipe image_vbn_pipe image_webp_pipe image_xbm_pipe image_xpm_pipe image_xwd_pipe ingenient ipmovie ipu ircam iss iv8 ivf ivr jacosub jv kux kvag laf lc3 live_flv lmlm4 loas lrc luodat lvf lxf mca mcc mgsts microdvd mjpeg mjpeg_2000 mlp mlv mm mmf mods moflex mpjpeg mpl2 mpsub msf msnwc_tcp msp mtaf mtv musx mv mvi mxf mxg nc nistsphere nsp nsv nuv obu oma osq paf pcm_vidc pdv pjs pmp pp_bnk pva pvf qcp qoa r3d rawvideo rcwt realtext redspark rka rl2 roq rpl rsd rso rtp rtsp sami sap sbc sbg scc scd sdns sdp sdr2 sds sdx segafilm ser sga shorten siff simbiosis_imx sln smacker smjpeg smush sol spdif srt stl str subviewer subviewer1 sup svag svs tedcaptions thp threedostr tiertexseq tmv truehd tty txd ty usm v210 v210x vag vc1t vividas vivo vmd vobsub voc vpk vplayer vqf w64 wady wavarc wc3 webm_dash_manifest webvtt wsaud wsd wsvqa wtv wve xa xbin xmd xmv xvag xwma yop yuv4mpegpipe )/" APKBUILD
# `- hipster formats / filetypes / demuxers   # caf: only need muxing  # bfstm=3ds/gc/wii

# cat aaa | grep -E '^ D..... ('"$(xsel -o | tr ' ' '|'))" | grep decoder
# xsel -o | tr ' ' '\n' | LC_ALL=C sort | tr '\n' ' ' | xsel -ib
}



[ $1 -gt 1 ] && sed -ri 's/(--disable-libxcb )/\1--disable-doc --disable-htmlpages --disable-manpages --disable-podpages --disable-txtpages /' APKBUILD

p=/root/packages/$(abuild -A)
rm -rf $p
abuild -FrcK

mkdir $p/ex
mv $p/ffmpeg-d* $p/ex  # dbg,dev,doc
cp -pv src/ffmpeg-*/ffbuild/config.log $p/
#tar -cz src > $p/.tar

[ $hub ] && rm -rf $p.hub && mv $p $p.hub

cp -pv /root/.abuild/*.pub ~/packages/
