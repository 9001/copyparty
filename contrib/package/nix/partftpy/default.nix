{
  lib,
  buildPythonPackage,
  fetchurl,
  setuptools,
}:
let
  pinData = lib.importJSON ./pin.json;
in

buildPythonPackage rec {
  pname = "partftpy";
  inherit (pinData) version;
  pyproject = true;

  src = fetchurl {
    inherit (pinData) url hash;
  };

  build-system = [ setuptools ];

  pythonImportsCheck = [ "partftpy.TftpServer" ];

  meta = {
    description = "Pure Python TFTP library  (copyparty edition)";
    homepage = "https://github.com/9001/partftpy";
    changelog = "https://github.com/9001/partftpy/releases/tag/${version}";
    license = lib.licenses.mit;
  };
}
