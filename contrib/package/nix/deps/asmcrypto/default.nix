{ buildNpmPackage, fetchFromGitHub, jq, nodejs_20}:
buildNpmPackage rec {
  pname = "asmcrypto";
  version = "c72492f4a66e17a0e5dd8ad7874de354f3ccdaa5";

  src = fetchFromGitHub {
    owner = "openpgpjs";
    repo = "asmcrypto.js";
    rev = version;
    hash = "sha256-nuRVRrET+HIjho+d5MHVIk4iKJg967CqMAuvAQoJNmI=";
  };

  nativeBuildInputs = [ jq ];

  postPatch = ''
    echo "export { Sha512 } from './hash/sha512/sha512';" > src/entry-export_all.ts
  '';

  npmDepsHash = "sha256-QlGyILr4B3H1bW4vpAeuT7FkkUWGQg2DqpZn8uDh2po=";

  # Some assertion fails with newer node
  nodejs = nodejs_20;

  npmBuildScript = "prepare";

  # This has broken symlinks for some reason, and Nix doesn't like it
  postInstall = "rm -r $out/lib/node_modules/@openpgp/asmcrypto.js/node_modules/.bin/";
}
