# coding: utf-8

VERSION = (1, 1, 5)
CODENAME = "opus"
BUILD_DT = (2021, 12, 4)

S_VERSION = ".".join(map(str, VERSION))
S_BUILD_DT = "{0:04d}-{1:02d}-{2:02d}".format(*BUILD_DT)

__version__ = S_VERSION
__build_dt__ = S_BUILD_DT

# I'm all ears
