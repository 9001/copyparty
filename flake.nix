{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    {
      nixosModules.default = ./contrib/nixos/modules/copyparty.nix;
      overlays.default = final: prev: {
        copyparty = final.python3.pkgs.callPackage ./contrib/package/nix/copyparty {
          ffmpeg = final.ffmpeg-full;
        };
        python3 = prev.python3.override {
          packageOverrides = pyFinal: pyPrev: {
            partftpy = pyFinal.tftpy.overrideAttrs {
              pname = "partftpy";
              version = "0.4.0";
              src = final.fetchurl {
                url = "https://github.com/9001/partftpy/releases/download/v0.4.0/partftpy-0.4.0.tar.gz";
                hash = "sha256-5Q2zyuJ892PGZmb+YXg0ZPW/DK8RDL1uE0j5HPd4We0=";
              };
              pythonImportsCheck = [ "partftpy.TftpServer" ];
            };
          };
        };
      };
    }
    // flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowAliases = false;
          };
          overlays = [ self.overlays.default ];
        };
      in
      {
        # check that copyparty builds with all optionals turned on
        checks.copyparty-full = self.packages.${system}.copyparty.override {
          withHashedPasswords = true;
          withCertgen = true;
          withThumbnails = true;
          withFastThumbnails = true;
          withMediaProcessing = true;
          withBasicAudioMetadata = true;
          withZeroMQ = true;
          withFTPS = true;
          withSMB = true;
        };

        packages = {
          inherit (pkgs)
            copyparty
            ;
          default = self.packages.${system}.copyparty;
        };

        formatter = pkgs.nixfmt-tree;
      }
    );
}
