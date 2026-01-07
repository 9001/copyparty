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
      overlays.default = final: prev:
        (import ./contrib/package/nix/overlay.nix final prev) // { copypartyFlake = self; };
    }
    // flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config = {
            allowAliases = false;
          };
          overlays = [
            self.overlays.default
          ];
        };
      in
      {
        # check that copyparty builds with all optionals turned on
        checks = {
          inherit (pkgs)
            copyparty-full
            copyparty-unstable-full
            ;
        };

        packages = {
          inherit (pkgs)
            copyparty
            copyparty-full
            copyparty-unstable
            copyparty-unstable-full
            ;
          default = self.packages.${system}.copyparty;
        };

        formatter = pkgs.nixfmt-tree;
      }
    );
}
