{
  lib,
  buildPythonApplication,
  fetchurl,
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
  paramiko,
  pyftpdlib,
  magic,
  partftpy,
  fusepy, # for partyfuse

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

  # enable SFTP server
  withSFTP ? false,

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

  # to build stable + unstable with the same file
  stable ? true,

  # for commit date, only used when stable = false
  copypartyFlake ? null,

  nix-gitignore,
}:

let
  pinData = lib.importJSON ./pin.json;
  runtimeDeps = ([ util-linux ] ++ extraPackages ++ lib.optional withMediaProcessing ffmpeg);
  inherit (copypartyFlake) lastModifiedDate;
  # ex: "1970" "01" "01"
  dateStringsZeroPrefixed = {
    year = builtins.substring 0 4 lastModifiedDate;
    month = builtins.substring 4 2 lastModifiedDate;
    day = builtins.substring 6 2 lastModifiedDate;
  };
  # ex: "1970" "1" "1"
  dateStringsShort = builtins.mapAttrs (_: val: toString (lib.toIntBase10 val)) dateStringsZeroPrefixed;
  unstableVersion =
    if copypartyFlake == null then
      "${pinData.version}-unstable"
    else
      with dateStringsZeroPrefixed; "${pinData.version}-unstable-${year}-${month}-${day}"
  ;
  version = if stable then pinData.version else unstableVersion;
  stableSrc = fetchurl {
    inherit (pinData) url hash;
  };
  root = ../../../..;
  unstableSrc = nix-gitignore.gitignoreSource [] root;
  src = if stable then stableSrc else unstableSrc;
  rev = copypartyFlake.shortRev or copypartyFlake.dirtyShortRev or "unknown";
  unstableCodename = "unstable" + (lib.optionalString (copypartyFlake != null) "-${rev}");
in
buildPythonApplication {
  pname = "copyparty";
  inherit version src;
  postPatch = lib.optionalString (!stable) ''
    old_src="$(mktemp -d)"
    tar -C "$old_src" -xf ${stableSrc}
    declare -a folders
    folders=("$old_src"/*)
    count_folders="''${#folders[@]}"
    if [[ $count_folders != 1 ]]; then
      declare -p folders
      echo "Expected 1 folder, found $count_folders" >&2
      exit 1
    fi
    old_src_folder="''${folders[0]}"
    cp -r "$old_src_folder"/copyparty/web/deps copyparty/web/deps
    sed -i 's/^CODENAME =.*$/CODENAME = "${unstableCodename}"/' copyparty/__version__.py
    ${lib.optionalString (copypartyFlake != null) (with dateStringsShort; ''
      sed -i 's/^BUILD_DT =.*$/BUILD_DT = (${year}, ${month}, ${day})/' copyparty/__version__.py
    '')}
  '';
  dependencies =
    [
      jinja2
      fusepy
    ]
    ++ lib.optional withSMB impacket
    ++ lib.optional withSFTP paramiko
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
  meta = {
    description = "Turn almost any device into a file server";
    longDescription = ''
      Portable file server with accelerated resumable uploads, dedup, WebDAV, SFTP,
      FTP, TFTP, zeroconf, media indexer, thumbnails++ all in one file, no deps
    '';
    homepage = "https://github.com/9001/copyparty";
    changelog = "https://github.com/9001/copyparty/releases/tag/v${pinData.version}";
    license = lib.licenses.mit;
    mainProgram = "copyparty";
    sourceProvenance = [ lib.sourceTypes.fromSource ];
  };
}
