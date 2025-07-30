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
      overlays.default = import ./contrib/package/nix/overlay.nix;
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
