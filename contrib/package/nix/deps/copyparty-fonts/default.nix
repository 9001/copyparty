{ runCommand, fetchzip, fetchurl, python3 }:
let
  fontawesomeVersion = "5.13.0";
  fontawesomeSrc = fetchzip {
    url = "https://github.com/FortAwesome/Font-Awesome/releases/download/${fontawesomeVersion}/fontawesome-free-${fontawesomeVersion}-web.zip";
    hash = "sha256-gK21ztU2egNORebAyKlmxGKmoshp5ZZgMAv5jWIYBkI=";
  };
  scp = fetchurl {
    url = "https://fonts.gstatic.com/s/sourcecodepro/v11/HI_SiYsKILxRpg3hIP6sJ7fM7PqlPevW.woff2";
    hash = "sha256-ZZ/2tZan3bZIzWWlQpiTvmVWKcDTancDgXpjoIcOwCA=";
  };
  python = python3.withPackages (ps: with ps; [ fonttools zopfli brotli ]);
  rawScript = ./../../../../../scripts/deps-docker/mini-fa.sh;

in
runCommand "copyparty-fonts"
{
  nativeBuildInputs = [ python ];
}
  ''
    mkdir -p $out/no-pk
    substitute ${rawScript} nix-mini-fa.sh \
      --replace-fail "/z/fontawesome-fre*" "${fontawesomeSrc}" \
      --replace-fail "/z/dist" $out \
      --replace-fail "/z/mini-fa.css" "${./../../../../../scripts/deps-docker/mini-fa.css}" \
      --replace-fail "/z/icon.list" "/build/icon.list" \
      --replace-fail "/z/scp.woff2" "${scp}"
    bash nix-mini-fa.sh
  ''

