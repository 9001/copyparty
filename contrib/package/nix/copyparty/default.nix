{
  lib,
  stdenv,
  makeWrapper,
  fetchurl,
  util-linux,
  python,
  jinja2,
  impacket,
  pyopenssl,
  cfssl,
  argon2-cffi,
  pillow,
  pyvips,
  pyzmq,
  ffmpeg,
  mutagen,

  # use argon2id-hashed passwords in config files (sha2 is always available)
  withHashedPasswords ? true,

  # generate TLS certificates on startup (pointless when reverse-proxied)
  withCertgen ? false,

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

  # send ZeroMQ messages from event-hooks
  withZeroMQ ? true,

  # enable FTPS support in the FTP server
  withFTPS ? false,

  # samba/cifs server; dangerous and buggy, enable if you really need it
  withSMB ? false,

  # extra packages to add to the PATH
  extraPackages ? [ ],

  # function that accepts a python packageset and returns a list of packages to
  # be added to the python venv. useful for scripts and such that require
  # additional dependencies
  extraPythonPackages ? (_p: [ ]),

}:

let
  pinData = lib.importJSON ./pin.json;
  pyEnv = python.withPackages (
    ps:
    with ps;
    [
      jinja2
    ]
    ++ lib.optional withSMB impacket
    ++ lib.optional withFTPS pyopenssl
    ++ lib.optional withCertgen cfssl
    ++ lib.optional withThumbnails pillow
    ++ lib.optional withFastThumbnails pyvips
    ++ lib.optional withMediaProcessing ffmpeg
    ++ lib.optional withBasicAudioMetadata mutagen
    ++ lib.optional withHashedPasswords argon2-cffi
    ++ lib.optional withZeroMQ pyzmq
    ++ (extraPythonPackages ps)
  );

  runtimeDeps = ([ util-linux ] ++ extraPackages ++ lib.optional withMediaProcessing ffmpeg);
in
stdenv.mkDerivation {
  pname = "copyparty";
  inherit (pinData) version;
  src = fetchurl {
    inherit (pinData) url hash;
  };
  nativeBuildInputs = [ makeWrapper ];
  dontUnpack = true;
  installPhase = ''
    install -Dm755 $src $out/share/copyparty-sfx.py
    makeWrapper ${pyEnv.interpreter} $out/bin/copyparty \
      --prefix PATH : ${lib.makeBinPath runtimeDeps} \
      --add-flag $out/share/copyparty-sfx.py
  '';
  meta = {
    description = "Turn almost any device into a file server";
    longDescription = ''
      Portable file server with accelerated resumable uploads, dedup, WebDAV,
      FTP, TFTP, zeroconf, media indexer, thumbnails++ all in one file, no deps
    '';
    homepage = "https://github.com/9001/copyparty";
    changelog = "https://github.com/9001/copyparty/releases/tag/v${pinData.version}";
    license = lib.licenses.mit;
    inherit (python.meta) platforms;
    mainProgram = "copyparty";
    sourceProvenance = [ lib.sourceTypes.binaryBytecode ];
  };
}
