{ fetchzip, breakpointHook, stdenvNoCC }: stdenvNoCC.mkDerivation rec {
  # The build script for this uses docker, so let's just use the release tarball
  name = "hash-wasm";
  version = "4.12.0";

  src = fetchzip {
    url = "https://github.com/Daninet/hash-wasm/releases/download/v${version}/hash-wasm@${version}.zip";
    hash = "sha256-bjHpMzOXPCoKVoucVY7CXZ70vPtn8+UXMxBD7KOHg2k=";
  };

  dontBuild = true;

  installPhase = ''
      mkdir $out
      cp $src/* -r --target-directory=$out
    '';

  nativeBuildInputs = [ breakpointHook ];

  npmDepsHash = "sha256-S9g8YlrsD7t0y9qi/CsN7qHZcT/TDfC1XxiArSGjAe4=";
}
