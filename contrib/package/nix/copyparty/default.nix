{ lib, stdenv, makeWrapper, fetchurl, utillinux, python, jinja2, impacket, pyftpdlib, pyopenssl, argon2-cffi, pillow, pyvips, ffmpeg, mutagen,

# use argon2id-hashed passwords in config files (sha2 is always available)
withHashedPasswords ? true,

# create thumbnails with Pillow; faster than FFmpeg / MediaProcessing
withThumbnails ? true,

# create thumbnails with PyVIPS; even faster, uses more memory
# -- can be combined with Pillow to support more filetypes
withFastThumbnails ? false,

# enable FFmpeg; thumbnails for most filetypes (also video and audio), extract audio metadata, transcode audio to opus
# -- possibly dangerous if you allow anonymous uploads, since FFmpeg has a huge attack surface
# -- can be combined with Thumbnails and/or FastThumbnails, since FFmpeg is slower than both
withMediaProcessing ? true,

# if MediaProcessing is not enabled, you probably want this instead (less accurate, but much safer and faster)
withBasicAudioMetadata ? false,

# enable FTPS support in the FTP server
withFTPS ? false,

# samba/cifs server; dangerous and buggy, enable if you really need it
withSMB ? false,

}:

let
  pinData = lib.importJSON ./pin.json;
  pyEnv = python.withPackages (ps:
    with ps; [
      jinja2
    ]
    ++ lib.optional withSMB impacket
    ++ lib.optional withFTPS pyopenssl
    ++ lib.optional withThumbnails pillow
    ++ lib.optional withFastThumbnails pyvips
    ++ lib.optional withMediaProcessing ffmpeg
    ++ lib.optional withBasicAudioMetadata mutagen
    ++ lib.optional withHashedPasswords argon2-cffi
    );
in stdenv.mkDerivation {
  pname = "copyparty";
  version = pinData.version;
  src = fetchurl {
    url = pinData.url;
    hash = pinData.hash;
  };
  buildInputs = [ makeWrapper ];
  dontUnpack = true;
  dontBuild = true;
  installPhase = ''
    install -Dm755 $src $out/share/copyparty-sfx.py
    makeWrapper ${pyEnv.interpreter} $out/bin/copyparty \
      --set PATH '${lib.makeBinPath ([ utillinux ] ++ lib.optional withMediaProcessing ffmpeg)}:$PATH' \
      --add-flags "$out/share/copyparty-sfx.py"
  '';
}
