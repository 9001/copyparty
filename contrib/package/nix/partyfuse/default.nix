{
  stdenvNoCC,
  copyparty,
  python3,
  makeBinaryWrapper,
}:
let
  python = python3.withPackages (p: [ p.fusepy ]);
in
stdenvNoCC.mkDerivation {
  pname = "partyfuse";
  inherit (copyparty) version meta;
  src = ../../../..;

  nativeBuildInputs = [ makeBinaryWrapper ];

  installPhase = ''
    runHook preInstall

    install -Dm444 bin/partyfuse.py -t $out/share/copyparty
    makeWrapper ${python.interpreter} $out/bin/partyfuse \
      --add-flag $out/share/copyparty/partyfuse.py

    runHook postInstall
  '';
}
