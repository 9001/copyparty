{
  lib,
  buildNpmPackage,
  fetchFromGitHub,
}:

buildNpmPackage rec {
  pname = "codemirror";
  version = "5.65.18";

  src = fetchFromGitHub {
    owner = "codemirror";
    repo = "codemirror5";
    tag = version;
    hash = "sha256-VQTpLaTYfJRUKUjLgomE6TijHIZszQqH0L+khErruAU=";
  };

  env.PUPPETEER_SKIP_CHROMIUM_DOWNLOAD = true;

  npmDepsHash = "sha256-OjftAKA4YQIHJqfZ0yuZbIWtgAJOLSeroLua3FA+rTk=";

  patches = [
    ./../../../../../scripts/deps-docker/codemirror.patch
  ];

  postPatch = ''
    # Upstream doesn't have a package-lock.json
    cp ${./package-lock.json} ./package-lock.json

    sed -ri '/^var urlRE = /d' mode/gfm/gfm.js
  '';
}
