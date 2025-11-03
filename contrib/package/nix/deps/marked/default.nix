{ buildNpmPackage, fetchFromGitHub, breakpointHook }:
buildNpmPackage rec {
  pname = "marked";
  version = "4.3.0";

  src = fetchFromGitHub {
    owner = "markedjs";
    repo = "marked";
    tag = "v${version}";
    hash = "sha256-xJotgIUoZSmjgLRIgJP9134PR1GYKjVXM5jp+JpM7bg=";
  };

  dompurify = fetchFromGitHub {
    owner = "cure53";
    repo = "DOMPurify";
    tag = "3.2.7";
    hash = "sha256-lwBi/3uqWBa0UTPV1iKIIXDC6+Fc9uwIgs4+pRUjdPA=";
  };

  npmDepsHash = "sha256-omsoER0I28ZHN78X0aku2jNJApPvpqYKgfPhRbEi+HM=";

  patches = [
    ./../../../../../scripts/deps-docker/marked.patch
    ./../../../../../scripts/deps-docker/marked-ln.patch
  ];

  nativeBuildInputs = [ breakpointHook ];
  postBuild = ''
    # Inject DOMPurify to minified marked
    cat ${dompurify}/dist/purify.min.js >> marked.min.js
  '';
}
