{ lib, stdenv, makeWrapper, fetchurl, utillinux, python, jinja2, mutagen, pillow
, pyvips, pyftpdlib, pyopenssl, impacket, ffmpeg }:

let
  pinData = lib.importJSON ./pin.json;
  pyEnv = python.withPackages (ps:
    with ps; [
      # mandatory
      jinja2
      # thumbnails
      pyvips
      ffmpeg
      # alternative thumbnails, but not needed in the presence of pyvips and ffmpeg
      # pillow pyheif-pillow-opener pillow-avif-plugin
      # audio metadata
      mutagen
      # ftp server
      pyftpdlib
      pyopenssl
      # smb server
      impacket
    ]);
in stdenv.mkDerivation rec {
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
      --set PATH '${lib.makeBinPath [ utillinux ffmpeg ]}:$PATH' \
      --add-flags "$out/share/copyparty-sfx.py"
  '';
}
