{ stdenvNoCC, fetchFromGitHub, python3 }: stdenvNoCC.mkDerivation rec {
  name = "prism";
  version = "1.29.0";

  src = fetchFromGitHub {
    owner = "PrismJS";
    repo = "prism";
    tag = "v${version}";
    hash = "sha256-KEoICg4xviKsmN9M8ceJdAJ1NhTO7urDJnJknuP4GoQ=";
  };

  nativeBuildInputs = [ python3 ];

  depsScriptDir = ../../../../../scripts/deps-docker;

  postUnpack = ''
    cp ${depsScriptDir}/genprism.* .
  '';

  postPatch = ''
    substituteInPlace ../genprism.sh \
      --replace-fail "/z/dist" "$out" \
      --replace-fail 'prism-$1' "$src" \
      --replace-fail "./genprism.py" "python3 ./genprism.py"
  '';

  buildPhase = ''
    mkdir $out
    cd ..
    bash ./genprism.sh ${version}
  '';

  # genprism.sh already moves things into place
  dontInstall = true;
}
