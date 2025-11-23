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

        # Make sure that the nix dependencies don't drift away
        checks.nix-deps-updated = pkgs.runCommandLocal "nix-deps-updated-check" { } ''
          hash="6e3a014f303f86992e75446c3ce3aaf704fc838b850ba3688c9a1f5d358bc9f4"
          dockerfilePath="${self.outPath}/scripts/deps-docker/Dockerfile"

          echo "If you can see this, the dependencies dockerfile updated."
          echo "Please update the nix packages (if necessary) and the hash on this check"
          echo $hash $dockerfilePath | sha256sum --check --status

          # Need to make an empty folder so that Nix doesn't complain
          mkdir $out
        '';

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
