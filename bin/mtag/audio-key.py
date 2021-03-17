#!/usr/bin/env python

import sys
import keyfinder

"""
dep: github/mixxxdj/libkeyfinder
dep: pypi/keyfinder
dep: ffmpeg

note: cannot fsenc
"""


try:
    print(keyfinder.key(sys.argv[1]).camelot())
except:
    pass
