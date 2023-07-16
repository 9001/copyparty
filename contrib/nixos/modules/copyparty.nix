{ config, pkgs, lib, ... }:

with lib;

let
  mkKeyValue = key: value:
    if value == true then
    # sets with a true boolean value are coerced to just the key name
      key
    else if value == false then
    # or omitted completely when false
      ""
    else
      (generators.mkKeyValueDefault { inherit mkValueString; } ": " key value);

  mkAttrsString = value: (generators.toKeyValue { inherit mkKeyValue; } value);

  mkValueString = value:
    if isList value then
      (concatStringsSep ", " (map mkValueString value))
    else if isAttrs value then
      "\n" + (mkAttrsString value)
    else
      (generators.mkValueStringDefault { } value);

  mkSectionName = value: "[" + (escape [ "[" "]" ] value) + "]";

  mkSection = name: attrs: ''
    ${mkSectionName name}
    ${mkAttrsString attrs}
  '';

  mkVolume = name: attrs: ''
    ${mkSectionName name}
    ${attrs.path}
    ${mkAttrsString {
      accs = attrs.access;
      flags = attrs.flags;
    }}
  '';

  passwordPlaceholder = name: "{{password-${name}}}";

  accountsWithPlaceholders = mapAttrs (name: attrs: passwordPlaceholder name);

  configStr = ''
    ${mkSection "global" cfg.settings}
    ${mkSection "accounts" (accountsWithPlaceholders cfg.accounts)}
    ${concatStringsSep "\n" (mapAttrsToList mkVolume cfg.volumes)}
  '';

  name = "copyparty";
  cfg = config.services.copyparty;
  configFile = pkgs.writeText "${name}.conf" configStr;
  runtimeConfigPath = "/run/${name}/${name}.conf";
  home = "/var/lib/${name}";
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

    openFilesLimit = mkOption {
      default = 4096;
      type = types.either types.int types.str;
      description = "Number of files to allow copyparty to open.";
    };

    settings = mkOption {
      type = types.attrs;
      description = ''
        Global settings to apply.
        Directly maps to values in the [global] section of the copyparty config.
        See `${getExe cfg.package} --help` for more details.
      '';
      default = {
        i = "127.0.0.1";
        no-reload = true;
      };
      example = literalExpression ''
        {
          i = "0.0.0.0";
          no-reload = true;
        }
      '';
    };

    accounts = mkOption {
      type = types.attrsOf (types.submodule ({ ... }: {
        options = {
          passwordFile = mkOption {
            type = types.str;
            description = ''
              Runtime file path to a file containing the user password.
              Must be readable by the copyparty user.
            '';
            example = "/run/keys/copyparty/ed";
          };
        };
      }));
      description = ''
        A set of copyparty accounts to create.
      '';
      default = { };
      example = literalExpression ''
        {
          ed.passwordFile = "/run/keys/copyparty/ed";
        };
      '';
    };

    volumes = mkOption {
      type = types.attrsOf (types.submodule ({ ... }: {
        options = {
          path = mkOption {
            type = types.str;
            description = ''
              Path of a directory to share.
            '';
          };
          access = mkOption {
            type = types.attrs;
            description = ''
              Attribute list of permissions and the users to apply them to.

              The key must be a string containing any combination of allowed permission:
                "r" (read):   list folder contents, download files
                "w" (write):  upload files; need "r" to see the uploads
                "m" (move):   move files and folders; need "w" at destination
                "d" (delete): permanently delete files and folders
                "g" (get):    download files, but cannot see folder contents
                "G" (upget):  "get", but can see filekeys of their own uploads
                "a" (upget):  can see uploader IPs, config-reload

              For example: "rwmd"

              The value must be one of:
                an account name, defined in `accounts`
                a list of account names
                "*", which means "any account"
            '';
            example = literalExpression ''
              {
                # wG = write-upget = see your own uploads only
                wG = "*";
                # read-write-modify-delete for users "ed" and "k"
                rwmd = ["ed" "k"];
              };
            '';
          };
          flags = mkOption {
            type = types.attrs;
            description = ''
              Attribute list of volume flags to apply.
              See `${getExe cfg.package} --help-flags` for more details.
            '';
            example = literalExpression ''
              {
                # "fk" enables filekeys (necessary for upget permission) (4 chars long)
                fk = 4;
                # scan for new files every 60sec
                scan = 60;
                # volflag "e2d" enables the uploads database
                e2d = true;
                # "d2t" disables multimedia parsers (in case the uploads are malicious)
                d2t = true;
                # skips hashing file contents if path matches *.iso
                nohash = "\.iso$";
              };
            '';
            default = { };
          };
        };
      }));
      description = "A set of copyparty volumes to create";
      default = {
        "/" = {
          path = defaultShareDir;
          access = { r = "*"; };
        };
      };
      example = literalExpression ''
        {
          "/" = {
            path = ${defaultShareDir};
            access = {
              # wG = write-upget = see your own uploads only
              wG = "*";
              # read-write-modify-delete for users "ed" and "k"
              rwmd = ["ed" "k"];
            };
          };
        };
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

      preStart = let
        replaceSecretCommand = name: attrs:
          "${getExe pkgs.replace-secret} '${
            passwordPlaceholder name
          }' '${attrs.passwordFile}' ${runtimeConfigPath}";
      in ''
        set -euo pipefail
        install -m 600 ${configFile} ${runtimeConfigPath}
        ${concatStringsSep "\n"
        (mapAttrsToList replaceSecretCommand cfg.accounts)}
      '';

      serviceConfig = {
        Type = "simple";
        ExecStart = "${getExe cfg.package} -c ${runtimeConfigPath}";

        # Hardening options
        User = "copyparty";
        Group = "copyparty";
        RuntimeDirectory = name;
        RuntimeDirectoryMode = "0700";
        StateDirectory = [ name "${name}/data" "${name}/.config" ];
        StateDirectoryMode = "0700";
        WorkingDirectory = home;
        TemporaryFileSystem = "/:ro";
        BindReadOnlyPaths = [
          "/nix/store"
          "-/etc/resolv.conf"
          "-/etc/nsswitch.conf"
          "-/etc/hosts"
          "-/etc/localtime"
        ] ++ (mapAttrsToList (k: v: "-${v.passwordFile}") cfg.accounts);
        BindPaths = [ home ] ++ (mapAttrsToList (k: v: v.path) cfg.volumes);
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
