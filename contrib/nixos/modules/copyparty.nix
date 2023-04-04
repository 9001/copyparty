{ config, pkgs, lib, ... }:

with lib;

let
  name = "copyparty";
  cfg = config.services.copyparty;
  configFile = pkgs.writeText "copyparty.conf" cfg.config;
  bin = "${cfg.package}/bin/${name}";
  home = "/var/lib/copyparty";
  defaultShareDir = "${home}/data";
in {
  options.services.copyparty = {
    enable = mkEnableOption "web-based file manager";

    package = mkOption {
      type = types.package;
      default = pkgs.copyparty;
      defaultText = "pkgs.copyparty";
      description = ''
        Package of the application to run, exposed for overriding purposes.
      '';
    };

    readWritePaths = mkOption {
      default = [ ];
      type = types.listOf types.str;
      description = "Paths permitted for read/write.";
    };

    openFilesLimit = mkOption {
      default = 4096;
      type = types.either types.int types.str;
      description = "Number of files to allow copyparty to open.";
    };

    config = mkOption {
      type = types.lines;
      description =
        "Configuration file. See https://github.com/9001/copyparty#server-config for reference";
      default = ''
        [global]
          i: 127.0.0.1
          no-reload

        # create a volume:
        [/]                   # create a volume at "/" (the webroot), which will
          ${defaultShareDir}  # share the contents of "${defaultShareDir}"
          accs:
            r: *              # everyone gets read-access, but
      '';
      example = ''
        [global]
          i: 0.0.0.0
          no-reload

        # create users:
        [accounts]
          # username: password
          ed: 123

        # create a volume:
        [/]                   # create a volume at "/" (the webroot), which will
          ${defaultShareDir}  # share the contents of "${defaultShareDir}"
          accs:
            r: *              # everyone gets read-access, but
            rw: ed            # the user "ed" gets read-write
      '';
    };
  };

  config = mkIf cfg.enable {
    systemd.services.copyparty = {
      description = "http file sharing hub";
      wantedBy = [ "multi-user.target" ];

      environment = {
        PYTHONUNBUFFERED = "true";
        XDG_CONFIG_HOME = "${home}/.config";
      };

      preStart = ''
        mkdir -p "$XDG_CONFIG_HOME"
        mkdir -p "${defaultShareDir}"
      '';

      serviceConfig = {
        Type = "simple";
        ExecStart = "${bin} -c ${configFile}";

        # Hardening options
        User = "copyparty";
        Group = "copyparty";
        StateDirectory = "copyparty";
        StateDirectoryMode = "0755";
        WorkingDirectory = home;
        TemporaryFileSystem = "/:ro";
        BindReadOnlyPaths = [
          "/nix/store"
          "-/etc/resolv.conf"
          "-/etc/nsswitch.conf"
          "-/etc/hosts"
          "-/etc/localtime"
        ];
        BindPaths = [ home ] ++ cfg.readWritePaths;
        # Would re-mount paths ignored by temporary root
        #ProtectSystem = "strict";
        ProtectHome = true;
        PrivateTmp = true;
        PrivateDevices = true;
        ProtectKernelTunables = true;
        ProtectControlGroups = true;
        RestrictSUIDSGID = true;
        PrivateMounts = true;
        ProtectKernelModules = true;
        ProtectKernelLogs = true;
        ProtectHostname = true;
        ProtectClock = true;
        ProtectProc = "invisible";
        ProcSubset = "pid";
        RestrictNamespaces = true;
        RemoveIPC = true;
        UMask = "0077";
        LimitNOFILE = cfg.openFilesLimit;
        NoNewPrivileges = true;
        LockPersonality = true;
        RestrictRealtime = true;
        RestrictAddressFamilies = "AF_INET AF_INET6";
      };
    };

    users.groups.copyparty = { };
    users.users.copyparty = {
      description = "Service user for copyparty";
      group = "copyparty";
      home = home;
      isSystemUser = true;
    };
  };
}
