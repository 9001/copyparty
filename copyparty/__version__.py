# coding: utf-8

VERSION = (0, 12, 3)
CODENAME = "fil\033[33med"
BUILD_DT = (2021, 7, 30)

S_VERSION = ".".join(map(str, VERSION))
S_BUILD_DT = "{0:04d}-{1:02d}-{2:02d}".format(*BUILD_DT)

__version__ = S_VERSION
__build_dt__ = S_BUILD_DT

# I'm all ears
