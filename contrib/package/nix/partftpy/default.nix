{
  lib,
  buildPythonPackage,
  fetchurl,
  setuptools,
}:

buildPythonPackage rec {
  pname = "partftpy";
  version = "0.4.0";
  pyproject = true;

  src = fetchurl {
    url = "https://github.com/9001/partftpy/releases/download/v0.4.0/partftpy-0.4.0.tar.gz";
    hash = "sha256-5Q2zyuJ892PGZmb+YXg0ZPW/DK8RDL1uE0j5HPd4We0=";
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
