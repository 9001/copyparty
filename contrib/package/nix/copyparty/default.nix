{ lib, stdenv, makeWrapper, fetchurl, utillinux, python, jinja2, mutagen, pillow
, pyvips, pyftpdlib, pyopenssl, impacket, ffmpeg }:

let
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
  version = "1.6.11";
  src = fetchurl {
    url =
      "https://github.com/9001/copyparty/releases/download/v${version}/copyparty-sfx.py";
    hash = "sha256-0JbjOrZm70UhOJndOhBzX2K1RBM5y3N0+TsjLQtsjTQ=";
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
