"""
if you use collabora office editor with copyparty, you already have a thumbnailer for office formats:
https://sdk.collaboraonline.com/docs/conversion_api.html
the 'convert-to' api accepts files in multipart/form-data format

just add this extractor to copyparty with an argument like this:
  --th-extract=docx,xlsx,pptx,odt,ods,pdf,fb2=~/dev/copyparty/bin/thumbs/collabora.py
and set COLLABORA_INSTANCE_URL below to your collabora instace url

full list of supported file types:
https://sdk.collaboraonline.com/docs/conversion_api.html#supported-input-formats

this is also an example of deferred IO:
no files opened and no network requests made if copyparty doesn't like the file type
"""

import os
import string
import random
import mimetypes
from urllib.error import HTTPError
from urllib.request import Request, urlopen

COLLABORA_INSTANCE_URL = 'http://collabora:9980'
BOUNDARY_CHARS = string.ascii_letters + string.digits


def main(abspath, **kwargs):
    boundary = 'CopypartyFormData' + ''.join(random.choices(BOUNDARY_CHARS, k=53))
    start, end = make_headers(abspath, boundary)
    size = len(start) + os.path.getsize(abspath) + len(end)
    request = Request(
        COLLABORA_INSTANCE_URL + '/cool/convert-to/png',
        method='POST',
        data=iterate(start, abspath, end),
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(size)
        }
    )

    file_like = Wrapper(request)
    offset, whence, length = 0, 0, None

    return 'png', file_like, offset, whence, length


def make_headers(abspath, boundary):
    """stuff to wrap file contents by for multipart"""

    fname = 'file.' + abspath.rsplit('.', 1)[-1]
    ftype = mimetypes.guess_file_type(fname)[0] or 'application/octet-stream'
    start = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="data"; filename="{fname}"\r\n'
        f'Content-Type: {ftype}\r\n\r\n'
    )
    end = f'\r\n--{boundary}--'
    return bytes(start, 'ascii'), bytes(end, 'ascii')


def iterate(start, fpath, end):
    """docs may be big so read and send them in chunks"""

    yield start
    with open(fpath, 'rb') as f:
        while True:
            b = f.read(32768)
            if not b:
                break
            yield b
    yield end


class Wrapper:
    """
    This file-like wrapper defers expensive work until first .seek() call
    Useful  to not waste resources in case copyparty decides
    to throw our thumbnail away based on returned file extension
    """

    def __init__(self, request):
        self.request = request
        self.response = None

    def seek(self, offset, whence=0):
        if self.response:
            return 0

        try:
            # the heavy part: 
            # - reading probably big file
            # - sending it over the network
            # - making collabora do some work
            self.response = urlopen(self.request, timeout=10)
        except HTTPError as e:
            e.close()
            raise e
        except Exception as e:
            self.close()
            raise e

        # actual response is not seekable
        # just return 0
        return 0

    def read(self, amount):
        return self.response.read(amount)

    def close(self):
        if self.response:
            self.response.close()
