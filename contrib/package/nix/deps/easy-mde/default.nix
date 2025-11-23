{fetchFromGitHub, buildNpmPackage, marked, codemirror}:
buildNpmPackage rec {
  pname = "easy-mde";
  version = "2.18.0";

  src = fetchFromGitHub {
    owner = "Ionaru";
    repo = "easy-markdown-editor";
    tag = version;
    hash = "sha256-g3ZjvT/gqKztyrItn+xOysOWcyQ70xCkFY+dWlK7hL8=";
  };

  npmDepsHash = "sha256-Vkyw8PisYD7XznOQjzb2S9No7Ec5tGYUImRQOJLin3M=";

  env.CYPRESS_INSTALL_BINARY = "0";

  patches = [
    ./../../../../../scripts/deps-docker/easymde-ln.patch
  ];
  postPatch = ''
    sed -ri 's`^var marked = require\(.marked.\).marked;$`var marked = window.marked;`' src/js/easymde.js
  '';

  preBuild = ''
    rm -r node_modules/{codemirror,marked}
    ln -s ${codemirror}/lib/node_modules/codemirror node_modules/codemirror
    ln -s ${marked}/lib/node_modules/marked node_modules/marked
  '';

  npmBuildScript = "prepare";
}
