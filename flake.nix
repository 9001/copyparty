{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-22.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    {
      nixosModules.default = ./contrib/nixos/modules/copyparty.nix;
      overlays.default = self: super: {
        copyparty =
          self.python3.pkgs.callPackage ./contrib/package/nix/copyparty {
            ffmpeg = self.ffmpeg-full;
          };
      };
    } // flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlays.default ];
        };
      in {
        packages = {
          inherit (pkgs) copyparty;
          default = self.packages.${system}.copyparty;
        };
      });
}
