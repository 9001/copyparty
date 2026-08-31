import io
import os
import struct
from base64 import b64decode


def create_gif() -> bytes:
    head = r"R0lGODdhIAAgAIAB"
    tail = r"AAD/LAAAAAAgACAAAAIehI+py+0Po5y02ouz3rz7D4biSJbmiabqyrbuC5sFADs="
    #color = struct.pack(">L", random.randrange(0xffffff))  # wow, way too stable
    color = b"\x00" + os.urandom(3)
    return b64decode(head) + color + b64decode(tail)


def main(abspath, **ka) -> Optional[tuple[str, IO[bytes], int, int, Optional[int]]]:
    print("hello from randomcolor.py pretending to extract a thumb from " + abspath)

    # need to return a file-like object
    gif_bytes = create_gif()
    file_obj = io.BytesIO(gif_bytes)

    # where copyparty should seek to in the "file" to start reading from
    seek_offset = 0
    seek_whence = 0

    filesize = None  # auto; read until end

    # "gif" is the file-extension to decode the file as
    return "gif", file_obj, seek_offset, seek_whence, filesize
