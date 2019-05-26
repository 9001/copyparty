#!/usr/bin/env python
# coding: utf-8
from __future__ import print_function

import platform
import sys
import os

WINDOWS = platform.system() == "Windows"
PY2 = sys.version_info[0] == 2
if PY2:
    sys.dont_write_bytecode = True

