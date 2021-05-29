#!/usr/bin/env python

import sys
import time
import json
import pefile

"""
retrieve exe info,
example for multivalue providers
"""


def unk(v):
    return "unk({:04x})".format(v)


class PE2(pefile.PE):
    def __init__(self, *a, **ka):
        for k in [
            # -- parse_data_directories:
            "parse_import_directory",
            "parse_export_directory",
            # "parse_resources_directory",
            "parse_debug_directory",
            "parse_relocations_directory",
            "parse_directory_tls",
            "parse_directory_load_config",
            "parse_delay_import_directory",
            "parse_directory_bound_imports",
            # -- full_load:
            "parse_rich_header",
        ]:
            setattr(self, k, self.noop)

        super(PE2, self).__init__(*a, **ka)

    def noop(*a, **ka):
        pass


try:
    pe = PE2(sys.argv[1], fast_load=False)
except:
    sys.exit(0)

arch = pe.FILE_HEADER.Machine
if arch == 0x14C:
    arch = "x86"
elif arch == 0x8664:
    arch = "x64"
else:
    arch = unk(arch)

try:
    buildtime = time.gmtime(pe.FILE_HEADER.TimeDateStamp)
    buildtime = time.strftime("%Y-%m-%d_%H:%M:%S", buildtime)
except:
    buildtime = "invalid"

ui = pe.OPTIONAL_HEADER.Subsystem
if ui == 2:
    ui = "GUI"
elif ui == 3:
    ui = "cmdline"
else:
    ui = unk(ui)

extra = {}
if hasattr(pe, "FileInfo"):
    for v1 in pe.FileInfo:
        for v2 in v1:
            if v2.name != "StringFileInfo":
                continue

            for v3 in v2.StringTable:
                for k, v in v3.entries.items():
                    v = v.decode("utf-8", "replace").strip()
                    if not v:
                        continue

                    if k in [b"FileVersion", b"ProductVersion"]:
                        extra["ver"] = v

                    if k in [b"OriginalFilename", b"InternalName"]:
                        extra["orig"] = v

r = {
    "arch": arch,
    "built": buildtime,
    "ui": ui,
    "cksum": "{:08x}".format(pe.OPTIONAL_HEADER.CheckSum),
}
r.update(extra)

print(json.dumps(r, indent=4))
