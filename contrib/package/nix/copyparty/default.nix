{
  lib,
  buildPythonApplication,
  fetchurl,
  runCommand,
  compressDrvWeb,
  pigz,
  util-linux,
  python,
  setuptools,
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
  pyftpdlib,
  magic,
  partftpy,
  fusepy, # for partyfuse

  # deps in /copyparty/web/deps
  marked,
  easy-mde,
  busy-mp3,
  copyparty-fonts,
  asmcrypto,
  hash-wasm,
  prism,
  fusepy-copyparty,

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

  # enable FTP server
  withFTP ? true,

  # enable FTPS support in the FTP server
  withFTPS ? false,

  # enable TFTP server
  withTFTP ? false,

  # samba/cifs server; dangerous and buggy, enable if you really need it
  withSMB ? false,

  # enables filetype detection for nameless uploads
  withMagic ? false,

  # extra packages to add to the PATH
  extraPackages ? [ ],

  # function that accepts a python packageset and returns a list of packages to
  # be added to the python venv. useful for scripts and such that require
  # additional dependencies
  extraPythonPackages ? (_p: [ ]),

}:

let
  pinData = lib.importJSON ./pin.json;
  runtimeDeps = ([ util-linux ] ++ extraPackages ++ lib.optional withMediaProcessing ffmpeg);

  sitePackages = drv: "${drv.outPath}/lib/python${lib.versions.majorMinor python.version}/site-packages";
  nodeModules = drv: "${drv.outPath}/lib/node_modules";
  webDeps = runCommand "copyparty-webdeps" {
    nativeBuildInputs = [ util-linux ];
  } ''
    mkdir $out
    cp --verbose -r --target-directory $out \
      ${copyparty-fonts}/*  ${prism}/* \
      ${sitePackages fusepy-copyparty}/fuse.py \
      ${nodeModules easy-mde}/easymde/dist/* \
      ${nodeModules marked}/marked/marked.min.js
    cp ${busy-mp3} $out/busy.mp3.gz
    cp ${hash-wasm}/sha512.umd.min.js $out/sha512.hw.js
    cp ${nodeModules asmcrypto}/@openpgp/asmcrypto.js/asmcrypto.all.es5.js $out/sha512.ac.js
    rename -v ".min" "" $out/*
  '';
  smolWebDeps = compressDrvWeb webDeps {
    compressors.gz = "${lib.getExe pigz} -11 -I 2048 --force {}";
  };
in
buildPythonApplication {
  pname = "copyparty";
  inherit (pinData) version;
  src = fetchurl {
    inherit (pinData) url hash;
  };
  dependencies =
    [
      jinja2
      fusepy
    ]
    ++ lib.optional withSMB impacket
    ++ lib.optional withFTP pyftpdlib
    ++ lib.optional withFTPS pyopenssl
    ++ lib.optional withTFTP partftpy
    ++ lib.optional withCertgen cfssl
    ++ lib.optional withThumbnails pillow
    ++ lib.optional withFastThumbnails pyvips
    ++ lib.optional withMediaProcessing ffmpeg
    ++ lib.optional withBasicAudioMetadata mutagen
    ++ lib.optional withHashedPasswords argon2-cffi
    ++ lib.optional withZeroMQ pyzmq
    ++ lib.optional withMagic magic
    ++ (extraPythonPackages python.pkgs);
  makeWrapperArgs = [ "--prefix PATH : ${lib.makeBinPath runtimeDeps}" ];

  pyproject = true;
  build-system = [
    setuptools
  ];
  # Build webdeps when building from source
  preBuild = lib.optionalString (true) ''
    # TODO: remove this when we build this from source.
    # This is just so that we can try this without building from source
    rm -r copyparty/web/deps/* && touch copyparty/web/deps/__init__.py

    cp -vr ${smolWebDeps}/* copyparty/web/deps/
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
    mainProgram = "copyparty";
    sourceProvenance = [ lib.sourceTypes.fromSource ];
  };
}
