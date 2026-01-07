#!/usr/bin/env python3

from typing import Any

_ = r"""
the fastest hook in the west
(runs directly inside copyparty, not as a subprocess)

example usage as global config:
    --xbu I,bin/hooks/import-me.py

example usage as a volflag (per-volume config):
    -v srv/inc:inc:r:rw,ed:c,xbu=I,bin/hooks/import-me.py
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    (share filesystem-path srv/inc as volume /inc,
     readable by everyone, read-write for user 'ed',
     running this plugin on all uploads with the params listed below)

example usage as a volflag in a copyparty config file:
    [/inc]
      srv/inc
      accs:
        r: *
        rw: ed
      flags:
        xbu: I,bin/hooks/import-me.py

parameters explained,
    I = import; do not fork / subprocess

IMPORTANT NOTE:
    because this hook is running inside copyparty, you need to
    be EXCEPTIONALLY CAREFUL to avoid side-effects, for example
    DO NOT os.chdir() or anything like that, and also make sure
    that the name of this file is unique (cannot be the same as
    an existing python module/library)
"""


def main(ka: dict[str, Any]) -> dict[str, Any]:
    # "ka" is a dictionary with info from copyparty...

    # but because we are running inside copyparty, we don't need such courtesies;
    import inspect

    cf = inspect.currentframe().f_back.f_back.f_back
    t = "hello from hook; I am able to peek into copyparty's memory like so:\n  function name: %s\n  variables:\n    %s\n"
    t2 = "\n    ".join([("%r: %r" % (k, v))[:99] for k, v in cf.f_locals.items()][:9])
    logger = ka["log"]
    logger(t % (cf.f_code, t2))

    # must return a dictionary with:
    #  "rc": the retcode; 0 is ok
    return {"rc": 0}
