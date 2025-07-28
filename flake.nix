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
      overlays.default = self: super: rec {
        copyparty = self.python3.pkgs.callPackage ./contrib/package/nix/copyparty {
          ffmpeg = self.ffmpeg-full;
        };

        partyfuse = super.callPackage ./contrib/package/nix/partyfuse {
          inherit copyparty;
        };

        u2c = super.callPackage ./contrib/package/nix/u2c {
          inherit copyparty;
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
        packages = {
          inherit (pkgs)
            copyparty
            partyfuse
            u2c
            ;
          default = self.packages.${system}.copyparty;
        };

        formatter = pkgs.nixfmt-tree;
      }
    );
}
