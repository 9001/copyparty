{
  stdenvNoCC,
  copyparty,
  python312,
  makeBinaryWrapper,
}:
stdenvNoCC.mkDerivation {
  pname = "u2c";
  inherit (copyparty) version meta;
  src = ../../../..;

  nativeBuildInputs = [ makeBinaryWrapper ];

  installPhase = ''
    runHook preInstall

    install -Dm444 bin/u2c.py -t $out/share/copyparty
    mkdir $out/bin
    makeWrapper ${python312.interpreter} $out/bin/u2c \
      --add-flag $out/share/copyparty/u2c.py

    runHook postInstall
  '';
}
