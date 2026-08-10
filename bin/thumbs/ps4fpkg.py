"""
originally created by kamaeff in kamaeff/copyparty-dumb-fpkgi-handler
contributed to copyparty under whatever the license copyparty uses

learn more about ps4 fake package format: https://www.psdevwiki.com/ps4/PKG_files
"""

import struct
from typing import IO, Optional

SEEK_SET = 0

FPKG_MAGIC = 0x7F434E54
ENTRY_ID_ICON0_PNG = 0x1200
ENTRY_ID_PIC0_PNG = 0x1220
# limits for sanity checks
ENTRY_COUNT_LIMIT = 255
FILE_SIZE_LIMIT = 10_000_000


def main(abspath, **kwargs) -> Optional[tuple[str, IO[bytes], int, int, Optional[int]]]:
    f = None
    try:
        f = open(abspath, 'rb')
        magic, entry_count, entry_table_position = _read_struct(f, '>I12xI4xI')
        if magic != FPKG_MAGIC:
            raise Exception("pkg file: not a playstation 4 fPKG: %s" % abspath)
        if entry_count > ENTRY_COUNT_LIMIT:
            raise Exception("pkg file: suspicious; too many entries: %s" % abspath)

        cover_offset = cover_length = None
        f.seek(entry_table_position)
        for _ in range(entry_count):
            entry_id, offset, length = _read_struct(f, '>I12xII8x')
            if entry_id not in {ENTRY_ID_ICON0_PNG, ENTRY_ID_PIC0_PNG}:
                continue
            cover_offset, cover_length = offset, length
            # prefer icon0.png
            if entry_id == ENTRY_ID_ICON0_PNG:
                break

        if cover_length is None or cover_offset is None:
            raise Exception("pkg file: no cover image found: %s" % abspath)
        if cover_length > FILE_SIZE_LIMIT:
            raise Exception("pkg file: suspicious; cover image too large: %s" % abspath)

        return 'png', f, cover_offset, SEEK_SET, cover_length
    except Exception as e:
        if f:
            f.close()
        raise e


def _read_struct(file: IO[bytes], fmt: str) -> tuple[int, ...]:
    size = struct.calcsize(fmt)
    return struct.unpack(fmt, file.read(size))
